<script setup lang="ts">
import AuthLoginModalHost from '~/components/auth/LoginModalHost.vue'

const colorMode = useColorMode()
const route = useRoute()

const color = computed(() => colorMode.value === 'dark' ? '#1b1718' : 'white')

useHead({
  meta: [
    { charset: 'utf-8' },
    { name: 'viewport', content: 'width=device-width, initial-scale=1' },
    { key: 'theme-color', name: 'theme-color', content: color }
  ],
  link: [
    { rel: 'icon', href: '/favicon.ico' }
  ],
  htmlAttrs: {
    lang: 'zh'
  }
})

const title = 'BuildMate Managed AI Agent'
const description = 'BuildMate Managed AI Agent is a full-featured, hackable AI agent made with Nuxt UI.'

useSeoMeta({
  title,
  description,
  ogTitle: title,
  ogDescription: description,
})
</script>

<template>
  <UApp :toaster="{ position: 'top-right' }" :tooltip="{ delayDuration: 200 }">
    <NuxtLoadingIndicator color="var(--ui-primary)" />

    <NuxtLayout>
      <NuxtPage />
    </NuxtLayout>

    <AuthLoginModalHost />
  </UApp>
</template>
