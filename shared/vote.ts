export class Vote {
  chatId: string
  messageId: string
  isUpvoted: boolean

  constructor(data: {
    chatId: string
    messageId: string
    isUpvoted: boolean
  }) {
    this.chatId = data.chatId
    this.messageId = data.messageId
    this.isUpvoted = data.isUpvoted
  }
}
