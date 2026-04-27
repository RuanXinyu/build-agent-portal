# File Preview Maximize in Message Area — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move file preview maximize from fullscreen overlay to message-area overlay, and fix the broken message scrolling.

**Architecture:** Lift `maximizedFile` state to `chat/[id].vue`. The page renders a `FilePreview` overlay inside the `UContainer` when maximized. `BrowserPanel` emits events to request maximize/minimize. Fix scrolling by restoring `overflow-y-auto` on the dashboard panel body and making `UContainer` a proper flex scroll container.

**Tech Stack:** Vue 3, Nuxt UI v4, @guolao/vue-monaco-editor

---

### Task 1: Fix message area scrolling

The `:ui="{ body: 'p-0 sm:p-0 overscroll-none' }"` prop on `UDashboardPanel` **replaces** (not merges) the default body classes, which strips `flex flex-col flex-1 overflow-y-auto` from the body wrapper. This kills scrolling. Additionally, `UContainer` has `overflow-hidden` which clips content.

**Files:**
- Modify: `app/pages/chat/[id].vue:124` (UDashboardPanel `:ui` prop)
- Modify: `app/pages/chat/[id].vue:139` (UContainer classes)

- [ ] **Step 1: Fix UDashboardPanel body classes**

In `app/pages/chat/[id].vue`, change the `:ui` prop on `UDashboardPanel` (line 124) to restore the critical default classes:

```vue
:ui="{ body: 'flex flex-col flex-1 overflow-y-auto p-0 sm:p-0 overscroll-none' }"
```

This restores `flex`, `flex-col`, `flex-1`, and `overflow-y-auto` while keeping the custom padding and overscroll behavior.

- [ ] **Step 2: Fix UContainer overflow**

On the same file, change the `UContainer` class (line 139) from `overflow-hidden` to `overflow-y-auto min-h-0`:

```vue
<UContainer class="flex-1 flex flex-col gap-4 sm:gap-6 min-w-0 min-h-0 overflow-y-auto relative">
```

`min-h-0` allows the flex child to shrink below its content size, and `overflow-y-auto` enables scrolling. Together with the fixed dashboard panel body, this creates a proper scroll container that `UChatMessages` can find via its `getScrollParent()` utility.

- [ ] **Step 3: Verify scrolling works**

Run: `pnpm dev`

Manual test: open a chat with enough messages to overflow, confirm messages scroll smoothly within the message area (not at the document level).

- [ ] **Step 4: Commit**

```bash
git add app/pages/chat/[id].vue
git commit -m "fix: restore message area scrolling in chat detail page"
```

---

### Task 2: Modify BrowserPanel to emit maximize events instead of managing overlay

Remove the fullscreen overlay and `isMaximized` state from `BrowserPanel`. Add new props/emits for communication with the page.

**Files:**
- Modify: `app/components/file/BrowserPanel.vue`

- [ ] **Step 1: Update script section**

Replace the entire `<script setup>` in `app/components/file/BrowserPanel.vue` with:

```vue
<script setup lang="ts">
const props = defineProps<{
  open: boolean
  maximizedFile: string | null
}>()

const emit = defineEmits<{
  'update:open': [value: boolean]
  'maximize': [path: string]
  'select-file': [path: string]
}>()

// --- State ---
const currentPath = ref('~')
const selectedFilePath = ref<string | null>(null)

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
  emit('select-file', path)
}

function onMaximize() {
  if (selectedFilePath.value) {
    emit('maximize', selectedFilePath.value)
  }
}

function closePanel() {
  emit('update:open', false)
}
</script>
```

Key changes:
- Removed `isMaximized` ref
- Added `maximizedFile` prop
- Added `maximize` and `select-file` emits
- `onMaximize` now emits the selected file path to the parent
- `onSelectFile` now also emits `select-file` so the page can track file changes
- Removed `isMaximized` reset from the `watch(open)` handler

- [ ] **Step 2: Update template — remove fullscreen overlay, fix preview condition**

Replace the entire `<template>` in `app/components/file/BrowserPanel.vue` with:

```vue
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
      </div>

      <!-- File list section -->
      <div class="flex-1 overflow-hidden">
        <FileList
          :current-path="currentPath"
          :selected-file-path="selectedFilePath"
          @navigate="onNavigate"
          @select-file="onSelectFile"
        />
      </div>

      <!-- File preview section (hidden when current file is maximized in message area) -->
      <div
        v-if="selectedFilePath && maximizedFile !== selectedFilePath"
        class="border-t border-default"
        style="height: 40%"
      >
        <FilePreview
          :file-path="selectedFilePath"
          :embedded="true"
          @maximize="onMaximize"
        />
      </div>
    </div>
  </Transition>
</template>
```

Key changes:
- Removed the `<Transition name="fade">` fullscreen overlay block entirely
- Changed preview visibility condition from `!isMaximized` to `maximizedFile !== selectedFilePath`
- The maximize button in FilePreview still works — it now bubbles up to the page

- [ ] **Step 3: Update styles — remove fade transition**

Replace the `<style scoped>` in `app/components/file/BrowserPanel.vue` with:

```vue
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
```

Removed the `.fade-*` rules since the fullscreen overlay is gone.

- [ ] **Step 4: Commit**

```bash
git add app/components/file/BrowserPanel.vue
git commit -m "refactor: lift maximize state from BrowserPanel to page"
```

---

### Task 3: Add maximized preview overlay to chat page

Add the `maximizedFile` state to `chat/[id].vue`, wire up events from `BrowserPanel`, and render the overlay `FilePreview` inside the message area.

**Files:**
- Modify: `app/pages/chat/[id].vue`

- [ ] **Step 1: Add state and event handlers in script**

In `app/pages/chat/[id].vue`, add after line 29 (`const panelOpen = ref(false)`):

```typescript
const maximizedFile = ref<string | null>(null)

// Clear maximized state when panel closes
watch(panelOpen, (open) => {
  if (!open) {
    maximizedFile.value = null
  }
})

function onFileMaximize(path: string) {
  maximizedFile.value = path
}

function onFileSelected(path: string) {
  if (maximizedFile.value !== null) {
    maximizedFile.value = path
  }
}

function onMinimizePreview() {
  maximizedFile.value = null
}

function onPreviewKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape' && maximizedFile.value) {
    maximizedFile.value = null
  }
}
```

- [ ] **Step 2: Add overlay inside UContainer, before closing tag**

In the template, insert the overlay inside `UContainer`, after the `UChatPrompt` block (after line 189), before the `</UContainer>` closing tag:

```vue
        <!-- Maximized file preview overlay -->
        <Transition name="fade">
          <div
            v-if="maximizedFile"
            class="absolute inset-0 z-20 bg-default flex flex-col"
            @keydown="onPreviewKeydown"
          >
            <!-- Toolbar -->
            <div class="flex items-center gap-2 px-3 py-2 border-b border-default bg-elevated/30 text-sm shrink-0">
              <div class="flex-1" />
              <button
                class="inline-flex items-center justify-center size-7 rounded-md text-muted hover:text-highlighted hover:bg-elevated/50 transition-colors"
                @click="onMinimizePreview"
              >
                <UIcon name="i-lucide-minimize-2" class="size-4" />
              </button>
            </div>
            <!-- File preview -->
            <div class="flex-1 min-h-0">
              <FilePreview
                :file-path="maximizedFile"
                :embedded="false"
                @maximize="onMinimizePreview"
              />
            </div>
          </div>
        </Transition>
```

Note: The `FilePreview` component already has its own action bar with filename, download button, etc. The toolbar here just adds a dedicated minimize button. When FilePreview emits `maximize` (toggling), we treat it as minimize since we're already in maximized state.

- [ ] **Step 3: Update BrowserPanel bindings**

Change the `FileBrowserPanel` tag (line 192) to pass new props and handle new events:

```vue
        <FileBrowserPanel
          v-model:open="panelOpen"
          :maximized-file="maximizedFile"
          @maximize="onFileMaximize"
          @select-file="onFileSelected"
        />
```

- [ ] **Step 4: Add fade transition styles**

Add a `<style scoped>` block at the end of the file (after `</template>`):

```vue
<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.15s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
```

- [ ] **Step 5: Commit**

```bash
git add app/pages/chat/[id].vue
git commit -m "feat: add file preview overlay in message area when maximized"
```

---

### Task 4: Fix FilePreview maximize button behavior

Currently `FilePreview` has its own `isMaximized` local state and an Escape key listener. In the new flow, the maximize button should simply emit the event — the parent decides what "maximize" means. The local `isMaximized` state in `FilePreview` is only meaningful for the button icon (maximize vs minimize), but since the parent now controls the actual maximize state, we should simplify.

**Files:**
- Modify: `app/components/file/FilePreview.vue`

- [ ] **Step 1: Remove local isMaximized state and simplify**

In `app/components/file/FilePreview.vue`, make these changes in the `<script setup>`:

Remove the `isMaximized` ref (line 22):
```typescript
// DELETE this line:
const isMaximized = ref(false)
```

Simplify `toggleMaximize` (lines 218-221) to just emit:
```typescript
function toggleMaximize() {
  emit('maximize')
}
```

Remove the `onKeydown` function (lines 223-228) and its lifecycle hooks (lines 230-236). The Escape key is now handled by the page-level overlay.

Remove `defineExpose` (line 238).

- [ ] **Step 2: Fix maximize button icon**

Since `FilePreview` no longer tracks `isMaximized`, the button should always show the `maximize-2` icon (the component itself doesn't know if it's in maximized mode). Change line 295:

```vue
<UIcon name="i-lucide-maximize-2" class="size-4" />
```

(This replaces the ternary `isMaximized ? 'i-lucide-minimize-2' : 'i-lucide-maximize-2'`.)

- [ ] **Step 3: Commit**

```bash
git add app/components/file/FilePreview.vue
git commit -m "refactor: simplify FilePreview maximize to emit-only"
```

---

### Task 5: Verify and final commit

- [ ] **Step 1: Run dev server and manually test all scenarios**

Run: `pnpm dev`

Test checklist:
1. Open a chat → messages scroll properly within the message area
2. Open file browser panel → select a file → small preview shows in panel
3. Click maximize in panel preview → overlay appears in message area with toolbar + preview
4. While maximized, select a different file in panel → overlay updates to new file, stays maximized
5. Click minimize button in overlay toolbar → overlay disappears, panel preview shows current file
6. Press Escape while maximized → overlay disappears
7. Close panel while maximized → overlay disappears
8. Light/dark mode toggle → overlay background matches theme

- [ ] **Step 2: Run lint check**

Run: `pnpm lint`

Fix any lint errors.

- [ ] **Step 3: Final verification commit (if needed)**

```bash
git add -A
git commit -m "fix: address lint errors from file preview maximize changes"
```

Only if there are lint fixes needed.
