export default defineEventHandler(async (event) => {
  const query = getQuery(event)
  const path = (query.path as string) || '~'

  return await useInternalService<{
    entries: Array<{
      name: string
      path: string
      type: 'directory' | 'file'
      size?: number
      language?: string | null
    }>
  }>(event, '/api/files', {
    params: { path }
  })
})
