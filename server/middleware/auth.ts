export default defineEventHandler(async (event) => {
  const url = getRequestURL(event)

  // Only apply to /api/ routes, skip auth routes
  if (!url.pathname.startsWith('/api/') || url.pathname.startsWith('/api/auth/')) {
    return
  }

  const config = useRuntimeConfig()

  // If static token is set, useInternalService handles it — no need for SSO refresh
  if (config.staticAuthToken) {
    return
  }

  const session = await getUserSession(event)
  const xAuthToken = session.secure?.xAuthToken

  console.log('[SSO] Auth middleware:', url.pathname, 'hasToken:', !!xAuthToken)

  // If no x-auth-token in session, attempt to exchange SSO Cookie for one
  if (!xAuthToken) {
    const newToken = await exchangeSSOCookieForToken(event)
    if (newToken) {
      console.log('[SSO] Auth middleware: token refreshed via SSO Cookie')
      await setUserSession(event, { secure: { xAuthToken: newToken } })
    } else {
      console.warn('[SSO] Auth middleware: no token for', url.pathname)
      throw createError({
        statusCode: 401,
        statusMessage: 'Authentication required'
      })
    }
  }
})
