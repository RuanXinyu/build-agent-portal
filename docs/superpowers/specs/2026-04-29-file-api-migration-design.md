# File API Migration Design

Migrate file browser APIs from flat `/api/v1/files` routes to chat-scoped `/api/v1/agent/chats/[id]/files` routes, aligning with the updated Flask backend URL structure and nested tree data format.

## Background

The Python Flask backend (`app.py`) has been updated:
- File API URLs changed from `/api/files` to `/buildagent/v1/agent/chats/<chat_id>/workspace/output/files` (and `/content`, `/download` suffixes)
- `list_files` now supports `recursive` and `depth` parameters, returns nested tree structure by default
- `content` endpoint wraps response in `{ data: {...}, error?: string }` format
- File content is base64-encoded
- Paths no longer use `~` prefix

## Changes

### 1. Python: `file_mock_data.py`

**`list_directory(path)` returns nested tree:**
```json
{
  "data": {
    "files": [
      {
        "filename": "src",
        "type": "dir",
        "files": [
          {
            "filename": "App.vue",
            "type": "file",
            "size": 890
          },
          {
            "filename": "components",
            "type": "dir",
            "files": [...]
          }
        ]
      }
    ]
  }
}
```

- `filename` instead of `name`
- `type` is `"dir"` or `"file"` (not `"directory"`)
- Directories have nested `files` array
- Files have `size` field
- No `path`, `language`, or `~` prefixes in any path

**`get_file_content(path)` returns:**
```json
{
  "data": {
    "name": "auth.ts",
    "size": 1234,
    "content": "<base64-encoded-string>"
  }
}
```

- Only `name`, `size`, `content` fields
- `content` is base64-encoded
- No `language`, `downloadUrl`, `previewable` fields

### 2. Python: `app.py`

**`list_files` endpoint:**
- Path: `/buildagent/v1/agent/chats/<chat_id>/workspace/output/files`
- Query params: `filepath`, `recursive` (default `"true"`), `depth` (default `"2"`)
- Response: `{ "data": { "files": [...] } }`
- `filepath` defaults to `/` for root directory (no `~`)
- Paths do not contain `~`

**`get_file_content` endpoint:**
- Path: `/buildagent/v1/agent/chats/<chat_id>/workspace/output/files/content`
- Query params: `filepath`
- Response: `{ "data": { "name", "size", "content" }, "error": "" }`
- Check `error` field first; if non-empty, return error

**`download_file` endpoint:**
- Path: `/buildagent/v1/agent/chats/<chat_id>/workspace/output/files/download`
- Query params: `filepath`
- Returns binary file

### 3. Nuxt Server API

**Delete old routes:**
- `server/api/v1/files.get.ts`
- `server/api/v1/files/content.get.ts`
- `server/api/v1/files/download.get.ts`

**New route: `server/api/v1/agent/chats/[id]/files.get.ts`**
- Extract `id` from route params as `chatId`
- Proxy to Flask: `/buildagent/v1/agent/chats/{chatId}/workspace/output/files`
- Pass query params: `filepath`, `recursive=true`, `depth=2`
- Pass through the nested tree response as-is

**New route: `server/api/v1/agent/chats/[id]/files/content.get.ts`**
- Extract `id` from route params as `chatId`
- Proxy to Flask: `/buildagent/v1/agent/chats/{chatId}/workspace/output/files/content`
- Receive: `{ data: { name, size, content(base64) }, error?: string }`
- If `error` is non-empty, throw 400 with error message
- Decode `content` from base64
- Compute `language` from filename (use existing extension-to-language map)
- Compute `previewable` from filename extension
- Return to frontend: `{ name, language, size, content, previewable }`

**New route: `server/api/v1/agent/chats/[id]/files/download.get.ts`**
- Extract `id` from route params as `chatId`
- Proxy to Flask: `/buildagent/v1/agent/chats/{chatId}/workspace/output/files/download`
- Pass `filepath` query param
- Set `content-type: application/octet-stream` and `content-disposition: attachment` headers

### 4. Frontend: `FileList.vue`

**New props:**
- `chatId: string` (required)

**Data fetching:**
- Single call: `GET /api/v1/agent/chats/{chatId}/files?filepath=/`
- Stores complete tree in `treeData` ref
- No re-fetching on directory navigation

**Local filtering:**
- `currentPath` starts at `/` (root)
- On navigation, find the corresponding node in the tree by path segments
- Extract `files` array from that node as the display list
- Map `filename` -> `name`, `type` ("dir"|"file") -> display type
- Compute `path` for each entry relative to current directory

**Breadcrumb:**
- Root shows home icon, no `~` prefix
- Segments split from `currentPath` (e.g., `/src/components` -> ["src", "components"])

### 5. Frontend: `FilePreview.vue`

**New props:**
- `chatId: string` (required)

**Data fetching:**
- URL: `GET /api/v1/agent/chats/{chatId}/files/content?path={filePath}`
- Response format unchanged from frontend perspective: `{ name, language, size, content, previewable }`
- Error handling: server-side already converts Flask `error` field to HTTP error, frontend handles via catch

**Download URL:**
- Changed to `/api/v1/agent/chats/{chatId}/files/download?path={filePath}`

### 6. Frontend: `BrowserPanel.vue`

**New props:**
- `chatId: string` (required)

**Changes:**
- `currentPath` initial value: `'/'` instead of `'~'`
- Pass `chatId` to `FileList` and `FilePreview`
- Reset `currentPath` to `'/'` on panel open

### 7. Frontend: `chat/[id].vue`

**Changes:**
- Pass `route.params.id` as `chatId` prop to `FileBrowserPanel`

## File Change Summary

| File | Action |
|------|--------|
| `scripts/python/server/file_mock_data.py` | Modify: nested tree return, base64 content |
| `scripts/python/server/app.py` | Modify: new URLs, new response format |
| `server/api/v1/files.get.ts` | Delete |
| `server/api/v1/files/content.get.ts` | Delete |
| `server/api/v1/files/download.get.ts` | Delete |
| `server/api/v1/agent/chats/[id]/files.get.ts` | Create |
| `server/api/v1/agent/chats/[id]/files/content.get.ts` | Create |
| `server/api/v1/agent/chats/[id]/files/download.get.ts` | Create |
| `app/components/file/FileList.vue` | Modify: chatId prop, tree data, local filter |
| `app/components/file/FilePreview.vue` | Modify: chatId prop, new URL |
| `app/components/file/BrowserPanel.vue` | Modify: chatId prop, path `/` |
| `app/pages/chat/[id].vue` | Modify: pass chatId |
