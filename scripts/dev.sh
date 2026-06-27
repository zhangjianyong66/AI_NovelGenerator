#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
API_HOST="${API_HOST:-127.0.0.1}"
API_PORT="${API_PORT:-8000}"
FRONTEND_HOST="${FRONTEND_HOST:-127.0.0.1}"
FRONTEND_PORT="${FRONTEND_PORT:-1420}"

resolve_python() {
  if [[ -n "${PYTHON:-}" ]]; then
    if [[ ! -x "${PYTHON}" ]]; then
      echo "指定的 Python 解释器不可执行：${PYTHON}" >&2
      exit 127
    fi
    echo "${PYTHON}"
  elif [[ -x "${ROOT_DIR}/.venv/bin/python" ]]; then
    echo "${ROOT_DIR}/.venv/bin/python"
  elif [[ -x "${ROOT_DIR}/venv/bin/python" ]]; then
    echo "${ROOT_DIR}/venv/bin/python"
  elif command -v python3 >/dev/null 2>&1; then
    command -v python3
  elif command -v python >/dev/null 2>&1; then
    command -v python
  else
    echo "未找到 Python 解释器。请先安装 python3，或使用 PYTHON=/path/to/python 指定解释器。" >&2
    exit 127
  fi
}

PYTHON_BIN="$(resolve_python)"

if ! "${PYTHON_BIN}" -c "import uvicorn" >/dev/null 2>&1; then
  echo "当前 Python 解释器缺少 uvicorn：${PYTHON_BIN}" >&2
  echo "请先安装依赖：${PYTHON_BIN} -m pip install -r requirements.txt" >&2
  exit 1
fi

if ! command -v npm >/dev/null 2>&1; then
  echo "未找到 npm。请先安装 Node.js 和 npm。" >&2
  exit 127
fi

if [[ ! -d "${ROOT_DIR}/frontend/node_modules" ]]; then
  echo "前端依赖尚未安装。请先运行：cd frontend && npm install" >&2
  exit 1
fi

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
  local deadline=$((SECONDS + 30))

  while (( SECONDS < deadline )); do
    if [[ -n "${BACKEND_PID}" ]] && ! kill -0 "${BACKEND_PID}" 2>/dev/null; then
      echo "后端服务启动失败，请检查上方 uvicorn 输出。" >&2
      return 1
    fi

    if "${PYTHON_BIN}" - "$url" <<'PY'
import sys
from urllib.request import urlopen

url = sys.argv[1]
try:
    with urlopen(url, timeout=1) as response:
        if response.status == 200:
            sys.exit(0)
except Exception:
    pass

sys.exit(1)
PY
    then
      return 0
    fi

    sleep 0.5
  done

  echo "后端服务启动超时：${url}" >&2
  return 1
}

trap cleanup EXIT INT TERM

cd "${ROOT_DIR}"
"${PYTHON_BIN}" -m uvicorn app.api.server:app --reload --host "${API_HOST}" --port "${API_PORT}" &
BACKEND_PID=$!

wait_for_backend

cd "${ROOT_DIR}/frontend"
VITE_API_BASE_URL="http://${API_HOST}:${API_PORT}" npm run dev -- --host "${FRONTEND_HOST}" --port "${FRONTEND_PORT}" --strictPort &
FRONTEND_PID=$!

echo "后端服务：http://${API_HOST}:${API_PORT}"
echo "前端服务：http://${FRONTEND_HOST}:${FRONTEND_PORT}"
echo "按 Ctrl+C 同时停止前后端服务。"

wait -n "${BACKEND_PID}" "${FRONTEND_PID}"
