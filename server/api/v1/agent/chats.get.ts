function toDate(value: unknown): Date {
  if (value instanceof Date) return value

  if (typeof value === 'number') {
    const ms = value < 1e12 ? value * 1000 : value
    return new Date(ms)
  }

  if (typeof value === 'string') {
    const numericValue = Number(value)
    if (!Number.isNaN(numericValue)) {
      const ms = numericValue < 1e12 ? numericValue * 1000 : numericValue
      return new Date(ms)
    }
    return new Date(value)
  }

  return new Date(0)
}

interface FlaskChatItem {
  id: string
  chat_id: string
  title: string | null
  created_at: string | number
}

interface ChatsPagination {
  page: number
  page_size: number
  total: number
  total_pages: number
  has_next: boolean
  has_prev: boolean
}

interface FlaskChatsPageResponse {
  data: FlaskChatItem[]
  pagination?: ChatsPagination
}

function mapChats(items: FlaskChatItem[]) {
  return items.map(chat => ({
    ...chat,
    createdAt: toDate(chat.created_at)
  }))
}

export default defineEventHandler(async (event) => {
  const query = getQuery(event)
  const page = query.page ? String(query.page) : undefined
  const pageSize = query.page_size ? String(query.page_size) : undefined
  const limit = query.limit ? String(query.limit) : undefined
  const hasPaginationQuery = Boolean(page || pageSize || limit)

  const params: Record<string, string> | undefined = hasPaginationQuery
    ? {
        ...(page ? { page } : {}),
        ...(pageSize ? { page_size: pageSize } : {}),
        ...(limit ? { limit } : {})
      }
    : undefined

  const res = await useInternalService<FlaskChatsPageResponse>(event, '/buildagent/v1/agent/chats', { params })

  const mappedChats = mapChats(res.data || [])
  if (!hasPaginationQuery) {
    return mappedChats
  }

  return {
    data: mappedChats,
    pagination: res.pagination
  }
})
