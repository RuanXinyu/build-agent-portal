# Auth & Navigation Improvements Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add static auth token support for local dev, simplify navbar user menu, remove login page, add global 401 interception, and enforce auth on chat endpoints.

**Architecture:** Server-side static token injection in `useInternalService` bypasses SSO. Client-side global `$fetch` plugin catches 401 responses and redirects to SSO. Navbar simplified to icon-only user menu with compact dropdown.

**Tech Stack:** Nuxt 4, Vue 3, @nuxt/ui, nuxt-auth-utils, ofetch

---

## File Structure

| File | Action | Responsibility |
|------|--------|----------------|
| `nuxt.config.ts` | Modify | Add `staticAuthToken` to runtimeConfig |
| `.env` | Modify | Add `NUXT_STATIC_AUTH_TOKEN` |
| `.env.example` | Modify | Add `NUXT_STATIC_AUTH_TOKEN` |
| `server/utils/internalService.ts` | Modify | Check static token first, skip SSO flow |
| `server/middleware/auth.ts` | Modify | Skip SSO refresh when static token is set |
| `app/components/UserMenu.vue` | Modify | Compact dropdown: theme toggle + logout only |
| `app/components/AppHeader.vue` | Modify | Icon-only user trigger, direct SSO login link |
| `app/pages/login.vue` | Delete | No longer needed |
| `server/routes/auth/sso.get.ts` | Modify | Redirect to `/chat` on success, `/home?error=` on failure |
| `app/composables/useAuthFetch.ts` | Delete | Replaced by global plugin |
| `app/plugins/fetch.client.ts` | Create | Global 401 interception for all `$fetch('/api/*')` calls |
| `app/pages/home.vue` | Modify | Show SSO error toast from query param |

---

### Task 1: Add Static Auth Token to Runtime Config

**Files:**
- Modify: `nuxt.config.ts:30-39`
- Modify: `.env:10`
- Modify: `.env.example:15`

- [ ] **Step 1: Add `staticAuthToken` to `nuxt.config.ts` runtimeConfig**

In `nuxt.config.ts`, add `staticAuthToken` to the `runtimeConfig` block (after `ssoCookieName`):

```typescript
runtimeConfig: {
    flaskApiUrl: process.env.FLASK_API_URL || 'http://localhost:5001',
    ssoClientId: process.env.NUXT_SSO_CLIENT_ID || '',
    ssoClientSecret: process.env.NUXT_SSO_CLIENT_SECRET || '',
    ssoAuthorizeUrl: process.env.NUXT_SSO_AUTHORIZE_URL || '',
    ssoTokenUrl: process.env.NUXT_SSO_TOKEN_URL || '',
    ssoUserinfoUrl: process.env.NUXT_SSO_USERINFO_URL || '',
    ssoRedirectUrl: process.env.NUXT_SSO_REDIRECT_URL || '',
    tokenExchangeUrl: process.env.NUXT_TOKEN_EXCHANGE_URL || '',
    ssoCookieName: process.env.NUXT_SSO_COOKIE_NAME || 'sso_token',
    staticAuthToken: process.env.NUXT_STATIC_AUTH_TOKEN || ''
  },
```

- [ ] **Step 2: Add `NUXT_STATIC_AUTH_TOKEN` to `.env`**

Append to end of `.env`:

```
NUXT_STATIC_AUTH_TOKEN=
```

- [ ] **Step 3: Add `NUXT_STATIC_AUTH_TOKEN` to `.env.example`**

Append after the `BLOB_READ_WRITE_TOKEN=` line:

```
# Static auth token for local development (bypasses SSO)
NUXT_STATIC_AUTH_TOKEN=
```

- [ ] **Step 4: Commit**

```bash
git add nuxt.config.ts .env .env.example
git commit -m "feat: add NUXT_STATIC_AUTH_TOKEN to runtime config"
```

---

### Task 2: Use Static Token in `useInternalService`

**Files:**
- Modify: `server/utils/internalService.ts`

- [ ] **Step 1: Modify `useInternalService` to check static token first**

Replace the entire content of `server/utils/internalService.ts` with:

```typescript
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
 * If NUXT_STATIC_AUTH_TOKEN is set, use it directly (bypasses SSO).
 * Otherwise, on 401, attempts to refresh x-auth-token via SSO Cookie and retries once.
 */
export async function useInternalService<T>(
  event: H3Event,
  path: string,
  options: InternalServiceOptions = {}
): Promise<T> {
  const config = useRuntimeConfig()
  const staticToken = config.staticAuthToken

  // Static token mode: bypass SSO entirely
  if (staticToken) {
    console.log('[SSO] Static token mode:', path)
    return await ofetch<T>(`${config.flaskApiUrl}${path}`, {
      method: options.method || 'GET',
      params: options.params,
      body: options.body,
      headers: {
        'X-Auth-Token': staticToken,
        ...options.headers
      }
    })
  }

  // Normal SSO mode
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
```

- [ ] **Step 2: Commit**

```bash
git add server/utils/internalService.ts
git commit -m "feat: use static auth token in useInternalService when configured"
```

---

### Task 3: Skip Auth Middleware When Static Token Is Set

**Files:**
- Modify: `server/middleware/auth.ts`

- [ ] **Step 1: Add static token check to auth middleware**

Replace the entire content of `server/middleware/auth.ts` with:

```typescript
export default defineEventHandler(async (event) => {
  const url = getRequestURL(event)

  // Only apply to /api/ routes, skip auth routes
  if (!url.pathname.startsWith('/api/') || url.pathname.startsWith('/api/auth/')) {
    return
  }

  const config = useRuntimeConfig()

  // If static token is set, useInternalService handles it — no need for SSO refresh
  if (config.staticAuthToken) {
    return
  }

  const session = await getUserSession(event)
  const xAuthToken = session.secure?.xAuthToken

  console.log('[SSO] Auth middleware:', url.pathname, 'hasToken:', !!xAuthToken)

  // If no x-auth-token in session, attempt to exchange SSO Cookie for one
  if (!xAuthToken) {
    const newToken = await exchangeSSOCookieForToken(event)
    if (newToken) {
      console.log('[SSO] Auth middleware: token refreshed via SSO Cookie')
      await setUserSession(event, { secure: { xAuthToken: newToken } })
    } else {
      console.warn('[SSO] Auth middleware: no token for', url.pathname)
    }
  }
})
```

- [ ] **Step 2: Commit**

```bash
git add server/middleware/auth.ts
git commit -m "feat: skip auth middleware SSO refresh when static token is set"
```

---

### Task 4: Simplify UserMenu to Compact Dropdown

**Files:**
- Modify: `app/components/UserMenu.vue`

- [ ] **Step 1: Replace UserMenu with compact version**

Replace the entire content of `app/components/UserMenu.vue` with:

```vue
<script setup lang="ts">
import type { DropdownMenuItem } from '@nuxt/ui'

const colorMode = useColorMode()
const { clear } = useUserSession()

const items = computed<DropdownMenuItem[][]>(() => ([[{
  label: colorMode.value === 'dark' ? '浅色模式' : '深色模式',
  icon: colorMode.value === 'dark' ? 'i-lucide-sun' : 'i-lucide-moon',
  onSelect() {
    colorMode.preference = colorMode.value === 'dark' ? 'light' : 'dark'
  }
}], [{
  label: '退出登录',
  icon: 'i-lucide-log-out',
  onSelect() {
    clear()
    navigateTo('/home')
  }
}]]))
</script>

<template>
  <UDropdownMenu
    :items="items"
    :content="{ align: 'end', collisionPadding: 12 }"
    :ui="{ content: 'w-40' }"
  >
    <UButton
      icon="i-lucide-user"
      color="neutral"
      variant="ghost"
      size="sm"
      class="data-[state=open]:bg-elevated"
    />
  </UDropdownMenu>
</template>
```

- [ ] **Step 2: Commit**

```bash
git add app/components/UserMenu.vue
git commit -m "feat: simplify UserMenu to compact icon dropdown with theme and logout"
```

---

### Task 5: Update AppHeader for Direct SSO Login

**Files:**
- Modify: `app/components/AppHeader.vue`

- [ ] **Step 1: Update AppHeader login button to go directly to SSO**

In `app/components/AppHeader.vue`, change the login button's `@click` from `navigateTo('/login')` to direct SSO redirect. Also move `<UColorModeButton>` inside the non-logged-in branch since logged-in users now have it in UserMenu.

Replace the `<template #right>` section (lines 34-46):

```vue
    <template #right>
      <slot name="right" />
      <UserMenu v-if="loggedIn" />
      <template v-else>
        <UButton
          label="登录"
          icon="i-lucide-log-in"
          color="neutral"
          variant="ghost"
          @click="window.location.href = '/auth/sso'"
        />
        <UColorModeButton />
      </template>
    </template>
```

- [ ] **Step 2: Commit**

```bash
git add app/components/AppHeader.vue
git commit -m "feat: login button redirects directly to SSO, remove login page dependency"
```

---

### Task 6: Update SSO Callback Redirects

**Files:**
- Modify: `server/routes/auth/sso.get.ts`

- [ ] **Step 1: Change success redirect to `/chat` and error redirect to `/home?error=`**

In `server/routes/auth/sso.get.ts`, make three changes:

1. Line 25 — error redirect from `/login?error=` to `/home?error=`:
```typescript
    return sendRedirect(event, '/home?error=' + encodeURIComponent(error))
```

2. Line 40 — token exchange failure redirect from `/login?error=` to `/home?error=`:
```typescript
      return sendRedirect(event, '/home?error=' + encodeURIComponent('token_exchange_failed'))
```

3. Line 71 — user creation failure redirect from `/login?error=` to `/home?error=`:
```typescript
      return sendRedirect(event, '/home?error=' + encodeURIComponent('user_creation_failed'))
```

4. Line 90 — success redirect from `/` to `/chat`:
```typescript
    return sendRedirect(event, '/chat')
```

5. Line 93 — catch-all error redirect from `/login?error=` to `/home?error=`:
```typescript
    return sendRedirect(event, '/home?error=' + encodeURIComponent('callback_error'))
```

- [ ] **Step 2: Commit**

```bash
git add server/routes/auth/sso.get.ts
git commit -m "feat: SSO success redirects to /chat, errors to /home?error="
```

---

### Task 7: Delete Login Page

**Files:**
- Delete: `app/pages/login.vue`

- [ ] **Step 1: Delete login.vue**

```bash
git rm app/pages/login.vue
```

- [ ] **Step 2: Commit**

```bash
git commit -m "feat: remove standalone login page, SSO handles login directly"
```

---

### Task 8: Create Global 401 Interception Plugin

**Files:**
- Create: `app/plugins/fetch.client.ts`
- Modify: `nuxt.config.ts` — add `public.hasStaticAuthToken` boolean flag
- Delete: `app/composables/useAuthFetch.ts`

- [ ] **Step 1: Add `hasStaticAuthToken` flag to `nuxt.config.ts` runtimeConfig.public**

In `nuxt.config.ts`, add a `public` block inside `runtimeConfig` (we only expose a boolean, not the actual token value):

```typescript
  runtimeConfig: {
    flaskApiUrl: process.env.FLASK_API_URL || 'http://localhost:5001',
    ssoClientId: process.env.NUXT_SSO_CLIENT_ID || '',
    ssoClientSecret: process.env.NUXT_SSO_CLIENT_SECRET || '',
    ssoAuthorizeUrl: process.env.NUXT_SSO_AUTHORIZE_URL || '',
    ssoTokenUrl: process.env.NUXT_SSO_TOKEN_URL || '',
    ssoUserinfoUrl: process.env.NUXT_SSO_USERINFO_URL || '',
    ssoRedirectUrl: process.env.NUXT_SSO_REDIRECT_URL || '',
    tokenExchangeUrl: process.env.NUXT_TOKEN_EXCHANGE_URL || '',
    ssoCookieName: process.env.NUXT_SSO_COOKIE_NAME || 'sso_token',
    staticAuthToken: process.env.NUXT_STATIC_AUTH_TOKEN || '',
    public: {
      hasStaticAuthToken: !!process.env.NUXT_STATIC_AUTH_TOKEN
    }
  },
```

- [ ] **Step 2: Create `app/plugins/fetch.client.ts`**

This client-only plugin intercepts 401 errors from API calls. When using a static token, it shows an error toast (since SSO login won't help). Otherwise, it clears the session and redirects to SSO.

```typescript
export default defineNuxtPlugin(() => {
  const nuxt = useNuxtApp()

  nuxt.hook('app:error' as any, (error: any) => {
    if (error?.statusCode === 401) {
      handle401()
    }
  })
})

let isRedirecting = false

async function handle401() {
  if (isRedirecting) return
  isRedirecting = true

  const config = useRuntimeConfig()
  const { loggedIn, clear } = useUserSession()

  if (config.public.hasStaticAuthToken) {
    const toast = useToast()
    toast.add({
      title: '认证失败',
      description: 'Static auth token 无效，请检查 NUXT_STATIC_AUTH_TOKEN 配置',
      color: 'error'
    })
    isRedirecting = false
    return
  }

  if (loggedIn.value) {
    await clear()
  }

  window.location.href = '/auth/sso'
}
```

- [ ] **Step 3: Delete unused `app/composables/useAuthFetch.ts`**

```bash
git rm app/composables/useAuthFetch.ts
```

- [ ] **Step 4: Commit**

```bash
git add app/plugins/fetch.client.ts nuxt.config.ts
git commit -m "feat: add global 401 interception plugin with static token awareness"
```

Then separately:

```bash
git rm app/composables/useAuthFetch.ts
git commit -m "chore: remove unused useAuthFetch composable, replaced by global plugin"
```

---

### Task 9: Add Error Toast Display to Home Page

**Files:**
- Modify: `app/pages/home.vue`

- [ ] **Step 1: Add error toast logic to home page**

Add a `<script setup>` block at the top of `app/pages/home.vue` to show a toast when redirected from SSO with an error:

```vue
<script setup lang="ts">
definePageMeta({
  layout: 'default'
})

const route = useRoute()
const toast = useToast()

const errorMessages: Record<string, string> = {
  token_exchange_failed: '令牌交换失败，请重试',
  user_creation_failed: '用户创建失败，请重试',
  callback_error: '登录过程中出现错误，请重试',
  access_denied: '您拒绝了授权请求'
}

onMounted(() => {
  const error = route.query.error as string
  if (error) {
    toast.add({
      title: '登录失败',
      description: errorMessages[error] || '登录失败，请重试',
      color: 'error'
    })
    // Clean the URL
    navigateTo('/home', { replace: true })
  }
})
</script>
```

Note: This replaces the existing `<script setup>` block (which only contained `definePageMeta`). The `definePageMeta` call is kept.

- [ ] **Step 2: Commit**

```bash
git add app/pages/home.vue
git commit -m "feat: show SSO error toast on home page when redirected with error param"
```

---

### Task 10: Final Verification

- [ ] **Step 1: Verify dev server starts without errors**

```bash
npm run dev
```

Expected: Server starts, no compilation errors.

- [ ] **Step 2: Verify static token mode**

1. Set `NUXT_STATIC_AUTH_TOKEN=valid-token` in `.env`
2. Start Flask mock server
3. Navigate to `/chat` — should load chat list without SSO login
4. Verify API requests include `X-Auth-Token: valid-token` header (check Flask console logs)

- [ ] **Step 3: Verify SSO mode (no static token)**

1. Remove `NUXT_STATIC_AUTH_TOKEN` value from `.env`
2. Navigate to `/chat` — should redirect to SSO login
3. After SSO login, should land on `/chat`
4. User icon in navbar — click to see compact dropdown with theme toggle and logout
5. Click logout — should redirect to `/home`

- [ ] **Step 4: Verify 401 interception**

1. Without static token, log in via SSO
2. Manually clear session (or let token expire)
3. Make an API call — should redirect to SSO login

- [ ] **Step 5: Verify error toast**

1. Cancel SSO login (access_denied)
2. Should redirect to `/home?error=access_denied`
3. Should see error toast on home page

- [ ] **Step 6: Final commit if any fixes needed**

```bash
git add -A
git commit -m "fix: address verification issues for auth improvements"
```
