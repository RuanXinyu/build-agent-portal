export default defineNitroPlugin(() => {
  sessionHooks.hook('clear', async (event, _session) => {
    if (!event) return

    try {
      const config = useRuntimeConfig()
      const ssoCookieName = config.ssoCookieName

      if (ssoCookieName) {
        deleteCookie(event, ssoCookieName, {
          path: '/',
          domain: '.localhost'
        })
      }
    } catch (err) {
      console.error('[SSO] Failed to clear SSO Cookie on logout:', err)
    }
  })
})
