# MVP 优先级清单

## 优先级总览

| 优先级 | Phase | 内容 | 阻塞关系 | 复杂度 |
|--------|-------|------|---------|--------|
| **P0** | 1 | 前后端脚手架 | 无，可并行 | 低 |
| **P0** | 2 | conversation 域 (会话上下文) | Phase 1 后端 | 低 |
| **P0** | 3.1-3.2 | llm_gateway 域 (Mock Provider) | Phase 1 后端 | 中 |
| **P0** | 5 | agent 域 + transport 域 (SSE 端点) | Phase 2 + 3 | 高 |
| **P0** | 6 | 前端 Chat 页面 + SSE 客户端 | Phase 1 前端 + Phase 5 | 中 |
| **P1** | 4 | tools 域 (时间工具) | Phase 1 后端 | 中 |
| **P1** | 5 补充 | agent 工具调用循环 | Phase 3 + 4 | 高 |
| **P1** | 3.3 | OpenAI Provider (可切换) | Phase 3.2 | 低 |
| **P2** | 7 | 端到端集成验证 | 全部 | 低 |

## 最小可运行路径 (P0)

只做 P0 即可得到一个能跑通的系统：用户发消息 → Mock LLM 流式回复 → 前端打字机展示。

```
Phase 1.1 + 1.2 (脚手架，可并行)
    │
    ├── Phase 2 (conversation 域: 会话管理)
    │
    └── Phase 3.1-3.2 (llm_gateway 域: Mock LLM 流式输出)
            │
            ▼
        Phase 5.1-5.3 (agent 编排 + transport SSE 端点)
        注意: 此阶段 agent 不含工具调用循环，只做 LLM → 流式输出
            │
            ▼
        Phase 6 (前端: Repo/Service/Runtime/UI 全层)
            │
            ▼
        ✅ 最小可用
```

### P0 验证标准

- [ ] 后端 `GET /health` 返回 200
- [ ] 前端页面正常加载
- [ ] 发送消息 → SSE 流式返回 → 打字机效果
- [ ] 连续发送多条消息 → 上下文保持

## P1 增量: 工具能力

在 P0 基础上增加工具调用能力。

```
Phase 4 (tools 域: 工具注册 + TimeTool)
    │
    ▼
Phase 5.1 补充: orchestrator 加入工具调用循环
    │
    ▼
Phase 6 补充: 前端展示 tool_call / tool_result 中间状态
    │
    ▼
✅ 完整 MVP
```

### P1 验证标准

- [ ] 发送"现在几点了" → 出现 tool_call 事件 → tool_result 事件 → 最终文本回复
- [ ] 非法时区参数 → ToolResult(error) → LLM 生成友好提示
- [ ] 工具调用不超过 max_iterations 次

## P2 补充: 可切换真实 API + 集成验证

```
Phase 3.3 (OpenAI Provider)
    │
    ▼
Phase 7 (端到端集成测试)
    │
    ▼
✅ 生产可用 MVP
```

### P2 验证标准

- [ ] 设置 `LLM_PROVIDER=openai` + API Key → 切换到真实 API
- [ ] 真实 API 下普通对话正常
- [ ] 真实 API 下工具调用正常
- [ ] 全部 E2E 场景通过

## 排除范围

以下功能明确不在 MVP 范围内：

- 用户认证 / 登录
- 多会话列表 UI (MVP 只有单会话)
- 消息持久化 (重启丢失可接受)
- 流式中断 / 停止生成
- Markdown 渲染 (MVP 纯文本)
- 部署 / Docker
- 可观测性 / 日志 (架构预留，不实现)

## 决策记录

| 决策 | 理由 |
|------|------|
| Python 3.9.6 兼容 | 不用 match/case、`X\|Y` 联合类型语法 |
| 内存存储 | MVP 够用，ConversationRepository Protocol 预留持久化扩展 |
| 自定义 SSE JSON 事件格式 | 比 OpenAI 格式灵活，能携带 tool_call 中间状态 |
| Mock LLM 关键词触发 | 正则匹配决定 tool_calls，Function Calling 兼容格式 |
| 工具失败 → 错误回传 LLM | LLM 生成友好提示，不直接暴露异常 |
| 可观测性域预留 | 目录结构中不创建，架构上留位 |
