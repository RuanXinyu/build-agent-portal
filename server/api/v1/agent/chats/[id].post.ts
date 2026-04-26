import { createUIMessageStream, createUIMessageStreamResponse } from 'ai'
import { z } from 'zod'

interface FlaskMessage {
  id: string
  chatId: string
  role: 'user' | 'assistant' | 'system'
  parts: any[]
  createdAt: string
}

export default defineEventHandler(async (event) => {
  const { id } = await getValidatedRouterParams(event, z.object({
    id: z.string()
  }).parse)

  const config = useRuntimeConfig()

  const stream = createUIMessageStream({
    execute: async ({ writer }) => {
      // 调用 Flask SSE 接口获取 mock 消息
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
          } else if (line.startsWith('data: ')) {
            if (currentEvent === 'message') {
              const data = line.slice(6)
              try {
                const msg = JSON.parse(data) as FlaskMessage

                if (msg.role === 'assistant') {
                  writer.write({
                    type: 'message',
                    role: 'assistant',
                    id: msg.id,
                    parts: msg.parts
                  })
                }
              } catch {
                // 忽略解析错误
              }
            }
            currentEvent = ''
          }
        }
      }
    }
  })

  return createUIMessageStreamResponse({ stream })
})
