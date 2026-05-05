# SSO 登录弹框与 TokenExchange 签名改造 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 统一未登录会话访问与手动登录入口为全局登录弹框，并完成 TokenExchange 新协议（GET + 全量 Cookie + AK/SK 签名）与 SSOUser 字段扩展。

**Architecture:** 前端通过 `useLoginModal` 提供单一认证入口状态，路由守卫、Header 登录按钮和 401 处理都只触发该入口；后端在 `tokenExchange` 中新增自定义 sha256 签名头并切换为 GET；SSO 回调将扩展字段写入 session user，缺失字段不阻断流程。为避免 SSR 直达保护页白屏，使用 `/home?auth_required=1` 兜底并由客户端插件拉起弹框。

**Tech Stack:** Nuxt 3, Vue 3, @nuxt/ui, nuxt-auth-utils, ofetch, Node.js crypto

---

## File Structure

| File | Action | Responsibility |
|---|---|---|
| `app/composables/useLoginModal.ts` | Create | 全局登录弹框状态、打开来源、关闭策略 |
| `app/components/auth/LoginModal.vue` | Create | 登录弹框 UI（使用W3登录、关闭） |
| `app/components/auth/LoginModalHost.vue` | Create | 宿主组件，承接跳转与副作用 |
| `app/app.vue` | Modify | 全局挂载 `LoginModalHost` |
| `app/middleware/auth.global.ts` | Modify | chat 路由未登录拦截逻辑（客户端 abort + SSR 兜底） |
| `app/plugins/fetch.client.ts` | Modify | 401 改为打开全局弹框，不直接跳 SSO |
| `app/plugins/auth-required.client.ts` | Create | 处理 `auth_required=1` 并打开弹框后清 query |
| `app/components/AppHeader.vue` | Modify | 登录按钮改为打开登录弹框 |
| `app/layouts/chat.vue` | Modify | 移除未登录直跳 `/auth/sso`，改统一入口 |
| `nuxt.config.ts` | Modify | 新增 `ssoAccessKey/ssoSecretKey` runtimeConfig |
| `server/utils/tokenExchange.ts` | Modify | GET + 全量 Cookie + `X-HW-*` 签名头 |
| `server/utils/sso.ts` | Modify | `SSOUser` 新增 `uuid/globalUserID/tenantId` |
| `server/routes/auth/sso.get.ts` | Modify | 扩展字段写入 session user（宽松模式） |
| `shared/types/auth.d.ts` | Modify | session user 类型补齐 3 个可选字段 |
| `server/utils/tokenExchange.test.ts`（如仓库无同类测试则新建） | Create/Modify | 签名输入串与头构造测试 |
| `vitest.config.ts`（如不存在） | Create | Vitest 运行配置 |

---

### Task 0: 补齐测试基建（若仓库未配置）

**Files:**
- Modify: `package.json`
- Modify: `pnpm-lock.yaml`
- Create: `vitest.config.ts`（若不存在）

- [ ] **Step 1: 检查 vitest 基建是否已存在**

Run:
```bash
cd /d/codes/BuildMate/chat && cat package.json
```

Expected: 若不存在 `vitest` 与 `@nuxt/test-utils`，继续 Step 2；否则跳至 Task 1。

- [ ] **Step 2: 安装最小测试依赖**

Run: `cd /d/codes/BuildMate/chat && pnpm add -D vitest @nuxt/test-utils @vue/test-utils happy-dom`

Expected: 依赖安装成功，`package.json` 更新。

- [ ] **Step 3: 补充 vitest 配置**

要求：
- 可运行 `pnpm vitest --run`
- 提供 Nuxt 上下文支持（或明确 mock 策略）

- [ ] **Step 4: 验证测试命令可执行**

Run: `cd /d/codes/BuildMate/chat && pnpm vitest --run`

Expected: 命令可执行（允许出现与本功能无关的历史失败）。

- [ ] **Step 5: Commit**

Run: `cd /d/codes/BuildMate/chat && git add package.json pnpm-lock.yaml vitest.config.ts && git commit -m "test: setup vitest and nuxt test utils baseline"`

---

### Task 1: 建立全局登录弹框状态中心

**Files:**
- Create: `app/composables/useLoginModal.ts`
- Test: `app/composables/useLoginModal.test.ts`（如已有 Vitest 体系）

- [ ] **Step 1: 写失败测试（状态默认值与打开/关闭行为）**

示例断言（伪码）：
```ts
it('opens modal with source and closes to home strategy', () => {
  const modal = useLoginModal()
  expect(modal.isOpen.value).toBe(false)
  modal.open('route-guard')
  expect(modal.isOpen.value).toBe(true)
  expect(modal.source.value).toBe('route-guard')
  modal.close('go-home')
  expect(modal.isOpen.value).toBe(false)
})
```

测试准备要求：
- `useState` 依赖 Nuxt 上下文，测试需使用 `@nuxt/test-utils`（如 `mountSuspended`）或 mock `#app` 中的 `useState`。

- [ ] **Step 2: 运行测试并确认失败**

Run: `cd /d/codes/BuildMate/chat && pnpm vitest app/composables/useLoginModal.test.ts`

Expected: FAIL（模块不存在或行为未实现）。

- [ ] **Step 3: 实现 `useLoginModal` 最小能力**

实现点：
- `isOpen/source` 使用 `useState`。
- 暴露 `open(source)`、`close()`、`requestLogin()`。
- `close(strategy?: 'go-home' | 'stay')` 签名与测试保持一致。
- `requestLogin()` 不直接跳转，由 Host 接管。

- [ ] **Step 4: 再次运行测试**

Run: `cd /d/codes/BuildMate/chat && pnpm vitest app/composables/useLoginModal.test.ts`

Expected: PASS。

- [ ] **Step 5: Commit**

Run: `cd /d/codes/BuildMate/chat && git add app/composables/useLoginModal.ts app/composables/useLoginModal.test.ts && git commit -m "feat: add global login modal state composable"`

---

### Task 2: 实现全局登录弹框组件与挂载

**Files:**
- Create: `app/components/auth/LoginModal.vue`
- Create: `app/components/auth/LoginModalHost.vue`
- Modify: `app/app.vue`

- [ ] **Step 1: 写失败测试（按钮行为）**

覆盖：
- 点击“使用W3登录”触发 host 的登录动作。
- 点击关闭触发“跳 `/home`”。

- [ ] **Step 2: 运行测试并确认失败**

Run: `cd /d/codes/BuildMate/chat && pnpm vitest --run app/components/auth/LoginModalHost.test.ts`

Expected: FAIL。

- [ ] **Step 3: 实现 `LoginModal.vue` UI**

实现点：
- 使用 `UModal`（或项目一致的 Nuxt UI 对话框组件）。
- 文案固定为“使用W3登录”。
- 提供 `confirm` 与 `close` 事件。

- [ ] **Step 4: 实现 `LoginModalHost.vue` 副作用**

实现点：
- 监听 composable 状态决定弹框显示。
- `confirm` 时执行 `window.location.href = '/auth/sso'`。
- `close` 时执行 `navigateTo('/home')`。

- [ ] **Step 5: 在 `app/app.vue` 全局挂载 Host**

保证跨 layout 可见。

- [ ] **Step 6: 运行测试**

Run: `cd /d/codes/BuildMate/chat && pnpm vitest --run app/components/auth/LoginModalHost.test.ts`

Expected: PASS。

- [ ] **Step 7: Commit**

Run: `cd /d/codes/BuildMate/chat && git add app/components/auth/LoginModal.vue app/components/auth/LoginModalHost.vue app/app.vue && git commit -m "feat: add global W3 login modal host"`

---

### Task 3: 改造路由守卫与 auth_required 兜底

**Files:**
- Modify: `app/middleware/auth.global.ts`
- Create: `app/plugins/auth-required.client.ts`

- [ ] **Step 1: 写失败测试（未登录访问 chat 行为）**

覆盖：
- 客户端导航到 `/chat`：`abortNavigation` + 打开弹框。
- SSR 直达 `/chat`：重定向 `/home?auth_required=1`。

- [ ] **Step 2: 运行测试并确认失败**

Run: `cd /d/codes/BuildMate/chat && pnpm vitest --run app/middleware/auth.global.test.ts`

Expected: FAIL。

- [ ] **Step 3: 实现中间件新逻辑**

实现点：
- 保留 `hasStaticAuthToken` 放行。
- `to.path.startsWith('/chat') && !loggedIn` 时分客户端/服务端处理。

- [ ] **Step 4: 实现 `auth-required.client` 插件**

实现点：
- 检测 `route.query.auth_required === '1'`。
- 打开登录弹框。
- `router.replace` 清除 query，避免重复弹。

- [ ] **Step 5: 运行测试**

Run: `cd /d/codes/BuildMate/chat && pnpm vitest --run app/middleware/auth.global.test.ts`

Expected: PASS。

- [ ] **Step 6: Commit**

Run: `cd /d/codes/BuildMate/chat && git add app/middleware/auth.global.ts app/middleware/auth.global.test.ts app/plugins/auth-required.client.ts && git commit -m "feat: gate chat routes with global login modal flow"`

---

### Task 4: 统一 Header / chat layout / 401 认证入口

**Files:**
- Modify: `app/components/AppHeader.vue`
- Modify: `app/layouts/chat.vue`
- Modify: `app/plugins/fetch.client.ts`

- [ ] **Step 1: 写失败测试（登录入口统一）**

覆盖：
- Header 登录按钮只打开弹框。
- chat layout 未登录变化不再直跳 `/auth/sso`。
- 401 触发后打开弹框而不是外跳。

- [ ] **Step 2: 运行测试并确认失败**

Run: `cd /d/codes/BuildMate/chat && pnpm vitest --run app/components/AppHeader.test.ts app/plugins/fetch.client.test.ts`

Expected: FAIL。

- [ ] **Step 3: 改造 `AppHeader.vue`**

将 `loginWithSSO` 改为 `openLoginModal`。

- [ ] **Step 4: 改造 `chat.vue`**

删除或替换 `navigateTo('/auth/sso', { external: true })`，并保留：
- `clearNuxtData('chats')`
- `open.value = false`

- [ ] **Step 5: 改造 `fetch.client.ts`**

实现点：
- 401 时 `clear()` 后打开弹框。
- 防重复触发标记改为认证处理中语义。
- 保留 `hasStaticAuthToken` 分支逻辑（继续 toast 提示，不弹框）。

- [ ] **Step 6: 运行测试**

Run: `cd /d/codes/BuildMate/chat && pnpm vitest --run app/components/AppHeader.test.ts app/plugins/fetch.client.test.ts`

Expected: PASS。

- [ ] **Step 7: Commit**

Run: `cd /d/codes/BuildMate/chat && git add app/components/AppHeader.vue app/layouts/chat.vue app/plugins/fetch.client.ts && git commit -m "refactor: unify login entry via global modal"`

---

### Task 5: TokenExchange 协议升级（GET + 签名头）

**Files:**
- Modify: `nuxt.config.ts`
- Modify: `server/utils/tokenExchange.ts`
- Test: `server/utils/tokenExchange.test.ts`

- [ ] **Step 1: 写失败测试（签名串与请求头）**

覆盖：
- method 为 GET。
- `X-HW-DATE` 为 ISO8601 UTC。
- `X-HW-SIGN` 输入串为 `path|GET|time|ak|sk` 后 sha256 hex。
- Cookie 透传为完整原始 cookie。

- [ ] **Step 2: 运行测试并确认失败**

Run: `cd /d/codes/BuildMate/chat && pnpm vitest --run server/utils/tokenExchange.test.ts`

Expected: FAIL。

- [ ] **Step 3: 增加 runtimeConfig 私有配置**

在 `nuxt.config.ts` 新增：
- `ssoAccessKey`
- `ssoSecretKey`

- [ ] **Step 4: 实现 `tokenExchange.ts` 新协议**

实现点：
- 从 event 读取完整 cookie 字符串（不是单 cookie）。
- `ofetch(..., { method: 'GET', headers })`。
- `X-HW-ACCESS-KEY` / `X-HW-DATE` / `X-HW-SIGN`。
- `path` 由 `new URL(config.tokenExchangeUrl).pathname` 提取。
- AK/SK 缺失时返回 `null` 并记录日志。
- 日志安全约束：禁止输出 `sk`、禁止输出完整 `signatureInput`。

- [ ] **Step 5: 运行测试**

Run: `cd /d/codes/BuildMate/chat && pnpm vitest --run server/utils/tokenExchange.test.ts`

Expected: PASS。

- [ ] **Step 6: Commit**

Run: `cd /d/codes/BuildMate/chat && git add nuxt.config.ts server/utils/tokenExchange.ts server/utils/tokenExchange.test.ts && git commit -m "feat: update token exchange with signed GET headers"`

---

### Task 6: SSOUser 字段扩展并写入 session

**Files:**
- Modify: `server/utils/sso.ts`
- Modify: `server/routes/auth/sso.get.ts`
- Modify: `shared/types/auth.d.ts`
- Test: `server/routes/auth/sso.get.test.ts`（若已有对应测试文件则修改）

- [ ] **Step 1: 写失败测试（字段缺失不阻断）**

覆盖：
- 返回包含 `uuid/globalUserID/tenantId` 时写入 session。
- 任意字段缺失时仍可登录成功。

- [ ] **Step 2: 运行测试并确认失败**

Run: `cd /d/codes/BuildMate/chat && pnpm vitest --run server/routes/auth/sso.get.test.ts`

Expected: FAIL。

- [ ] **Step 3: 扩展 SSOUser 类型**

在 `server/utils/sso.ts` 增加 3 个可选字段，并做好大小写兼容归一化（如 `globalUserId` -> `globalUserID`）。

- [ ] **Step 4: 写入 session user**

在 `server/routes/auth/sso.get.ts` 的 `setUserSession` 用户对象中追加 3 字段，缺失时不抛错。

- [ ] **Step 5: 同步共享类型**

在 `shared/types/auth.d.ts` 对应 `User` 接口追加 3 个可选字段。

- [ ] **Step 6: 运行测试**

Run: `cd /d/codes/BuildMate/chat && pnpm vitest --run server/routes/auth/sso.get.test.ts`

Expected: PASS。

- [ ] **Step 7: Commit**

Run: `cd /d/codes/BuildMate/chat && git add server/utils/sso.ts server/routes/auth/sso.get.ts shared/types/auth.d.ts server/routes/auth/sso.get.test.ts && git commit -m "feat: add SSO user optional identity fields"`

---

### Task 7: 端到端回归与发布前检查

**Files:**
- Modify (if needed): `docs/superpowers/specs/2026-05-05-sso-login-modal-token-exchange-design.md`
- Modify (if needed): `docs/superpowers/plans/2026-05-05-sso-login-modal-token-exchange-plan.md`

- [ ] **Step 1: 运行关键校验命令**

Run:
```bash
cd /d/codes/BuildMate/chat && pnpm lint
cd /d/codes/BuildMate/chat && pnpm vitest --run
```

Expected: 本次改动相关检查通过（若仓库已有历史失败项，需在记录中区分）。

- [ ] **Step 2: 手工验收登录交互**

检查：
1. 未登录访问 `/chat` 与 `/chat/:id` 弹框出现。
2. Header 登录按钮弹同一框。
3. 仅弹框内“使用W3登录”触发 `/auth/sso`。
4. 关闭弹框跳 `/home`。

- [ ] **Step 3: 手工验收 token 交换请求**

检查：
1. 请求为 GET。
2. 含 `X-HW-ACCESS-KEY/X-HW-DATE/X-HW-SIGN`。
3. Cookie 为全量透传。

- [ ] **Step 4: 汇总验证证据并 Commit（如有修复）**

Run: `cd /d/codes/BuildMate/chat && git add -A && git commit -m "test: validate global login modal and signed token exchange flow"`

---

## 备注

- DRY：登录跳转副作用集中在 `LoginModalHost`。
- YAGNI：本期不做 users 表 migration，仅扩展 session 字段。
- 若测试基建不足，可先补最小可维护测试再进入实现。
