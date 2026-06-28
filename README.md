# AI Chatbot

支持流式对话、多轮上下文、工具调用的 AI 聊天系统 MVP，且方便后续扩展。

## 技术栈

| 层 | 技术 |
|---|---|
| 前端 | React 18 + TypeScript + Vite 5 + Ant Design + Less |
| 后端 | Python 3.9 + FastAPI + SSE |
| LLM | LangChain + OpenAI 兼容接口 |
| 存储 | 内存（已预留 Repository 接口） |

## 快速开始

### 前置要求

- Node.js >= 20
- Python >= 3.9

### 快捷一键启动（安装）
```bash
./start.sh

# 脚本会自动完成：
# 创建 Python venv + 安装依赖
# 复制 .env.example → .env（默认 mock 模式，零配置）
# 启动后端并验证 health 端点
# 安装前端依赖 + 启动 dev serve
```

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

## 项目结构

```
├── backend/
│   └── app/
│       ├── main.py                          # FastAPI 入口
│       ├── shared/config.py                 # 环境变量读取
│       └── domains/
│           ├── transport/                   # HTTP/SSE 传输层
│           │   ├── application/chat_route   # 路由 + 请求校验
│           │   ├── domain/events            # 流式事件定义
│           │   └── infrastructure/sse_formatter
│           ├── agent/                       # Agent 编排
│           │   ├── application/agent_service # 依赖组装入口
│           │   └── domain/orchestrator      # LLM ↔ Tool 循环
│           ├── llm_gateway/                 # LLM 网关
│           │   ├── domain/provider          # Provider Protocol
│           │   └── infrastructure/          # OpenAI / Mock 实现
│           ├── tools/                       # 工具系统
│           │   ├── domain/                  # Tool Protocol + Registry
│           │   └── infrastructure/          # TimeTool + 注册
│           └── conversation/                # 会话管理
│               ├── domain/                  # Message / Conversation 模型
│               ├── application/             # conversation_service
│               └── infrastructure/          # 内存 Repository
├── frontend/
│   └── src/
│       ├── App.tsx                          # 组合入口
│       └── domains/chat/
│           ├── types/                       # Message 类型
│           ├── config/                      # API 地址、展示常量
│           ├── repo/chatRepo.ts             # SSE 流式通信
│           ├── service/chatService.ts       # 消息拼装业务逻辑
│           ├── runtime/useChat.ts           # 状态管理 Hook
│           └── ui/                          # ChatPage / MessageList / MessageBubble / MessageInput
└── 方案说明.md                               # 设计决策与架构详解
```

## SSE 协议

`POST /api/chat`，请求体：

```json
{ "message": "你好", "conversation_id": "uuid（可选）" }
```

响应为 SSE 流，事件类型：

| type | 字段 | 说明 |
|------|------|------|
| `token` | `token` | 流式文本片段 |
| `tool_call` | `name`, `arguments` | AI 发起工具调用 |
| `tool_result` | `name`, `result`, `success` | 工具执行结果 |
| `error` | `message` | 错误信息 |
| `done` | `conversation_id` | 本轮结束 |

## Mock 模式

无需 API Key，修改 `backend/.env`：

```
LLM_PROVIDER=mock
```

可完整验证 SSE → Agent 循环 → 工具调用 → 前端渲染全链路。

## 详细方案

架构设计、技术取舍、AI 工具使用等详见 [方案说明.md](方案说明.md)。

## 其它文档说明

| 文档 | 内容 |
|------|------|
| [00-plan.md](docs/00-plan.md) | 整体规划 |
| [01-system-architecture.md](docs/01-system-architecture.md) | 系统架构设计 |
| [02-api-definition.md](docs/02-api-definition.md) | API 接口定义 |
| [03-context-management.md](docs/03-context-management.md) | 多轮上下文管理 |
| [04-tool-calling-flow.md](docs/04-tool-calling-flow.md) | 工具调用流程 |
| [05-mvp-priority.md](docs/05-mvp-priority.md) | MVP 优先级划分 |
| [06-phased-implementation.md](docs/06-phased-implementation.md) | 分阶段实施计划 |
| [dev-guide.md](docs/dev-guide.md) | 开发指南 |
