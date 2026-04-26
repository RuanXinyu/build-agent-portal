<script setup lang="ts">
import { Chat } from '@ai-sdk/vue'
import { parseJsonEventStream, uiMessageChunkSchema } from 'ai'
import type { ChatTransport, UIMessage, UIMessageChunk, ChatRequestOptions } from 'ai'

const route = useRoute()
const toast = useToast()
const { csrf, headerName } = useCsrf()

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
const lastTimestamp = ref(data.value?.lastTimestamp ?? 0)

const customTransport: ChatTransport<UIMessage> = {
  async sendMessages({
    chatId,
    messages,
    abortSignal,
  }: {
    trigger: 'submit-message' | 'regenerate-message'
    chatId: string
    messageId: string | undefined
    messages: UIMessage[]
    abortSignal: AbortSignal | undefined
  } & ChatRequestOptions): Promise<ReadableStream<UIMessageChunk>> {
    // Extract text from the last message
    const lastMessage = messages[messages.length - 1]
    const text = lastMessage?.parts
      ?.filter((p: any) => p.type === 'text')
      ?.map((p: any) => p.text)
      ?.join('') || ''

    // 1. POST to trigger chat
    const result = await $fetch<{ chat_id: string; message_id: string }>('/api/v1/agent/chats', {
      method: 'POST',
      headers: { [headerName]: csrf },
      body: { chat_id: chatId, prompt: text }
    })

    // 2. Fetch SSE stream with lastTimestamp for incremental queries
    const url = `/api/v1/agent/chats/${result.chat_id}?stream=true&after_ts=${lastTimestamp.value}`
    const response = await fetch(url, { signal: abortSignal })

    if (!response.body) throw new Error('No response body')

    // 3. Parse SSE response and return as ReadableStream<UIMessageChunk>
    return parseJsonEventStream({
      stream: response.body,
      schema: uiMessageChunkSchema,
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

// Update lastTimestamp when streaming completes
watch(
  () => chat.status,
  (status) => {
    if (status === 'ready') {
      lastTimestamp.value = Date.now()
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
    v-if="data?.id"
    id="chat"
    class="relative min-h-0"
    :ui="{ body: 'p-0 sm:p-0 overscroll-none' }"
  >
    <template #body>
      <UContainer class="flex-1 flex flex-col gap-4 sm:gap-6">
        <UChatMessages
          should-auto-scroll
          :messages="chat.messages"
          :status="chat.status"
          :spacing-offset="isOwner ? 160 : 0"
          class="pt-(--ui-header-height) pb-4 sm:pb-6"
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
              :streaming="chat.status === 'streaming' && message.id === chat.messages[chat.messages.length - 1]?.id"
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
            <div class="flex items-center gap-1">
            </div>

            <UChatPromptSubmit
              :status="chat.status"
              color="neutral"
              size="sm"
            />
          </template>
        </UChatPrompt>
      </UContainer>
    </template>
  </UDashboardPanel>

  <UContainer v-else class="flex-1 flex flex-col gap-4 sm:gap-6">
    <UError :error="{ statusMessage: 'Chat not found', statusCode: 404 }" class="min-h-full" />
  </UContainer>
</template>
