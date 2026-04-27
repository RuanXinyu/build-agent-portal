# FilePreview Enhancement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade FilePreview to use Monaco Editor for code files, Monaco Diff Editor for patch files, fix the embedded action bar, and ensure non-previewable files show proper UI.

**Architecture:** Replace the plain-text `<table>` renderer in FilePreview.vue with Monaco Editor (read-only mode). The component detects file type via `data.language` and `filePath` extension, then routes to the appropriate renderer: Monaco Editor for code/text, Monaco Diff Editor for `.patch`/`.diff` files, ChatComark for Markdown, or the existing "cannot preview" UI for binary files. The action bar is restructured to always render (compact when `embedded=true`).

**Tech Stack:** @guolao/vue-monaco-editor, @comark/nuxt (existing), Nuxt 4, Vue 3 Composition API

---

## File Structure

| File | Action | Responsibility |
|------|--------|----------------|
| `app/components/file/FilePreview.vue` | Modify | Complete rewrite of script + template |
| `scripts/python/server/file_mock_data.py` | Modify | Add a `.patch` file for diff testing |
| `package.json` | Modify (via pnpm) | Add @guolao/vue-monaco-editor |

---

### Task 1: Install Monaco Editor dependency

**Files:**
- Modify: `package.json`

- [ ] **Step 1: Install the package**

Run:
```bash
pnpm add @guolao/vue-monaco-editor
```

Expected: `package.json` gains `"@guolao/vue-monaco-editor": "^x.x.x"` in dependencies. `pnpm-lock.yaml` updates.

- [ ] **Step 2: Commit**

```bash
git add package.json pnpm-lock.yaml
git commit -m "chore: add @guolao/vue-monaco-editor dependency"
```

---

### Task 2: Add a diff/patch file to mock data

**Files:**
- Modify: `scripts/python/server/file_mock_data.py`

Add a `.patch` file entry to the mock tree so the Diff Editor can be tested. Also add `diff` language support to `EXTENSION_LANGUAGE_MAP`.

- [ ] **Step 1: Add `.patch` and `.diff` to EXTENSION_LANGUAGE_MAP**

In `file_mock_data.py`, add these entries to `EXTENSION_LANGUAGE_MAP` after the `.dockerfile` line:

```python
    ".diff": "diff",
    ".patch": "diff",
```

- [ ] **Step 2: Add a patch file entry to the mock tree**

In the `"~"` list (root directory), add a patch file entry. Insert after the `("README.md", ...)` entry at the end of the list:

```python
        ("hotfix.patch", "file", 589, 'diff --git a/src/utils/auth.ts b/src/utils/auth.ts\nindex a1b2c3d..e4f5g6h 100644\n--- a/src/utils/auth.ts\n+++ b/src/utils/auth.ts\n@@ -15,6 +15,10 @@ const TOKEN_EXPIRY = "7d"\n \n export interface TokenPayload {\n   userId: string\n   email: string\n-  role: "admin" | "user"\n+  role: "admin" | "user" | "moderator"\n+  permissions: string[]\n }\n+\n+export const DEFAULT_PERMISSIONS = ["read"] as const\n'),
```

- [ ] **Step 3: Verify mock server starts**

Run:
```bash
cd scripts/python/server && python app.py
```

Expected: Server starts on port 5001 without errors. Check `GET http://localhost:5001/api/files?path=~` returns `hotfix.patch` in the list.

- [ ] **Step 4: Commit**

```bash
git add scripts/python/server/file_mock_data.py
git commit -m "feat: add patch file to mock data for diff editor testing"
```

---

### Task 3: Rewrite FilePreview.vue script section

**Files:**
- Modify: `app/components/file/FilePreview.vue`

This task rewrites the entire `<script setup>` block of FilePreview.vue. The template will be rewritten in Task 4.

The key changes:
1. Add language-to-Monaco mapping function
2. Add diff detection computed
3. Import and configure Monaco Editor components
4. Restructure action bar visibility logic (always show, compact when embedded)

- [ ] **Step 1: Replace the entire `<script setup>` block**

Replace everything from `<script setup lang="ts">` to `</script>` with:

```typescript
<script setup lang="ts">
import { VueMonacoEditor } from '@guolao/vue-monaco-editor'

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

// --- Data fetching ---
const data = ref<FileContentResponse | null>(null)
const pending = ref(false)
const error = ref<any>(null)

async function fetchData() {
  if (!props.filePath) return
  pending.value = true
  error.value = null
  try {
    data.value = await $fetch<FileContentResponse>('/api/v1/files/content', {
      query: { path: props.filePath }
    })
  } catch (e: any) {
    error.value = e
  } finally {
    pending.value = false
  }
}

watch(() => props.filePath, (newPath) => {
  if (newPath) {
    fetchData()
  }
})

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
    plain_text: 'plaintext',
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
    plain_text: 'Plain Text',
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
    diff: 'i-lucide-git-compare',
  }
  return iconMap[language.toLowerCase()] || 'i-lucide-file'
}

// --- Computed properties ---

const lineCount = computed(() => {
  if (!data.value?.content) return 0
  return data.value.content.split('\n').length
})

const fileExtension = computed(() => {
  if (!data.value?.name) return ''
  const parts = data.value.name.split('.')
  return parts.length > 1 ? `.${parts[parts.length - 1]}` : ''
})

const isMarkdown = computed(() => {
  return data.value?.language?.toLowerCase() === 'markdown'
})

const isDiff = computed(() => {
  if (!data.value) return false
  if (data.value.language?.toLowerCase() === 'diff') return true
  const name = data.value.name.toLowerCase()
  return name.endsWith('.patch') || name.endsWith('.diff')
})

const downloadUrl = computed(() => {
  if (!props.filePath) return ''
  return `/api/v1/files/download?path=${encodeURIComponent(props.filePath)}`
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
    horizontalScrollbarSize: 8,
  },
  padding: { top: 8, bottom: 8 },
  overviewRulerBorder: false,
  hideCursorInOverviewRuler: true,
  overviewRulerLanes: 0,
  renderWhitespace: 'none' as const,
}))

// --- Actions ---

function toggleMaximize() {
  isMaximized.value = !isMaximized.value
  emit('maximize')
}

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
```

Key differences from the current code:
- Imports `VueMonacoEditor` from `@guolao/vue-monaco-editor`
- Adds `getMonacoLanguage()` function mapping API language → Monaco language ID
- Adds `isDiff` computed for detecting patch/diff files
- Adds `editorOptions` computed with read-only Monaco configuration
- Adds `diff` to `getLanguageDisplay()` and `getFileIcon()` maps
- Keeps all existing fetching, error handling, and keyboard logic unchanged

- [ ] **Step 2: Verify no TypeScript errors**

Run:
```bash
npx nuxi typecheck
```

Expected: No errors related to FilePreview.vue. (There may be pre-existing warnings from other files — those are acceptable.)

- [ ] **Step 3: Commit**

```bash
git add app/components/file/FilePreview.vue
git commit -m "refactor: rewrite FilePreview script with Monaco Editor integration"
```

---

### Task 4: Rewrite FilePreview.vue template section

**Files:**
- Modify: `app/components/file/FilePreview.vue`

Replace the entire `<template>` block. Key changes:
1. Action bar always renders (compact in embedded mode)
2. Code files rendered with `<VueMonacoEditor>` instead of `<table>`
3. Diff files rendered with `<VueMonacoDiffEditor>`
4. Non-previewable section unchanged but now always has action bar above it

- [ ] **Step 1: Replace the entire `<template>` block**

Replace everything from `<template>` to `</template>` with:

```html
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
          <span class="truncate text-highlighted font-medium">{{ data.name }}</span>
          <template v-if="!embedded">
            <span v-if="data.language" class="text-xs text-muted bg-dimmed px-1.5 py-0.5 rounded">
              {{ getLanguageDisplay(data.language) }}
            </span>
            <span class="text-xs text-muted">{{ lineCount }} 行</span>
          </template>
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

        <!-- Diff/Patch rendering -->
        <div v-else-if="isDiff" class="flex-1 overflow-hidden">
          <VueMonacoDiffEditor
            :original="''"
            :modified="data.content || ''"
            :language="getMonacoLanguage(data.language)"
            :options="{
              readOnly: true,
              renderSideBySide: true,
              minimap: { enabled: false },
              scrollBeyondLastLine: false,
              lineNumbers: 'on',
              renderLineHighlight: 'none',
              scrollbar: { verticalScrollbarSize: 8, horizontalScrollbarSize: 8 },
            }"
            :theme="($colorMode?.value === 'dark' ? 'vs-dark' : 'vs')"
            class="h-full"
          />
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
```

Key differences from the current template:
- Action bar: removed `v-if="!embedded"`, now always renders. Language badge and line count wrapped in `<template v-if="!embedded">` for compact mode.
- Code section: replaced `<table>` with `<VueMonacoEditor>` using `editorOptions` computed
- New diff section: `<VueMonacoDiffEditor>` with original="" and modified=file content
- Markdown and non-previewable sections unchanged
- Theme: uses `$colorMode` to switch between `vs-dark` and `vs`

- [ ] **Step 2: Verify the page loads without errors**

Run the Nuxt dev server and navigate to a chat detail page. Click the folder icon, select a code file. Verify:
- Action bar shows filename + download + maximize icons
- Monaco Editor renders the file content with syntax highlighting
- Selecting a different file updates the editor content

- [ ] **Step 3: Verify Markdown rendering**

Click on a `.md` file (e.g., `README.md`). Verify:
- ChatComark renders the Markdown content
- Action bar shows with filename, download icon

- [ ] **Step 4: Verify diff rendering**

Click on `hotfix.patch`. Verify:
- Monaco Diff Editor shows the file content (original side empty, modified side has content)
- Syntax highlighting applies to the diff

- [ ] **Step 5: Verify non-previewable file**

Click on `logo.png` or `data.sqlite`. Verify:
- Shows "无法预览此文件" message with download button
- Action bar still shows with download icon

- [ ] **Step 6: Verify maximize mode**

Click the maximize icon on any previewable file. Verify:
- Full-screen overlay appears with the file content in Monaco Editor
- Escape key closes the maximize overlay
- Download icon works in maximize overlay

- [ ] **Step 7: Commit**

```bash
git add app/components/file/FilePreview.vue
git commit -m "feat: integrate Monaco Editor with syntax highlighting, diff view, and fixed action bar"
```

---

### Task 5: Final verification and cleanup

- [ ] **Step 1: Run full typecheck**

```bash
npx nuxi typecheck
```

Expected: No new errors introduced.

- [ ] **Step 2: Run lint**

```bash
pnpm lint
```

Expected: No new lint errors. Fix any that appear.

- [ ] **Step 3: Final commit if any fixes needed**

```bash
git add -A
git commit -m "fix: address lint/typecheck issues from FilePreview enhancement"
```
