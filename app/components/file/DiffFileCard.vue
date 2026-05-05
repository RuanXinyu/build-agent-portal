<script setup lang="ts">
import { html as renderDiffHtml } from 'diff2html'
import 'diff2html/bundles/css/diff2html.min.css'
import type { DiffFile } from 'diff2html/lib/types'

const props = defineProps<{
  fileDiff: DiffFile
  diffMode: 'side-by-side' | 'inline'
}>()

const colorMode = useColorMode()

const displayFileName = computed(() => {
  const name = props.fileDiff.newName !== '/dev/null' && props.fileDiff.newName
    ? props.fileDiff.newName
    : props.fileDiff.oldName !== '/dev/null' && props.fileDiff.oldName
      ? props.fileDiff.oldName
      : ''
  return name || 'unknown'
})

const renderedDiff = computed(() => {
  try {
    return {
      html: renderDiffHtml([props.fileDiff], {
        outputFormat: props.diffMode === 'side-by-side' ? 'side-by-side' : 'line-by-line',
        drawFileList: false,
        matching: 'lines'
      }),
      errorMessage: null as string | null
    }
  } catch (err: unknown) {
    const errorMessage = err instanceof Error ? err.message : '未知渲染错误'
    console.error('[DiffFileCard] failed to render diff html:', {
      oldName: props.fileDiff.oldName,
      newName: props.fileDiff.newName,
      error: err
    })
    return {
      html: '',
      errorMessage
    }
  }
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
      v-if="renderedDiff.errorMessage"
      class="px-3 py-4 text-sm text-warning bg-warning/5 border-t border-warning/30"
    >
      <div class="flex items-start gap-2">
        <UIcon name="i-lucide-triangle-alert" class="size-4 mt-0.5 shrink-0" />
        <div class="min-w-0">
          <p>该文件 Diff 渲染失败</p>
          <p class="mt-1 text-xs text-muted truncate">
            错误: {{ renderedDiff.errorMessage }}
          </p>
        </div>
      </div>
    </div>
    <div
      v-else
      class="d2h-wrapper d2h-file-wrapper"
      v-html="renderedDiff.html"
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

/* Hide diff2html file tags */
:deep(.d2h-tag) {
  display: none;
}

/* Anchor absolute line-number blocks inside each diff row */
:deep(.d2h-diff-tbody tr) {
  position: relative;
}

/* Keep diff rendering clipped inside card body */
:deep(.d2h-file-wrapper),
:deep(.d2h-file-diff) {
  overflow: hidden;
}

/* Fallback anchors for inline containers */
:deep(.d2h-code-line),
:deep(.d2h-code-side-line) {
  position: relative;
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
