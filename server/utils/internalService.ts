import { ofetch } from 'ofetch'
import type { H3Event } from 'h3'

interface InternalServiceOptions {
  method?: string
  params?: Record<string, string>
  body?: Record<string, unknown> | null
  headers?: Record<string, string>
}

/**
 * Make an authenticated request to the internal service.
 * On 401, attempts to refresh x-auth-token via SSO Cookie and retries once.
 */
export async function useInternalService<T>(
  event: H3Event,
  path: string,
  options: InternalServiceOptions = {}
): Promise<T> {
  const config = useRuntimeConfig()
  const session = await getUserSession(event)
  const xAuthToken = session.secure?.xAuthToken

  console.log('[SSO] Internal service call:', path, 'hasToken:', !!xAuthToken)

  const headers: Record<string, string> = { ...options.headers }
  if (xAuthToken) {
    headers['X-Auth-Token'] = xAuthToken
  }

  try {
    return await ofetch<T>(`${config.flaskApiUrl}${path}`, {
      method: options.method || 'GET',
      params: options.params,
      body: options.body,
      headers
    })
  } catch (error: unknown) {
    const fetchError = error as { statusCode?: number }
    if (fetchError.statusCode !== 401) {
      throw error
    }

    // Token expired — try refreshing via SSO Cookie
    const newToken = await exchangeSSOCookieForToken(event)
    if (!newToken) {
      console.warn('[SSO] SSO session expired, cannot refresh token')
      throw createError({
        statusCode: 401,
        statusMessage: 'SSO session expired'
      })
    }

    // Update session with new token
    await setUserSession(event, { secure: { xAuthToken: newToken } })

    console.log('[SSO] Token refreshed, retrying request:', path)

    // Retry the request with the new token
    return await ofetch<T>(`${config.flaskApiUrl}${path}`, {
      method: options.method || 'GET',
      params: options.params,
      body: options.body,
      headers: {
        'X-Auth-Token': newToken,
        ...options.headers
      }
    })
  }
}
