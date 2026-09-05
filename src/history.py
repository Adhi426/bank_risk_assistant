"""
SentinelRisk History Module
---------------------------
Manages persistent, immutable historical assessment records in SQLite (transactions.db).
"""

import json
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional


def init_history_db(db_path: str = "transactions.db"):
    """
    Ensure the investigation_assessments table exists in SQLite.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS investigation_assessments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            assessment_id TEXT UNIQUE NOT NULL,
            customer_id TEXT NOT NULL,
            customer_name TEXT NOT NULL,
            created_at TEXT NOT NULL,
            risk_score INTEGER NOT NULL,
            risk_level TEXT NOT NULL,
            attention_required BOOLEAN NOT NULL,
            status TEXT NOT NULL,
            rule_trigger_count INTEGER NOT NULL,
            flagged_transaction_count INTEGER NOT NULL,
            primary_finding TEXT NOT NULL,
            connected_transactions_json TEXT,
            triggered_rules_json TEXT,
            baseline_json TEXT,
            why_it_matters_json TEXT,
            investigator_priority_json TEXT,
            recommended_next_steps_json TEXT,
            evidence_json TEXT,
            validation_json TEXT,
            model_name TEXT,
            full_report_json TEXT
        )
    """)
    conn.commit();
    conn.close()


def generate_assessment_id(db_path: str = "transactions.db") -> str:
    """
    Generate sequential Assessment ID e.g. ASSESS-2026-0001
    """
    init_history_db(db_path)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM investigation_assessments")
    count = cursor.fetchone()[0] + 1
    conn.close()
    year = datetime.now().year
    return f"ASSESS-{year}-{count:04d}"


def save_assessment_record(
    db_path: str,
    customer_id: str,
    customer_name: str,
    risk_score: int,
    risk_level: str,
    attention_required: bool,
    status: str,
    primary_finding: str,
    connected_transactions: List[Any],
    triggered_rules: List[Any],
    baseline: Dict[str, Any],
    why_it_matters: List[str],
    investigator_priority: List[str],
    recommended_next_steps: List[str],
    evidence: Any,
    validation: Dict[str, Any],
    model_name: str,
    full_report: Any,
    assessment_id: Optional[str] = None,
    created_at_override: Optional[str] = None
) -> Dict[str, Any]:
    """
    Save an immutable assessment snapshot to SQLite.
    """
    init_history_db(db_path)
    if not assessment_id:
        assessment_id = generate_assessment_id(db_path)

    created_at = created_at_override or datetime.now().strftime("%d %b %Y • %H:%M")

    rule_trigger_count = len(triggered_rules) if isinstance(triggered_rules, list) else 0
    flagged_transaction_count = len(connected_transactions) if isinstance(connected_transactions, list) else 0

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO investigation_assessments (
            assessment_id, customer_id, customer_name, created_at, risk_score, risk_level,
            attention_required, status, rule_trigger_count, flagged_transaction_count,
            primary_finding, connected_transactions_json, triggered_rules_json,
            baseline_json, why_it_matters_json, investigator_priority_json,
            recommended_next_steps_json, evidence_json, validation_json,
            model_name, full_report_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        assessment_id,
        customer_id,
        customer_name,
        created_at,
        int(risk_score),
        risk_level,
        1 if attention_required else 0,
        status,
        rule_trigger_count,
        flagged_transaction_count,
        primary_finding,
        json.dumps(connected_transactions),
        json.dumps(triggered_rules),
        json.dumps(baseline),
        json.dumps(why_it_matters),
        json.dumps(investigator_priority),
        json.dumps(recommended_next_steps),
        json.dumps(evidence),
        json.dumps(validation),
        model_name,
        json.dumps(full_report) if not isinstance(full_report, str) else full_report
    ))
    conn.commit()
    conn.close()

    return {
        "assessment_id": assessment_id,
        "created_at": created_at,
        "customer_id": customer_id,
        "customer_name": customer_name,
        "risk_score": risk_score,
        "risk_level": risk_level,
        "attention_required": attention_required,
        "status": status,
        "primary_finding": primary_finding
    }


def get_history_summaries(
    db_path: str = "transactions.db",
    search: Optional[str] = None,
    risk_level: Optional[str] = None,
    attention_required: Optional[bool] = None,
    customer_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Fetch history summaries sorted newest first.
    """
    init_history_db(db_path)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    query = "SELECT * FROM investigation_assessments WHERE 1=1"
    params = []

    if customer_id:
        query += " AND customer_id = ?"
        params.append(customer_id)

    if risk_level and risk_level.upper() != 'ALL':
        query += " AND UPPER(risk_level) = ?"
        params.append(risk_level.upper())

    if attention_required is not None:
        query += " AND attention_required = ?"
        params.append(1 if attention_required else 0)

    query += " ORDER BY id DESC"

    rows = cursor.execute(query, params).fetchall()
    conn.close()

    results = []
    search_term = search.lower().strip() if search else None

    for r in rows:
        item = {
            "assessment_id": r["assessment_id"],
            "customer_id": r["customer_id"],
            "customer_name": r["customer_name"],
            "created_at": r["created_at"],
            "risk_score": r["risk_score"],
            "risk_level": r["risk_level"],
            "attention_required": bool(r["attention_required"]),
            "status": r["status"],
            "rule_trigger_count": r["rule_trigger_count"],
            "flagged_transaction_count": r["flagged_transaction_count"],
            "primary_finding": r["primary_finding"],
            "model_name": r["model_name"]
        }

        if search_term:
            combined = f"{item['assessment_id']} {item['customer_id']} {item['customer_name']} {item['primary_finding']} {item['risk_level']} {item['status']}".lower()
            if search_term not in combined:
                continue

        results.append(item)

    return results


def get_assessment_by_id(db_path: str, assessment_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve full saved assessment record snapshot by assessment_id.
    """
    init_history_db(db_path)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    row = cursor.execute(
        "SELECT * FROM investigation_assessments WHERE assessment_id = ?",
        (assessment_id,)
    ).fetchone()
    conn.close()

    if not row:
        return None

    r = dict(row)
    return {
        "assessment_id": r["assessment_id"],
        "customer_id": r["customer_id"],
        "customer_name": r["customer_name"],
        "created_at": r["created_at"],
        "risk_score": r["risk_score"],
        "risk_level": r["risk_level"],
        "attention_required": bool(r["attention_required"]),
        "status": r["status"],
        "rule_trigger_count": r["rule_trigger_count"],
        "flagged_transaction_count": r["flagged_transaction_count"],
        "primary_finding": r["primary_finding"],
        "connected_transactions": json.loads(r["connected_transactions_json"] or "[]"),
        "triggered_rules": json.loads(r["triggered_rules_json"] or "[]"),
        "baseline": json.loads(r["baseline_json"] or "{}"),
        "why_it_matters": json.loads(r["why_it_matters_json"] or "[]"),
        "investigator_priority": json.loads(r["investigator_priority_json"] or "[]"),
        "recommended_next_steps": json.loads(r["recommended_next_steps_json"] or "[]"),
        "evidence": json.loads(r["evidence_json"] or "{}"),
        "validation": json.loads(r["validation_json"] or "{}"),
        "model_name": r["model_name"],
        "full_report": r["full_report_json"]
    }


def seed_initial_history(db_path: str = "transactions.db"):
    """
    Seed initial historical assessments if none exist in the database.
    """
    init_history_db(db_path)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    count = cursor.execute("SELECT COUNT(*) FROM investigation_assessments").fetchone()[0]
    conn.close()

    if count > 0:
        return

    # Seed 1: CUST_002 High Risk
    save_assessment_record(
        db_path=db_path,
        customer_id="CUST_002",
        customer_name="Vikram Rathore",
        risk_score=82,
        risk_level="HIGH",
        attention_required=True,
        status="ATTENTION REQUIRED",
        primary_finding="New payee + rapid velocity + odd-hours activity during off-peak hours.",
        connected_transactions=[
            {"txn_id": "TXN_203", "amount": 95000.0, "payee": "Unknown Payee - Alpha Holdings", "channel": "IMPS", "timestamp": "2026-08-15T03:14:00"},
            {"txn_id": "TXN_204", "amount": 98000.0, "payee": "Unknown Payee - Alpha Holdings", "channel": "IMPS", "timestamp": "2026-08-15T03:26:00"},
            {"txn_id": "TXN_205", "amount": 92000.0, "payee": "Unknown Payee - Alpha Holdings", "channel": "IMPS", "timestamp": "2026-08-15T03:39:00"},
            {"txn_id": "TXN_00206", "amount": 60000.0, "payee": "Josalukas", "channel": "UPI", "timestamp": "2026-08-20T03:14:00"}
        ],
        triggered_rules=[
            "ODD_HOURS_ACTIVITY",
            "RAPID_VELOCITY_BURST",
            "NEW_PAYEE_HIGH_VALUE",
            "NEW_CHANNEL_BEHAVIOUR"
        ],
        baseline={
            "historical_baseline_average": 10250.0,
            "normal_activity_window": "10 AM – 6 PM",
            "established_payees_count": 5,
            "established_channels": "NEFT / IMPS"
        },
        why_it_matters=[
            "Amounts deviate significantly from historical behaviour (typical ₹8,000–₹15,000)",
            "Payee was newly observed in current transaction window",
            "Transactions occurred in a compressed time window during off-hours (3:14 AM)",
            "Activity occurred outside the customer's normal daytime pattern"
        ],
        investigator_priority=[
            "Verify customer authorization via registered telephone",
            "Verify the newly observed payee entity credentials",
            "Review authentication/device login activity around 3:00 AM",
            "Review surrounding transactions and outbound payment rails"
        ],
        recommended_next_steps=[
            "Freeze Outbound Rails",
            "Request KYC / Income Proof",
            "Review Transaction Context"
        ],
        evidence={
            "evidence_id": "EVID-TXN_00206-NEW_CHANNEL_BEHAVIOUR",
            "hash": "0x9f8a3c4e7b1d2e0f"
        },
        validation={
            "evidence_validated": True,
            "traceable_to_ledger": True,
            "grounded": True,
            "human_decision_required": True
        },
        model_name="Gemini 2.0 Flash",
        full_report="### SentinelRisk Assessment Dossier — Vikram Rathore\n\n**ATTENTION REQUIRED:** Deterministic rules identified high velocity bursts during off-hours to unverified payees.",
        assessment_id="ASSESS-2026-0021",
        created_at_override="05 Sep 2026 • 13:30"
    )

    # Seed 2: CUST_003 Medium Risk / Structuring
    save_assessment_record(
        db_path=db_path,
        customer_id="CUST_003",
        customer_name="Ananya Sen",
        risk_score=65,
        risk_level="MEDIUM",
        attention_required=True,
        status="ATTENTION REQUIRED",
        primary_finding="Potential structuring pattern: Multiple transfers right below ₹50,000 threshold.",
        connected_transactions=[
            {"txn_id": "TXN_302", "amount": 49900.0, "payee": "Apex Crypto Traders", "channel": "IMPS", "timestamp": "2026-08-20T16:00:00"},
            {"txn_id": "TXN_303", "amount": 49500.0, "payee": "Apex Crypto Traders", "channel": "IMPS", "timestamp": "2026-08-20T18:00:00"},
            {"txn_id": "TXN_304", "amount": 49800.0, "payee": "Apex Crypto Traders", "channel": "IMPS", "timestamp": "2026-08-20T20:00:00"}
        ],
        triggered_rules=[
            "STRUCTURING_THRESHOLD_EVASION",
            "RAPID_VELOCITY_BURST"
        ],
        baseline={
            "historical_baseline_average": 3500.0,
            "normal_activity_window": "10 AM – 11 PM",
            "established_payees_count": 4,
            "established_channels": "UPI / IMPS"
        },
        why_it_matters=[
            "Repeated transfers structured right under ₹50,000 mandatory compliance reporting threshold",
            "High frequency execution within a compressed 4-hour window",
            "Payee categorized under high-risk virtual asset service provider"
        ],
        investigator_priority=[
            "Request income proof & tax declarations from customer",
            "Verify source of funds and business justification for P2P settlement",
            "File Suspicious Activity Report (SAR) if unverified"
        ],
        recommended_next_steps=[
            "Request KYC / Income Proof",
            "Review Customer Profile",
            "File SAR Report"
        ],
        evidence={
            "evidence_id": "EVID-TXN_302-STRUCTURING_THRESHOLD_EVASION",
            "hash": "0x4b7c2a1d9e8f"
        },
        validation={
            "evidence_validated": True,
            "traceable_to_ledger": True,
            "grounded": True,
            "human_decision_required": True
        },
        model_name="Gemini 2.0 Flash",
        full_report="### SentinelRisk Assessment Dossier — Ananya Sen\n\n**ATTENTION REQUIRED:** Structuring pattern detected below statutory limits.",
        assessment_id="ASSESS-2026-0019",
        created_at_override="05 Sep 2026 • 12:10"
    )

    # Seed 3: CUST_001 Low Risk / Clean
    save_assessment_record(
        db_path=db_path,
        customer_id="CUST_001",
        customer_name="Priya Sharma",
        risk_score=0,
        risk_level="LOW",
        attention_required=False,
        status="NO ATTENTION REQUIRED",
        primary_finding="NO ATTENTION REQUIRED: No configured risk rule identified behaviour requiring investigator review.",
        connected_transactions=[],
        triggered_rules=[],
        baseline={
            "historical_baseline_average": 1766.0,
            "normal_activity_window": "9 AM – 9 PM",
            "established_payees_count": 8,
            "established_channels": "UPI / POS"
        },
        why_it_matters=[
            "Activity conforms strictly to established monthly grocery and utility baseline",
            "No unusual velocity or off-hour activity detected"
        ],
        investigator_priority=[
            "No immediate action required. Account operates within normal risk parameters."
        ],
        recommended_next_steps=[
            "Clear Case as Benign"
        ],
        evidence={
            "evidence_id": "EVID-CUST_001-CLEAN_BASELINE",
            "hash": "0x1a2b3c4d5e"
        },
        validation={
            "evidence_validated": True,
            "traceable_to_ledger": True,
            "grounded": True,
            "human_decision_required": True
        },
        model_name="Gemini 2.0 Flash",
        full_report="### SentinelRisk Assessment Dossier — Priya Sharma\n\n**NO ATTENTION REQUIRED:** Baseline verified.",
        assessment_id="ASSESS-2026-0015",
        created_at_override="05 Sep 2026 • 09:45"
    )
