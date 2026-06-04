#!/usr/bin/env bash
# 并行启动后端(uvicorn :54322) + 前端(vite :54321)
set -euo pipefail
cd "$(dirname "$0")/.."
ROOT="$(pwd)"

BACKEND_PORT="${PORT_BACKEND:-54322}"
FRONTEND_PORT="${PORT_FRONTEND:-54321}"

echo "▶ 后端 http://127.0.0.1:${BACKEND_PORT}  (uvicorn --reload)"
( cd "$ROOT" && uvicorn server.app.main:app --host 0.0.0.0 --port "${BACKEND_PORT}" --reload ) &
BACK_PID=$!

echo "▶ 前端 http://127.0.0.1:${FRONTEND_PORT}  (vite)"
( cd "$ROOT/web" && npm run dev -- --port "${FRONTEND_PORT}" ) &
FRONT_PID=$!

trap 'echo; echo "⏹ 关闭..."; kill $BACK_PID $FRONT_PID 2>/dev/null || true' INT TERM
wait
