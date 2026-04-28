export default defineNitroPlugin(() => {
  sessionHooks.hook('clear', async (event, _session) => {
    const config = useRuntimeConfig()
    const ssoCookieName = config.ssoCookieName

    if (ssoCookieName) {
      // Clear SSO Cookie from parent domain
      deleteCookie(event, ssoCookieName, {
        path: '/',
        domain: '.localhost'
      })
    }
  })
})
