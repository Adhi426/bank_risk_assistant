"""
Evidence Builder
----------------
Converts deterministic rule findings into traceable evidence records.

Important:
- Evidence is created ONLY from transactions present in the database.
- Every evidence item contains the original transaction ID.
- Gemini never creates the underlying evidence.
"""

from typing import Any, Dict, List
from datetime import datetime


def _safe_iso(value: Any) -> str:
    """Convert timestamps into a consistent string representation."""
    if value is None:
        return ""

    if isinstance(value, datetime):
        return value.isoformat()

    return str(value)


def build_evidence_pack(
    customer: Dict[str, Any],
    transactions: List[Dict[str, Any]],
    flags: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Build a traceable evidence pack from deterministic findings.

    Returns:
        {
            "customer": {...},
            "evidence": [...],
            "valid_transaction_ids": [...]
        }
    """

    transaction_map = {
        str(txn.get("txn_id") or txn.get("id")): txn
        for txn in transactions
        if (txn.get("txn_id") is not None or txn.get("id") is not None)
    }

    evidence: List[Dict[str, Any]] = []

    for flag in flags:
        txn_id = str(flag.get("txn_id", ""))

        # Never create evidence for an unknown transaction.
        if txn_id not in transaction_map:
            continue

        txn = transaction_map[txn_id]

        evidence_item = {
            "evidence_id": f"EVID-{txn_id}-{flag.get('rule_name', 'UNKNOWN')}",
            "transaction_id": txn_id,
            "evidence_type": "transaction_anomaly",
            "rule_name": flag.get("rule_name", "UNKNOWN"),
            "rule_description": flag.get("description", ""),
            "transaction": {
                "id": txn_id,
                "timestamp": _safe_iso(txn.get("timestamp")),
                "amount": txn.get("amount"),
                "payee": txn.get("payee"),
                "channel": txn.get("channel"),
                "description": txn.get("description"),
            },
        }

        evidence.append(evidence_item)

    # Remove duplicates while preserving order.
    unique_evidence = []
    seen = set()

    for item in evidence:
        key = (
            item["transaction_id"],
            item["rule_name"],
        )

        if key not in seen:
            seen.add(key)
            unique_evidence.append(item)

    valid_transaction_ids = sorted(transaction_map.keys())

    return {
        "customer": customer,
        "evidence": unique_evidence,
        "valid_transaction_ids": valid_transaction_ids,
        "evidence_count": len(unique_evidence),
    }


def evidence_to_text(evidence_item: Dict[str, Any]) -> str:
    """
    Convert one evidence item into a compact text representation.

    This text is used for Gemini embeddings and retrieval.
    """

    txn = evidence_item["transaction"]

    return (
        f"Transaction ID: {txn.get('id')}. "
        f"Timestamp: {txn.get('timestamp')}. "
        f"Amount: ₹{txn.get('amount')}. "
        f"Payee: {txn.get('payee')}. "
        f"Channel: {txn.get('channel')}. "
        f"Description: {txn.get('description')}. "
        f"Triggered rule: {evidence_item.get('rule_name')}. "
        f"Rule description: {evidence_item.get('rule_description')}."
    )


def evidence_pack_to_text(evidence_pack: Dict[str, Any]) -> str:
    """
    Convert the entire evidence pack into readable text.
    """

    evidence_items = evidence_pack.get("evidence", [])

    if not evidence_items:
        return "No deterministic risk evidence was detected."

    sections = []

    for item in evidence_items:
        sections.append(evidence_to_text(item))

    return "\n".join(sections)