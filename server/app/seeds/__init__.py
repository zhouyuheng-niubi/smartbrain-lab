"""Built-in seed methodologies + idempotent loader."""
from __future__ import annotations

from sqlmodel import Session, select

from server.app.models.database import Methodology, engine
from server.app.seeds import (
    adr_tech_decision,
    amazon_working_backwards,
    code_review,
    first_principles,
    five_whys_postmortem,
    musk_five_step,
    pre_mortem,
    requirement_decomposition,
    rice_prioritization,
)

# Order = library display order (most generally useful first).
ALL_SEEDS: list[dict] = [
    requirement_decomposition.METHODOLOGY,
    first_principles.METHODOLOGY,
    musk_five_step.METHODOLOGY,
    amazon_working_backwards.METHODOLOGY,
    rice_prioritization.METHODOLOGY,
    five_whys_postmortem.METHODOLOGY,
    pre_mortem.METHODOLOGY,
    adr_tech_decision.METHODOLOGY,
    code_review.METHODOLOGY,
]

# slot fields that default to {} vs []
_DICT_SLOTS = ("trigger", "applicability", "provenance")
_LIST_SLOTS = ("principles", "steps", "gates", "anti_patterns", "artifacts",
               "metrics", "examples", "related", "tags")
_ALL_SLOTS = _DICT_SLOTS + _LIST_SLOTS


def _slot_value(seed: dict, slot: str):
    return seed.get(slot, {} if slot in _DICT_SLOTS else [])


def seed_builtin(session: Session | None = None) -> dict:
    """Upsert all built-in methodologies by slug. Idempotent.

    Existing rows have their content refreshed but keep id / run_count /
    avg_artifact_score / created_at (so usage stats survive re-seeding).
    """
    own_session = session is None
    session = session or Session(engine)
    created, updated = 0, 0
    try:
        for seed in ALL_SEEDS:
            prov = dict(seed.get("provenance", {}))
            prov.setdefault("source_type", "builtin")
            existing = session.exec(
                select(Methodology).where(Methodology.slug == seed["slug"])
            ).first()
            if existing:
                existing.name = seed["name"]
                existing.summary = seed.get("summary", "")
                for slot in _ALL_SLOTS:
                    setattr(existing, slot, _slot_value(seed, slot))
                existing.provenance = prov
                existing.origin = "builtin"
                existing.status = "published"
                session.add(existing)
                updated += 1
            else:
                fields = {slot: _slot_value(seed, slot) for slot in _ALL_SLOTS}
                fields["provenance"] = prov
                session.add(Methodology(
                    slug=seed["slug"],
                    name=seed["name"],
                    summary=seed.get("summary", ""),
                    origin="builtin",
                    status="published",
                    **fields,
                ))
                created += 1
        session.commit()
    finally:
        if own_session:
            session.close()
    return {"created": created, "updated": updated, "total": len(ALL_SEEDS)}
