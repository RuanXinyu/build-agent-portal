import { z } from 'zod'

export default defineEventHandler(async (event) => {
  const body = await readValidatedBody(event, z.object({
    chat_id: z.string().optional(),
    prompt: z.string()
  }).parse)

  const result = await useInternalService<{
    chat_id: string
    message_id: string
  }>(event, '/api/chats', {
    method: 'POST',
    body: {
      chat_id: body.chat_id || '',
      prompt: body.prompt
    }
  })

  return result
})
