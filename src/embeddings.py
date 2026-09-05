"""
Gemini Embeddings
-----------------
Uses Google's Gemini embedding model required by the PS06 architecture.

Model:
    gemini-embedding-001

No external vector database is used.
"""

import os
from typing import List, Optional

from google import genai


EMBEDDING_MODEL = "gemini-embedding-001"


def get_gemini_client(api_key: Optional[str] = None):
    """
    Create a Gemini client.

    Priority:
    1. Explicit API key
    2. GEMINI_API_KEY environment variable
    """

    key = api_key or os.getenv("GEMINI_API_KEY")

    if not key:
        return None

    return genai.Client(api_key=key)


def generate_embedding(
    text: str,
    api_key: Optional[str] = None,
) -> Optional[List[float]]:
    """
    Generate a Gemini embedding for a piece of evidence.

    Returns None when the API key is unavailable or embedding fails.
    """

    if not text:
        return None

    client = get_gemini_client(api_key)

    if client is None:
        return None

    try:
        response = client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=text,
        )

        embedding = getattr(response, "embeddings", None)

        if not embedding:
            return None

        first_embedding = embedding[0]

        values = getattr(first_embedding, "values", None)

        if values is None:
            return None

        return list(values)

    except Exception:
        return None


def generate_embeddings(
    texts: List[str],
    api_key: Optional[str] = None,
) -> List[Optional[List[float]]]:
    """
    Generate embeddings for multiple evidence documents.

    A failed embedding does not crash the investigation.
    """

    results = []

    for text in texts:
        results.append(
            generate_embedding(
                text=text,
                api_key=api_key,
            )
        )

    return results