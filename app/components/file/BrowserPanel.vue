<script setup lang="ts">
const props = defineProps<{
  open: boolean
}>()

const emit = defineEmits<{
  'update:open': [value: boolean]
}>()

// --- State ---
const currentPath = ref('~')
const selectedFilePath = ref<string | null>(null)
const isMaximized = ref(false)

// --- Resizable panel ---
const DEFAULT_WIDTH = 380
const MIN_WIDTH = 280

const panelWidth = ref(DEFAULT_WIDTH)
const isDragging = ref(false)
const dragStartX = ref(0)
const dragStartWidth = ref(0)

const maxWidth = computed(() => {
  if (import.meta.server) return 800
  return window.innerWidth * 0.6
})

function onMouseDown(e: MouseEvent) {
  isDragging.value = true
  dragStartX.value = e.clientX
  dragStartWidth.value = panelWidth.value

  document.addEventListener('mousemove', onMouseMove)
  document.addEventListener('mouseup', onMouseUp)
  document.body.style.cursor = 'col-resize'
  document.body.style.userSelect = 'none'
}

function onMouseMove(e: MouseEvent) {
  if (!isDragging.value) return
  const delta = dragStartX.value - e.clientX
  const newWidth = Math.min(
    Math.max(MIN_WIDTH, dragStartWidth.value + delta),
    maxWidth.value
  )
  panelWidth.value = Math.round(newWidth)
}

function onMouseUp() {
  isDragging.value = false
  document.removeEventListener('mousemove', onMouseMove)
  document.removeEventListener('mouseup', onMouseUp)
  document.body.style.cursor = ''
  document.body.style.userSelect = ''
}

// Reset state when panel opens
watch(() => props.open, (newVal) => {
  if (newVal) {
    currentPath.value = '~'
    selectedFilePath.value = null
    isMaximized.value = false
    panelWidth.value = DEFAULT_WIDTH
  }
})

// Cleanup event listeners on unmount
onUnmounted(() => {
  document.removeEventListener('mousemove', onMouseMove)
  document.removeEventListener('mouseup', onMouseUp)
})

// --- Event handlers ---
function onNavigate(path: string) {
  currentPath.value = path
  selectedFilePath.value = null
}

function onSelectFile(path: string) {
  selectedFilePath.value = path
}

function onMaximize() {
  isMaximized.value = !isMaximized.value
}

function closePanel() {
  emit('update:open', false)
}
</script>

<template>
  <Transition name="slide">
    <div
      v-if="open"
      class="h-full flex flex-col border-l border-default bg-default relative"
      :style="{ width: `${panelWidth}px` }"
    >
      <!-- Drag handle (left edge) -->
      <div
        class="absolute top-0 left-0 bottom-0 w-1 cursor-col-resize hover:bg-primary/30 active:bg-primary/50 transition-colors z-10"
        :class="{ 'bg-primary/50': isDragging }"
        @mousedown="onMouseDown"
      />

      <!-- Panel header -->
      <div class="flex items-center gap-2 px-3 py-2.5 border-b border-default bg-elevated/30 shrink-0">
        <UIcon name="i-lucide-folder-tree" class="size-4 text-primary" />
        <span class="text-sm font-medium text-highlighted">项目文件</span>
        <div class="flex-1" />
        <button
          class="inline-flex items-center justify-center size-7 rounded-md text-muted hover:text-highlighted hover:bg-elevated/50 transition-colors"
          @click="closePanel"
        >
          <UIcon name="i-lucide-x" class="size-4" />
        </button>
      </div>

      <!-- File list section -->
      <div class="flex-1 overflow-hidden">
        <FileFileList
          :current-path="currentPath"
          :selected-file-path="selectedFilePath"
          @navigate="onNavigate"
          @select-file="onSelectFile"
        />
      </div>

      <!-- File preview section (shows when a file is selected) -->
      <div
        v-if="selectedFilePath"
        class="border-t border-default"
        style="height: 40%"
      >
        <FileFilePreview
          :file-path="selectedFilePath"
          :embedded="true"
          @maximize="onMaximize"
        />
      </div>
    </div>
  </Transition>
</template>

<style scoped>
.slide-enter-active,
.slide-leave-active {
  transition: transform 0.25s ease, opacity 0.25s ease;
}

.slide-enter-from,
.slide-leave-to {
  transform: translateX(100%);
  opacity: 0;
}
</style>
