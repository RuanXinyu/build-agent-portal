# Chat File Layout Optimization

**Date:** 2026-04-27
**Status:** Approved

## Problem

The chat detail page (`app/pages/chat/[id].vue`) uses a `UDashboardNavbar` occupying a full row at the top solely to host a folder toggle icon. This wastes vertical space and adds unnecessary visual weight. Additionally, the scroll behavior needs improvement: the page scroll should target the message area exclusively, while the `FileBrowserPanel` scrolls independently.

## Design Decisions

### 1. Remove UDashboardNavbar, use floating icon

- Delete the `#header` slot and `UDashboardNavbar` entirely
- Move the folder toggle `UButton` inside the `UContainer` (message area) as an absolutely positioned element at `top-3 right-3`
- Button retains current styling: `size="sm"`, `ghost` variant (closed) / `soft` variant + `primary` color (open)
- `z-10` ensures the button stays above message content
- The icon does not obstruct messages since chat content typically occupies the left/center of the container

### 2. Message area handles its own scrolling

- `UContainer` (message area wrapper) gets `overflow-hidden`
- `UChatMessages` with `should-auto-scroll` controls scrolling internally
- Remove `pt-(--ui-header-height)` since there is no longer a navbar to offset
- Keep `pb-4 sm:pb-6` bottom padding

### 3. FileBrowserPanel unchanged

- `FileBrowserPanel` remains a right-side sliding panel with its own internal scrolling
- Layout stays flex horizontal: message area (`flex-1`) + `FileBrowserPanel` side by side
- No changes to `BrowserPanel.vue` or `FilePreview.vue`

## Scope

| File | Change |
|------|--------|
| `app/pages/chat/[id].vue` | Remove Navbar, restructure template layout, add floating icon |
| `app/components/file/BrowserPanel.vue` | No change |
| `app/components/file/FilePreview.vue` | No change |

## Template Structure (After)

```
UDashboardPanel
  └── #body: div.flex.h-full
        ├── UContainer.flex-1.overflow-hidden.relative
        │     ├── UButton (absolute top-3 right-3 z-10, folder toggle)
        │     ├── UChatMessages (should-auto-scroll, internal scroll)
        │     └── UChatPrompt (sticky bottom)
        └── FileBrowserPanel (sliding right panel)
```

## Acceptance Criteria

1. Folder icon floats at top-right of message area, no navbar row
2. Clicking the icon toggles FileBrowserPanel open/closed
3. Message area scrolls independently via UChatMessages internal scroll
4. FileBrowserPanel scrolls independently
5. No visual regression in message display or prompt positioning
