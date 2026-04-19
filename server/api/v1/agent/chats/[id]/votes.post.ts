import { Vote } from '#shared/vote'
import { z } from 'zod'

const mockVotes: Vote[] = [
  new Vote({ chatId: 'mock-1', messageId: 'msg-1-2', isUpvoted: true }),
  new Vote({ chatId: 'mock-3', messageId: 'msg-3-2', isUpvoted: false })
]

export default defineEventHandler(async (event) => {
  const id = getRouterParam(event, 'id')
  if (!id) {
    throw createError({ statusCode: 400, statusMessage: 'Missing chat id' })
  }

  const { messageId, isUpvoted } = await readValidatedBody(event, z.object({
    messageId: z.string(),
    isUpvoted: z.boolean().optional()
  }).parse)

  const idx = mockVotes.findIndex(v => v.chatId === id && v.messageId === messageId)

  if (isUpvoted === undefined) {
    if (idx !== -1) mockVotes.splice(idx, 1)
  } else {
    if (idx !== -1) {
      mockVotes[idx]!.isUpvoted = isUpvoted
    } else {
      mockVotes.push(new Vote({ chatId: id, messageId, isUpvoted }))
    }
  }

  return { chatId: id, messageId, isUpvoted }
})
