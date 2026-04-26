<script setup lang="ts">
</script>

<template>
  <div class="landing-layout">
  <AppHeader sticky />

  <UMain>
    <NuxtPage />
  </UMain>

  <UFooter>
    <template #left>
      <p class="text-muted text-sm">Copyright &copy; {{ new Date().getFullYear() }} BuildMate</p>
    </template>
  </UFooter>
  </div>
</template>

<style scoped>
.landing-layout {
  --ui-container: 96rem;
}
</style>
