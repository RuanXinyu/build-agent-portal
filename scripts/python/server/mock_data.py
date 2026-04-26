"""
Mock data layer for the Flask mock API server.

Stores chat data in opencode NDJSON event format and provides functions
for creating, reading, and generating random opencode log events.
"""

import random
import uuid
from datetime import datetime, timezone, timedelta


# ---------------------------------------------------------------------------
# Timestamp helpers
# ---------------------------------------------------------------------------

def _now_ms():
    """Current UTC time as milliseconds since epoch."""
    return int(datetime.now(timezone.utc).timestamp() * 1000)


def _iso(dt=None):
    """Return an ISO-8601 string. Defaults to now."""
    if dt is None:
        dt = datetime.now(timezone.utc)
    return dt.isoformat()


# ---------------------------------------------------------------------------
# ID generators
# ---------------------------------------------------------------------------

def _uid(prefix=""):
    return f"{prefix}{uuid.uuid4().hex[:12]}"


# ---------------------------------------------------------------------------
# opencode NDJSON event builders
# ---------------------------------------------------------------------------

def make_step_start(session_id, message_id, timestamp=None):
    """Create a step_start event."""
    ts = timestamp or _now_ms()
    part_id = _uid("prt_")
    return {
        "type": "step_start",
        "timestamp": ts,
        "sessionID": session_id,
        "part": {
            "id": part_id,
            "messageID": message_id,
            "sessionID": session_id,
            "snapshot": uuid.uuid4().hex[:40],
            "type": "step-start",
        },
    }


def make_text(session_id, message_id, text, timestamp=None):
    """Create a text event."""
    ts = timestamp or _now_ms()
    part_id = _uid("prt_")
    start = ts - random.randint(200, 1500)
    return {
        "type": "text",
        "timestamp": ts,
        "sessionID": session_id,
        "part": {
            "id": part_id,
            "messageID": message_id,
            "sessionID": session_id,
            "type": "text",
            "text": text,
            "time": {"start": start, "end": ts - 1},
        },
    }


def make_tool_use(session_id, message_id, tool_name, call_id, input_data, output_data, title="", timestamp=None):
    """Create a tool_use event."""
    ts = timestamp or _now_ms()
    part_id = _uid("prt_")
    start = ts - random.randint(50, 500)
    end = ts - random.randint(1, 40)
    return {
        "type": "tool_use",
        "timestamp": ts,
        "sessionID": session_id,
        "part": {
            "type": "tool",
            "tool": tool_name,
            "callID": call_id,
            "state": {
                "status": "completed",
                "input": input_data,
                "output": output_data,
            },
            "id": part_id,
            "messageID": message_id,
            "sessionID": session_id,
            "title": title or f"Run {tool_name}",
            "time": {"start": start, "end": end},
        },
    }


def make_step_finish(session_id, message_id, reason="end-turn", timestamp=None):
    """Create a step_finish event."""
    ts = timestamp or _now_ms()
    part_id = _uid("prt_")
    return {
        "type": "step_finish",
        "timestamp": ts,
        "sessionID": session_id,
        "part": {
            "id": part_id,
            "reason": reason,
            "messageID": message_id,
            "sessionID": session_id,
            "type": "step-finish",
            "tokens": {
                "total": random.randint(800, 16000),
                "input": random.randint(600, 14000),
                "output": random.randint(50, 1500),
                "reasoning": random.randint(0, 500),
                "cache": {"write": 0, "read": random.choice([0, 64, 128])},
            },
            "cost": 0,
        },
    }


def make_chat_completed(session_id, timestamp=None):
    """Create a chat.completed event."""
    ts = timestamp or _now_ms()
    return {
        "type": "chat.completed",
        "timestamp": ts,
        "sessionID": session_id,
    }


# ---------------------------------------------------------------------------
# Random content generation
# ---------------------------------------------------------------------------

# Text pools used by random generators
_TEXT_REPLIES = [
    "Nuxt UI provides a rich set of Vue components. You can use `<UButton>`, `<UInput>`, `<UModal>` and more directly in your templates after installing the module.",
    "To set up TypeScript in your project, run `npx tsc --init` and configure `tsconfig.json` to match your build tool.",
    "Docker Compose lets you define multi-container applications. Each service runs in its own container but they share a network.",
    "The Git rebase command re-applies commits on top of another base tip. Use it to maintain a clean project history.",
    "CSS Grid is a two-dimensional layout system. Define rows and columns with `grid-template-rows` and `grid-template-columns`.",
    "REST APIs use HTTP methods to represent actions: GET for reading, POST for creating, PUT/PATCH for updating, DELETE for removing resources.",
    "Vue 3 Composition API allows you to organize component logic by feature rather than by option type. Use `setup()` or `<script setup>`.",
    "To debug Node.js applications, use `node --inspect` and open `chrome://inspect` in Chrome DevTools.",
    "Tailwind CSS utility classes map directly to CSS properties. For example, `p-4` is `padding: 1rem` and `flex` is `display: flex`.",
    "PostgreSQL supports JSONB columns for semi-structured data. Index them with GIN indexes for fast lookups.",
]

_BASH_COMMANDS = [
    ("echo hello", "hello\n"),
    ("ls -la src/", "total 24\ndrwxr-xr-x  5 user  staff  160 Apr 26 10:00 .\ndrwxr-xr-x  8 user  staff  256 Apr 26 09:55 ..\n-rw-r--r--  1 user  staff  1024 Apr 26 10:00 index.ts\n"),
    ("cat package.json | head -5", '{\n  "name": "my-project",\n  "version": "1.0.0",\n  "private": true,\n'),
    ("git status", "On branch main\nChanges not staged for commit:\n  modified:   src/app.vue\n\nno changes added to commit\n"),
    ("npm run build", "\n> my-project@1.0.0 build\n> nuxt build\n\nDone in 3.2s\n"),
    ("node -e \"console.log(Date.now())\"", "1745280000000\n"),
    ("pwd", "/home/user/projects/my-app\n"),
    ("df -h /", "Filesystem  Size  Used Avail Use%  Mounted on\n/dev/sda1   50G   20G   28G  42%  /\n"),
]

_TOOL_NAMES = ["bash", "read", "write", "glob", "grep"]

_GLOB_PATTERNS = [
    ("**/*.vue", "src/components/Button.vue\nsrc/pages/index.vue\nsrc/layouts/default.vue\n"),
    ("**/*.ts", "src/types/index.ts\nserver/api/index.ts\nshared/utils.ts\n"),
    ("src/**/*.css", "src/assets/main.css\nsrc/components/modal.css\n"),
]

_READ_FILES = [
    ("src/app.vue", "<template>\n  <div>\n    <NuxtPage />\n  </div>\n</template>\n"),
    ("package.json", '{\n  "name": "demo",\n  "version": "1.0.0",\n  "dependencies": { "nuxt": "^3.0" }\n}\n'),
    ("nuxt.config.ts", "export default defineNuxtConfig({\n  modules: ['@nuxt/ui'],\n})\n"),
]

_SUMMARIES = [
    "Based on the output above, everything looks good. The project structure follows standard conventions and all files are in place.",
    "The results show that the codebase is well-organized. You can proceed with development using the established patterns.",
    "Here is a summary of what I found. All checks passed and the configuration is correct for your stack.",
    "I've reviewed the files and the project is set up correctly. No issues found in the configuration or structure.",
]


def _pick_text_reply():
    return random.choice(_TEXT_REPLIES)


def _pick_bash_command():
    return random.choice(_BASH_COMMANDS)


def _pick_glob_pattern():
    return random.choice(_GLOB_PATTERNS)


def _pick_read_file():
    return random.choice(_READ_FILES)


def _pick_summary():
    return random.choice(_SUMMARIES)


# ---------------------------------------------------------------------------
# Template generators – each returns a list of event dicts
# ---------------------------------------------------------------------------

def _template_pure_text(session_id, message_id, base_ts):
    """Pure text reply — no tool calls."""
    events = []
    ts = base_ts
    events.append(make_step_start(session_id, message_id, timestamp=ts))
    ts += random.randint(300, 800)
    events.append(make_text(session_id, message_id, _pick_text_reply(), timestamp=ts))
    ts += random.randint(100, 300)
    events.append(make_step_finish(session_id, message_id, reason="end-turn", timestamp=ts))
    return events


def _template_bash_text(session_id, message_id, base_ts):
    """bash tool call followed by a text explanation."""
    events = []
    ts = base_ts
    events.append(make_step_start(session_id, message_id, timestamp=ts))
    ts += random.randint(200, 600)

    cmd, output = _pick_bash_command()
    call_id = _uid("call_")
    events.append(make_tool_use(
        session_id, message_id, "bash", call_id,
        input_data={"command": cmd},
        output_data=output,
        title=f"Run: {cmd}",
        timestamp=ts,
    ))
    ts += random.randint(200, 500)
    events.append(make_step_finish(session_id, message_id, reason="tool-calls", timestamp=ts))

    # Second step: text
    ts += random.randint(300, 700)
    events.append(make_step_start(session_id, message_id, timestamp=ts))
    ts += random.randint(200, 600)
    events.append(make_text(session_id, message_id, _pick_summary(), timestamp=ts))
    ts += random.randint(100, 300)
    events.append(make_step_finish(session_id, message_id, reason="end-turn", timestamp=ts))
    return events


def _template_multi_tool(session_id, message_id, base_ts):
    """Multiple tool calls (bash + grep or glob) then text."""
    events = []
    ts = base_ts
    events.append(make_step_start(session_id, message_id, timestamp=ts))
    ts += random.randint(200, 500)

    # First tool: bash
    cmd, output = _pick_bash_command()
    call_id_1 = _uid("call_")
    events.append(make_tool_use(
        session_id, message_id, "bash", call_id_1,
        input_data={"command": cmd},
        output_data=output,
        title=f"Run: {cmd}",
        timestamp=ts,
    ))
    ts += random.randint(100, 300)

    # Second tool: grep or glob
    if random.random() < 0.5:
        pattern = random.choice(["TODO", "FIXME", "console\\.log"])
        grep_output = "src/app.vue:12: // TODO: refactor\nsrc/utils.ts:45: // FIXME: handle error\n"
        call_id_2 = _uid("call_")
        events.append(make_tool_use(
            session_id, message_id, "grep", call_id_2,
            input_data={"pattern": pattern, "path": "src/"},
            output_data=grep_output,
            title=f"Search for {pattern}",
            timestamp=ts,
        ))
    else:
        pattern, glob_output = _pick_glob_pattern()
        call_id_2 = _uid("call_")
        events.append(make_tool_use(
            session_id, message_id, "glob", call_id_2,
            input_data={"pattern": pattern},
            output_data=glob_output,
            title=f"Find files: {pattern}",
            timestamp=ts,
        ))
    ts += random.randint(100, 300)
    events.append(make_step_finish(session_id, message_id, reason="tool-calls", timestamp=ts))

    # Text step
    ts += random.randint(300, 700)
    events.append(make_step_start(session_id, message_id, timestamp=ts))
    ts += random.randint(200, 600)
    events.append(make_text(session_id, message_id, _pick_summary(), timestamp=ts))
    ts += random.randint(100, 300)
    events.append(make_step_finish(session_id, message_id, reason="end-turn", timestamp=ts))
    return events


def _template_multi_step(session_id, message_id, base_ts):
    """Multi-step: first step does tool calls, second step gives a text summary."""
    events = []
    ts = base_ts

    # Step 1: bash command
    events.append(make_step_start(session_id, message_id, timestamp=ts))
    ts += random.randint(200, 500)
    cmd, output = _pick_bash_command()
    call_id = _uid("call_")
    events.append(make_tool_use(
        session_id, message_id, "bash", call_id,
        input_data={"command": cmd},
        output_data=output,
        title=f"Run: {cmd}",
        timestamp=ts,
    ))
    ts += random.randint(100, 300)
    events.append(make_step_finish(session_id, message_id, reason="tool-calls", timestamp=ts))

    # Step 2: another tool
    ts += random.randint(400, 800)
    events.append(make_step_start(session_id, message_id, timestamp=ts))
    ts += random.randint(200, 500)
    pattern, glob_output = _pick_glob_pattern()
    call_id_2 = _uid("call_")
    events.append(make_tool_use(
        session_id, message_id, "glob", call_id_2,
        input_data={"pattern": pattern},
        output_data=glob_output,
        title=f"Find: {pattern}",
        timestamp=ts,
    ))
    ts += random.randint(100, 300)
    events.append(make_step_finish(session_id, message_id, reason="tool-calls", timestamp=ts))

    # Step 3: text summary
    ts += random.randint(400, 800)
    events.append(make_step_start(session_id, message_id, timestamp=ts))
    ts += random.randint(200, 600)
    events.append(make_text(session_id, message_id, _pick_summary(), timestamp=ts))
    ts += random.randint(100, 300)
    events.append(make_step_finish(session_id, message_id, reason="end-turn", timestamp=ts))
    return events


def _template_glob_read_text(session_id, message_id, base_ts):
    """glob to find files, read to inspect, then detailed text analysis."""
    events = []
    ts = base_ts

    # Step 1: glob
    events.append(make_step_start(session_id, message_id, timestamp=ts))
    ts += random.randint(200, 500)
    pattern, glob_output = _pick_glob_pattern()
    call_id_1 = _uid("call_")
    events.append(make_tool_use(
        session_id, message_id, "glob", call_id_1,
        input_data={"pattern": pattern},
        output_data=glob_output,
        title=f"Find files: {pattern}",
        timestamp=ts,
    ))
    ts += random.randint(100, 300)
    events.append(make_step_finish(session_id, message_id, reason="tool-calls", timestamp=ts))

    # Step 2: read a file
    ts += random.randint(300, 600)
    events.append(make_step_start(session_id, message_id, timestamp=ts))
    ts += random.randint(200, 500)
    file_path, file_content = _pick_read_file()
    call_id_2 = _uid("call_")
    events.append(make_tool_use(
        session_id, message_id, "read", call_id_2,
        input_data={"file_path": file_path},
        output_data=file_content,
        title=f"Read {file_path}",
        timestamp=ts,
    ))
    ts += random.randint(100, 300)
    events.append(make_step_finish(session_id, message_id, reason="tool-calls", timestamp=ts))

    # Step 3: detailed text analysis
    ts += random.randint(400, 800)
    events.append(make_step_start(session_id, message_id, timestamp=ts))
    ts += random.randint(300, 800)
    detailed_text = (
        f"After examining the project files, here is my detailed analysis:\n\n"
        f"**File structure:** The project uses a standard directory layout. The glob search "
        f"found several key files matching `{pattern}`.\n\n"
        f"**File contents (`{file_path}`):** The code follows modern conventions and is "
        f"well-structured. No obvious issues were found.\n\n"
        f"**Recommendation:** The current setup is production-ready. Consider adding unit "
        f"tests for the core modules."
    )
    events.append(make_text(session_id, message_id, detailed_text, timestamp=ts))
    ts += random.randint(100, 300)
    events.append(make_step_finish(session_id, message_id, reason="end-turn", timestamp=ts))
    return events


# Weighted template list: (weight, generator_function)
_TEMPLATES = [
    (3, _template_pure_text),
    (2, _template_bash_text),
    (2, _template_multi_tool),
    (2, _template_multi_step),
    (1, _template_glob_read_text),
]

_TEMPLATE_POOL = []
for _weight, _fn in _TEMPLATES:
    _TEMPLATE_POOL.extend([_fn] * _weight)


def generate_opencode_logs(session_id, message_id, prompt, base_ts=None):
    """
    Pick a random template and return a list of opencode event dicts.

    The events are guaranteed to have monotonically increasing timestamps.
    A `chat.completed` event is NOT included — the caller should append it
    when the conversation turn is finished.
    """
    ts = base_ts or _now_ms()
    template_fn = random.choice(_TEMPLATE_POOL)
    return template_fn(session_id, message_id, ts)


# ---------------------------------------------------------------------------
# Preset data (6 chats with rich multi-turn conversations)
# ---------------------------------------------------------------------------

_now = datetime.now(timezone.utc)
_hours_ago = _now - timedelta(hours=3)
_yesterday = _now - timedelta(days=1)
_two_days_ago = _now - timedelta(days=2)
_three_days_ago = _now - timedelta(days=3)
_last_week = _now - timedelta(days=6)

# Convert to rough ms timestamps for preset logs
_ts_now = int(_now.timestamp() * 1000)
_ts_hours_ago = int(_hours_ago.timestamp() * 1000)
_ts_yesterday = int(_yesterday.timestamp() * 1000)
_ts_two_days_ago = int(_two_days_ago.timestamp() * 1000)
_ts_three_days_ago = int(_three_days_ago.timestamp() * 1000)
_ts_last_week = int(_last_week.timestamp() * 1000)

INITIAL_LOGS = {}

# --- mock-1: 纯文本对话 (多轮) ------------------------------------------------

_s1 = "ses_m1_" + uuid.uuid4().hex[:8]

INITIAL_LOGS["mock-1"] = [
    # 第一轮：纯文本
    make_step_start(_s1, "msg_m1_001", timestamp=_ts_now),
    make_text(_s1, "msg_m1_001",
        "Nuxt UI 是一套基于 Vue 3 的组件库，提供了丰富的 UI 组件，比如按钮、输入框、模态框等。\n\n"
        "安装方式：`npx nuxi module add @nuxt/ui`\n\n"
        "安装完成后可以直接在模板中使用 `<UButton>`、`<UInput>`、`<UModal>` 等组件。",
        timestamp=_ts_now + 800),
    make_step_finish(_s1, "msg_m1_001", reason="end-turn", timestamp=_ts_now + 1200),
    make_chat_completed(_s1, timestamp=_ts_now + 1400),
    # 第二轮：用户追问
    make_step_start(_s1, "msg_m1_002", timestamp=_ts_now + 5000),
    make_text(_s1, "msg_m1_002",
        "关于 Nuxt UI 的主题定制，你可以通过 `app.config.ts` 文件来配置主题色、圆角、字体等样式变量。\n\n"
        "例如：\n```ts\nexport default defineAppConfig({\n  ui: {\n    primary: 'indigo',\n    gray: 'slate'\n  }\n})\n```\n\n"
        "还可以通过 `ui` prop 对单个组件进行样式覆盖，非常灵活。",
        timestamp=_ts_now + 6000),
    make_step_finish(_s1, "msg_m1_002", reason="end-turn", timestamp=_ts_now + 6500),
    make_chat_completed(_s1, timestamp=_ts_now + 6700),
]

# --- mock-2: 工具调用对话 (bash + glob + 多轮) -----------------------------------

_s2 = "ses_m2_" + uuid.uuid4().hex[:8]

INITIAL_LOGS["mock-2"] = [
    # 第一轮：查看项目结构
    make_step_start(_s2, "msg_m2_001", timestamp=_ts_hours_ago),
    make_tool_use(_s2, "msg_m2_001", "bash", "call_m2_bash1",
        input_data={"command": "ls -la"},
        output_data="total 48\ndrwxr-xr-x  8 user staff  256 Apr 26 10:00 .\ndrwxr-xr-x  5 user staff  160 Apr 26 09:55 ..\n-rw-r--r--  1 user staff  1024 Apr 26 10:00 package.json\n-rw-r--r--  1 user staff   512 Apr 26 10:00 nuxt.config.ts\ndrwxr-xr-x  3 user staff   96 Apr 26 10:00 server\ndrwxr-xr-x  4 user staff  128 Apr 26 10:00 app\ndrwxr-xr-x  4 user staff  128 Apr 26 10:00 shared\n",
        title="List project root",
        timestamp=_ts_hours_ago + 400),
    make_step_finish(_s2, "msg_m2_001", reason="tool-calls", timestamp=_ts_hours_ago + 800),
    make_step_start(_s2, "msg_m2_001", timestamp=_ts_hours_ago + 1200),
    make_text(_s2, "msg_m2_001",
        "项目结构已获取。可以看到这是一个标准的 Nuxt 项目，包含 `server/`、`app/`、`shared/` 三个目录。\n\n"
        "**目录说明：**\n- `app/` — 前端页面和组件\n- `server/` — 后端 API 路由\n- `shared/` — 前后端共享的类型和工具",
        timestamp=_ts_hours_ago + 2000),
    make_step_finish(_s2, "msg_m2_001", reason="end-turn", timestamp=_ts_hours_ago + 2400),
    make_chat_completed(_s2, timestamp=_ts_hours_ago + 2600),
    # 第二轮：查找特定文件
    make_step_start(_s2, "msg_m2_002", timestamp=_ts_hours_ago + 10000),
    make_tool_use(_s2, "msg_m2_002", "glob", "call_m2_glob1",
        input_data={"pattern": "**/*.vue"},
        output_data="app/pages/index.vue\napp/pages/chat/[id].vue\napp/layouts/default.vue\napp/components/Navbar.vue\napp/components/chat/ChatIndicator.vue\napp/components/chat/ChatMessageContent.vue\napp/components/chat/ChatMessageActions.vue\n",
        title="Find all Vue components",
        timestamp=_ts_hours_ago + 10400),
    make_tool_use(_s2, "msg_m2_002", "bash", "call_m2_bash2",
        input_data={"command": "wc -l app/pages/chat/\\[id\\].vue"},
        output_data="  186 app/pages/chat/[id].vue\n",
        title="Count lines in chat page",
        timestamp=_ts_hours_ago + 10600),
    make_step_finish(_s2, "msg_m2_002", reason="tool-calls", timestamp=_ts_hours_ago + 11000),
    make_step_start(_s2, "msg_m2_002", timestamp=_ts_hours_ago + 11500),
    make_text(_s2, "msg_m2_002",
        "共找到 **7 个 Vue 文件**：\n\n| 文件 | 用途 |\n|------|------|\n| `pages/index.vue` | 首页 |\n| `pages/chat/[id].vue` | 聊天详情页 (186行) |\n| `layouts/default.vue` | 默认布局 |\n| `components/Navbar.vue` | 导航栏 |\n| `components/chat/Chat*.vue` | 聊天相关组件 |\n\n"
        "聊天页面是最复杂的组件，包含了消息渲染、流式响应、自定义 transport 等逻辑。",
        timestamp=_ts_hours_ago + 13000),
    make_step_finish(_s2, "msg_m2_002", reason="end-turn", timestamp=_ts_hours_ago + 13500),
    make_chat_completed(_s2, timestamp=_ts_hours_ago + 13700),
]

# --- mock-3: 多步骤分析对话 (glob → read → read → text) --------------------------

_s3 = "ses_m3_" + uuid.uuid4().hex[:8]

INITIAL_LOGS["mock-3"] = [
    # 第一轮：分析项目架构
    make_step_start(_s3, "msg_m3_001", timestamp=_ts_yesterday),
    make_tool_use(_s3, "msg_m3_001", "glob", "call_m3_glob1",
        input_data={"pattern": "server/**/*.ts"},
        output_data="server/api/v1/agent/chats.get.ts\nserver/api/v1/agent/chats.post.ts\nserver/api/v1/agent/chats/[id].get.ts\nserver/db/schema.ts\n",
        title="Find server-side TypeScript files",
        timestamp=_ts_yesterday + 300),
    make_step_finish(_s3, "msg_m3_001", reason="tool-calls", timestamp=_ts_yesterday + 600),
    make_step_start(_s3, "msg_m3_001", timestamp=_ts_yesterday + 1000),
    make_tool_use(_s3, "msg_m3_001", "read", "call_m3_read1",
        input_data={"file_path": "server/api/v1/agent/chats/[id].get.ts"},
        output_data="import { createUIMessageStream, createUIMessageStreamResponse } from 'ai'\nimport { z } from 'zod'\n// ... 双模式端点：JSON 初次加载 + SSE 流式\n",
        title="Read chat detail endpoint",
        timestamp=_ts_yesterday + 2000),
    make_tool_use(_s3, "msg_m3_001", "read", "call_m3_read2",
        input_data={"file_path": "server/api/v1/agent/chats.post.ts"},
        output_data="import { z } from 'zod'\n// ... 统一创建/继续对话入口\n",
        title="Read chat POST endpoint",
        timestamp=_ts_yesterday + 2200),
    make_step_finish(_s3, "msg_m3_001", reason="tool-calls", timestamp=_ts_yesterday + 2600),
    make_step_start(_s3, "msg_m3_001", timestamp=_ts_yesterday + 3200),
    make_text(_s3, "msg_m3_001",
        "## 项目架构分析\n\n"
        "经过代码审查，该项目的后端架构如下：\n\n"
        "### API 层（Nuxt Server Routes）\n\n"
        "1. **`chats.get.ts`** — 获取会话列表\n"
        "2. **`chats.post.ts`** — 统一对话入口（创建新会话 / 继续已有会话）\n"
        "3. **`[id].get.ts`** — 会话详情，支持两种模式：\n"
        "   - JSON 模式：初次加载全部历史消息\n"
        "   - SSE 模式：流式推送新增消息（opencode → AI SDK 格式转换）\n\n"
        "### 数据层\n"
        "- 使用 Flask Mock API 作为后端\n"
        "- 支持 opencode NDJSON 格式的流式日志\n"
        "- 通过 `after_ts` 参数实现增量日志获取\n\n"
        "### 架构亮点\n"
        "- Nuxt server 层做格式转换，前端无需了解 opencode 格式\n"
        "- `chat.completed` 事件标记对话结束\n"
        "- 自定义 `ChatTransport` 对接 `@ai-sdk/vue`",
        timestamp=_ts_yesterday + 5500),
    make_step_finish(_s3, "msg_m3_001", reason="end-turn", timestamp=_ts_yesterday + 6000),
    make_chat_completed(_s3, timestamp=_ts_yesterday + 6200),
    # 第二轮：性能优化建议
    make_step_start(_s3, "msg_m3_002", timestamp=_ts_yesterday + 20000),
    make_tool_use(_s3, "msg_m3_002", "bash", "call_m3_bash1",
        input_data={"command": "du -sh node_modules/ && du -sh .output/ 2>/dev/null || echo 'no output dir'"},
        output_data="248M\t node_modules/\nno output dir\n",
        title="Check project size",
        timestamp=_ts_yesterday + 20400),
    make_step_finish(_s3, "msg_m3_002", reason="tool-calls", timestamp=_ts_yesterday + 20800),
    make_step_start(_s3, "msg_m3_002", timestamp=_ts_yesterday + 21300),
    make_text(_s3, "msg_m3_002",
        "### 性能优化建议\n\n"
        "1. **按需加载**：`node_modules` 248MB，建议开启 Nuxt 的自动 tree-shaking\n"
        "2. **SSE 连接管理**：建议在前端添加重连逻辑和超时处理\n"
        "3. **缓存策略**：会话列表可以添加客户端缓存，减少请求频率\n"
        "4. **流式分块**：长文本回复建议分段推送，避免单次推送过大的 text-delta",
        timestamp=_ts_yesterday + 23000),
    make_step_finish(_s3, "msg_m3_002", reason="end-turn", timestamp=_ts_yesterday + 23500),
    make_chat_completed(_s3, timestamp=_ts_yesterday + 23700),
]

# --- mock-4: 调试排错对话 (bash 多次执行 + grep) --------------------------------

_s4 = "ses_m4_" + uuid.uuid4().hex[:8]

INITIAL_LOGS["mock-4"] = [
    # 第一轮：定位编译错误
    make_step_start(_s4, "msg_m4_001", timestamp=_ts_two_days_ago),
    make_tool_use(_s4, "msg_m4_001", "bash", "call_m4_bash1",
        input_data={"command": "npm run build 2>&1 | head -30"},
        output_data="ERROR in app/pages/chat/[id].vue:28:15\nTS2345: Argument of type 'string | undefined' is not assignable to parameter of type 'string'.\n  26 | const result = await $fetch('/api/v1/agent/chats', {\n  27 |   method: 'POST',\n  28 |   body: { chat_id: chatId, prompt: text }\n     |               ^^^^^^\n",
        title="Run build to find errors",
        timestamp=_ts_two_days_ago + 3000),
    make_step_finish(_s4, "msg_m4_001", reason="tool-calls", timestamp=_ts_two_days_ago + 3500),
    make_step_start(_s4, "msg_m4_001", timestamp=_ts_two_days_ago + 4000),
    make_tool_use(_s4, "msg_m4_001", "read", "call_m4_read1",
        input_data={"file_path": "app/pages/chat/[id].vue", "offset": 20, "limit": 15},
        output_data="  const result = await $fetch<{ chat_id: string; message_id: string }>('/api/v1/agent/chats', {\n    method: 'POST',\n    headers: { [headerName]: csrf },\n    body: { chat_id: chatId, prompt: text }\n  })\n",
        title="Read the error location",
        timestamp=_ts_two_days_ago + 5000),
    make_step_finish(_s4, "msg_m4_001", reason="tool-calls", timestamp=_ts_two_days_ago + 5500),
    make_step_start(_s4, "msg_m4_001", timestamp=_ts_two_days_ago + 6000),
    make_text(_s4, "msg_m4_001",
        "找到问题了！在 `app/pages/chat/[id].vue` 第 28 行，`chatId` 的类型是 `string | undefined`，"
        "但 `$fetch` 的 body 期望 `string`。\n\n"
        "**修复方案：**\n```typescript\nbody: { chat_id: chatId || '', prompt: text }\n```\n\n"
        "使用空字符串作为默认值，这样当 `chatId` 为 `undefined` 时会创建新会话。",
        timestamp=_ts_two_days_ago + 8000),
    make_step_finish(_s4, "msg_m4_001", reason="end-turn", timestamp=_ts_two_days_ago + 8500),
    make_chat_completed(_s4, timestamp=_ts_two_days_ago + 8700),
    # 第二轮：验证修复
    make_step_start(_s4, "msg_m4_002", timestamp=_ts_two_days_ago + 30000),
    make_tool_use(_s4, "msg_m4_002", "bash", "call_m4_bash2",
        input_data={"command": "npm run build 2>&1 | tail -5"},
        output_data="✔ Client built in 3.2s\n✔ Server built in 1.1s\n✔ You can preview this build using: npm run preview\n",
        title="Rebuild to verify fix",
        timestamp=_ts_two_days_ago + 33000),
    make_step_finish(_s4, "msg_m4_002", reason="tool-calls", timestamp=_ts_two_days_ago + 33500),
    make_step_start(_s4, "msg_m4_002", timestamp=_ts_two_days_ago + 34000),
    make_text(_s4, "msg_m4_002",
        "构建成功！错误已修复。构建耗时：\n- Client: 3.2s\n- Server: 1.1s\n\n"
        "项目现在可以正常运行了。如果还有其他 TypeScript 类型错误，可以使用 `npx nuxi typecheck` 进行全面检查。",
        timestamp=_ts_two_days_ago + 35500),
    make_step_finish(_s4, "msg_m4_002", reason="end-turn", timestamp=_ts_two_days_ago + 36000),
    make_chat_completed(_s4, timestamp=_ts_two_days_ago + 36200),
]

# --- mock-5: 代码审查对话 (grep + read + 多步骤分析) ------------------------------

_s5 = "ses_m5_" + uuid.uuid4().hex[:8]

INITIAL_LOGS["mock-5"] = [
    # 第一轮：搜索安全漏洞
    make_step_start(_s5, "msg_m5_001", timestamp=_ts_three_days_ago),
    make_tool_use(_s5, "msg_m5_001", "bash", "call_m5_bash1",
        input_data={"command": "grep -rn 'eval(' app/ server/ --include='*.ts' --include='*.vue' 2>/dev/null || echo 'No eval found'"},
        output_data="No eval found\n",
        title="Search for dangerous eval() calls",
        timestamp=_ts_three_days_ago + 1500),
    make_tool_use(_s5, "msg_m5_001", "bash", "call_m5_bash2",
        input_data={"command": "grep -rn 'innerHTML' app/ server/ --include='*.ts' --include='*.vue' 2>/dev/null || echo 'No innerHTML found'"},
        output_data="No innerHTML found\n",
        title="Search for XSS-prone innerHTML",
        timestamp=_ts_three_days_ago + 1700),
    make_tool_use(_s5, "msg_m5_001", "bash", "call_m5_bash3",
        input_data={"command": "grep -rn 'v-html' app/ --include='*.vue' 2>/dev/null || echo 'No v-html found'"},
        output_data="No v-html found\n",
        title="Search for v-html directives",
        timestamp=_ts_three_days_ago + 1900),
    make_step_finish(_s5, "msg_m5_001", reason="tool-calls", timestamp=_ts_three_days_ago + 2500),
    make_step_start(_s5, "msg_m5_001", timestamp=_ts_three_days_ago + 3000),
    make_text(_s5, "msg_m5_001",
        "## 安全审查结果\n\n"
        "经过扫描，未发现常见安全漏洞：\n\n"
        "| 检查项 | 结果 |\n|--------|------|\n| `eval()` 调用 | 未发现 |\n| `innerHTML` 使用 | 未发现 |\n| `v-html` 指令 | 未发现 |\n\n"
        "项目在 XSS 防护方面做得很好。Vue 的模板编译器会自动转义 HTML，所以只要不使用 `v-html`，默认就是安全的。\n\n"
        "**建议：**\n"
        "- 继续避免使用 `v-html`\n"
        "- 对用户输入的 prompt 做长度限制\n"
        "- 在 API 层添加 rate limiting",
        timestamp=_ts_three_days_ago + 5000),
    make_step_finish(_s5, "msg_m5_001", reason="end-turn", timestamp=_ts_three_days_ago + 5500),
    make_chat_completed(_s5, timestamp=_ts_three_days_ago + 5700),
    # 第二轮：依赖检查
    make_step_start(_s5, "msg_m5_002", timestamp=_ts_three_days_ago + 15000),
    make_tool_use(_s5, "msg_m5_002", "bash", "call_m5_bash4",
        input_data={"command": "cat package.json | grep -A 20 'dependencies'"},
        output_data='{\n  "dependencies": {\n    "@ai-sdk/vue": "^1.0.0",\n    "ai": "^4.0.0",\n    "zod": "^3.22.0",\n    "flask-cors": "^4.0.0"\n  }\n}\n',
        title="Check project dependencies",
        timestamp=_ts_three_days_ago + 15400),
    make_step_finish(_s5, "msg_m5_002", reason="tool-calls", timestamp=_ts_three_days_ago + 15800),
    make_step_start(_s5, "msg_m5_002", timestamp=_ts_three_days_ago + 16300),
    make_text(_s5, "msg_m5_002",
        "### 依赖分析\n\n"
        "项目依赖非常精简，只有 4 个核心依赖：\n\n"
        "1. **`@ai-sdk/vue` + `ai`** — AI SDK，用于聊天流式响应\n"
        "2. **`zod`** — 请求参数校验\n"
        "3. **`flask-cors`** — 跨域支持（仅在 Flask Mock 中使用）\n\n"
        "依赖数量少，攻击面小，维护成本低。这是一个很好的实践。",
        timestamp=_ts_three_days_ago + 18000),
    make_step_finish(_s5, "msg_m5_002", reason="end-turn", timestamp=_ts_three_days_ago + 18500),
    make_chat_completed(_s5, timestamp=_ts_three_days_ago + 18700),
]

# --- mock-6: 综合对话 (多工具调用 + 长文本 + 多轮) --------------------------------

_s6 = "ses_m6_" + uuid.uuid4().hex[:8]

INITIAL_LOGS["mock-6"] = [
    # 第一轮：项目初始化引导
    make_step_start(_s6, "msg_m6_001", timestamp=_ts_last_week),
    make_tool_use(_s6, "msg_m6_001", "bash", "call_m6_bash1",
        input_data={"command": "node --version && npm --version"},
        output_data="v20.11.0\n10.2.4\n",
        title="Check Node.js and npm versions",
        timestamp=_ts_last_week + 1000),
    make_tool_use(_s6, "msg_m6_001", "bash", "call_m6_bash2",
        input_data={"command": "python3 --version 2>/dev/null || python --version"},
        output_data="Python 3.12.3\n",
        title="Check Python version",
        timestamp=_ts_last_week + 1200),
    make_tool_use(_s6, "msg_m6_001", "glob", "call_m6_glob1",
        input_data={"pattern": "**/*.config.*"},
        output_data="nuxt.config.ts\ntsconfig.json\n",
        title="Find config files",
        timestamp=_ts_last_week + 1400),
    make_step_finish(_s6, "msg_m6_001", reason="tool-calls", timestamp=_ts_last_week + 2000),
    make_step_start(_s6, "msg_m6_001", timestamp=_ts_last_week + 2500),
    make_text(_s6, "msg_m6_001",
        "## 开发环境检查\n\n"
        "### 环境信息\n"
        "| 工具 | 版本 |\n|------|------|\n| Node.js | v20.11.0 |\n| npm | 10.2.4 |\n| Python | 3.12.3 |\n\n"
        "### 配置文件\n"
        "项目包含 `nuxt.config.ts` 和 `tsconfig.json`，是一个标准的 Nuxt + TypeScript 项目。\n\n"
        "### 启动开发环境\n\n"
        "需要两个终端：\n\n"
        "**终端 1 — 启动 Flask Mock API：**\n```bash\ncd scripts/python/server\npip install flask flask-cors\npython app.py\n```\n\n"
        "**终端 2 — 启动 Nuxt 前端：**\n```bash\nnpm install\nnpm run dev\n```\n\n"
        "然后打开浏览器访问 `http://localhost:3000` 即可。",
        timestamp=_ts_last_week + 6000),
    make_step_finish(_s6, "msg_m6_001", reason="end-turn", timestamp=_ts_last_week + 6500),
    make_chat_completed(_s6, timestamp=_ts_last_week + 6700),
    # 第二轮：API 流程说明
    make_step_start(_s6, "msg_m6_002", timestamp=_ts_last_week + 20000),
    make_tool_use(_s6, "msg_m6_002", "read", "call_m6_read1",
        input_data={"file_path": "shared/chat.ts"},
        output_data="export class Chat {\n  id: string\n  chat_id: string\n  title: string | null\n  // ...\n}\n",
        title="Read Chat model",
        timestamp=_ts_last_week + 20500),
    make_step_finish(_s6, "msg_m6_002", reason="tool-calls", timestamp=_ts_last_week + 21000),
    make_step_start(_s6, "msg_m6_002", timestamp=_ts_last_week + 21500),
    make_text(_s6, "msg_m6_002",
        "## API 数据流程\n\n"
        "### 创建新会话\n"
        "```\n前端 → POST /api/v1/agent/chats { prompt }\n     → Nuxt chats.post.ts → Flask POST /api/chats\n     ← { chat_id: 'mock-7', message_id: 'msg_xxx' }\n     → navigateTo('/chat/mock-7')\n```\n\n"
        "### 加载历史消息\n"
        "```\n前端 → GET /api/v1/agent/chats/mock-7\n     → Nuxt [id].get.ts (无 stream 参数)\n     → Flask GET /api/chats/mock-7/stream\n     ← 解析 NDJSON → 转换为前端消息格式 + lastTimestamp\n```\n\n"
        "### 继续对话（流式）\n"
        "```\n前端 → POST /api/v1/agent/chats { chat_id: 'mock-7', prompt: '...' }\n     → 打开 EventSource: /api/v1/agent/chats/mock-7?stream=true&after_ts=xxx\n     → Nuxt [id].get.ts (SSE 模式)\n     → Flask GET /api/chats/mock-7/stream?after_ts=xxx\n     ← 逐行 NDJSON → 实时转换为 AI SDK stream parts → SSE 推送\n     ← 收到 chat.completed → 关闭连接\n```",
        timestamp=_ts_last_week + 25000),
    make_step_finish(_s6, "msg_m6_002", reason="end-turn", timestamp=_ts_last_week + 25500),
    make_chat_completed(_s6, timestamp=_ts_last_week + 25700),
]

INITIAL_CHATS = [
    {
        "id": "mock-1",
        "chat_id": "mock-1",
        "title": "Nuxt UI 组件使用指南",
        "userId": "user-1",
        "createdAt": _iso(_now),
    },
    {
        "id": "mock-2",
        "chat_id": "mock-2",
        "title": "项目结构查看与分析",
        "userId": "user-1",
        "createdAt": _iso(_hours_ago),
    },
    {
        "id": "mock-3",
        "chat_id": "mock-3",
        "title": "后端架构分析",
        "userId": "user-1",
        "createdAt": _iso(_yesterday),
    },
    {
        "id": "mock-4",
        "chat_id": "mock-4",
        "title": "TypeScript 编译错误修复",
        "userId": "user-1",
        "createdAt": _iso(_two_days_ago),
    },
    {
        "id": "mock-5",
        "chat_id": "mock-5",
        "title": "安全审查与依赖检查",
        "userId": "user-1",
        "createdAt": _iso(_three_days_ago),
    },
    {
        "id": "mock-6",
        "chat_id": "mock-6",
        "title": "开发环境配置指南",
        "userId": "user-1",
        "createdAt": _iso(_last_week),
    },
]


# ---------------------------------------------------------------------------
# In-memory store
# ---------------------------------------------------------------------------

chats_store = list(INITIAL_CHATS)
logs_store = dict(INITIAL_LOGS)
_next_id = 7


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_all_chats():
    """Return all chats sorted by createdAt descending."""
    return sorted(chats_store, key=lambda c: c["createdAt"], reverse=True)


def get_chat(chat_id):
    """Look up a chat by id. Returns (chat, logs) or (None, None)."""
    chat = next((c for c in chats_store if c["id"] == chat_id), None)
    if not chat:
        return None, None
    logs = logs_store.get(chat_id, [])
    return chat, logs


def append_logs(chat_id, logs):
    """Append a list of event dicts to the chat's log store."""
    if chat_id not in logs_store:
        logs_store[chat_id] = []
    logs_store[chat_id].extend(logs)


def create_or_continue_chat(chat_id, prompt):
    """
    Unified create / continue.

    - If chat_id is empty string or None: create a new chat, generate
      random opencode logs, and return (chat, message_id).
    - If chat_id is provided and found: append random logs to the existing
      chat and return (chat, message_id).
    - If chat_id is provided but not found: return (None, None).
    """
    global _next_id

    message_id = _uid("msg_")
    session_id = _uid("ses_")

    if not chat_id:
        # ---- Create new chat ----
        chat_id = f"mock-{_next_id}"
        _next_id += 1

        now_iso = _iso()
        title = prompt[:30] if prompt else "新会话"

        chat = {
            "id": chat_id,
            "chat_id": chat_id,
            "title": title,
            "userId": "user-1",
            "createdAt": now_iso,
        }
        chats_store.append(chat)

        # Generate random opencode logs for the assistant reply
        events = generate_opencode_logs(session_id, message_id, prompt)
        # chat.completed timestamp must be after the last event
        last_event_ts = events[-1].get("timestamp", _now_ms()) if events else _now_ms()
        events.append(make_chat_completed(session_id, timestamp=last_event_ts + 100))
        logs_store[chat_id] = events

        return chat, message_id

    # ---- Continue existing chat ----
    chat = next((c for c in chats_store if c["id"] == chat_id), None)
    if not chat:
        return None, None

    # Ensure new timestamps are after the last existing event
    existing_logs = logs_store.get(chat_id, [])
    last_ts = max((e.get("timestamp", 0) for e in existing_logs), default=0)
    base_ts = max(_now_ms(), last_ts + 1)

    # Generate random opencode logs for the new assistant reply
    events = generate_opencode_logs(session_id, message_id, prompt, base_ts=base_ts)
    # chat.completed timestamp must be after the last event
    last_event_ts = events[-1].get("timestamp", _now_ms()) if events else _now_ms()
    events.append(make_chat_completed(session_id, timestamp=last_event_ts + 100))
    append_logs(chat_id, events)

    return chat, message_id
