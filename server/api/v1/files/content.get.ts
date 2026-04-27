export default defineEventHandler(async (event) => {
  const query = getQuery(event)
  const path = query.path as string

  if (!path) {
    throw createError({ statusCode: 400, statusMessage: 'path parameter is required' })
  }

  return await useInternalService<{
    name: string
    language: string | null
    size: number
    content: string | null
    previewable: boolean
    downloadUrl?: string
  }>(event, '/api/files/content', {
    params: { path }
  })
})
