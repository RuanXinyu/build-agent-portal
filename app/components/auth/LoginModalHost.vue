<script setup lang="ts">
import LoginModal from './LoginModal.vue'

const { isOpen, source, close } = useLoginModal()

function handleConfirm() {
  close('stay')

  if (import.meta.client) {
    window.location.href = '/auth/sso'
  }
}

async function handleClose() {
  close('go-home')
  await navigateTo('/home')
}
</script>

<template>
  <LoginModal
    :open="isOpen"
    :source="source"
    @confirm="handleConfirm"
    @close="handleClose"
  />
</template>
