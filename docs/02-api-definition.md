# 前后端接口定义

## POST /api/chat

聊天接口，接收用户消息，返回 SSE 流式响应。

### Request

**Content-Type**: `application/json`

```json
{
  "conversation_id": "string | null",
  "message": "string"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `conversation_id` | `string \| null` | 否 | 会话 ID，null 或不传表示新建会话 |
| `message` | `string` | 是 | 用户消息，不可为空字符串 |

### Response

**Content-Type**: `text/event-stream`

每条事件格式为 `data: {json}\n\n`。

### 事件类型

#### token — 流式文本片段

```json
{"type": "token", "token": "你"}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `type` | `"token"` | 事件类型 |
| `token` | `string` | 单个文本片段 |

#### tool_call — LLM 决定调用工具

```json
{
  "type": "tool_call",
  "name": "get_current_time",
  "args": {"timezone": "Asia/Shanghai"}
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `type` | `"tool_call"` | 事件类型 |
| `name` | `string` | 工具名称 |
| `args` | `object` | 工具参数 |

#### tool_result — 工具执行结果

```json
{
  "type": "tool_result",
  "name": "get_current_time",
  "result": "2026-06-27 15:30:00",
  "success": true
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `type` | `"tool_result"` | 事件类型 |
| `name` | `string` | 工具名称 |
| `result` | `string` | 执行结果或错误信息 |
| `success` | `boolean` | 是否执行成功 |

#### error — 服务端错误

```json
{"type": "error", "message": "LLM 调用失败"}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `type` | `"error"` | 事件类型 |
| `message` | `string` | 错误描述 |

#### done — 流结束

```json
{"type": "done", "conversation_id": "a1b2c3-..."}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `type` | `"done"` | 事件类型 |
| `conversation_id` | `string` | 会话 ID (首次对话时为新生成的 UUID) |

### HTTP 状态码

| 状态码 | 场景 |
|--------|------|
| 200 | 正常，开始 SSE 流 |
| 400 | message 为空或格式错误 |
| 404 | conversation_id 无效（传入但找不到对应会话） |
| 500 | 内部错误（在 SSE 建立前发生） |

### 时序示例

#### 普通对话

```
Client: POST /api/chat
        {"message": "你好"}

Server: data: {"type":"token","token":"你"}\n\n
        data: {"type":"token","token":"好"}\n\n
        data: {"type":"token","token":"！"}\n\n
        data: {"type":"token","token":"我是"}\n\n
        data: {"type":"token","token":"AI助手"}\n\n
        data: {"type":"done","conversation_id":"a1b2c3"}\n\n
```

#### 工具调用

```
Client: POST /api/chat
        {"conversation_id":"a1b2c3", "message":"现在几点了"}

Server: data: {"type":"tool_call","name":"get_current_time","args":{"timezone":"Asia/Shanghai"}}\n\n
        data: {"type":"tool_result","name":"get_current_time","result":"2026-06-27 15:30:00","success":true}\n\n
        data: {"type":"token","token":"现在"}\n\n
        data: {"type":"token","token":"是"}\n\n
        data: {"type":"token","token":"15:30"}\n\n
        data: {"type":"done","conversation_id":"a1b2c3"}\n\n
```

#### 工具参数错误

```
Client: POST /api/chat
        {"conversation_id":"a1b2c3", "message":"告诉我 Mars/Olympus 时区的时间"}

Server: data: {"type":"tool_call","name":"get_current_time","args":{"timezone":"Mars/Olympus"}}\n\n
        data: {"type":"tool_result","name":"get_current_time","result":"无效的时区: Mars/Olympus","success":false}\n\n
        data: {"type":"token","token":"抱歉"}\n\n
        data: {"type":"token","token":"，"}\n\n
        data: {"type":"token","token":"Mars/Olympus 不是有效的时区"}\n\n
        data: {"type":"done","conversation_id":"a1b2c3"}\n\n
```

---

## GET /health

健康检查端点。

### Response

**Status**: `200 OK`

```json
{"status": "ok"}
```
