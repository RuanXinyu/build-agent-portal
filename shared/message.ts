import type { MessagePart } from './message-part'

export class Message {
  id: string
  chatId: string
  role: 'user' | 'assistant' | 'system'
  parts: MessagePart[]
  createdAt: Date

  constructor(data: {
    id: string
    chatId: string
    role: 'user' | 'assistant' | 'system'
    parts: MessagePart[]
    createdAt: Date
  }) {
    this.id = data.id
    this.chatId = data.chatId
    this.role = data.role
    this.parts = data.parts
    this.createdAt = data.createdAt
  }
}
