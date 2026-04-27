import { ofetch } from 'ofetch'
import type { H3Event } from 'h3'

interface InternalServiceOptions {
  method?: string
  params?: Record<string, string>
  body?: Record<string, unknown> | null
  headers?: Record<string, string>
}

interface SessionData {
  xAuthToken?: string
  [key: string]: unknown
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
  const sessionData = session as SessionData
  const xAuthToken = sessionData.xAuthToken

  if (!xAuthToken) {
    throw createError({
      statusCode: 401,
      statusMessage: 'No x-auth-token in session'
    })
  }

  try {
    return await ofetch<T>(`${config.flaskApiUrl}${path}`, {
      method: options.method || 'GET',
      params: options.params,
      body: options.body,
      headers: {
        'X-Auth-Token': xAuthToken,
        ...options.headers
      }
    })
  } catch (error: unknown) {
    const fetchError = error as { statusCode?: number }
    if (fetchError.statusCode !== 401) {
      throw error
    }

    // Token expired — try refreshing via SSO Cookie
    const newToken = await exchangeSSOCookieForToken(event)
    if (!newToken) {
      throw createError({
        statusCode: 401,
        statusMessage: 'SSO session expired'
      })
    }

    // Update session with new token
    await setUserSession(event, { xAuthToken: newToken } as Record<string, unknown>)

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
