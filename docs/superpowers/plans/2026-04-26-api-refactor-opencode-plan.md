# API 重构：统一对话入口 + opencode 格式转换 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 Flask Mock API 改为 opencode NDJSON 格式输出，Nuxt server 层做 opencode→AI SDK 格式转换，统一对话入口，支持增量日志和对话完成标记。

**Architecture:** Flask 作为 mock 后端返回 opencode NDJSON 格式流（与 `opencode --format json run` 一致）。Nuxt server/api 层作为中间层，`chats.post.ts` 统一处理创建/继续对话，`[id].get.ts` 双模式运行（JSON 初次加载 + SSE 流式推送），实时将 opencode 事件转换为 AI SDK stream parts。前端保留 `@ai-sdk/vue` Chat 类，通过自定义 transport 对接。

**Tech Stack:** Python/Flask (mock), Nuxt 4, AI SDK 6.x (`@ai-sdk/vue`, `createUIMessageStream`), TypeScript, SSE/EventSource

---

## File Structure

| Operation | File | Responsibility |
|-----------|------|----------------|
| Rewrite | `scripts/python/server/mock_data.py` | opencode NDJSON 格式存储 + 随机生成逻辑 |
| Rewrite | `scripts/python/server/app.py` | 统一 POST + NDJSON stream + after_ts 增量过滤 |
| Rewrite | `server/api/v1/agent/chats.post.ts` | 统一对话入口（创建/继续） |
| Rewrite | `server/api/v1/agent/chats/[id].get.ts` | 双模式 + opencode→AI SDK 格式转换 + 增量日志 |
| Delete | `server/api/v1/agent/chats/[id].post.ts` | 不再需要独立流式端点 |
| Modify | `app/pages/index.vue` | 适配新 POST 响应格式 |
| Modify | `app/pages/chat/[id].vue` | 自定义 transport + lastTimestamp 管理 |

---

### Task 1: 重写 mock_data.py — opencode NDJSON 格式存储 + 随机生成

**Files:**
- Rewrite: `scripts/python/server/mock_data.py`

**Context:** 当前 `mock_data.py` 使用自定义 messages 数组格式存储预设数据。需要改为 opencode NDJSON 格式。每个会话存储为一个 NDJSON 行列表（每行一个 JSON 对象）。随机生成逻辑需要在每次创建/继续对话时生成丰富多样的内容（纯文本、工具调用、多 step 等）。

- [ ] **Step 1: 重写 mock_data.py**

```python
import json
import uuid
import random
from datetime import datetime, timezone, timedelta


def _now():
    return datetime.now(timezone.utc)


def _iso(dt):
    return dt.isoformat()


def _ts():
    """毫秒时间戳"""
    return int(_now().timestamp() * 1000)


def _uid(prefix=""):
    return f"{prefix}{uuid.uuid4().hex[:20]}"


# --- opencode NDJSON 辅助函数 ---

def make_step_start(session_id, message_id, timestamp=None):
    return {
        "type": "step_start",
        "timestamp": timestamp or _ts(),
        "sessionID": session_id,
        "part": {
            "id": _uid("prt_"),
            "messageID": message_id,
            "sessionID": session_id,
            "snapshot": uuid.uuid4().hex[:40],
            "type": "step-start"
        }
    }


def make_text(session_id, message_id, text, timestamp=None):
    now = _ts()
    return {
        "type": "text",
        "timestamp": timestamp or now,
        "sessionID": session_id,
        "part": {
            "id": _uid("prt_"),
            "messageID": message_id,
            "sessionID": session_id,
            "type": "text",
            "text": text,
            "time": {"start": now - random.randint(100, 1500), "end": now}
        }
    }


def make_tool_use(session_id, message_id, tool_name, call_id, input_data, output_data, title="", timestamp=None):
    now = _ts()
    return {
        "type": "tool_use",
        "timestamp": timestamp or now,
        "sessionID": session_id,
        "part": {
            "type": "tool",
            "tool": tool_name,
            "callID": call_id,
            "state": {
                "status": "completed",
                "input": input_data,
                "output": output_data
            },
            "id": _uid("prt_"),
            "messageID": message_id,
            "sessionID": session_id,
            "title": title,
            "time": {"start": now - random.randint(100, 5000), "end": now}
        }
    }


def make_step_finish(session_id, message_id, reason="end-turn", timestamp=None):
    now = _ts()
    return {
        "type": "step_finish",
        "timestamp": timestamp or now,
        "sessionID": session_id,
        "part": {
            "id": _uid("prt_"),
            "reason": reason,
            "messageID": message_id,
            "sessionID": session_id,
            "type": "step-finish",
            "tokens": {
                "total": random.randint(5000, 20000),
                "input": random.randint(4000, 18000),
                "output": random.randint(50, 2000),
                "reasoning": random.randint(0, 500),
                "cache": {"write": 0, "read": random.randint(0, 5000)}
            },
            "cost": 0
        }
    }


def make_chat_completed(session_id, timestamp=None):
    return {
        "type": "chat.completed",
        "timestamp": timestamp or _ts(),
        "sessionID": session_id
    }


# --- 随机内容生成器 ---

REPLY_TEMPLATES = [
    # 纯文本回复
    {
        "weight": 3,
        "generate": lambda prompt: [
            ("text", f"收到您的消息：「{prompt}」\n\n这是一个模拟回复，用于验证纯文本场景。在实际部署中，这里会是对接真实业务系统后的 AI 回复。")
        ]
    },
    # bash 工具调用 + 文本
    {
        "weight": 2,
        "generate": lambda prompt: [
            ("tool", {
                "tool": "bash",
                "title": f"执行查询: {prompt[:30]}",
                "input": {"command": f"echo 'processing: {prompt[:50]}'"},
                "output": f"processing: {prompt[:50]}\nDone.\n"
            }),
            ("text", f"已执行命令处理您的请求：「{prompt}」。结果显示操作成功完成。")
        ]
    },
    # 多工具调用 + 文本
    {
        "weight": 2,
        "generate": lambda prompt: [
            ("tool", {
                "tool": "bash",
                "title": "检查环境信息",
                "input": {"command": "uname -a"},
                "output": "Linux buildmate 5.15.0 #1 SMP x86_64 GNU/Linux\n"
            }),
            ("tool", {
                "tool": "bash",
                "title": "查询相关文件",
                "input": {"command": f"find . -name '*.ts' | head -5"},
                "output": "./server/api/v1/agent/chats.get.ts\n./server/api/v1/agent/chats.post.ts\n"
            }),
            ("text", f"根据环境检查和文件扫描的结果，关于「{prompt}」的处理已经完成。系统运行正常，相关文件已定位。")
        ]
    },
    # 多 step：第一步工具调用，第二步文本总结
    {
        "weight": 2,
        "generate": lambda prompt: [
            # step 1: tool calls
            ("step_break", None),
            ("tool", {
                "tool": "bash",
                "title": "分析需求",
                "input": {"command": f"echo 'analyzing: {prompt[:60]}'"},
                "output": f"Analysis complete for: {prompt[:60]}\n3 key points found.\n"
            }),
            # step 2: text summary
            ("step_break", None),
            ("text", f"经过分析，关于「{prompt}」的回复如下：\n\n1. 第一要点：系统已正确理解您的需求\n2. 第二要点：相关资源已准备就绪\n3. 第三要点：建议下一步操作可以继续提问\n\n如有更多问题，请继续输入。")
        ]
    },
    # glob + read 工具 + 详细文本
    {
        "weight": 1,
        "generate": lambda prompt: [
            ("tool", {
                "tool": "glob",
                "title": "搜索相关文件",
                "input": {"pattern": "**/*.{ts,vue}"},
                "output": "Found 15 matching files.\n"
            }),
            ("tool", {
                "tool": "read",
                "title": "读取配置文件",
                "input": {"filePath": "nuxt.config.ts"},
                "output": "// Nuxt config content\nexport default defineNuxtConfig({})\n"
            }),
            ("text", f"已搜索并读取相关文件。关于「{prompt}」，以下是详细分析：\n\n**文件搜索结果**：找到 15 个相关文件。\n\n**配置检查**：项目配置正常。\n\n建议您可以根据这些信息进行下一步操作。")
        ]
    },
]


def generate_opencode_logs(session_id, message_id, prompt):
    """随机生成一组 opencode 格式的日志行"""
    template = random.choices(
        REPLY_TEMPLATES,
        weights=[t["weight"] for t in REPLY_TEMPLATES]
    )[0]

    items = template["generate"](prompt)
    lines = []
    current_ts = _ts() - random.randint(5000, 10000)

    def next_ts():
        nonlocal current_ts
        current_ts += random.randint(200, 2000)
        return current_ts

    step_items = []
    for item in items:
        if item[0] == "step_break":
            if step_items:
                step_items = []
            continue
        step_items.append(item)

    # 分组到 steps
    steps = []
    current_step = []
    for item in items:
        if item[0] == "step_break":
            if current_step:
                steps.append(current_step)
                current_step = []
        else:
            current_step.append(item)
    if current_step:
        steps.append(current_step)

    for step_items in steps:
        lines.append(make_step_start(session_id, message_id, next_ts()))
        for kind, content in step_items:
            if kind == "text":
                lines.append(make_text(session_id, message_id, content, next_ts()))
            elif kind == "tool":
                call_id = _uid("call_")
                lines.append(make_tool_use(
                    session_id, message_id,
                    content["tool"], call_id,
                    content["input"], content["output"],
                    content.get("title", ""),
                    next_ts()
                ))
        lines.append(make_step_finish(
            session_id, message_id,
            reason="tool-calls" if any(i[0] == "tool" for i in step_items) else "end-turn",
            timestamp=next_ts()
        ))

    lines.append(make_chat_completed(session_id, next_ts()))
    return lines


# --- 预置数据 ---

now = _now()
yesterday = now - timedelta(days=1)
two_days_ago = now - timedelta(days=2)
last_week = now - timedelta(days=5)
last_month = now - timedelta(days=20)

INITIAL_CHATS = [
    {"id": "mock-1", "chat_id": "mock-1", "title": "纯文本对话", "createdAt": _iso(now)},
    {"id": "mock-2", "chat_id": "mock-2", "title": "工具调用示例", "createdAt": _iso(yesterday)},
    {"id": "mock-3", "chat_id": "mock-3", "title": "多步骤对话", "createdAt": _iso(two_days_ago)},
]

# 预置日志存储为 opencode NDJSON 格式
# 每个 chat_id 对应一个行列表，每行是一个 JSON 对象
INITIAL_LOGS = {}

# mock-1: 纯文本对话
ses_1 = "ses_" + uuid.uuid4().hex[:22]
msg_1 = "msg_" + uuid.uuid4().hex[:20]
ts_base = int(now.timestamp() * 1000) - 60000
INITIAL_LOGS["mock-1"] = [
    make_step_start(ses_1, msg_1, ts_base),
    make_text(ses_1, msg_1, "你好！有什么我可以帮助你的吗？", ts_base + 1500),
    make_step_finish(ses_1, msg_1, "end-turn", ts_base + 2000),
    make_chat_completed(ses_1, ts_base + 2500),
]

# mock-2: 工具调用
ses_2 = "ses_" + uuid.uuid4().hex[:22]
msg_2 = "msg_" + uuid.uuid4().hex[:20]
ts_base = int(yesterday.timestamp() * 1000) - 30000
INITIAL_LOGS["mock-2"] = [
    make_step_start(ses_2, msg_2, ts_base),
    make_tool_use(
        ses_2, msg_2, "bash", "call_" + uuid.uuid4().hex[:20],
        {"command": "ls -la"}, "total 42\ndrwxr-xr-x 5 user user 4096 Jan 1 00:00 .\n",
        "List directory contents", ts_base + 1000
    ),
    make_step_finish(ses_2, msg_2, "tool-calls", ts_base + 1500),
    make_step_start(ses_2, _uid("msg_"), ts_base + 3000),
    make_text(ses_2, _uid("msg_"), "目录列表已获取，共 42 个条目。请问还需要查看其他内容吗？", ts_base + 5000),
    make_step_finish(ses_2, _uid("msg_"), "end-turn", ts_base + 5500),
    make_chat_completed(ses_2, ts_base + 6000),
]

# mock-3: 多步骤对话
ses_3 = "ses_" + uuid.uuid4().hex[:22]
msg_3 = "msg_" + uuid.uuid4().hex[:20]
ts_base = int(two_days_ago.timestamp() * 1000) - 20000
INITIAL_LOGS["mock-3"] = [
    make_step_start(ses_3, msg_3, ts_base),
    make_tool_use(
        ses_3, msg_3, "bash", "call_" + uuid.uuid4().hex[:20],
        {"command": "cat README.md"}, "# BuildMate Chat\n\nA chat application.\n",
        "Read README", ts_base + 1000
    ),
    make_step_finish(ses_3, msg_3, "tool-calls", ts_base + 1500),
    make_step_start(ses_3, _uid("msg_"), ts_base + 3000),
    make_tool_use(
        ses_3, _uid("msg_"), "glob", "call_" + uuid.uuid4().hex[:20],
        {"pattern": "**/*.vue"}, "Found 8 .vue files.\n",
        "Search Vue files", ts_base + 4000
    ),
    make_step_finish(ses_3, _uid("msg_"), "tool-calls", ts_base + 4500),
    make_step_start(ses_3, _uid("msg_"), ts_base + 6000),
    make_text(ses_3, _uid("msg_"), "项目包含 8 个 Vue 组件。README 显示这是一个聊天应用。如需更详细的分析，请告诉我。", ts_base + 8000),
    make_step_finish(ses_3, _uid("msg_"), "end-turn", ts_base + 8500),
    make_chat_completed(ses_3, ts_base + 9000),
]


# --- 内存存储 ---

chats_store = list(INITIAL_CHATS)
logs_store = {k: list(v) for k, v in INITIAL_LOGS.items()}
_next_id = 4  # 下一个可用 id 编号（已用 1,2,3）


def get_all_chats():
    """返回所有会话，按创建时间倒序"""
    return sorted(chats_store, key=lambda c: c["createdAt"], reverse=True)


def get_chat(chat_id):
    """根据 id 查找会话，返回 (chat, logs) 或 (None, None)"""
    chat = next((c for c in chats_store if c["id"] == chat_id or c["chat_id"] == chat_id), None)
    if not chat:
        return None, None
    logs = logs_store.get(chat["id"], [])
    return chat, logs


def append_logs(chat_id, logs):
    """追加日志到指定会话"""
    if chat_id not in logs_store:
        logs_store[chat_id] = []
    logs_store[chat_id].extend(logs)


def create_or_continue_chat(chat_id, prompt):
    """
    统一创建/继续对话。
    - chat_id 为空或 None：创建新会话
    - chat_id 有值：在已有会话中追加日志
    返回 (chat, message_id)
    """
    global _next_id

    if not chat_id:
        # 创建新会话
        new_id = f"mock-{_next_id}"
        _next_id += 1

        now_iso = _iso(_now())
        title = prompt[:20] if prompt else "新会话"

        chat = {
            "id": new_id,
            "chat_id": new_id,
            "title": title,
            "createdAt": now_iso,
        }
        chats_store.insert(0, chat)
        logs_store[new_id] = []
        chat_id = new_id
    else:
        chat = next((c for c in chats_store if c["id"] == chat_id or c["chat_id"] == chat_id), None)
        if not chat:
            return None, None

    # 生成 opencode 日志
    session_id = _uid("ses_")
    message_id = _uid("msg_")
    logs = generate_opencode_logs(session_id, message_id, prompt)
    append_logs(chat_id, logs)

    return chat, message_id
```

- [ ] **Step 2: 验证 mock_data.py 语法**

Run: `cd D:/codes/BuildMate/chat/scripts/python/server && python -c "from mock_data import get_all_chats, get_chat, create_or_continue_chat; c, m = create_or_continue_chat('', 'test'); print(f'Created: {c[\"id\"]}, msg: {m}')"`
Expected: 输出 `Created: mock-4, msg: msg_...`

- [ ] **Step 3: Commit**

```bash
git add scripts/python/server/mock_data.py
git commit -m "refactor: rewrite mock_data.py to opencode NDJSON format with random generation"
```

---

### Task 2: 重写 app.py — 统一入口 + NDJSON stream + after_ts

**Files:**
- Rewrite: `scripts/python/server/app.py`

**Context:** Flask app 需要三个改动：1) POST /api/chats 统一处理创建/继续对话；2) GET /api/chats/{id}/stream 返回 opencode NDJSON 格式（非 SSE），支持 `after_ts` 增量过滤；3) 逐行推送带延迟模拟流式效果。

- [ ] **Step 1: 重写 app.py**

```python
import json
import time
from flask import Flask, jsonify, request, Response
from flask_cors import CORS
from mock_data import get_all_chats, get_chat, create_or_continue_chat

app = Flask(__name__)
CORS(app)


@app.route("/api/chats", methods=["GET"])
def list_chats():
    """会话列表"""
    return jsonify(get_all_chats())


@app.route("/api/chats", methods=["POST"])
def upsert_chat():
    """统一创建/继续对话"""
    body = request.get_json(force=True)
    chat_id = body.get("chat_id", "") or ""
    prompt = body.get("prompt", "")

    chat, message_id = create_or_continue_chat(chat_id, prompt)
    if not chat:
        return jsonify({"error": "Chat not found"}), 404

    return jsonify({
        "chat_id": chat["id"],
        "message_id": message_id
    })


@app.route("/api/chats/<chat_id>/stream", methods=["GET"])
def stream_chat(chat_id):
    """返回 opencode NDJSON 格式流（支持 after_ts 增量过滤）"""
    chat, logs = get_chat(chat_id)
    if not chat:
        return jsonify({"error": "Chat not found"}), 404

    after_ts = request.args.get("after_ts", type=int)

    # 过滤日志
    if after_ts is not None:
        logs = [l for l in logs if l.get("timestamp", 0) > after_ts]

    def generate():
        for line in logs:
            yield json.dumps(line, ensure_ascii=False) + "\n"
            time.sleep(random_delay())
        # 如果所有日志都已发送完毕（包括 chat.completed），
        # 客户端通过 chat.completed 事件判断结束

    return Response(generate(), mimetype="text/x-ndjson")


def random_delay():
    """50-100ms 随机延迟模拟流式效果"""
    import random
    return random.randint(50, 100) / 1000


if __name__ == "__main__":
    app.run(port=5001, debug=True)
```

- [ ] **Step 2: 验证 Flask 启动和接口**

Run: `cd D:/codes/BuildMate/chat/scripts/python/server && python -c "from app import app; client = app.test_client(); r = client.post('/api/chats', json={'prompt': 'hello'}); print(r.get_json())"`
Expected: `{'chat_id': 'mock-4', 'message_id': 'msg_...'}`

- [ ] **Step 3: Commit**

```bash
git add scripts/python/server/app.py
git commit -m "refactor: rewrite Flask app.py with unified chat entry + NDJSON stream + after_ts"
```

---

### Task 3: 重写 chats.post.ts — 统一对话入口

**Files:**
- Rewrite: `server/api/v1/agent/chats.post.ts`

**Context:** 接收 `{ chat_id?, prompt }`，调用 Flask `POST /api/chats`，返回 `{ chat_id, message_id }`。不再返回完整的 chat 对象。

- [ ] **Step 1: 重写 chats.post.ts**

```typescript
import { z } from 'zod'

export default defineEventHandler(async (event) => {
  const body = await readValidatedBody(event, z.object({
    chat_id: z.string().optional(),
    prompt: z.string()
  }).parse)

  const config = useRuntimeConfig()

  const result = await $fetch<{
    chat_id: string
    message_id: string
  }>(`${config.backendApiUrl}/api/chats`, {
    method: 'POST',
    body: {
      chat_id: body.chat_id || '',
      prompt: body.prompt
    }
  })

  return result
})
```

- [ ] **Step 2: 验证 TypeScript 编译**

Run: `cd D:/codes/BuildMate/chat && npx nuxi typecheck`
Expected: 无类型错误

- [ ] **Step 3: Commit**

```bash
git add server/api/v1/agent/chats.post.ts
git commit -m "refactor: unify chats.post.ts as single entry for create/continue chat"
```

---

### Task 4: 删除 [id].post.ts

**Files:**
- Delete: `server/api/v1/agent/chats/[id].post.ts`

**Context:** 流式对话功能合并到 `[id].get.ts` 的 SSE 模式中，此文件不再需要。

- [ ] **Step 1: 删除文件**

Run: `rm D:/codes/BuildMate/chat/server/api/v1/agent/chats/[id].post.ts`

- [ ] **Step 2: 验证无引用残留**

Search codebase for `[id].post` references. Expected: none.

- [ ] **Step 3: Commit**

```bash
git add -u server/api/v1/agent/chats/[id].post.ts
git commit -m "refactor: delete [id].post.ts, stream merged into [id].get.ts"
```

---

### Task 5: 重写 [id].get.ts — 双模式 + opencode→AI SDK 格式转换

**Files:**
- Rewrite: `server/api/v1/agent/chats/[id].get.ts`

**Context:** 这是核心改动。端点需要两种模式：
1. **无 `?stream` 参数**：调用 Flask stream（无 after_ts）获取全部 NDJSON，解析并转换为前端消息格式（JSON 响应），记录最新 timestamp
2. **`?stream=true&after_ts=xxx`**：调用 Flask stream（带 after_ts），逐行解析 NDJSON，实时转换为 AI SDK stream parts，通过 SSE 推送给前端

opencode→AI SDK 转换规则：
| opencode 事件 | AI SDK stream part |
|---|---|
| `step_start` | `{ type: 'step-start' }` |
| `text` | `{ type: 'text-delta', text: part.text }` |
| `tool_use` | `{ type: 'tool-call', toolCallId: part.callID, toolName: part.tool, args: part.state.input }` |
| `tool_use` (completed) | `{ type: 'tool-result', toolCallId: part.callID, result: part.state.output }` |
| `step_finish` | `{ type: 'finish-step' }` |
| `chat.completed` | 结束 SSE（不产生 part） |

- [ ] **Step 1: 重写 [id].get.ts**

```typescript
import { createUIMessageStream, createUIMessageStreamResponse } from 'ai'
import { z } from 'zod'

interface OpenCodeEvent {
  type: string
  timestamp: number
  sessionID: string
  part?: {
    id?: string
    messageID?: string
    sessionID?: string
    type?: string
    text?: string
    tool?: string
    callID?: string
    state?: {
      status?: string
      input?: any
      output?: any
    }
    reason?: string
    tokens?: any
    cost?: number
    title?: string
    time?: { start: number; end: number }
  }
}

interface FlaskChat {
  id: string
  chat_id: string
  title: string | null
  createdAt: string
}

/**
 * 解析 NDJSON 文本为 opencode 事件列表
 */
function parseNDJSON(text: string): OpenCodeEvent[] {
  const events: OpenCodeEvent[] = []
  for (const line of text.split('\n')) {
    const trimmed = line.trim()
    if (!trimmed) continue
    try {
      events.push(JSON.parse(trimmed))
    } catch {
      // 忽略解析错误
    }
  }
  return events
}

/**
 * 将 opencode 事件列表转换为前端消息格式
 * 合并同一 messageID 的事件为一个 message
 */
function convertToMessages(events: OpenCodeEvent[]) {
  // 按 messageID 分组
  const messageMap = new Map<string, { role: string; parts: any[]; createdAt: string }>()

  let currentMessageId = ''
  for (const event of events) {
    if (event.type === 'chat.completed') continue

    const messageId = event.part?.messageID || currentMessageId
    if (event.part?.messageID) {
      currentMessageId = messageId
    }

    if (!messageMap.has(messageId)) {
      messageMap.set(messageId, {
        role: 'assistant',
        parts: [],
        createdAt: new Date(event.timestamp).toISOString()
      })
    }

    const msg = messageMap.get(messageId)!

    switch (event.type) {
      case 'step_start':
        msg.parts.push({ type: 'step-start' })
        break
      case 'text':
        msg.parts.push({ type: 'text', text: event.part?.text || '' })
        break
      case 'tool_use':
        msg.parts.push({
          type: `tool-${event.part?.tool || 'unknown'}`,
          toolCallId: event.part?.callID,
          state: event.part?.state?.status || 'completed',
          input: event.part?.state?.input,
          output: event.part?.state?.output
        })
        break
      case 'step_finish':
        // step-finish 不产生前端可见 part
        break
    }
  }

  const messages: any[] = []
  let msgIndex = 0
  for (const [id, msg] of messageMap) {
    messages.push({
      id,
      role: msg.role,
      parts: msg.parts,
      createdAt: msg.createdAt
    })
    msgIndex++
  }

  return messages
}

export default defineEventHandler(async (event) => {
  const { id } = await getValidatedRouterParams(event, z.object({
    id: z.string()
  }).parse)

  const query = getQuery(event)
  const isStream = query.stream === 'true'
  const afterTs = query.after_ts ? Number(query.after_ts) : undefined

  const config = useRuntimeConfig()

  // 先获取会话元信息
  const chats = await $fetch<FlaskChat[]>(`${config.backendApiUrl}/api/chats`)
  const chat = chats.find(c => c.id === id || c.chat_id === id)

  if (!chat) {
    throw createError({ statusCode: 404, statusMessage: 'Chat not found' })
  }

  if (isStream) {
    // === SSE 流式模式 ===
    const stream = createUIMessageStream({
      execute: async ({ writer }) => {
        // 构造 URL（带 after_ts）
        let url = `${config.backendApiUrl}/api/chats/${id}/stream`
        if (afterTs) {
          url += `?after_ts=${afterTs}`
        }

        const response = await fetch(url)
        if (!response.ok) {
          throw createError({ statusCode: response.status, statusMessage: 'Stream fetch failed' })
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

          for (const line of lines) {
            const trimmed = line.trim()
            if (!trimmed) continue

            let opencodeEvent: OpenCodeEvent
            try {
              opencodeEvent = JSON.parse(trimmed)
            } catch {
              continue
            }

            // 转换 opencode 事件为 AI SDK stream parts
            switch (opencodeEvent.type) {
              case 'step_start':
                writer.write({ type: 'step-start' })
                break
              case 'text':
                writer.write({ type: 'text-delta', text: opencodeEvent.part?.text || '' })
                break
              case 'tool_use': {
                const part = opencodeEvent.part
                if (part?.callID) {
                  writer.write({
                    type: 'tool-call',
                    toolCallId: part.callID,
                    toolName: part.tool || 'unknown',
                    args: part.state?.input || {}
                  })
                  if (part.state?.status === 'completed' && part.state.output !== undefined) {
                    writer.write({
                      type: 'tool-result',
                      toolCallId: part.callID,
                      result: part.state.output
                    })
                  }
                }
                break
              }
              case 'step_finish':
                writer.write({ type: 'finish-step' })
                break
              case 'chat.completed':
                // 对话结束，不产生 stream part
                break
            }
          }
        }
      }
    })

    return createUIMessageStreamResponse({ stream })
  } else {
    // === JSON 初次加载模式 ===
    const response = await fetch(`${config.backendApiUrl}/api/chats/${id}/stream`)
    if (!response.ok) {
      throw createError({ statusCode: response.status, statusMessage: 'Chat not found' })
    }

    const reader = response.body?.getReader()
    if (!reader) {
      throw createError({ statusCode: 500, statusMessage: 'Failed to read stream' })
    }

    const decoder = new TextDecoder()
    let fullText = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      fullText += decoder.decode(value, { stream: true })
    }

    const events = parseNDJSON(fullText)
    const messages = convertToMessages(events)

    // 记录最新 timestamp
    let lastTimestamp = 0
    for (const ev of events) {
      if (ev.timestamp > lastTimestamp) {
        lastTimestamp = ev.timestamp
      }
    }

    return {
      id: chat.id,
      title: chat.title,
      createdAt: chat.createdAt,
      messages,
      lastTimestamp,
      isOwner: true
    }
  }
})
```

- [ ] **Step 2: 验证 TypeScript 编译**

Run: `cd D:/codes/BuildMate/chat && npx nuxi typecheck`
Expected: 无类型错误

- [ ] **Step 3: Commit**

```bash
git add server/api/v1/agent/chats/[id].get.ts
git commit -m "refactor: rewrite [id].get.ts with dual-mode (JSON+SSE) and opencode→AI SDK conversion"
```

---

### Task 6: 修改 index.vue — 适配新 POST 响应格式

**Files:**
- Modify: `app/pages/index.vue`

**Context:** 创建新会话时 POST `{ prompt }`（无 chat_id），响应从完整的 chat 对象变为 `{ chat_id, message_id }`。导航使用 `chat_id`。不再发送 `app_name` 和 `app_chat_id`。

- [ ] **Step 1: 修改 createChat 函数**

将 `app/pages/index.vue` 中的 `createChat` 函数改为：

```typescript
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
```

同时删除第 4 行不再使用的 `chatId` 变量：

```typescript
// 删除这一行:
const chatId = crypto.randomUUID()
```

- [ ] **Step 2: 验证 TypeScript 编译**

Run: `cd D:/codes/BuildMate/chat && npx nuxi typecheck`
Expected: 无类型错误

- [ ] **Step 3: Commit**

```bash
git add app/pages/index.vue
git commit -m "refactor: adapt index.vue to new unified POST response format"
```

---

### Task 7: 修改 [id].vue — 自定义 transport + lastTimestamp 管理

**Files:**
- Modify: `app/pages/chat/[id].vue`

**Context:** 替换 `DefaultChatTransport` 为自定义 transport：
1. `sendMessage` 时先 POST 到 `chats.post.ts` 获取 `{ chat_id, message_id }`
2. 然后打开 EventSource 连接 `[id].get.ts?stream=true&after_ts={lastTimestamp}`
3. 解析 SSE 事件流
4. 收到结束信号时关闭 EventSource

初次加载时从 `[id].get.ts` JSON 响应中获取 `lastTimestamp`。

- [ ] **Step 1: 重写 [id].vue script 部分**

```vue
<script setup lang="ts">
import { Chat } from '@ai-sdk/vue'
import type { ChatTransport, UIMessage } from 'ai'

const route = useRoute()
const toast = useToast()
const { csrf, headerName } = useCsrf()

const { data } = await useFetch<{
  id: string
  title: string | null
  createdAt: string
  messages: any[]
  lastTimestamp: number
  isOwner: boolean
}>(`/api/v1/agent/chats/${route.params.id}`, {
  cache: 'force-cache'
})

const isOwner = computed(() => data.value?.isOwner ?? false)

// 记录最新时间戳，用于增量查询
const lastTimestamp = ref(data.value?.lastTimestamp || 0)

const input = ref('')

// 自定义 transport
const customTransport: ChatTransport = {
  async sendMessage({ messages, abortSignal }) {
    const lastMessage = messages[messages.length - 1]
    const text = lastMessage?.parts
      ?.filter((p: any) => p.type === 'text')
      ?.map((p: any) => p.text)
      ?.join('') || ''

    // 1. POST 触发创建/继续对话
    const result = await $fetch<{ chat_id: string; message_id: string }>('/api/v1/agent/chats', {
      method: 'POST',
      headers: { [headerName]: csrf },
      body: {
        chat_id: data.value?.id,
        prompt: text
      }
    })

    // 2. 创建 EventSource 连接接收流式响应
    const url = `/api/v1/agent/chats/${result.chat_id}?stream=true&after_ts=${lastTimestamp.value}`

    return {
      stream: new ReadableStream({
        async start(controller) {
          const eventSource = new EventSource(url)
          const encoder = new TextEncoder()

          eventSource.onmessage = (e) => {
            if (e.data === '[DONE]') {
              eventSource.close()
              controller.close()
              return
            }
            // 转发 SSE data 为 AI SDK 期望的格式
            controller.enqueue(encoder.encode(e.data + '\n'))
          }

          eventSource.onerror = () => {
            eventSource.close()
            controller.close()
          }

          if (abortSignal) {
            abortSignal.addEventListener('abort', () => {
              eventSource.close()
              controller.close()
            })
          }
        }
      }),
      messageId: result.message_id
    }
  }
}

const chat = new Chat({
  id: data.value?.id,
  messages: data.value?.messages,
  transport: customTransport,
  onError(error) {
    const { message } = typeof error.message === 'string' && error.message[0] === '{' ? JSON.parse(error.message) : error
    toast.add({
      description: message,
      icon: 'i-lucide-alert-circle',
      color: 'error',
      duration: 0
    })
  }
})

// 监听消息变化，更新 lastTimestamp
watch(() => chat.messages, () => {
  lastTimestamp.value = Date.now()
}, { deep: true })

async function handleSubmit(e: Event) {
  e.preventDefault()
  if (input.value.trim()) {
    chat.sendMessage({
      text: input.value
    })
    input.value = ''
  }
}
</script>
```

- [ ] **Step 2: 验证 TypeScript 编译**

Run: `cd D:/codes/BuildMate/chat && npx nuxi typecheck`
Expected: 无类型错误（可能有 ChatTransport 类型相关的警告，需要根据 AI SDK 6.x 的实际接口调整）

- [ ] **Step 3: Commit**

```bash
git add app/pages/chat/[id].vue
git commit -m "refactor: replace DefaultChatTransport with custom transport for opencode SSE"
```

---

### Task 8: 端到端验证

**Context:** 启动 Flask 和 Nuxt，验证完整流程。

- [ ] **Step 1: 启动 Flask mock 服务**

Run: `cd D:/codes/BuildMate/chat/scripts/python/server && python app.py`
Expected: `Running on http://127.0.0.1:5001`

- [ ] **Step 2: 启动 Nuxt dev server**

Run: `cd D:/codes/BuildMate/chat && npm run dev`
Expected: Nuxt 启动成功

- [ ] **Step 3: 测试会话列表**

浏览器打开 `http://localhost:3000/`，左侧应显示 3 个预设会话。

- [ ] **Step 4: 测试新创建会话**

在首页输入框输入 "测试消息" 并提交，应跳转到新会话页面 `/chat/mock-4`，页面应显示 AI 回复（随机内容，可能是纯文本或带工具调用）。

- [ ] **Step 5: 测试继续对话**

在会话页面继续输入消息，应触发新的流式响应，消息追加到页面中。

- [ ] **Step 6: 测试历史会话加载**

点击左侧预设会话（mock-1、mock-2、mock-3），应正确显示历史消息。

- [ ] **Step 7: 最终 Commit**

```bash
git add -A
git commit -m "chore: e2e verification of opencode NDJSON format + unified chat API"
```

---

## Self-Review Checklist

1. **Spec coverage:**
   - `chats.post.ts` 统一创建/继续入口 → Task 3
   - Flask stream 返回 opencode NDJSON → Task 2
   - Nuxt 层格式转换 opencode → AI SDK → Task 5
   - 删除 `[id].post.ts` → Task 4
   - 增量日志 after_ts → Task 2 (Flask) + Task 5 (Nuxt)
   - `chat.completed` 结束标记 → Task 1 (mock_data) + Task 5 (Nuxt)
   - Flask 随机生成 → Task 1
   - 前端自定义 transport → Task 7
   - index.vue 适配 → Task 6

2. **Placeholder scan:** No TBD, TODO, or placeholder patterns found.

3. **Type consistency:** All types consistent across tasks. `OpenCodeEvent` interface defined in Task 5. Response shapes match between Flask (`{ chat_id, message_id }`) and Nuxt consumer. `lastTimestamp` is `number` throughout.
