export default defineEventHandler(async (event) => {
  const config = useRuntimeConfig()
  const query = getQuery(event)
  const path = (query.path as string) || '~'

  const res = await $fetch<{ entries: Array<{
    name: string
    path: string
    type: 'directory' | 'file'
    size?: number
    language?: string | null
  }> }>(`${config.flaskApiUrl}/api/files`, {
    params: { path }
  })

  return res
})
