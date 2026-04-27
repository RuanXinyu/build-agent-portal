import { ofetch } from 'ofetch'
import type { H3Event } from 'h3'

interface InternalServiceOptions {
  method?: string
  params?: Record<string, string>
  body?: unknown
  headers?: Record<string, string>
}

interface SessionData {
  xAuthToken?: string
  [key: string]: unknown
}

/**
 * Make an authenticated request to the internal service.
 * Reads x-auth-token from session and injects it as X-Auth-Token header.
 *
 * Throws with statusCode 401 if the token is missing or the internal service rejects it.
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

  return await ofetch<T>(`${config.flaskApiUrl}${path}`, {
    method: options.method || 'GET',
    params: options.params,
    body: options.body,
    headers: {
      'X-Auth-Token': xAuthToken,
      ...options.headers
    }
  })
}
