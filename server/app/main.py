"""FastAPI application entry — methodology runtime backend."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from server.app.core.config import CORS_ORIGINS
from server.app.models.database import create_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1) tables
    create_db()
    # 2) built-in methodologies (idempotent)
    try:
        from server.app.seeds import seed_builtin
        stats = seed_builtin()
        logger.info("Seeded methodologies: %s", stats)
    except Exception as exc:  # pragma: no cover - seeding must never block boot
        logger.warning("Seeding failed (continuing): %s", exc)
    # 3) semantic index for "auto-surfacing" (best-effort; needs embedding API key)
    try:
        from server.app.engine.methodology_index import build_methodology_index
        n = build_methodology_index()
        logger.info("Methodology semantic index built: %d entries", n)
    except Exception as exc:  # pragma: no cover
        logger.warning("Index build skipped (continuing): %s", exc)
    yield


app = FastAPI(title="project_smartbrain", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── routers ──
from server.app.api import health  # noqa: E402

app.include_router(health.router)

# methodologies + runs routers are wired in as they are implemented (T7 / T11)
try:
    from server.app.api import methodologies  # noqa: E402
    app.include_router(methodologies.router)
except Exception as exc:  # pragma: no cover
    logger.warning("methodologies router not loaded: %s", exc)

try:
    from server.app.api import runs  # noqa: E402
    app.include_router(runs.router)
except Exception as exc:  # pragma: no cover
    logger.warning("runs router not loaded: %s", exc)

try:
    from server.app.api import distill  # noqa: E402
    app.include_router(distill.router)
except Exception as exc:  # pragma: no cover
    logger.warning("distill router not loaded: %s", exc)

for _mod in ("lens", "advisor", "bindings"):
    try:
        _m = __import__(f"server.app.api.{_mod}", fromlist=["router"])
        app.include_router(_m.router)
    except Exception as exc:  # pragma: no cover
        logger.warning("%s router not loaded: %s", _mod, exc)
