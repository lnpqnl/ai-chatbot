import { useState, useRef, useCallback } from 'react'
import { streamChat } from '../repo/chatRepo'
import type { Message } from '../types'

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [conversationId, setConversationId] = useState<string | null>(null)
  const assistantRef = useRef('')

  const handleSend = useCallback(async () => {
    const text = input.trim()
    if (!text || loading) return

    setInput('')
    setMessages(prev => [...prev, { role: 'user', content: text }])
    setLoading(true)
    assistantRef.current = ''

    setMessages(prev => [...prev, { role: 'assistant', content: '' }])

    await streamChat(text, conversationId, {
      onToken(token) {
        assistantRef.current += token
        setMessages(prev => {
          const next = [...prev]
          next[next.length - 1] = { role: 'assistant', content: assistantRef.current }
          return next
        })
      },
      onToolCall(name) {
        setMessages(prev => [...prev, { role: 'tool', content: `🔧 调用工具: ${name}...` }])
      },
      onToolResult(name, result) {
        setMessages(prev => {
          const next = [...prev]
          const lastToolIdx = next.findLastIndex(m => m.role === 'tool')
          if (lastToolIdx >= 0) {
            next[lastToolIdx] = { role: 'tool', content: `✅ ${name}: ${result}` }
          }
          next.push({ role: 'assistant', content: '' })
          return next
        })
        assistantRef.current = ''
      },
      onDone(id) {
        setConversationId(id)
        setLoading(false)
      },
      onError(err) {
        console.error(err)
        setLoading(false)
      },
    })
  }, [input, loading, conversationId])

  return { messages, input, setInput, loading, handleSend }
}
