# File Preview Maximize in Message Area — Design Spec

**Date:** 2026-04-27
**Status:** Approved

## Problem

Currently, maximizing the file preview shows a fullscreen overlay (`fixed inset-0 z-50`) that covers the entire page. The user wants maximized preview to appear within the message area instead, so it feels more contextual and doesn't lose the page layout. When switching files while maximized, the maximize state should persist.

## Requirements

1. Maximized preview overlays the message area (not fullscreen)
2. Background is opaque (theme `bg-default`)
3. Switching files while maximized keeps the maximized state
4. Closing the file browser panel also closes the maximized preview
5. Small panel preview hidden when the file is maximized in the message area
6. Escape key dismisses the maximized preview

## Approach: State Lift to Page

Lift the maximize state (`maximizedFile`) from `BrowserPanel` to `chat/[id].vue`. The page controls when the overlay appears, and `BrowserPanel` emits events to request maximize/minimize.

## State Model

**In `chat/[id].vue`:**

```typescript
const maximizedFile = ref<string | null>(null)
```

- `null` → no maximized preview
- file path string → that file is shown maximized in the message area

**State transitions:**

| Action | `maximizedFile` | `selectedFilePath` (panel) |
|--------|-----------------|---------------------------|
| Click maximize in panel | `= selectedFilePath` | unchanged |
| Select different file while maximized | `= new file path` | `= new file path` |
| Click minimize in overlay | `= null` | unchanged |
| Press Escape | `= null` | unchanged |
| Close panel | `= null` | reset to `null` |

## Message Area Overlay Layout

The `UContainer` in `chat/[id].vue` becomes:

```
UContainer (flex-1, overflow-hidden, relative)
  ├── UButton (floating folder toggle, absolute top-3 right-3 z-10)
  ├── UChatMessages (always present, scrolls underneath)
  ├── UChatPrompt (sticky bottom input)
  └── Transition "fade"
       └── div.overlay (absolute inset-0 z-20, bg-default)  [v-if="maximizedFile"]
            ├── Toolbar (h-10, flex, items-center, border-b)
            │    ├── File icon + filename (left)
            │    └── Download button + Minimize button (right, i-lucide-minimize-2)
            └── FilePreview (flex-1, :file-path="maximizedFile", :embedded="false")
```

**Overlay styles:**
- `absolute inset-0 z-20` — covers the entire message area
- Opaque background using theme's `bg-default`
- Fade transition: 0.15s ease

**Toolbar:**
- Height: ~40px (`h-10`)
- Left: file icon (language-specific) + filename (truncated)
- Right: download link + minimize button (`i-lucide-minimize-2`)
- Bottom border separator (`border-b border-default`)
- Clicking minimize sets `maximizedFile = null`

**Keyboard:**
- Escape key listener on the overlay sets `maximizedFile = null`

## BrowserPanel Changes

**Remove:**
- `isMaximized` ref
- The fullscreen overlay (`Transition name="fade"` with `fixed inset-0 z-50`)
- Maximize state management inside the component

**Modify:**
- Add `maximize` emit: when FilePreview's maximize button is clicked, emit `('maximize', selectedFilePath)` to the page
- Change embedded FilePreview visibility condition: `selectedFilePath && maximizedFile !== selectedFilePath`
- Add `maximizedFile` prop (or handle via emit) so the panel knows when its current file is maximized

**New props/emits:**
- Prop: `maximizedFile: string | null` — so the panel knows which file (if any) is maximized
- Emit: `maximize(path: string)` — request maximize for a file
- Emit: `update:maximizedFile` — for v-model pattern with the page

**Panel close behavior:**
- When `open` transitions to `false`, the panel resets `currentPath`, `selectedFilePath`, `panelWidth`
- The page watches `panelOpen` and sets `maximizedFile = null` when it becomes `false`

## Data Flow

```
chat/[id].vue
  ├── panelOpen (ref<boolean>)
  ├── maximizedFile (ref<string | null>)
  │
  ├── UContainer (message area)
  │     ├── UChatMessages
  │     ├── UChatPrompt
  │     └── [overlay: FilePreview when maximizedFile !== null]
  │
  └── BrowserPanel
        ├── v-model:open="panelOpen"
        ├── :maximized-file="maximizedFile"
        ├── @maximize="maximizedFile = $event"
        │
        └── FilePreview (embedded, hidden when file is maximized)
              └── @maximize → emit('maximize', selectedFilePath)
```

## File Switching While Maximized

1. User maximizes file A → `maximizedFile = 'A'` → overlay shows file A, panel preview hidden
2. User clicks file B in FileList → `selectedFilePath = 'B'` in panel
3. Page watches `selectedFilePath` change (via emit) or BrowserPanel emits `maximize('B')` → `maximizedFile = 'B'` → overlay updates to file B
4. User clicks minimize → `maximizedFile = null` → overlay disappears, panel preview shows file B

The key insight: when the panel emits `selectFile` and `maximizedFile` is not null, the page should automatically update `maximizedFile` to the new file path, keeping the maximize state.

## Error Handling

- If file fetch fails in the maximized preview, show the same error state as FilePreview (alert icon + "加载失败" + retry button)
- If `maximizedFile` path becomes invalid, the FilePreview component handles it with its existing error UI

## No Additional Tests Required

This is a UI layout change. Manual testing covers:
1. Maximize from panel → overlay appears in message area
2. Switch files while maximized → overlay updates, stays maximized
3. Minimize → overlay disappears, panel preview shows current file
4. Close panel → overlay disappears
5. Escape key → overlay disappears
6. Light/dark mode → overlay background matches theme
