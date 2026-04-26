<script setup lang="ts">
import type { NavigationMenuItem } from '@nuxt/ui'

const { loggedIn, openInPopup } = useUserSession()

const open = ref(false)

const { data: chats, refresh: refreshChats } = await useFetch('/api/v1/agent/chats', {
  key: 'chats',
  transform: data => data.map(chat => ({
    id: chat.chat_id,
    label: chat.title || '未命名会话',
    to: `/chat/${chat.chat_id}`,
    icon: 'i-lucide-message-circle',
    createdAt: chat.createdAt
  }))
})

onNuxtReady(async () => {
  const first10 = (chats.value || []).slice(0, 10)
  for (const chat of first10) {
    await $fetch(`/api/v1/agent/chats/${chat.id}`)
  }
})

watch(loggedIn, () => {
  refreshChats()
  open.value = false
})

const { groups } = useChats(chats)

const items = computed(() => groups.value?.flatMap((group) => {
  return [{
    label: group.label,
    type: 'label' as const
  }, ...group.items.map(item => ({
    ...item,
    slot: 'chat' as const,
    icon: undefined,
    class: item.label === '未命名会话' ? 'text-muted' : ''
  }))]
}))

const navItems = computed<NavigationMenuItem[]>(() => [
  { label: '首页', to: '/home', icon: 'i-lucide-home' },
  { label: '命令行', to: '/cli', icon: 'i-lucide-terminal' },
  { label: '会话', to: '/chat', icon: 'i-lucide-messages-square' }
])

defineShortcuts({
  c: () => {
    navigateTo('/chat')
  }
})
</script>

<template>
  <div class="flex flex-col h-screen">
    <UHeader to="/home" :ui="{ root: 'bg-default/75 backdrop-blur border-b border-default h-(--ui-header-height) relative z-50', container: 'max-w-none flex items-center justify-between gap-3 h-full px-4 sm:px-6 lg:px-8' }">
      <template #title>
        <Logo class="h-6 w-auto" />
        <span class="text-lg font-bold text-highlighted">BuildAgent</span>
      </template>

      <UNavigationMenu :items="navItems" />

      <template #right>
        <UColorModeButton />
        <UButton
          color="neutral"
          variant="ghost"
          icon="i-lucide-plus"
          to="/chat"
          class="lg:hidden"
          aria-label="新建会话"
        />
      </template>

      <template #body>
        <UNavigationMenu :items="navItems" orientation="vertical" class="-mx-2.5" />
      </template>
    </UHeader>

    <UDashboardGroup unit="rem" class="flex-1 min-h-0">
      <UDashboardSidebar
        id="default"
        v-model:open="open"
        :min-size="12"
        collapsible
        resizable
        class="border-r-0 py-4"
      >
        <template #header="{ collapsed }">
          <NuxtLink to="/home" class="flex items-end gap-0.5">
            <Logo class="h-8 w-auto shrink-0" />
            <span v-if="!collapsed" class="text-xl font-bold text-highlighted">BuildMateChat</span>
          </NuxtLink>
        </template>

        <template #default="{ collapsed }">
          <div class="flex flex-col gap-1.5">
            <UButton
              v-bind="collapsed ? { icon: 'i-lucide-plus' } : { label: '新会话' }"
              variant="soft"
              block
              to="/chat"
              @click="open = false"
            />

            <template v-if="collapsed">
              <UDashboardSearchButton collapsed />
            </template>
          </div>

          <UNavigationMenu
            v-if="!collapsed"
            :items="items"
            :collapsed="collapsed"
            orientation="vertical"
            :ui="{ link: 'overflow-hidden' }"
          />
        </template>

        <template #footer="{ collapsed }">
          <UserMenu v-if="loggedIn" :collapsed="collapsed" />
          <UButton
            v-else
            :label="collapsed ? '' : '登录'"
            icon="i-simple-icons-github"
            color="neutral"
            variant="ghost"
            class="w-full"
            @click="openInPopup('/auth/github')"
          />
        </template>
      </UDashboardSidebar>

      <div class="flex-1 flex m-4 lg:ml-0 rounded-lg ring ring-default bg-default/75 shadow min-w-0 overflow-hidden">
        <slot />
      </div>
    </UDashboardGroup>
  </div>
</template>
