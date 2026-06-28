# 本地开发启动指南

## 快速开始

### 前置要求

- Node.js >= 20
- Python >= 3.9

### 后端

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 填入 API Key

# 启动（mock 模式无需 API Key等信息，将 LLM_PROVIDER 改为 mock 即可）
uvicorn app.main:app --reload --port 8000
```

### 前端

```bash
cd frontend
npm install
npm run dev
```

访问 http://localhost:5173 即可开始对话。
