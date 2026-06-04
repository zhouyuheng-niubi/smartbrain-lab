"""Semantic index for methodology auto-surfacing.

Embeds each published methodology's `trigger` text into an in-memory VectorStore.
Degrades gracefully: with no SILICONFLOW_API_KEY, embed_text returns zero vectors,
VectorStore.add skips them, the index stays empty, and the /suggest endpoint falls
back to keyword matching.
"""
from __future__ import annotations

import logging

from sqlmodel import Session, select

from core.embedding import VectorStore, embed_text
from server.app.models.database import Methodology, engine

logger = logging.getLogger(__name__)

_store = VectorStore()


def _trigger_text(m: Methodology) -> str:
    t = m.trigger if isinstance(m.trigger, dict) else {}
    scenarios = " ".join(t.get("scenarios", []) or [])
    keywords = " ".join(t.get("keywords", []) or [])
    return f"{m.name} {m.summary or ''} {scenarios} {keywords}".strip()


def build_methodology_index() -> int:
    """(Re)build the index from all published methodologies. Returns # indexed."""
    global _store
    store = VectorStore()
    with Session(engine) as session:
        rows = list(session.exec(
            select(Methodology).where(Methodology.status == "published")
        ).all())
    for m in rows:
        text = _trigger_text(m)
        if not text:
            continue
        store.add(
            chunk_id=m.id,
            text=text,
            vector=embed_text(text),
            metadata={"id": m.id, "slug": m.slug, "name": m.name},
        )
    _store = store
    return len(store)


def suggest_methodologies(raw_input: str, top_k: int = 3) -> list[dict]:
    """Return the most semantically relevant methodologies for a raw input."""
    if len(_store) == 0:
        if build_methodology_index() == 0:
            return []  # no embeddings available → caller should keyword-fallback
    hits = _store.search(embed_text(raw_input), top_k=top_k, min_score=0.2)
    return [
        {
            "id": h.metadata.get("id"),
            "slug": h.metadata.get("slug"),
            "name": h.metadata.get("name"),
            "score": round(h.score, 3),
        }
        for h in hits
    ]
