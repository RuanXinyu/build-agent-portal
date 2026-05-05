export type LoginModalCloseStrategy = 'go-home' | 'stay'

export function useLoginModal() {
  const isOpen = useState<boolean>('login-modal:is-open', () => false)
  const source = useState<string | null>('login-modal:source', () => null)

  function open(nextSource: string) {
    source.value = nextSource
    isOpen.value = true
  }

  function close(strategy: LoginModalCloseStrategy = 'stay') {
    // Strategy is consumed by callers; this composable only manages state.
    void strategy
    isOpen.value = false
    source.value = null
  }

  function requestLogin(sourceIntent = 'request-login') {
    open(sourceIntent)
  }

  return {
    isOpen,
    source,
    open,
    close,
    requestLogin
  }
}
