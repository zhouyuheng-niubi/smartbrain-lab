# ╔══════════════════════════════════════════════════════════════════════════╗
# ║ VENDORED FROM bi-dashboard-demo@6dc89a0 (multi_agent_dev/config.py)        ║
# ║ on 2026-06-04, unmodified. See core/VENDOR.md.                             ║
# ╚══════════════════════════════════════════════════════════════════════════╝
"""Multi-provider LLM configuration.

Supports CodingPlan / DeepSeek / SiliconFlow with per-agent provider + model override.
- Switch provider: change PROVIDER_DEFAULT in .env or call switch_provider() at runtime
- Per-agent model:  set AGENT_<ROLE>_MODEL=<model-id> in .env or call set_agent_model()
"""

from __future__ import annotations

import logging
import os
import threading
from dataclasses import dataclass, field
from typing import Optional

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

logger = logging.getLogger(__name__)

# Runtime overrides (thread-safe via lock)
_runtime_lock = threading.Lock()
_runtime_provider: str | None = None
_runtime_agent_models: dict[str, str] = {}
_runtime_agent_providers: dict[str, str] = {}

# ── CodingPlan available models ──────────────────────────────────────────────
# These are all models included in the CodingPlan subscription (no extra cost).
# https://www.volcengine.com/docs/82379/1925114
CODINGPLAN_MODELS: dict[str, str] = {
    "ark-code-latest":      "Auto（智能调度，默认）",
    "doubao-seed-2.0-lite": "Doubao Seed-2.0 Lite · 兼顾质量与速度，适合内容创作",
    "doubao-seed-2.0-pro":  "Doubao Seed-2.0 Pro · 旗舰推理，适合复杂逻辑与架构",
    "doubao-seed-2.0-code": "Doubao Seed-2.0 Code · 前端出众，多语言适配",
    "doubao-seed-code":     "Doubao Seed Code · 精准代码生成与任务调度",
    "kimi-k2.5":            "Kimi-K2.5 · 强化前端代码质量与设计表现力（Moonshot AI）",
    "glm-4.7":              "GLM-4.7 · 代码生成、调试、全链路理解（智谱 AI）",
    "deepseek-v3.2":        "DeepSeek-V3.2 · 平衡推理与输出，轻量级代码开发",
    "minimax-m2.5":         "MiniMax-M2.5 · 编程、工具调用和搜索（MiniMax 旗舰开源）",
}

# ── SiliconFlow available models ──────────────────────────────────────────────
SILICONFLOW_MODELS: dict[str, str] = {
    "deepseek-ai/DeepSeek-V3":                 "DeepSeek-V3 · 综合能力强，中文写作、推理、分析",
    "Pro/deepseek-ai/DeepSeek-V3.2":           "DeepSeek-V3.2 Pro · 最强推理，复杂架构设计",
    "deepseek-ai/DeepSeek-V3.2":               "DeepSeek-V3.2 · 新一代推理模型",
    "deepseek-ai/DeepSeek-R1":                 "DeepSeek-R1 · 深度推理，数学和逻辑",
    "Qwen/Qwen3-Coder-30B-A3B-Instruct":       "Qwen3-Coder-30B · 代码专用 MoE，快速精准",
    "Qwen/Qwen3-Coder-480B-A35B-Instruct":     "Qwen3-Coder-480B · 代码专用旗舰",
    "Qwen/Qwen3-32B":                          "Qwen3-32B · 通用大模型",
    "Qwen/Qwen3-8B":                           "Qwen3-8B · 轻量快速，适合摘要等简单任务",
    "Pro/moonshotai/Kimi-K2.5":                "Kimi-K2.5 Pro · 前端代码和设计表现力突出",
    "Pro/zai-org/GLM-5":                       "GLM-5 Pro · 智谱旗舰",
}

# ── Recommended model per agent role, keyed by provider ──────────────────────
_ROLE_DEFAULT_MODEL_BY_PROVIDER: dict[str, dict[str, str]] = {
    "siliconflow": {
        "product_manager":         "Pro/deepseek-ai/DeepSeek-V3.2",
        "architect":               "Pro/deepseek-ai/DeepSeek-V3.2",
        "designer":                "Pro/moonshotai/Kimi-K2.5",
        "frontend":                "Qwen/Qwen3-Coder-30B-A3B-Instruct",
        "backend":                 "Qwen/Qwen3-Coder-30B-A3B-Instruct",
        "qa_devops":               "Pro/deepseek-ai/DeepSeek-V3.2",
        "summarizer":              "deepseek-ai/DeepSeek-V3",
        "requirement_consultant":  "Pro/deepseek-ai/DeepSeek-V3.2",
    },
    "codingplan": {
        "product_manager":         "doubao-seed-2.0-pro",
        "architect":               "doubao-seed-2.0-pro",
        "designer":                "doubao-seed-2.0-pro",
        "frontend":                "doubao-seed-2.0-code",
        "backend":                 "doubao-seed-2.0-code",
        "qa_devops":               "doubao-seed-2.0-pro",
        "summarizer":              "doubao-seed-2.0-lite",
        "requirement_consultant":  "doubao-seed-2.0-pro",
    },
    "deepseek": {
        "product_manager":         "deepseek-coder",
        "architect":               "deepseek-coder",
        "designer":                "deepseek-coder",
        "frontend":                "deepseek-coder",
        "backend":                 "deepseek-coder",
        "qa_devops":               "deepseek-coder",
        "summarizer":              "deepseek-coder",
        "requirement_consultant":  "deepseek-coder",
    },
    # VENDOR-PATCH: 阿里云通义千问角色默认模型
    "dashscope": {
        "product_manager":         "qwen-max",
        "architect":               "qwen-max",
        "designer":                "qwen-plus",
        "frontend":                "qwen-plus",
        "backend":                 "qwen-plus",
        "qa_devops":               "qwen-plus",
        "summarizer":              "qwen-turbo",
        "requirement_consultant":  "qwen-max",
        "requirement_decomposer":  "qwen-plus",
    },
}

def _get_role_defaults(provider: str | None = None) -> dict[str, str]:
    prov = provider or get_default_provider_name()
    return _ROLE_DEFAULT_MODEL_BY_PROVIDER.get(prov, {})


@dataclass(frozen=True)
class AgentModelInfo:
    """Describes which model is assigned to a specific agent role."""
    role: str
    label: str
    model: str
    model_desc: str
    source: str  # "env" | "default"


@dataclass(frozen=True)
class ProviderConfig:
    name: str
    api_key: str
    base_url: str
    default_model: str
    price_prompt_per_1k: float = 0.0
    price_completion_per_1k: float = 0.0
    is_subscription: bool = False


_PROVIDER_SPECS: dict[str, dict] = {
    "codingplan": {
        "key_env": "CODINGPLAN_API_KEY",
        "url_env": "CODINGPLAN_BASE_URL",
        "model_env": "CODINGPLAN_MODEL",
        "defaults": {
            "base_url": "https://ark.cn-beijing.volces.com/api/coding/v3",
            "model": "ark-code-latest",
            "price_prompt": 0.0,
            "price_completion": 0.0,
            "subscription": True,
        },
    },
    "deepseek": {
        "key_env": "DEEPSEEK_API_KEY",
        "url_env": "DEEPSEEK_BASE_URL",
        "model_env": "DEEPSEEK_MODEL",
        "defaults": {
            "base_url": "https://api.deepseek.com/v1",
            "model": "deepseek-coder",
            "price_prompt": 0.001,
            "price_completion": 0.002,
            "subscription": False,
        },
    },
    "siliconflow": {
        "key_env": "SILICONFLOW_API_KEY",
        "url_env": "SILICONFLOW_BASE_URL",
        "model_env": "SILICONFLOW_MODEL",
        "defaults": {
            "base_url": "https://api.siliconflow.cn/v1",
            "model": "deepseek-ai/DeepSeek-V3",
            "price_prompt": 0.0007,
            "price_completion": 0.0007,
            "subscription": False,
        },
    },
    # VENDOR-PATCH: 阿里云 DashScope / 通义千问 (OpenAI 兼容模式)
    "dashscope": {
        "key_env": "REDACTED_CREDENTIAL_NAME",
        "url_env": "DASHSCOPE_BASE_URL",
        "model_env": "DASHSCOPE_MODEL",
        "defaults": {
            "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "model": "qwen-plus",
            "price_prompt": 0.0008,
            "price_completion": 0.002,
            "subscription": False,
        },
    },
}


def _load_provider(name: str) -> Optional[ProviderConfig]:
    spec = _PROVIDER_SPECS.get(name)
    if not spec:
        return None

    api_key = os.getenv(spec["key_env"], "")
    if not api_key and name == "codingplan":
        api_key = os.getenv("ARK_API_KEY", "")
    if not api_key:
        return None

    d = spec["defaults"]

    base_url = os.getenv(spec["url_env"], "")
    if not base_url and name == "codingplan":
        base_url = os.getenv("ARK_BASE_URL", "")
    base_url = base_url or d["base_url"]

    model = os.getenv(spec["model_env"], "")
    if not model and name == "codingplan":
        model = os.getenv("ARK_MODEL", "")
    model = model or d["model"]

    return ProviderConfig(
        name=name,
        api_key=api_key,
        base_url=base_url,
        default_model=model,
        price_prompt_per_1k=d["price_prompt"],
        price_completion_per_1k=d["price_completion"],
        is_subscription=d["subscription"],
    )


def get_default_provider_name() -> str:
    with _runtime_lock:
        if _runtime_provider:
            return _runtime_provider
    return os.getenv("PROVIDER_DEFAULT", "siliconflow")


def get_provider_for_agent(agent_role: str) -> str:
    with _runtime_lock:
        if agent_role in _runtime_agent_providers:
            return _runtime_agent_providers[agent_role]
    env_key = f"AGENT_{agent_role.upper()}_PROVIDER"
    return os.getenv(env_key, "") or get_default_provider_name()


def get_model_for_agent(agent_role: str) -> str | None:
    """Return the per-agent model override.

    Priority:  runtime override > AGENT_<ROLE>_MODEL env var > provider-aware default.
    Returns None only if agent_role is empty/unknown.
    """
    if not agent_role:
        return None
    with _runtime_lock:
        if agent_role in _runtime_agent_models:
            return _runtime_agent_models[agent_role]
    env_key = f"AGENT_{agent_role.upper()}_MODEL"
    from_env = os.getenv(env_key, "").strip()
    if from_env:
        return from_env
    return _get_role_defaults().get(agent_role)


# ── Runtime switching API ─────────────────────────────────────────────────────

def switch_provider(provider_name: str) -> ProviderConfig:
    """Switch the default LLM provider at runtime (no server restart needed).

    Also clears per-agent model overrides so all agents use the new provider's
    default model until explicitly reconfigured.
    """
    cfg = _load_provider(provider_name)
    if not cfg:
        raise ValueError(f"供应商 '{provider_name}' 未配置或缺少 API Key")
    with _runtime_lock:
        global _runtime_provider
        _runtime_provider = provider_name
        _runtime_agent_models.clear()
        _runtime_agent_providers.clear()
    logger.info("Runtime provider switched to: %s (model: %s)", provider_name, cfg.default_model)
    return cfg


def set_agent_model(agent_role: str, model: str | None = None, provider: str | None = None) -> None:
    """Override model and/or provider for a specific agent role at runtime."""
    with _runtime_lock:
        if model is not None:
            _runtime_agent_models[agent_role] = model
        if provider is not None:
            _runtime_agent_providers[agent_role] = provider


def get_runtime_overrides() -> dict:
    """Return current runtime override state (for diagnostics)."""
    with _runtime_lock:
        return {
            "runtime_provider": _runtime_provider,
            "runtime_agent_models": dict(_runtime_agent_models),
            "runtime_agent_providers": dict(_runtime_agent_providers),
        }


_ROLE_LABELS: dict[str, str] = {
    "product_manager":        "产品经理",
    "architect":              "架构师",
    "designer":               "UI/UX 设计师",
    "frontend":               "前端工程师",
    "backend":                "后端工程师",
    "qa_devops":              "QA / DevOps",
    "summarizer":             "摘要 Agent",
    "requirement_consultant": "需求顾问",
}


def get_all_agent_models() -> list[AgentModelInfo]:
    """Return model assignment for every agent role (for display in Settings UI)."""
    defaults = _get_role_defaults()
    result = []
    for role in _ROLE_LABELS:
        default_model = defaults.get(role, "")
        with _runtime_lock:
            runtime_model = _runtime_agent_models.get(role)
        env_key = f"AGENT_{role.upper()}_MODEL"
        from_env = os.getenv(env_key, "").strip()

        if runtime_model:
            model, source = runtime_model, "runtime"
        elif from_env:
            model, source = from_env, "env"
        elif default_model:
            model, source = default_model, "default"
        else:
            model, source = "", "none"

        desc = CODINGPLAN_MODELS.get(model) or SILICONFLOW_MODELS.get(model) or model
        result.append(AgentModelInfo(
            role=role,
            label=_ROLE_LABELS.get(role, role),
            model=model,
            model_desc=desc,
            source=source,
        ))
    return result


def get_provider_config(provider_name: str | None = None) -> ProviderConfig:
    name = provider_name or get_default_provider_name()
    cfg = _load_provider(name)
    if not cfg:
        raise RuntimeError(f"供应商 '{name}' 未配置或缺少 API Key，请检查 .env")
    return cfg


def get_llm(
    agent_role: str = "",
    model: str | None = None,
    temperature: float = 0.7,
    max_tokens: int = 8192,
    stream_usage: bool = False,
    request_timeout: float | None = None,
) -> ChatOpenAI:
    """Create an LLM instance.

    Model resolution priority:
      1. Explicit `model` parameter (caller override)
      2. AGENT_<ROLE>_MODEL env var / runtime override
      3. Provider-aware per-role default
      4. Provider default model (CODINGPLAN_MODEL / ark-code-latest)
    """
    provider_name = (
        get_provider_for_agent(agent_role) if agent_role else get_default_provider_name()
    )
    cfg = get_provider_config(provider_name)

    resolved_model = model or get_model_for_agent(agent_role) or cfg.default_model

    timeout = request_timeout or float(os.getenv("LLM_REQUEST_TIMEOUT", "300"))

    extra: dict = {}
    if stream_usage:
        extra["stream_usage"] = True

    return ChatOpenAI(
        base_url=cfg.base_url,
        api_key=cfg.api_key,
        model=resolved_model,
        temperature=temperature,
        max_tokens=max_tokens,
        request_timeout=timeout,
        **extra,
    )


def get_monthly_quota() -> int:
    return int(os.getenv("CODINGPLAN_MONTHLY_QUOTA", "500"))


def list_configured_providers() -> dict[str, bool]:
    return {name: _load_provider(name) is not None for name in _PROVIDER_SPECS}
