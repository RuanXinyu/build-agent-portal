export class Chat {
  id: string
  chat_id: string
  title: string | null
  userId: string
  visibility: 'public' | 'private'
  createdAt: Date

  constructor(data: {
    id: string
    chat_id: string
    title: string | null
    userId: string
    visibility: 'public' | 'private'
    createdAt: Date
  }) {
    this.id = data.id
    this.chat_id = data.chat_id
    this.title = data.title
    this.userId = data.userId
    this.visibility = data.visibility
    this.createdAt = data.createdAt
  }
}
