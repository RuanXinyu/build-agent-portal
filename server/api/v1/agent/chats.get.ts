export default defineEventHandler(async (event) => {
  const res = await useInternalService<{ id: string, chat_id: string, title: string | null, createdAt: string }[]>(
    event,
    '/api/chats'
  )

  return res.map(chat => ({
    ...chat,
    userId: 'mock-user',
    createdAt: new Date(chat.createdAt)
  }))
})
