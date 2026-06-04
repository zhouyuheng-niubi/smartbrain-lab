"""Methodology CRUD + semantic suggest + OPC export seam."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from server.app.models.database import (
    Methodology,
    MethodologyVersion,
    get_session,
)
from server.app.schemas.schemas import MethodologyIn, SuggestIn

router = APIRouter(prefix="/api/methodologies", tags=["methodologies"])

_SLOTS = ("trigger", "principles", "steps", "gates", "anti_patterns", "artifacts", "metrics",
          "applicability", "examples", "provenance", "related")


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _snapshot(m: Methodology) -> dict:
    snap = {"name": m.name, "summary": m.summary, "tags": m.tags}
    for slot in _SLOTS:
        snap[slot] = getattr(m, slot)
    return snap


def to_agent_markdown(m: Methodology) -> str:
    """OPC seam: render a methodology as context injectable into an agent prompt."""
    lines = [f"## 方法论：{m.name}"]
    if m.summary:
        lines.append(m.summary)
    if m.principles:
        lines.append("\n### 内核原则")
        for p in m.principles:
            lines.append(f"- **{p.get('title', '')}**：{p.get('detail', '')}")
    if m.steps:
        lines.append("\n### 执行步骤")
        for s in m.steps:
            lines.append(f"- {s.get('name', '')}：{s.get('guidance', '')}")
    if m.gates:
        lines.append("\n### 决策闸门（每步必须回答）")
        for g in m.gates:
            lines.append(f"- {g.get('question', '')}")
    if m.anti_patterns:
        lines.append("\n### 反模式（务必避免）")
        for a in m.anti_patterns:
            lines.append(f"- {a.get('name', '')}：{a.get('symptom', '')}")
    appl = m.applicability or {}
    if appl.get("when_not_to_use"):
        lines.append("\n### 不适用（什么时候别用它）")
        for x in appl["when_not_to_use"]:
            lines.append(f"- {x}")
    return "\n".join(lines)


@router.get("")
def list_methodologies(
    origin: str | None = Query(default=None),
    status: str | None = Query(default=None),
    tag: str | None = Query(default=None),
    q: str | None = Query(default=None),
    session: Session = Depends(get_session),
) -> dict:
    stmt = select(Methodology)
    if origin:
        stmt = stmt.where(Methodology.origin == origin)
    if status:
        stmt = stmt.where(Methodology.status == status)
    rows = list(session.exec(stmt).all())

    if tag:
        rows = [m for m in rows if tag in (m.tags or [])]
    if q:
        ql = q.lower()
        rows = [m for m in rows if ql in m.name.lower() or ql in (m.summary or "").lower()]

    rows.sort(key=lambda m: (m.origin != "builtin", -m.run_count, m.name))
    return {"methodologies": rows, "total": len(rows)}


@router.post("")
def create_methodology(payload: MethodologyIn, session: Session = Depends(get_session)) -> Methodology:
    slug = "custom-" + payload.name.strip().lower().replace(" ", "-")[:40] + "-" + _now().strftime("%H%M%S")
    m = Methodology(
        slug=slug,
        name=payload.name,
        summary=payload.summary,
        trigger=payload.trigger,
        principles=payload.principles,
        steps=payload.steps,
        gates=payload.gates,
        anti_patterns=payload.anti_patterns,
        artifacts=payload.artifacts,
        metrics=payload.metrics,
        applicability=payload.applicability,
        examples=payload.examples,
        provenance=payload.provenance or {"source_type": "manual"},
        related=payload.related,
        tags=payload.tags,
        origin="custom",
        status=payload.status or "published",
    )
    session.add(m)
    session.commit()
    session.refresh(m)
    return m


@router.get("/{methodology_id}")
def get_methodology(methodology_id: str, session: Session = Depends(get_session)) -> Methodology:
    m = session.get(Methodology, methodology_id)
    if not m:
        raise HTTPException(status_code=404, detail="methodology not found")
    return m


@router.put("/{methodology_id}")
def update_methodology(
    methodology_id: str, payload: MethodologyIn, session: Session = Depends(get_session)
) -> Methodology:
    m = session.get(Methodology, methodology_id)
    if not m:
        raise HTTPException(status_code=404, detail="methodology not found")

    # snapshot current version before mutating
    session.add(MethodologyVersion(
        methodology_id=m.id, version=m.version, snapshot=_snapshot(m), note=payload.edit_note,
    ))

    m.name = payload.name
    m.summary = payload.summary
    m.trigger = payload.trigger
    m.principles = payload.principles
    m.steps = payload.steps
    m.gates = payload.gates
    m.anti_patterns = payload.anti_patterns
    m.artifacts = payload.artifacts
    m.metrics = payload.metrics
    m.applicability = payload.applicability
    m.examples = payload.examples
    if payload.provenance:
        m.provenance = payload.provenance
    m.related = payload.related
    m.tags = payload.tags
    if payload.status:
        m.status = payload.status
    m.version += 1
    m.updated_at = _now()
    session.add(m)
    session.commit()
    session.refresh(m)
    return m


@router.delete("/{methodology_id}")
def archive_methodology(methodology_id: str, session: Session = Depends(get_session)) -> dict:
    m = session.get(Methodology, methodology_id)
    if not m:
        raise HTTPException(status_code=404, detail="methodology not found")
    if m.origin == "builtin":
        raise HTTPException(status_code=400, detail="内置方法论不可删除（可归档自定义副本）")
    m.status = "archived"
    m.updated_at = _now()
    session.add(m)
    session.commit()
    return {"ok": True, "id": m.id, "status": m.status}


@router.get("/{methodology_id}/export")
def export_methodology(
    methodology_id: str,
    format: str = Query(default="agent_md"),
    session: Session = Depends(get_session),
) -> dict:
    """OPC seam — export a methodology as agent-injectable context."""
    m = session.get(Methodology, methodology_id)
    if not m:
        raise HTTPException(status_code=404, detail="methodology not found")
    if format != "agent_md":
        raise HTTPException(status_code=400, detail="unsupported format")
    return {"id": m.id, "format": "agent_md", "content": to_agent_markdown(m)}


@router.post("/{methodology_id}/fork")
def fork_methodology(methodology_id: str, session: Session = Depends(get_session)) -> Methodology:
    """本地化：把一套方法论（通常是大厂内置）克隆成可改造的'我们公司版'草稿。"""
    parent = session.get(Methodology, methodology_id)
    if not parent:
        raise HTTPException(status_code=404, detail="methodology not found")
    provenance = {
        "source_type": "manual",
        "origin": (parent.provenance or {}).get("origin", ""),
        "note": f"fork 自「{parent.name}」",
        "forked_from": parent.slug,
    }
    clone = Methodology(
        slug=f"custom-{parent.slug}-" + _now().strftime("%H%M%S%f"),
        name=f"{parent.name}（我们公司版）",
        summary=parent.summary,
        trigger=parent.trigger, principles=parent.principles, steps=parent.steps, gates=parent.gates,
        anti_patterns=parent.anti_patterns, artifacts=parent.artifacts, metrics=parent.metrics,
        applicability=parent.applicability, examples=parent.examples, provenance=provenance,
        related=parent.related, tags=parent.tags,
        origin="custom", status="draft",
    )
    session.add(clone)
    session.commit()
    session.refresh(clone)
    return clone


@router.post("/suggest")
def suggest(payload: SuggestIn, session: Session = Depends(get_session)) -> dict:
    """Semantic 'auto-surfacing' — which methodologies fit this input?"""
    try:
        from server.app.engine.methodology_index import suggest_methodologies
        hits = suggest_methodologies(payload.raw_input, top_k=payload.top_k)
        if hits:
            return {"suggestions": hits, "mode": "semantic"}
    except Exception:
        pass

    # keyword fallback (works without embedding API key)
    ql = payload.raw_input.lower()
    rows = list(session.exec(select(Methodology).where(Methodology.status == "published")).all())
    scored = []
    for m in rows:
        kws = (m.trigger or {}).get("keywords", []) if isinstance(m.trigger, dict) else []
        score = sum(1 for k in kws if k.lower() in ql)
        if score:
            scored.append({"id": m.id, "slug": m.slug, "name": m.name, "score": float(score)})
    scored.sort(key=lambda x: x["score"], reverse=True)
    return {"suggestions": scored[: payload.top_k], "mode": "keyword"}
