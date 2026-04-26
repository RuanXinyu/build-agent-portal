import { createUIMessageStream, createUIMessageStreamResponse } from 'ai'
import { z } from 'zod'

// --- opencode NDJSON event types ---

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

// --- helpers ---

/**
 * Parse NDJSON text into an array of opencode events.
 * Each non-empty line is expected to be a JSON object.
 */
function parseNDJSON(text: string): OpenCodeEvent[] {
  const events: OpenCodeEvent[] = []
  for (const line of text.split('\n')) {
    const trimmed = line.trim()
    if (!trimmed) continue
    try {
      events.push(JSON.parse(trimmed))
    } catch {
      // skip malformed lines
    }
  }
  return events
}

/**
 * Convert opencode events into frontend UIMessage format for JSON initial load.
 *
 * Events are grouped by part.messageID into separate assistant messages.
 * Each group produces one message with parts that the frontend can render:
 * - step_start  -> { type: 'step-start' }
 * - text        -> { type: 'text', text }
 * - tool_use    -> { type: 'tool-<name>', toolCallId, state, input, output }
 * - step_finish -> (no visible part)
 */
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
        createdAt: new Date(event.timestamp).toISOString(),
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
          ...(part?.state?.status === 'completed' && { output: part.state.output }),
        })
        break
      }
      // step_finish produces no visible frontend part
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
      createdAt: msg.createdAt,
    })
  }

  return messages
}

// --- main handler ---

export default defineEventHandler(async (event) => {
  const { id } = await getValidatedRouterParams(
    event,
    z.object({ id: z.string() }).parse,
  )

  const query = getQuery(event)
  const isStream = query.stream === 'true'
  const afterTs = query.after_ts ? Number(query.after_ts) : undefined

  const config = useRuntimeConfig()

  // Fetch chat metadata from the list endpoint
  const chats = await $fetch<FlaskChat[]>(`${config.flaskApiUrl}/api/chats`)
  const chat = chats.find(c => c.id === id || c.chat_id === id)

  if (!chat) {
    throw createError({ statusCode: 404, statusMessage: 'Chat not found' })
  }

  // ---------------------------------------------------------------
  // SSE streaming mode  (?stream=true&after_ts=xxx)
  // ---------------------------------------------------------------
  if (isStream) {
    const stream = createUIMessageStream({
      execute: async ({ writer }) => {
        // Build Flask URL with optional after_ts for incremental fetch
        let url = `${config.flaskApiUrl}/api/chats/${id}/stream`
        if (afterTs) {
          url += `?after_ts=${afterTs}`
        }

        const response = await fetch(url)
        if (!response.ok) {
          throw createError({
            statusCode: response.status,
            statusMessage: 'Stream fetch failed',
          })
        }

        const reader = response.body?.getReader()
        if (!reader) {
          throw createError({
            statusCode: 500,
            statusMessage: 'Failed to read stream',
          })
        }

        const decoder = new TextDecoder()
        let buffer = ''
        // Track a text id so we can group text-start / text-delta / text-end
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
              } catch {
                continue
              }

              // Convert opencode events to AI SDK stream parts
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
                    delta: opencodeEvent.part?.text || '',
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
                      input: part.state?.input ?? {},
                    })
                    if (
                      part.state?.status === 'completed'
                      && part.state.output !== undefined
                    ) {
                      writer.write({
                        type: 'tool-output-available',
                        toolCallId: part.callID,
                        output: part.state.output,
                      })
                    }
                  }
                  break
                }

                case 'step_finish':
                  writer.write({ type: 'finish-step' })
                  break

                case 'chat.completed':
                  // End of conversation — no stream part generated.
                  // The SSE connection will be closed by the stream ending.
                  break
              }
            }
          }
        } finally {
          reader.releaseLock()
        }
      },
    })

    return createUIMessageStreamResponse({ stream })
  }

  // ---------------------------------------------------------------
  // JSON initial load mode  (no ?stream parameter)
  // ---------------------------------------------------------------
  const response = await fetch(
    `${config.flaskApiUrl}/api/chats/${id}/stream`,
  )
  if (!response.ok) {
    throw createError({
      statusCode: response.status,
      statusMessage: 'Chat not found',
    })
  }

  const reader = response.body?.getReader()
  if (!reader) {
    throw createError({
      statusCode: 500,
      statusMessage: 'Failed to read stream',
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
  } finally {
    reader.releaseLock()
  }

  const events = parseNDJSON(fullText)
  const messages = convertToMessages(events)

  // Track the latest timestamp for incremental queries
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
    isOwner: true,
  }
})
