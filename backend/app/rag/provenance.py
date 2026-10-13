"""Provenance formatting and citation generator for RAG retrieval."""

from typing import Any, Dict, List, Optional


def build_grounded_context(chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Builds structured grounded context with strict citations from retrieved chunks.

    Never fabricates sources. If chunk list is empty, returns insufficient-approved-evidence flag.
    """
    if not chunks:
        return {
            "has_sufficient_evidence": False,
            "citations": [],
            "grounded_text": "Insufficient approved syllabus evidence available for this concept.",
        }

    citations = []
    text_blocks = []

    for i, chk in enumerate(chunks, 1):
        meta = chk.get("metadata", {})
        citation = {
            "index": i,
            "chunk_id": chk.get("id"),
            "source_title": meta.get("source_title", "Official Curriculum Material"),
            "source_locator": meta.get("source_locator", "N/A"),
            "section_title": meta.get("section_title", "General Section"),
            "page_number": meta.get("page_number", 0),
            "language": meta.get("language", "bilingual"),
            "retrieval_mode": chk.get("retrieval_mode", "vector"),
        }
        citations.append(citation)

        block = (
            f"[{i}] Source: {citation['source_title']} ({citation['source_locator']}, p.{citation['page_number']})\n"
            f"Section: {citation['section_title']}\n"
            f"Content: {chk.get('text', '').strip()}"
        )
        text_blocks.append(block)

    return {
        "has_sufficient_evidence": True,
        "citations": citations,
        "grounded_text": "\n\n".join(text_blocks),
    }
