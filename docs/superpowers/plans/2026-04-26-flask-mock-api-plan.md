# Flask Mock API 替代数据库直接访问 — 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 Nuxt 项目中 chats/messages 的数据库直接访问替换为调用 Flask Mock API，使项目在不依赖本地数据库的情况下可运行。

**Architecture:** Flask Mock 服务在 5001 端口提供 3 个 REST 接口（创建会话、会话列表、SSE 流式对话），使用内存数据模拟。Nuxt server/api 层作为中间层调用 Flask，前端代码不变。

**Tech Stack:** Flask + flask-cors (Python mock 服务), Nuxt 4 + $fetch (server API 层)

---

## 文件结构

| 操作 | 文件路径 | 职责 |
|------|----------|------|
| 创建 | `scripts/python/server/requirements.txt` | Python 依赖 |
| 创建 | `scripts/python/server/mock_data.py` | Mock 数据和内存存储 |
| 创建 | `scripts/python/server/app.py` | Flask 路由和 SSE 流 |
| 修改 | `.env` | 添加 FLASK_API_URL |
| 修改 | `nuxt.config.ts` | 添加 runtimeConfig |
| 修改 | `server/db/schema.ts` | 删除 chats/messages 表定义 |
| 修改 | `server/routes/auth/github.get.ts` | 移除 chats 表引用 |
| 重写 | `server/api/v1/agent/chats.get.ts` | 调用 Flask 会话列表 |
| 重写 | `server/api/v1/agent/chats.post.ts` | 调用 Flask 创建会话 |
| 重写 | `server/api/v1/agent/chats/[id].get.ts` | 调用 Flask 获取会话详情 |
| 重写 | `server/api/v1/agent/chats/[id].post.ts` | 调用 Flask SSE 流 |
| 删除 | `server/api/v1/agent/chats/[id].delete.ts` | 不再需要 |

---

### Task 1: 创建 Flask Mock 服务 — requirements.txt 和 mock_data.py

**Files:**
- Create: `scripts/python/server/requirements.txt`
- Create: `scripts/python/server/mock_data.py`

- [ ] **Step 1: 创建 requirements.txt**

```txt
flask==3.1.0
flask-cors==5.0.1
```

- [ ] **Step 2: 创建 mock_data.py**

这个文件包含预置的 5 条 mock 会话数据（与当前 Nuxt 中硬编码的数据一致），以及内存存储的管理逻辑。

```python
import json
import uuid
from datetime import datetime, timezone, timedelta

def _now():
    return datetime.now(timezone.utc)

def _iso(dt):
    return dt.isoformat()

# --- 预置数据 ---

now = _now()
yesterday = now - timedelta(days=1)
two_days_ago = now - timedelta(days=2)
last_week = now - timedelta(days=5)
last_month = now - timedelta(days=20)

INITIAL_CHATS = [
    {"id": "mock-1", "chat_id": "mock-1", "title": "【Text】纯文本对话", "createdAt": _iso(now)},
    {"id": "mock-2", "chat_id": "mock-2", "title": "【Reasoning】带思考链的回答", "createdAt": _iso(yesterday)},
    {"id": "mock-3", "chat_id": "mock-3", "title": "【File】带图片附件的对话", "createdAt": _iso(two_days_ago)},
    {"id": "mock-4", "chat_id": "mock-4", "title": "【Source URL】带来源引用的回答", "createdAt": _iso(last_week)},
    {"id": "mock-6", "chat_id": "mock-6", "title": "【综合】多步骤工具调用 + 思考链 + 来源文档 + 图表", "createdAt": _iso(last_month)},
]

INITIAL_MESSAGES = {
    "mock-1": [
        {
            "id": "msg-1-1", "chatId": "mock-1", "role": "user",
            "parts": [{"type": "text", "text": "How do I use Nuxt UI components?"}],
            "createdAt": _iso(now)
        },
        {
            "id": "msg-1-2", "chatId": "mock-1", "role": "assistant",
            "parts": [{"type": "text", "text": "Nuxt UI provides a set of Vue components that you can use directly in your templates. Install it with `npx nuxi module add @nuxt/ui`, then use components like `<UButton>`, `<UInput>`, `<UModal>`, etc. in your pages."}],
            "createdAt": _iso(now)
        }
    ],
    "mock-2": [
        {
            "id": "msg-2-1", "chatId": "mock-2", "role": "user",
            "parts": [{"type": "text", "text": "Can you think step by step: what is 15% of 240?"}],
            "createdAt": _iso(yesterday)
        },
        {
            "id": "msg-2-2", "chatId": "mock-2", "role": "assistant",
            "parts": [
                {"type": "reasoning", "text": "Let me calculate 15% of 240.\n\nStep 1: Convert 15% to decimal \u2192 0.15\nStep 2: Multiply 240 \u00d7 0.15\nStep 3: 240 \u00d7 0.15 = 36\n\nSo the answer is 36."},
                {"type": "text", "text": "15% of 240 is **36**.\n\nHere's how I calculated it:\n- 15% = 0.15\n- 240 \u00d7 0.15 = 36"}
            ],
            "createdAt": _iso(yesterday)
        }
    ],
    "mock-3": [
        {
            "id": "msg-3-1", "chatId": "mock-3", "role": "user",
            "parts": [
                {"type": "text", "text": "What does this screenshot show?"},
                {"type": "file", "mediaType": "image/png", "filename": "dashboard.png", "url": "https://placehold.co/600x400/png"}
            ],
            "createdAt": _iso(two_days_ago)
        },
        {
            "id": "msg-3-2", "chatId": "mock-3", "role": "assistant",
            "parts": [{"type": "text", "text": "This screenshot shows a dashboard with charts and metrics. I can see what appears to be a data visualization interface with line charts and summary cards."}],
            "createdAt": _iso(two_days_ago)
        },
        {
            "id": "msg-3-3", "chatId": "mock-3", "role": "user",
            "parts": [
                {"type": "text", "text": "Here's the PDF report as well"},
                {"type": "file", "mediaType": "application/pdf", "filename": "report-2024.pdf", "url": "https://placehold.co/600x400/png"}
            ],
            "createdAt": _iso(two_days_ago)
        },
        {
            "id": "msg-3-4", "chatId": "mock-3", "role": "assistant",
            "parts": [{"type": "text", "text": "Thanks for sharing the PDF report. I've reviewed it and the data aligns with what we see in the dashboard screenshot."}],
            "createdAt": _iso(two_days_ago)
        }
    ],
    "mock-4": [
        {
            "id": "msg-4-1", "chatId": "mock-4", "role": "user",
            "parts": [{"type": "text", "text": "What are the latest features in Vue 3.5?"}],
            "createdAt": _iso(last_week)
        },
        {
            "id": "msg-4-2", "chatId": "mock-4", "role": "assistant",
            "parts": [
                {"type": "text", "text": "Vue 3.5 introduced several exciting features:\n\n1. **Reactive Props Destructure** \u2014 You can now destructure props in `<script setup>` without losing reactivity.\n2. **useTemplateRef()** \u2014 A new composable to get template refs.\n3. **Deferred Teleport** \u2014 Teleport supports deferred mounting.\n4. **useId()** \u2014 Generate unique IDs for SSR-friendly accessibility.\n\n"},
                {"type": "source-url", "sourceId": "src-1", "url": "https://blog.vuejs.org/posts/vue-3-5", "title": "Vue 3.5 Release Blog Post"},
                {"type": "source-url", "sourceId": "src-2", "url": "https://vuejs.org/api/", "title": "Vue.js API Reference"}
            ],
            "createdAt": _iso(last_week)
        }
    ],
    "mock-6": [
        {
            "id": "msg-6-1", "chatId": "mock-6", "role": "user",
            "parts": [
                {"type": "text", "text": "Analyze the sales data and create a chart showing the trend."},
                {"type": "file", "mediaType": "text/csv", "filename": "sales-2024.csv", "url": "https://placehold.co/600x200/png"}
            ],
            "createdAt": _iso(last_month)
        },
        {
            "id": "msg-6-2", "chatId": "mock-6", "role": "assistant",
            "parts": [
                {"type": "step-start"},
                {"type": "reasoning", "text": "The user has uploaded a CSV file with sales data. I need to:\n1. Analyze the data in the CSV\n2. Identify trends and patterns\n3. Create a line chart visualization\n4. Provide a summary with source references"},
                {"type": "text", "text": "I'll analyze the sales data from your CSV file and create a visualization."},
                {
                    "type": "tool-createChart",
                    "toolCallId": "call-chart-1",
                    "state": "output-available",
                    "input": {
                        "title": "Monthly Sales Trend 2024",
                        "data": [
                            {"month": "Jan", "revenue": 42000, "profit": 12600},
                            {"month": "Feb", "revenue": 38500, "profit": 10780},
                            {"month": "Mar", "revenue": 51200, "profit": 16384},
                            {"month": "Apr", "revenue": 47800, "profit": 14340},
                            {"month": "May", "revenue": 55600, "profit": 18120},
                            {"month": "Jun", "revenue": 62300, "profit": 21760}
                        ],
                        "xKey": "month",
                        "series": [
                            {"key": "revenue", "name": "Revenue", "color": "#3b82f6"},
                            {"key": "profit", "name": "Profit", "color": "#10b981"}
                        ],
                        "xLabel": "Month",
                        "yLabel": "Amount (USD)"
                    },
                    "output": {
                        "title": "Monthly Sales Trend 2024",
                        "data": [
                            {"month": "Jan", "revenue": 42000, "profit": 12600},
                            {"month": "Feb", "revenue": 38500, "profit": 10780},
                            {"month": "Mar", "revenue": 51200, "profit": 16384},
                            {"month": "Apr", "revenue": 47800, "profit": 14340},
                            {"month": "May", "revenue": 55600, "profit": 18120},
                            {"month": "Jun", "revenue": 62300, "profit": 21760}
                        ],
                        "xKey": "month",
                        "series": [
                            {"key": "revenue", "name": "Revenue", "color": "#3b82f6"},
                            {"key": "profit", "name": "Profit", "color": "#10b981"}
                        ],
                        "xLabel": "Month",
                        "yLabel": "Amount (USD)"
                    }
                },
                {"type": "text", "text": "\nHere's the analysis of your sales data:\n\n**Key Findings:**\n- Revenue shows a general **upward trend** from January to June\n- February had the lowest revenue at $38,500\n- June was the strongest month with $62,300 in revenue\n- Profit margins averaged around 30% across all months\n\nThe chart above visualizes the monthly revenue and profit trends."},
                {"type": "source-document", "sourceId": "doc-1", "mediaType": "text/csv", "title": "Sales Data 2024", "filename": "sales-2024.csv"},
                {"type": "source-url", "sourceId": "src-1", "url": "https://example.com/sales-analytics-methodology", "title": "Sales Analytics Methodology"}
            ],
            "createdAt": _iso(last_month)
        }
    ],
}

# --- 内存存储 ---

# 用可变列表/字典，运行时可追加
chats_store = list(INITIAL_CHATS)
messages_store = dict(INITIAL_MESSAGES)
_next_id = 7  # 下一个可用 id 编号


def get_all_chats():
    """返回所有会话，按创建时间倒序"""
    return sorted(chats_store, key=lambda c: c["createdAt"], reverse=True)


def get_chat(chat_id):
    """根据 id 查找会话，返回 (chat, messages) 或 (None, None)"""
    chat = next((c for c in chats_store if c["id"] == chat_id), None)
    if not chat:
        return None, None
    messages = messages_store.get(chat_id, [])
    return chat, messages


def create_chat(prompt_text):
    """创建新会话 + mock 回复，返回 chat 对象"""
    global _next_id
    chat_id = f"mock-{_next_id}"
    _next_id += 1

    now_iso = _iso(_now())
    title = prompt_text[:20] if prompt_text else "新会话"

    chat = {
        "id": chat_id,
        "chat_id": chat_id,
        "title": title,
        "createdAt": now_iso,
    }
    chats_store.insert(0, chat)

    # 创建用户消息
    user_msg = {
        "id": str(uuid.uuid4()),
        "chatId": chat_id,
        "role": "user",
        "parts": [{"type": "text", "text": prompt_text}],
        "createdAt": now_iso,
    }

    # 创建 mock 助手回复
    assistant_msg = {
        "id": str(uuid.uuid4()),
        "chatId": chat_id,
        "role": "assistant",
        "parts": [{"type": "text", "text": f"收到您的消息：「{prompt_text}」\n\n这是一个模拟回复。在实际部署中，这里会是对接真实业务系统后的 AI 回复。"}],
        "createdAt": _iso(_now()),
    }

    messages_store[chat_id] = [user_msg, assistant_msg]

    return chat
```

- [ ] **Step 3: 提交**

```bash
git add scripts/python/server/requirements.txt scripts/python/server/mock_data.py
git commit -m "feat: add Flask mock data and requirements"
```

---

### Task 2: 创建 Flask 主应用 app.py

**Files:**
- Create: `scripts/python/server/app.py`

- [ ] **Step 1: 创建 app.py**

包含 3 个路由：POST /api/chats（创建会话）、GET /api/chats（会话列表）、GET /api/chats/\<chat_id\>/stream（SSE 流式对话）。

```python
import json
import time
from flask import Flask, jsonify, request, Response
from flask_cors import CORS
from mock_data import get_all_chats, get_chat, create_chat

app = Flask(__name__)
CORS(app)


@app.route("/api/chats", methods=["GET"])
def list_chats():
    """会话列表"""
    return jsonify(get_all_chats())


@app.route("/api/chats", methods=["POST"])
def new_chat():
    """创建会话"""
    body = request.get_json(force=True)
    prompt = body.get("message", "") or body.get("prompt", "")
    chat = create_chat(prompt)
    return jsonify(chat)


@app.route("/api/chats/<chat_id>/stream", methods=["GET"])
def stream_chat(chat_id):
    """SSE 流式返回会话的所有消息"""
    chat, messages = get_chat(chat_id)
    if not chat:
        return jsonify({"error": "Chat not found"}), 404

    def generate():
        for msg in messages:
            event_data = json.dumps(msg, ensure_ascii=False)
            yield f"event: message\ndata: {event_data}\n\n"
            time.sleep(0.08)  # 80ms 延迟模拟流式效果
        yield "event: done\ndata: {}\n\n"

    return Response(generate(), mimetype="text/event-stream")


if __name__ == "__main__":
    app.run(port=5001, debug=True)
```

- [ ] **Step 2: 启动 Flask 验证接口**

Run: `cd scripts/python/server && pip install -r requirements.txt && python app.py`

在另一个终端中测试：
```bash
curl http://localhost:5001/api/chats
curl -X POST http://localhost:5001/api/chats -H "Content-Type: application/json" -d '{"message":"测试创建会话"}'
curl http://localhost:5001/api/chats/mock-1/stream
```

Expected: 三个接口都返回正确的 JSON/SSE 数据。

- [ ] **Step 3: 提交**

```bash
git add scripts/python/server/app.py
git commit -m "feat: add Flask mock API server with 3 endpoints"
```

---

### Task 3: 配置 Nuxt runtimeConfig 和 .env

**Files:**
- Modify: `.env`
- Modify: `nuxt.config.ts`

- [ ] **Step 1: 在 .env 中添加 FLASK_API_URL**

在 `.env` 文件末尾追加：

```
FLASK_API_URL=http://localhost:5001
```

- [ ] **Step 2: 在 nuxt.config.ts 中添加 runtimeConfig**

在 `nuxt.config.ts` 的 `defineNuxtConfig` 中添加 `runtimeConfig` 字段。放在 `compatibilityDate` 之后：

```typescript
  runtimeConfig: {
    flaskApiUrl: process.env.FLASK_API_URL || 'http://localhost:5001'
  },
```

- [ ] **Step 3: 提交**

```bash
git add .env nuxt.config.ts
git commit -m "feat: add FLASK_API_URL runtime config"
```

---

### Task 4: 清理 schema.ts — 删除 chats/messages 表定义

**Files:**
- Modify: `server/db/schema.ts`

- [ ] **Step 1: 重写 schema.ts，只保留 users 表**

将 `server/db/schema.ts` 的全部内容替换为：

```typescript
import { sqliteTable, text, integer, uniqueIndex } from 'drizzle-orm/sqlite-core'
import { relations } from 'drizzle-orm'

const timestamps = {
  createdAt: integer('created_at', { mode: 'timestamp' }).notNull().$defaultFn(() => new Date())
}

export const users = sqliteTable('users', {
  id: text('id').primaryKey().$defaultFn(() => crypto.randomUUID()),
  email: text('email').notNull(),
  name: text('name').notNull(),
  avatar: text('avatar').notNull(),
  username: text('username').notNull(),
  provider: text('provider', { enum: ['github'] }).notNull(),
  providerId: text('provider_id').notNull(),
  ...timestamps
}, table => [
  uniqueIndex('users_provider_id_idx').on(table.provider, table.providerId)
])

export const usersRelations = relations(users, ({}) => ({}))
```

注意：`usersRelations` 中移除了对 `chats` 的 `many` 引用。`relations` 的回调参数改为空解构 `({})`，返回空对象 `({})`。

- [ ] **Step 2: 提交**

```bash
git add server/db/schema.ts
git commit -m "refactor: remove chats and messages table definitions from schema"
```

---

### Task 5: 修复 auth/github.get.ts — 移除 chats 表引用

**Files:**
- Modify: `server/routes/auth/github.get.ts`

- [ ] **Step 1: 移除 chats 相关的数据库操作**

将 `server/routes/auth/github.get.ts` 的全部内容替换为：

```typescript
import { db, schema } from 'hub:db'
import { and, eq } from 'drizzle-orm'

export default defineOAuthGitHubEventHandler({
  async onSuccess(event, { user: ghUser }) {
    const session = await getUserSession(event)

    let user = await db.query.users.findFirst({
      where: () => and(
        eq(schema.users.provider, 'github'),
        eq(schema.users.providerId, ghUser.id.toString())
      )
    })
    if (!user) {
      [user] = await db.insert(schema.users).values({
        id: session.id,
        name: ghUser.name || '',
        email: ghUser.email || '',
        avatar: ghUser.avatar_url || '',
        username: ghUser.login,
        provider: 'github',
        providerId: ghUser.id.toString()
      }).returning()
    }

    await setUserSession(event, { user })

    return sendRedirect(event, '/')
  },
  onError(event, error) {
    console.error('GitHub OAuth error:', error)
    return sendRedirect(event, '/')
  }
})
```

变更说明：移除了 `else` 分支中 `db.update(schema.chats).set({ userId }).where(...)` 的操作，因为 chats 表不再存在。用户登录后只做 user 记录的查找/创建。

- [ ] **Step 2: 提交**

```bash
git add server/routes/auth/github.get.ts
git commit -m "refactor: remove chats table reference from GitHub OAuth handler"
```

---

### Task 6: 重写 chats.get.ts — 调用 Flask 会话列表

**Files:**
- Modify: `server/api/v1/agent/chats.get.ts`

- [ ] **Step 1: 重写为调用 Flask API**

将 `server/api/v1/agent/chats.get.ts` 的全部内容替换为：

```typescript
export default defineEventHandler(async () => {
  const config = useRuntimeConfig()
  const res = await $fetch<{ id: string, chat_id: string, title: string | null, createdAt: string }[]>(
    `${config.flaskApiUrl}/api/chats`
  )
  return res.map(chat => ({
    ...chat,
    userId: 'mock-user',
    createdAt: new Date(chat.createdAt)
  }))
})
```

说明：Flask 返回的 `createdAt` 是 ISO 字符串，这里转为 `Date` 对象以匹配前端 `Chat` 类的预期。补充 `userId` 字段保持兼容。

- [ ] **Step 2: 提交**

```bash
git add server/api/v1/agent/chats.get.ts
git commit -m "refactor: chats list endpoint calls Flask API instead of mock data"
```

---

### Task 7: 重写 chats.post.ts — 调用 Flask 创建会话

**Files:**
- Modify: `server/api/v1/agent/chats.post.ts`

- [ ] **Step 1: 重写为调用 Flask API**

注意观察 `app/pages/index.vue` 中前端发送的请求体格式：

```typescript
// index.vue 第 29-37 行
body: {
  app_name: "BuildMateWeb",
  app_chat_id: chatId,
  prompt: prompt,
}
```

前端发送 `prompt` 字段（不是 `message`）。需要从请求体提取 `prompt`，传给 Flask 的 `message` 字段。

将 `server/api/v1/agent/chats.post.ts` 的全部内容替换为：

```typescript
import { z } from 'zod'

export default defineEventHandler(async (event) => {
  const body = await readValidatedBody(event, z.object({
    app_name: z.string().optional(),
    app_chat_id: z.string().optional(),
    prompt: z.string()
  }).parse)

  const config = useRuntimeConfig()
  const chat = await $fetch<{
    id: string
    chat_id: string
    title: string | null
    createdAt: string
  }>(`${config.flaskApiUrl}/api/chats`, {
    method: 'POST',
    body: { message: body.prompt }
  })

  return chat
})
```

- [ ] **Step 2: 提交**

```bash
git add server/api/v1/agent/chats.post.ts
git commit -m "refactor: create chat endpoint calls Flask API instead of database"
```

---

### Task 8: 重写 [id].get.ts — 调用 Flask 获取会话详情

**Files:**
- Modify: `server/api/v1/agent/chats/[id].get.ts`

- [ ] **Step 1: 重写为调用 Flask SSE 接口收集消息**

将 `server/api/v1/agent/chats/[id].get.ts` 的全部内容替换为：

```typescript
import { z } from 'zod'

interface FlaskMessage {
  id: string
  chatId: string
  role: 'user' | 'assistant' | 'system'
  parts: any[]
  createdAt: string
}

interface FlaskChat {
  id: string
  chat_id: string
  title: string | null
  createdAt: string
}

export default defineEventHandler(async (event) => {
  const { id } = await getValidatedRouterParams(event, z.object({
    id: z.string()
  }).parse)

  const config = useRuntimeConfig()

  // 先从会话列表中找到该会话的 title
  const chats = await $fetch<FlaskChat[]>(`${config.flaskApiUrl}/api/chats`)
  const chat = chats.find(c => c.id === id || c.chat_id === id)

  if (!chat) {
    throw createError({ statusCode: 404, statusMessage: 'Chat not found' })
  }

  // 调用 SSE 接口收集所有消息
  const messages: FlaskMessage[] = []

  const response = await fetch(`${config.flaskApiUrl}/api/chats/${id}/stream`)
  if (!response.ok) {
    throw createError({ statusCode: response.status, statusMessage: 'Chat not found' })
  }

  const reader = response.body?.getReader()
  if (!reader) {
    throw createError({ statusCode: 500, statusMessage: 'Failed to read stream' })
  }

  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() || ''

    let currentEvent = ''
    for (const line of lines) {
      if (line.startsWith('event: ')) {
        currentEvent = line.slice(7).trim()
      } else if (line.startsWith('data: ') && currentEvent === 'message') {
        const data = line.slice(6)
        try {
          const msg = JSON.parse(data) as FlaskMessage
          messages.push({
            ...msg,
            createdAt: msg.createdAt
          })
        } catch {
          // 忽略解析错误
        }
        currentEvent = ''
      }
    }
  }

  return {
    id: chat.id,
    title: chat.title,
    createdAt: chat.createdAt,
    messages,
    isOwner: true
  }
})
```

说明：这个接口通过读取 Flask SSE 流来收集所有消息，然后作为普通 JSON 一次性返回给前端。前端通过 `useFetch` 调用此接口，不支持流式（流式在 `[id].post.ts` 处理）。

- [ ] **Step 2: 提交**

```bash
git add server/api/v1/agent/chats/[id].get.ts
git commit -m "refactor: chat detail endpoint calls Flask API instead of mock data"
```

---

### Task 9: 重写 [id].post.ts — 调用 Flask SSE 流式对话

**Files:**
- Modify: `server/api/v1/agent/chats/[id].post.ts`

这是最复杂的改动。前端通过 `DefaultChatTransport` POST 到此端点，期望收到 AI SDK 流协议格式（`createUIMessageStreamResponse`）。需要：
1. 接收前端的 POST 请求
2. 调用 Flask SSE 接口获取 mock 消息
3. 将 mock 消息转换为 AI SDK 流协议格式返回给前端

- [ ] **Step 1: 重写为调用 Flask 并转换流格式**

将 `server/api/v1/agent/chats/[id].post.ts` 的全部内容替换为：

```typescript
import { createUIMessageStream, createUIMessageStreamResponse } from 'ai'
import { z } from 'zod'

interface FlaskMessage {
  id: string
  chatId: string
  role: 'user' | 'assistant' | 'system'
  parts: any[]
  createdAt: string
}

export default defineEventHandler(async (event) => {
  const { id } = await getValidatedRouterParams(event, z.object({
    id: z.string()
  }).parse)

  const config = useRuntimeConfig()

  const stream = createUIMessageStream({
    execute: async ({ writer }) => {
      // 调用 Flask SSE 接口获取 mock 消息
      const response = await fetch(`${config.flaskApiUrl}/api/chats/${id}/stream`)
      if (!response.ok) {
        throw createError({ statusCode: response.status, statusMessage: 'Chat not found' })
      }

      const reader = response.body?.getReader()
      if (!reader) {
        throw createError({ statusCode: 500, statusMessage: 'Failed to read stream' })
      }

      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        let currentEvent = ''
        for (const line of lines) {
          if (line.startsWith('event: ')) {
            currentEvent = line.slice(7).trim()
          } else if (line.startsWith('data: ')) {
            if (currentEvent === 'message') {
              const data = line.slice(6)
              try {
                const msg = JSON.parse(data) as FlaskMessage

                if (msg.role === 'assistant') {
                  // 将 assistant 消息的 parts 转换为 AI SDK 流协议
                  writer.write({
                    type: 'message',
                    role: 'assistant',
                    id: msg.id,
                    parts: msg.parts
                  })
                }
              } catch {
                // 忽略解析错误
              }
            }
            currentEvent = ''
          }
        }
      }
    }
  })

  return createUIMessageStreamResponse({ stream })
})
```

说明：
- 使用 `createUIMessageStream` + `createUIMessageStreamResponse` 来创建 AI SDK 兼容的流响应
- 从 Flask SSE 收集消息后，只将 `assistant` 角色的消息通过 `writer.write()` 推送给前端
- `writer.write({ type: 'message', role: 'assistant', id, parts })` 是 AI SDK 6.x 的 UI message stream 协议格式
- 前端 `DefaultChatTransport` 能正确解析此格式

- [ ] **Step 2: 提交**

```bash
git add server/api/v1/agent/chats/[id].post.ts
git commit -m "refactor: chat streaming endpoint calls Flask API with AI SDK stream conversion"
```

---

### Task 10: 删除 [id].delete.ts

**Files:**
- Delete: `server/api/v1/agent/chats/[id].delete.ts`

- [ ] **Step 1: 删除文件**

```bash
rm server/api/v1/agent/chats/[id].delete.ts
```

- [ ] **Step 2: 提交**

```bash
git add -u server/api/v1/agent/chats/[id].delete.ts
git commit -m "refactor: remove chat delete endpoint (no longer needed)"
```

---

### Task 11: 端到端验证

- [ ] **Step 1: 启动 Flask Mock 服务**

```bash
cd scripts/python/server && pip install -r requirements.txt && python app.py
```

Expected: Flask 在 5001 端口启动，无报错。

- [ ] **Step 2: 在另一个终端启动 Nuxt 开发服务器**

```bash
cd D:/codes/BuildMate/chat && pnpm dev
```

Expected: Nuxt 在默认端口启动，无编译错误。

- [ ] **Step 3: 验证会话列表**

浏览器打开 Nuxt 应用，检查左侧边栏是否显示 5 条 mock 会话。

Expected: 5 条会话标题正确显示。

- [ ] **Step 4: 验证会话详情**

点击任一会话，检查消息是否正确显示。

Expected: 消息内容、reasoning、文件附件、来源引用等都正确渲染。

- [ ] **Step 5: 验证创建会话**

在首页输入框输入文本并提交，检查是否创建新会话并跳转。

Expected: 新会话创建成功，跳转到 `/chat/mock-7`（或下一个 id）。

- [ ] **Step 6: 提交最终状态**

如果有任何热修复，在此提交。

---

## Self-Review

**1. Spec coverage:**
- Flask 3 个接口：Task 1-2 ✓
- Nuxt runtimeConfig：Task 3 ✓
- schema.ts 清理：Task 4 ✓
- auth/github.get.ts 修复：Task 5 ✓
- chats.get.ts：Task 6 ✓
- chats.post.ts：Task 7 ✓
- [id].get.ts：Task 8 ✓
- [id].post.ts：Task 9 ✓
- [id].delete.ts 删除：Task 10 ✓
- 端到端验证：Task 11 ✓

**2. Placeholder scan:** 无 TBD、TODO、fill in details。所有代码步骤都有完整代码。

**3. Type consistency:**
- Flask 返回的 Chat 对象字段（id, chat_id, title, createdAt）在 Task 6-8 中使用一致
- Flask 返回的 Message 对象字段（id, chatId, role, parts, createdAt）在 Task 8-9 中使用一致
- `FlaskMessage` 和 `FlaskChat` interface 在 Task 8 和 Task 9 中定义一致
- AI SDK 流协议 `writer.write({ type: 'message', role, id, parts })` 格式与 `createUIMessageStream` 兼容
