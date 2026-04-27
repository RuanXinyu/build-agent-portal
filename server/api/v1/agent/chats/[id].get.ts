import { createUIMessageStream, createUIMessageStreamResponse } from 'ai'
import { z } from 'zod'

interface OpenCodeEvent {
  type: string
  timestamp: number
  sessionID: string
  part?: {
    id?: string
    messageID?: string
    sessionID?: string
    type?: string
    text?: string
    tool?: string
    callID?: string
    state?: {
      status?: string
      input?: unknown
      output?: unknown
    }
    reason?: string
    tokens?: unknown
    cost?: number
    title?: string
    time?: { start: number; end: number }
  }
}

interface FlaskChat {
  id: string
  chat_id: string
  title: string | null
  createdAt: string
}

function parseNDJSON(text: string): OpenCodeEvent[] {
  const events: OpenCodeEvent[] = []
  for (const line of text.split('\n')) {
    const trimmed = line.trim()
    if (!trimmed) continue
    try {
      events.push(JSON.parse(trimmed))
    }
    catch {
      // skip malformed lines
    }
  }
  return events
}

function convertToMessages(events: OpenCodeEvent[]) {
  const messageMap = new Map<string, { role: 'assistant'; parts: unknown[]; createdAt: string }>()

  let currentMessageId = ''
  for (const event of events) {
    if (event.type === 'chat.completed') continue

    const messageId = event.part?.messageID || currentMessageId
    if (event.part?.messageID) {
      currentMessageId = messageId
    }

    if (!messageId) continue

    if (!messageMap.has(messageId)) {
      messageMap.set(messageId, {
        role: 'assistant',
        parts: [],
        createdAt: new Date(event.timestamp).toISOString()
      })
    }

    const msg = messageMap.get(messageId)!

    switch (event.type) {
      case 'step_start':
        msg.parts.push({ type: 'step-start' })
        break
      case 'text':
        msg.parts.push({ type: 'text', text: event.part?.text || '' })
        break
      case 'tool_use': {
        const part = event.part
        msg.parts.push({
          type: `tool-${part?.tool || 'unknown'}`,
          toolCallId: part?.callID || '',
          state: part?.state?.status === 'completed' ? 'output-available' : 'input-available',
          input: part?.state?.input,
          ...(part?.state?.status === 'completed' && { output: part.state.output })
        })
        break
      }
    }
  }

  const messages: Array<{
    id: string
    role: string
    parts: unknown[]
    createdAt: string
  }> = []

  for (const [id, msg] of messageMap) {
    messages.push({
      id,
      role: msg.role,
      parts: msg.parts,
      createdAt: msg.createdAt
    })
  }

  return messages
}

export default defineEventHandler(async (event) => {
  const { id } = await getValidatedRouterParams(
    event,
    z.object({ id: z.string() }).parse
  )

  const query = getQuery(event)
  const isStream = query.stream === 'true'
  const afterTs = query.after_ts ? Number(query.after_ts) : undefined

  const chats = await useInternalService<FlaskChat[]>(event, '/api/chats')
  const chat = chats.find(c => c.id === id || c.chat_id === id)

  if (!chat) {
    throw createError({ statusCode: 404, statusMessage: 'Chat not found' })
  }

  // SSE streaming mode
  if (isStream) {
    const session = await getUserSession(event)
    const sessionData = session as { xAuthToken?: string }
    const xAuthToken = sessionData.xAuthToken

    const stream = createUIMessageStream({
      execute: async ({ writer }) => {
        let url = `/api/chats/${id}/stream`
        if (afterTs) {
          url += `?after_ts=${afterTs}`
        }

        const config = useRuntimeConfig()
        const response = await fetch(`${config.flaskApiUrl}${url}`, {
          headers: {
            'X-Auth-Token': xAuthToken || ''
          }
        })

        if (!response.ok) {
          throw createError({
            statusCode: response.status,
            statusMessage: 'Stream fetch failed'
          })
        }

        const reader = response.body?.getReader()
        if (!reader) {
          throw createError({
            statusCode: 500,
            statusMessage: 'Failed to read stream'
          })
        }

        const decoder = new TextDecoder()
        let buffer = ''
        let textId = 0

        try {
          while (true) {
            const { done, value } = await reader.read()
            if (done) break

            buffer += decoder.decode(value, { stream: true })
            const lines = buffer.split('\n')
            buffer = lines.pop() || ''

            for (const line of lines) {
              const trimmed = line.trim()
              if (!trimmed) continue

              let opencodeEvent: OpenCodeEvent
              try {
                opencodeEvent = JSON.parse(trimmed)
              }
              catch {
                continue
              }

              switch (opencodeEvent.type) {
                case 'step_start':
                  writer.write({ type: 'start-step' })
                  break
                case 'text': {
                  const tid = `txt-${++textId}`
                  writer.write({ type: 'text-start', id: tid })
                  writer.write({
                    type: 'text-delta',
                    id: tid,
                    delta: opencodeEvent.part?.text || ''
                  })
                  writer.write({ type: 'text-end', id: tid })
                  break
                }
                case 'tool_use': {
                  const part = opencodeEvent.part
                  if (part?.callID) {
                    writer.write({
                      type: 'tool-input-available',
                      toolCallId: part.callID,
                      toolName: part.tool || 'unknown',
                      input: part.state?.input ?? {}
                    })
                    if (
                      part.state?.status === 'completed'
                      && part.state.output !== undefined
                    ) {
                      writer.write({
                        type: 'tool-output-available',
                        toolCallId: part.callID,
                        output: part.state.output
                      })
                    }
                  }
                  break
                }
                case 'step_finish':
                  writer.write({ type: 'finish-step' })
                  break
                case 'chat.completed':
                  break
              }
            }
          }
        }
        finally {
          reader.releaseLock()
        }
      }
    })

    return createUIMessageStreamResponse({ stream })
  }

  // JSON initial load mode
  const session = await getUserSession(event)
  const sessionData = session as { xAuthToken?: string }
  const xAuthToken = sessionData.xAuthToken
  const config = useRuntimeConfig()

  const response = await fetch(
    `${config.flaskApiUrl}/api/chats/${id}/stream`,
    {
      headers: {
        'X-Auth-Token': xAuthToken || ''
      }
    }
  )
  if (!response.ok) {
    throw createError({
      statusCode: response.status,
      statusMessage: 'Chat not found'
    })
  }

  const reader = response.body?.getReader()
  if (!reader) {
    throw createError({
      statusCode: 500,
      statusMessage: 'Failed to read stream'
    })
  }

  const decoder = new TextDecoder()
  let fullText = ''

  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      fullText += decoder.decode(value, { stream: true })
    }
  }
  finally {
    reader.releaseLock()
  }

  const events = parseNDJSON(fullText)
  const messages = convertToMessages(events)

  let lastTimestamp = 0
  for (const ev of events) {
    if (ev.timestamp > lastTimestamp) {
      lastTimestamp = ev.timestamp
    }
  }

  return {
    id: chat.id,
    title: chat.title,
    createdAt: chat.createdAt,
    messages,
    lastTimestamp,
    isOwner: true
  }
})
