# FilePreview Enhancement Design

## Goal

Upgrade the FilePreview component to use Monaco Editor for code/text files, Monaco Diff Editor for patch files, and @comark/nuxt for Markdown. Fix the embedded mode action bar being hidden, and ensure non-previewable files show proper UI.

## Context

The file browser panel (BrowserPanel) is working. When a file is selected, FilePreview loads inside the panel with `embedded=true`. Current issues:

- Action bar (download + maximize icons) is hidden when `embedded=true`
- Code files render as plain text with no syntax highlighting
- Non-previewable files may not show proper indication
- No diff/patch file support

## Architecture

Single component modification: `app/components/file/FilePreview.vue`

Rendering strategy by file type:

| File Type | Renderer | Trigger |
|-----------|----------|---------|
| Code/Text | Monaco Editor (read-only) | `data.previewable && !isMarkdown && !isDiff` |
| Markdown | @comark/nuxt (ChatComark) | `data.language === 'markdown'` |
| Patch/Diff | Monaco Diff Editor | File extension `.patch` / `.diff` or language `diff` |
| Non-previewable | Icon + message + download button | `!data.previewable` |

## Component Changes

### FilePreview.vue

**Action bar:** Always visible, but compact in embedded mode.

- Full mode (`embedded=false`): filename, language badge, line count, download button, maximize button
- Embedded mode (`embedded=true`): filename, download button, maximize button

**Code/Text rendering:** Replace plain text `<table>` with `VueMonacoEditor`:

- `readOnly: true`
- `minimap: { enabled: false }`
- `lineNumbers: 'on'`
- `scrollBeyondLastLine: false`
- `renderLineHighlight: 'none'`
- Language mapping: API returns `language` field (e.g., `typescript`), map to Monaco language ID
- Height: `flex-1` to fill available space

**Markdown rendering:** Keep existing `ChatComark` component, no changes.

**Diff/Patch rendering:** Use `VueMonacoDiffEditor`:

- Original: empty string, Modified: file content
- `readOnly: true`
- `renderSideBySide: true`

**Non-previewable rendering:** Keep existing UI (icon + message + download button), ensure action bar still shows download link.

### Language Mapping

Map API `language` field to Monaco language IDs. Common mappings:

```
typescript → typescript
javascript → javascript
python → python
java → java
c → c
cpp → cpp
go → go
rust → rust
ruby → ruby
php → php
vue → html
html → html
css → css
scss → scss
less → less
shell → shell
bash → shell
json → json
yaml → yaml
toml → toml
xml → xml
sql → sql
dockerfile → dockerfile
markdown → markdown
diff → diff
graphql → graphql
plain_text → plaintext
```

Fallback: `plaintext` for unknown languages.

### Diff Detection

Detect diff/patch files by:

1. File extension: `.patch`, `.diff`
2. Language field: `diff`

## Dependencies

Add one package:

```
pnpm add @guolao/vue-monaco-editor
```

No other new dependencies. @comark/nuxt already installed for Markdown rendering.

## Data Fetching

Keep `$fetch` approach. The component naming issue was the root cause of the previous bug, not `$fetch`. These components are client-only (inside `<Transition>` + `v-if`), so `$fetch` is simpler and more reliable than `useFetch`.

## Error Handling

- Loading state: spinner
- Fetch error: error icon + retry button
- Monaco load error: fallback to plain text `<pre>` display
- Non-previewable: icon + "无法预览此文件" message + download button
