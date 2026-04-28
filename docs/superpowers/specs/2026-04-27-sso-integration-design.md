# SSO Integration Design

## Background

Current project uses `nuxt-auth-utils` with GitHub OAuth for user authentication. Sessions are managed via encrypted cookies (no server-side session store). The local SQLite database contains a `users` table (chats/messages/votes tables have been removed).

We need to replace GitHub OAuth with an internal SSO system and integrate with internal service APIs for data retrieval.

## Architecture Overview

```
Browser                        Nuxt Server                     Internal Service
  |                              |                              |
  |-- SSO OAuth Login ------------------------------------------>| (SSO)
  |<-- Cookie set on .company.com ------------------------------| (SSO)
  |                              |                              |
  |  (subsequent requests carry Cookie automatically)           |
  |                              |                              |
  |-- Call Nuxt API ----------->|                              |
  |  (request carries SSO Cookie)|-- Read SSO Cookie from req   |
  |                              |-- Cookie -> token exchange -->|
  |                              |<-- x-auth-token -------------|
  |                              |-- Store in session           |
  |<-- Return success ----------|                              |
  |                              |                              |
  |-- Call Nuxt API ----------->|                              |
  |                              |-- Get x-auth-token from session
  |                              |-- Proxy request with token -->|
  |                              |<-- Data ----------------------|
  |<-- Return data -------------|                              |
```

Key constraint: x-auth-token is never exposed to the frontend. All token management happens server-side.

## Authentication Flow

### Login Flow

1. User clicks login -> redirect to SSO authorization page (OAuth 2.0 Authorization Code flow)
2. User completes login at SSO -> SSO sets Cookie on `.company.com` -> callback to Nuxt
3. Nuxt server callback handler:
   - Reads SSO Cookie from the incoming request
   - Exchanges authorization code for access token (standard OAuth)
   - Uses SSO Cookie to call token exchange endpoint -> obtains x-auth-token
   - Uses access token to call UserInfo endpoint -> obtains user info
4. Stores `x-auth-token` and `user` in nuxt-auth-utils session
5. Upserts user record in local `users` table
6. Redirects to home page

### Logout Flow

- Unchanged from current implementation: `clear()` from `useUserSession()` clears the session

### Token Lifecycle

- **x-auth-token validity**: ~3 days
- **Refresh mechanism**: server-side automatic refresh
- **Refresh trigger**: when internal service API returns 401

## Session & Token Management

### Storage

- `x-auth-token` stored in nuxt-auth-utils session (encrypted cookie, frontend cannot read)
- User basic info (id, name, email, avatar) stored alongside in session

### Token Refresh (Server Middleware)

Server middleware intercepts all authenticated API requests:

```
Request arrives -> Read x-auth-token from session
  -> Token valid -> Forward to API route
  -> Token expired (internal service returns 401)
     -> Read SSO Cookie from incoming request
     -> Re-exchange for new x-auth-token
     -> Update session
     -> Retry original request
  -> SSO Cookie also expired (exchange returns 401)
     -> Return 401 to frontend
     -> Frontend redirects to SSO login
```

## API Proxy Layer

### Internal Service Request Utility

Create a shared utility function (e.g., `useInternalService(event, path, options)`):

- Reads x-auth-token from session
- Assembles request header `X-Auth-Token`
- Calls internal service endpoint via `$fetch`
- Returns response to caller
- All server API routes use this utility

### Server API Routes

Transform existing `server/api/v1/` routes from mock data to proxy mode:

- Each route calls internal service via the shared utility
- Passes through responses from internal service
- Errors are handled by the middleware layer

## Code Changes

### Files to Modify

| File | Change |
|------|--------|
| `shared/types/auth.d.ts` | Change `provider` type from `'github'` to `'sso'` |
| `server/routes/auth/github.get.ts` | Replace with `server/routes/auth/sso.get.ts`: custom OAuth 2.0 + token exchange + UserInfo |
| `server/db/schema.ts` | Update `provider` enum to include `'sso'` |
| `server/middleware/auth.ts` | New: auth + token refresh middleware |
| `server/utils/internalService.ts` | New: internal service request utility |
| `server/api/v1/*` | Transform from mock data to proxy mode using internal service |
| `app/components/AppHeader.vue` | Change login redirect from `/auth/github` to `/auth/sso` |
| `nuxt.config.ts` | Add SSO environment variable config (clientId, clientSecret, tokenEndpoint, etc.) |
| `.env` / `.env.example` | Add SSO configuration items |
| `package.json` | May need `ofetch` or use built-in `$fetch` |

### Files Unchanged

These files use `useUserSession()` composable (user, loggedIn, clear) and require no changes:

- `app/components/UserMenu.vue`
- `app/layouts/chat.vue`
- `app/pages/chat/index.vue`
- `app/components/drag-drop/Overlay.vue`

## Environment Variables

New environment variables needed:

```
NUXT_SSO_CLIENT_ID=          # SSO OAuth client ID
NUXT_SSO_CLIENT_SECRET=      # SSO OAuth client secret
NUXT_SSO_AUTHORIZE_URL=      # SSO authorization endpoint
NUXT_SSO_TOKEN_URL=          # SSO token exchange endpoint
NUXT_SSO_USERINFO_URL=       # SSO UserInfo endpoint
NUXT_SSO_REDIRECT_URL=       # OAuth callback URL
NUXT_TOKEN_EXCHANGE_URL=     # SSO Cookie -> x-auth-token exchange endpoint
NUXT_INTERNAL_SERVICE_BASE=  # Internal service base URL
```

## Key Design Decisions

1. **Keep nuxt-auth-utils** for session management - preserves existing `useUserSession` API, minimal frontend changes
2. **Server-side token management** - x-auth-token never exposed to frontend, all exchange/refresh handled by server
3. **Shared parent domain Cookie** - SSO Cookie on `.company.com` allows Nuxt server to read it from requests
4. **Middleware-based token refresh** - transparent to API routes, automatic retry on token expiry
5. **Proxy pattern for API routes** - frontend only talks to Nuxt server, internal services are abstracted away
