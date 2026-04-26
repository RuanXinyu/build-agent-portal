# File Browser Panel Design

## Overview

Add a file browser panel to the chat detail page. A folder icon in the navbar toggles a resizable right-side panel that displays an Agent's working directory file tree with file content preview.

## API Design

### Flask Mock API (3 new endpoints)

#### `GET /api/files?path=~`

List directory contents.

- `path` (query): directory path, `~` = project root (default)
- Response:

```json
{
  "entries": [
    { "name": "src", "path": "~/src", "type": "directory" },
    { "name": "auth.ts", "path": "~/src/auth.ts", "type": "file", "size": 1234, "language": "typescript" }
  ]
}
```

Frontend builds breadcrumbs by splitting the `path` parameter on `/`.

#### `GET /api/files/content?path=~/src/auth.ts`

Get file content for preview.

- `path` (query): file path
- Response (previewable):

```json
{
  "name": "auth.ts",
  "language": "typescript",
  "size": 1234,
  "content": "import { createHash } from 'crypto'\n...",
  "previewable": true
}
```

- Response (not previewable):

```json
{
  "name": "data.sqlite",
  "language": null,
  "size": 204800,
  "content": null,
  "previewable": false,
  "downloadUrl": "/api/files/download?path=~/assets/data.sqlite"
}
```

Files over 1MB are marked `previewable: false`.

#### `GET /api/files/download?path=~/assets/data.sqlite`

Download file as binary stream with `Content-Disposition: attachment`.

### Nuxt Server Routes (BFF proxy)

- `server/api/v1/files.get.ts` — proxies directory listing to Flask
- `server/api/v1/files/content.get.ts` — proxies file content to Flask
- `server/api/v1/files/download.get.ts` — proxies file download to Flask

### Path Security

Backend validates `path` parameter: rejects `..` segments that would escape the project root.

## Frontend Architecture

### New Components

```
app/components/file/
├── BrowserPanel.vue    # Right-side resizable panel container
├── FileList.vue        # Directory listing + breadcrumb navigation
└── FilePreview.vue     # File content preview area
```

#### BrowserPanel.vue

- Props: `open` (boolean) — controls panel visibility
- Contains a draggable divider on its left edge (mousedown/mousemove/mouseup)
- Width constraints: min 280px, max 60% viewport width
- Default width: 380px (resets on each open, not persisted)
- Internal layout: FileList (top) + FilePreview (bottom, flexible height)

#### FileList.vue

- Calls `GET /api/v1/files?path=xxx` to load directory entries
- Breadcrumb: splits current path on `/`, each segment clickable to navigate
- Root breadcrumb: `~` icon for project root
- Directory entries: folder icon + name, click navigates into subdirectory
- File entries: file icon + name + size, click triggers preview
- Active file highlighted with left border accent
- Entries sorted: directories first, then files, both alphabetically

#### FilePreview.vue

- Calls `GET /api/v1/files/content?path=xxx` to load file content
- Action bar: filename + language tag + download button (⬇) + maximize button (⤢, previewable only)
- Previewable files:
  - Code files → Shiki syntax highlighting (project has `@comark/nuxt` + `shiki`)
  - Markdown → rendered to HTML via `@comark/nuxt`
  - Plain text → monospace font with line numbers
- Non-previewable files: centered message "无法预览此文件" + file type description + download button
- Maximize mode: full-screen overlay covering chat area (z-index stacking), dark header bar with file info, download/close buttons, Esc to exit

### Modified Files

- **`app/components/Navbar.vue`** — add `i-lucide-folder-open` icon button in `#right` slot, emits toggle event
- **`app/pages/chat/[id].vue`** — import BrowserPanel, manage `panelOpen` state, wrap chat content + panel in horizontal flex layout

### Data Flow

```
User clicks 📂 in Navbar
  → chat/[id].vue sets panelOpen = true
  → BrowserPanel renders, FileList fetches root directory
  → User clicks directory → FileList fetches subdirectory, updates breadcrumb
  → User clicks file → FilePreview fetches file content
  → User clicks maximize → FilePreview enters fullscreen mode
```

## Error Handling

- **Directory not found**: API returns 404, FileList shows "该目录不存在" empty state
- **File not found**: API returns 404, FilePreview shows "文件未找到" with back-to-list button
- **Network error**: generic error message with retry button
- **Loading state**: FileList and FilePreview each manage their own loading state with skeleton/spinner

## Edge Cases

- Empty directory: shows "此目录为空" empty state
- Large files (>1MB): backend marks as non-previewable, frontend shows download-only UI
- Path traversal: backend rejects paths escaping project root
- Breadcrumb click: navigates to any ancestor directory
- File list sorting: directories first, then files, alphabetical within each group
- Panel width: resets to default on each open (not persisted across toggles)
