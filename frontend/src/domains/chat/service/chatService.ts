import type { Message } from '../types'
import { TOOL_CALL_PREFIX, TOOL_RESULT_PREFIX } from '../config'

/**
 * Chat Service —— 纯业务逻辑，无状态、无副作用。
 * 负责消息列表的数据加工和业务规则。
 */

/** 追加 user 消息并创建空的 assistant 占位 */
export function appendUserMessage(messages: Message[], text: string): Message[] {
  return [
    ...messages,
    { role: 'user', content: text },
    { role: 'assistant', content: '' },
  ]
}

/** 更新最后一条 assistant 消息的内容（流式拼接） */
export function updateLastAssistant(messages: Message[], content: string): Message[] {
  const next = [...messages]
  next[next.length - 1] = { role: 'assistant', content }
  return next
}

/** 追加工具调用中状态 */
export function appendToolCall(messages: Message[], toolName: string): Message[] {
  return [...messages, { role: 'tool', content: `${TOOL_CALL_PREFIX} ${toolName}...` }]
}

/** 工具调用完成：替换最后一条 tool 消息为结果，追加空 assistant 占位 */
export function resolveToolResult(messages: Message[], toolName: string, result: string): Message[] {
  const next = [...messages]
  const lastToolIdx = next.findLastIndex(m => m.role === 'tool')
  if (lastToolIdx >= 0) {
    next[lastToolIdx] = { role: 'tool', content: `${TOOL_RESULT_PREFIX} ${toolName}: ${result}` }
  }
  next.push({ role: 'assistant', content: '' })
  return next
}
