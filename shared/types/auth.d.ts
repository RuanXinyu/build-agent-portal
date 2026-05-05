// auth.d.ts
declare module '#auth-utils' {
  interface User {
    id: string
    name: string
    email: string
    avatar: string
    username: string
    uuid?: string
    globalUserID?: string
    tenantId?: string
    provider: 'sso'
    providerId: string
  }

  interface SecureSessionData {
    xAuthToken: string
  }
}

export {}
