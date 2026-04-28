# Auth & Navigation Improvements Design

## Overview

Five improvements to the authentication flow and navigation UI:
1. Static auth token support via `.env` for local development
2. Simplified navbar user menu (icon + compact dropdown)
3. Remove standalone login page (redirect directly to SSO)
4. Global 401 interception with automatic SSO redirect
5. Chat list API requires authentication (enforced via 401 + global interception)

## Part 1: Static Auth Token

### Files Changed
- `nuxt.config.ts` — add `staticAuthToken` to `runtimeConfig`
- `.env` / `.env.example` — add `NUXT_STATIC_AUTH_TOKEN`
- `server/utils/internalService.ts` — prioritize static token
- `server/middleware/auth.ts` — skip auth when static token present

### Logic

In `useInternalService()`:
```
if config.staticAuthToken:
  use staticAuthToken as X-Auth-Token header directly
else:
  existing flow (session → SSO cookie refresh → retry)
```

In `server/middleware/auth.ts`:
- If `staticAuthToken` is set, no-op (pass through). The `useInternalService` will use it.

### Behavior
- When `NUXT_STATIC_AUTH_TOKEN` is unset or empty: all behavior unchanged.
- When set: all API proxy requests use this token, bypassing SSO entirely.
- No token is exposed to the client.

## Part 2: Simplified Navbar User Menu

### Files Changed
- `app/components/AppHeader.vue` — show fixed user icon instead of avatar/name when logged in
- `app/components/UserMenu.vue` — compact dropdown

### AppHeader Changes
- Logged in: show a `<UButton>` with icon `i-lucide-user` (circular), no text
- Logged out: "Login" text button, click triggers `window.location.href = '/auth/sso'`

### UserMenu Changes
- **Remove**: user avatar/name display section, 17-color primary picker, 5-color neutral picker
- **Keep**: theme toggle (light/dark via `UColorModeButton`), logout button
- **Adjust**: dropdown width to be compact (fit-content, minimal padding)
- **Trigger**: `<UButton icon="i-lucide-user" variant="ghost" size="sm" />`

### Dropdown Items
```
[Light/Dark Toggle]
[Logout]
```

## Part 3: Remove Login Page

### Files Changed
- Delete `app/pages/login.vue`
- `app/components/AppHeader.vue` — login button navigates directly to `/auth/sso`
- `server/routes/auth/sso.get.ts` — success redirect to `/chat` instead of `/`

### Behavior
- All login flows go directly to `window.location.href = '/auth/sso'`
- SSO callback redirects to `/chat` on success
- Error handling: SSO errors redirect to `/home?error=<code>` and show a toast on the home page (since `/chat` requires auth and would trigger another 401 loop)

## Part 4: Global 401 Interception

### Files Changed
- Replace `app/composables/useAuthFetch.ts` with `app/plugins/fetch.ts`
- `app/layouts/chat.vue` — remove direct `useFetch` for chats, use intercepted fetch

### Implementation

Create `app/plugins/fetch.ts`:
- Register a Nuxt plugin that provides a custom `$fetch` wrapper
- Use `onResponse` interceptor to detect 401 status codes
- On 401:
  1. If user was logged in (`useUserSession().loggedIn`), call `clear()` to clear session
  2. Redirect to `/auth/sso` via `window.location.href`
- Special case: if `NUXT_STATIC_AUTH_TOKEN` is set and backend returns 401, show error toast instead of redirecting to SSO (static token failures are not recoverable via SSO login)

### Scope
- Intercepts all `$fetch('/api/*')` calls
- Does not intercept external URLs

## Part 5: Chat List Requires Auth

This is automatically enforced by the combination of:
- Flask backend requires `X-Auth-Token` for chat endpoints → returns 401 without it
- Nuxt `useInternalService` forwards the token
- No valid token → backend 401 → global 401 interceptor → SSO redirect

No additional code changes needed beyond Parts 1 and 4.

## Edge Cases

| Scenario | Behavior |
|----------|----------|
| Static token set, token valid | All requests succeed normally |
| Static token set, token invalid (401) | Show error toast, no SSO redirect |
| No static token, no session | SSO redirect on 401 |
| No static token, expired session | Attempt SSO cookie refresh → if fails → 401 → SSO redirect |
| SSO login cancelled | User lands on `/home?error=access_denied`, sees toast |
| User clicks logout | Clear session, navigate to `/home` |
