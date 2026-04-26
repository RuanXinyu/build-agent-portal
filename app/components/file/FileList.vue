<script setup lang="ts">
interface FileEntry {
  name: string
  path: string
  type: 'directory' | 'file'
  size?: number
  language?: string | null
}

const props = defineProps<{
  currentPath: string
  selectedFilePath: string | null
}>()

const emit = defineEmits<{
  navigate: [path: string]
  selectFile: [path: string]
}>()

const { data, pending, error, refresh } = useFetch<{ entries: FileEntry[] }>(
  '/api/v1/files',
  {
    query: computed(() => ({ path: props.currentPath })),
    watch: [() => props.currentPath]
  }
)

defineExpose({ refresh })

// Breadcrumb segments computed from currentPath
const breadcrumbs = computed(() => {
  if (!props.currentPath || props.currentPath === '/') {
    return []
  }
  const segments = props.currentPath.split('/').filter(Boolean)
  return segments.map((segment, index) => ({
    label: segment,
    path: '/' + segments.slice(0, index + 1).join('/')
  }))
})

function navigateTo(path: string) {
  emit('navigate', path)
}

function selectFile(entry: FileEntry) {
  emit('selectFile', entry.path)
}

function getFileIcon(entry: FileEntry): string {
  if (entry.type === 'directory') {
    return 'i-lucide-folder'
  }
  const language = entry.language?.toLowerCase() || ''
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
    image: 'i-lucide-image',
  }
  return iconMap[language] || 'i-lucide-file'
}

function formatFileSize(bytes?: number): string {
  if (bytes == null) return ''
  if (bytes === 0) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  const size = bytes / Math.pow(1024, i)
  return `${size.toFixed(i === 0 ? 0 : 1)} ${units[i]}`
}

function isFileSelected(entry: FileEntry): boolean {
  return entry.type === 'file' && entry.path === props.selectedFilePath
}
</script>

<template>
  <div class="flex flex-col h-full">
    <!-- Breadcrumb bar -->
    <div class="flex items-center gap-1 px-3 py-2 border-b border-default bg-elevated/30 text-sm overflow-x-auto shrink-0">
      <button
        class="flex items-center gap-1 text-muted hover:text-highlighted transition-colors px-1.5 py-0.5 rounded hover:bg-elevated/50"
        @click="navigateTo('/')"
      >
        <UIcon name="i-lucide-home" class="size-4" />
      </button>
      <template v-for="(crumb, index) in breadcrumbs" :key="crumb.path">
        <UIcon name="i-lucide-chevron-right" class="size-3 text-muted shrink-0" />
        <button
          class="text-muted hover:text-highlighted transition-colors px-1.5 py-0.5 rounded hover:bg-elevated/50 whitespace-nowrap"
          @click="navigateTo(crumb.path)"
        >
          {{ crumb.label }}
        </button>
      </template>
    </div>

    <!-- Loading state -->
    <div v-if="pending" class="flex items-center justify-center gap-2 py-12 text-muted">
      <UIcon name="i-lucide-loader-2" class="size-5 animate-spin" />
      <span>加载中...</span>
    </div>

    <!-- Error state -->
    <div v-else-if="error" class="flex flex-col items-center justify-center gap-3 py-12 text-error">
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

    <!-- Empty directory -->
    <div v-else-if="data && data.entries.length === 0" class="flex flex-col items-center justify-center gap-2 py-12 text-muted">
      <UIcon name="i-lucide-folder-open" class="size-8" />
      <span class="text-sm">此目录为空</span>
    </div>

    <!-- File list -->
    <div v-else-if="data" class="flex-1 overflow-y-auto">
      <button
        v-for="entry in data.entries"
        :key="entry.path"
        class="w-full flex items-center gap-3 px-3 py-2 text-sm transition-colors hover:bg-elevated/50 cursor-pointer"
        :class="isFileSelected(entry) ? 'bg-elevated/80 border-l-2 border-primary' : 'border-l-2 border-transparent'"
        @click="entry.type === 'directory' ? navigateTo(entry.path) : selectFile(entry)"
      >
        <UIcon :name="getFileIcon(entry)" class="size-4 shrink-0" :class="entry.type === 'directory' ? 'text-primary' : 'text-muted'" />
        <span class="flex-1 text-left truncate text-highlighted">{{ entry.name }}</span>
        <span v-if="entry.type === 'file' && entry.size != null" class="text-xs text-muted whitespace-nowrap">
          {{ formatFileSize(entry.size) }}
        </span>
      </button>
    </div>
  </div>
</template>
