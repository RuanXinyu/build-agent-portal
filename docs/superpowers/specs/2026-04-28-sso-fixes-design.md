# SSO Integration Fix & Mock Server Design

## Background

After the initial SSO integration, several issues were identified:
1. `/auth/sso` returns 404 when clicking login
2. No login page for graceful error handling
3. Missing structured logging for SSO flows
4. `fetchSSOUserInfo` uses wrong API format (should be POST body, not Authorization header)
5. Logout doesn't clear SSO Cookie (auto-re-authenticates)
6. No mock SSO server for local development

Additionally, after reviewing nuxt-auth-utils documentation, the session storage should use the `secure` field for server-only data.

## Changes

### 1. Fix `/auth/sso` 404 — Restore Explicit Imports

The `sso.get.ts` route relies on Nuxt auto-imports for functions from `server/utils/`. If auto-import fails to resolve, the entire route file fails to load, causing a 404.

**Fix:** Add explicit imports back to `server/routes/auth/sso.get.ts`:
- Import `getSSOAuthUrl`, `exchangeCodeForToken`, `fetchSSOUserInfo` from `#imports` (Nuxt auto-import alias)
- Import `exchangeSSOCookieForToken` from `#imports`
- Replace dynamic `await import('hub:db')` with static `import { db, schema } from 'hub:db'`

### 2. Create Login Page

Create `app/pages/login.vue`:
- Displays a "SSO 登录" button that navigates to `/auth/sso`
- Shows error message if redirected back with an error query param
- Update `AppHeader.vue` to use `<AuthState>` component pattern per nuxt-auth-utils docs
- Update frontend 401 redirect target from `/auth/sso` to `/login`

### 3. Fix `fetchSSOUserInfo` API Format

**Current (wrong):** `GET` + `Authorization: Bearer <token>` header
**Correct:** `POST` + body `{ client_id, access_token, scope: 'base.profile' }`

Update `server/utils/sso.ts`:
- Change `fetchSSOUserInfo` from GET with Bearer header to POST with JSON body
- Add `client_id` from runtime config
- Add `scope: 'base.profile'` to request body

### 4. Move `xAuthToken` to Session `secure` Field

Per nuxt-auth-utils docs, server-only data should go in the `secure` field:
- Update `setUserSession` calls to use `secure: { xAuthToken }` instead of top-level `xAuthToken`
- Update all readers of `xAuthToken` (middleware, internalService, sso callback) to read from `session.secure.xAuthToken`
- Update `shared/types/auth.d.ts` to add `SecureSessionData` interface with `xAuthToken`

### 5. Fix Logout — Clear SSO Cookie via Session Hook

Create `server/plugins/session.ts` using nuxt-auth-utils' `sessionHooks.hook('clear', ...)`:
- Delete the SSO Cookie from the parent domain when session is cleared
- This hook fires automatically when `useUserSession().clear()` is called from `UserMenu.vue`
- No changes needed to `UserMenu.vue`

### 6. Add Structured SSO Logging

Add `[SSO]` prefixed logs to all SSO functions:
- `server/utils/sso.ts` — OAuth URL generation, code exchange, UserInfo fetch
- `server/utils/tokenExchange.ts` — Cookie → token exchange, refresh attempts
- `server/utils/internalService.ts` — API proxy calls, token retry
- `server/routes/auth/sso.get.ts` — Login redirect, callback processing
- `server/middleware/auth.ts` — Token validation, refresh

### 7. Mock SSO Server in Flask

Add SSO endpoints to the existing Flask app at `scripts/python/server/app.py` (port 5001):

**Endpoints:**
- `GET /sso/authorize` — Returns a simple HTML form with a "Login" button that submits to the redirect URL with a mock authorization code
- `POST /sso/token` — Accepts authorization code, returns a mock access_token
- `POST /sso/userinfo` — Accepts body `{ client_id, access_token, scope }`, returns mock user info
- `POST /sso/token-exchange` — Accepts SSO Cookie, returns a mock x-auth-token

**Flask app changes:**
- Add `X-Auth-Token` validation middleware to existing API routes (reject invalid tokens)
- Set SSO Cookie on the `.localhost` domain when the authorize endpoint is called
- Mock user data from existing mock data or hardcoded test user

**`.env` configuration for local development:**
```
NUXT_SSO_CLIENT_ID=mock-client-id
NUXT_SSO_CLIENT_SECRET=mock-client-secret
NUXT_SSO_AUTHORIZE_URL=http://localhost:5001/sso/authorize
NUXT_SSO_TOKEN_URL=http://localhost:5001/sso/token
NUXT_SSO_USERINFO_URL=http://localhost:5001/sso/userinfo
NUXT_SSO_REDIRECT_URL=http://localhost:3001/auth/sso
NUXT_TOKEN_EXCHANGE_URL=http://localhost:5001/sso/token-exchange
NUXT_SSO_COOKIE_NAME=sso_token
```

## Key Design Decisions

1. **`secure` field for xAuthToken** — Follows nuxt-auth-utils best practice; ensures the token is never exposed to the client
2. **Session hook for logout** — Decouples logout logic from UI components; `UserMenu.vue` just calls `clear()`
3. **`<AuthState>` component** — Handles SSR/caching edge cases per nuxt-auth-utils docs
4. **Same Flask app for SSO mock** — No extra process to manage; uses existing infrastructure
5. **Explicit imports in route handler** — Prevents 404 from auto-import resolution failures
