import { ofetch } from 'ofetch'
import type { H3Event } from 'h3'
import { createHash } from 'node:crypto'

interface TokenExchangeResponse {
  token: string
  expires_in?: number
}

/**
 * Read the incoming cookies and exchange for an x-auth-token.
 * Returns the x-auth-token string, or null if exchange fails.
 */
export async function exchangeSSOCookieForToken(event: H3Event): Promise<string | null> {
  const config = useRuntimeConfig()
  const rawCookie = getRequestHeader(event, 'cookie')

  if (!rawCookie) {
    console.log('[SSO] No Cookie header found in request')
    return null
  }

  if (!config.ssoAccessKey || !config.ssoSecretKey) {
    console.error('[SSO] Missing HW AK/SK for token exchange signing')
    return null
  }

  const exchangePath = new URL(config.tokenExchangeUrl).pathname
  const date = new Date().toISOString()
  const signInput = `${exchangePath}|GET|${date}|${config.ssoAccessKey}|${config.ssoSecretKey}`
  const sign = createHash('sha256').update(signInput).digest('hex')

  try {
    console.log('[SSO] Exchanging cookies for x-auth-token')
    const res = await ofetch<TokenExchangeResponse>(config.tokenExchangeUrl, {
      method: 'GET',
      headers: {
        Cookie: rawCookie,
        'X-HW-ACCESS-KEY': config.ssoAccessKey,
        'X-HW-DATE': date,
        'X-HW-SIGN': sign
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
