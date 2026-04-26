# Top Navigation Bar & Landing Pages Design

## Overview

Add a global top navigation bar to BuildMate with three entries (Home, CLI, Chat), and create landing pages for Home and CLI. The existing chat functionality is preserved under the Chat navigation entry.

## Architecture: Dual Layout System

### Landing Layout (`layouts/landing.vue`)

Used by `/home` and `/cli` pages. Clean marketing-style layout with no sidebar.

```
UHeader (top nav: logo + 3 menu items + color mode button)
  └── #body slot: mobile vertical nav
UMain
  └── NuxtPage (landing page content)
UFooter
```

**Components:**
- `UHeader` — sticky top navigation bar
  - `#title` slot: Logo component + "BuildMate" text
  - Default slot: `UNavigationMenu` with 3 horizontal items
  - `#right` slot: `UColorModeButton`
  - `#body` slot: `UNavigationMenu` vertical for mobile
- `UMain` — page content container
- `UFooter` — footer with copyright

### Chat Layout (`layouts/default.vue` — modified)

Used by `/chat` and `/chat/:id`. Preserves existing dashboard sidebar layout, adds top navigation above it.

```
UHeader (top nav: logo + 3 menu items + sidebar toggle + color mode button)
UDashboardGroup
  └── UDashboardSidebar (existing chat list)
  └── Content area (page content)
```

**Changes from current `default.vue`:**
- Add `UHeader` above `UDashboardGroup`
- Move sidebar toggle (`UDashboardSidebarCollapse`) from in-page `Navbar.vue` to the `#right` slot of `UHeader`
- Keep all existing sidebar functionality (chat list, user menu, new chat button)

## Routes

| Route | Page File | Layout | Description |
|-------|-----------|--------|-------------|
| `/` | — | — | Redirect to `/home` via `navigateTo` in `pages/index.vue` (kept as redirect-only file) |
| `/home` | `pages/home.vue` | landing | Home landing page |
| `/cli` | `pages/cli.vue` | landing | CLI landing page |
| `/chat` | `pages/chat/index.vue` | default | Chat home (current `pages/index.vue` content) |
| `/chat/:id` | `pages/chat/[id].vue` | default | Chat detail (existing file, unchanged) |

## Navigation Menu Items

```ts
const navItems = computed(() => [
  { label: '首页', to: '/home', icon: 'i-lucide-home' },
  { label: '命令行', to: '/cli', icon: 'i-lucide-terminal' },
  { label: '会话', to: '/chat', icon: 'i-lucide-messages-square' }
])
```

## Landing Pages

### Home Page (`/home`)

Using Nuxt UI landing page components:

1. **UPageHero** — hero section
   - Title: "BuildMate"
   - Description: AI-powered build management assistant
   - Links: "开始使用" → `/chat`, "了解更多" → scrolls down
   - Orientation: `horizontal` (text left, illustration area right)

2. **UPageSection** — features grid (3 columns)
   - 3-4 feature cards with icons, titles, descriptions
   - Placeholder content, user will customize later

3. **UPageCTA** — call to action
   - Title and description
   - Link to `/chat`

### CLI Page (`/cli`)

1. **UPageHero** — hero section
   - Title: "BuildMate CLI"
   - Description: Command-line tool for build management
   - Code block or terminal mockup as visual element

2. **UPageSection** — CLI features
   - Installation instructions
   - Key commands showcase
   - Feature highlights

3. **UPageCTA** — call to action
   - Link to documentation or getting started

## Files to Create

| File | Purpose |
|------|---------|
| `app/layouts/landing.vue` | New landing page layout with UHeader/UMain/UFooter |
| `app/pages/home.vue` | Home landing page |
| `app/pages/cli.vue` | CLI landing page |
| `app/pages/chat/index.vue` | Chat home (moved from `pages/index.vue`) |

## Files to Modify

| File | Changes |
|------|---------|
| `app/layouts/default.vue` | Add UHeader above dashboard, move sidebar toggle and color mode from Navbar to UHeader `#right` slot |
| `app/components/Navbar.vue` | Delete — its role (sidebar toggle, color mode) moves to UHeader in chat layout |
| `app/pages/index.vue` | Replace content with redirect to `/home` using `navigateTo` |

## Component Selection

All components from `@nuxt/ui` v4:

- `UHeader` — top navigation bar with mobile hamburger menu support
- `UNavigationMenu` — horizontal nav items with active state highlighting
- `UPageHero` — landing page hero section with title, description, links
- `UPageSection` — content section with features grid
- `UPageCTA` — call to action block
- `UPageGrid` / `UPageCard` — feature card layout (used inside UPageSection)
- `UFooter` — page footer
- `UMain` — main content wrapper
- `UColorModeButton` — dark/light mode toggle

## Design Constraints

- All colors must use Nuxt UI semantic tokens (`text-default`, `bg-elevated`, etc.)
- Navigation active state highlights current page automatically via `UNavigationMenu` `to` prop
- Mobile responsive: `UHeader` `#body` slot provides hamburger menu with vertical nav
- Landing pages are placeholder content — user will customize text and images later
- Chat layout preserves all existing functionality (sidebar, streaming, message rendering)
