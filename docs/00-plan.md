# AI-Chat MVP 架构设计 + 实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 构建一个支持 SSE 流式输出、工具调用（Function Calling）的 AI 聊天 MVP

**Architecture:** 前后端分离，按业务子域组织。后端轻量 DDD（应用层+领域层+基础设施层），前端六层架构（Types→Config→Repo→Service→Runtime→UI）。域间通过 Protocol/ABC 接口通信，依赖倒置。

**Tech Stack:**
- Frontend: React 18 + Vite + Ant Design + Less
- Backend: Python 3.9.6 + FastAPI + LangChain + langchain-openai + pip
- Storage: In-memory (dict)
- Streaming: SSE (Server-Sent Events)

---

## 业务子域

| 类型 | 子域 | 职责 |
|------|------|------|
| 核心域 | agent (编排) | 决策循环：何时调工具、何时回复、如何组合结果 |
| 核心域 | conversation (会话) | 会话生命周期、上下文序列、消息存取 |
| 支撑域 | llm_gateway (LLM网关) | Provider 抽象、模型调用、流式输出 |
| 支撑域 | tools (工具系统) | 工具注册、schema、参数校验、执行、错误处理 |
| 支撑域 | transport (消息传输) | SSE 协议、事件格式、HTTP 端点 |
| 预留 | observability (可观测性) | 日志、链路追踪 (MVP 不做) |

## 分层规范

### 后端: 轻量 DDD
- 应用层: 用例编排，调用领域层
- 领域层: 核心业务规则、Protocol 接口定义、值对象
- 基础设施层: 接口实现、外部服务对接

### 前端: 六层
- Types → Config → Repo → Service → Runtime → UI
- 严格单向依赖，禁止反向引用

## 域间通信
- 直接函数调用 + Protocol/ABC 接口抽象
- agent 域是唯一编排者，其他域为被调用方

---

---

## 核心流程

```
用户输入 → POST /api/chat (conversation_id + message)
  → transport.应用层: 接收请求，委托 agent
  → agent.应用层 (ChatUseCase):
      1. conversation 域: 获取/创建会话，追加用户消息
      2. llm_gateway 域: 调用 LLM (stream)
      3. 判断 LLM 响应:
         ├─ tool_calls → tools 域: 校验参数 → 执行 → 结果回传 LLM → 回到 2
         └─ 纯文本 → 逐 token yield
      4. conversation 域: 追加助手消息
  → transport.基础设施层: SSE 序列化输出
  → 前端 Repo 层: 解析 SSE 事件流
  → 前端 Service 层: 状态更新
  → 前端 Runtime 层: hook 驱动重渲染
  → 前端 UI 层: 打字机效果渲染
```

---

## Phase 1: 脚手架 + 共享层 (可并行)

### Task 1.1: 后端项目初始化
- 创建 `backend/` 目录骨架（含 domains/ 各子域空目录）
- `requirements.txt`: fastapi, uvicorn[standard], langchain, langchain-openai, pydantic, python-dotenv, sse-starlette, pytz
- `app/main.py`: FastAPI 启动 + CORS + `GET /health`
- `app/shared/config.py`: 读取 .env (LLM_PROVIDER, OPENAI_API_KEY 等)
- 验证: uvicorn 启动无报错

### Task 1.2: 前端项目初始化 *(parallel with 1.1)*
- Vite + React-TS 脚手架
- 安装: antd, less, @ant-design/icons
- vite.config.ts: proxy `/api` → `localhost:8000`
- `domains/chat/types/index.ts`: Message, ChatEvent 类型
- `domains/chat/config/index.ts`: API 地址、事件类型常量
- 验证: `npm run dev` 正常

---

## Phase 2: conversation 域 (会话管理)

### Task 2.1: 领域层
- `conversation/domain/models.py`: `Conversation` 聚合根 (id, messages, created_at)、`Message` 值对象 (role, content, tool_calls, tool_call_id)
- `conversation/domain/repository.py`: `ConversationRepository(Protocol)` — get, save, exists

### Task 2.2: 基础设施层
- `conversation/infrastructure/memory_repo.py`: `InMemoryConversationRepository` 实现 (dict 存储)

### Task 2.3: 应用层
- `conversation/application/conversation_service.py`: `get_or_create()`, `append_message()`, `get_messages()`
- 验证: 单元测试 CRUD

---

## Phase 3: llm_gateway 域 (LLM 网关)

### Task 3.1: 领域层
- `llm_gateway/domain/provider.py`: `LLMProvider(Protocol)` — `async stream(messages, tools) -> AsyncIterator[LLMEvent]`
- `llm_gateway/domain/events.py`: `LLMEvent` 值对象 (TokenEvent, ToolCallEvent, DoneEvent)

### Task 3.2: 基础设施层 — Mock Provider
- `llm_gateway/infrastructure/mock_provider.py`:
  - 逐 token 流式 (50ms 延迟)
  - 关键词识别 → 返回 ToolCallEvent (Function Calling 兼容格式)
  - 非工具场景 → 模板 echo 回复
  - `bind_tools()` 支持

### Task 3.3: 基础设施层 — OpenAI Provider
- `llm_gateway/infrastructure/openai_provider.py`: 包装 `ChatOpenAI` streaming
- `llm_gateway/infrastructure/factory.py`: 根据 config 返回对应 provider
- 验证: Mock provider 单独测试 stream 输出

---

## Phase 4: tools 域 (工具系统)

### Task 4.1: 领域层
- `tools/domain/base.py`: `Tool(Protocol)` — name, description, parameters_schema, `async execute(params) -> ToolResult`
- `tools/domain/base.py`: `ToolResult` 值对象 (success: bool, data/error)
- `tools/domain/registry.py`: `ToolRegistry` — register, get_by_name, get_all, get_schemas

### Task 4.2: 基础设施层 — 时间工具
- `tools/infrastructure/time_tool.py`: `TimeTool` 实现
  - 参数 schema: `{"timezone": {"type": "string", "default": "Asia/Shanghai"}}`
  - 参数校验: pytz 验证合法时区，失败返回 ToolResult(success=False, error=...)
  - 执行异常: try/except → ToolResult(success=False)
- 验证: 合法/非法参数测试

---

## Phase 5: agent 域 (编排) + transport 域 (传输)

### Task 5.1: agent 领域层
- `agent/domain/orchestrator.py`: `AgentOrchestrator`
  - `async orchestrate(messages, llm_provider, tool_registry) -> AsyncIterator[StreamEvent]`
  - 循环: call LLM → if tool_calls → execute tools → feed back → call LLM again
  - 最大循环次数限制 (防无限 loop)

### Task 5.2: agent 应用层
- `agent/application/chat_usecase.py`: `ChatUseCase`
  - 组合 conversation_service + llm_provider + tool_registry
  - `async stream_chat(conversation_id, message) -> AsyncIterator[StreamEvent]`

### Task 5.3: transport 域
- `transport/domain/events.py`: `StreamEvent` 值对象 (token/tool_call/tool_result/error/done)
- `transport/application/chat_route.py`: `POST /api/chat` FastAPI 路由
  - SSE: `data: {json}\n\n` 格式
- `transport/infrastructure/sse_formatter.py`: StreamEvent → SSE 字符串
- 验证: curl 测试完整流程

---

## Phase 6: 前端实现

### Task 6.1: Repo + Service 层
- `domains/chat/repo/chatRepo.ts`: fetch + ReadableStream SSE 解析
- `domains/chat/service/chatService.ts`: 事件分发、消息序列管理

### Task 6.2: Runtime 层
- `domains/chat/runtime/useChat.ts`: messages/isLoading/conversationId 状态，sendMessage 方法

### Task 6.3: UI 层
- `domains/chat/ui/ChatPage/` — 页面容器
- `domains/chat/ui/MessageBubble/` — 气泡 (支持逐字增长)
- `domains/chat/ui/MessageList/` — 列表 (自动滚底)
- `domains/chat/ui/MessageInput/` — 输入 (Ant Design, Enter 发送)
- App.tsx 入口配置
- 验证: 完整 E2E 流程

---

## Phase 7: 端到端集成验证

| 场景 | 预期 |
|------|------|
| 普通消息 | 流式打字机回复 |
| "现在几点了" | tool_call → tool_result → 时间回复 |
| 非法 timezone | ToolResult(error) → LLM 生成友好提示 |
| 连续对话 | 上下文保持 |
| `LLM_PROVIDER=openai` | 切换真实 API 正常 |

---

## 目录结构 (最终)

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

---

## 决策记录

- Python 3.9.6 兼容: 不用 match/case、`X|Y` 联合类型
- 内存存储: MVP 够用，ConversationRepository Protocol 预留持久化扩展
- 自定义 SSE JSON 事件格式: 比 OpenAI 格式灵活，能携带 tool_call 中间状态
- Mock LLM 关键词触发: 正则匹配决定 tool_calls，Function Calling 兼容格式
- 工具失败 → ToolResult(error) → 回传 LLM 生成友好提示
- 可观测性域预留: 目录结构中不创建，但架构上留位

## 排除范围

- 用户认证/登录、多会话列表 UI、消息持久化
- 流式中断/停止生成、Markdown 渲染、部署/Docker
- 可观测性/日志 (架构预留，MVP 不实现)
