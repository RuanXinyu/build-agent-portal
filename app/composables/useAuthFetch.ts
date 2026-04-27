export function useAuthFetch() {
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
