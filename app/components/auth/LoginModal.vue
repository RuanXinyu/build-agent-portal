<script setup lang="ts">
defineProps<{
  open: boolean
  source?: string | null
}>()

const emit = defineEmits<{
  confirm: []
  close: []
}>()
</script>

<template>
  <div
    v-if="open"
    class="fixed inset-0 z-[1000] flex items-center justify-center bg-black/50 px-4"
    data-testid="login-modal"
  >
    <div class="w-full max-w-md rounded-lg bg-white p-6 shadow-xl dark:bg-neutral-900">
      <h2 class="text-lg font-semibold text-neutral-900 dark:text-neutral-100">
        需要登录后继续
      </h2>
      <p class="mt-2 text-sm text-neutral-600 dark:text-neutral-300">
        请先完成登录，再继续当前操作。
      </p>
      <p
        v-if="source"
        class="mt-1 text-xs text-neutral-500 dark:text-neutral-400"
      >
        来源：{{ source }}
      </p>

      <div class="mt-6 flex justify-end gap-3">
        <button
          type="button"
          class="rounded-md border border-neutral-300 px-4 py-2 text-sm text-neutral-700 hover:bg-neutral-100 dark:border-neutral-700 dark:text-neutral-200 dark:hover:bg-neutral-800"
          data-testid="login-modal-close"
          @click="emit('close')"
        >
          稍后再说
        </button>
        <button
          type="button"
          class="rounded-md bg-primary-500 px-4 py-2 text-sm font-medium text-white hover:bg-primary-600"
          data-testid="login-modal-confirm"
          @click="emit('confirm')"
        >
          使用W3登录
        </button>
      </div>
    </div>
  </div>
</template>
