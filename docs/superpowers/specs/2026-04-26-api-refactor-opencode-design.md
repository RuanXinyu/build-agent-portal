# API 重构：统一对话入口 + opencode 格式转换

## 背景

上一轮实现了 Flask Mock API 替代数据库直接访问。现在需要进一步调整 API 流程：

1. 统一对话入口：`chats.post.ts` 同时处理「创建会话」和「继续对话」（通过 `chat_id` 是否为空区分）
2. Flask stream 接口返回 opencode NDJSON 格式（与 `opencode --format json run` 一致）
3. Nuxt server 层做格式转换：opencode → AI SDK 前端可渲染格式
4. 删除 `[id].post.ts`，消息获取统一走 `[id].get.ts`（SSE 模式）
5. 增量日志：初次加载记录最新时间戳，流式监听只返回新增日志
6. 对话完成标记：最后一行 `type: "chat.completed"` 表示对话结束
7. Flask 随机生成丰富数据以辅助验证

## 架构

```
前端 (Chat + 自定义 Transport)
  ↓ POST { chat_id?, prompt }           ↓ EventSource ?stream=true&after_ts=xxx
  chats.post.ts                         [id].get.ts
  ↓ 调用 Flask                          ↓ 调用 Flask stream + after_ts
  Flask POST /api/chats                 Flask GET /api/chats/{id}/stream?after_ts=xxx
  (返回 chat_id, message_id)            (返回增量 opencode NDJSON)
                                        ↓ 格式转换
                                        opencode → AI SDK stream parts
                                        ↓ SSE 推送
                                        前端 Chat 类消费
```

## opencode NDJSON 格式

每行一个 JSON 对象，5 种事件类型：

### step_start
```json
{
  "type": "step_start",
  "timestamp": 1777186655741,
  "sessionID": "ses_xxx",
  "part": {
    "id": "prt_xxx",
    "messageID": "msg_xxx",
    "sessionID": "ses_xxx",
    "snapshot": "334ccf1...",
    "type": "step-start"
  }
}
```

### text
```json
{
  "type": "text",
  "timestamp": 1777186675209,
  "sessionID": "ses_xxx",
  "part": {
    "id": "prt_xxx",
    "messageID": "msg_xxx",
    "sessionID": "ses_xxx",
    "type": "text",
    "text": "AI 回复内容",
    "time": { "start": 1777186673495, "end": 1777186675208 }
  }
}
```

### tool_use
```json
{
  "type": "tool_use",
  "timestamp": 1777186656354,
  "sessionID": "ses_xxx",
  "part": {
    "type": "tool",
    "tool": "bash",
    "callID": "call_xxx",
    "state": {
      "status": "completed",
      "input": { "command": "echo hello" },
      "output": "hello\n"
    },
    "id": "prt_xxx",
    "messageID": "msg_xxx",
    "sessionID": "ses_xxx",
    "title": "Echo hello",
    "time": { "start": 1777186656314, "end": 1777186656350 }
  }
}
```

### step_finish
```json
{
  "type": "step_finish",
  "timestamp": 1777186656622,
  "sessionID": "ses_xxx",
  "part": {
    "id": "prt_xxx",
    "reason": "tool-calls",
    "messageID": "msg_xxx",
    "sessionID": "ses_xxx",
    "type": "step-finish",
    "tokens": { "total": 13213, "input": 13092, "output": 13, "reasoning": 44, "cache": { "write": 0, "read": 64 } },
    "cost": 0
  }
}
```

### chat.completed
```json
{
  "type": "chat.completed",
  "timestamp": 1777186690000,
  "sessionID": "ses_xxx"
}
```

对话结束标记。出现在所有 step_start/text/tool_use/step_finish 事件之后，表示此次对话的日志流已经完整结束。前端收到此事件后应关闭 SSE 连接。

## 增量日志机制

### 时间戳过滤

Flask `GET /api/chats/{chat_id}/stream` 支持查询参数 `after_ts`：

- **无 `after_ts`**：返回该会话的全部 opencode 日志（初次加载）
- **`after_ts=1777186675209`**：仅返回 `timestamp > after_ts` 的日志（增量监听）

### 流程

1. **初次加载**：前端调用 `[id].get.ts`（无 stream 参数）→ Nuxt 调用 Flask stream（无 after_ts）→ 获取全部日志 → 解析并记录最新 timestamp → 返回 JSON
2. **流式监听**：前端发送消息后，EventSource 连接 `[id].get.ts?stream=true&after_ts={最新timestamp}` → Nuxt 调用 Flask stream（带 after_ts）→ 仅获取新增日志 → 实时转换为 AI SDK 格式 SSE 推送

## opencode → AI SDK 流协议转换

在 Nuxt `[id].get.ts`（SSE 模式）中执行转换：

| opencode 事件 | AI SDK stream part |
|---|---|
| `step_start` | `{ type: 'step-start' }` |
| `text` | `{ type: 'text-delta', text: part.text }` |
| `tool_use` (input) | `{ type: 'tool-call', toolCallId: part.callID, toolName: part.tool, args: part.state.input }` |
| `tool_use` (output, status=completed) | `{ type: 'tool-result', toolCallId: part.callID, result: part.state.output }` |
| `step_finish` | `{ type: 'finish-step' }` |
| `chat.completed` | 结束 SSE 连接（不产生 stream part） |

## Flask Mock 服务改动

### POST /api/chats — 统一创建/继续对话

**请求体：**
```json
{
  "chat_id": "",       // 空 = 创建新会话，有值 = 继续对话
  "prompt": "用户输入"
}
```

**响应：**
```json
{
  "chat_id": "mock-7",
  "message_id": "msg-xxx"
}
```

**逻辑：**
- chat_id 为空：创建新会话（生成 mock-N id），生成 opencode 格式的日志（step_start + text/tool_use + step_finish + chat.completed）
- chat_id 有值：在已有会话中追加新的 opencode 日志
- **随机生成丰富内容**：每次调用随机决定回复包含哪些元素（纯文本、工具调用、多 step 等），以辅助前端验证各种场景
- 返回 chat_id 和新消息的 message_id

### GET /api/chats/{chat_id}/stream — 返回 opencode NDJSON（支持增量）

**查询参数：**
- `after_ts`（可选）：毫秒时间戳，仅返回 `timestamp > after_ts` 的日志

**响应：**
- Content-Type: `text/x-ndjson`
- 逐行推送，每行之间加 50-100ms 延迟模拟流式效果
- 最后一行为 `chat.completed`

**预置 mock 数据**也存储为 opencode 格式（不再是自定义的 messages 数组），初次加载时直接按 NDJSON 格式输出。

### GET /api/chats — 会话列表（不变）

## Nuxt server/api 层改动

### chats.post.ts — 统一对话入口

**接收：** `{ chat_id?: string, prompt: string }`

**处理：**
1. 调用 Flask `POST /api/chats`，传入 `{ chat_id, prompt }`
2. 返回 `{ chat_id: string, message_id: string }`

### [id].get.ts — 双模式（JSON 加载 + SSE 流式）

**无 `?stream` 参数（初次加载）：**
- 调用 Flask `GET /api/chats/{id}/stream`（无 after_ts）获取全部 NDJSON
- 解析所有 opencode 事件，转换为前端消息格式
- 记录最新 timestamp，包含在响应中供后续增量查询使用
- 返回 JSON：`{ id, title, createdAt, messages, lastTimestamp, isOwner: true }`

**`?stream=true&after_ts=xxx`（流式监听）：**
- 调用 Flask `GET /api/chats/{id}/stream?after_ts=xxx`
- 逐行解析 NDJSON 事件
- 实时转换为 AI SDK 流协议格式（通过 `createUIMessageStream`）
- 收到 `chat.completed` 时结束 SSE 连接
- 以 SSE 推送给前端

### [id].post.ts — 删除

不再需要独立的流式对话端点。

## 前端改动

### index.vue — 创建会话

- POST `{ prompt }` 到 `chats.post.ts`（无 chat_id）
- 拿到 `{ chat_id }` 后跳转 `/chat/{chat_id}`

### [id].vue — 聊天页面

保留 `@ai-sdk/vue` Chat 类，使用自定义 transport：

**Custom Transport 逻辑：**
1. `sendMessage(text)`:
   - POST `/api/v1/agent/chats`，body: `{ chat_id, prompt: text }`
   - 返回 `{ chat_id, message_id }`
2. 打开 EventSource 连接 `/api/v1/agent/chats/{chat_id}?stream=true&after_ts={lastTimestamp}`
3. 解析 SSE 事件流，通过 `createUIMessageStream` 解析为 Chat 类能消费的格式
4. 收到 `chat.completed` 对应的结束信号时关闭 EventSource
5. Chat 类自动更新 messages 数组和 streaming 状态

**`UChatMessages` 组件不变**，继续消费 `chat.messages` 和 `chat.status`。

## 文件改动清单

| 操作 | 文件 |
|------|------|
| 重写 | `scripts/python/server/mock_data.py` — 预置 mock 数据改为 opencode NDJSON 格式 + 随机生成逻辑 |
| 重写 | `scripts/python/server/app.py` — POST 统一入口 + stream 返回 NDJSON + after_ts 增量过滤 |
| 重写 | `server/api/v1/agent/chats.post.ts` — 统一对话入口 |
| 重写 | `server/api/v1/agent/chats/[id].get.ts` — 双模式 + 格式转换 + 增量日志 |
| 删除 | `server/api/v1/agent/chats/[id].post.ts` |
| 修改 | `app/pages/index.vue` — 适配新 POST 响应格式 |
| 修改 | `app/pages/chat/[id].vue` — 自定义 transport + lastTimestamp 管理 |

## 后续切换到真实业务接口

1. 将 Flask 地址改为真实业务地址
2. 真实业务接口返回 opencode NDJSON 格式，支持 `after_ts` 增量查询
3. 真实业务接口最后一行返回 `chat.completed`
4. Nuxt server 层的格式转换逻辑不变
