interface MessageInputProps {
  input: string
  loading: boolean
  onInputChange: (value: string) => void
  onSend: () => void
}

export function MessageInput({ input, loading, onInputChange, onSend }: MessageInputProps) {
  return (
    <div className="message-input">
      <input
        className="message-input__field"
        value={input}
        onChange={e => onInputChange(e.target.value)}
        onKeyDown={e => e.key === 'Enter' && onSend()}
        placeholder="输入消息..."
        disabled={loading}
      />
      <button className="message-input__btn" onClick={onSend} disabled={loading || !input.trim()}>
        发送
      </button>
    </div>
  )
}
