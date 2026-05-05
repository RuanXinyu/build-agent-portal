export function resolveAuthGuardResult(to: { path: string }, isServer = import.meta.server) {
  const config = useRuntimeConfig()

  // Static token mode doesn't use SSO
  if (config.public.hasStaticAuthToken) return

  if (to.path.startsWith('/chat')) {
    const { loggedIn } = useUserSession()
    if (!loggedIn.value) {
      void isServer
      return navigateTo('/home?auth_required=1')
    }
  }
}

export default defineNuxtRouteMiddleware((to) => resolveAuthGuardResult(to))
