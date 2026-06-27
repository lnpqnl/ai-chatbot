export interface Message {
  role: 'user' | 'assistant' | 'tool'
  content: string
}
