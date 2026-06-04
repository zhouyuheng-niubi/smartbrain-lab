"""Lens API — diagnose an existing material through a methodology's lens."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from server.app.engine import lens
from server.app.models.database import LensReview, get_session
from server.app.schemas.schemas import LensIn

router = APIRouter(prefix="/api/lens", tags=["lens"])


@router.post("")
def create_lens(payload: LensIn, session: Session = Depends(get_session)) -> dict:
    if not payload.material.strip():
        raise HTTPException(status_code=400, detail="material 不能为空")
    try:
        review = lens.diagnose(session, payload.methodology_id, payload.material, payload.title)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"review": review}


@router.get("")
def list_lens(
    methodology_id: str | None = Query(default=None),
    session: Session = Depends(get_session),
) -> dict:
    stmt = select(LensReview)
    if methodology_id:
        stmt = stmt.where(LensReview.methodology_id == methodology_id)
    rows = list(session.exec(stmt).all())
    rows.sort(key=lambda r: r.created_at, reverse=True)
    return {"reviews": rows, "total": len(rows)}


@router.get("/{review_id}")
def get_lens(review_id: str, session: Session = Depends(get_session)) -> dict:
    r = session.get(LensReview, review_id)
    if not r:
        raise HTTPException(status_code=404, detail="lens review not found")
    return {"review": r}
