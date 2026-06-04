"""Pydantic v2 request DTOs. Responses return SQLModel ORM objects directly."""
from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class MethodologyIn(BaseModel):
    """Create/update a methodology (the 7 slots + light metadata)."""
    name: str
    summary: str = ""
    trigger: dict = Field(default_factory=dict)
    principles: list = Field(default_factory=list)
    steps: list = Field(default_factory=list)
    gates: list = Field(default_factory=list)
    anti_patterns: list = Field(default_factory=list)
    artifacts: list = Field(default_factory=list)
    metrics: list = Field(default_factory=list)
    # ── thick-asset fields (Phase A) ──
    applicability: dict = Field(default_factory=dict)
    examples: list = Field(default_factory=list)
    provenance: dict = Field(default_factory=dict)
    related: list = Field(default_factory=list)
    tags: list = Field(default_factory=list)
    status: Optional[str] = None  # draft | published | archived
    edit_note: str = ""           # stored on the version snapshot when updating


class SuggestIn(BaseModel):
    raw_input: str
    top_k: int = 3


class RunCreateIn(BaseModel):
    methodology_id: str
    raw_input: str
    title: str = ""


class GateAnswerIn(BaseModel):
    gate_id: str
    answer: str


class OutcomeIn(BaseModel):
    usefulness: int = 0          # 1-5
    adopted: bool = False
    metric_values: dict[str, Any] = Field(default_factory=dict)
    note: str = ""


# ── Distillation ──
class DistillMaterialsIn(BaseModel):
    materials: list[str]
    hint: str = ""
    topic: str = ""


class InterviewStartIn(BaseModel):
    topic: str
    expert_name: str = ""


class InterviewAnswerIn(BaseModel):
    answer: str


# ── Lens / Advisor / Bindings ──
class LensIn(BaseModel):
    methodology_id: str
    material: str
    title: str = ""


class AdvisorStartIn(BaseModel):
    methodology_id: str
    topic: str = ""


class AdvisorMessageIn(BaseModel):
    content: str


class BindingIn(BaseModel):
    methodology_id: str
