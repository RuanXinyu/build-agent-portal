# SSO Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace GitHub OAuth with internal SSO login, add server-side x-auth-token management, and proxy all internal service API calls with authentication.

**Architecture:** Keep nuxt-auth-utils for session management. Custom OAuth 2.0 authorization code handler for SSO. Server middleware handles x-auth-token lifecycle (acquire, store, refresh). All internal service calls proxied through a shared utility that injects x-auth-token from session.

**Tech Stack:** Nuxt 4, nuxt-auth-utils, Drizzle ORM (SQLite), h3 event handlers, $fetch

---

## File Structure

| Action | File | Responsibility |
|--------|------|---------------|
| Modify | `shared/types/auth.d.ts` | User type: change provider from `'github'` to `'sso'` |
| Modify | `server/db/schema.ts` | Users table: update provider enum to `'sso'` |
| Modify | `nuxt.config.ts` | Add SSO runtime config vars |
| Modify | `.env` | Add SSO environment variables |
| Modify | `.env.example` | Update with SSO env var template |
| Create | `server/utils/sso.ts` | SSO OAuth 2.0 helpers: authorization URL builder, code-for-token exchange, UserInfo fetch |
| Create | `server/utils/tokenExchange.ts` | SSO Cookie → x-auth-token exchange function |
| Create | `server/utils/internalService.ts` | Generic internal service request utility (reads x-auth-token from session, injects header) |
| Create | `server/routes/auth/sso.get.ts` | OAuth callback handler: exchange code, get x-auth-token, get UserInfo, upsert user, set session |
| Create | `server/middleware/auth.ts` | Auth middleware: ensure session + x-auth-token, handle token refresh on 401 |
| Modify | `server/api/v1/agent/chats.get.ts` | Replace `$fetch(config.backendApiUrl)` with `useInternalService()` |
| Modify | `server/api/v1/agent/chats.post.ts` | Replace `$fetch(config.backendApiUrl)` with `useInternalService()` |
| Modify | `server/api/v1/agent/chats/[id].get.ts` | Replace `$fetch(config.backendApiUrl)` with `useInternalService()` |
| Modify | `server/api/v1/files.get.ts` | Replace `$fetch(config.backendApiUrl)` with `useInternalService()` |
| Modify | `server/api/v1/files/content.get.ts` | Replace `$fetch(config.backendApiUrl)` with `useInternalService()` |
| Modify | `server/api/v1/files/download.get.ts` | Replace `$fetch(config.backendApiUrl)` with `useInternalService()` |
| Modify | `app/components/AppHeader.vue` | Change login URL from `/auth/github` to `/auth/sso` |
| Delete | `server/routes/auth/github.get.ts` | Remove GitHub OAuth handler |

---

### Task 1: Update environment variables and runtime config

**Files:**
- Modify: `nuxt.config.ts:30-32`
- Modify: `.env`
- Modify: `.env.example`

- [ ] **Step 1: Add SSO runtime config to `nuxt.config.ts`**

Replace the existing `runtimeConfig` block (lines 30-32) with:

```ts
runtimeConfig: {
    backendApiUrl: process.env.BACKEND_API_URL || 'http://localhost:5001',
    ssoClientId: process.env.NUXT_SSO_CLIENT_ID || '',
    ssoClientSecret: process.env.NUXT_SSO_CLIENT_SECRET || '',
    ssoAuthorizeUrl: process.env.NUXT_SSO_AUTHORIZE_URL || '',
    ssoTokenUrl: process.env.NUXT_SSO_TOKEN_URL || '',
    ssoUserinfoUrl: process.env.NUXT_SSO_USERINFO_URL || '',
    ssoRedirectUrl: process.env.NUXT_SSO_REDIRECT_URL || '',
    tokenExchangeUrl: process.env.NUXT_TOKEN_EXCHANGE_URL || '',
    ssoCookieName: process.env.NUXT_SSO_COOKIE_NAME || 'sso_token'
  },
```

- [ ] **Step 2: Update `.env` file**

Add SSO variables after the existing content:

```
NUXT_SSO_CLIENT_ID=
NUXT_SSO_CLIENT_SECRET=
NUXT_SSO_AUTHORIZE_URL=
NUXT_SSO_TOKEN_URL=
NUXT_SSO_USERINFO_URL=
NUXT_SSO_REDIRECT_URL=
NUXT_TOKEN_EXCHANGE_URL=
NUXT_SSO_COOKIE_NAME=sso_token
```

- [ ] **Step 3: Update `.env.example` file**

Replace the GitHub OAuth entries with SSO entries. Full new content:

```
# Password for nuxt-auth-utils (minimum 32 characters)
NUXT_SESSION_PASSWORD=
# SSO OAuth configuration
NUXT_SSO_CLIENT_ID=
NUXT_SSO_CLIENT_SECRET=
NUXT_SSO_AUTHORIZE_URL=
NUXT_SSO_TOKEN_URL=
NUXT_SSO_USERINFO_URL=
NUXT_SSO_REDIRECT_URL=
NUXT_TOKEN_EXCHANGE_URL=
NUXT_SSO_COOKIE_NAME=sso_token
# Internal service base URL
BACKEND_API_URL=http://localhost:5001
# Blob read write token
BLOB_READ_WRITE_TOKEN=
```

- [ ] **Step 4: Commit**

```bash
git add nuxt.config.ts .env .env.example
git commit -m "feat: add SSO environment variables and runtime config"
```

---

### Task 2: Update User type definition and database schema

**Files:**
- Modify: `shared/types/auth.d.ts`
- Modify: `server/db/schema.ts`

- [ ] **Step 1: Update `shared/types/auth.d.ts`**

Replace the full file content:

```ts
// auth.d.ts
declare module '#auth-utils' {
  interface User {
    id: string
    name: string
    email: string
    avatar: string
    username: string
    provider: 'sso'
    providerId: string
  }
}

export {}
```

- [ ] **Step 2: Update `server/db/schema.ts` — change provider enum**

In `server/db/schema.ts` line 14, change:

```ts
// FROM:
provider: text('provider', { enum: ['github'] }).notNull(),
// TO:
provider: text('provider', { enum: ['sso'] }).notNull(),
```

- [ ] **Step 3: Generate and apply database migration**

Run:
```bash
pnpm db:generate
pnpm db:migrate
```

- [ ] **Step 4: Commit**

```bash
git add shared/types/auth.d.ts server/db/schema.ts
git commit -m "feat: update user type and schema from github to sso provider"
```

---

### Task 3: Create SSO OAuth utility

**Files:**
- Create: `server/utils/sso.ts`

This utility handles the SSO OAuth 2.0 protocol: building the authorization URL, exchanging authorization code for access token, and fetching user info.

- [ ] **Step 1: Create `server/utils/sso.ts`**

```ts
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
    headers: {
      Authorization: `Bearer ${accessToken}`
    }
  })
}
```

- [ ] **Step 2: Verify no TypeScript errors**

Run:
```bash
pnpm typecheck
```

Expected: No errors related to `server/utils/sso.ts`

- [ ] **Step 3: Commit**

```bash
git add server/utils/sso.ts
git commit -m "feat: add SSO OAuth utility functions"
```

---

### Task 4: Create token exchange utility

**Files:**
- Create: `server/utils/tokenExchange.ts`

This utility handles the SSO Cookie → x-auth-token exchange. The Nuxt server reads the SSO Cookie from the incoming request and calls the token exchange endpoint to obtain x-auth-token.

- [ ] **Step 1: Create `server/utils/tokenExchange.ts`**

```ts
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
    return null
  }

  try {
    const res = await ofetch<TokenExchangeResponse>(config.tokenExchangeUrl, {
      method: 'POST',
      headers: {
        Cookie: `${config.ssoCookieName}=${ssoCookie}`
      }
    })
    return res.token
  }
  catch (error: unknown) {
    const status = (error as { statusCode?: number })?.statusCode
    if (status === 401) {
      console.warn('SSO Cookie expired during token exchange')
      return null
    }
    throw error
  }
}
```

- [ ] **Step 2: Verify no TypeScript errors**

Run:
```bash
pnpm typecheck
```

- [ ] **Step 3: Commit**

```bash
git add server/utils/tokenExchange.ts
git commit -m "feat: add SSO Cookie to x-auth-token exchange utility"
```

---

### Task 5: Create internal service request utility

**Files:**
- Create: `server/utils/internalService.ts`

This is the shared utility that all server API routes use to call the internal service. It reads x-auth-token from session and injects the `X-Auth-Token` header.

- [ ] **Step 1: Create `server/utils/internalService.ts`**

```ts
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

  return await ofetch<T>(`${config.backendApiUrl}${path}`, {
    method: options.method || 'GET',
    params: options.params,
    body: options.body,
    headers: {
      'X-Auth-Token': xAuthToken,
      ...options.headers
    }
  })
}
```

- [ ] **Step 2: Verify no TypeScript errors**

Run:
```bash
pnpm typecheck
```

- [ ] **Step 3: Commit**

```bash
git add server/utils/internalService.ts
git commit -m "feat: add internal service request utility with x-auth-token"
```

---

### Task 6: Create auth middleware with token refresh

**Files:**
- Create: `server/middleware/auth.ts`

This middleware intercepts all `/api/` requests. It ensures the session has an x-auth-token. If the internal service returns 401 (token expired), it attempts to refresh using the SSO Cookie from the request. If SSO Cookie is also expired, it returns 401 to the frontend.

- [ ] **Step 1: Create `server/middleware/auth.ts`**

```ts
import { exchangeSSOCookieForToken } from '~/server/utils/tokenExchange'

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
```

Note: The 401 retry logic for expired x-auth-token will be handled in `useInternalService` — see Task 7 where we add retry-on-401 behavior to the internal service utility. The middleware ensures a token exists before the request reaches the API route.

- [ ] **Step 2: Verify no TypeScript errors**

Run:
```bash
pnpm typecheck
```

- [ ] **Step 3: Commit**

```bash
git add server/middleware/auth.ts
git commit -m "feat: add auth middleware with SSO Cookie token exchange"
```

---

### Task 7: Add token refresh retry to internal service utility

**Files:**
- Modify: `server/utils/internalService.ts`

When the internal service returns 401, the utility should attempt to refresh x-auth-token using the SSO Cookie and retry the request once.

- [ ] **Step 1: Update `server/utils/internalService.ts`**

Replace the full file with:

```ts
import { ofetch } from 'ofetch'
import type { H3Event } from 'h3'
import { exchangeSSOCookieForToken } from '~/server/utils/tokenExchange'

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
    return await ofetch<T>(`${config.backendApiUrl}${path}`, {
      method: options.method || 'GET',
      params: options.params,
      body: options.body,
      headers: {
        'X-Auth-Token': xAuthToken,
        ...options.headers
      }
    })
  }
  catch (error: unknown) {
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
    return await ofetch<T>(`${config.backendApiUrl}${path}`, {
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
```

- [ ] **Step 2: Verify no TypeScript errors**

Run:
```bash
pnpm typecheck
```

- [ ] **Step 3: Commit**

```bash
git add server/utils/internalService.ts
git commit -m "feat: add token refresh retry to internal service utility"
```

---

### Task 8: Update server API routes to use internal service utility

**Files:**
- Modify: `server/api/v1/agent/chats.get.ts`
- Modify: `server/api/v1/agent/chats.post.ts`
- Modify: `server/api/v1/agent/chats/[id].get.ts`
- Modify: `server/api/v1/files.get.ts`
- Modify: `server/api/v1/files/content.get.ts`
- Modify: `server/api/v1/files/download.get.ts`

All routes replace direct `$fetch(config.backendApiUrl)` calls with `useInternalService(event, path, options)`. The utility handles auth headers, so routes only specify the path relative to the base URL.

- [ ] **Step 1: Update `server/api/v1/agent/chats.get.ts`**

Replace the full file:

```ts
export default defineEventHandler(async (event) => {
  const res = await useInternalService<{ id: string, chat_id: string, title: string | null, createdAt: string }[]>(
    event,
    '/api/chats'
  )

  return res.map(chat => ({
    ...chat,
    userId: 'mock-user',
    createdAt: new Date(chat.createdAt)
  }))
})
```

- [ ] **Step 2: Update `server/api/v1/agent/chats.post.ts`**

Replace the full file:

```ts
import { z } from 'zod'

export default defineEventHandler(async (event) => {
  const body = await readValidatedBody(event, z.object({
    chat_id: z.string().optional(),
    prompt: z.string()
  }).parse)

  const result = await useInternalService<{
    chat_id: string
    message_id: string
  }>(event, '/api/chats', {
    method: 'POST',
    body: {
      chat_id: body.chat_id || '',
      prompt: body.prompt
    }
  })

  return result
})
```

- [ ] **Step 3: Update `server/api/v1/agent/chats/[id].get.ts`**

This is the largest file. Only the `$fetch` calls change — they now go through `useInternalService`. Replace the full file:

```ts
import { createUIMessageStream, createUIMessageStreamResponse } from 'ai'
import { z } from 'zod'

interface OpenCodeEvent {
  type: string
  timestamp: number
  sessionID: string
  part?: {
    id?: string
    messageID?: string
    sessionID?: string
    type?: string
    text?: string
    tool?: string
    callID?: string
    state?: {
      status?: string
      input?: unknown
      output?: unknown
    }
    reason?: string
    tokens?: unknown
    cost?: number
    title?: string
    time?: { start: number; end: number }
  }
}

interface FlaskChat {
  id: string
  chat_id: string
  title: string | null
  createdAt: string
}

function parseNDJSON(text: string): OpenCodeEvent[] {
  const events: OpenCodeEvent[] = []
  for (const line of text.split('\n')) {
    const trimmed = line.trim()
    if (!trimmed) continue
    try {
      events.push(JSON.parse(trimmed))
    }
    catch {
      // skip malformed lines
    }
  }
  return events
}

function convertToMessages(events: OpenCodeEvent[]) {
  const messageMap = new Map<string, { role: 'assistant'; parts: unknown[]; createdAt: string }>()

  let currentMessageId = ''
  for (const event of events) {
    if (event.type === 'chat.completed') continue

    const messageId = event.part?.messageID || currentMessageId
    if (event.part?.messageID) {
      currentMessageId = messageId
    }

    if (!messageId) continue

    if (!messageMap.has(messageId)) {
      messageMap.set(messageId, {
        role: 'assistant',
        parts: [],
        createdAt: new Date(event.timestamp).toISOString()
      })
    }

    const msg = messageMap.get(messageId)!

    switch (event.type) {
      case 'step_start':
        msg.parts.push({ type: 'step-start' })
        break
      case 'text':
        msg.parts.push({ type: 'text', text: event.part?.text || '' })
        break
      case 'tool_use': {
        const part = event.part
        msg.parts.push({
          type: `tool-${part?.tool || 'unknown'}`,
          toolCallId: part?.callID || '',
          state: part?.state?.status === 'completed' ? 'output-available' : 'input-available',
          input: part?.state?.input,
          ...(part?.state?.status === 'completed' && { output: part.state.output })
        })
        break
      }
    }
  }

  const messages: Array<{
    id: string
    role: string
    parts: unknown[]
    createdAt: string
  }> = []

  for (const [id, msg] of messageMap) {
    messages.push({
      id,
      role: msg.role,
      parts: msg.parts,
      createdAt: msg.createdAt
    })
  }

  return messages
}

export default defineEventHandler(async (event) => {
  const { id } = await getValidatedRouterParams(
    event,
    z.object({ id: z.string() }).parse
  )

  const query = getQuery(event)
  const isStream = query.stream === 'true'
  const afterTs = query.after_ts ? Number(query.after_ts) : undefined

  const chats = await useInternalService<FlaskChat[]>(event, '/api/chats')
  const chat = chats.find(c => c.id === id || c.chat_id === id)

  if (!chat) {
    throw createError({ statusCode: 404, statusMessage: 'Chat not found' })
  }

  // SSE streaming mode
  if (isStream) {
    const session = await getUserSession(event)
    const sessionData = session as { xAuthToken?: string }
    const xAuthToken = sessionData.xAuthToken

    const stream = createUIMessageStream({
      execute: async ({ writer }) => {
        let url = `/api/chats/${id}/stream`
        if (afterTs) {
          url += `?after_ts=${afterTs}`
        }

        const config = useRuntimeConfig()
        const response = await fetch(`${config.backendApiUrl}${url}`, {
          headers: {
            'X-Auth-Token': xAuthToken || ''
          }
        })

        if (!response.ok) {
          throw createError({
            statusCode: response.status,
            statusMessage: 'Stream fetch failed'
          })
        }

        const reader = response.body?.getReader()
        if (!reader) {
          throw createError({
            statusCode: 500,
            statusMessage: 'Failed to read stream'
          })
        }

        const decoder = new TextDecoder()
        let buffer = ''
        let textId = 0

        try {
          while (true) {
            const { done, value } = await reader.read()
            if (done) break

            buffer += decoder.decode(value, { stream: true })
            const lines = buffer.split('\n')
            buffer = lines.pop() || ''

            for (const line of lines) {
              const trimmed = line.trim()
              if (!trimmed) continue

              let opencodeEvent: OpenCodeEvent
              try {
                opencodeEvent = JSON.parse(trimmed)
              }
              catch {
                continue
              }

              switch (opencodeEvent.type) {
                case 'step_start':
                  writer.write({ type: 'start-step' })
                  break
                case 'text': {
                  const tid = `txt-${++textId}`
                  writer.write({ type: 'text-start', id: tid })
                  writer.write({
                    type: 'text-delta',
                    id: tid,
                    delta: opencodeEvent.part?.text || ''
                  })
                  writer.write({ type: 'text-end', id: tid })
                  break
                }
                case 'tool_use': {
                  const part = opencodeEvent.part
                  if (part?.callID) {
                    writer.write({
                      type: 'tool-input-available',
                      toolCallId: part.callID,
                      toolName: part.tool || 'unknown',
                      input: part.state?.input ?? {}
                    })
                    if (
                      part.state?.status === 'completed'
                      && part.state.output !== undefined
                    ) {
                      writer.write({
                        type: 'tool-output-available',
                        toolCallId: part.callID,
                        output: part.state.output
                      })
                    }
                  }
                  break
                }
                case 'step_finish':
                  writer.write({ type: 'finish-step' })
                  break
                case 'chat.completed':
                  break
              }
            }
          }
        }
        finally {
          reader.releaseLock()
        }
      }
    })

    return createUIMessageStreamResponse({ stream })
  }

  // JSON initial load mode
  const session = await getUserSession(event)
  const sessionData = session as { xAuthToken?: string }
  const xAuthToken = sessionData.xAuthToken
  const config = useRuntimeConfig()

  const response = await fetch(
    `${config.backendApiUrl}/api/chats/${id}/stream`,
    {
      headers: {
        'X-Auth-Token': xAuthToken || ''
      }
    }
  )
  if (!response.ok) {
    throw createError({
      statusCode: response.status,
      statusMessage: 'Chat not found'
    })
  }

  const reader = response.body?.getReader()
  if (!reader) {
    throw createError({
      statusCode: 500,
      statusMessage: 'Failed to read stream'
    })
  }

  const decoder = new TextDecoder()
  let fullText = ''

  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      fullText += decoder.decode(value, { stream: true })
    }
  }
  finally {
    reader.releaseLock()
  }

  const events = parseNDJSON(fullText)
  const messages = convertToMessages(events)

  let lastTimestamp = 0
  for (const ev of events) {
    if (ev.timestamp > lastTimestamp) {
      lastTimestamp = ev.timestamp
    }
  }

  return {
    id: chat.id,
    title: chat.title,
    createdAt: chat.createdAt,
    messages,
    lastTimestamp,
    isOwner: true
  }
})
```

Note: The streaming fetch calls in this file use raw `fetch` with explicit headers because `ofetch` / `useInternalService` does not support streaming response bodies well. The token is read directly from session for these cases.

- [ ] **Step 4: Update `server/api/v1/files.get.ts`**

Replace the full file:

```ts
export default defineEventHandler(async (event) => {
  const query = getQuery(event)
  const path = (query.path as string) || '~'

  return await useInternalService<{
    entries: Array<{
      name: string
      path: string
      type: 'directory' | 'file'
      size?: number
      language?: string | null
    }>
  }>(event, '/api/files', {
    params: { path }
  })
})
```

- [ ] **Step 5: Update `server/api/v1/files/content.get.ts`**

Replace the full file:

```ts
export default defineEventHandler(async (event) => {
  const query = getQuery(event)
  const path = query.path as string

  if (!path) {
    throw createError({ statusCode: 400, statusMessage: 'path parameter is required' })
  }

  return await useInternalService<{
    name: string
    language: string | null
    size: number
    content: string | null
    previewable: boolean
    downloadUrl?: string
  }>(event, '/api/files/content', {
    params: { path }
  })
})
```

- [ ] **Step 6: Update `server/api/v1/files/download.get.ts`**

Replace the full file:

```ts
export default defineEventHandler(async (event) => {
  const query = getQuery(event)
  const path = query.path as string

  if (!path) {
    throw createError({ statusCode: 400, statusMessage: 'path parameter is required' })
  }

  const res = await useInternalService<ArrayBuffer>(event, '/api/files/download', {
    params: { path }
  })

  const filename = path.split('/').pop() || 'file'
  setResponseHeader(event, 'content-type', 'application/octet-stream')
  setResponseHeader(event, 'content-disposition', `attachment; filename="${filename}"`)
  return res
})
```

- [ ] **Step 7: Verify no TypeScript errors**

Run:
```bash
pnpm typecheck
```

- [ ] **Step 8: Commit**

```bash
git add server/api/v1/
git commit -m "feat: update API routes to use internal service with x-auth-token"
```

---

### Task 9: Update frontend login, create SSO route handler, remove GitHub OAuth

**Files:**
- Create: `server/routes/auth/sso.get.ts`
- Modify: `app/components/AppHeader.vue`
- Delete: `server/routes/auth/github.get.ts`

This task creates the combined SSO route handler (redirect + callback), updates the frontend login button, and removes the old GitHub OAuth handler.

- [ ] **Step 1: Create `server/routes/auth/sso.get.ts`**

This single handler covers both the login redirect (no `code` query param) and the OAuth callback (with `code` query param):

```ts
import { db, schema } from 'hub:db'
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
    const session = await getUserSession(event)
    const providerId = String(ssoUser.id)

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
```

- [ ] **Step 2: Update `app/components/AppHeader.vue`**

Update the login button (lines 37-44). Replace:

```vue
      <UserMenu v-if="loggedIn" />
      <UButton
        v-else
        label="登录"
        icon="i-simple-icons-github"
        color="neutral"
        variant="ghost"
        @click="openInPopup('/auth/github')"
      />
```

With:

```vue
      <UserMenu v-if="loggedIn" />
      <UButton
        v-else
        label="登录"
        icon="i-lucide-log-in"
        color="neutral"
        variant="ghost"
        @click="navigateTo('/auth/sso')"
      />
```

Note: We use `navigateTo` instead of `openInPopup` because the SSO login flow requires a full page redirect (not a popup). The SSO provider redirects back to the Nuxt callback URL after login.

- [ ] **Step 3: Delete the GitHub OAuth handler**

```bash
rm server/routes/auth/github.get.ts
```

- [ ] **Step 4: Verify no TypeScript errors**

Run:
```bash
pnpm typecheck
```

- [ ] **Step 5: Commit**

```bash
git add app/components/AppHeader.vue server/routes/auth/sso.get.ts
git rm server/routes/auth/github.get.ts
git commit -m "feat: update login to use SSO, remove GitHub OAuth"
```

---

### Task 10: Add frontend 401 handling

**Files:**
- Modify: `app/components/AppHeader.vue` (or create a composable)

When the frontend receives a 401 from any API call, it should redirect the user to the SSO login page.

- [ ] **Step 1: Create `app/composables/useAuthFetch.ts`**

A composable that wraps `useFetch` / `$fetch` with automatic 401 → redirect-to-login handling:

```ts
export function useAuthFetch() {
  const { loggedIn } = useUserSession()

  async function authFetch<T>(url: string, options?: Parameters<typeof $fetch>[1]): Promise<T> {
    try {
      return await $fetch<T>(url, options)
    }
    catch (error: unknown) {
      const fetchError = error as { statusCode?: number }
      if (fetchError.statusCode === 401) {
        navigateTo('/auth/sso')
      }
      throw error
    }
  }

  return { authFetch }
}
```

- [ ] **Step 2: Verify no TypeScript errors**

Run:
```bash
pnpm typecheck
```

- [ ] **Step 3: Commit**

```bash
git add app/composables/useAuthFetch.ts
git commit -m "feat: add authFetch composable with 401 redirect"
```

---

### Task 11: Final verification and cleanup

**Files:**
- All modified files

- [ ] **Step 1: Run TypeScript check on entire project**

Run:
```bash
pnpm typecheck
```

Expected: No errors

- [ ] **Step 2: Run lint check**

Run:
```bash
pnpm lint
```

Expected: No errors (or only pre-existing ones)

- [ ] **Step 3: Verify dev server starts**

Run:
```bash
pnpm dev
```

Expected: Server starts without errors, SSO login redirects to the configured SSO URL

- [ ] **Step 4: Final commit if any fixes were needed**

```bash
git add -A
git commit -m "fix: resolve typecheck and lint issues from SSO integration"
```

---

## Self-Review Checklist

- [x] **Spec coverage:** Each section in the design doc maps to at least one task
- [x] **Login flow:** Task 9 (redirect + callback + upsert + session in single handler)
- [x] **Token management:** Task 4 (exchange) + Task 6 (middleware) + Task 7 (retry)
- [x] **API proxy:** Task 5 (utility) + Task 8 (route updates)
- [x] **Frontend changes:** Task 9 (AppHeader) + Task 10 (401 handling)
- [x] **Type/schema updates:** Task 2
- [x] **Config:** Task 1
- [x] **Placeholder scan:** No TBD/TODO/fill-in-later — all code is complete
- [x] **Type consistency:** `useInternalService<T>` used consistently across all routes; `SessionData` interface with `xAuthToken` used in middleware and utility; `provider: 'sso'` used in schema, types, and callback handler
