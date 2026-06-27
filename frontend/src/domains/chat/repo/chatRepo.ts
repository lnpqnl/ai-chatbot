export interface StreamCallbacks {
  onToken: (token: string) => void
  onToolCall: (name: string, args: Record<string, unknown>) => void
  onToolResult: (name: string, result: string, success: boolean) => void
  onDone: (conversationId: string) => void
  onError: (error: Error) => void
}

export async function streamChat(message: string, conversationId: string | null, callbacks: StreamCallbacks) {
  const body: Record<string, string> = { message }
  if (conversationId) body.conversation_id = conversationId

  const response = await fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })

  if (!response.ok || !response.body) {
    callbacks.onError(new Error(`HTTP ${response.status}`))
    return
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() || ''

    for (const line of lines) {
      if (!line.startsWith('data:')) continue
      const jsonStr = line.slice(5).trim()
      if (!jsonStr) continue

      try {
        const event = JSON.parse(jsonStr)
        if (event.type === 'token') {
          callbacks.onToken(event.token)
        } else if (event.type === 'tool_call') {
          callbacks.onToolCall(event.name, event.arguments)
        } else if (event.type === 'tool_result') {
          callbacks.onToolResult(event.name, event.result, event.success)
        } else if (event.type === 'error') {
          callbacks.onError(new Error(event.message))
        } else if (event.type === 'done') {
          callbacks.onDone(event.conversation_id)
        }
      } catch {
        // skip malformed JSON
      }
    }
  }
}
