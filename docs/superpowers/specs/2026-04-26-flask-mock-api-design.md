# Flask Mock API 替代数据库直接访问

## 背景

当前 Nuxt 项目通过 NuxtHub 的 `hub:db` 模块直接操作 SQLite 数据库（Drizzle ORM），其中 `chats` 和 `messages` 两张表负责存储会话和消息数据。项目需要将这部分数据库操作替换为调用外部 API 接口，以对接实际业务系统。

为了在不依赖真实业务接口的情况下保持项目可运行，在 `scripts/python/server/` 下创建 Flask Mock 服务，提供 API 接口供 Nuxt server 层调用。

## 架构

```
前端 (Vue) --> Nuxt server/api --> Flask Mock API (内存数据)
                                     |
                            后续替换为真实业务 API
```

Nuxt `server/api` 层作为中间层，前端代码不变，后续只需将 server 层的调用目标从 Flask 地址切换为真实业务地址。

## Flask Mock 服务

### 项目结构

```
scripts/python/server/
├── app.py              # Flask 主入口，定义路由
├── requirements.txt    # flask, flask-cors
└── mock_data.py        # 预置 mock 数据和内存存储
```

### 运行配置

- 端口：`5001`
- 启用 CORS（`flask-cors`）
- Mock 数据存储在内存中（Python 字典/列表），服务重启后数据重置

### 接口定义

#### 1. POST /api/chats — 创建会话

接收用户消息，在内存中创建新会话和消息记录，返回会话信息。

**请求体：**
```json
{
  "message": "你好，帮我分析一下项目架构"
}
```

**响应（200）：**
```json
{
  "id": "mock-7",
  "chat_id": "mock-7",
  "title": "你好，帮我分析一下项目架构",
  "createdAt": "2026-04-26T10:00:00Z"
}
```

**逻辑：**
- 生成递增 id（mock-7, mock-8, ...）
- 使用用户消息前 20 字符作为 title
- 创建一条 role=user 的 message
- 自动生成 1-2 条 mock 的 assistant 回复（预设中文模板文本）

#### 2. GET /api/chats — 会话列表

返回所有会话的摘要列表。

**请求参数：** 无

**响应（200）：**
```json
[
  {
    "id": "mock-1",
    "chat_id": "mock-1",
    "title": "帮我分析一下这段代码",
    "createdAt": "2026-04-26T08:00:00Z"
  }
]
```

**逻辑：**
- 返回内存中所有会话
- 预置 5 条 mock 数据（与当前 `chats.get.ts` 一致）
- 按创建时间倒序排列

#### 3. GET /api/chats/\<chat_id\>/stream — SSE 流式对话

以 SSE 格式逐条推送会话的消息记录。

**请求参数：** `chat_id` 在 URL 路径中

**响应（200，Content-Type: text/event-stream）：**

```
event: message
data: {"id":"msg-1","chatId":"mock-1","role":"user","parts":[{"type":"text","text":"帮我分析一下这段代码"}],"createdAt":"2026-04-26T08:00:00Z"}

event: message
data: {"id":"msg-2","chatId":"mock-1","role":"assistant","parts":[{"type":"text","text":"好的，让我来分析这段代码..."}],"createdAt":"2026-04-26T08:00:01Z"}

event: done
data: {}
```

**逻辑：**
- 查找内存中该 chat_id 的所有 messages
- 每条 message 作为一个 `event: message` 推送
- 每条之间加 50-100ms 延迟模拟流式效果
- 最后发送 `event: done` 结束

### Mock 数据格式

**Chat 对象：**
```json
{
  "id": "mock-1",
  "chat_id": "mock-1",
  "title": "帮我分析一下这段代码",
  "createdAt": "2026-04-26T08:00:00Z"
}
```

**Message 对象：**
```json
{
  "id": "msg-1",
  "chatId": "mock-1",
  "role": "user",
  "parts": [
    {"type": "text", "text": "帮我分析一下这段代码"}
  ],
  "createdAt": "2026-04-26T08:00:00Z"
}
```

**预置 Mock 会话（5 条）：**

| ID | Title | Messages |
|----|-------|----------|
| mock-1 | 帮我分析一下这段代码 | 用户提问 + assistant 文本回复 |
| mock-2 | 如何优化数据库查询 | 用户提问 + assistant 含 reasoning 的回复 |
| mock-3 | 帮我看看这个文件 | 用户提问 + assistant 含文件附件的回复 |
| mock-4 | 搜索最新的技术文档 | 用户提问 + assistant 含 source URL 的回复 |
| mock-6 | 多步骤任务演示 | 用户提问 + assistant 含工具调用、图表、来源的回复 |

## Nuxt server/api 层改动

### 配置

在 `.env` 中添加：
```
FLASK_API_URL=http://localhost:5001
```

在 `nuxt.config.ts` 的 `runtimeConfig` 中声明：
```typescript
runtimeConfig: {
  flaskApiUrl: process.env.FLASK_API_URL || 'http://localhost:5001'
}
```

Server 端通过 `useRuntimeConfig().flaskApiUrl` 读取。

### 文件改动清单

#### `chats.get.ts` — 会话列表
- 移除硬编码 mock 数据
- 调用 `GET {flaskApiUrl}/api/chats`
- 将响应映射为 `Chat[]` 返回

#### `[id].get.ts` — 会话详情
- 移除硬编码 mock 数据
- 调用 `GET {flaskApiUrl}/api/chats/<id>/stream`，收集 SSE events 中的 messages
- 组装为 `{ id, title, createdAt, messages, isOwner: true }` 返回

#### `chats.post.ts` — 创建会话
- 移除 DB 操作（`db.insert(schema.chats)`、`db.insert(schema.messages)`）
- 移除 `import { db, schema } from 'hub:db'`
- 调用 `POST {flaskApiUrl}/api/chats`，传入 `{ message }`
- 返回 Flask 返回的会话数据

#### `[id].post.ts` — 流式对话

> **注意**：前端使用 `@ai-sdk/vue` 的 `Chat` 类配合 `DefaultChatTransport`，该 transport POST 到此端点后期望收到 AI SDK 流协议格式的 SSE 响应（`0:` 文本、`9:` 工具调用等）。Nuxt server 层需要将 Flask 的自定义 SSE 格式转换为 AI SDK 流协议格式。

- 移除 DB 操作（`db.query.chats.findFirst`、`db.insert(schema.messages)`）
- 移除 AI SDK `streamText` 调用及相关 import（保留 `streamSSE` 等流工具）
- 接收前端 POST 请求，提取用户消息
- 调用 `GET {flaskApiUrl}/api/chats/<id>/stream` 获取 mock SSE 数据
- 在 Nuxt 层将 Flask SSE events 转换为 AI SDK 流协议格式（使用 `createDataStreamResponse` 或 `streamSSE`）返回给前端
- AI SDK 流协议关键格式：
  - `0:"text"\n` — 文本增量
  - `9:{"toolCallId","toolName","args"}\n` — 工具调用
  - `e:{"finishReason"}\n` — 完成事件
  - `d:{}\n` — 结束标记

#### `[id].delete.ts` — 删除会话
- 移除 DB 操作和 blob 操作
- Flask 不提供删除接口，该文件可删除或保留为空操作

### schema.ts 改动

- 删除 `chats` 表定义
- 删除 `chatsRelations`
- 删除 `messages` 表定义
- 删除 `messagesRelations`
- 保留 `users` 表和 `usersRelations`（OAuth 认证仍需要）
- 删除不再需要的 import（`sqliteTable`, `index` 等，如果 users 也删除则全部清理）

### 删除的文件

- `server/api/v1/agent/chats/[id].delete.ts`

## 后续切换到真实业务接口

切换步骤：
1. 将 `.env` 中的 `FLASK_API_URL` 改为真实业务接口地址
2. 在 Nuxt server/api 层调整请求参数/响应格式映射（如有差异）
3. 移除 `scripts/python/server/` 目录
