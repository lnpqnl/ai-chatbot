import { useChat } from '../runtime/useChat'
import { MessageList } from './MessageList'
import { MessageInput } from './MessageInput'
import './chat.less'

export function ChatPage() {
  const { messages, input, setInput, loading, handleSend } = useChat()

  return (
    <div className="chat-page">
      <h2 className="chat-page__title">AI Chatbot</h2>
      <MessageList messages={messages} />
      <MessageInput input={input} loading={loading} onInputChange={setInput} onSend={handleSend} />
    </div>
  )
}
