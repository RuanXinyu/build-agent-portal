# Chat 详情页预览遮罩与 chat_id 修复 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修复 chat 详情页的预览遮罩穿透、继续对话 `chat_id` 语义、详情判存逻辑，并补齐 `chat_id` 数据契约。

**Architecture:** 保持现有页面与网关结构不变，采用最小侵入改造。前端在 `app/pages/chat/[id].vue` 强化“发送参数强约束 + 预览层全遮罩锁滚”，服务端在 `server/api/v1/agent/chats/[id].get.ts` 改为“第三方详情接口判存 + 返回 `chat_id` 字段”，通过针对性测试与回归脚本验证不破坏现有新建/续聊链路。

**Tech Stack:** Nuxt 4、Vue 3、TypeScript、Nitro/h3、Vitest

---

## Scope & File Structure

### 目标文件与职责

- Modify: `server/api/v1/agent/chats/[id].get.ts`
  - 用第三方详情接口 `/buildagent/v1/agent/chats/{id}` 判存。
  - 返回体新增 `chat_id`，并固定 `id` 语义为路由参数。
- Modify: `app/pages/chat/[id].vue`
  - `ChatData` 类型补充 `chat_id`。
  - 发送请求体 `chat_id` 强制取 `String(route.params.id)`。
  - 文件预览最大化时启用全遮罩与滚动锁清理机制。
- Verify only: `server/api/v1/agent/chats.post.ts`
  - 确认继续对话路径仍统一透传 `app_name: "BuildAgentPortal"`。

### 测试文件

- Create: `server/api/v1/agent/chats/[id].get.test.ts`
  - 覆盖详情接口判存路径与返回字段契约（含 `chat_id`）。
- Create: `app/pages/chat/[id].transport.test.ts`
  - 覆盖发送 body 中 `chat_id` 强制来源于 URL id 的规则。
- Create: `app/composables/usePreviewOverlayLock.test.ts`
  - 覆盖预览打开/关闭/卸载时滚动锁行为。
- Create: `app/composables/usePreviewOverlayLock.ts`
  - 抽离预览锁滚逻辑，避免把副作用散落在页面脚本里。

---

### Task 1: 服务端详情判存改造与返回契约

**Files:**
- Modify: `server/api/v1/agent/chats/[id].get.ts`
- Test: `server/api/v1/agent/chats/[id].get.test.ts`

- [ ] **Step 1: 写失败测试（详情判存与返回结构）**

```ts
it('returns 404 when upstream chat detail does not exist', async () => {
  // mock upstream GET /buildagent/v1/agent/chats/:id -> 404
  // expect handler to throw 404 Chat not found
})

it('returns chat_id from upstream detail payload', async () => {
  // mock detail endpoint returns { id: "r1", chat_id: "c1", ... }
  // expect response.chat_id === "c1"
  // expect response.id === route param id
})
```

- [ ] **Step 2: 运行测试并确认失败**

Run: `pnpm vitest "server/api/v1/agent/chats/[id].get.test.ts" -r verbose`  
Expected: FAIL，提示当前实现仍依赖列表判存或缺失 `chat_id`。

- [ ] **Step 3: 最小实现**

```ts
// in handler
const detail = await useInternalService(event, `/buildagent/v1/agent/chats/${id}`)
// remove list+find existence check
return {
  id, // keep route id semantics
  chat_id: detail.data.chat_id,
  // ...existing fields
}
```

- [ ] **Step 4: 重新运行测试确认通过**

Run: `pnpm vitest "server/api/v1/agent/chats/[id].get.test.ts" -r verbose`  
Expected: PASS。

- [ ] **Step 5: 提交**

```bash
git add server/api/v1/agent/chats/[id].get.ts server/api/v1/agent/chats/[id].get.test.ts
git commit -m "fix: use chat detail endpoint for existence and return chat_id"
```

---

### Task 2: 继续对话 chat_id 强约束（URL id 优先）

**Files:**
- Modify: `app/pages/chat/[id].vue`
- Test: `app/pages/chat/[id].transport.test.ts`

- [ ] **Step 1: 写失败测试（发送参数约束）**

```ts
it('always sends route id as chat_id on detail page', async () => {
  // given route.params.id = "chat-from-url"
  // when sendMessages() is called with any sdk chatId
  // expect POST /api/v1/agent/chats body.chat_id === "chat-from-url"
})
```

- [ ] **Step 2: 运行测试并确认失败**

Run: `pnpm vitest "app/pages/chat/[id].transport.test.ts" -r verbose`  
Expected: FAIL，当前构造 body 可能受 SDK chatId 影响。

- [ ] **Step 3: 最小实现**

```ts
const routeChatId = String(route.params.id || '')
const body = { prompt, chat_id: routeChatId }
```

- [ ] **Step 4: 重新运行测试确认通过**

Run: `pnpm vitest "app/pages/chat/[id].transport.test.ts" -r verbose`  
Expected: PASS。

- [ ] **Step 5: 提交**

```bash
git add app/pages/chat/[id].vue app/pages/chat/[id].transport.test.ts
git commit -m "fix: enforce route chat id in detail page send payload"
```

---

### Task 3: 预览最大化全遮罩与滚动锁

**Files:**
- Create: `app/composables/usePreviewOverlayLock.ts`
- Test: `app/composables/usePreviewOverlayLock.test.ts`
- Modify: `app/pages/chat/[id].vue`

- [ ] **Step 1: 写失败测试（锁滚与清理）**

```ts
it('locks scrolling when preview opens and restores on close', () => {
  // open -> expect class/style lock applied
  // close -> expect lock removed
})

it('cleans lock on scope dispose', () => {
  // mount composable, open lock, dispose scope
  // expect no residual lock on body/container
})
```

- [ ] **Step 2: 运行测试并确认失败**

Run: `pnpm vitest "app/composables/usePreviewOverlayLock.test.ts" -r verbose`  
Expected: FAIL，因 composable 尚不存在。

- [ ] **Step 3: 最小实现（抽离锁滚）**

```ts
export function usePreviewOverlayLock(isOpen: Ref<boolean>) {
  // watch isOpen and toggle document.body overflow/class
  // onBeforeUnmount cleanup
}
```

- [ ] **Step 4: 页面接入与样式兜底**

```vue
<!-- overlay keeps full viewport coverage and blocks pointer events -->
<div v-if="maximizedFile" class="fixed inset-0 z-50 ...">
```

- [ ] **Step 5: 跑测试确认通过**

Run: `pnpm vitest "app/composables/usePreviewOverlayLock.test.ts" -r verbose`  
Expected: PASS。

- [ ] **Step 6: 手工验证交互**

Run: `pnpm dev`  
Manual checks:
- 打开文件最大化后，消息列表不可滚动。
- 底层消息不可点击/选中。
- 关闭或跳转页面后滚动恢复。

- [ ] **Step 7: 提交**

```bash
git add app/composables/usePreviewOverlayLock.ts app/composables/usePreviewOverlayLock.test.ts app/pages/chat/[id].vue
git commit -m "fix: prevent message scroll-through under maximized preview"
```

---

### Task 4: 全链路回归与收尾

**Files:**
- Verify: `server/api/v1/agent/chats.post.ts`
- Verify: `server/api/v1/agent/chats/[id].get.ts`
- Verify: `app/pages/chat/[id].vue`

- [ ] **Step 1: 写回归检查清单（脚本化）**

```txt
1) GET /api/v1/agent/chats/:id returns chat_id
2) POST /api/v1/agent/chats includes app_name in upstream payload
3) detail-page send payload uses route id as chat_id
4) preview overlay blocks background interactions
```

- [ ] **Step 2: 运行测试集**

Run: `pnpm vitest "server/api/v1/agent/chats/[id].get.test.ts" "app/pages/chat/[id].transport.test.ts" "app/composables/usePreviewOverlayLock.test.ts" -r verbose`  
Expected: PASS。

- [ ] **Step 3: 类型与基础 lint 检查**

Run: `pnpm lint && pnpm typecheck`  
Expected: PASS（无新增错误）。

- [ ] **Step 4: 提交**

```bash
git add -A
git commit -m "test: add regression coverage for chat detail id and preview overlay behavior"
```

---

## 执行注意事项

- 先做测试再做实现（TDD），每个任务保持最小改动面（YAGNI）。
- 每个任务完成后立即运行对应测试，不跨任务叠加未验证改动。
- 如果发现现有仓库没有适配的测试 harness，可在任务内先补最小 harness，再继续测试步骤。
- 使用 `@superpowers:subagent-driven-development` 执行时，按 Task 粒度派发，任务间做代码评审。
- 使用 `@superpowers:executing-plans` 执行时，每完成 1 个 Task 就停下来做一次验收 checkpoint。
