<script setup lang="ts">
import type { DropdownMenuItem } from '@nuxt/ui'

const colorMode = useColorMode()
const { clear } = useUserSession()

const items = computed<DropdownMenuItem[][]>(() => ([[{
  label: colorMode.value === 'dark' ? '浅色模式' : '深色模式',
  icon: colorMode.value === 'dark' ? 'i-lucide-sun' : 'i-lucide-moon',
  onSelect() {
    colorMode.preference = colorMode.value === 'dark' ? 'light' : 'dark'
  }
}], [{
  label: '退出登录',
  icon: 'i-lucide-log-out',
  onSelect() {
    clear()
    navigateTo('/home')
  }
}]]))
</script>

<template>
  <UDropdownMenu
    :items="items"
    :content="{ align: 'end', collisionPadding: 12 }"
    :ui="{ content: 'w-40' }"
  >
    <UButton
      icon="i-lucide-user"
      color="neutral"
      variant="ghost"
      size="sm"
      class="data-[state=open]:bg-elevated"
    />
  </UDropdownMenu>
</template>
