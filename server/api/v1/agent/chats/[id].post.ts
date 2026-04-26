import { createUIMessageStream, createUIMessageStreamResponse } from 'ai'
import { z } from 'zod'

interface FlaskMessage {
  id: string
  chatId: string
  role: 'user' | 'assistant' | 'system'
  parts: any[]
  createdAt: string
}

function writeMessageParts(writer: any, parts: any[]) {
  for (const part of parts) {
    if (part.type === 'text') {
      writer.write({ type: 'text-delta', text: part.text })
    } else if (part.type === 'reasoning') {
      writer.write({ type: 'reasoning', text: part.text })
    } else if (part.type === 'source-url') {
      writer.write({
        type: 'source-url',
        sourceId: part.sourceId,
        url: part.url,
        title: part.title
      })
    } else if (part.type === 'source-document') {
      writer.write({
        type: 'source-document',
        sourceId: part.sourceId,
        mediaType: part.mediaType,
        title: part.title,
        filename: part.filename
      })
    } else if (part.type === 'file') {
      writer.write({
        type: 'file',
        mediaType: part.mediaType,
        url: part.url
      })
    } else if (part.type === 'step-start') {
      writer.write({ type: 'step-start' })
    } else if (part.type.startsWith('tool-')) {
      const toolName = part.type.slice(5) // remove 'tool-' prefix
      writer.write({
        type: 'tool-call',
        toolCallId: part.toolCallId,
        toolName,
        args: part.input
      })
      if (part.output !== undefined) {
        writer.write({
          type: 'tool-result',
          toolCallId: part.toolCallId,
          result: part.output
        })
      }
    }
  }
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
                  writeMessageParts(writer, msg.parts)
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
