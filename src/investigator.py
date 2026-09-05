"""
Gemini Investigation Assistant
--------------------------------

Deterministic rules create the evidence.
Gemini explains the evidence.

Gemini is never allowed to invent transaction IDs.
"""

import json
import os
import re
import time
from typing import Any, Dict, Optional, List

from google import genai
from google.genai import types

from src.evidence import (
    build_evidence_pack,
    evidence_to_text,
)
from src.embeddings import generate_embedding
from src.retrieval import (
    build_retrieval_query,
    retrieve_top_evidence,
)


VALIDATION_KEY = "<BROADCAST_VALIDATION_KEY>"


SYSTEM_PROMPT = """
You are SentinelRisk AI, a banking transaction-risk investigation assistant.

Your job is to explain deterministic evidence for a human investigator.

CRITICAL RULES:

1. Never claim that fraud has occurred.
2. Say whether the available evidence requires attention.
3. Every transaction ID you mention MUST exist in the supplied evidence.
4. Never invent transaction IDs, amounts, payees, timestamps, channels,
   or customer behaviour.
5. Distinguish deterministic rule findings from your reasoning.
6. Explain how related transactions connect.
7. Explain deviation from the customer's established behaviour.
8. Tell the investigator what should be reviewed first.
9. If evidence is insufficient, explicitly say so.
10. The final decision belongs to a human investigator.

Return ONLY valid JSON matching the requested schema.
"""


OUTPUT_SCHEMA = {
    "attention_required": "boolean",
    "risk_level": "LOW | MEDIUM | HIGH",
    "primary_finding": "string",
    "connected_transactions": ["transaction IDs"],
    "triggered_rules": ["rule names"],
    "baseline_comparison": {
        "historical_baseline_average": "number",
        "observed_amounts": ["numbers"],
        "explanation": "string",
    },
    "why_it_matters": ["strings"],
    "investigator_priority": ["strings"],
    "missing_information": ["strings"],
    "recommended_next_steps": ["strings"],
    "human_decision_required": True,
}


def _extract_json(text: str) -> Optional[Dict[str, Any]]:
    """
    Safely extract JSON from Gemini output.
    """

    if not text:
        return None

    text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    match = re.search(
        r"\{.*\}",
        text,
        flags=re.DOTALL,
    )

    if not match:
        return None

    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return None


def _validate_report(
    report: Dict[str, Any],
    valid_transaction_ids: List[str],
) -> Dict[str, Any]:
    """
    Validate that Gemini only references transactions that actually exist.
    """

    valid_ids = {
        str(txn_id)
        for txn_id in valid_transaction_ids
    }

    cited_ids = report.get(
        "connected_transactions",
        [],
    )

    invalid_ids = [
        str(txn_id)
        for txn_id in cited_ids
        if str(txn_id) not in valid_ids
    ]

    if invalid_ids:
        raise ValueError(
            "Gemini referenced unknown transaction IDs: "
            + ", ".join(invalid_ids)
        )

    report["connected_transactions"] = [
        str(txn_id)
        for txn_id in cited_ids
        if str(txn_id) in valid_ids
    ]

    report["human_decision_required"] = True

    return report


def _deterministic_fallback(
    customer: Dict[str, Any],
    transactions: List[Dict[str, Any]],
    flags: List[Dict[str, Any]],
    baseline: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Safe fallback when Gemini is unavailable.
    """

    if not flags:

        return {
            "attention_required": False,
            "risk_level": "LOW",
            "primary_finding": (
                "No deterministic risk rules were triggered "
                "for the supplied transaction history."
            ),
            "connected_transactions": [],
            "triggered_rules": [],
            "baseline_comparison": {
                "historical_baseline_average": baseline.get(
                    "historical_baseline_average",
                    0,
                ),
                "observed_amounts": [],
                "explanation": (
                    "No transaction required escalation "
                    "under the configured rules."
                ),
            },
            "why_it_matters": [],
            "investigator_priority": [],
            "missing_information": [],
            "recommended_next_steps": [
                "No immediate escalation is indicated by the configured rules."
            ],
            "human_decision_required": True,
        }

    flagged_ids = []
    triggered_rules = []

    for flag in flags:
        txn_id = str(flag.get("txn_id"))
        if txn_id not in flagged_ids:
            flagged_ids.append(txn_id)
        rule = flag.get("rule_name")
        if rule and rule not in triggered_rules:
            triggered_rules.append(rule)

    transaction_map = {
        str(txn.get("txn_id") or txn.get("id")): txn
        for txn in transactions
        if (txn.get("txn_id") is not None or txn.get("id") is not None)
    }

    observed_amounts = []

    for txn_id in flagged_ids:
        txn = transaction_map.get(txn_id)

        if txn:
            observed_amounts.append(
                float(txn["amount"])
            )

    return {
        "attention_required": True,
        "risk_level": "HIGH",
        "primary_finding": (
            "Deterministic rules identified transactions that "
            "require investigator review. This does not establish fraud."
        ),
        "connected_transactions": flagged_ids,
        "triggered_rules": triggered_rules,
        "baseline_comparison": {
            "historical_baseline_average": baseline.get(
                "historical_baseline_average",
                0,
            ),
            "observed_amounts": observed_amounts,
            "explanation": (
                "The flagged transactions contain one or more "
                "behavioural or transaction-level deviations."
            ),
        },
        "why_it_matters": [
            "The configured risk rules detected behaviour outside the established pattern."
        ],
        "investigator_priority": [
            "Verify whether the flagged transactions were legitimately initiated by the customer.",
            "Review the payee and transaction context.",
            "Review authentication, device, and account activity around the flagged transactions.",
        ],
        "missing_information": [
            "Authentication and device context was not available to the rule engine."
        ],
        "recommended_next_steps": [
            "Review the flagged transactions and supporting account activity before making a decision."
        ],
        "human_decision_required": True,
    }


def report_to_markdown(report: Dict[str, Any], customer: Optional[Dict[str, Any]] = None) -> str:
    """
    Format a structured report dictionary into clean Markdown for UI & export.
    """
    if isinstance(report, str):
        return report

    if not isinstance(report, dict):
        return str(report)

    attn_req = report.get("attention_required", False)
    attn_header = "ATTENTION REQUIRED" if attn_req else "NO ATTENTION REQUIRED"
    risk_lvl = report.get("risk_level", "LOW")
    primary = report.get("primary_finding", "No primary finding detailed.")

    connected_raw = report.get("connected_transactions", [])
    if isinstance(connected_raw, list) and connected_raw:
        connected_txns = ", ".join([str(t) for t in connected_raw])
    else:
        connected_txns = "None"

    triggered_raw = report.get("triggered_rules", [])
    if isinstance(triggered_raw, list) and triggered_raw:
        triggered_rules = "\n".join([f"- **{r}**" for r in triggered_raw])
    else:
        triggered_rules = "- None"

    baseline_info = report.get("baseline_comparison", {})
    base_avg = baseline_info.get("historical_baseline_average", "N/A")
    base_exp = baseline_info.get("explanation", "")

    why_matters_list = report.get("why_it_matters", [])
    why_matters = "\n".join([f"- {item}" for item in why_matters_list]) if why_matters_list else "- No specific escalation factors noted."

    priorities_list = report.get("investigator_priority", [])
    priorities = "\n".join([f"{i+1}. {item}" for i, item in enumerate(priorities_list)]) if priorities_list else "- Review standard customer profile."

    next_steps_list = report.get("recommended_next_steps", [])
    next_steps = "\n".join([f"- {item}" for item in next_steps_list]) if next_steps_list else "- Proceed with standard queue audit."

    missing_list = report.get("missing_information", [])
    missing = "\n".join([f"- {item}" for item in missing_list]) if missing_list else "- Standard database record available."

    cust_name = customer.get("name", "N/A") if customer else "N/A"
    cust_id = customer.get("customer_id", "N/A") if customer else "N/A"

    return f"""### Risk Investigation Report ({attn_header})
**Severity:** `{risk_lvl}` | **Customer:** {cust_name} (`{cust_id}`)

---

### Primary Finding
> **{attn_header}:** {primary}

### Case Breakdown & Deterministic Evidence
* **Connected Transactions:** `{connected_txns}`
* **Historical Baseline Average:** ₹{base_avg}
* **Baseline Context:** {base_exp}

### Triggered Risk Rules
{triggered_rules}

### Why It Matters
{why_matters}

### Investigator Action Plan & Priorities
{priorities}

### Recommended Next Steps
{next_steps}

### Additional Context Needed
{missing}

---
*Notice: This does not establish fraud. Human investigator review is required. This dossier synthesized deterministic rule triggers with local AI evidence retrieval. Final judgment remains with the human fraud desk investigator.*
"""



def generate_investigation_report(
    customer: Dict[str, Any],
    transactions: List[Dict[str, Any]],
    flags: List[Dict[str, Any]],
    baseline: Optional[Dict[str, Any]] = None,
    custom_api_key: Optional[str] = None,
) -> Dict[str, Any]:

    baseline = baseline or {}

    # ============================================================
    # Build evidence
    # ============================================================

    evidence_pack = build_evidence_pack(
        customer=customer,
        transactions=transactions,
        flags=flags,
    )

    evidence_items = evidence_pack["evidence"]

    # No flags = deterministic no-attention result.
    if not flags:

        return _deterministic_fallback(
            customer=customer,
            transactions=transactions,
            flags=flags,
            baseline=baseline,
        )

    api_key = (
        custom_api_key
        or os.getenv("GEMINI_API_KEY")
        or os.getenv("GEMINI_KEY")
    )

    if not api_key:
        return _deterministic_fallback(
            customer=customer,
            transactions=transactions,
            flags=flags,
            baseline=baseline,
        )

    try:
        client = genai.Client(
            api_key=api_key
        )
    except Exception:
        return _deterministic_fallback(
            customer=customer,
            transactions=transactions,
            flags=flags,
            baseline=baseline,
        )

    # ============================================================
    # Build retrieval query
    # ============================================================

    query_text = build_retrieval_query(
        customer=customer,
        flags=flags,
    )

    query_embedding = generate_embedding(
        text=query_text,
        api_key=api_key,
    )

    # ============================================================
    # Embed evidence
    # ============================================================

    evidence_texts = [
        evidence_to_text(item)
        for item in evidence_items
    ]

    evidence_embeddings = [
        generate_embedding(
            text=text,
            api_key=api_key,
        )
        for text in evidence_texts
    ]

    # ============================================================
    # Retrieve relevant evidence
    # ============================================================

    retrieved_evidence = retrieve_top_evidence(
        query_embedding=query_embedding,
        evidence_items=evidence_items,
        evidence_embeddings=evidence_embeddings,
        top_k=8,
    )

    # If embeddings fail, retrieve deterministic evidence directly.
    if not retrieved_evidence:
        retrieved_evidence = evidence_items[:8]

    valid_transaction_ids = (
        evidence_pack["valid_transaction_ids"]
    )

    # ============================================================
    # Build Gemini evidence context
    # ============================================================

    evidence_context = []

    for item in retrieved_evidence:

        txn = item["transaction"]

        evidence_context.append(
            {
                "evidence_id": item["evidence_id"],
                "transaction_id": item["transaction_id"],
                "rule_name": item["rule_name"],
                "rule_description": item["rule_description"],
                "timestamp": txn.get("timestamp"),
                "amount": txn.get("amount"),
                "payee": txn.get("payee"),
                "channel": txn.get("channel"),
                "description": txn.get("description"),
                "retrieval_score": item.get(
                    "retrieval_score"
                ),
            }
        )

    prompt = f"""
Customer:
{json.dumps(customer, indent=2, default=str)}

Deterministic baseline:
{json.dumps(baseline, indent=2, default=str)}

Deterministic flags:
{json.dumps(flags, indent=2, default=str)}

Retrieved evidence:
{json.dumps(evidence_context, indent=2, default=str)}

Valid transaction IDs:
{json.dumps(valid_transaction_ids, indent=2)}

Return JSON using this structure:

{json.dumps(OUTPUT_SCHEMA, indent=2)}

Remember:
- Never claim fraud occurred.
- Only cite transaction IDs from the valid transaction ID list.
- If evidence is insufficient, say so.
- The human investigator makes the final decision.
"""

    models = [
        "gemini-2.0-flash",
        "gemini-1.5-flash",
        "gemini-1.5-pro",
    ]

    for model_name in models:

        for attempt in range(2):

            try:

                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_PROMPT,
                        temperature=0.1,
                        response_mime_type="application/json",
                    ),
                )

                raw_text = getattr(
                    response,
                    "text",
                    "",
                )

                report = _extract_json(raw_text)

                if not report:
                    raise ValueError(
                        "Gemini did not return valid JSON."
                    )

                report = _validate_report(
                    report=report,
                    valid_transaction_ids=valid_transaction_ids,
                )

                # Attach provenance metadata.
                report["_metadata"] = {
                    "source": "Gemini",
                    "model": model_name,
                    "evidence_count": len(
                        retrieved_evidence
                    ),
                    "deterministic_rule_count": len(
                        flags
                    ),
                }

                return report

            except Exception:

                if attempt == 0:
                    time.sleep(0.5)

    return _deterministic_fallback(
        customer=customer,
        transactions=transactions,
        flags=flags,
        baseline=baseline,
    )