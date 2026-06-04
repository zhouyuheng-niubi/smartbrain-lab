"""Runtime configuration — reads .env once at import."""
from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./smartbrain.db")
CORS_ORIGINS: list[str] = [
    o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",") if o.strip()
] or ["*"]
PORT_BACKEND: int = int(os.getenv("PORT_BACKEND", "54322"))
PORT_FRONTEND: int = int(os.getenv("PORT_FRONTEND", "54321"))

# Agent role used for all LLM calls in the requirement-decomposition run engine.
DECOMPOSER_ROLE: str = "requirement_decomposer"
