# Patch Multi-File Card Preview Design

## Problem

When a `.patch` or `.diff` file contains modifications to multiple files, the current implementation concatenates all changes into a single original/modified pair and renders them in one Monaco DiffEditor. This makes it impossible to distinguish which changes belong to which file.

## Solution

Replace Monaco DiffEditor with `diff2html` library for rendering patch/diff files. Each file in the patch gets its own card with a header showing file path and change statistics, and a body showing the diff content. Users can toggle between side-by-side and inline mode globally.

## Architecture

### Rendering Pipeline

```
patch raw text → Diff2Html.parse() → FileResult[]
  → v-for each file → DiffFileCard (header + Diff2Html.generateFromJson())
```

### Changed Files

| File | Change |
|------|--------|
| `app/components/file/FilePreview.vue` | Replace Monaco DiffEditor with diff2html; add v-for rendering of DiffFileCard |
| `app/components/file/DiffFileCard.vue` | **New** - single file diff card component |
| `package.json` | Add `diff2html` dependency; remove `parse-diff` if no longer used elsewhere |

### Unchanged

- `isDiff` computed (detection logic stays the same)
- `diffMode` ref and toggle button (still global control)
- Monaco plain editor (for non-diff code files)
- File content API and fetch logic
- Action bar (download, maximize buttons)
- BrowserPanel, chat page, and all external components

## Component: DiffFileCard

**File:** `app/components/file/DiffFileCard.vue`

**Props:**

| Prop | Type | Description |
|------|------|-------------|
| `fileDiff` | `FileResult` | Single file parsed by diff2html |
| `diffMode` | `'side-by-side' \| 'inline'` | Current global display mode |

**Structure:**

```
┌─────────────────────────────────────────────┐
│ src/components/AppHeader.vue    +12  -5      │  Header: file path + stats
├─────────────────────────────────────────────┤
│                                             │
│  diff2html rendered content                  │  Body: side-by-side or inline
│                                             │
└─────────────────────────────────────────────┘
```

**Header data source:** `FileResult` provides `oldName`, `newName`, `addedLines`, `deletedLines`.

**Diff rendering:** Use `Diff2Html.generateFromJson()` with a single `FileResult`, output HTML string rendered via `v-html`.

## Component: FilePreview Changes

### Remove

- `parse-diff` import and `parsePatchContent()` function
- `VueMonacoDiffEditor` usage in diff rendering path
- `diffData` computed property

### Add

- `import { Diff2Html } from 'diff2html'`
- `parsedFiles` computed: `Diff2Html.parse(data.value.content)` → `FileResult[]`
- `v-for` rendering of `DiffFileCard` components

### Diff Mode Toggle Mapping

- `side-by-side` → diff2html `outputFormat: 'side-by-side'`
- `inline` → diff2html `outputFormat: 'line-by-line'`

Toggle button icons remain unchanged (`i-lucide-columns` / `i-lucide-align-left`).

## Styling and Theming

### diff2html Base Styles

Import in `DiffFileCard.vue`: `import 'diff2html/bundles/css/diff2html.min.css'`

### Dark Mode Adaptation

Use `:deep()` CSS overrides on the `DiffFileCard` root element, conditioned on `$colorMode`. Override:

- Row background colors (green for additions, red for deletions)
- Text color
- Line number color
- Code block background

Match the project's existing dark/light theme palette. No additional theme library.

### Card Spacing

Multiple `DiffFileCard` components separated by `space-y-4`. The overall diff area is scrollable.

## Dependencies

- **Add:** `diff2html` (latest)
- **Remove:** `parse-diff` (if no other usage)

## Design Decisions

1. **diff2html over Monaco DiffEditor** — Native multi-file support, GitHub-like card layout, lighter weight than Monaco for diff viewing.
2. **Global mode toggle** — Simpler UX than per-card toggle; matches user preference.
3. **Vertical stacking** — Matches GitHub PR changes page pattern; natural scroll experience.
4. **Full file path in header** — Avoids ambiguity when multiple files share the same name.
5. **CSS override for theming** — Avoids extra dependencies; maintains consistency with existing UI.
