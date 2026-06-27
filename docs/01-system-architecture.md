# 系统架构图

## 总体架构

前后端分离，按业务子域组织。后端轻量 DDD（应用层+领域层+基础设施层），前端六层架构（Types→Config→Repo→Service→Runtime→UI）。域间通过 Protocol/ABC 接口通信，依赖倒置。

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Frontend (React + Vite)                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  chat domain                                                 │   │
│  │  ┌────────┐  ┌────────┐  ┌──────────┐  ┌────────┐  ┌────┐  │   │
│  │  │  Types │→│ Config │→│   Repo    │→│Service │→│Runtime│  │   │
│  │  └────────┘  └────────┘  └──────────┘  └────────┘  └──┬──┘  │   │
│  │                             │ fetch+                    │      │   │
│  │                             │ ReadableStream            ▼      │   │
│  │                             │                  ┌────────────┐  │   │
│  │                             │                  │  UI Layer  │  │   │
│  │                             │                  │ ChatPage   │  │   │
│  │                             │                  │ MessageList│  │   │
│  │                             │                  │ MsgBubble  │  │   │
│  │                             │                  │ MsgInput   │  │   │
│  │                             │                  └────────────┘  │   │
│  └─────────────────────────────┼────────────────────────────────┘   │
└────────────────────────────────┼────────────────────────────────────┘
                                 │ POST /api/chat
                                 │ SSE (text/event-stream)
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Backend (FastAPI + LangChain)                   │
│                                                                      │
│  ┌─── transport 域 ──────────────────────────────────────────────┐  │
│  │  application/chat_route.py   POST /api/chat                   │  │
│  │  infrastructure/sse_formatter.py   StreamEvent → SSE bytes    │  │
│  │  domain/events.py   StreamEvent 值对象                         │  │
│  └──────────────────────────────┬────────────────────────────────┘  │
│                                 │ 委托                              │
│  ┌─── agent 域 (核心编排) ──────▼────────────────────────────────┐  │
│  │  application/chat_usecase.py                                   │  │
│  │    组合 conversation + llm_gateway + tools                     │  │
│  │  domain/orchestrator.py                                        │  │
│  │    LLM 调用 → tool_calls 判断 → 执行 → 回传 → 循环            │  │
│  └──────┬──────────────┬──────────────────┬──────────────────────┘  │
│         │              │                  │                          │
│         ▼              ▼                  ▼                          │
│  ┌─conversation─┐ ┌─llm_gateway──┐ ┌───tools────────┐              │
│  │ domain/      │ │ domain/      │ │ domain/         │              │
│  │  models.py   │ │  provider.py │ │  base.py        │              │
│  │  repository  │ │  events.py   │ │  registry.py    │              │
│  │  (Protocol)  │ │  (Protocol)  │ │  (Protocol)     │              │
│  │ infra/       │ │ infra/       │ │ infra/          │              │
│  │  memory_repo │ │  mock_prov.  │ │  time_tool.py   │              │
│  └──────────────┘ │  openai_prov.│ └─────────────────┘              │
│                   │  factory.py  │                                    │
│                   └──────────────┘                                    │
│                                                                      │
│  ┌─── shared ────────────────────────────────────────────────────┐  │
│  │  config.py   环境变量 / Provider 选择                          │  │
│  └───────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────┘
```

## 业务子域

| 类型 | 子域 | 职责 |
|------|------|------|
| 核心域 | agent (编排) | 决策循环：何时调工具、何时回复、如何组合结果 |
| 核心域 | conversation (会话) | 会话生命周期、上下文序列、消息存取 |
| 支撑域 | llm_gateway (LLM网关) | Provider 抽象、模型调用、流式输出 |
| 支撑域 | tools (工具系统) | 工具注册、schema、参数校验、执行、错误处理 |
| 支撑域 | transport (消息传输) | SSE 协议、事件格式、HTTP 端点 |
| 预留 | observability (可观测性) | 日志、链路追踪 (MVP 不做) |

## 依赖规则

```
transport → agent → { conversation, llm_gateway, tools }
各域 infrastructure → 各域 domain (依赖倒置)
跨域只依赖对方 domain 层的 Protocol，禁止依赖 infrastructure
```

## 技术栈

- **Frontend**: React 18 + Vite + Ant Design + Less
- **Backend**: Python 3.9.6 + FastAPI + LangChain + langchain-openai + pip
- **Storage**: In-memory (dict)
- **Streaming**: SSE (Server-Sent Events)

## 目录结构

```
ai-chatbot/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── shared/
│   │   │   └── config.py
│   │   └── domains/
│   │       ├── agent/
│   │       │   ├── application/
│   │       │   │   └── chat_usecase.py
│   │       │   └── domain/
│   │       │       └── orchestrator.py
│   │       ├── conversation/
│   │       │   ├── domain/
│   │       │   │   ├── models.py
│   │       │   │   └── repository.py
│   │       │   ├── application/
│   │       │   │   └── conversation_service.py
│   │       │   └── infrastructure/
│   │       │       └── memory_repo.py
│   │       ├── llm_gateway/
│   │       │   ├── domain/
│   │       │   │   ├── provider.py
│   │       │   │   └── events.py
│   │       │   └── infrastructure/
│   │       │       ├── mock_provider.py
│   │       │       ├── openai_provider.py
│   │       │       └── factory.py
│   │       ├── tools/
│   │       │   ├── domain/
│   │       │   │   ├── base.py
│   │       │   │   └── registry.py
│   │       │   └── infrastructure/
│   │       │       └── time_tool.py
│   │       └── transport/
│   │           ├── domain/
│   │           │   └── events.py
│   │           ├── application/
│   │           │   └── chat_route.py
│   │           └── infrastructure/
│   │               └── sse_formatter.py
│   ├── tests/
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── domains/
│   │   │   └── chat/
│   │   │       ├── types/index.ts
│   │   │       ├── config/index.ts
│   │   │       ├── repo/chatRepo.ts
│   │   │       ├── service/chatService.ts
│   │   │       ├── runtime/useChat.ts
│   │   │       └── ui/
│   │   │           ├── ChatPage/
│   │   │           ├── MessageList/
│   │   │           ├── MessageBubble/
│   │   │           └── MessageInput/
│   │   └── shared/
│   │       └── styles/variables.less
│   ├── vite.config.ts
│   └── package.json
└── README.md
```
