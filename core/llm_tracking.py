# ╔══════════════════════════════════════════════════════════════════════════╗
# ║ VENDORED FROM bi-dashboard-demo@6dc89a0 (multi_agent_dev/tracking.py)      ║
# ║ on 2026-06-04. Only edit blocks marked VENDOR-PATCH. See core/VENDOR.md.   ║
# ╚══════════════════════════════════════════════════════════════════════════╝
"""LLM usage tracking — records token / cost for every API call.

Two invocation modes:
  - create_and_invoke(): blocking call, full response at once
  - create_and_stream(): streaming call, pushes delta chunks via emit_fn
Both modes record usage to the tracker after completion.
Includes exponential-backoff retry for transient LLM provider errors.
"""

from __future__ import annotations

import logging
import os
import random
import threading
import time
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Callable

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult

if TYPE_CHECKING:
    from langchain_core.messages import BaseMessage

logger = logging.getLogger(__name__)

# ── Budget configuration ───────────────────────────────────────────────────
# Default to disabled: the platform should surface actual usage, not impose a budget gate
# unless an operator explicitly opts in via environment variables.
PROJECT_TOKEN_BUDGET = <REDACTED_CREDENTIAL>
# Exceeding PROJECT_TOKEN_BUDGET is observational by default; set enforce=1 to opt into a hard stop.
PROJECT_TOKEN_BUDGET_ENFORCE = <REDACTED_CREDENTIAL>
    "1", "true", "yes", "on",
}
PROJECT_TOKEN_BUDGET_WARNING_PERCENT = <REDACTED_CREDENTIAL>
    1, min(100, int(os.getenv("PROJECT_TOKEN_BUDGET_WARNING_PERCENT", "80")))
)

_soft_budget_warned: set[str] = set()


class TokenBudgetExceeded(Exception):
    """Raised when a project has consumed its token budget."""

    def __init__(self, project_id: str, used: int, budget: int):
        self.project_id = project_id
        self.used = used
        self.budget = budget
        super().__init__(
            f"Project {project_id} token budget exceeded: {used:,}/{budget:,} tokens used"
        )


def check_budget(project_id: str) -> None:
    """Enforce or warn on token budget before each LLM call (see PROJECT_TOKEN_BUDGET_ENFORCE)."""
    if PROJECT_TOKEN_BUDGET <= 0:
        return  # Budget disabled

    try:
        from sqlmodel import Session, func, select
        from server.app.models.database import LlmUsage, engine

        with Session(engine) as session:
            total = session.exec(
                select(func.coalesce(func.sum(LlmUsage.total_tokens), 0)).where(
                    LlmUsage.run_id == project_id  # VENDOR-PATCH: project_id -> run_id
                )
            ).one()
            used = int(total)  # type: ignore[arg-type]
    except Exception:
        # If DB query fails, don't block. Budget is soft protection.
        return

    if used >= PROJECT_TOKEN_BUDGET:
        if PROJECT_TOKEN_BUDGET_ENFORCE:
            raise TokenBudgetExceeded(project_id, used, PROJECT_TOKEN_BUDGET)
        if project_id not in _soft_budget_warned:
            _soft_budget_warned.add(project_id)
            logger.warning(
                "Project %s over token budget (soft mode, calls continue): %s/%s",
                project_id,
                used,
                PROJECT_TOKEN_BUDGET,
            )


def _month_start_utc() -> datetime:
    now = datetime.now(timezone.utc)
    return datetime(now.year, now.month, 1, tzinfo=timezone.utc)


def get_budget_status(project_id: str) -> dict:
    """Return budget consumption status for a project (includes calendar-month rollup)."""
    used = 0
    monthly_tokens = 0
    monthly_estimated_cost = 0.0
    try:
        from sqlmodel import Session, func, select
        from server.app.models.database import LlmUsage, engine

        month_start = _month_start_utc()
        with Session(engine) as session:
            total = session.exec(
                select(func.coalesce(func.sum(LlmUsage.total_tokens), 0)).where(
                    LlmUsage.run_id == project_id  # VENDOR-PATCH: project_id -> run_id
                )
            ).one()
            used = int(total)  # type: ignore[arg-type]

            rows = session.exec(
                select(LlmUsage).where(
                    LlmUsage.run_id == project_id,  # VENDOR-PATCH
                    LlmUsage.created_at >= month_start,  # type: ignore[operator]
                )
            ).all()
            for r in rows:
                monthly_tokens += r.total_tokens
                monthly_estimated_cost += r.estimated_cost
    except Exception:
        used = 0

    budget = PROJECT_TOKEN_BUDGET
    pct = round(used / budget * 100, 1) if budget > 0 else 0
    warn_at = PROJECT_TOKEN_BUDGET_WARNING_PERCENT
    return {
        "project_id": project_id,
        "used_tokens": used,
        "budget_tokens": budget,
        "remaining_tokens": max(0, budget - used),
        "usage_percent": pct,
        "budget_enabled": budget > 0,
        "budget_enforce": PROJECT_TOKEN_BUDGET_ENFORCE,
        "warning_percent": warn_at,
        "near_limit": budget > 0 and pct >= warn_at,
        "monthly_tokens": monthly_tokens,
        "monthly_estimated_cost": round(monthly_estimated_cost, 6),
    }

# ── Retry configuration ────────────────────────────────────────────────────
MAX_RETRIES = int(os.getenv("LLM_MAX_RETRIES", "3"))
RETRY_BASE_DELAY = float(os.getenv("LLM_RETRY_BASE_DELAY", "2.0"))
RETRY_MAX_DELAY = float(os.getenv("LLM_RETRY_MAX_DELAY", "30.0"))

RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


def _is_retryable(exc: Exception) -> bool:
    """Decide whether an LLM call exception warrants a retry."""
    exc_str = str(exc).lower()

    # httpx / openai style: "status_code=429"
    for code in RETRYABLE_STATUS_CODES:
        if f"status_code={code}" in exc_str or f"status code: {code}" in exc_str:
            return True

    # Common transient patterns
    retryable_patterns = [
        "rate limit",
        "rate_limit",
        "too many requests",
        "server error",
        "bad gateway",
        "service unavailable",
        "gateway timeout",
        "connection error",
        "connection reset",
        "connection refused",
        "timed out",
        "timeout",
        "temporary failure",
        "temporarily unavailable",
    ]
    return any(p in exc_str for p in retryable_patterns)


def _backoff_delay(attempt: int) -> float:
    """Exponential backoff with jitter."""
    delay = min(RETRY_BASE_DELAY * (2 ** attempt), RETRY_MAX_DELAY)
    return delay + random.uniform(0, delay * 0.1)


@dataclass
class UsageRecord:
    agent_role: str
    provider: str
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    duration_ms: int = 0
    estimated_cost: float = 0.0
    timestamp: float = field(default_factory=time.time)
    # OPC stage: "research" | "build" | "promote" | "" (legacy / unknown)
    stage: str = ""


# ---------------------------------------------------------------------------
# OPC: per-call stage propagation via ContextVar (Task 15.1)
# ---------------------------------------------------------------------------
from contextvars import ContextVar  # noqa: E402

_current_stage: ContextVar[str] = ContextVar("opc_current_stage", default="")


def set_current_stage(stage: str) -> "object":
    """Set the per-task current stage; returns a token usable with ``reset_current_stage``."""
    return _current_stage.set(stage or "")


def get_current_stage() -> str:
    return _current_stage.get("")


def reset_current_stage(token="<REDACTED_CREDENTIAL>") -> None:
    try:
        _current_stage.reset(token)  # type: ignore[arg-type]
    except Exception:
        pass


class UsageTracker:
    """Thread-safe per-project usage buffer."""

    def __init__(self) -> None:
        self._store: dict[str, list[UsageRecord]] = {}
        self._lock = threading.Lock()

    def record(
        self,
        project_id: str,
        agent_role: str,
        provider: str,
        model: str,
        response: "BaseMessage",
        duration_ms: int,
        price_prompt_per_1k: float = 0.0,
        price_completion_per_1k: float = 0.0,
    ) -> UsageRecord:
        usage_meta: dict = {}
        if hasattr(response, "response_metadata"):
            usage_meta = response.response_metadata.get("token_usage", {}) or {}

        prompt_tokens = usage_meta.get("prompt_tokens", 0) or 0
        completion_tokens = usage_meta.get("completion_tokens", 0) or 0
        total_tokens = prompt_tokens + completion_tokens

        estimated_cost = (
            prompt_tokens / 1000.0 * price_prompt_per_1k
            + completion_tokens / 1000.0 * price_completion_per_1k
        )

        rec = UsageRecord(
            agent_role=agent_role,
            provider=provider,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            duration_ms=duration_ms,
            estimated_cost=round(estimated_cost, 6),
            stage=_current_stage.get(""),
        )

        with self._lock:
            self._store.setdefault(project_id, []).append(rec)

        # VENDOR-PATCH: this product has no `project` table, so persist each record
        # immediately to the local LlmUsage table keyed by run_id (the value passed
        # in as `project_id`). Best-effort: never break the LLM call on a DB error.
        _persist_usage(project_id, rec)
        return rec

    def flush(self, project_id: str) -> list[UsageRecord]:
        """Return and clear all buffered records for *project_id*."""
        with self._lock:
            return self._store.pop(project_id, [])

    def peek(self, project_id: str) -> list[UsageRecord]:
        with self._lock:
            return list(self._store.get(project_id, []))


def _persist_usage(run_id: str, rec: "UsageRecord") -> None:
    """VENDOR-PATCH: write one usage row to this repo's LlmUsage table.

    bi-dashboard buffered records in memory and flushed them elsewhere against a
    project foreign key. This product has no project table, so we persist
    immediately keyed by run_id. Best-effort — swallow all errors.
    """
    try:
        from sqlmodel import Session
        from server.app.models.database import LlmUsage, engine

        with Session(engine) as session:
            session.add(LlmUsage(
                run_id=run_id or None,
                agent_role=rec.agent_role,
                provider=rec.provider,
                model=rec.model,
                prompt_tokens=rec.prompt_tokens,
                completion_tokens=rec.completion_tokens,
                total_tokens=rec.total_tokens,
                duration_ms=rec.duration_ms,
                estimated_cost=rec.estimated_cost,
            ))
            session.commit()
    except Exception:
        pass


usage_tracker = UsageTracker()


def _get_provider_info(agent_role: str):
    from core.llm_config import (  # VENDOR-PATCH: multi_agent_dev.config -> core.llm_config
        get_model_for_agent,
        get_provider_config,
        get_provider_for_agent,
    )
    provider_name = get_provider_for_agent(agent_role)
    cfg = get_provider_config(provider_name)
    resolved_model = get_model_for_agent(agent_role) or cfg.default_model
    return provider_name, cfg, resolved_model


def create_and_invoke(
    messages: list,
    *,
    project_id: str,
    agent_role: str,
    temperature: float = 0.7,
    max_tokens: int = 8192,
    emit_fn: Callable | None = None,
) -> "BaseMessage":
    """Blocking LLM call with usage tracking, budget guard, and automatic retry."""
    from core.llm_config import get_llm  # VENDOR-PATCH

    check_budget(project_id)

    provider_name, cfg, resolved_model = _get_provider_info(agent_role)
    llm = get_llm(agent_role=agent_role, temperature=temperature, max_tokens=max_tokens)

    last_exc: Exception | None = None

    for attempt in range(MAX_RETRIES + 1):
        try:
            start = time.time()
            response = llm.invoke(messages)
            duration_ms = int((time.time() - start) * 1000)

            finish_reason = (
                response.response_metadata.get("finish_reason")
                if hasattr(response, "response_metadata") and response.response_metadata
                else None
            )
            if finish_reason == "length":
                logger.warning(
                    "⚠️ Agent '%s' output TRUNCATED (finish_reason=length, max_tokens=%d)",
                    agent_role, max_tokens,
                )

            usage_tracker.record(
                project_id=project_id,
                agent_role=agent_role,
                provider=provider_name,
                model=resolved_model,
                response=response,
                duration_ms=duration_ms,
                price_prompt_per_1k=cfg.price_prompt_per_1k,
                price_completion_per_1k=cfg.price_completion_per_1k,
            )

            # ── Auto-continuation when output is truncated ──────────
            MAX_CONTINUATIONS = 2
            if finish_reason == "length" and response.content and response.content.strip():
                from langchain_core.messages import AIMessage, HumanMessage as _HM
                full_content = response.content
                for cont_i in range(1, MAX_CONTINUATIONS + 1):
                    logger.info(
                        "Auto-continuing (invoke) agent '%s' (continuation %d/%d, %d chars)",
                        agent_role, cont_i, MAX_CONTINUATIONS, len(full_content),
                    )
                    check_budget(project_id)

                    cont_messages = list(messages) + [
                        AIMessage(content=full_content),
                        _HM(content=(
                            "你的上一次回复因为长度限制被截断了。"
                            "请从你上次停止的位置**精确地继续输出**，"
                            "不要重复已经生成的内容，不要添加开头说明，"
                            "直接从断点处继续。"
                        )),
                    ]

                    try:
                        cont_start = time.time()
                        cont_resp = llm.invoke(cont_messages)
                        cont_dur = int((time.time() - cont_start) * 1000)

                        usage_tracker.record(
                            project_id=project_id,
                            agent_role=agent_role,
                            provider=provider_name,
                            model=resolved_model,
                            response=cont_resp,
                            duration_ms=cont_dur,
                            price_prompt_per_1k=cfg.price_prompt_per_1k,
                            price_completion_per_1k=cfg.price_completion_per_1k,
                        )

                        full_content += (cont_resp.content or "")
                        cont_finish = (
                            cont_resp.response_metadata.get("finish_reason")
                            if hasattr(cont_resp, "response_metadata") and cont_resp.response_metadata
                            else None
                        )
                        if cont_finish != "length":
                            break
                    except Exception as cont_exc:
                        logger.warning("Continuation %d (invoke) failed for agent %s: %s", cont_i, agent_role, cont_exc)
                        break

                response = AIMessage(content=full_content)
                logger.info("Agent '%s' final invoke output after continuation: %d chars", agent_role, len(full_content))

            return response

        except Exception as exc:
            last_exc = exc
            if attempt < MAX_RETRIES and _is_retryable(exc):
                delay = _backoff_delay(attempt)
                logger.warning(
                    "LLM invoke retry %d/%d for agent %s: %s (backoff %.1fs)",
                    attempt + 1, MAX_RETRIES, agent_role, exc, delay,
                )
                if emit_fn:
                    try:
                        emit_fn({
                            "type": "llm_retry",
                            "agent": agent_role,
                            "attempt": attempt + 1,
                            "max_retries": MAX_RETRIES,
                            "delay_seconds": round(delay, 1),
                            "error": str(exc)[:200],
                        })
                    except Exception:
                        pass
                time.sleep(delay)
            else:
                break

    raise last_exc  # type: ignore[misc]


class UsageTrackerCallbackHandler(BaseCallbackHandler):
    def __init__(self, project_id: str, agent_role: str):
        self.project_id = project_id
        self.agent_role = agent_role
        self.start_times: dict[str, float] = {}
        
    def on_llm_start(self, serialized: dict[str, Any], prompts: list[str], **kwargs: Any) -> Any:
        run_id = str(kwargs.get("run_id", ""))
        self.start_times[run_id] = time.time()
        
    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> Any:
        run_id = str(kwargs.get("run_id", ""))
        start_time = self.start_times.pop(run_id, time.time())
        duration_ms = int((time.time() - start_time) * 1000)
        
        provider_name, cfg, resolved_model = _get_provider_info(self.agent_role)
        
        # We process token usage if it exists in the LLM output
        llm_output = response.llm_output or {}
        token_usage = llm_output.get("token_usage", {})
        
        # Create a dummy response object to pass to the tracker since record() expects a BaseMessage
        class DummyResponse:
            def __init__(self, usage):
                self.response_metadata = {"token_usage": usage}
                
        dummy_resp = DummyResponse(token_usage)
        
        usage_tracker.record(
            project_id=self.project_id,
            agent_role=self.agent_role,
            provider=provider_name,
            model=resolved_model,  
            response=dummy_resp,
            duration_ms=duration_ms,
            price_prompt_per_1k=cfg.price_prompt_per_1k,
            price_completion_per_1k=cfg.price_completion_per_1k,
        )


def get_tracker_callback(project_id: str, agent_role: str) -> BaseCallbackHandler:
    """Returns a Langchain callback handler to trace token usage for an agent."""
    return UsageTrackerCallbackHandler(project_id, agent_role)


def create_and_stream(
    messages: list,
    *,
    project_id: str,
    agent_role: str,
    temperature: float = 0.7,
    max_tokens: int = 8192,
    emit_fn: Callable | None = None,
) -> "BaseMessage":
    """Streaming LLM call with budget guard and automatic retry on transient failures."""
    from langchain_core.messages import AIMessage
    from core.llm_config import get_llm  # VENDOR-PATCH

    check_budget(project_id)

    provider_name, cfg, resolved_model = _get_provider_info(agent_role)
    llm = get_llm(
        agent_role=agent_role,
        temperature=temperature,
        max_tokens=max_tokens,
        stream_usage=True,
    )

    last_exc: Exception | None = None

    for attempt in range(MAX_RETRIES + 1):
        if emit_fn:
            try:
                emit_fn({"type": "stream_start", "agent": agent_role})
            except Exception:
                pass

        content_parts: list[str] = []
        last_chunk = None
        start = time.time()

        try:
            for chunk in llm.stream(messages):
                delta = getattr(chunk, "content", "") or ""
                if delta:
                    content_parts.append(delta)
                    if emit_fn:
                        try:
                            emit_fn({"type": "stream_chunk", "agent": agent_role, "content": delta})
                        except Exception:
                            pass
                last_chunk = chunk

            duration_ms = int((time.time() - start) * 1000)
            full_content = "".join(content_parts)

            response = AIMessage(content=full_content)
            if last_chunk is not None:
                meta = getattr(last_chunk, "response_metadata", None) or {}
                if meta:
                    response.response_metadata = meta

            finish_reason = (
                response.response_metadata.get("finish_reason")
                if hasattr(response, "response_metadata") and response.response_metadata
                else None
            )
            if finish_reason == "length":
                logger.warning(
                    "⚠️ Agent '%s' output TRUNCATED (finish_reason=length, max_tokens=%d, output_chars=%d). "
                    "Consider increasing max_tokens or simplifying the prompt.",
                    agent_role, max_tokens, len(full_content),
                )
                if emit_fn:
                    try:
                        emit_fn({
                            "type": "output_truncated",
                            "agent": agent_role,
                            "max_tokens": max_tokens,
                            "output_chars": len(full_content),
                        })
                    except Exception:
                        pass

            usage_tracker.record(
                project_id=project_id,
                agent_role=agent_role,
                provider=provider_name,
                model=resolved_model,
                response=response,
                duration_ms=duration_ms,
                price_prompt_per_1k=cfg.price_prompt_per_1k,
                price_completion_per_1k=cfg.price_completion_per_1k,
            )

            # ── Auto-continuation when output is truncated ──────────
            MAX_CONTINUATIONS = 2
            if finish_reason == "length" and full_content.strip():
                for cont_i in range(1, MAX_CONTINUATIONS + 1):
                    logger.info(
                        "Auto-continuing agent '%s' (continuation %d/%d, accumulated %d chars)",
                        agent_role, cont_i, MAX_CONTINUATIONS, len(full_content),
                    )
                    if emit_fn:
                        try:
                            emit_fn({
                                "type": "stream_continue",
                                "agent": agent_role,
                                "continuation": cont_i,
                            })
                        except Exception:
                            pass

                    check_budget(project_id)

                    from langchain_core.messages import HumanMessage as _HM
                    cont_messages = list(messages) + [
                        AIMessage(content=full_content),
                        _HM(content=(
                            "你的上一次回复因为长度限制被截断了。"
                            "请从你上次停止的位置**精确地继续输出**，"
                            "不要重复已经生成的内容，不要添加开头说明，"
                            "直接从断点处继续。"
                        )),
                    ]
                    cont_parts: list[str] = []
                    cont_last_chunk = None
                    cont_start = time.time()

                    try:
                        for chunk in llm.stream(cont_messages):
                            delta = getattr(chunk, "content", "") or ""
                            if delta:
                                cont_parts.append(delta)
                                if emit_fn:
                                    try:
                                        emit_fn({"type": "stream_chunk", "agent": agent_role, "content": delta})
                                    except Exception:
                                        pass
                            cont_last_chunk = chunk

                        cont_duration = int((time.time() - cont_start) * 1000)
                        cont_text = "".join(cont_parts)
                        full_content += cont_text

                        cont_response = AIMessage(content=cont_text)
                        if cont_last_chunk is not None:
                            cont_meta = getattr(cont_last_chunk, "response_metadata", None) or {}
                            if cont_meta:
                                cont_response.response_metadata = cont_meta

                        usage_tracker.record(
                            project_id=project_id,
                            agent_role=agent_role,
                            provider=provider_name,
                            model=resolved_model,
                            response=cont_response,
                            duration_ms=cont_duration,
                            price_prompt_per_1k=cfg.price_prompt_per_1k,
                            price_completion_per_1k=cfg.price_completion_per_1k,
                        )

                        cont_finish = (
                            cont_response.response_metadata.get("finish_reason")
                            if hasattr(cont_response, "response_metadata") and cont_response.response_metadata
                            else None
                        )
                        if cont_finish != "length":
                            break  # done — natural stop
                    except Exception as cont_exc:
                        logger.warning("Continuation %d failed for agent %s: %s", cont_i, agent_role, cont_exc)
                        break

                response = AIMessage(content=full_content)
                logger.info(
                    "Agent '%s' final output after continuation: %d chars",
                    agent_role, len(full_content),
                )

            return response

        except Exception as exc:
            last_exc = exc
            if attempt < MAX_RETRIES and _is_retryable(exc):
                delay = _backoff_delay(attempt)
                logger.warning(
                    "LLM stream retry %d/%d for agent %s: %s (backoff %.1fs)",
                    attempt + 1, MAX_RETRIES, agent_role, exc, delay,
                )
                if emit_fn:
                    try:
                        emit_fn({
                            "type": "llm_retry",
                            "agent": agent_role,
                            "attempt": attempt + 1,
                            "max_retries": MAX_RETRIES,
                            "delay_seconds": round(delay, 1),
                            "error": str(exc)[:200],
                        })
                    except Exception:
                        pass
                time.sleep(delay)
            else:
                logger.warning("Streaming failed for agent %s: %s", agent_role, exc)
                raise

    raise last_exc  # type: ignore[misc]
