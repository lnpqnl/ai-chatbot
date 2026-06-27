# 分阶段实施计划

> 严格按阶段推进：每阶段实施完成后，必须通过验证标准才能进入下一阶段。

---

## Phase 1: 脚手架初始化

**目标**: 前后端项目跑通，health 接口可访问。

### 实施

#### 后端

1. 创建 `backend/` 目录结构：

```
backend/
├── app/
│   ├── __init__.py
│   └── main.py
├── requirements.txt
└── .env.example
```

2. `requirements.txt`:
```
fastapi==0.104.1
uvicorn[standard]==0.24.0
langchain==0.1.20
langchain-openai==0.1.7
pydantic==2.5.0
python-dotenv==1.0.0
sse-starlette==1.8.2
pytz==2023.3
```

3. `app/main.py`:
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="AI Chatbot")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {"status": "ok"}
```

4. `.env.example`:
```
LLM_PROVIDER=mock
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4
```

#### 前端

1. 初始化 Vite + React-TS 项目:
```bash
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install antd @ant-design/icons less
```

2. 配置 `vite.config.ts`:
```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  css: {
    preprocessorOptions: {
      less: {
        javascriptEnabled: true,
      },
    },
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
```

3. 创建最小验证页面 `src/App.tsx`:
```tsx
import { useEffect, useState } from 'react'

function App() {
  const [status, setStatus] = useState('loading...')

  useEffect(() => {
    fetch('/api/health')
      .then(res => res.json())
      .then(data => setStatus(data.status))
      .catch(() => setStatus('error'))
  }, [])

  return <div>Backend status: {status}</div>
}

export default App
```

注意: 前端 proxy 路径为 `/api`，后端路由需对应调整为 `/api/health`，或在 proxy 中 rewrite。此处选择后端路由直接改为 `/api/health`：

```python
@app.get("/api/health")
async def health():
    return {"status": "ok"}
```

### 验证

| # | 验证项 | 命令 / 操作 | 预期结果 |
|---|--------|------------|---------|
| 1 | 后端启动 | `cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload --port 8000` | 启动无报错 |
| 2 | 后端健康检查 | `curl http://localhost:8000/api/health` | `{"status":"ok"}` |
| 3 | 前端启动 | `cd frontend && npm run dev` | Vite 启动无报错 |
| 4 | 前端代理 | 浏览器访问前端页面 | 显示 "Backend status: ok" |

**全部通过 → 进入 Phase 2**

---

## Phase 2: 最简流式对话

**目标**: Mock Provider 流式输出 + SSE 端点 + 前端打字机展示。单轮对话，不含上下文管理，不含工具调用。

### 实施

#### 后端

1. 创建 `backend/app/domains/` 目录 (暂时只创建需要的部分，不预创建空目录)

2. **Mock Provider** — `backend/app/domains/llm_gateway/mock_provider.py`:
   - 接收 message string
   - 逐字符 yield，每字符 sleep 50ms
   - 返回固定模板: "你好！我是 AI 助手，收到了你的消息：{echo}"

3. **SSE 端点** — `backend/app/domains/transport/chat_route.py`:
   - `POST /api/chat`
   - 请求体: `{"message": "xxx"}`
   - 返回 `StreamingResponse(media_type="text/event-stream")`
   - 每个 token 输出: `data: {"type":"token","token":"x"}\n\n`
   - 结束输出: `data: {"type":"done","conversation_id":"temp"}\n\n`

4. 在 `main.py` 中注册路由

#### 前端

5. **Repo 层** — `src/domains/chat/repo/chatRepo.ts`:
   - `streamChat(message, callbacks)`: fetch + ReadableStream 读取 SSE
   - 解析 `data: {json}\n\n` 格式
   - 回调: `onToken(token)`, `onDone(conversationId)`

6. **UI 层** — 简化版 Chat 页面:
   - 输入框 + 发送按钮
   - 消息列表 (user/assistant)
   - assistant 消息实时追加 token (打字机效果)

### 验证

| # | 验证项 | 命令 / 操作 | 预期结果 |
|---|--------|------------|---------|
| 1 | SSE 端点 | `curl -X POST http://localhost:8000/api/chat -H "Content-Type: application/json" -d '{"message":"hello"}' -N` | 逐条输出 `data: {"type":"token",...}` 事件，最后 `done` |
| 2 | 前端发送 | 在页面输入消息并发送 | 消息出现在列表，assistant 回复逐字显示 |
| 3 | 打字机效果 | 观察 assistant 回复渲染 | 文字逐字出现，非一次性全量显示 |

**全部通过 → 进入 Phase 3**

---

## Phase 3: 多轮上下文

**目标**: 实现 conversation 域，支持多轮连续对话，历史消息传入 Mock LLM。

### 实施

#### 后端

1. **Conversation 领域模型** — `backend/app/domains/conversation/domain/models.py`:
   - `Message` dataclass: role, content, tool_calls, tool_call_id, timestamp
   - `Conversation` dataclass: id, messages, created_at, updated_at

2. **Conversation Repository** — `backend/app/domains/conversation/domain/repository.py`:
   - `ConversationRepository(Protocol)`: get, save, exists

3. **内存实现** — `backend/app/domains/conversation/infrastructure/memory_repo.py`:
   - `InMemoryConversationRepository`: dict 存储

4. **应用服务** — `backend/app/domains/conversation/application/conversation_service.py`:
   - `get_or_create(conversation_id)` → (conversation, is_new)
   - `append_message(conversation_id, message)`
   - `get_messages(conversation_id)` → List[Message]

5. **修改 SSE 端点**:
   - 请求体增加 `conversation_id` 字段 (可选)
   - 首次对话: 创建会话，追加 system + user message
   - 后续对话: 查找会话，追加 user message
   - Mock Provider 改为接收完整 messages 列表 (但回复逻辑不变)
   - done 事件返回真实 conversation_id

6. **修改 Mock Provider**:
   - 接收 messages 列表，回复中 echo 最后一条 user message
   - 若历史中有多条消息，回复前缀加 "（第N轮对话）"

#### 前端

7. **状态管理**:
   - 维护 `conversationId` 状态
   - 首次对话后从 `done` 事件保存 conversationId
   - 后续请求带上 conversationId

### 验证

| # | 验证项 | 命令 / 操作 | 预期结果 |
|---|--------|------------|---------|
| 1 | 首次对话 | 发送第一条消息 | 返回 done 事件含 conversation_id (UUID) |
| 2 | 连续对话 | 接着发送第二条消息 | 请求带 conversation_id，回复含"第2轮对话"标识 |
| 3 | 上下文保持 | 后端检查 messages 列表 | 包含所有历史 user + assistant 消息 |
| 4 | 新会话 | 刷新页面后发送消息 | 生成新 conversation_id，从第1轮开始 |
| 5 | 无效会话 | curl 传入不存在的 conversation_id | 返回 404 |

**全部通过 → 进入 Phase 4**

---

## Phase 4: 工具调用闭环

**目标**: 在 Mock 模式下跑通完整的工具调用链路：触发 → 执行 → 回传 → 生成回复。

### 实施

#### 后端

1. **Tool Protocol** — `backend/app/domains/tools/domain/base.py`:
   - `Tool(Protocol)`: name, description, parameters_schema, execute(params) → ToolResult
   - `ToolResult` dataclass: success, data, error

2. **ToolRegistry** — `backend/app/domains/tools/domain/registry.py`:
   - register, get_by_name, get_all, get_schemas

3. **TimeTool** — `backend/app/domains/tools/infrastructure/time_tool.py`:
   - 参数: timezone (str, default "Asia/Shanghai")
   - 参数校验: pytz.timezone() 验证，失败返回 ToolResult(success=False)
   - 执行: 返回格式化当前时间

4. **修改 Mock Provider**:
   - 接收 tools schema 列表
   - 关键词识别 (`/时间|几点|what time|current time/i`)
   - 匹配时返回 tool_calls 格式 (不输出 token，直接返回 ToolCallEvent)
   - 收到 tool result 后，输出模板回复: "当前时间是 {result}。"

5. **Agent Orchestrator** — `backend/app/domains/agent/domain/orchestrator.py`:
   - `orchestrate(messages, provider, registry)` → AsyncIterator
   - 循环: LLM stream → 判断 tool_calls → 执行 → 回传 → 再调 LLM
   - max_iterations = 5

6. **修改 SSE 端点**:
   - 增加 tool_call 和 tool_result 事件输出
   - 集成 orchestrator 替代直接调用 provider

#### 前端

7. **展示工具调用中间状态**:
   - 收到 tool_call 事件 → 显示"正在查询时间..."
   - 收到 tool_result 事件 → 显示工具返回结果
   - 最终 token 流正常显示

### 验证

| # | 验证项 | 命令 / 操作 | 预期结果 |
|---|--------|------------|---------|
| 1 | 工具触发 | 发送"现在几点了" | SSE 流中出现 tool_call 事件 |
| 2 | 工具执行 | 同上 | SSE 流中出现 tool_result 事件，含当前时间 |
| 3 | 最终回复 | 同上 | tool_result 后出现 token 流，内容包含时间 |
| 4 | 非工具对话 | 发送"你好" | 正常流式回复，无 tool_call 事件 |
| 5 | 参数校验 | curl 手动构造非法 timezone 的工具调用场景 | ToolResult(success=false)，LLM 生成友好提示 |
| 6 | 循环限制 | (如适用) 构造需要多次工具调用的场景 | 不超过 5 次循环 |
| 7 | 前端展示 | 页面发送"现在几点了" | 显示工具调用中间状态 + 最终时间回复 |

**全部通过 → 进入 Phase 5**

---

## Phase 5: 真实 API 对齐

**目标**: 实现 OpenAI Provider，验证真实 API 下的对话和工具调用。

### 实施

1. **OpenAI Provider** — `backend/app/domains/llm_gateway/infrastructure/openai_provider.py`:
   - 使用 langchain-openai 的 `ChatOpenAI`
   - 支持 streaming
   - 支持 `bind_tools()` 绑定工具 schema

2. **Provider Factory** — `backend/app/domains/llm_gateway/infrastructure/factory.py`:
   - 读取环境变量 `LLM_PROVIDER`
   - `mock` → MockProvider
   - `openai` → OpenAIProvider (需 OPENAI_API_KEY)

3. **Config** — `backend/app/shared/config.py`:
   - 集中管理环境变量读取
   - 提供 `get_llm_provider()` 函数

4. **适配差异**:
   - OpenAI 的 tool_calls 格式与 Mock 对齐 (确保 orchestrator 无需修改)
   - 流式输出中 tool_calls 可能分多个 chunk 到达，需要聚合

### 验证

| # | 验证项 | 命令 / 操作 | 预期结果 |
|---|--------|------------|---------|
| 1 | Mock 模式不变 | `LLM_PROVIDER=mock`，重复 Phase 4 验证 | 全部通过 |
| 2 | 切换 OpenAI | 设置 `LLM_PROVIDER=openai` + API Key | 启动无报错 |
| 3 | 普通对话 | 发送"你好" | 真实 LLM 流式回复 |
| 4 | 工具调用 | 发送"现在几点了" | LLM 自主决定调用工具 → 执行 → 返回时间 |
| 5 | 多轮对话 | 连续对话 | 上下文保持正常 |

**全部通过 → 进入 Phase 6**

---

## Phase 6: 分层重构与完善

**目标**: 按 DDD 规范整理代码结构，补全参数校验、错误处理、边界情况。

### 实施

1. **代码归位**:
   - 确保所有文件在正确的层级目录中
   - 确保跨域依赖只通过 Protocol 接口
   - 补充缺失的 `__init__.py`

2. **参数校验**:
   - `POST /api/chat` 请求体校验: message 非空、类型正确
   - 工具参数 Pydantic 校验
   - conversation_id 格式校验 (UUID)

3. **错误处理**:
   - LLM 调用失败 → SSE error 事件
   - 工具执行异常 → ToolResult(error) → 回传 LLM
   - 未知异常 → 500 + 日志

4. **前端分层整理**:
   - 确保 Types / Config / Repo / Service / Runtime / UI 层级清晰
   - 无跨层依赖

5. **System Prompt**:
   - 为新会话添加 system message
   - 描述 AI 身份和可用工具

### 验证

| # | 验证项 | 操作 | 预期结果 |
|---|--------|------|---------|
| 1 | 请求校验 | POST 空 message | 400 错误 |
| 2 | 会话校验 | POST 非法 conversation_id | 404 错误 |
| 3 | 工具错误处理 | 非法 timezone 参数 | 友好提示，不崩溃 |
| 4 | LLM 异常 | (模拟) Provider 抛异常 | SSE error 事件，连接正常关闭 |
| 5 | 代码结构 | 检查 import 关系 | 无循环依赖，无跨域 infrastructure 直接引用 |
| 6 | 完整 E2E | 走完全部场景 | 普通对话 / 工具调用 / 多轮 / 错误处理 全部正常 |

**全部通过 → MVP 完成 ✅**

---

## 阶段依赖图

```
Phase 1 (脚手架)
    │
    ▼
Phase 2 (最简流式对话)
    │
    ▼
Phase 3 (多轮上下文)
    │
    ▼
Phase 4 (工具调用闭环)
    │
    ▼
Phase 5 (真实 API 对齐)
    │
    ▼
Phase 6 (分层重构与完善)
    │
    ▼
  ✅ MVP Done
```

每个阶段都是前一阶段的增量，不做跨阶段的提前实现。
