import sqlite3
from datetime import datetime
import statistics

def analyze_customer_transactions(db_path: str, customer_id: str):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM customers WHERE customer_id = ?", (customer_id,))
    customer = cursor.fetchone()
    if not customer:
        return None, None, []

    cursor.execute("SELECT * FROM transactions WHERE customer_id = ? ORDER BY timestamp ASC", (customer_id,))
    txns = [dict(row) for row in cursor.fetchall()]
    conn.close()

    if not txns:
        return dict(customer), [], []

    # Statistical baseline (excluding high spikes)
    amounts = [t["amount"] for t in txns]
    avg_amount = statistics.mean(amounts)
    std_dev = statistics.stdev(amounts) if len(amounts) > 1 else 0

    rule_flags = []

    # Historical payee set for baseline comparison
    # Payees seen in the first half of customer history or standard profile
    established_payees = set()
    half_index = max(1, len(txns) // 2)
    for t in txns[:half_index]:
        established_payees.add(t["payee"])

    # Established channels
    established_channels = set(t["channel"] for t in txns[:half_index])

    # 1. Check Odd-Hours Activity (11:00 PM to 5:00 AM)
    for t in txns:
        dt = datetime.fromisoformat(t["timestamp"])
        if dt.hour >= 23 or dt.hour <= 5:
            rule_flags.append({
                "rule_name": "ODD_HOURS_ACTIVITY",
                "txn_id": t["txn_id"],
                "details": f"Transaction executed at {dt.strftime('%H:%M')} (outside standard 06:00-23:00 operational hours)."
            })

    # 2. Check Sudden Velocity Spikes to Single Payee (>2 transactions within 1 hour)
    for i in range(len(txns)):
        cluster = [txns[i]]
        t1 = datetime.fromisoformat(txns[i]["timestamp"])
        for j in range(i + 1, len(txns)):
            t2 = datetime.fromisoformat(txns[j]["timestamp"])
            if (t2 - t1).total_seconds() <= 3600 and txns[j]["payee"] == txns[i]["payee"]:
                cluster.append(txns[j])
        if len(cluster) >= 3:
            for c in cluster:
                rule_flags.append({
                    "rule_name": "RAPID_VELOCITY_BURST",
                    "txn_id": c["txn_id"],
                    "details": f"Burst transaction to payee '{c['payee']}' within 1 hour."
                })

    # 3. Check Deviation from Baseline (> 3.5x average historical value and > ₹10,000)
    for t in txns:
        if avg_amount > 0 and t["amount"] >= (avg_amount * 3.5) and t["amount"] > 10000:
            rule_flags.append({
                "rule_name": "BASELINE_DEVIATION_HIGH_VALUE",
                "txn_id": t["txn_id"],
                "details": f"Amount ₹{t['amount']:,.2f} significantly exceeds historical customer average of ₹{round(avg_amount, 2):,.2f}."
            })

    # 4. Check Structuring / Smurfing Pattern (Multiple txns between ₹45,000 and ₹49,999 within 24h)
    structuring_txns = []
    for t in txns:
        if 45000 <= t["amount"] <= 49999:
            structuring_txns.append(t)
    if len(structuring_txns) >= 2:
        for st in structuring_txns:
            rule_flags.append({
                "rule_name": "STRUCTURING_SMURFING_PATTERN",
                "txn_id": st["txn_id"],
                "details": f"Amount ₹{st['amount']:,.2f} structured immediately below the ₹50,000 regulatory reporting threshold."
            })

    # 5. Check Burst to Unrecognized / New Payee
    for i, t in enumerate(txns):
        if i >= half_index and t["payee"] not in established_payees and t["amount"] >= 20000:
            rule_flags.append({
                "rule_name": "NEW_PAYEE_HIGH_VALUE",
                "txn_id": t["txn_id"],
                "details": f"High value transfer ₹{t['amount']:,.2f} to unverified new payee '{t['payee']}'."
            })

    # Deduplicate flags per transaction & rule
    deduped_flags = []
    seen = set()
    for f in rule_flags:
        key = (f["rule_name"], f["txn_id"])
        if key not in seen:
            seen.add(key)
            deduped_flags.append(f)

    return dict(customer), txns, deduped_flags