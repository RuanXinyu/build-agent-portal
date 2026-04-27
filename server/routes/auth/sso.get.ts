import { and, eq } from 'drizzle-orm'
import { getSSOAuthUrl, exchangeCodeForToken, fetchSSOUserInfo } from '~/server/utils/sso'
import { exchangeSSOCookieForToken } from '~/server/utils/tokenExchange'

export default defineEventHandler(async (event) => {
  const query = getQuery(event)
  const code = query.code as string | undefined
  const error = query.error as string | undefined

  // No code — this is the initial login request, redirect to SSO
  if (!code && !error) {
    const state = crypto.randomUUID()
    setCookie(event, 'sso_state', state, {
      httpOnly: true,
      secure: true,
      sameSite: 'lax',
      maxAge: 60 * 10 // 10 minutes
    })
    return sendRedirect(event, getSSOAuthUrl(state))
  }

  // Error from SSO
  if (error) {
    console.error('SSO OAuth error:', error)
    return sendRedirect(event, '/')
  }

  // Callback — exchange code for tokens
  try {
    // Step 1: Exchange code for access token
    const tokenResponse = await exchangeCodeForToken(code!)

    // Step 2: Fetch user info from SSO
    const ssoUser = await fetchSSOUserInfo(tokenResponse.access_token)

    // Step 3: Exchange SSO Cookie for x-auth-token
    const xAuthToken = await exchangeSSOCookieForToken(event)
    if (!xAuthToken) {
      console.error('Failed to exchange SSO Cookie for x-auth-token')
      return sendRedirect(event, '/')
    }

    // Step 4: Upsert user in local database
    const config = useRuntimeConfig()
    const session = await getUserSession(event)
    const providerId = String(ssoUser.id)

    const { db, schema } = await import('hub:db')

    let user = await db.query.users.findFirst({
      where: () => and(
        eq(schema.users.provider, 'sso'),
        eq(schema.users.providerId, providerId)
      )
    })

    if (!user) {
      ;[user] = await db.insert(schema.users).values({
        id: session.id,
        name: ssoUser.name || '',
        email: ssoUser.email || '',
        avatar: ssoUser.avatar || '',
        username: ssoUser.username || '',
        provider: 'sso',
        providerId
      }).returning()
    }

    // Step 5: Set session with user + x-auth-token
    await setUserSession(event, {
      user: {
        id: user.id,
        name: user.name,
        email: user.email,
        avatar: user.avatar,
        username: user.username,
        provider: 'sso',
        providerId: user.providerId
      },
      xAuthToken
    })

    return sendRedirect(event, '/')
  }
  catch (err) {
    console.error('SSO OAuth callback error:', err)
    return sendRedirect(event, '/')
  }
})
