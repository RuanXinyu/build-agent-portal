# Patch Multi-File Card Preview Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace Monaco DiffEditor with diff2html for patch/diff file preview, rendering each file in the patch as a separate card with header info and diff content.

**Architecture:** Patch raw text is parsed by `Diff2Html.parse()` into a `FileResult[]`. Each `FileResult` is rendered as a `DiffFileCard` component containing a header (file path + add/delete line counts) and a body (diff2html HTML output). A global toggle switches between side-by-side and inline modes.

**Tech Stack:** diff2html, Vue 3, Nuxt UI, Tailwind CSS

---

## File Structure

| File | Action | Responsibility |
|------|--------|---------------|
| `app/components/file/DiffFileCard.vue` | Create | Single file diff card: header (path + stats) + diff2html body |
| `app/components/file/FilePreview.vue` | Modify | Replace Monaco DiffEditor with v-for DiffFileCard; remove parse-diff |
| `package.json` | Modify | Add diff2html, remove parse-diff |

---

### Task 1: Install diff2html and remove parse-diff

**Files:**
- Modify: `package.json`

- [ ] **Step 1: Install diff2html and uninstall parse-diff**

Run:
```bash
cd D:\codes\BuildMate\chat && pnpm add diff2html && pnpm remove parse-diff
```

Expected: `package.json` now has `diff2html` in dependencies and `parse-diff` is removed.

- [ ] **Step 2: Verify installation**

Run:
```bash
cd D:\codes\BuildMate\chat && node -e "const { Diff2Html } = require('diff2html'); console.log('diff2html loaded:', typeof Diff2Html.parse)"
```

Expected: `diff2html loaded: function`

- [ ] **Step 3: Commit**

```bash
cd D:\codes\BuildMate\chat && git add package.json pnpm-lock.yaml && git commit -m "chore: replace parse-diff with diff2html dependency"
```

---

### Task 2: Create DiffFileCard component

**Files:**
- Create: `app/components/file/DiffFileCard.vue`

- [ ] **Step 1: Create DiffFileCard.vue**

```vue
<script setup lang="ts">
import { Diff2Html } from 'diff2html'
import 'diff2html/bundles/css/diff2html.min.css'
import type { FileResult } from 'diff2html/lib/types'

const props = defineProps<{
  fileDiff: FileResult
  diffMode: 'side-by-side' | 'inline'
}>()

const colorMode = useColorMode()

const displayFileName = computed(() => {
  if (props.fileDiff.newName && props.fileDiff.newName !== '/dev/null') {
    return props.fileDiff.newName.replace(/^a\//, '')
  }
  if (props.fileDiff.oldName && props.fileDiff.oldName !== '/dev/null') {
    return props.fileDiff.oldName.replace(/^b\//, '')
  }
  return props.fileDiff.oldName || props.fileDiff.newName || 'unknown'
})

const diffHtml = computed(() => {
  return Diff2Html.generateFromJson([props.fileDiff], {
    outputFormat: props.diffMode === 'side-by-side' ? 'side-by-side' : 'line-by-line',
    drawFileList: false,
    matching: 'lines',
    synchronisedScroll: true,
  })
})

const isDark = computed(() => colorMode.value === 'dark')
</script>

<template>
  <div
    class="rounded-lg border border-default overflow-hidden"
    :class="isDark ? 'd2h-dark' : ''"
  >
    <!-- Card header -->
    <div class="flex items-center gap-3 px-3 py-2 bg-elevated/50 border-b border-default text-sm">
      <UIcon name="i-lucide-file-code-2" class="size-4 shrink-0 text-muted" />
      <span class="truncate text-highlighted font-medium flex-1">{{ displayFileName }}</span>
      <span v-if="fileDiff.addedLines" class="text-xs font-mono text-green-500">+{{ fileDiff.addedLines }}</span>
      <span v-if="fileDiff.deletedLines" class="text-xs font-mono text-red-500">-{{ fileDiff.deletedLines }}</span>
    </div>

    <!-- Card body: diff2html rendered content -->
    <div
      class="d2h-wrapper d2h-file-wrapper"
      v-html="diffHtml"
    />
  </div>
</template>

<style scoped>
/* diff2html overrides: hide its built-in file header since we render our own */
:deep(.d2h-file-header) {
  display: none;
}

:deep(.d2h-files-diff) {
  margin: 0;
}

:deep(.d2h-file-list-wrapper) {
  display: none;
}

/* Light mode adjustments */
:deep(.d2h-tag) {
  display: none;
}

/* Dark mode overrides */
.d2h-dark :deep(.d2h-file-wrapper),
.d2h-dark :deep(.d2h-diff-table) {
  background-color: var(--ui-bg);
  color: var(--ui-text);
}

.d2h-dark :deep(.d2h-code-line) {
  background-color: var(--ui-bg);
}

.d2h-dark :deep(.d2h-code-line-ctn) {
  color: var(--ui-text);
}

.d2h-dark :deep(.d2h-del) {
  background-color: rgba(248, 81, 73, 0.15);
}

.d2h-dark :deep(.d2h-ins) {
  background-color: rgba(46, 160, 67, 0.15);
}

.d2h-dark :deep(.d2h-info) {
  background-color: var(--ui-bg-elevated);
  color: var(--ui-text-dimmed);
}

.d2h-dark :deep(.d2h-line-num) {
  color: var(--ui-text-dimmed);
}

.d2h-dark :deep(.d2h-code-linenumber) {
  background-color: var(--ui-bg-elevated);
}

.d2h-dark :deep(.d2h-empty-placeholder) {
  background-color: var(--ui-bg-elevated);
}
</style>
```

- [ ] **Step 2: Verify the component has no syntax errors by checking it loads**

Run:
```bash
cd D:\codes\BuildMate\chat && npx vue-tsc --noEmit --pretty 2>&1 | head -30
```

Expected: No errors referencing `DiffFileCard.vue`. (Other pre-existing type errors may exist and are acceptable.)

- [ ] **Step 3: Commit**

```bash
cd D:\codes\BuildMate\chat && git add app/components/file/DiffFileCard.vue && git commit -m "feat: add DiffFileCard component for per-file diff rendering"
```

---

### Task 3: Update FilePreview.vue to use DiffFileCard

**Files:**
- Modify: `app/components/file/FilePreview.vue`

This is the core change. We need to:
1. Remove `parse-diff` import and `parsePatchContent()` / `diffData`
2. Add `diff2html` import and `parsedFiles` computed
3. Replace the `<VueMonacoDiffEditor>` template block with `v-for` of `<DiffFileCard>`
4. Remove `VueMonacoDiffEditor` from the import (keep `VueMonacoEditor` for code files)

- [ ] **Step 1: Replace imports at the top of `<script setup>`**

Old (line 1-2):
```ts
import { VueMonacoEditor, VueMonacoDiffEditor } from '@guolao/vue-monaco-editor'
import parseDiff from 'parse-diff'
```

New:
```ts
import { VueMonacoEditor } from '@guolao/vue-monaco-editor'
import { Diff2Html } from 'diff2html'
```

- [ ] **Step 2: Replace the diff parsing section (lines 190-245)**

Old (lines 190-247):
```ts
// --- Diff/Patch parsing ---

function parsePatchContent(content: string): { original: string, modified: string, language: string } {
  const files = parseDiff(content)
  if (!files.length) {
    return { original: '', modified: '', language: 'plaintext' }
  }

  const originalLines: string[] = []
  const modifiedLines: string[] = []

  for (const file of files) {
    for (const chunk of file.chunks) {
      for (const change of chunk.changes) {
        const lineContent = change.content.slice(1) // strip prefix char (+/-/space)
        if (change.type === 'normal') {
          originalLines.push(lineContent)
          modifiedLines.push(lineContent)
        } else if (change.type === 'del') {
          originalLines.push(lineContent)
        } else if (change.type === 'add') {
          modifiedLines.push(lineContent)
        }
      }
    }
  }

  // Detect language from the patched file name
  const fileName = files[0]?.to || files[0]?.from || ''
  const ext = fileName.includes('.') ? '.' + fileName.split('.').pop() : ''
  const langMap: Record<string, string> = {
    '.ts': 'typescript', '.tsx': 'typescript',
    '.js': 'javascript', '.jsx': 'javascript',
    '.vue': 'html', '.py': 'python', '.css': 'css',
    '.html': 'html', '.json': 'json', '.yaml': 'yaml',
    '.yml': 'yaml', '.go': 'go', '.rs': 'rust',
    '.java': 'java', '.c': 'c', '.cpp': 'cpp',
    '.rb': 'ruby', '.php': 'php', '.swift': 'swift',
    '.kt': 'kotlin', '.sql': 'sql', '.sh': 'shell',
    '.md': 'markdown'
  }
  const language = langMap[ext.toLowerCase()] || 'plaintext'

  return {
    original: originalLines.join('\n'),
    modified: modifiedLines.join('\n'),
    language
  }
}

const diffData = computed(() => {
  if (!isDiff.value || !data.value?.content) {
    return { original: '', modified: '', language: 'plaintext' }
  }
  return parsePatchContent(data.value.content)
})

const diffMode = ref<'side-by-side' | 'inline'>('side-by-side')
```

New:
```ts
// --- Diff/Patch parsing ---

const parsedFiles = computed(() => {
  if (!isDiff.value || !data.value?.content) return []
  return Diff2Html.parse(data.value.content)
})

const diffMode = ref<'side-by-side' | 'inline'>('side-by-side')
```

- [ ] **Step 3: Replace the diff template block (lines 358-376)**

Old:
```html
        <!-- Diff/Patch rendering -->
        <div v-else-if="isDiff" class="flex-1 overflow-hidden">
          <VueMonacoDiffEditor
            :original="diffData.original"
            :modified="diffData.modified"
            :language="diffData.language"
            :options="{
              readOnly: true,
              renderSideBySide: diffMode === 'side-by-side',
              minimap: { enabled: false },
              scrollBeyondLastLine: false,
              lineNumbers: 'on',
              renderLineHighlight: 'none',
              scrollbar: { verticalScrollbarSize: 8, horizontalScrollbarSize: 8 }
            }"
            :theme="($colorMode?.value === 'dark' ? 'vs-dark' : 'vs')"
            class="h-full"
          />
        </div>
```

New:
```html
        <!-- Diff/Patch rendering -->
        <div v-else-if="isDiff" class="flex-1 overflow-y-auto">
          <div class="flex flex-col gap-4 p-4">
            <DiffFileCard
              v-for="(file, index) in parsedFiles"
              :key="index"
              :file-diff="file"
              :diff-mode="diffMode"
            />
          </div>
        </div>
```

- [ ] **Step 4: Verify no type errors in FilePreview.vue**

Run:
```bash
cd D:\codes\BuildMate\chat && npx vue-tsc --noEmit --pretty 2>&1 | grep -i "FilePreview" | head -20
```

Expected: No errors referencing `FilePreview.vue`.

- [ ] **Step 5: Commit**

```bash
cd D:\codes\BuildMate\chat && git add app/components/file/FilePreview.vue && git commit -m "feat: render multi-file patches as separate DiffFileCards using diff2html"
```

---

### Task 4: Manual verification and final commit

- [ ] **Step 1: Start dev server**

Run:
```bash
cd D:\codes\BuildMate\chat && pnpm dev
```

Wait for the server to be ready (Nuxt outputs "Local: http://localhost:...").

- [ ] **Step 2: Verify in browser**

Open the app in a browser, navigate to a chat with a `.patch` file containing multi-file changes. Confirm:

1. Each file in the patch appears as a separate card
2. Each card header shows the full file path and +/- line counts
3. Side-by-side toggle works (click the columns/align-left icon in the action bar)
4. Dark/light mode colors look correct
5. Non-diff files (code, markdown) still preview normally

- [ ] **Step 3: Final commit if any fixes needed**

If any fixes were needed during verification:
```bash
cd D:\codes\BuildMate\chat && git add -A && git commit -m "fix: polish diff2html multi-file card rendering"
```
