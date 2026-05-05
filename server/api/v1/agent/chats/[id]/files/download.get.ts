export default defineEventHandler(async (event) => {
  const chatId = getRouterParam(event, 'id')
  if (!chatId) {
    throw createError({ statusCode: 400, statusMessage: 'Chat ID is required' })
  }

  const query = getQuery(event)
  const path = query.path as string
  if (!path) {
    throw createError({ statusCode: 400, statusMessage: 'path parameter is required' })
  }

  const res = await useInternalService<ArrayBuffer>(
    event,
    `/buildagent/v1/agent/chats/${chatId}/workspace/output/files/download`,
    { params: { filepath: path.replace(/^\/+/, "")} }
  )

  const filename = path.split('/').pop() || 'file'
  setResponseHeader(event, 'content-type', 'application/octet-stream')
  setResponseHeader(event, 'content-disposition', `attachment; filename="${filename}"`)
  return res
})
