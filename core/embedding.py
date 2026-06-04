# ╔══════════════════════════════════════════════════════════════════════════╗
# ║ VENDORED FROM bi-dashboard-demo@6dc89a0 (multi_agent_dev/embedding.py)     ║
# ║ on 2026-06-04. Supported subset for this product: embed_text / embed_batch ║
# ║ / SearchHit / VectorStore / _split_chunks. The build_*_index & index_*     ║
# ║ helpers (which bind to bi-dashboard's KnowledgeDoc/Memory tables via lazy  ║
# ║ import) are unused here — this product builds its own index in             ║
# ║ server/app/engine/methodology_index.py. See core/VENDOR.md.               ║
# ╚══════════════════════════════════════════════════════════════════════════╝
"""Embedding service — SiliconFlow BAAI/bge-m3 + numpy vector store.

Provides:
  - embed_text(text) -> list[float]        single text embedding
  - embed_batch(texts) -> list[list[float]]  batch embedding
  - VectorStore                             in-memory numpy cosine similarity search
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import httpx
import numpy as np

logger = logging.getLogger(__name__)

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3")
EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "1024"))
EMBEDDING_BATCH_SIZE = int(os.getenv("EMBEDDING_BATCH_SIZE", "16"))

_CACHE_DIR = Path(os.getenv("EMBEDDING_CACHE_DIR", ".embedding_cache"))


def _get_api_config() -> tuple[str, str]:
    """Return (api_key, base_url) for the embeddings endpoint.

    VENDOR-PATCH: prefer dedicated EMBEDDING_API_KEY / EMBEDDING_BASE_URL so
    embeddings can use a different provider than chat (e.g. Aliyun DashScope's
    text-embedding-v4). Falls back to SILICONFLOW_* for backward compatibility.
    """
    api_key = os.getenv("EMBEDDING_API_KEY", "") or os.getenv("SILICONFLOW_API_KEY", "")
    base_url = (
        os.getenv("EMBEDDING_BASE_URL", "")
        or os.getenv("SILICONFLOW_BASE_URL", "https://api.siliconflow.cn/v1")
    )
    return api_key, base_url


def _text_hash(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()


class _DiskCache:
    """Simple disk cache for embeddings to avoid redundant API calls."""

    def __init__(self, cache_dir: Path):
        self._dir = cache_dir
        self._dir.mkdir(parents=True, exist_ok=True)

    def get(self, text: str) -> list[float] | None:
        path = self._dir / f"{_text_hash(text)}.npy"
        if path.exists():
            try:
                return np.load(str(path)).tolist()
            except Exception:
                return None
        return None

    def put(self, text: str, vec: list[float]) -> None:
        path = self._dir / f"{_text_hash(text)}.npy"
        try:
            np.save(str(path), np.array(vec, dtype=np.float32))
        except Exception as e:
            logger.warning("Failed to cache embedding: %s", e)


_cache = _DiskCache(_CACHE_DIR)


def embed_text(text: str, *, use_cache: bool = True) -> list[float]:
    """Embed a single text string. Returns a float vector."""
    if use_cache:
        cached = _cache.get(text)
        if cached is not None:
            return cached

    result = embed_batch([text], use_cache=False)
    if result:
        vec = result[0]
        # VENDOR-PATCH: never cache a failed (all-zero) embedding — otherwise a
        # transient API failure at cold start poisons the disk cache permanently.
        if use_cache and any(vec):
            _cache.put(text, vec)
        return vec
    return [0.0] * EMBEDDING_DIM


def embed_batch(texts: list[str], *, use_cache: bool = True) -> list[list[float]]:
    """Embed multiple texts via SiliconFlow embedding API."""
    if not texts:
        return []

    api_key, base_url = _get_api_config()
    if not api_key:
        logger.warning("No SILICONFLOW_API_KEY configured, returning zero vectors")
        return [[0.0] * EMBEDDING_DIM for _ in texts]

    results: list[list[float]] = [[] for _ in texts]
    uncached_indices: list[int] = []
    uncached_texts: list[str] = []

    if use_cache:
        for i, t in enumerate(texts):
            cached = _cache.get(t)
            if cached is not None:
                results[i] = cached
            else:
                uncached_indices.append(i)
                uncached_texts.append(t)
    else:
        uncached_indices = list(range(len(texts)))
        uncached_texts = list(texts)

    if not uncached_texts:
        return results

    url = f"{base_url.rstrip('/')}/embeddings"

    for batch_start in range(0, len(uncached_texts), EMBEDDING_BATCH_SIZE):
        batch = uncached_texts[batch_start : batch_start + EMBEDDING_BATCH_SIZE]
        batch_indices = uncached_indices[batch_start : batch_start + EMBEDDING_BATCH_SIZE]

        for attempt in range(3):
            try:
                resp = httpx.post(
                    url,
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json={"model": EMBEDDING_MODEL, "input": batch},
                    timeout=30.0,
                )
                resp.raise_for_status()
                data = resp.json()

                for item in data.get("data", []):
                    idx_in_batch = item["index"]
                    vec = item["embedding"]
                    global_idx = batch_indices[idx_in_batch]
                    results[global_idx] = vec
                    if use_cache:
                        _cache.put(batch[idx_in_batch], vec)
                break

            except Exception as e:
                logger.warning(
                    "Embedding API attempt %d failed: %s", attempt + 1, e
                )
                if attempt < 2:
                    time.sleep(1.5 * (attempt + 1))
                else:
                    for gi in batch_indices:
                        if not results[gi]:
                            results[gi] = [0.0] * EMBEDDING_DIM

    for i in range(len(results)):
        if not results[i]:
            results[i] = [0.0] * EMBEDDING_DIM

    return results


@dataclass
class SearchHit:
    chunk_id: str
    text: str
    score: float
    metadata: dict = field(default_factory=dict)


class VectorStore:
    """Lightweight numpy-based vector store with cosine similarity search."""

    def __init__(self) -> None:
        self._ids: list[str] = []
        self._texts: list[str] = []
        self._metadata: list[dict] = []
        self._matrix: np.ndarray | None = None
        self._lock = threading.Lock()

    def __len__(self) -> int:
        return len(self._ids)

    def add(self, chunk_id: str, text: str, vector: list[float], metadata: dict | None = None) -> None:
        vec = np.array(vector, dtype=np.float32)
        norm = np.linalg.norm(vec)
        if norm == 0:
            return
        vec = vec / norm

        with self._lock:
            self._ids.append(chunk_id)
            self._texts.append(text)
            self._metadata.append(metadata or {})

            if self._matrix is None:
                self._matrix = vec.reshape(1, -1)
            else:
                self._matrix = np.vstack([self._matrix, vec.reshape(1, -1)])

    def add_batch(
        self,
        chunk_ids: list[str],
        texts: list[str],
        vectors: list[list[float]],
        metadatas: list[dict] | None = None,
    ) -> None:
        if not chunk_ids:
            return
        metas = metadatas or [{} for _ in chunk_ids]
        mat = np.array(vectors, dtype=np.float32)
        norms = np.linalg.norm(mat, axis=1, keepdims=True)
        # np.atleast_1d ensures valid_mask is always a 1-d array,
        # even when there is only 1 vector (squeeze would return scalar).
        valid_mask = np.atleast_1d(norms.squeeze() > 0)
        if not np.any(valid_mask):
            return
        mat = mat[valid_mask]
        chunk_ids = [c for c, v in zip(chunk_ids, valid_mask) if v]
        texts = [t for t, v in zip(texts, valid_mask) if v]
        metas = [m for m, v in zip(metas, valid_mask) if v]
        norms = norms[valid_mask]
        mat = mat / norms

        with self._lock:
            self._ids.extend(chunk_ids)
            self._texts.extend(texts)
            self._metadata.extend(metas)
            if self._matrix is None:
                self._matrix = mat
            else:
                self._matrix = np.vstack([self._matrix, mat])

    def search(self, query_vector: list[float], top_k: int = 5, min_score: float = 0.3) -> list[SearchHit]:
        if self._matrix is None or len(self._ids) == 0:
            return []

        qvec = np.array(query_vector, dtype=np.float32)
        norm = np.linalg.norm(qvec)
        if norm > 0:
            qvec = qvec / norm

        with self._lock:
            scores = self._matrix @ qvec
            scores = np.nan_to_num(scores, nan=0.0, posinf=0.0, neginf=0.0)
            k = min(top_k, len(self._ids))
            top_indices = np.argsort(scores)[::-1][:k]

            hits = []
            for idx in top_indices:
                s = float(scores[idx])
                if s < min_score:
                    continue
                hits.append(SearchHit(
                    chunk_id=self._ids[idx],
                    text=self._texts[idx],
                    score=s,
                    metadata=self._metadata[idx],
                ))
            return hits

    def remove_by_metadata(self, key: str, value: Any) -> int:
        """Remove all entries matching metadata[key] == value."""
        with self._lock:
            keep = [i for i, m in enumerate(self._metadata) if m.get(key) != value]
            if len(keep) == len(self._ids):
                return 0
            removed = len(self._ids) - len(keep)

            self._ids = [self._ids[i] for i in keep]
            self._texts = [self._texts[i] for i in keep]
            self._metadata = [self._metadata[i] for i in keep]
            if self._matrix is not None and keep:
                self._matrix = self._matrix[keep]
            elif not keep:
                self._matrix = None
            return removed


# Global vector store instance
knowledge_store = VectorStore()
memory_store = VectorStore()


def build_knowledge_index() -> int:
    """Load all KnowledgeDoc content from DB, chunk, embed, and index."""
    from sqlmodel import Session, select
    from server.app.models.database import KnowledgeDoc, engine

    indexed = 0
    with Session(engine) as session:
        docs = session.exec(select(KnowledgeDoc)).all()

    for doc in docs:
        if not doc.content.strip():
            continue
        chunks = _split_chunks(doc.content, chunk_size=400, overlap=50)
        if not chunks:
            continue

        vectors = embed_batch(chunks)
        chunk_ids = [f"kdoc_{doc.id}_{i}" for i in range(len(chunks))]
        metadatas = [
            {"doc_id": doc.id, "filename": doc.filename, "doc_type": doc.doc_type, "chunk_idx": i}
            for i in range(len(chunks))
        ]
        knowledge_store.add_batch(chunk_ids, chunks, vectors, metadatas)
        indexed += len(chunks)

    logger.info("Knowledge index built: %d chunks from %d documents", indexed, len(docs))
    return indexed


def build_memory_index() -> int:
    """Load all Memory entries from DB, embed, and index."""
    from sqlmodel import Session, select
    from server.app.models.database import Memory, engine

    indexed = 0
    with Session(engine) as session:
        memories = session.exec(select(Memory)).all()

    for mem in memories:
        text = f"{mem.title}\n{mem.content}"
        if not text.strip():
            continue
        vec = embed_text(text)
        memory_store.add(
            chunk_id=f"mem_{mem.id}",
            text=text,
            vector=vec,
            metadata={
                "memory_id": mem.id,
                "scope": mem.scope,
                "category": mem.category,
                "title": mem.title,
            },
        )
        indexed += 1

    logger.info("Memory index built: %d entries", indexed)
    return indexed


def index_single_doc(doc_id: str, content: str, filename: str, doc_type: str) -> int:
    """Embed and index a single newly uploaded document."""
    chunks = _split_chunks(content, chunk_size=400, overlap=50)
    if not chunks:
        return 0

    vectors = embed_batch(chunks)
    chunk_ids = [f"kdoc_{doc_id}_{i}" for i in range(len(chunks))]
    metadatas = [
        {"doc_id": doc_id, "filename": filename, "doc_type": doc_type, "chunk_idx": i}
        for i in range(len(chunks))
    ]
    knowledge_store.add_batch(chunk_ids, chunks, vectors, metadatas)
    return len(chunks)


def index_single_memory(mem_id: str, title: str, content: str, scope: str, category: str) -> None:
    """Embed and index a single memory entry."""
    text = f"{title}\n{content}"
    vec = embed_text(text)
    memory_store.add(
        chunk_id=f"mem_{mem_id}",
        text=text,
        vector=vec,
        metadata={
            "memory_id": mem_id,
            "scope": scope,
            "category": category,
            "title": title,
        },
    )


def semantic_search(query: str, top_k: int = 5, search_type: str = "all") -> list[SearchHit]:
    """High-level semantic search across knowledge docs and/or memories."""
    query_vec = embed_text(query)
    hits: list[SearchHit] = []

    if search_type in ("all", "knowledge"):
        hits.extend(knowledge_store.search(query_vec, top_k=top_k))
    if search_type in ("all", "memory"):
        hits.extend(memory_store.search(query_vec, top_k=top_k))

    hits.sort(key=lambda h: h.score, reverse=True)
    return hits[:top_k]


def _split_chunks(text: str, chunk_size: int = 400, overlap: int = 50) -> list[str]:
    """Split text into overlapping chunks, preferring paragraph boundaries."""
    if len(text) <= chunk_size:
        return [text] if text.strip() else []

    paragraphs = text.split("\n\n")
    chunks: list[str] = []
    current = ""

    for para in paragraphs:
        if len(current) + len(para) + 2 <= chunk_size:
            current = current + "\n\n" + para if current else para
        else:
            if current.strip():
                chunks.append(current.strip())
            if len(para) > chunk_size:
                for i in range(0, len(para), chunk_size - overlap):
                    piece = para[i : i + chunk_size]
                    if piece.strip():
                        chunks.append(piece.strip())
                current = ""
            else:
                current = para

    if current.strip():
        chunks.append(current.strip())

    return chunks
