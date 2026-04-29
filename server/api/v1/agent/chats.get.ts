export default defineEventHandler(async (event) => {
  const res = await useInternalService<{ 
    data: Array<{
      id: string
      chat_id: string
      title: string | null
      created_at: string
    }>
  }>(
    event,
    '/buildagent/v1/agent/chats?page=1'
  )

  return res.data.map(chat => ({
    ...chat,
    createdAt: new Date(chat.created_at)
  }))
})
