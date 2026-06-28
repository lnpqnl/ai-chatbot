import { useState, useRef, useCallback } from 'react'
import { streamChat } from '../repo/chatRepo'
import { appendUserMessage, updateLastAssistant, appendToolCall, resolveToolResult } from '../service/chatService'
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
    setMessages(prev => appendUserMessage(prev, text))
    setLoading(true)
    assistantRef.current = ''

    await streamChat(text, conversationId, {
      onToken(token) {
        assistantRef.current += token
        setMessages(prev => updateLastAssistant(prev, assistantRef.current))
      },
      onToolCall(name) {
        setMessages(prev => appendToolCall(prev, name))
      },
      onToolResult(name, result) {
        setMessages(prev => resolveToolResult(prev, name, result))
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
