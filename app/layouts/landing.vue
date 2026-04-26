<script setup lang="ts">
import type { NavigationMenuItem } from '@nuxt/ui'

const items = computed<NavigationMenuItem[]>(() => [
  { label: '首页', to: '/home', icon: 'i-lucide-home' },
  { label: '命令行', to: '/cli', icon: 'i-lucide-terminal' },
  { label: '会话', to: '/chat', icon: 'i-lucide-messages-square' }
])
</script>

<template>
  <UHeader to="/home" :ui="{ container: 'max-w-none flex items-center justify-between gap-3 h-full px-4 sm:px-6 lg:px-8' }">
    <template #title>
      <Logo class="h-6 w-auto" />
      <span class="text-lg font-bold text-highlighted">BuildAgent</span>
    </template>

    <UNavigationMenu :items="items" />

    <template #right>
      <UColorModeButton />
    </template>

    <template #body>
      <UNavigationMenu :items="items" orientation="vertical" class="-mx-2.5" />
    </template>
  </UHeader>

  <UMain>
    <NuxtPage />
  </UMain>

  <UFooter>
    <template #left>
      <p class="text-muted text-sm">Copyright &copy; {{ new Date().getFullYear() }} BuildMate</p>
    </template>
  </UFooter>
</template>
