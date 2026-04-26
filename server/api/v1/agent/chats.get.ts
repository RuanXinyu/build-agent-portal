export default defineEventHandler(async () => {
  const config = useRuntimeConfig()
  const res = await $fetch<{ id: string, chat_id: string, title: string | null, createdAt: string }[]>(
    `${config.flaskApiUrl}/api/chats`
  )
  return res.map(chat => ({
    ...chat,
    userId: 'mock-user',
    createdAt: new Date(chat.createdAt)
  }))
})
