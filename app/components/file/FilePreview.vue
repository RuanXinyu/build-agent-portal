<script setup lang="ts">
import { VueMonacoEditor } from '@guolao/vue-monaco-editor'
import { parse as parseDiff } from 'diff2html'
import type { DiffFile } from 'diff2html/lib/types'
import emoji from '@comark/vue/plugins/emoji'
import binding, { Binding } from '@comark/vue/plugins/binding'
import breaks from '@comark/vue/plugins/breaks'
import mermaid, { Mermaid } from '@comark/vue/plugins/mermaid'
import taskList from '@comark/vue/plugins/task-list'
import toc from '@comark/vue/plugins/toc'
import highlight from '@comark/vue/plugins/highlight'
import githubLight from '@shikijs/themes/github-light'
import githubDark from '@shikijs/themes/github-dark'

interface FileContentResponse {
  filepath: string
  language: string | null
  size: number
  content: string | null
  previewable: boolean
}

interface ParsedDiffState {
  ok: boolean
  files: DiffFile[]
  errorMessage: string | null
  rawContent: string
}

const props = defineProps<{
  chatId: string
  filePath: string | null
  embedded?: boolean
}>()

const emit = defineEmits<{
  maximize: []
}>()

// --- Data fetching ---
const data = ref<FileContentResponse | null>(null)
const pending = ref(false)
const error = ref<Error | null>(null)

async function fetchData() {
  if (!props.filePath) return
  pending.value = true
  error.value = null
  try {
    data.value = await $fetch<FileContentResponse>(`/api/v1/agent/chats/${props.chatId}/files/content`, {
      query: { path: props.filePath }
    })
  } catch (e: unknown) {
    error.value = e instanceof Error ? e : new Error(String(e))
  } finally {
    pending.value = false
  }
}

watch(() => props.filePath, (newPath) => {
  if (newPath) {
    fetchData()
  }
}, { immediate: true })

// --- Language helpers ---

// Map API language name to Monaco Editor language ID
function getMonacoLanguage(language: string | null): string {
  if (!language) return 'plaintext'
  const map: Record<string, string> = {
    typescript: 'typescript',
    javascript: 'javascript',
    python: 'python',
    java: 'java',
    c: 'c',
    cpp: 'cpp',
    go: 'go',
    rust: 'rust',
    ruby: 'ruby',
    php: 'php',
    swift: 'swift',
    kotlin: 'kotlin',
    vue: 'html',
    html: 'html',
    css: 'css',
    scss: 'scss',
    less: 'less',
    shell: 'shell',
    bash: 'shell',
    markdown: 'markdown',
    json: 'json',
    yaml: 'yaml',
    toml: 'toml',
    xml: 'xml',
    sql: 'sql',
    dockerfile: 'dockerfile',
    diff: 'diff',
    graphql: 'graphql',
    plain_text: 'plaintext'
  }
  return map[language.toLowerCase()] || 'plaintext'
}

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
    diff: 'Diff',
    plain_text: 'Plain Text'
  }
  return map[language.toLowerCase()] || language
}

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
    diff: 'i-lucide-git-compare'
  }
  return iconMap[language.toLowerCase()] || 'i-lucide-file'
}

// --- Computed properties ---

const lineCount = computed(() => {
  if (!data.value?.content) return 0
  return data.value.content.split('\n').length
})

const fileExtension = computed(() => {
  if (!data.value?.filepath) return ''
  const parts = data.value.filepath.split('.')
  return parts.length > 1 ? `.${parts[parts.length - 1]}` : ''
})

const isMarkdown = computed(() => {
  return data.value?.language?.toLowerCase() === 'markdown'
})

const isDiff = computed(() => {
  if (!data.value) return false
  if (data.value.language?.toLowerCase() === 'diff') return true
  const filepath = data.value.filepath.toLowerCase()
  if (!filepath) {
    return false
  }
  return filepath.endsWith('.patch') || filepath.endsWith('.diff')
})

const downloadUrl = computed(() => {
  if (!props.filePath) return ''
  return `/api/v1/agent/chats/${props.chatId}/files/download?path=${encodeURIComponent(props.filePath)}`
})

// --- Diff/Patch parsing ---

const parsedDiff = computed<ParsedDiffState>(() => {
  const rawContent = data.value?.content || ''
  if (!isDiff.value || !rawContent) {
    return {
      ok: true,
      files: [],
      errorMessage: null,
      rawContent
    }
  }

  try {
    return {
      ok: true,
      files: parseDiff(rawContent),
      errorMessage: null,
      rawContent
    }
  } catch (err: unknown) {
    const errorMessage = err instanceof Error ? err.message : '未知解析错误'
    console.error('[FilePreview] failed to parse diff content:', err)
    return {
      ok: false,
      files: [],
      errorMessage,
      rawContent
    }
  }
})

const diffMode = ref<'side-by-side' | 'inline'>('side-by-side')
const hasRenderableDiff = computed(() => parsedDiff.value.ok && parsedDiff.value.files.length > 0)
const fallbackDiffMessage = computed(() => {
  if (!parsedDiff.value.ok) {
    return 'Diff 渲染失败，已回退为原始 Patch 文本'
  }
  return '未解析到可渲染的文件变更，已展示原始 Patch 文本'
})

const markdownRenderError = ref<Error | null>(null)
const markdownFallbackMessage = computed(() => {
  return 'Markdown 预览失败，已回退为原始文本'
})

watch(
  () => [data.value?.filepath, data.value?.content],
  () => {
    markdownRenderError.value = null
  }
)

onErrorCaptured((capturedError) => {
  if (!isMarkdown.value) {
    return
  }
  const normalizedError = capturedError instanceof Error
    ? capturedError
    : new Error(String(capturedError))
  markdownRenderError.value = normalizedError
  console.error('[FilePreview] failed to render markdown content:', capturedError)
  return false
})

// --- Monaco Editor options ---

const editorOptions = computed(() => ({
  readOnly: true,
  minimap: { enabled: false },
  lineNumbers: 'on' as const,
  scrollBeyondLastLine: false,
  renderLineHighlight: 'none' as const,
  folding: true,
  wordWrap: 'on' as const,
  fontSize: 13,
  lineDecorationsWidth: 0,
  lineNumbersMinChars: 3,
  glyphMargin: false,
  contextmenu: false,
  scrollbar: {
    verticalScrollbarSize: 8,
    horizontalScrollbarSize: 8
  },
  padding: { top: 8, bottom: 8 },
  overviewRulerBorder: false,
  hideCursorInOverviewRuler: true,
  overviewRulerLanes: 0,
  renderWhitespace: 'none' as const
}))

// --- Actions ---

function toggleMaximize() {
  emit('maximize')
}

function getDiffFileKey(file: DiffFile): string {
  const oldName = file.oldName || 'unknown-old'
  const newName = file.newName || 'unknown-new'
  const blockCount = Array.isArray(file.blocks) ? file.blocks.length : 0
  return `${oldName}|${newName}|${blockCount}`
}
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
        @click="fetchData()"
      />
    </div>

    <!-- File loaded -->
    <template v-else-if="data">
      <!-- Action bar (always visible, compact when embedded) -->
      <div class="flex items-center gap-2 px-3 py-2 border-b border-default bg-elevated/30 text-sm shrink-0">
        <div class="flex items-center gap-2 flex-1 min-w-0">
          <UIcon :name="getFileIcon(data.language)" class="size-4 shrink-0 text-muted" />
          <span class="truncate text-highlighted font-medium">{{ data.filepath }}</span>
          <template v-if="!embedded">
            <span v-if="data.language" class="text-xs text-muted bg-dimmed px-1.5 py-0.5 rounded">
              {{ getLanguageDisplay(data.language) }}
            </span>
            <span class="text-xs text-muted">{{ lineCount }} 行</span>
          </template>
        </div>
        <div class="flex items-center gap-1 shrink-0">
          <button
            v-if="isDiff && hasRenderableDiff"
            class="inline-flex items-center justify-center size-7 rounded-md text-muted hover:text-highlighted hover:bg-elevated/50 transition-colors"
            title="切换对比模式"
            @click="diffMode = diffMode === 'side-by-side' ? 'inline' : 'side-by-side'"
          >
            <UIcon :name="diffMode === 'side-by-side' ? 'i-lucide-columns' : 'i-lucide-align-left'" class="size-4" />
          </button>
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
            <UIcon name="i-lucide-maximize-2" class="size-4" />
          </button>
        </div>
      </div>

      <!-- Previewable content -->
      <template v-if="data.previewable">
        <!-- Markdown rendering -->
        <div v-if="isMarkdown" class="flex-1 min-h-0 flex flex-col">
          <div v-if="!markdownRenderError" class="flex-1 overflow-y-auto">
            <div class="prose prose-sm dark:prose-invert max-w-none p-4">
              <ChatComark
                :markdown="data.content || ''"
                :plugins="[emoji(), binding(), breaks(), mermaid(), taskList(), toc({ depth: 2 }), highlight({ themes: { light: githubLight, dark: githubDark } })]"
                :components="{ Binding, mermaid: Mermaid }"
              />
            </div>
          </div>
          <div v-else class="flex-1 min-h-0 flex flex-col">
            <div class="mx-4 mt-4 rounded-md border border-warning/40 bg-warning/10 px-3 py-2 text-warning text-sm">
              <div class="flex items-start gap-2">
                <UIcon name="i-lucide-triangle-alert" class="size-4 mt-0.5 shrink-0" />
                <div class="min-w-0">
                  <p>{{ markdownFallbackMessage }}</p>
                  <p v-if="markdownRenderError.message" class="mt-1 text-xs text-muted truncate">
                    渲染错误: {{ markdownRenderError.message }}
                  </p>
                </div>
              </div>
            </div>
            <div class="flex-1 min-h-0 mt-3 overflow-hidden">
              <VueMonacoEditor
                :value="data.content || ''"
                language="markdown"
                :options="editorOptions"
                :theme="($colorMode?.value === 'dark' ? 'vs-dark' : 'vs')"
                class="h-full"
              />
            </div>
          </div>
        </div>

        <!-- Diff/Patch rendering -->
        <div v-else-if="isDiff" class="flex-1 min-h-0 flex flex-col">
          <div v-if="hasRenderableDiff" class="flex-1 overflow-y-auto">
            <div class="flex flex-col gap-4 p-4">
              <FileDiffFileCard
                v-for="file in parsedDiff.files"
                :key="getDiffFileKey(file)"
                :file-diff="file"
                :diff-mode="diffMode"
              />
            </div>
          </div>
          <div v-else class="flex-1 min-h-0 flex flex-col">
            <div class="mx-4 mt-4 rounded-md border border-warning/40 bg-warning/10 px-3 py-2 text-warning text-sm">
              <div class="flex items-start gap-2">
                <UIcon name="i-lucide-triangle-alert" class="size-4 mt-0.5 shrink-0" />
                <div class="min-w-0">
                  <p>{{ fallbackDiffMessage }}</p>
                  <p v-if="parsedDiff.errorMessage" class="mt-1 text-xs text-muted truncate">
                    解析错误: {{ parsedDiff.errorMessage }}
                  </p>
                </div>
              </div>
            </div>
            <div class="flex-1 min-h-0 mt-3 overflow-hidden">
              <VueMonacoEditor
                :value="parsedDiff.rawContent"
                language="diff"
                :options="editorOptions"
                :theme="($colorMode?.value === 'dark' ? 'vs-dark' : 'vs')"
                class="h-full"
              />
            </div>
          </div>
        </div>

        <!-- Code / plain text rendering with Monaco Editor -->
        <div v-else class="flex-1 overflow-hidden">
          <VueMonacoEditor
            :value="data.content || ''"
            :language="getMonacoLanguage(data.language)"
            :options="editorOptions"
            :theme="($colorMode?.value === 'dark' ? 'vs-dark' : 'vs')"
            class="h-full"
          />
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
