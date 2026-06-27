# 工具调用流程

## 整体流程

```
                    AgentOrchestrator
                          │
          ┌───────────────┼───────────────┐
          │               │               │
          ▼               ▼               ▼
    LLMProvider     ToolRegistry    Conversation
          │               │
     ┌────┴────┐    ┌─────┴─────┐
     │ stream  │    │ get_by_name│
     │ (msgs,  │    │ execute    │
     │  tools) │    └───────────┘
     └─────────┘
```

## 详细步骤

```
┌──────────────────────────────────────────────────────────────┐
│ 1. ChatUseCase 收到用户消息                                   │
│    → conversation.append(user_message)                       │
│    → 获取完整 messages 列表                                    │
├──────────────────────────────────────────────────────────────┤
│ 2. AgentOrchestrator.orchestrate(messages, provider, tools)  │
│    │                                                          │
│    │  ┌─── Loop (max_iterations=5) ──────────────────────┐   │
│    │  │                                                    │   │
│    │  │  3. provider.stream(messages, tool_schemas)        │   │
│    │  │     └→ yield TokenEvent / ToolCallEvent            │   │
│    │  │                                                    │   │
│    │  │  4. 收集完整响应后判断:                                │   │
│    │  │     ├─ 无 tool_calls → 跳出循环                      │   │
│    │  │     └─ 有 tool_calls → 进入步骤 5                    │   │
│    │  │                                                    │   │
│    │  │  5. 遍历 tool_calls:                                │   │
│    │  │     ├─ registry.get_by_name(name)                  │   │
│    │  │     │   └─ 找不到 → yield StreamEvent(error)        │   │
│    │  │     ├─ 参数校验 (Pydantic/自定义)                     │   │
│    │  │     │   └─ 校验失败 → ToolResult(success=False)     │   │
│    │  │     ├─ tool.execute(validated_params)               │   │
│    │  │     │   └─ 异常 → try/except → ToolResult(error)   │   │
│    │  │     └─ yield StreamEvent(tool_result)               │   │
│    │  │                                                    │   │
│    │  │  6. 将 tool results 追加到 messages                  │   │
│    │  │     → 回到步骤 3 (下一轮 LLM 调用)                   │   │
│    │  │                                                    │   │
│    │  └────────────────────────────────────────────────────┘   │
│    │                                                          │
│    │  7. 循环结束，yield StreamEvent(done)                     │
├──────────────────────────────────────────────────────────────┤
│ 8. conversation.append(assistant_message)                     │
│    (含完整回复和 tool_calls 记录)                               │
└──────────────────────────────────────────────────────────────┘
```

## 工具注册

### ToolRegistry 接口

```
register(tool: Tool) → void       # 注册工具
get_by_name(name: str) → Tool     # 按名称查找，找不到返回 None
get_all() → List[Tool]            # 返回所有已注册工具
get_schemas() → List[dict]        # 返回 OpenAI function calling 格式的 schema 列表
```

### Tool Protocol

```
属性:
  name: str                        # 工具唯一标识
  description: str                 # 工具描述 (供 LLM 理解用途)
  parameters_schema: dict          # JSON Schema 格式的参数定义

方法:
  async execute(params: dict) → ToolResult
```

### 工具 Schema 示例 (get_current_time)

```json
{
  "type": "function",
  "function": {
    "name": "get_current_time",
    "description": "获取指定时区的当前时间",
    "parameters": {
      "type": "object",
      "properties": {
        "timezone": {
          "type": "string",
          "description": "IANA 时区名称，如 Asia/Shanghai",
          "default": "Asia/Shanghai"
        }
      },
      "required": []
    }
  }
}
```

## 错误处理

### 错误处理矩阵

| 错误场景 | 处理方式 | 对用户的影响 |
|----------|---------|-------------|
| 工具名不存在 | yield error event, 跳过该 tool_call | 前端显示错误提示 |
| 参数校验失败 | ToolResult(success=False, error=描述) → 回传 LLM | LLM 生成友好提示 |
| 工具执行异常 | try/except → ToolResult(success=False) → 回传 LLM | LLM 生成友好提示 |
| 超过最大循环次数 | 强制跳出循环，yield error event | 前端显示"处理超时" |

### ToolResult 值对象

```
ToolResult
├── success: bool          # 是否执行成功
├── data: Optional[str]    # 成功时的返回数据
└── error: Optional[str]   # 失败时的错误描述
```

### 错误回传机制

工具失败时，将错误信息作为 tool message 回传给 LLM，让 LLM 生成面向用户的友好提示，而非直接暴露异常堆栈。

```
工具失败:
  → ToolResult(success=False, error="无效的时区: Mars/Olympus")
  → 追加到 messages: {"role": "tool", "content": "错误: 无效的时区: Mars/Olympus", "tool_call_id": "call_001"}
  → LLM 根据错误信息生成: "抱歉，Mars/Olympus 不是一个有效的时区名称..."
```

## Mock LLM 的工具触发逻辑

### 关键词匹配规则

```
用户消息正则匹配:
  /时间|几点|what time|current time/i
    → 返回 ToolCallEvent:
      {
        "name": "get_current_time",
        "arguments": {"timezone": "Asia/Shanghai"}
      }

  其他消息
    → 纯文本 echo 回复 (逐 token 流式)
```

### 工具结果回传后

```
Mock LLM 收到 tool result 后:
  → 将 tool result 嵌入模板回复
  → 逐 token 流式输出: "当前时间是 {tool_result}。"
```
