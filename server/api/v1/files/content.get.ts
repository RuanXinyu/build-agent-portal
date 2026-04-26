export default defineEventHandler(async (event) => {
  const config = useRuntimeConfig()
  const query = getQuery(event)
  const path = query.path as string

  if (!path) {
    throw createError({ statusCode: 400, statusMessage: 'path parameter is required' })
  }

  const res = await $fetch<{
    name: string
    language: string | null
    size: number
    content: string | null
    previewable: boolean
    downloadUrl?: string
  }>(`${config.flaskApiUrl}/api/files/content`, {
    params: { path }
  })

  return res
})
