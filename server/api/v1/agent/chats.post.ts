import { z } from 'zod'

export default defineEventHandler(async (event) => {
  const body = await readValidatedBody(event, z.object({
    app_name: z.string().optional(),
    app_chat_id: z.string().optional(),
    prompt: z.string()
  }).parse)

  const config = useRuntimeConfig()
  const chat = await $fetch<{
    id: string
    chat_id: string
    title: string | null
    createdAt: string
  }>(`${config.flaskApiUrl}/api/chats`, {
    method: 'POST',
    body: { message: body.prompt }
  })

  return chat
})
