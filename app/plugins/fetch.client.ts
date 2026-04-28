export default defineNuxtPlugin(() => {
  const nuxt = useNuxtApp()

  nuxt.hook('app:error' as any, (error: any) => {
    if (error?.statusCode === 401) {
      handle401()
    }
  })
})

let isRedirecting = false

async function handle401() {
  if (isRedirecting) return
  isRedirecting = true

  const config = useRuntimeConfig()
  const { loggedIn, clear } = useUserSession()

  if (config.public.hasStaticAuthToken) {
    const toast = useToast()
    toast.add({
      title: '认证失败',
      description: 'Static auth token 无效，请检查 NUXT_STATIC_AUTH_TOKEN 配置',
      color: 'error'
    })
    isRedirecting = false
    return
  }

  if (loggedIn.value) {
    await clear()
  }

  window.location.href = '/auth/sso'
}
