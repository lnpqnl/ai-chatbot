# 本地开发启动指南

## 环境配置

编辑 `backend/.env`：

```bash
LLM_PROVIDER=mock          # mock 或 openai
OPENAI_API_KEY=sk-xxx      # 使用 openai 时必填
OPENAI_MODEL=gpt-4         # 可选
```

## 后端

```bash
cd backend && source venv/bin/activate && uvicorn app.main:app --reload --port 8000
```

验证：

```bash
curl http://localhost:8000/api/health
# 期望返回: {"status":"ok"}
```

## 前端

```bash
cd frontend && npm run dev
```

访问 http://localhost:5173

验证代理：

```bash
curl http://localhost:5173/api/health
# 期望返回: {"status":"ok"}
```
