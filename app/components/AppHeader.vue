<script setup lang="ts">
import type { NavigationMenuItem } from '@nuxt/ui'

defineProps<{
  sticky?: boolean
}>()

const { loggedIn, openInPopup } = useUserSession()

const navItems = computed<NavigationMenuItem[]>(() => [
  { label: '首页', to: '/home', icon: 'i-lucide-home' },
  { label: '命令行', to: '/cli', icon: 'i-lucide-terminal' },
  { label: '会话', to: '/chat', icon: 'i-lucide-messages-square' }
])
</script>

<template>
  <UHeader
    to="/home"
    :ui="{
      root: sticky
        ? 'bg-default/75 backdrop-blur border-b border-default h-(--ui-header-height) sticky top-0 z-50'
        : 'bg-default/75 backdrop-blur border-b border-default h-(--ui-header-height) relative z-50',
      container: 'max-w-none flex items-center justify-between gap-3 h-full px-4 sm:px-6 lg:px-8'
    }"
  >
    <template #title>
      <Logo class="h-6 w-auto" />
      <span class="text-lg font-bold text-highlighted">BuildAgent</span>
    </template>

    <UNavigationMenu :items="navItems" />

    <template #right>
      <slot name="right" />
      <UserMenu v-if="loggedIn" />
      <UButton
        v-else
        label="登录"
        icon="i-simple-icons-github"
        color="neutral"
        variant="ghost"
        @click="openInPopup('/auth/github')"
      />
      <UColorModeButton />
    </template>

    <template #body>
      <UNavigationMenu :items="navItems" orientation="vertical" class="-mx-2.5" />
    </template>
  </UHeader>
</template>
