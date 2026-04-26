export default defineEventHandler(async (event) => {
  const config = useRuntimeConfig()
  const query = getQuery(event)
  const path = query.path as string

  if (!path) {
    throw createError({ statusCode: 400, statusMessage: 'path parameter is required' })
  }

  const res = await $fetch<ArrayBuffer>(`${config.flaskApiUrl}/api/files/download`, {
    params: { path }
  })

  const filename = path.split('/').pop() || 'file'
  setResponseHeader(event, 'content-type', 'application/octet-stream')
  setResponseHeader(event, 'content-disposition', `attachment; filename="${filename}"`)
  return res
})
