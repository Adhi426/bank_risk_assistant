"""
Deterministic Banking Risk Rules
--------------------------------

The rule engine is intentionally deterministic.

Gemini is NOT responsible for detecting transactions.
Gemini only explains evidence produced here.
"""

import sqlite3
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Any


def _parse_timestamp(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value

    text = str(value)

    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue

    return datetime.fromisoformat(text)


def analyze_customer_transactions(
    db_file: str,
    customer_id: str,
) -> Dict[str, Any]:

    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row

    try:
        customer_row = conn.execute(
            """
            SELECT *
            FROM customers
            WHERE customer_id = ?
            """,
            (customer_id,),
        ).fetchone()

        if not customer_row:
            return {
                "customer": None,
                "transactions": [],
                "flags": [],
            }

        transaction_rows = conn.execute(
            """
            SELECT *
            FROM transactions
            WHERE customer_id = ?
            ORDER BY timestamp ASC
            """,
            (customer_id,),
        ).fetchall()

        customer = dict(customer_row)
        transactions = [dict(row) for row in transaction_rows]

    finally:
        conn.close()

    if not transactions:
        return {
            "customer": customer,
            "transactions": [],
            "flags": [],
        }

    parsed = []

    for txn in transactions:
        item = dict(txn)
        item["_dt"] = _parse_timestamp(txn["timestamp"])
        parsed.append(item)

    flags: List[Dict[str, Any]] = []

    def add_flag(
        txn_id: str,
        rule_name: str,
        description: str,
        severity: str = "MEDIUM",
    ):
        flags.append(
            {
                "txn_id": str(txn_id),
                "rule_name": rule_name,
                "description": description,
                "details": description,
                "severity": severity,
            }
        )

    # ============================================================
    # 1. Establish customer baseline
    # ============================================================

    amounts = [
        float(txn["amount"])
        for txn in parsed
        if txn.get("amount") is not None
    ]

    if amounts:
        avg_amount = statistics.mean(amounts)
        median_amount = statistics.median(amounts)
    else:
        avg_amount = 0
        median_amount = 0

    # Use the earlier portion of the history as the behavioural baseline.
    split_index = max(1, len(parsed) // 2)

    historical_transactions = parsed[:split_index]

    established_payees = {
        str(txn["payee"]).strip().lower()
        for txn in historical_transactions
        if txn.get("payee")
    }

    established_channels = {
        str(txn["channel"]).strip().lower()
        for txn in historical_transactions
        if txn.get("channel")
    }

    historical_amounts = [
        float(txn["amount"])
        for txn in historical_transactions
        if txn.get("amount") is not None
    ]

    if historical_amounts:
        baseline_average = statistics.mean(historical_amounts)
    else:
        baseline_average = avg_amount

    # ============================================================
    # 2. Odd-hours activity
    # ============================================================

    for txn in parsed:
        dt = txn["_dt"]
        t_id = txn.get("txn_id") or txn.get("id")

        if dt.hour >= 23 or dt.hour <= 5:
            add_flag(
                t_id,
                "ODD_HOURS_ACTIVITY",
                (
                    f"Transaction occurred at {dt.strftime('%H:%M')} "
                    "outside the typical daytime transaction window."
                ),
                "MEDIUM",
            )

    # ============================================================
    # 3. Rapid velocity burst
    # ============================================================

    for index, current in enumerate(parsed):

        current_payee = str(
            current.get("payee", "")
        ).strip().lower()

        window_start = current["_dt"] - timedelta(hours=1)

        burst = [
            previous
            for previous in parsed[: index + 1]
            if (
                str(previous.get("payee", "")).strip().lower()
                == current_payee
                and previous["_dt"] >= window_start
                and previous["_dt"] <= current["_dt"]
            )
        ]

        if len(burst) >= 3:

            for txn in burst:
                t_id = txn.get("txn_id") or txn.get("id")
                add_flag(
                    t_id,
                    "RAPID_VELOCITY_BURST",
                    (
                        f"{len(burst)} transactions to the same payee "
                        "occurred within a one-hour window."
                    ),
                    "HIGH",
                )

    # ============================================================
    # 4. Baseline deviation / unusually large transfer
    # ============================================================

    comparison_baseline = max(
        baseline_average,
        median_amount,
        1,
    )

    for txn in parsed:

        amount = float(txn["amount"])
        t_id = txn.get("txn_id") or txn.get("id")

        if (
            amount >= comparison_baseline * 3.5
            and amount > 10000
        ):
            add_flag(
                t_id,
                "BASELINE_DEVIATION_HIGH_VALUE",
                (
                    f"Transaction amount ₹{amount:,.2f} is substantially "
                    f"above the established customer baseline of "
                    f"approximately ₹{comparison_baseline:,.2f}."
                ),
                "HIGH",
            )

    # ============================================================
    # 5. Structuring
    #
    # IMPORTANT:
    # Transactions must actually be within a 24-hour window.
    # ============================================================

    structuring_candidates = [
        txn
        for txn in parsed
        if 45000 <= float(txn["amount"]) <= 49999
    ]

    for index, current in enumerate(structuring_candidates):

        window_start = current["_dt"] - timedelta(hours=24)

        related = [
            txn
            for txn in structuring_candidates[: index + 1]
            if (
                txn["_dt"] >= window_start
                and txn["_dt"] <= current["_dt"]
            )
        ]

        if len(related) >= 2:

            for txn in related:
                t_id = txn.get("txn_id") or txn.get("id")
                add_flag(
                    t_id,
                    "POTENTIAL_STRUCTURING_PATTERN",
                    (
                        f"{len(related)} transactions between "
                        "₹45,000 and ₹49,999 occurred within "
                        "a 24-hour window."
                    ),
                    "HIGH",
                )

    # ============================================================
    # 6. New payee + high-value transaction
    # ============================================================

    for index, txn in enumerate(parsed):

        if index < split_index:
            continue

        payee = str(
            txn.get("payee", "")
        ).strip().lower()

        amount = float(txn["amount"])
        t_id = txn.get("txn_id") or txn.get("id")

        if (
            payee
            and payee not in established_payees
            and amount >= 20000
        ):
            add_flag(
                t_id,
                "NEW_PAYEE_HIGH_VALUE",
                (
                    f"High-value transaction of ₹{amount:,.2f} "
                    f"was sent to payee '{txn.get('payee')}', "
                    "which was not present in the customer's "
                    "established historical payee set."
                ),
                "HIGH",
            )

    # ============================================================
    # 7. New channel behaviour
    # ============================================================

    for index, txn in enumerate(parsed):

        if index < split_index:
            continue

        channel = str(
            txn.get("channel", "")
        ).strip().lower()
        t_id = txn.get("txn_id") or txn.get("id")

        if (
            channel
            and channel not in established_channels
        ):
            add_flag(
                t_id,
                "NEW_CHANNEL_BEHAVIOUR",
                (
                    f"Transaction used channel '{txn.get('channel')}', "
                    "which was not observed in the customer's "
                    "historical baseline."
                ),
                "MEDIUM",
            )

    # ============================================================
    # Remove duplicate rule/transaction combinations
    # ============================================================

    unique_flags = []
    seen = set()

    for flag in flags:

        key = (
            flag["rule_name"],
            flag["txn_id"],
        )

        if key not in seen:
            seen.add(key)
            unique_flags.append(flag)

    # Remove internal parsing field before returning transactions.
    clean_transactions = []

    for txn in parsed:
        clean = {
            key: value
            for key, value in txn.items()
            if key != "_dt"
        }
        clean["id"] = clean.get("txn_id") or clean.get("id")
        clean["txn_id"] = clean["id"]
        clean_transactions.append(clean)

    # Calculate defensible category-based risk score & breakdown
    triggered_rules = {f.get("rule_name") for f in unique_flags if f.get("rule_name")}

    odd_score = 20 if any("ODD_HOURS" in r for r in triggered_rules) else 0
    vel_score = 25 if any("VELOCITY" in r for r in triggered_rules) else 0
    dev_score = 20 if any("BASELINE" in r for r in triggered_rules) else 0
    struct_score = 25 if any("STRUCTURING" in r or "NEW_PAYEE" in r for r in triggered_rules) else 0
    channel_score = 10 if any("NEW_CHANNEL" in r for r in triggered_rules) else 0

    total_risk = min(100, odd_score + vel_score + dev_score + struct_score + channel_score)
    risk_level = "LOW RISK" if total_risk == 0 else ("HIGH SEVERITY" if total_risk >= 60 else "ELEVATED RISK")

    return {
        "customer": customer,
        "transactions": clean_transactions,
        "flags": unique_flags,
        "risk_score": total_risk,
        "risk_level": risk_level,
        "risk_breakdown": {
            "odd_hours": odd_score,
            "velocity": vel_score,
            "baseline_deviation": dev_score,
            "structuring_payee": struct_score,
            "new_channel": channel_score,
        },
        "baseline": {
            "average_transaction": round(avg_amount, 2),
            "median_transaction": round(median_amount, 2),
            "historical_baseline_average": round(
                baseline_average,
                2,
            ),
        },
    }