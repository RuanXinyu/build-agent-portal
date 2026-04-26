import { z } from 'zod'

interface FlaskMessage {
  id: string
  chatId: string
  role: 'user' | 'assistant' | 'system'
  parts: any[]
  createdAt: string
}

interface FlaskChat {
  id: string
  chat_id: string
  title: string | null
  createdAt: string
}

export default defineEventHandler(async (event) => {
  const { id } = await getValidatedRouterParams(event, z.object({
    id: z.string()
  }).parse)

  const config = useRuntimeConfig()

  // 先从会话列表中找到该会话的 title
  const chats = await $fetch<FlaskChat[]>(`${config.flaskApiUrl}/api/chats`)
  const chat = chats.find(c => c.id === id || c.chat_id === id)

  if (!chat) {
    throw createError({ statusCode: 404, statusMessage: 'Chat not found' })
  }

  // 调用 SSE 接口收集所有消息
  const messages: FlaskMessage[] = []

  const response = await fetch(`${config.flaskApiUrl}/api/chats/${id}/stream`)
  if (!response.ok) {
    throw createError({ statusCode: response.status, statusMessage: 'Chat not found' })
  }

  const reader = response.body?.getReader()
  if (!reader) {
    throw createError({ statusCode: 500, statusMessage: 'Failed to read stream' })
  }

  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() || ''

    let currentEvent = ''
    for (const line of lines) {
      if (line.startsWith('event: ')) {
        currentEvent = line.slice(7).trim()
      } else if (line.startsWith('data: ') && currentEvent === 'message') {
        const data = line.slice(6)
        try {
          const msg = JSON.parse(data) as FlaskMessage
          messages.push({
            ...msg,
            createdAt: msg.createdAt
          })
        } catch {
          // 忽略解析错误
        }
        currentEvent = ''
      }
    }
  }

  return {
    id: chat.id,
    title: chat.title,
    createdAt: chat.createdAt,
    messages,
    isOwner: true
  }
})
