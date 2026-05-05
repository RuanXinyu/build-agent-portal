export default defineNuxtPlugin(() => {
  const nuxt = useNuxtApp()
  const router = useRouter()
  const config = useRuntimeConfig()
  const { loggedIn, clear } = useUserSession()
  const { open } = useLoginModal()
  const toast = useToast()
  let isHandlingAuthFailure = false

  const handle401 = async () => {
    if (isHandlingAuthFailure) return
    isHandlingAuthFailure = true

    try {
      if (config.public.hasStaticAuthToken) {
        toast.add({
          title: '认证失败',
          description: 'Static auth token 无效，请检查 NUXT_STATIC_AUTH_TOKEN 配置',
          color: 'error'
        })
        return
      }

      if (loggedIn.value) {
        await clear()
      }

      await router.replace('/home')
      open('fetch-401')
    } finally {
      isHandlingAuthFailure = false
    }
  }

  const safeHandle401 = () => {
    void handle401().catch((error: unknown) => {
      const message = error instanceof Error ? error.message : String(error)
      console.error('[auth] handle401 failed:', message)
    })
  }

  // Catch 401s from Nuxt error handling (useFetch errors during rendering)
  nuxt.hook('app:error' as any, (error: any) => {
    if (error?.statusCode === 401) {
      safeHandle401()
    }
  })

  // Catch 401s from unhandled $fetch promise rejections
  window.addEventListener('unhandledrejection', (event) => {
    const error = event.reason
    if (error?.statusCode === 401) {
      event.preventDefault()
      safeHandle401()
    }
  })
})
