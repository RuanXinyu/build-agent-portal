<script setup lang="ts">
interface TreeEntry {
  filename: string
  type: 'dir' | 'file'
  size?: number
  files?: TreeEntry[]
}

interface FileEntry {
  name: string
  path: string
  type: 'dir' | 'file'
  size?: number
}

const props = defineProps<{
  chatId: string
  currentPath: string
  selectedFilePath: string | null
}>()

const emit = defineEmits<{
  navigate: [path: string]
  selectFile: [path: string]
}>()

const treeData = ref<TreeEntry[] | null>(null)
const pending = ref(false)
const error = ref<Error | null>(null)

async function fetchTree() {
  pending.value = true
  error.value = null
  try {
    const result = await $fetch(`/api/v1/agent/chats/${props.chatId}/files`, {
      query: { filepath: '/' }
    }) as any
    console.log('[FileList] API raw result:', JSON.stringify(result).slice(0, 500))
    // Handle both { files: [...] } and { data: { files: [...] } } shapes
    const files = Array.isArray(result?.files)
      ? result.files
      : Array.isArray(result?.data?.files)
        ? result.data.files
        : null
    if (!files) {
      console.error('[FileList] Unexpected response shape:', Object.keys(result || {}))
      throw new Error('Invalid response from file API')
    }
    treeData.value = files
    console.log('[FileList] treeData set:', treeData.value.length, 'entries')
  } catch (e: unknown) {
    console.error('[FileList] fetch error:', e)
    error.value = e instanceof Error ? e : new Error(String(e))
  } finally {
    pending.value = false
  }
}

fetchTree()

defineExpose({ refresh: fetchTree })

// Find a node in the tree by path segments
function findNode(path: string): TreeEntry[] | null {
  if (path === '/' || path === '') return treeData.value
  const segments = path.split('/').filter(Boolean)
  let current = treeData.value
  for (const segment of segments) {
    if (!current) return null
    const node = current.find(e => e.filename === segment && e.type === 'dir')
    if (!node || !node.files) return null
    current = node.files
  }
  return current
}

// Flatten current directory entries for display
const entries = computed<FileEntry[]>(() => {
  const nodes = findNode(props.currentPath)
  if (!nodes) return []

  return nodes.map(node => {
    const prefix = props.currentPath === '/' ? '' : props.currentPath
    const entryPath = `${prefix}/${node.filename}`
    return {
      name: node.filename,
      path: entryPath,
      type: node.type,
      size: node.type === 'file' ? node.size : undefined,
    }
  })
})

// Breadcrumb segments
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
  if (entry.type === 'dir') {
    return 'i-lucide-folder'
  }
  const name = entry.name.toLowerCase()
  const extMap: Record<string, string> = {
    '.ts': 'i-lucide-file-code-2', '.tsx': 'i-lucide-file-code-2',
    '.js': 'i-lucide-file-code-2', '.jsx': 'i-lucide-file-code-2',
    '.vue': 'i-lucide-file-code-2', '.py': 'i-lucide-file-code-2',
    '.json': 'i-lucide-braces', '.md': 'i-lucide-file-text',
    '.css': 'i-lucide-file-code-2', '.html': 'i-lucide-file-code-2',
    '.sql': 'i-lucide-database', '.sh': 'i-lucide-file-code-2',
    '.yml': 'i-lucide-file-text', '.yaml': 'i-lucide-file-text',
    '.toml': 'i-lucide-file-text', '.xml': 'i-lucide-file-text',
    '.patch': 'i-lucide-git-compare', '.diff': 'i-lucide-git-compare',
  }
  for (const [ext, icon] of Object.entries(extMap)) {
    if (name.endsWith(ext)) return icon
  }
  if (name === 'dockerfile') return 'i-lucide-container'
  return 'i-lucide-file'
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
      <template v-for="crumb in breadcrumbs" :key="crumb.path">
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
        @click="fetchTree()"
      />
    </div>

    <!-- Empty directory -->
    <div v-else-if="entries.length === 0 && treeData !== null" class="flex flex-col items-center justify-center gap-2 py-12 text-muted">
      <UIcon name="i-lucide-folder-open" class="size-8" />
      <span class="text-sm">此目录为空</span>
    </div>

    <!-- File list -->
    <div v-else-if="treeData !== null" class="flex-1 overflow-y-auto">
      <button
        v-for="entry in entries"
        :key="entry.path"
        class="w-full flex items-center gap-3 px-3 py-2 text-sm transition-colors hover:bg-elevated/50 cursor-pointer"
        :class="isFileSelected(entry) ? 'bg-elevated/80 border-l-2 border-primary' : 'border-l-2 border-transparent'"
        @click="entry.type === 'dir' ? navigateTo(entry.path) : selectFile(entry)"
      >
        <UIcon :name="getFileIcon(entry)" class="size-4 shrink-0" :class="entry.type === 'dir' ? 'text-primary' : 'text-muted'" />
        <span class="flex-1 text-left truncate text-highlighted">{{ entry.name }}</span>
        <span v-if="entry.type === 'file' && entry.size != null" class="text-xs text-muted whitespace-nowrap">
          {{ formatFileSize(entry.size) }}
        </span>
      </button>
    </div>
  </div>
</template>
