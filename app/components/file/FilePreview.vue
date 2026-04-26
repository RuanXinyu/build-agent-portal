<script setup lang="ts">
interface FileContentResponse {
  name: string
  language: string | null
  size: number
  content: string | null
  previewable: boolean
  downloadUrl?: string
}

const props = defineProps<{
  filePath: string | null
  embedded?: boolean
}>()

const emit = defineEmits<{
  maximize: []
}>()

const isMaximized = ref(false)

// Fetch file content reactively
const { data, pending, error, refresh } = await useFetch<FileContentResponse>(
  '/api/v1/files/content',
  {
    query: computed(() => (props.filePath ? { path: props.filePath } : undefined)),
    watch: [() => props.filePath],
    immediate: false
  }
)

// Re-fetch when filePath changes to a non-null value
watch(() => props.filePath, (newPath) => {
  if (newPath) {
    refresh()
  }
})

// Language display name mapping
function getLanguageDisplay(language: string | null): string {
  if (!language) return ''
  const map: Record<string, string> = {
    typescript: 'TypeScript',
    javascript: 'JavaScript',
    python: 'Python',
    java: 'Java',
    c: 'C',
    cpp: 'C++',
    go: 'Go',
    rust: 'Rust',
    ruby: 'Ruby',
    php: 'PHP',
    swift: 'Swift',
    kotlin: 'Kotlin',
    vue: 'Vue',
    html: 'HTML',
    css: 'CSS',
    scss: 'SCSS',
    less: 'Less',
    shell: 'Shell',
    bash: 'Bash',
    markdown: 'Markdown',
    json: 'JSON',
    yaml: 'YAML',
    toml: 'TOML',
    xml: 'XML',
    sql: 'SQL',
    dockerfile: 'Dockerfile',
    graphql: 'GraphQL',
    plain_text: 'Plain Text',
  }
  return map[language.toLowerCase()] || language
}

// File icon based on language
function getFileIcon(language: string | null): string {
  if (!language) return 'i-lucide-file'
  const iconMap: Record<string, string> = {
    javascript: 'i-lucide-file-code-2',
    typescript: 'i-lucide-file-code-2',
    python: 'i-lucide-file-code-2',
    java: 'i-lucide-file-code-2',
    c: 'i-lucide-file-code-2',
    cpp: 'i-lucide-file-code-2',
    go: 'i-lucide-file-code-2',
    rust: 'i-lucide-file-code-2',
    ruby: 'i-lucide-file-code-2',
    php: 'i-lucide-file-code-2',
    swift: 'i-lucide-file-code-2',
    kotlin: 'i-lucide-file-code-2',
    vue: 'i-lucide-file-code-2',
    html: 'i-lucide-file-code-2',
    css: 'i-lucide-file-code-2',
    scss: 'i-lucide-file-code-2',
    less: 'i-lucide-file-code-2',
    shell: 'i-lucide-file-code-2',
    bash: 'i-lucide-file-code-2',
    markdown: 'i-lucide-file-text',
    json: 'i-lucide-braces',
    yaml: 'i-lucide-file-text',
    toml: 'i-lucide-file-text',
    xml: 'i-lucide-file-text',
    sql: 'i-lucide-database',
    dockerfile: 'i-lucide-container',
  }
  return iconMap[language.toLowerCase()] || 'i-lucide-file'
}

// Compute line count from content
const lineCount = computed(() => {
  if (!data.value?.content) return 0
  return data.value.content.split('\n').length
})

// File extension for non-previewable display
const fileExtension = computed(() => {
  if (!data.value?.name) return ''
  const parts = data.value.name.split('.')
  return parts.length > 1 ? `.${parts[parts.length - 1]}` : ''
})

// Whether the file is markdown
const isMarkdown = computed(() => {
  return data.value?.language?.toLowerCase() === 'markdown'
})

// Download URL
const downloadUrl = computed(() => {
  if (!props.filePath) return ''
  return `/api/v1/files/download?path=${encodeURIComponent(props.filePath)}`
})

// Toggle maximize
function toggleMaximize() {
  isMaximized.value = !isMaximized.value
  emit('maximize')
}

// Escape key handler
function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape' && isMaximized.value) {
    isMaximized.value = false
    emit('maximize')
  }
}

onMounted(() => {
  document.addEventListener('keydown', onKeydown)
})

onUnmounted(() => {
  document.removeEventListener('keydown', onKeydown)
})

defineExpose({ isMaximized })
</script>

<template>
  <div class="flex flex-col h-full">
    <!-- No file selected state -->
    <div v-if="!filePath" class="flex flex-col items-center justify-center gap-3 py-16 text-muted">
      <UIcon name="i-lucide-file-search" class="size-10" />
      <span class="text-sm">选择文件以预览</span>
    </div>

    <!-- Loading state -->
    <div v-else-if="pending" class="flex items-center justify-center gap-2 py-16 text-muted">
      <UIcon name="i-lucide-loader-2" class="size-5 animate-spin" />
      <span>加载中...</span>
    </div>

    <!-- Error state -->
    <div v-else-if="error" class="flex flex-col items-center justify-center gap-3 py-16 text-error">
      <UIcon name="i-lucide-alert-circle" class="size-6" />
      <span class="text-sm">加载失败</span>
      <UButton
        size="xs"
        variant="ghost"
        icon="i-lucide-refresh-cw"
        label="重试"
        @click="refresh()"
      />
    </div>

    <!-- File loaded -->
    <template v-else-if="data">
      <!-- Action bar (hidden when embedded) -->
      <div
        v-if="!embedded"
        class="flex items-center gap-2 px-3 py-2 border-b border-default bg-elevated/30 text-sm shrink-0"
      >
        <div class="flex items-center gap-2 flex-1 min-w-0">
          <UIcon :name="getFileIcon(data.language)" class="size-4 shrink-0 text-muted" />
          <span class="truncate text-highlighted font-medium">{{ data.name }}</span>
          <span v-if="data.language" class="text-xs text-muted bg-dimmed px-1.5 py-0.5 rounded">
            {{ getLanguageDisplay(data.language) }}
          </span>
          <span class="text-xs text-muted">{{ lineCount }} 行</span>
        </div>
        <div class="flex items-center gap-1 shrink-0">
          <a
            :href="downloadUrl"
            target="_blank"
            class="inline-flex items-center justify-center size-7 rounded-md text-muted hover:text-highlighted hover:bg-elevated/50 transition-colors"
          >
            <UIcon name="i-lucide-download" class="size-4" />
          </a>
          <button
            v-if="data.previewable"
            class="inline-flex items-center justify-center size-7 rounded-md text-muted hover:text-highlighted hover:bg-elevated/50 transition-colors"
            @click="toggleMaximize"
          >
            <UIcon :name="isMaximized ? 'i-lucide-minimize-2' : 'i-lucide-maximize-2'" class="size-4" />
          </button>
        </div>
      </div>

      <!-- Previewable content -->
      <template v-if="data.previewable">
        <!-- Markdown rendering -->
        <div v-if="isMarkdown" class="flex-1 overflow-y-auto">
          <div class="prose prose-sm dark:prose-invert max-w-none p-4">
            <ChatComark :content="data.content || ''" />
          </div>
        </div>

        <!-- Code / plain text rendering -->
        <div v-else class="flex-1 overflow-auto">
          <table class="w-full text-sm font-mono">
            <tbody>
              <tr
                v-for="(line, index) in (data.content || '').split('\n')"
                :key="index"
                class="hover:bg-elevated/30"
              >
                <td class="text-right text-muted/40 select-none px-3 py-0 border-r border-default align-top whitespace-nowrap">
                  {{ index + 1 }}
                </td>
                <td class="px-3 py-0 text-highlighted whitespace-pre">
                  {{ line }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </template>

      <!-- Non-previewable content -->
      <div v-else class="flex-1 flex flex-col items-center justify-center gap-3 py-16 text-muted">
        <div class="size-16 rounded-full bg-dimmed flex items-center justify-center">
          <UIcon name="i-lucide-file-x" class="size-8" />
        </div>
        <span class="text-sm text-highlighted">无法预览此文件</span>
        <span class="text-xs text-muted">{{ fileExtension }} 文件类型暂不支持在线预览</span>
        <a
          :href="downloadUrl"
          target="_blank"
        >
          <UButton
            size="sm"
            variant="outline"
            icon="i-lucide-download"
            label="下载文件"
          />
        </a>
      </div>
    </template>
  </div>
</template>
