# Move Login/UserMenu to Navigation Bar Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move the login button and UserMenu from chat.vue's sidebar footer to AppHeader.vue's right area, making auth UI visible on all pages.

**Architecture:** Move `useUserSession()` logic and the conditional rendering (UserMenu vs login button) into AppHeader.vue. Remove the sidebar `#footer` template from chat.vue.

**Tech Stack:** Nuxt 4, Nuxt UI v4, Vue 3 Composition API

---

### Task 1: Add login/user UI to AppHeader.vue

**Files:**
- Modify: `app/components/AppHeader.vue`

- [ ] **Step 1: Add useUserSession to AppHeader script**

In `app/components/AppHeader.vue`, add `useUserSession()` to the `<script setup>` block. The script should become:

```vue
<script setup lang="ts">
import type { NavigationMenuItem } from '@nuxt/ui'

defineProps<{
  sticky?: boolean
}>()

const { loggedIn, openInPopup } = useUserSession()

const navItems = computed<NavigationMenuItem[]>(() => [
  { label: '首页', to: '/home', icon: 'i-lucide-home' },
  { label: '命令行', to: '/cli', icon: 'i-lucide-terminal' },
  { label: '会话', to: '/chat', icon: 'i-lucide-messages-square' }
])
</script>
```

- [ ] **Step 2: Add UserMenu and login button to the #right template**

Replace the `<template #right>` block (lines 32-35) with:

```vue
    <template #right>
      <slot name="right" />
      <UserMenu v-if="loggedIn" />
      <UButton
        v-else
        label="登录"
        icon="i-simple-icons-github"
        color="neutral"
        variant="ghost"
        @click="openInPopup('/auth/github')"
      />
      <UColorModeButton />
    </template>
```

Note: `UserMenu` is called without `collapsed` prop — in the nav bar it always shows the expanded state with username.

- [ ] **Step 3: Verify the dev server compiles without errors**

Run: `pnpm dev` (or check the already-running dev server)
Expected: No compilation errors, nav bar shows login button (if logged out) or UserMenu (if logged in) on all pages.

- [ ] **Step 4: Commit**

```bash
git add app/components/AppHeader.vue
git commit -m "feat: add login button and UserMenu to AppHeader nav bar"
```

---

### Task 2: Remove login/user UI from chat.vue sidebar footer

**Files:**
- Modify: `app/layouts/chat.vue`

- [ ] **Step 1: Remove the #footer template from UDashboardSidebar**

Delete the entire `<template #footer>` block (lines 99-110):

```vue
          <template #footer="{ collapsed }">
            <UserMenu v-if="loggedIn" :collapsed="collapsed" />
            <UButton
              v-else
              :label="collapsed ? '' : '登录'"
              icon="i-simple-icons-github"
              color="neutral"
              variant="ghost"
              class="w-full"
              @click="openInPopup('/auth/github')"
            />
          </template>
```

- [ ] **Step 2: Remove unused destructured values from useUserSession**

In `chat.vue` line 2, `openInPopup` is no longer used in this file. Change:

```ts
const { loggedIn, openInPopup } = useUserSession()
```

to:

```ts
const { loggedIn } = useUserSession()
```

(`loggedIn` is still used in the `watch` on line 24.)

- [ ] **Step 3: Verify chat page renders correctly**

Check in browser:
- Chat page sidebar footer should be empty (no UserMenu, no login button)
- Top nav bar should show UserMenu (if logged in) or login button (if logged out)
- Sidebar collapse/expand should still work
- Chat list navigation should still work

- [ ] **Step 4: Commit**

```bash
git add app/layouts/chat.vue
git commit -m "refactor: remove login UI from chat sidebar footer (moved to AppHeader)"
```

---

### Task 3: Smoke test across all pages

**Files:** None (verification only)

- [ ] **Step 1: Verify on home page (`/home`)**

- Nav bar shows login button or UserMenu on the right side
- UColorModeButton still visible
- Page content renders normally

- [ ] **Step 2: Verify on CLI page (`/cli`)**

- Same nav bar behavior as home page
- Page content renders normally

- [ ] **Step 3: Verify on chat home (`/chat`)**

- Nav bar shows login button or UserMenu
- Sidebar shows chat list, no footer user section
- New chat button still works

- [ ] **Step 4: Verify on chat detail (`/chat/:id`)**

- Nav bar shows login button or UserMenu
- Sidebar shows chat list
- Chat content renders normally
