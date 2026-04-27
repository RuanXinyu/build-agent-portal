interface SessionData {
  xAuthToken?: string
  [key: string]: unknown
}

export default defineEventHandler(async (event) => {
  const url = getRequestURL(event)

  // Only apply to /api/ routes, skip auth routes
  if (!url.pathname.startsWith('/api/') || url.pathname.startsWith('/api/auth/')) {
    return
  }

  const session = await getUserSession(event)
  const sessionData = session as SessionData

  // If no x-auth-token in session, attempt to exchange SSO Cookie for one
  if (!sessionData.xAuthToken) {
    const newToken = await exchangeSSOCookieForToken(event)
    if (newToken) {
      await setUserSession(event, { xAuthToken: newToken } as Record<string, unknown>)
    }
    else {
      throw createError({
        statusCode: 401,
        statusMessage: 'Authentication required'
      })
    }
  }
})
