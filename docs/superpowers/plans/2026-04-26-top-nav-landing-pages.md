# Top Navigation Bar & Landing Pages Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a global top navigation bar with three entries (Home, CLI, Chat) and create landing pages for Home and CLI, while preserving the existing chat functionality.

**Architecture:** Dual layout system — a `landing` layout for marketing pages (Home, CLI) using UHeader/UMain/UFooter, and a modified `default` layout for chat pages adding UHeader above the existing DashboardGroup with sidebar.

**Tech Stack:** Nuxt 4, @nuxt/ui v4 (UHeader, UNavigationMenu, UPageHero, UPageSection, UPageCTA, UFooter), Tailwind CSS

---

### Task 1: Create landing layout

**Files:**
- Create: `app/layouts/landing.vue`

This layout provides the shell for landing pages: top nav bar + main content area + footer. Uses `UHeader` with navigation, `UMain` for page content, and `UFooter` for the bottom.

- [ ] **Step 1: Create `app/layouts/landing.vue`**

```vue
<script setup lang="ts">
import type { NavigationMenuItem } from '@nuxt/ui'

const items = computed<NavigationMenuItem[]>(() => [
  { label: '首页', to: '/home', icon: 'i-lucide-home' },
  { label: '命令行', to: '/cli', icon: 'i-lucide-terminal' },
  { label: '会话', to: '/chat', icon: 'i-lucide-messages-square' }
])
</script>

<template>
  <UHeader to="/home">
    <template #title>
      <Logo class="h-6 w-auto" />
    </template>

    <UNavigationMenu :items="items" />

    <template #right>
      <UColorModeButton />
    </template>

    <template #body>
      <UNavigationMenu :items="items" orientation="vertical" class="-mx-2.5" />
    </template>
  </UHeader>

  <UMain>
    <NuxtPage />
  </UMain>

  <UFooter>
    <template #left>
      <p class="text-muted text-sm">Copyright &copy; {{ new Date().getFullYear() }} BuildMate</p>
    </template>
  </UFooter>
</template>
```

- [ ] **Step 2: Verify the layout loads without errors**

Run: `npx nuxi typecheck --preset=node-server 2>&1 | head -20`
Expected: No errors related to `landing.vue`

---

### Task 2: Create home landing page

**Files:**
- Create: `app/pages/home.vue`

The home page uses Nuxt UI landing page components: a hero section, a features grid, and a call-to-action. Content is placeholder text the user will customize later.

- [ ] **Step 1: Create `app/pages/home.vue`**

```vue
<script setup lang="ts">
definePageMeta({
  layout: 'landing'
})
</script>

<template>
  <UPageHero
    title="BuildMate"
    description="AI 驱动的智能构建助手，让构建管理更高效、更智能"
    :links="[
      { label: '开始使用', to: '/chat', icon: 'i-lucide-square-play' },
      { label: '了解更多', color: 'neutral', variant: 'subtle', trailingIcon: 'i-lucide-arrow-right' }
    ]"
  />

  <UPageSection
    id="features"
    headline="功能特性"
    title="强大功能，开箱即用"
    description="BuildMate 提供全方位的智能构建管理能力，帮助你专注于代码本身。"
    :features="[
      { title: '智能构建分析', description: '自动检测并诊断构建错误，提供精准的修复建议。', icon: 'i-lucide-zap' },
      { title: '代码审查', description: '深度分析代码质量，发现潜在问题并提供优化方案。', icon: 'i-lucide-search-code' },
      { title: '状态监控', description: '实时追踪构建状态，第一时间获取构建结果通知。', icon: 'i-lucide-activity' },
      { title: '多项目管理', description: '统一管理多个项目的构建流程，提升团队协作效率。', icon: 'i-lucide-folder-kanban' },
      { title: 'CLI 工具', description: '强大的命令行工具，支持 CI/CD 集成和自动化工作流。', icon: 'i-lucide-terminal' },
      { title: 'AI 对话', description: '通过自然语言与 AI 交互，快速解决构建问题。', icon: 'i-lucide-message-square' }
    ]"
  />

  <UPageCTA
    title="开始使用 BuildMate"
    description="立即体验 AI 驱动的智能构建管理，让你的开发工作流更上一层楼。"
    :links="[
      { label: '开始对话', to: '/chat', icon: 'i-lucide-square-play' },
      { label: 'CLI 工具', to: '/cli', color: 'neutral', variant: 'subtle', trailingIcon: 'i-lucide-arrow-right' }
    ]"
    class="rounded-none"
  />
</template>
```

- [ ] **Step 2: Verify `/home` renders the landing page**

Run: `npx nuxi typecheck --preset=node-server 2>&1 | head -20`
Expected: No errors related to `home.vue`

---

### Task 3: Create CLI landing page

**Files:**
- Create: `app/pages/cli.vue`

The CLI page showcases the command-line tool with a hero, feature highlights, and a terminal-style installation section.

- [ ] **Step 1: Create `app/pages/cli.vue`**

```vue
<script setup lang="ts">
definePageMeta({
  layout: 'landing'
})
</script>

<template>
  <UPageHero
    title="BuildMate CLI"
    description="强大的命令行工具，将 AI 智能构建能力带入你的终端"
    :links="[
      { label: '查看文档', color: 'neutral', variant: 'subtle', trailingIcon: 'i-lucide-arrow-right' }
    ]"
  >
    <div class="bg-elevated rounded-lg p-4 font-mono text-sm text-muted border border-default">
      <div class="text-toned">$ npm install -g buildmate-cli</div>
      <div class="text-toned mt-1">$ buildmate init</div>
      <div class="mt-1 text-primary">✓ BuildMate CLI initialized successfully</div>
      <div class="text-toned mt-1">$ buildmate analyze</div>
      <div class="mt-1 text-primary">✓ Found 3 issues, 2 auto-fixable</div>
    </div>
  </UPageHero>

  <UPageSection
    id="features"
    headline="CLI 特性"
    title="终端中的智能构建助手"
    description="BuildMate CLI 让你在命令行中享受完整的 AI 构建管理能力。"
    :features="[
      { title: '快速分析', description: '一键分析项目构建状态，快速定位问题根源。', icon: 'i-lucide-gauge' },
      { title: '自动修复', description: '智能检测并自动修复常见构建错误，减少手动干预。', icon: 'i-lucide-wrench' },
      { title: 'CI/CD 集成', description: '无缝集成到现有 CI/CD 流水线，构建守护自动化。', icon: 'i-lucide-git-merge' },
      { title: '实时通知', description: '构建状态变更即时推送，第一时间掌握构建动态。', icon: 'i-lucide-bell' },
      { title: '多语言支持', description: '支持 Java、Python、Go、Node.js 等主流构建生态。', icon: 'i-lucide-languages' },
      { title: '脚本化工作流', description: '通过脚本编排复杂构建流程，实现自动化运维。', icon: 'i-lucide-file-code' }
    ]"
  />

  <UPageCTA
    title="立即开始使用 BuildMate CLI"
    description="将 AI 构建能力集成到你的工作流中，提升团队开发效率。"
    :links="[
      { label: '开始对话', to: '/chat', icon: 'i-lucide-square-play' },
      { label: '返回首页', to: '/home', color: 'neutral', variant: 'subtle', trailingIcon: 'i-lucide-arrow-right' }
    ]"
    class="rounded-none"
  />
</template>
```

- [ ] **Step 2: Verify `/cli` renders the CLI landing page**

Run: `npx nuxi typecheck --preset=node-server 2>&1 | head -20`
Expected: No errors related to `cli.vue`

---

### Task 4: Create chat home page at `/chat`

**Files:**
- Create: `app/pages/chat/index.vue`

Copy the content from the current `app/pages/index.vue` and adapt it: remove `Navbar` from the header slot, and update the shortcut `c` to navigate to `/chat` (already correct for this page since it IS `/chat`).

- [ ] **Step 1: Create `app/pages/chat/index.vue`**

```vue
<script setup lang="ts">
const input = ref('')
const loading = ref(false)
const { user } = useUserSession()

const greeting = computed(() => {
  const hour = new Date().getHours()
  let timeGreeting = '晚上好'
  if (hour < 12) timeGreeting = '早上好'
  else if (hour < 18) timeGreeting = '下午好'

  const name = user.value?.name?.split(' ')[0] || user.value?.username

  return name ? `${timeGreeting}, ${name}` : `${timeGreeting}`
})

const { csrf, headerName } = useCsrf()

async function createQuickChat(prompt: string) {
  input.value = prompt
}

async function createChat(prompt: string) {
  input.value = prompt
  loading.value = true

  const result = await $fetch<{ chat_id: string; message_id: string }>('/api/v1/agent/chats', {
    method: 'POST',
    headers: { [headerName]: csrf },
    body: {
      prompt: prompt,
    }
  })

  refreshNuxtData('chats')
  navigateTo(`/chat/${result.chat_id}`)
}

async function onSubmit() {
  await createChat(input.value)
}

const quickChats = [
  {
    label: '查询构建状态',
    icon: 'i-lucide-check-circle'
  },
  {
    label: '修复构建编译错误',
    icon: 'i-lucide-bug'
  },
  {
    label: '检视代码仓库代码',
    icon: 'i-lucide-code'
  }
]
</script>

<template>
  <UDashboardPanel
    id="home"
    class="min-h-0"
    :ui="{ body: 'p-0 sm:p-0' }"
  >
    <template #body>
      <UContainer class="flex-1 flex flex-col justify-center gap-4 sm:gap-6 py-8">
        <h1 class="text-3xl sm:text-4xl text-highlighted font-bold">
          {{ greeting }}
        </h1>

        <UChatPrompt
          v-model="input"
          :status="loading ? 'streaming' : 'ready'"
          class="[view-transition-name:chat-prompt]"
          variant="subtle"
          :ui="{ base: 'px-1.5' }"
          @submit="onSubmit"
        >
          <template #footer>
            <div class="flex items-center gap-1">
            </div>

            <UChatPromptSubmit color="neutral" size="sm" />
          </template>
        </UChatPrompt>

        <div class="flex flex-wrap gap-2">
          <UButton
            v-for="quickChat in quickChats"
            :key="quickChat.label"
            :icon="quickChat.icon"
            :label="quickChat.label"
            size="sm"
            color="neutral"
            variant="outline"
            class="rounded-full"
            @click="createQuickChat(quickChat.label)"
          />
        </div>
      </UContainer>
    </template>
  </UDashboardPanel>
</template>
```

Note: The `<Navbar />` in `#header` slot is removed. The `#header` template is removed entirely since the UHeader in the layout now handles navigation.

- [ ] **Step 2: Verify no type errors**

Run: `npx nuxi typecheck --preset=node-server 2>&1 | head -20`
Expected: No errors related to `chat/index.vue`

---

### Task 5: Update chat layout with UHeader

**Files:**
- Modify: `app/layouts/default.vue`

Add `UHeader` above the `UDashboardGroup`. Move the sidebar toggle button and color mode button from `Navbar.vue` into the header's `#right` slot. Update internal links (`/` → `/home` for sidebar logo, `/` → `/chat` for new chat button, shortcut `c` → `/chat`).

- [ ] **Step 1: Replace `app/layouts/default.vue`**

```vue
<script setup lang="ts">
import type { NavigationMenuItem } from '@nuxt/ui'

const { loggedIn, openInPopup } = useUserSession()

const open = ref(false)

const { data: chats, refresh: refreshChats } = await useFetch('/api/v1/agent/chats', {
  key: 'chats',
  transform: data => data.map(chat => ({
    id: chat.chat_id,
    label: chat.title || '未命名会话',
    to: `/chat/${chat.chat_id}`,
    icon: 'i-lucide-message-circle',
    createdAt: chat.createdAt
  }))
})

onNuxtReady(async () => {
  const first10 = (chats.value || []).slice(0, 10)
  for (const chat of first10) {
    await $fetch(`/api/v1/agent/chats/${chat.id}`)
  }
})

watch(loggedIn, () => {
  refreshChats()
  open.value = false
})

const { groups } = useChats(chats)

const items = computed(() => groups.value?.flatMap((group) => {
  return [{
    label: group.label,
    type: 'label' as const
  }, ...group.items.map(item => ({
    ...item,
    slot: 'chat' as const,
    icon: undefined,
    class: item.label === '未命名会话' ? 'text-muted' : ''
  }))]
}))

const navItems = computed<NavigationMenuItem[]>(() => [
  { label: '首页', to: '/home', icon: 'i-lucide-home' },
  { label: '命令行', to: '/cli', icon: 'i-lucide-terminal' },
  { label: '会话', to: '/chat', icon: 'i-lucide-messages-square' }
])

defineShortcuts({
  c: () => {
    navigateTo('/chat')
  }
})
</script>

<template>
  <div class="flex flex-col h-screen">
    <UHeader to="/home">
      <template #title>
        <Logo class="h-6 w-auto" />
      </template>

      <UNavigationMenu :items="navItems" />

      <template #right>
        <UDashboardSidebarCollapse />
        <UColorModeButton />
        <UButton
          color="neutral"
          variant="ghost"
          icon="i-lucide-plus"
          to="/chat"
          class="lg:hidden"
          aria-label="新建会话"
        />
      </template>

      <template #body>
        <UNavigationMenu :items="navItems" orientation="vertical" class="-mx-2.5" />
      </template>
    </UHeader>

    <UDashboardGroup unit="rem" class="flex-1 min-h-0">
      <UDashboardSidebar
        id="default"
        v-model:open="open"
        :min-size="12"
        collapsible
        resizable
        class="border-r-0 py-4"
      >
        <template #header="{ collapsed }">
          <NuxtLink to="/home" class="flex items-end gap-0.5">
            <Logo class="h-8 w-auto shrink-0" />
            <span v-if="!collapsed" class="text-xl font-bold text-highlighted">BuildMateChat</span>
          </NuxtLink>
        </template>

        <template #default="{ collapsed }">
          <div class="flex flex-col gap-1.5">
            <UButton
              v-bind="collapsed ? { icon: 'i-lucide-plus' } : { label: '新会话' }"
              variant="soft"
              block
              to="/chat"
              @click="open = false"
            />

            <template v-if="collapsed">
              <UDashboardSearchButton collapsed />
            </template>
          </div>

          <UNavigationMenu
            v-if="!collapsed"
            :items="items"
            :collapsed="collapsed"
            orientation="vertical"
            :ui="{ link: 'overflow-hidden' }"
          />
        </template>

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
      </UDashboardSidebar>

      <div class="flex-1 flex m-4 lg:ml-0 rounded-lg ring ring-default bg-default/75 shadow min-w-0 overflow-hidden">
        <slot />
      </div>
    </UDashboardGroup>
  </div>
</template>
```

Key changes from the original:
1. Wrapped in `<div class="flex flex-col h-screen">` so UHeader + UDashboardGroup stack vertically
2. Added `UHeader` with `UNavigationMenu`, `UDashboardSidebarCollapse`, `UColorModeButton`
3. UDashboardGroup gets `class="flex-1 min-h-0"` to fill remaining height
4. Sidebar logo link changed `/` → `/home`
5. "新会话" button link changed `/` → `/chat`
6. Shortcut `c` changed to navigate to `/chat`
7. Mobile "new chat" button in header links to `/chat`

- [ ] **Step 2: Verify no type errors**

Run: `npx nuxi typecheck --preset=node-server 2>&1 | head -20`
Expected: No errors related to `default.vue`

---

### Task 6: Update chat detail page

**Files:**
- Modify: `app/pages/chat/[id].vue`

Remove the `<Navbar />` from the `#header` slot of `UDashboardPanel`, since the UHeader in the layout now handles navigation.

- [ ] **Step 1: Remove Navbar from `app/pages/chat/[id].vue`**

In `app/pages/chat/[id].vue`, remove the entire `<template #header>` block:

Remove these lines (lines 121-123):
```vue
    <template #header>
      <Navbar />
    </template>
```

The `UDashboardPanel` will now only have the `#body` slot.

- [ ] **Step 2: Verify no type errors**

Run: `npx nuxi typecheck --preset=node-server 2>&1 | head -20`
Expected: No errors related to `chat/[id].vue`

---

### Task 7: Replace root page with redirect

**Files:**
- Modify: `app/pages/index.vue`

Replace the entire content with a redirect to `/home`. This ensures `/` redirects users to the new home landing page.

- [ ] **Step 1: Replace `app/pages/index.vue`**

```vue
<script setup lang="ts">
definePageMeta({
  layout: 'landing'
})

navigateTo('/home', { redirectCode: 301, replace: true })
</script>

<template>
  <div />
</template>
```

- [ ] **Step 2: Verify `/` redirects to `/home`**

Run: `npx nuxi typecheck --preset=node-server 2>&1 | head -20`
Expected: No errors

---

### Task 8: Update UserMenu logout redirect

**Files:**
- Modify: `app/components/UserMenu.vue`

Update the logout navigation from `/` to `/home`.

- [ ] **Step 1: Update logout redirect in `app/components/UserMenu.vue`**

In `app/components/UserMenu.vue`, find this line (line 98):

```ts
    navigateTo('/')
```

Replace with:

```ts
    navigateTo('/home')
```

- [ ] **Step 2: Verify no type errors**

Run: `npx nuxi typecheck --preset=node-server 2>&1 | head -20`
Expected: No errors related to `UserMenu.vue`

---

### Task 9: Delete Navbar component and commit

**Files:**
- Delete: `app/components/Navbar.vue`

The `Navbar.vue` component is no longer used — its responsibilities (sidebar toggle, color mode button) have been moved to the UHeader in the chat layout.

- [ ] **Step 1: Verify Navbar.vue is not imported anywhere**

Run: `grep -r "Navbar" app/ --include="*.vue" --include="*.ts"`
Expected: No results (all references have been removed in previous tasks)

- [ ] **Step 2: Delete the file**

```bash
rm app/components/Navbar.vue
```

- [ ] **Step 3: Run type check**

Run: `npx nuxi typecheck --preset=node-server 2>&1 | head -20`
Expected: No errors

- [ ] **Step 4: Commit all changes**

```bash
git add app/layouts/landing.vue app/pages/home.vue app/pages/cli.vue app/pages/chat/index.vue app/layouts/default.vue app/pages/chat/[id].vue app/pages/index.vue app/components/UserMenu.vue
git rm app/components/Navbar.vue
git commit -m "feat: add top navigation bar with Home, CLI, Chat entries and landing pages

- Add landing layout with UHeader, UMain, UFooter
- Create /home landing page with hero, features, CTA
- Create /cli landing page with terminal mockup and features
- Move chat home from / to /chat
- Add UHeader to chat layout with nav menu and sidebar toggle
- Redirect / to /home
- Remove Navbar.vue (role moved to UHeader)"
```

---

### Task 10: Manual smoke test

- [ ] **Step 1: Start dev server**

```bash
npx nuxi dev
```

- [ ] **Step 2: Verify all routes**

Check each route in the browser:
- `/` → should redirect to `/home`
- `/home` → should show landing page with top nav, hero, features, CTA, footer
- `/cli` → should show CLI landing page with terminal mockup
- `/chat` → should show chat home with sidebar, greeting, prompt input (no double nav)
- `/chat/:id` (any existing chat ID) → should show chat messages (no double nav)

- [ ] **Step 3: Verify navigation**

- Click "首页" in top nav → goes to `/home`
- Click "命令行" in top nav → goes to `/cli`
- Click "会话" in top nav → goes to `/chat`
- Active page is highlighted in the nav
- Color mode toggle works in both layouts
- Sidebar toggle works on chat pages
- Mobile hamburger menu shows vertical nav
