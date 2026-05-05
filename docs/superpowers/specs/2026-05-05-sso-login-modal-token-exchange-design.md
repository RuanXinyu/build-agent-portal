# 会话页登录弹框与 TokenExchange 签名改造设计

## 背景与目标

当前登录流程存在以下问题：

1. 未登录访问会话列表/详情页时会直接外跳 `/auth/sso`，缺少统一的登录确认体验。
2. 顶部导航登录按钮与会话页未登录拦截行为不一致，不满足“先弹框、后点击按钮再登录”的交互要求。
3. `TokenExchange` 仍按旧协议调用（`POST` + 单 Cookie），与目标服务的签名协议不一致。
4. `SSOUser` 模型缺少 `uuid`、`globalUserID`、`tenantId` 三个字段。

本次设计目标：

- 统一所有登录入口为“全局登录弹框”。
- 将 Token 交换改为 GET + 全量 Cookie + AK/SK 签名头。
- 扩展 SSO 用户字段，且缺失字段时不阻断登录。

## 用户已确认的约束

1. 未登录访问 `/chat` 或 `/chat/:id` 时：通过路由守卫拦截并弹框，不直接跳外部 SSO。
2. 全局登录框关闭行为：跳转到 `/home`。
3. 签名输入串中的 `url`：仅使用 `path`（不含 query、host）。
4. `X-HW-DATE`：ISO8601 UTC 格式（例如 `2026-05-05T08:44:00Z`）。
5. `SSOUser` 新增字段缺失时：宽松模式，允许继续登录。

## 方案选型

### 方案 A（采用）：全局状态中心 + 统一弹框组件 + 路由守卫触发

- 新增全局登录弹框状态管理（`useLoginModal` composable，基于 `useState`）。
- 路由中间件只负责“拦截 + 打开弹框”，不执行 SSO 跳转。
- Header 登录按钮改为打开同一弹框。
- 弹框中的“使用W3登录”按钮是唯一发起 `/auth/sso` 跳转的入口。

采用原因：

- 满足交互一致性与单一入口要求。
- 后续可按来源（路由拦截/按钮触发/401触发）做差异文案和埋点。
- 避免登录流程逻辑分散在多个组件中。

## 详细设计

### 1. 前端认证交互与路由控制

#### 1.1 全局登录弹框

新增全局组件（建议：`app/components/auth/LoginModal.vue`）与宿主组件（建议：`app/components/auth/LoginModalHost.vue`）：

- 固定标题和说明文案。
- 主按钮：`使用W3登录`。
- 可关闭。

挂载位置：

- 在 `app/app.vue` 或全局根 layout 中挂载 `LoginModalHost`，确保 `/home` 与 `/chat` 等不同 layout 都可见同一弹框。

行为定义：

- 打开来源支持：
  - 未登录访问会话页的路由守卫
  - 顶部导航登录按钮
  - 前端捕获 401
- 点击主按钮：
  - 关闭弹框
  - 执行 `window.location.href = '/auth/sso'`
- 点击关闭：
  - 关闭弹框
  - 跳转 `/home`

#### 1.2 路由守卫改造

文件：`app/middleware/auth.global.ts`

- 保留 `hasStaticAuthToken` 快速放行逻辑。
- 对 `/chat` 前缀路由，未登录时：
  - 不再 `navigateTo('/auth/sso', { external: true })`
  - 客户端导航：打开全局登录框，并 `return abortNavigation()`
  - 首次 SSR 直达保护路由：重定向到 `/home?auth_required=1`（仅作为技术兜底，避免 SSR 无法展示弹框导致空白）

兜底触发说明：

- 在全局插件中监听 `route.query.auth_required === '1'` 时自动打开登录弹框，然后通过 `router.replace` 移除 query，避免刷新后重复弹框。

#### 1.3 Header 登录按钮改造

文件：`app/components/AppHeader.vue`

- 现有 `loginWithSSO()` 从直接跳 `/auth/sso` 改为“打开全局登录框”。
- 按钮文本和图标保持不变，用户认知成本最低。

#### 1.4 401 处理改造

文件：`app/plugins/fetch.client.ts`

- 当前 401 行为是直接 `window.location.href = '/auth/sso'`。
- 改为：
  1. 清理前端会话（已登录时）
  2. 打开全局登录框
  3. 防重复触发（沿用已有 `isRedirecting` 防抖语义，可重命名为 `isHandlingAuthFailure`）
  4. 如当前不在 `/home`，可导航到 `/home` 后展示弹框，保持“关闭弹框回到 home”一致体验

#### 1.5 chat 布局遗留重定向清理

文件：`app/layouts/chat.vue`

- 当前 `watch(loggedIn)` 内存在直接 `navigateTo('/auth/sso', { external: true })` 的逻辑。
- 需改为复用全局登录弹框打开动作，避免与新规则冲突。
- `loggedIn` 变为 false 时，清理 chat 缓存数据并收起侧栏，再由统一认证入口接管后续动作。

### 2. TokenExchange 协议与签名

#### 2.1 runtimeConfig 扩展

文件：`nuxt.config.ts`

新增私有配置项：

- `ssoAccessKey: process.env.NUXT_SSO_AK || ''`
- `ssoSecretKey: process.env.NUXT_SSO_SK || ''`

说明：

- 仅放在服务端 `runtimeConfig`，不暴露到 `public`。

#### 2.2 tokenExchange 调用改造

文件：`server/utils/tokenExchange.ts`

接口调用变更：

- 方法：`POST` -> `GET`
- Cookie：从单 Cookie 拼接改为透传请求中的完整 Cookie 字符串
- 新增 headers：
  - `X-HW-ACCESS-KEY`
  - `X-HW-DATE`
  - `X-HW-SIGN`

签名规则：

- 待签名字符串：`{path}|{method}|{time}|{ak}|{sk}`
- `path`：仅 URL path
- `method`：固定 `GET`
- `time`：与 `X-HW-DATE` 同值（ISO8601 UTC）
- 算法：`sha256`，输出 hex
- 协议性质：这是对端定义的自定义签名串协议，不使用 HMAC；实现时应在注释中明确，避免后续维护者误改为 HMAC 模式

`path` 提取规范：

- 使用 `new URL(config.tokenExchangeUrl).pathname` 提取，确保不会包含 query 与域名。

建议新增辅助函数（同文件内私有函数）：

- `buildHwDate(now = new Date()): string`
- `buildSignatureInput(path, method, time, ak, sk): string`
- `buildHwSign(input): string`

异常处理：

- AK/SK 缺失时，记录明确日志并返回 `null`。
- 不打印 SK 和完整签名源串，避免敏感信息泄露。

### 3. SSOUser 字段扩展

#### 3.1 类型扩展

文件：`server/utils/sso.ts`

`SSOUser` 新增字段：

- `uuid?: string`
- `globalUserID?: string`
- `tenantId?: string`

字段来源兼容：

- 对接返回可能出现大小写差异（例如 `globalUserID` / `globalUserId`），在归一化步骤统一映射到会话字段命名。

#### 3.2 登录流程数据承载

文件：`server/routes/auth/sso.get.ts`

在 `setUserSession` 的 `user` 结构中追加上述字段（缺失则为空值或 `undefined` 均可），满足“宽松模式”：

- 缺失不抛错
- 不阻断登录链路

> 本设计默认：本轮先扩展 session 用户字段，不引入数据库 schema 迁移，避免影响当前发布窗口。

类型同步：

- 若项目存在 `shared/types/auth.d.ts`（或同等 session user 类型声明），需同步补充三个可选字段，确保 TS 类型与运行态一致。

## 影响范围

前端：

- `app/middleware/auth.global.ts`
- `app/components/AppHeader.vue`
- `app/plugins/fetch.client.ts`
- 新增全局登录弹框相关组件/状态管理

后端：

- `server/utils/tokenExchange.ts`
- `server/utils/sso.ts`
- `server/routes/auth/sso.get.ts`
- `nuxt.config.ts`（服务端 runtimeConfig）

## 风险与缓解

1. **路由守卫与页面请求并发触发导致闪烁**
   - 缓解：在守卫层尽早中断导航，避免进入会话页后再抛 401。

2. **401 全局处理重复触发**
   - 缓解：保留单飞标记，统一只触发一次弹框打开。

3. **签名字段格式与服务端不一致**
   - 缓解：签名输入串构造集中封装；添加单元级断言（可选）和详细调试日志（不含密钥）。

4. **完整 Cookie 透传可能含无关字段**
   - 缓解：遵循接口要求全量透传，并在日志中仅打印长度或键名摘要。

## 验收标准

### 交互验收

1. 未登录访问 `/chat` 与 `/chat/:id` 时弹出全局登录框，不直接跳 SSO。
2. 点击导航栏“登录”按钮时弹出同一登录框。
3. 点击登录框“使用W3登录”才触发 `/auth/sso` 跳转。
4. 关闭登录框后跳转 `/home`。

### 协议验收

1. TokenExchange 请求方法为 `GET`。
2. `Cookie` header 为原始完整 cookie 字符串。
3. 请求头包含 `X-HW-ACCESS-KEY`、`X-HW-DATE`、`X-HW-SIGN`。
4. `X-HW-SIGN` 按 `path|GET|time|ak|sk` 的 sha256 hex 生成。
5. AK/SK 缺失场景可观测且安全失败。

### 数据验收

1. `SSOUser` 类型包含 `uuid`、`globalUserID`、`tenantId`。
2. 三字段缺失不阻断登录。

## 不在本次范围

1. `users` 表 schema 迁移与历史数据回填。
2. 多登录方式（除 W3 之外）的 UI 扩展。
3. SSO 协议对接方的错误码体系重构。
