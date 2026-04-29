interface TreeEntry {
  filename: string
  type: 'dir' | 'file'
  size?: number
  files?: TreeEntry[]
}

interface FlaskFilesResponse {
  data: {
    files: TreeEntry[]
  }
  error?: string
}

export default defineEventHandler(async (event) => {
  const chatId = getRouterParam(event, 'id')
  if (!chatId) {
    throw createError({ statusCode: 400, statusMessage: 'Chat ID is required' })
  }

  const query = getQuery(event)
  const filepath = (query.filepath as string) || '/'

  const flaskResponse = await useInternalService<FlaskFilesResponse>(
    event,
    `/buildagent/v1/agent/chats/${chatId}/workspace/output/files`,
    { params: { filepath, recursive: 'true', depth: '2' } }
  )

  if (flaskResponse.error) {
    throw createError({ statusCode: 400, statusMessage: flaskResponse.error })
  }

  return flaskResponse.data
})
