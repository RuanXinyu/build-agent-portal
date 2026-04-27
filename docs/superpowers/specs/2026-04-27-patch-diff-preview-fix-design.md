# Patch/Diff File Preview Fix

## Problem

When previewing `.patch` or `.diff` files in the file browser, the side-by-side diff editor shows an empty left pane and the entire patch text in the right pane. This is because `original` is hardcoded to `''` and `modified` receives the raw patch content, making every line appear as an "addition."

Root cause: `FilePreview.vue:292-293` passes `original=""` and `modified=data.content` to `VueMonacoDiffEditor`.

## Solution

Install `parse-diff` to parse unified diff format, extract original (context + deleted lines) and modified (context + added lines) content, and pass both to the existing `VueMonacoDiffEditor`.

## Design

### 1. New dependency: `parse-diff`

Lightweight (~600B gzipped) library that parses unified diff strings into structured JSON with typed changes per chunk (`add`, `del`, `normal`).

### 2. `parsePatchContent(content: string)` utility function

Input: raw unified diff text.
Output: `{ original: string, modified: string }`.

Algorithm:
- Call `parseDiff(content)` to get structured data
- For each file's chunks, iterate changes:
  - `normal`: append line content to both original and modified
  - `del`: append line content to original only
  - `add`: append line content to modified only
- Join lines with newlines

### 3. `diffData` computed property

When `isDiff && data.content`, call `parsePatchContent(data.content)` and cache the result. Returns `{ original: '', modified: '' }` when not applicable.

### 4. `diffMode` reactive state

- Type: `'side-by-side'` | `'inline'`
- Default: `'side-by-side'`
- User can toggle via button in action bar (only visible when `isDiff`)
- Maps to Monaco's `renderSideBySide` option

### 5. Updated DiffEditor bindings

- `:original="diffData.original"` (was `''`)
- `:modified="diffData.modified"` (was `data.content`)
- `:options="{ renderSideBySide: diffMode === 'side-by-side', ... }"`

### 6. Toggle button in action bar

When `isDiff`, show a button with:
- `i-lucide-columns` icon when in side-by-side mode
- `i-lucide-align-left` icon when in inline mode
- Tooltip: "切换对比模式"
- Click toggles `diffMode`

## Files changed

| File | Change |
|------|--------|
| `package.json` | Add `parse-diff` dependency |
| `app/components/file/FilePreview.vue` | Add import, `parsePatchContent()`, `diffData` computed, `diffMode` ref, update template |

## Edge cases

- Multi-file patches: concatenate all hunks across files into one original/modified pair
- Empty patch: `parseDiff` returns empty array, both sides will be empty strings
- Malformed diff: `parse-diff` handles gracefully, returns what it can parse
