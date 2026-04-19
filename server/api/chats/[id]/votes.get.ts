import { Vote } from '#shared/vote'

const mockVotes: Vote[] = [
  new Vote({ chatId: 'mock-1', messageId: 'msg-1-2', isUpvoted: true }),
  new Vote({ chatId: 'mock-3', messageId: 'msg-3-2', isUpvoted: false })
]

export default defineEventHandler((event) => {
  const id = getRouterParam(event, 'id')
  if (!id) {
    throw createError({ statusCode: 400, statusMessage: 'Missing chat id' })
  }

  return mockVotes.filter(v => v.chatId === id)
})
