export function useAuthFetch() {
  async function authFetch<T>(url: string, options?: Record<string, any>): Promise<T> {
    try {
      return await $fetch(url, options) as T
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
