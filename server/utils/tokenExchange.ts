import { ofetch } from 'ofetch'
import type { H3Event } from 'h3'

interface TokenExchangeResponse {
  token: string
  expires_in?: number
}

/**
 * Read the SSO Cookie from the incoming request and exchange it for an x-auth-token.
 * Returns the x-auth-token string, or null if exchange fails.
 */
export async function exchangeSSOCookieForToken(event: H3Event): Promise<string | null> {
  const config = useRuntimeConfig()
  const ssoCookie = getCookie(event, config.ssoCookieName)

  if (!ssoCookie) {
    console.log('[SSO] No SSO Cookie found in request')
    return null
  }

  try {
    console.log('[SSO] Exchanging SSO Cookie for x-auth-token')
    const res = await ofetch<TokenExchangeResponse>(config.tokenExchangeUrl, {
      method: 'POST',
      headers: {
        Cookie: `${config.ssoCookieName}=${ssoCookie}`
      }
    })
    console.log('[SSO] Token exchange successful')
    return res.token
  } catch (error: unknown) {
    const status = (error as { statusCode?: number })?.statusCode
    if (status === 401) {
      console.warn('[SSO] SSO Cookie expired during token exchange')
      return null
    }
    console.error('[SSO] Token exchange error:', error)
    throw error
  }
}
