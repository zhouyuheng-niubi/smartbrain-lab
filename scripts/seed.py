"""Seed the database with built-in methodologies. Idempotent.

Usage:  python scripts/seed.py
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from server.app.models.database import create_db
from server.app.seeds import seed_builtin

if __name__ == "__main__":
    create_db()
    result = seed_builtin()
    print(f"✓ seeded: created={result['created']} updated={result['updated']} total={result['total']}")
