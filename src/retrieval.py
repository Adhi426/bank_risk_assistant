"""
Local Evidence Retrieval
------------------------

Uses NumPy cosine similarity.

No hosted vector database is required.
"""

from typing import Any, Dict, List, Optional

import numpy as np


def cosine_similarity(
    vector_a: List[float],
    vector_b: List[float],
) -> float:
    """Calculate cosine similarity between two vectors."""

    a = np.asarray(vector_a, dtype=np.float32)
    b = np.asarray(vector_b, dtype=np.float32)

    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return float(np.dot(a, b) / (norm_a * norm_b))


def retrieve_top_evidence(
    query_embedding: Optional[List[float]],
    evidence_items: List[Dict[str, Any]],
    evidence_embeddings: List[Optional[List[float]]],
    top_k: int = 8,
) -> List[Dict[str, Any]]:
    """
    Retrieve the most relevant evidence items.

    Evidence without embeddings is skipped.
    """

    if not query_embedding:
        return evidence_items[:top_k]

    scored = []

    for evidence, embedding in zip(
        evidence_items,
        evidence_embeddings,
    ):
        if not embedding:
            continue

        score = cosine_similarity(
            query_embedding,
            embedding,
        )

        item = dict(evidence)
        item["retrieval_score"] = round(score, 6)

        scored.append(item)

    scored.sort(
        key=lambda item: item["retrieval_score"],
        reverse=True,
    )

    return scored[:top_k]


def build_retrieval_query(
    customer: Dict[str, Any],
    flags: List[Dict[str, Any]],
) -> str:
    """
    Build a semantic query representing the investigation.
    """

    customer_id = customer.get("customer_id", "UNKNOWN")

    rules = sorted(
        {
            str(flag.get("rule_name"))
            for flag in flags
            if flag.get("rule_name")
        }
    )

    rule_text = ", ".join(rules) if rules else "No detected risk rules"

    return (
        f"Investigate customer {customer_id}. "
        f"Determine whether transaction behaviour requires attention. "
        f"Focus on these deterministic findings: {rule_text}. "
        f"Look for connected transactions, unusual timing, "
        f"large amounts, new payees, velocity bursts, "
        f"and deviation from established customer behaviour."
    )