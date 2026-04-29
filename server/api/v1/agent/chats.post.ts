import { z } from 'zod'

export default defineEventHandler(async (event) => {
  const body = await readValidatedBody(event, z.object({
    chat_id: z.string().optional(),
    prompt: z.string()
  }).parse)

  const result = await useInternalService<{
    data: {
      chat_id: string
      message_id: string
    }
  }>(event, '/buildagent/v1/agent/chats', {
    method: 'POST',
    body: {
      app_name: "BuildAgentPortal",
      chat_id: body.chat_id || null,
      prompt: body.prompt
    }
  })

  return result.data
})
