<script setup lang="ts">
const route = useRoute()
const errorMessage = computed(() => {
  const error = route.query.error as string
  if (!error) return ''
  const messages: Record<string, string> = {
    token_exchange_failed: '令牌交换失败，请重试',
    user_creation_failed: '用户创建失败，请重试',
    callback_error: '登录过程中出现错误，请重试',
    access_denied: '您拒绝了授权请求'
  }
  return messages[error] || '登录失败，请重试'
})
</script>

<template>
  <div class="flex items-center justify-center min-h-screen">
    <div class="text-center space-y-6">
      <h1 class="text-2xl font-bold">登录</h1>
      <p v-if="errorMessage" class="text-red-500">
        {{ errorMessage }}
      </p>
      <UButton
        label="SSO 登录"
        icon="i-lucide-log-in"
        size="lg"
        @click="navigateTo('/auth/sso')"
      />
    </div>
  </div>
</template>
