<script setup lang="ts">
import { html as renderDiffHtml } from 'diff2html'
import 'diff2html/bundles/css/diff2html.min.css'
import type { FileResult } from 'diff2html/lib/types'

const props = defineProps<{
  fileDiff: FileResult
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

const diffHtml = computed(() => {
  return renderDiffHtml([props.fileDiff], {
    outputFormat: props.diffMode === 'side-by-side' ? 'side-by-side' : 'line-by-line',
    drawFileList: false,
    matching: 'lines',
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

/* Hide diff2html file tags */
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
