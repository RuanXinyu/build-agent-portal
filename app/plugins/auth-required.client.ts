import type { LocationQuery } from 'vue-router'

export function handleAuthRequiredQuery(query: LocationQuery) {
  if (query.auth_required !== '1') return false

  useLoginModal().open('route-guard-ssr')
  return true
}

export default defineNuxtPlugin(() => {
  onNuxtReady(() => {
    const route = useRoute()
    const router = useRouter()

    const processAuthRequired = () => {
      if (!handleAuthRequiredQuery(route.query)) return

      const restQuery = Object.fromEntries(
        Object.entries(route.query).filter(([key]) => key !== 'auth_required')
      )

      void router.replace({
        path: route.path,
        query: restQuery,
        hash: route.hash
      })
    }

    watch(() => route.query.auth_required, processAuthRequired, { immediate: true, flush: 'post' })
  })
})
