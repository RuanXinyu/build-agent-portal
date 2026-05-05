<script setup lang="ts">
const { loggedIn } = useUserSession()

const open = ref(false)
const CHAT_PAGE_SIZE = 20

interface SidebarChat {
  id: string
  label: string
  to: string
  icon: string
  createdAt: string
}

interface SidebarPagination {
  page: number
  page_size: number
  total: number
  total_pages: number
  has_next: boolean
  has_prev: boolean
}

interface SidebarChatsResponse {
  data: Array<{
    chat_id: string
    title: string | null
    createdAt: string
  }>
  pagination?: SidebarPagination
}

function toSidebarChats(data: Array<{
  chat_id: string
  title: string | null
  createdAt: string
}>) {
  return data.map(chat => ({
    id: chat.chat_id,
    label: chat.title || '未命名会话',
    to: `/chat/${chat.chat_id}`,
    icon: 'i-lucide-message-circle',
    createdAt: chat.createdAt
  }))
}

function normalizeChatsPayload(payload: SidebarChatsResponse | SidebarChat[] | null | undefined) {
  if (!payload) {
    return {
      items: [] as SidebarChat[],
      pagination: null as SidebarPagination | null
    }
  }

  if (Array.isArray(payload)) {
    return {
      items: payload as SidebarChat[],
      pagination: null as SidebarPagination | null
    }
  }

  return {
    items: toSidebarChats(payload.data ?? []),
    pagination: payload.pagination ?? null
  }
}

const currentPage = ref(1)
const chats = ref<SidebarChat[]>([])
const pagination = ref<SidebarPagination | null>(null)
const loadingMore = ref(false)
const listScrollContainer = ref<HTMLElement | null>(null)
const loadMoreSentinel = ref<HTMLElement | null>(null)
let loadMoreObserver: IntersectionObserver | null = null
const { data: cachedChatsData } = useNuxtData<SidebarChatsResponse>('chats')

const { data: chatsRaw, refresh: refreshChats } = await useFetch<SidebarChatsResponse>('/api/v1/agent/chats', {
  key: 'chats',
  immediate: false,
  query: {
    page: 1,
    page_size: CHAT_PAGE_SIZE
  }
})

if (!cachedChatsData.value) {
  await refreshChats()
}

watch(chatsRaw, (value) => {
  const normalized = normalizeChatsPayload(value)
  chats.value = normalized.items
  pagination.value = normalized.pagination
  currentPage.value = normalized.pagination?.page ?? 1
}, { immediate: true })

const hasMoreChats = computed(() => {
  if (pagination.value) {
    return pagination.value.has_next
  }
  return false
})

async function loadMoreChats() {
  if (!hasMoreChats.value || loadingMore.value) return

  loadingMore.value = true
  try {
    const nextPage = currentPage.value + 1
    const res = await $fetch<SidebarChatsResponse>('/api/v1/agent/chats', {
      query: {
        page: nextPage,
        page_size: CHAT_PAGE_SIZE
      }
    })

    const normalized = normalizeChatsPayload(res)
    const existingIds = new Set(chats.value.map(chat => chat.id))
    const newItems = normalized.items.filter(chat => !existingIds.has(chat.id))
    chats.value = [...chats.value, ...newItems]
    pagination.value = normalized.pagination
    currentPage.value = normalized.pagination?.page ?? nextPage
  } finally {
    loadingMore.value = false
  }
}

function stopLoadMoreObserver() {
  if (loadMoreObserver) {
    loadMoreObserver.disconnect()
    loadMoreObserver = null
  }
}

function startLoadMoreObserver() {
  if (!import.meta.client) return
  stopLoadMoreObserver()

  if (!hasMoreChats.value || !listScrollContainer.value || !loadMoreSentinel.value) return

  loadMoreObserver = new IntersectionObserver((entries) => {
    const shouldLoad = entries.some(entry => entry.isIntersecting)
    if (shouldLoad) {
      loadMoreChats()
    }
  }, {
    root: listScrollContainer.value,
    rootMargin: '120px 0px',
    threshold: 0.01
  })

  loadMoreObserver.observe(loadMoreSentinel.value)
}

watch([hasMoreChats, loadMoreSentinel, listScrollContainer], async () => {
  if (!hasMoreChats.value) {
    stopLoadMoreObserver()
    return
  }
  await nextTick()
  startLoadMoreObserver()
}, { flush: 'post' })

onBeforeUnmount(() => {
  stopLoadMoreObserver()
})

watch(loggedIn, (isLoggedIn) => {
  if (!isLoggedIn) {
    clearNuxtData('chats')
    navigateTo('/auth/sso', { external: true })
  } else {
    refreshChats()
  }
  open.value = false
})

const { groups } = useChats(computed(() => chats.value))

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

defineShortcuts({
  c: () => {
    navigateTo('/chat')
  }
})
</script>

<template>
  <div class="flex flex-col h-screen">
    <AppHeader>
      <template #right>
        <UButton
          color="neutral"
          variant="ghost"
          icon="i-lucide-plus"
          to="/chat"
          class="lg:hidden"
          aria-label="新建会话"
        />
      </template>
    </AppHeader>

    <UMain>
      <UDashboardGroup unit="rem" class="flex-1 relative" style="height: calc(100vh - var(--ui-header-height))">
        <UDashboardSidebar
          id="default"
          v-model:open="open"
          :min-size="12"
          collapsible
          resizable
          class="border-r-0 py-4 overflow-hidden"
        >
          <template #default="{ collapsed }">
            <div class="flex h-full min-h-0 flex-col gap-1.5">
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

              <div
                v-else
                ref="listScrollContainer"
                class="flex-1 min-h-0 overflow-y-auto pr-1"
              >
                <UNavigationMenu
                  :items="items"
                  :collapsed="collapsed"
                  orientation="vertical"
                  :ui="{ link: 'overflow-hidden' }"
                />

                <div
                  v-if="hasMoreChats"
                  ref="loadMoreSentinel"
                  class="mt-2 h-10 flex items-center justify-center text-xs text-muted"
                >
                  <UIcon
                    v-if="loadingMore"
                    name="i-lucide-loader-circle"
                    class="mr-1 animate-spin"
                  />
                  <span>{{ loadingMore ? '加载中...' : '继续下拉自动加载' }}</span>
                </div>
              </div>
            </div>
          </template>
        </UDashboardSidebar>

        <div class="flex-1 flex m-4 lg:ml-0 rounded-lg ring ring-default bg-default/75 shadow min-w-0 overflow-hidden">
          <slot />
        </div>
      </UDashboardGroup>
    </UMain>
  </div>
</template>
