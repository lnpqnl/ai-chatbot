#!/bin/bash
# AI Chatbot 一键启动脚本
# 用法: ./start.sh

set -e

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"

echo "========================================="
echo "  AI Chatbot - 一键启动"
echo "========================================="

# ---------- 后端 ----------
echo ""
echo "[1/4] 初始化后端 Python 虚拟环境..."
cd "$BACKEND_DIR"

if [ ! -d "venv" ]; then
  python3 -m venv venv
fi
source venv/bin/activate

echo "[2/4] 安装后端依赖..."
pip install -r requirements.txt -q

# 如果没有 .env，从 .env.example 复制（默认 mock 模式，无需 API Key）
if [ ! -f ".env" ]; then
  cp .env.example .env
  echo "  → 已创建 .env（默认 mock 模式，无需配置 API Key）"
fi

echo "[3/4] 启动后端服务 (port 8000)..."
uvicorn app.main:app --reload --port 8000 &
BACKEND_PID=$!
sleep 2

# 验证后端是否启动成功
if curl -s http://localhost:8000/api/health | grep -q "ok"; then
  echo "  → 后端启动成功 ✓"
else
  echo "  → 后端启动失败，请检查日志"
  kill $BACKEND_PID 2>/dev/null
  exit 1
fi

# ---------- 前端 ----------
echo "[4/4] 启动前端服务..."
cd "$FRONTEND_DIR"

if [ ! -d "node_modules" ]; then
  echo "  → 安装前端依赖..."
  npm install --silent
fi

npm run dev &
FRONTEND_PID=$!
sleep 3

echo ""
echo "========================================="
echo "  启动完成！"
echo ""
echo "  前端：http://localhost:5173"
echo "  后端：http://localhost:8000"
echo "  健康检查：http://localhost:8000/api/health"
echo ""
echo "  当前模式：mock（无需 API Key 即可体验完整流程）"
echo "  如需切换真实 LLM，编辑 backend/.env"
echo ""
echo "  按 Ctrl+C 停止所有服务"
echo "========================================="

# 捕获退出信号，清理子进程
cleanup() {
  echo ""
  echo "正在停止服务..."
  kill $BACKEND_PID 2>/dev/null
  kill $FRONTEND_PID 2>/dev/null
  exit 0
}
trap cleanup SIGINT SIGTERM

# 等待子进程
wait
