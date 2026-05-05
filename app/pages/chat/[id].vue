<script setup lang="ts">
import { Chat } from '@ai-sdk/vue'
import { parseJsonEventStream, uiMessageChunkSchema } from 'ai'
import type { ChatTransport, UIMessage, UIMessageChunk, ChatRequestOptions } from 'ai'

definePageMeta({
  layout: 'chat'
})

const route = useRoute()
const toast = useToast()
const { csrf, headerName } = useCsrf()

function getMessageText(message?: UIMessage) {
  if (!message) return ''

  return message.parts
    ?.filter((p: any) => p.type === 'text')
    ?.map((p: any) => p.text)
    ?.join('')
    ?.trim() || ''
}

interface ChatData {
  id: string
  title: string | null
  createdAt: string
  messages: UIMessage[]
  lastTimestamp: number
  isOwner: boolean
}

const { data } = await useFetch<ChatData>(`/api/v1/agent/chats/${route.params.id}`)

const isOwner = computed(() => data.value?.isOwner ?? false)

const input = ref('')
type TimestampUnit = 'seconds' | 'milliseconds'

function detectTimestampUnit(value: number): TimestampUnit {
  return value > 0 && value < 1e12 ? 'seconds' : 'milliseconds'
}

function nowByUnit(unit: TimestampUnit): number {
  return unit === 'seconds'
    ? Math.floor(Date.now() / 1000)
    : Date.now()
}

const initialLastTimestamp = Number(data.value?.lastTimestamp ?? 0)
const timestampUnit = ref<TimestampUnit>(detectTimestampUnit(initialLastTimestamp))
const lastTimestamp = ref(initialLastTimestamp)
const panelOpen = ref(false)
const maximizedFile = ref<string | null>(null)

// Clear maximized state when panel closes
watch(panelOpen, (open) => {
  if (!open) {
    maximizedFile.value = null
  }
})

function onFileMaximize(path: string) {
  maximizedFile.value = path
}

function onFileSelected(path: string) {
  if (maximizedFile.value !== null) {
    maximizedFile.value = path
  }
}

function onMinimizePreview() {
  maximizedFile.value = null
}

function onPreviewKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape' && maximizedFile.value) {
    maximizedFile.value = null
  }
}

// Auto-focus overlay for Escape key
const previewOverlay = ref<HTMLElement | null>(null)
watch(maximizedFile, (path) => {
  if (path) {
    nextTick(() => previewOverlay.value?.focus())
  }
})

const customTransport: ChatTransport<UIMessage> = {
  async sendMessages({
    chatId,
    messageId,
    trigger,
    messages,
    abortSignal
  }: {
    trigger: 'submit-message' | 'regenerate-message'
    chatId: string
    messageId: string | undefined
    messages: UIMessage[]
    abortSignal: AbortSignal | undefined
  } & ChatRequestOptions): Promise<ReadableStream<UIMessageChunk>> {
    // Only send the newly added user prompt, not full history.
    const currentMessage = messageId
      ? messages.find(message => message.id === messageId)
      : undefined
    const latestUserMessage = [...messages].reverse().find(message => message.role === 'user')
    const prompt = getMessageText(
      trigger === 'submit-message' ? (currentMessage ?? latestUserMessage) : latestUserMessage
    )
    if (!prompt) {
      throw new Error('消息内容不能为空')
    }

    // 1. POST to trigger chat
    const body: { prompt: string; chat_id?: string } = { prompt }
    if (chatId) {
      body.chat_id = chatId
    }

    const result = await $fetch<{ chat_id?: string, chatId?: string, id?: string, message_id?: string }>('/api/v1/agent/chats', {
      method: 'POST',
      headers: { [headerName]: csrf },
      body
    })
    const resolvedChatId = result.chat_id ?? result.chatId ?? result.id
    if (!resolvedChatId) {
      throw new Error('发送失败：接口未返回有效 chat_id')
    }

    if (String(route.params.id) !== String(resolvedChatId)) {
      await navigateTo(`/chat/${resolvedChatId}`)
    }

    // 2. Fetch SSE stream with lastTimestamp for incremental queries
    const url = `/api/v1/agent/chats/${resolvedChatId}?stream=true&after_ts=${lastTimestamp.value}`
    const response = await fetch(url, { signal: abortSignal })

    if (!response.body) throw new Error('No response body')

    // 3. Parse SSE response and return as ReadableStream<UIMessageChunk>
    return parseJsonEventStream({
      stream: response.body,
      schema: uiMessageChunkSchema
    }).pipeThrough(
      new TransformStream({
        transform(chunk, controller) {
          if (!chunk.success) throw chunk.error
          controller.enqueue(chunk.value)
        }
      })
    )
  },

  async reconnectToStream(): Promise<ReadableStream<UIMessageChunk> | null> {
    return null
  }
}

const chat = new Chat({
  id: data.value?.id,
  messages: data.value?.messages,
  transport: customTransport,
  onError(error) {
    const { message } = typeof error.message === 'string' && error.message[0] === '{' ? JSON.parse(error.message) : error
    toast.add({
      description: message,
      icon: 'i-lucide-alert-circle',
      color: 'error',
      duration: 0
    })
  }
})

const visibleMessages = computed(() =>
  chat.messages.filter(message => getMessageText(message))
)

// Update lastTimestamp when streaming completes
watch(
  () => chat.status,
  (status) => {
    if (status === 'ready') {
      lastTimestamp.value = nowByUnit(timestampUnit.value)
    }
  }
)

async function handleSubmit(e: Event) {
  e.preventDefault()
  if (input.value.trim()) {
    chat.sendMessage({
      text: input.value
    })
    input.value = ''
  }
}
</script>

<template>
  <UDashboardPanel
    id="chat"
    class="relative min-h-0"
    :ui="{ body: 'flex flex-col flex-1 p-0 sm:p-0 overscroll-none' }"
  >
    <template #body>
      <div class="flex h-full">
        <!-- Floating folder toggle button -->
        <UButton
          :icon="panelOpen ? 'i-lucide-folder-open' : 'i-lucide-folder'"
          :color="panelOpen ? 'primary' : 'neutral'"
          :variant="panelOpen ? 'soft' : 'ghost'"
          size="sm"
          aria-label="浏览文件"
          :aria-pressed="panelOpen"
          class="absolute top-2 right-5 z-200"
          @click="panelOpen = !panelOpen"
        />
        <UContainer class="flex-1 flex flex-col gap-4 sm:gap-6 min-w-0 min-h-0 relative max-w-7xl">
          <UChatMessages
            should-auto-scroll
            :user="{
              side: 'right',
              variant: 'solid',
              avatar: {
                icon: 'i-lucide-user'
              },
            }"
            :assistant="{
              side: 'left',
              variant: 'soft',
              avatar: {
                icon: 'i-lucide-bot'
              },
            }"
            :messages="visibleMessages"
            :status="chat.status"
            :spacing-offset="isOwner ? 160 : 0"
            class="pt-3 pb-4 sm:pb-6"
          >
            <template #indicator>
              <div class="flex items-center gap-1.5">
                <ChatIndicator />

                <UChatShimmer text="Thinking..." class="text-sm" />
              </div>
            </template>

            <template #content="{ message }">
              <ChatMessageContent
                :message="message"
              />
            </template>

            <template v-if="isOwner" #actions="{ message }">
              <ChatMessageActions
                :message="message"
                :streaming="chat.status === 'streaming' && message.id === visibleMessages[visibleMessages.length - 1]?.id"
              />
            </template>
          </UChatMessages>

          <UChatPrompt
            v-if="isOwner"
            v-model="input"
            :error="chat.error"
            variant="subtle"
            class="sticky bottom-0 [view-transition-name:chat-prompt] rounded-b-none z-10"
            :ui="{ base: 'px-1.5' }"
            @submit="handleSubmit"
          >
            <template #footer>
              <div class="flex items-center gap-1" />

              <UChatPromptSubmit
                :status="chat.status"
                color="neutral"
                size="sm"
              />
            </template>
          </UChatPrompt>

          <!-- Maximized file preview overlay -->
          <Transition name="fade">
            <div
              v-if="maximizedFile"
              ref="previewOverlay"
              tabindex="-1"
              class="absolute inset-0 z-20 bg-default flex flex-col outline-none"
              @keydown="onPreviewKeydown"
            >
              <!-- File preview -->
              <div class="flex-1 min-h-0">
                <FilePreview
                  :chat-id="String(route.params.id)"
                  :file-path="maximizedFile"
                  :embedded="false"
                  @maximize="onMinimizePreview"
                />
              </div>
            </div>
          </Transition>
        </UContainer>

        <FileBrowserPanel
          title="Agent产物"
          :chat-id="String(route.params.id)"
          v-model:open="panelOpen"
          :maximized-file="maximizedFile"
          @maximize="onFileMaximize"
          @select-file="onFileSelected"
        />
      </div>
    </template>
  </UDashboardPanel>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.15s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
