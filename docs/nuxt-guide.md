# Nuxt 3 使用说明文档

> 本文档基于 Nuxt 3.x（Skill 版本 2026.1.28），由 Nuxt Skill + Context7 MCP 生成。
> 涵盖项目创建、目录结构、路由、数据获取、服务端开发、状态管理、渲染模式及部署等核心内容。

---

## 目录

- [1. 快速开始](#1-快速开始)
- [2. 项目目录结构](#2-项目目录结构)
- [3. 配置文件](#3-配置文件)
- [4. 路由系统](#4-路由系统)
- [5. 数据获取](#5-数据获取)
- [6. 自动导入](#6-自动导入)
- [7. 内置组件](#7-内置组件)
- [8. 状态管理](#8-状态管理)
- [9. 服务端开发](#9-服务端开发)
- [10. 渲染模式](#10-渲染模式)
- [11. 部署指南](#11-部署指南)
- [12. CLI 常用命令速查](#12-cli-常用命令速查)

---

## 1. 快速开始

### 创建项目

```bash
# 交互式创建
npx nuxi@latest init my-app

# 指定包管理器
npx nuxi@latest init my-app --packageManager pnpm

# 携带模块初始化
npx nuxi@latest init my-app --modules "@nuxt/ui,@nuxt/image"
```

### 启动开发

```bash
cd my-app
pnpm install
pnpm dev          # 默认 http://localhost:3000
```

### 开发服务器选项

```bash
npx nuxt dev --port 4000        # 自定义端口
npx nuxt dev --host 0.0.0.0    # 局域网访问（移动端调试）
npx nuxt dev --https            # HTTPS 模式
npx nuxt dev --tunnel           # 创建公网隧道
npx nuxt dev --qr               # 显示二维码
```

---

## 2. 项目目录结构

```
my-nuxt-app/
├── app/                       # 应用源码（也可在根目录）
│   ├── app.vue                # 根组件
│   ├── app.config.ts          # 运行时应用配置
│   ├── error.vue              # 错误页面
│   ├── components/            # 自动导入的 Vue 组件
│   ├── composables/           # 自动导入的组合式函数
│   ├── layouts/               # 布局组件
│   ├── middleware/            # 路由中间件
│   ├── pages/                 # 基于文件的路由
│   ├── plugins/               # Vue 插件
│   └── utils/                 # 自动导入的工具函数
├── assets/                    # 构建处理的静态资源（CSS、图片）
├── public/                    # 原样提供的静态资源
├── server/                    # 服务端代码
│   ├── api/                   # API 路由 (/api/*)
│   ├── routes/                # 服务端路由
│   ├── middleware/            # 服务端中间件
│   ├── plugins/               # Nitro 插件
│   └── utils/                 # 服务端工具（自动导入）
├── nuxt.config.ts             # Nuxt 主配置
├── package.json
└── tsconfig.json
```

### 目录说明

| 目录 | 说明 | 自动导入 |
|------|------|---------|
| `components/` | Vue 组件，按名称自动注册 | ✅ |
| `composables/` | 组合式函数（仅顶层文件） | ✅ |
| `utils/` | 工具函数（仅顶层文件） | ✅ |
| `pages/` | 文件路由页面 | - |
| `layouts/` | 布局模板 | - |
| `middleware/` | 路由中间件 | ✅ |
| `plugins/` | 插件（按数字前缀排序） | ✅ |
| `server/utils/` | 服务端工具 | ✅ |
| `public/` | 静态资源，原样输出 | - |
| `assets/` | 需构建处理的资源 | - |

### 文件命名约定

| 模式 | 含义 | 示例 |
|------|------|------|
| `[param]` | 动态路由参数 | `pages/users/[id].vue` |
| `[[param]]` | 可选参数 | `pages/[[lang]].vue` |
| `[...slug]` | 通配路由 | `pages/[...catch].vue` |
| `(group)` | 路由分组（不出现在 URL 中） | `pages/(marketing)/pricing.vue` |
| `.client.vue` | 仅客户端渲染组件 | `Comments.client.vue` |
| `.server.vue` | 仅服务端渲染组件 | `ServerData.server.vue` |
| `.global.ts` | 全局中间件 | `auth.global.ts` |

---

## 3. 配置文件

### nuxt.config.ts（构建时配置）

```ts
export default defineNuxtConfig({
  devtools: { enabled: true },
  modules: ['@nuxt/ui', '@nuxt/image'],

  // 环境覆盖
  $production: {
    routeRules: { '/**': { isr: true } },
  },
  $development: {
    // 开发环境专属配置
  },
  $env: {
    staging: {
      // 预发布环境配置
    },
  },
})
```

### 运行时配置（Runtime Config）

用于需要通过环境变量覆盖的值：

```ts
// nuxt.config.ts
export default defineNuxtConfig({
  runtimeConfig: {
    apiSecret: '123',          // 仅服务端可访问
    public: {
      apiBase: '/api',          // 客户端也可访问
    },
  },
})
```

环境变量覆盖：

```ini
# .env
NUXT_API_SECRET=api_secret_token
NUXT_PUBLIC_API_BASE=https://api.example.com
```

组件中使用：

```vue
<script setup lang="ts">
const config = useRuntimeConfig()
// 服务端: config.apiSecret, config.public.apiBase
// 客户端: config.public.apiBase
</script>
```

### 应用配置（App Config）

用于构建时确定的公开配置（不可通过环境变量覆盖）：

```ts
// app/app.config.ts
export default defineAppConfig({
  title: 'Hello Nuxt',
  theme: { dark: true, colors: { primary: '#ff0000' } },
})
```

```vue
<script setup lang="ts">
const appConfig = useAppConfig()
</script>
```

### runtimeConfig vs app.config

| 特性 | runtimeConfig | app.config |
|------|--------------|------------|
| 客户端传递方式 | 水合（Hydrated） | 打包（Bundled） |
| 环境变量覆盖 | ✅ | ❌ |
| 响应式 | ✅ | ✅ |
| 热更新 | ❌ | ✅ |
| 非原始类型 | ❌ | ✅ |

> **经验法则：** 密钥和环境相关值用 `runtimeConfig`，主题配置和公开 token 用 `app.config`。

---

## 4. 路由系统

Nuxt 基于 `app/pages/` 目录实现文件系统路由，底层使用 vue-router。

### 基础路由映射

```
pages/
├── index.vue           → /
├── about.vue           → /about
├── blog/
│   ├── index.vue       → /blog
│   └── [slug].vue      → /blog/:slug
├── users/
│   └── [id]/
│       └── profile.vue → /users/:id/profile
└── [...slug].vue       → /* (通配)
```

> **注意：** 如果没有 `pages/` 目录，vue-router 不会被引入，适用于单页应用（如只有一个 `app.vue`）。

### 访问路由参数

```vue
<script setup lang="ts">
const route = useRoute()
// /posts/123 → route.params.id = '123'
console.log(route.params.id)
</script>
```

### 页面导航

```vue
<template>
  <!-- 声明式导航（自动预取） -->
  <NuxtLink to="/">首页</NuxtLink>
  <NuxtLink :to="{ name: 'posts-id', params: { id: 1 } }">文章 1</NuxtLink>
</template>

<script setup lang="ts">
// 编程式导航
const router = useRouter()

function goToPost(id: number) {
  navigateTo(`/posts/${id}`)
  // 或
  router.push({ name: 'posts-id', params: { id } })
}
</script>
```

### 路由中间件

**命名中间件：**

```ts
// middleware/auth.ts
export default defineNuxtRouteMiddleware((to, from) => {
  const isAuthenticated = false
  if (!isAuthenticated) {
    return navigateTo('/login')
  }
})
```

在页面中使用：

```vue
<script setup lang="ts">
definePageMeta({
  middleware: 'auth',
  // 多个中间件: middleware: ['auth', 'admin']
})
</script>
```

**全局中间件（`.global.ts` 后缀）：**

```ts
// middleware/logging.global.ts
export default defineNuxtRouteMiddleware((to, from) => {
  console.log('Navigating to:', to.path)
})
```

### 布局系统

```vue
<!-- layouts/default.vue -->
<template>
  <div>
    <TheHeader />
    <slot />
    <TheFooter />
  </div>
</template>
```

```vue
<!-- pages/admin.vue -->
<script setup lang="ts">
definePageMeta({
  layout: 'admin',    // 指定布局
  // layout: false    // 禁用布局
})
</script>
```

动态切换布局：

```vue
<script setup lang="ts">
setPageLayout('admin')
</script>
```

### 路由验证

```vue
<script setup lang="ts">
definePageMeta({
  validate: (route) => {
    return /^\d+$/.test(route.params.id as string)
  },
})
</script>
```

### 导航守卫

```vue
<script setup lang="ts">
onBeforeRouteLeave((to, from) => {
  const answer = window.confirm('确定离开？')
  if (!answer) return false
})
</script>
```

---

## 5. 数据获取

Nuxt 提供三个核心工具用于 SSR 友好的数据获取：

| 工具 | 用途 | 场景 |
|------|------|------|
| `useFetch` | SSR 安全的 fetch 封装 | 组件初始化数据 |
| `useAsyncData` | SSR 安全的异步函数封装 | 自定义数据获取逻辑 |
| `$fetch` | 基础 fetch 工具 | 客户端事件（表单提交等） |

### useFetch（最常用）

```vue
<script setup lang="ts">
const { data, status, error, refresh, clear } = await useFetch('/api/posts')
</script>

<template>
  <div v-if="status === 'pending'">加载中...</div>
  <div v-else-if="error">错误: {{ error.message }}</div>
  <div v-else>
    <article v-for="post in data" :key="post.id">
      {{ post.title }}
    </article>
  </div>
</template>
```

**常用选项：**

```ts
const { data } = await useFetch('/api/posts', {
  query: { page: 1, limit: 10 },     // 查询参数
  method: 'POST',                     // HTTP 方法
  body: { title: 'New Post' },        // 请求体
  pick: ['id', 'title'],              // 只选取特定字段
  transform: (posts) => posts.map(p => ({ ...p, slug: slugify(p.title) })),
  key: 'posts-list',                  // 缓存键
  server: false,                      // 不在服务端获取
  lazy: true,                         // 不阻塞导航
  immediate: false,                   // 不立即获取
  default: () => [],                  // 默认值
})
```

**响应式参数（自动重新获取）：**

```vue
<script setup lang="ts">
const page = ref(1)
const { data } = await useFetch('/api/posts', {
  query: { page },                    // page 变化时自动重新请求
})
</script>
```

### useAsyncData

用于包装任意异步函数：

```vue
<script setup lang="ts">
const { data } = await useAsyncData('cart', async () => {
  const [coupons, offers] = await Promise.all([
    $fetch('/api/coupons'),
    $fetch('/api/offers'),
  ])
  return { coupons, offers }
})
</script>
```

### $fetch

用于客户端事件处理：

```vue
<script setup lang="ts">
async function submitForm() {
  const result = await $fetch('/api/submit', {
    method: 'POST',
    body: { name: 'John' },
  })
}
</script>
```

> **重要：** 不要在 `<script setup>` 中单独使用 `$fetch` 获取初始数据，它会在服务端和客户端各执行一次。应使用 `useFetch` 或 `useAsyncData`。

### 懒加载

```vue
<script setup lang="ts">
const { data, status } = await useFetch('/api/posts', { lazy: true })
// 或使用快捷方式
const { data, status } = await useLazyFetch('/api/posts')
const { data, status } = await useLazyAsyncData('key', fetchFn)
</script>
```

### 刷新与监听

```vue
<script setup lang="ts">
const category = ref('tech')
const { data, refresh } = await useFetch('/api/posts', {
  query: { category },
  watch: [category],   // category 变化时自动刷新
})
</script>
```

### 缓存与共享

```vue
<script setup lang="ts">
// 组件 A
const { data } = await useFetch('/api/user', { key: 'current-user' })

// 组件 B - 使用缓存数据
const { data } = useNuxtData('current-user')

// 手动刷新
await refreshNuxtData('current-user')   // 刷新特定
await refreshNuxtData()                  // 刷新全部
clearNuxtData('current-user')           // 清除缓存
</script>
```

---

## 6. 自动导入

Nuxt 自动导入 Vue API、Nuxt 组合式函数以及自定义的 composables/utils。

### Vue API（无需 import）

```vue
<script setup lang="ts">
const count = ref(0)
const doubled = computed(() => count.value * 2)
watch(count, (val) => console.log('Changed:', val))
onMounted(() => console.log('Mounted'))
</script>
```

### Nuxt 内置组合式函数

```ts
useRoute()               // 当前路由信息
useRouter()              // 路由实例
useRuntimeConfig()       // 运行时配置
useAppConfig()           // 应用配置
useFetch('/api/data')    // 数据获取
useAsyncData('key', fn)  // 异步数据
useState('key', () => v) // 跨组件状态
useCookie('token')       // Cookie 操作
useHead({ title })       // 页面头信息
useSeoMeta({})           // SEO 元信息
useRequestHeaders()      // 请求头（SSR）
useRequestURL()          // 请求 URL（SSR）
```

### 自定义 Composables

```ts
// composables/useCounter.ts
export function useCounter(initial = 0) {
  const count = ref(initial)
  const increment = () => count.value++
  const decrement = () => count.value--
  return { count, increment, decrement }
}
```

```vue
<script setup lang="ts">
const { count, increment } = useCounter(10)  // 自动导入
</script>
```

> **扫描规则：** 仅 `composables/` 和 `utils/` 的顶层文件被自动扫描。子目录需通过 `index.ts` 导出，或配置 `imports.dirs`。

### 工具函数

```ts
// utils/format.ts
export function formatDate(date: Date) {
  return date.toLocaleDateString()
}
```

```vue
<script setup lang="ts">
const date = formatDate(new Date())  // 自动导入
</script>
```

### Composable 上下文规则

Nuxt 组合式函数必须在有效上下文中调用：

```ts
// ❌ 错误 - 模块顶层
const config = useRuntimeConfig()

// ✅ 正确 - 在函数内部
export function useMyComposable() {
  const config = useRuntimeConfig()
  return { apiBase: config.public.apiBase }
}
```

有效上下文：`<script setup>`、`setup()`、`defineNuxtPlugin()`、`defineNuxtRouteMiddleware()`。

---

## 7. 内置组件

### NuxtLink（导航链接）

```vue
<template>
  <NuxtLink to="/about">关于</NuxtLink>
  <NuxtLink to="https://nuxt.com" external>外部链接</NuxtLink>
  <NuxtLink to="/heavy" :prefetch="false">禁用预取</NuxtLink>
  <NuxtLink to="/page" replace>替换历史记录</NuxtLink>
</template>
```

### NuxtPage（页面出口）

```vue
<!-- app.vue -->
<template>
  <NuxtLayout>
    <NuxtPage />
  </NuxtLayout>
</template>
```

### NuxtLayout（布局）

```vue
<template>
  <NuxtLayout :name="layout">
    <NuxtPage />
  </NuxtLayout>
</template>
```

### NuxtLoadingIndicator（加载进度条）

```vue
<template>
  <NuxtLoadingIndicator color="#00dc82" :height="3" :duration="2000" />
  <NuxtLayout><NuxtPage /></NuxtLayout>
</template>
```

### ClientOnly（仅客户端渲染）

```vue
<template>
  <ClientOnly>
    <BrowserOnlyChart :data="chartData" />
    <template #fallback>
      <p>加载图表中...</p>
    </template>
  </ClientOnly>
</template>
```

### DevOnly（仅开发环境渲染）

```vue
<template>
  <DevOnly>
    <DebugPanel />
  </DevOnly>
</template>
```

### NuxtErrorBoundary（错误边界）

```vue
<template>
  <NuxtErrorBoundary @error="handleError">
    <ComponentThatMightFail />
    <template #error="{ error, clearError }">
      <p>出错了: {{ error.message }}</p>
      <button @click="clearError">重试</button>
    </template>
  </NuxtErrorBoundary>
</template>
```

### NuxtRouteAnnouncer（无障碍）

```vue
<template>
  <NuxtRouteAnnouncer />
  <NuxtLayout><NuxtPage /></NuxtLayout>
</template>
```

---

## 8. 状态管理

### useState（SSR 安全的状态共享）

```vue
<script setup lang="ts">
const counter = useState('counter', () => 0)
</script>

<template>
  <div>
    计数器: {{ counter }}
    <button @click="counter++">+</button>
    <button @click="counter--">-</button>
  </div>
</template>
```

### 创建共享状态 Composable

```ts
// composables/useUser.ts
export function useUser() {
  return useState<User | null>('user', () => null)
}
```

```vue
<script setup lang="ts">
const user = useUser()  // 所有组件共享同一实例
</script>
```

### 最佳实践

```ts
// ❌ 错误 - 模块级 ref，会导致内存泄漏和请求间状态共享
export const globalState = ref({ user: null })

// ✅ 正确 - 使用 useState
export const useGlobalState = () => useState('global', () => ({ user: null }))
```

### 清除状态

```ts
clearNuxtState('counter')          // 清除特定
clearNuxtState(['counter', 'user']) // 清除多个
clearNuxtState()                    // 清除全部
```

### Pinia 集成（复杂状态管理）

```bash
npx nuxi module add pinia
```

```ts
// stores/counter.ts
export const useCounterStore = defineStore('counter', {
  state: () => ({ count: 0 }),
  actions: { increment() { this.count++ } },
})
```

```vue
<script setup lang="ts">
const store = useCounterStore()
</script>
```

---

## 9. 服务端开发

Nuxt 内置 Nitro 服务引擎，支持全栈开发。

### API 路由

```ts
// server/api/hello.ts → GET /api/hello
export default defineEventHandler((event) => {
  return { message: 'Hello World' }
})
```

### HTTP 方法匹配

```ts
// server/api/users.get.ts       → GET /api/users
// server/api/users.post.ts      → POST /api/users
// server/api/users/[id].put.ts  → PUT /api/users/:id
// server/api/users/[id].delete.ts → DELETE /api/users/:id
```

### 路由参数与查询

```ts
// server/api/posts/[id].ts → /api/posts/:id
export default defineEventHandler((event) => {
  const id = getRouterParam(event, 'id')
  return getPost(id)
})

// server/api/search.ts → /api/search?q=nuxt&page=1
export default defineEventHandler((event) => {
  const query = getQuery(event)
  return search(query.q, Number(query.page))
})
```

### 请求体

```ts
// server/api/submit.post.ts
export default defineEventHandler(async (event) => {
  const body = await readBody(event)
  return { success: true, data: body }
})
```

### Headers 与 Cookies

```ts
export default defineEventHandler((event) => {
  const auth = getHeader(event, 'authorization')
  const token = getCookie(event, 'token')

  setHeader(event, 'X-Custom-Header', 'value')
  setCookie(event, 'token', 'new-token', {
    httpOnly: true,
    secure: true,
    maxAge: 60 * 60 * 24,
  })
})
```

### 服务端中间件

```ts
// server/middleware/auth.ts
export default defineEventHandler((event) => {
  const token = getCookie(event, 'token')
  event.context.user = token ? verifyToken(token) : null
})
```

在路由中访问上下文：

```ts
// server/api/profile.ts
export default defineEventHandler((event) => {
  const user = event.context.user
  if (!user) {
    throw createError({ statusCode: 401, message: 'Unauthorized' })
  }
  return user
})
```

### 错误处理

```ts
export default defineEventHandler((event) => {
  const id = getRouterParam(event, 'id')
  const user = findUser(id)
  if (!user) {
    throw createError({ statusCode: 404, statusMessage: 'User not found' })
  }
  return user
})
```

### 服务端存储

```ts
// server/api/cache.ts
export default defineEventHandler(async (event) => {
  const storage = useStorage()
  await storage.setItem('key', { data: 'value' })
  return await storage.getItem('key')
})
```

---

## 10. 渲染模式

### 通用渲染（SSR，默认）

```ts
export default defineNuxtConfig({
  ssr: true,  // 默认值
})
```

**优势：** 首屏快速加载、SEO 友好、无 JS 也可展示。

**流程：** 服务端执行 Vue → 生成 HTML → 浏览器展示 → JS 加载后水合交互。

### 客户端渲染（SPA）

```ts
export default defineNuxtConfig({
  ssr: false,
})
```

**适用场景：** 管理后台、SaaS 应用、需要登录的应用。

### 混合渲染（按路由配置）

```ts
export default defineNuxtConfig({
  routeRules: {
    '/': { prerender: true },           // 静态预渲染
    '/about': { prerender: true },
    '/blog/**': { isr: 3600 },          // ISR，每小时重新生成
    '/products/**': { swr: true },      // 边缓存边验证
    '/admin/**': { ssr: false },        // 仅客户端渲染
    '/api/**': { cors: true },          // CORS
  },
})
```

**路由规则参考：**

| 规则 | 说明 |
|------|------|
| `prerender: true` | 构建时预渲染 |
| `ssr: false` | 仅客户端 |
| `swr: number \| true` | 边缓存边验证 |
| `isr: number \| true` | 增量静态再生 |
| `redirect: string` | 重定向 |
| `cors: true` | CORS 头 |
| `headers: object` | 自定义响应头 |

### 页面级路由规则

```vue
<script setup lang="ts">
defineRouteRules({
  prerender: true,
})
</script>
```

### 条件渲染代码

```ts
if (import.meta.server) {
  // 仅服务端执行
}

if (import.meta.client) {
  // 仅客户端执行
}
```

---

## 11. 部署指南

### Node.js 服务器

```bash
nuxt build
node .output/server/index.mjs
```

环境变量：`PORT`（默认 3000）、`HOST`（默认 0.0.0.0）。

### 静态站点

```bash
nuxt generate
# 输出到 .output/public/，可部署到任意静态托管
```

### 平台预设

```ts
// nuxt.config.ts
export default defineNuxtConfig({
  nitro: {
    preset: 'vercel',  // 或 'netlify'、'cloudflare-pages' 等
  },
})
```

或通过环境变量：`NITRO_PRESET=vercel nuxt build`

### Docker 部署

```dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:20-alpine
WORKDIR /app
COPY --from=builder /app/.output .output
ENV PORT=3000
EXPOSE 3000
CMD ["node", ".output/server/index.mjs"]
```

### 平台选择指南

| 需求 | 推荐平台 |
|------|---------|
| 最快上手、小团队 | **Vercel** |
| 静态站点 + 表单 | **Netlify** |
| 成本敏感、全球加速 | **Cloudflare Pages** |
| 完全控制、企业级 | **Docker + VPS** |
| 无服务器 API | **Vercel / AWS Lambda** |

---

## 12. CLI 常用命令速查

| 命令 | 说明 |
|------|------|
| `npx nuxi init my-app` | 创建新项目 |
| `npx nuxt dev` | 启动开发服务器 |
| `npx nuxt dev --port 4000` | 指定端口 |
| `npx nuxt build` | 生产构建 |
| `npx nuxt build --prerender` | 构建并预渲染 |
| `npx nuxt generate` | 生成静态站点 |
| `npx nuxt preview` | 预览构建结果 |
| `npx nuxt prepare` | 生成 TypeScript 类型 |
| `npx nuxt typecheck` | 类型检查 |
| `npx nuxt analyze` | 分析打包体积 |
| `npx nuxt cleanup` | 清理生成文件 |
| `npx nuxt info` | 显示环境信息 |
| `npx nuxt upgrade` | 升级 Nuxt 版本 |
| `npx nuxt module add @nuxt/ui` | 添加模块 |
| `npx nuxt devtools enable` | 启用 DevTools |

---

## 附录：常用文件模板

### app.vue（最简版）

```vue
<template>
  <NuxtRouteAnnouncer />
  <NuxtLoadingIndicator />
  <NuxtLayout>
    <NuxtPage />
  </NuxtLayout>
</template>
```

### 典型页面

```vue
<script setup lang="ts">
const { data, status, error } = await useFetch('/api/items')

useHead({ title: 'Items List' })
</script>

<template>
  <div v-if="status === 'pending'">加载中...</div>
  <div v-else-if="error">{{ error.message }}</div>
  <div v-else>
    <div v-for="item in data" :key="item.id">
      {{ item.name }}
    </div>
  </div>
</template>
```

### 典型 API 路由

```ts
// server/api/items.ts
export default defineEventHandler(async (event) => {
  const query = getQuery(event)
  const items = await db.items.findMany({
    take: Number(query.limit) || 10,
  })
  return items
})
```

---

> **文档来源：** 本文档基于 [Nuxt Skill (antfu/skills@nuxt)](https://skills.sh/antfu/skills/nuxt) v2026.1.28 生成，该 Skill 提取自 Nuxt 官方仓库（[github.com/nuxt/nuxt](https://github.com/nuxt/nuxt)）。
> 如需了解更多细节，请参考 [Nuxt 官方文档](https://nuxt.com/docs)。
