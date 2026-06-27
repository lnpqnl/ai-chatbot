import type { Message } from '../types'

interface MessageBubbleProps {
  message: Message
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const { role, content } = message
  return (
    <div className={`message-bubble message-bubble--${role}`}>
      <span className="message-bubble__content">
        {content || '▍'}
      </span>
    </div>
  )
}
