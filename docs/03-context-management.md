# 上下文管理方案

## 数据模型

```
Conversation (聚合根)
├── id: str (UUID)
├── messages: List[Message] (有序)
├── created_at: datetime
└── updated_at: datetime

Message (值对象)
├── role: "system" | "user" | "assistant" | "tool"
├── content: str
├── tool_calls: Optional[List[ToolCall]]     # role=assistant 时
├── tool_call_id: Optional[str]              # role=tool 时
└── timestamp: datetime

ToolCall (值对象)
├── id: str
├── name: str
└── arguments: dict
```

## 上下文生命周期

### 1. 首次对话 (conversation_id = null)

```
→ 创建 Conversation，生成 UUID
→ 追加 system message (预设 prompt)
→ 追加 user message
→ 调用 LLM (传入 [system, user])
→ 追加 assistant message
→ done 事件返回 conversation_id
```

### 2. 后续对话 (conversation_id = "xxx")

```
→ 按 id 查找 Conversation
→ 追加 user message
→ 传完整 messages 列表给 LLM (含全部历史)
→ 追加 assistant message (含可能的 tool_calls)
→ 若有工具调用:
    → 追加 tool message (role=tool, tool_call_id=xxx)
    → 再次调用 LLM (含 tool 结果)
    → 追加最终 assistant message
```

### 3. 会话不存在

```
→ conversation_id 传入但找不到对应会话
→ 返回 HTTP 404
```

## 消息序列示例

一次包含工具调用的完整会话，messages 列表如下：

```json
[
  {
    "role": "system",
    "content": "你是一个有用的AI助手，可以使用工具来帮助用户。"
  },
  {
    "role": "user",
    "content": "你好"
  },
  {
    "role": "assistant",
    "content": "你好！我是AI助手，有什么可以帮你的？"
  },
  {
    "role": "user",
    "content": "现在几点了"
  },
  {
    "role": "assistant",
    "content": "",
    "tool_calls": [
      {
        "id": "call_001",
        "name": "get_current_time",
        "arguments": {"timezone": "Asia/Shanghai"}
      }
    ]
  },
  {
    "role": "tool",
    "content": "2026-06-27 15:30:00",
    "tool_call_id": "call_001"
  },
  {
    "role": "assistant",
    "content": "现在是 2026年6月27日 15:30。"
  }
]
```

## 上下文窗口策略

### MVP 阶段

- **不做截断**，全量传入 LLM
- Mock LLM 不受 token 限制
- 切换 OpenAI 时，由 LangChain/OpenAI SDK 自行处理超限报错

### 后续扩展点 (不在 MVP 范围)

| 策略 | 说明 |
|------|------|
| 滑动窗口 | 保留最近 N 条消息 |
| Token 计数截断 | tiktoken 计算 token 数，超限时丢弃最早消息 |
| 摘要压缩 | 定期将旧消息压缩为摘要，替换原始消息 |

## 存储实现

### InMemoryConversationRepository

```
内部结构: Dict[str, Conversation]

特性:
  - 进程级单例
  - 服务重启 = 全部丢失
  - 无并发锁 (单进程 asyncio 无竞争)

接口 (Protocol):
  get(conversation_id: str) -> Optional[Conversation]
  save(conversation: Conversation) -> None
  exists(conversation_id: str) -> bool
```

### 扩展性

存储接口定义在 conversation 领域层 (Protocol)，实现在基础设施层。切换为 SQLite/Redis/PostgreSQL 时：

1. 在 infrastructure/ 新增实现类
2. 修改工厂/注入配置
3. 不改动领域层和应用层代码
