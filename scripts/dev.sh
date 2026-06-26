#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
API_HOST="${API_HOST:-127.0.0.1}"
API_PORT="${API_PORT:-8000}"
FRONTEND_HOST="${FRONTEND_HOST:-127.0.0.1}"
FRONTEND_PORT="${FRONTEND_PORT:-1420}"

BACKEND_PID=""
FRONTEND_PID=""

cleanup() {
  if [[ -n "${FRONTEND_PID}" ]] && kill -0 "${FRONTEND_PID}" 2>/dev/null; then
    kill "${FRONTEND_PID}" 2>/dev/null || true
  fi
  if [[ -n "${BACKEND_PID}" ]] && kill -0 "${BACKEND_PID}" 2>/dev/null; then
    kill "${BACKEND_PID}" 2>/dev/null || true
  fi
}

wait_for_backend() {
  local url="http://${API_HOST}:${API_PORT}/health"
  python - "$url" <<'PY'
import sys
import time
from urllib.error import URLError
from urllib.request import urlopen

url = sys.argv[1]
deadline = time.monotonic() + 30
while time.monotonic() < deadline:
    try:
        with urlopen(url, timeout=1) as response:
            if response.status == 200:
                sys.exit(0)
    except URLError:
        pass
    time.sleep(0.5)

print(f"后端服务启动超时：{url}", file=sys.stderr)
sys.exit(1)
PY
}

trap cleanup EXIT INT TERM

cd "${ROOT_DIR}"
python -m uvicorn app.api.server:app --reload --host "${API_HOST}" --port "${API_PORT}" &
BACKEND_PID=$!

wait_for_backend

cd "${ROOT_DIR}/frontend"
VITE_API_BASE_URL="http://${API_HOST}:${API_PORT}" npm run dev -- --host "${FRONTEND_HOST}" --port "${FRONTEND_PORT}" --strictPort &
FRONTEND_PID=$!

echo "后端服务：http://${API_HOST}:${API_PORT}"
echo "前端服务：http://${FRONTEND_HOST}:${FRONTEND_PORT}"
echo "按 Ctrl+C 同时停止前后端服务。"

wait -n "${BACKEND_PID}" "${FRONTEND_PID}"
