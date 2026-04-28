import { ofetch } from 'ofetch'

interface SSOUser {
  id: string | number
  name: string
  email: string
  avatar: string
  username: string
}

interface SSOTokenResponse {
  access_token: string
  token_type: string
  expires_in?: number
  refresh_token?: string
}

/**
 * Build the SSO authorization URL to redirect the user to.
 */
export function getSSOAuthUrl(state: string): string {
  const config = useRuntimeConfig()
  const params = new URLSearchParams({
    response_type: 'code',
    client_id: config.ssoClientId,
    redirect_uri: config.ssoRedirectUrl,
    state
  })
  return `${config.ssoAuthorizeUrl}?${params.toString()}`
}

/**
 * Exchange an authorization code for an access token.
 */
export async function exchangeCodeForToken(code: string): Promise<SSOTokenResponse> {
  const config = useRuntimeConfig()
  return await ofetch<SSOTokenResponse>(config.ssoTokenUrl, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded'
    },
    body: new URLSearchParams({
      grant_type: 'authorization_code',
      code,
      client_id: config.ssoClientId,
      client_secret: config.ssoClientSecret,
      redirect_uri: config.ssoRedirectUrl
    }).toString()
  })
}

/**
 * Fetch user info from SSO using the access token.
 */
export async function fetchSSOUserInfo(accessToken: string): Promise<SSOUser> {
  const config = useRuntimeConfig()
  return await ofetch<SSOUser>(config.ssoUserinfoUrl, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: {
      client_id: config.ssoClientId,
      access_token: accessToken,
      scope: 'base.profile'
    }
  })
}
