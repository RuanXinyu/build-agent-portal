export default defineNuxtRouteMiddleware((to) => {
  const config = useRuntimeConfig()

  // Static token mode doesn't use SSO
  if (config.public.hasStaticAuthToken) return

  if (to.path.startsWith('/chat')) {
    const { loggedIn } = useUserSession()
    if (!loggedIn.value) {
      return navigateTo('/auth/sso', { external: true })
    }
  }
})
