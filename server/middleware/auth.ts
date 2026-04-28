export default defineEventHandler(async (event) => {
  const url = getRequestURL(event)

  // Only apply to /api/ routes, skip auth routes
  if (!url.pathname.startsWith('/api/') || url.pathname.startsWith('/api/auth/')) {
    return
  }

  const session = await getUserSession(event)
  const xAuthToken = session.secure?.xAuthToken

  // If no x-auth-token in session, attempt to exchange SSO Cookie for one
  if (!xAuthToken) {
    const newToken = await exchangeSSOCookieForToken(event)
    if (newToken) {
      await setUserSession(event, { secure: { xAuthToken: newToken } })
    } else {
      throw createError({
        statusCode: 401,
        statusMessage: 'Authentication required'
      })
    }
  }
})
