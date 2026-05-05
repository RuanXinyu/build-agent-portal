<script setup lang="ts">
definePageMeta({
  layout: 'chat'
})

const input = ref('')
const loading = ref(false)
const { user } = useUserSession()

const greeting = computed(() => {
  const hour = new Date().getHours()
  let timeGreeting = '晚上好'
  if (hour < 12) timeGreeting = '早上好'
  else if (hour < 18) timeGreeting = '下午好'

  const name = user.value?.name?.split(' ')[0] || user.value?.username

  return name ? `${timeGreeting}, ${name}` : `${timeGreeting}`
})

const { csrf, headerName } = useCsrf()

async function createQuickChat(prompt: string) {
  input.value = prompt
}

async function createChat(prompt: string) {
  const trimmedPrompt = prompt.trim()
  if (!trimmedPrompt) return

  input.value = trimmedPrompt
  loading.value = true

  try {
    const result = await $fetch<{ chat_id?: string; chatId?: string; id?: string }>('/api/v1/agent/chats', {
      method: 'POST',
      headers: { [headerName]: csrf },
      body: {
        prompt: trimmedPrompt,
      }
    })

    const chatId = result.chat_id ?? result.chatId ?? result.id
    if (!chatId) {
      throw new Error('创建会话失败：未返回有效 chat_id')
    }

    refreshNuxtData('chats')
    await navigateTo(`/chat/${chatId}`)
  } catch (error: any) {
    loading.value = false
    if (error?.statusCode !== 401) {
      const toast = useToast()
      toast.add({
        description: error?.data?.message || error?.message || '创建会话失败',
        icon: 'i-lucide-alert-circle',
        color: 'error'
      })
    }
  }
}

async function onSubmit() {
  await createChat(input.value)
}

const quickChats = [
  {
    label: '查询构建状态',
    icon: 'i-lucide-check-circle'
  },
  {
    label: '修复构建编译错误',
    icon: 'i-lucide-bug'
  },
  {
    label: '检视代码仓库代码',
    icon: 'i-lucide-code'
  }
]
</script>

<template>
  <UDashboardPanel
    id="home"
    class="min-h-0"
    :ui="{ body: 'p-0 sm:p-0' }"
  >
    <template #body>
      <UContainer class="flex-1 flex flex-col justify-center gap-4 sm:gap-6 py-8">
        <h1 class="text-3xl sm:text-4xl text-highlighted font-bold">
          {{ greeting }}
        </h1>

        <UChatPrompt
          v-model="input"
          :status="loading ? 'streaming' : 'ready'"
          class="[view-transition-name:chat-prompt]"
          variant="subtle"
          :ui="{ base: 'px-1.5' }"
          @submit="onSubmit"
        >
          <template #footer>
            <div class="flex items-center gap-1">
            </div>

            <UChatPromptSubmit color="neutral" size="sm" />
          </template>
        </UChatPrompt>

        <div class="flex flex-wrap gap-2">
          <UButton
            v-for="quickChat in quickChats"
            :key="quickChat.label"
            :icon="quickChat.icon"
            :label="quickChat.label"
            size="sm"
            color="neutral"
            variant="outline"
            class="rounded-full"
            @click="createQuickChat(quickChat.label)"
          />
        </div>
      </UContainer>
    </template>
  </UDashboardPanel>
</template>
