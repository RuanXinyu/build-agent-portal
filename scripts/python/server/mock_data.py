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
# Preset data (3 chats in opencode NDJSON format)
# ---------------------------------------------------------------------------

_now = datetime.now(timezone.utc)
_yesterday = _now - timedelta(days=1)
_two_days_ago = _now - timedelta(days=2)

# Convert to rough ms timestamps for preset logs
_ts_now = int(_now.timestamp() * 1000)
_ts_yesterday = int(_yesterday.timestamp() * 1000)
_ts_two_days_ago = int(_two_days_ago.timestamp() * 1000)

# --- mock-1: Pure text conversation -----------------------------------------

_mock1_session = "ses_mock1_abc123"
_mock1_msg = "msg_mock1_def456"

INITIAL_LOGS = {}

INITIAL_LOGS["mock-1"] = [
    make_step_start(_mock1_session, _mock1_msg, timestamp=_ts_now),
    make_text(
        _mock1_session, _mock1_msg,
        "Nuxt UI provides a set of Vue components that you can use directly in your "
        "templates. Install it with `npx nuxi module add @nuxt/ui`, then use components "
        "like `<UButton>`, `<UInput>`, `<UModal>`, etc. in your pages.",
        timestamp=_ts_now + 500,
    ),
    make_step_finish(_mock1_session, _mock1_msg, reason="end-turn", timestamp=_ts_now + 1200),
    make_chat_completed(_mock1_session, timestamp=_ts_now + 1400),
]

# --- mock-2: Tool call conversation -----------------------------------------

_mock2_session = "ses_mock2_ghi789"
_mock2_msg = "msg_mock2_jkl012"

INITIAL_LOGS["mock-2"] = [
    make_step_start(_mock2_session, _mock2_msg, timestamp=_ts_yesterday),
    make_tool_use(
        _mock2_session, _mock2_msg, "bash", "call_mock2_bash1",
        input_data={"command": "ls -la src/"},
        output_data="total 24\ndrwxr-xr-x  5 user staff 160 Apr 26 10:00 .\n-rw-r--r--  1 user staff 1024 Apr 26 10:00 index.ts\n",
        title="List source files",
        timestamp=_ts_yesterday + 400,
    ),
    make_step_finish(_mock2_session, _mock2_msg, reason="tool-calls", timestamp=_ts_yesterday + 800),
    make_step_start(_mock2_session, _mock2_msg, timestamp=_ts_yesterday + 1200),
    make_text(
        _mock2_session, _mock2_msg,
        "I've listed the source directory. The project has a standard structure with an "
        "`index.ts` entry point. Everything looks good.",
        timestamp=_ts_yesterday + 1800,
    ),
    make_step_finish(_mock2_session, _mock2_msg, reason="end-turn", timestamp=_ts_yesterday + 2200),
    make_chat_completed(_mock2_session, timestamp=_ts_yesterday + 2400),
]

# --- mock-3: Multi-step conversation ----------------------------------------

_mock3_session = "ses_mock3_mno345"
_mock3_msg = "msg_mock3_pqr678"

INITIAL_LOGS["mock-3"] = [
    make_step_start(_mock3_session, _mock3_msg, timestamp=_ts_two_days_ago),
    make_tool_use(
        _mock3_session, _mock3_msg, "glob", "call_mock3_glob1",
        input_data={"pattern": "**/*.vue"},
        output_data="src/components/Button.vue\nsrc/pages/index.vue\nsrc/layouts/default.vue\n",
        title="Find Vue components",
        timestamp=_ts_two_days_ago + 300,
    ),
    make_step_finish(_mock3_session, _mock3_msg, reason="tool-calls", timestamp=_ts_two_days_ago + 600),
    make_step_start(_mock3_session, _mock3_msg, timestamp=_ts_two_days_ago + 1000),
    make_tool_use(
        _mock3_session, _mock3_msg, "read", "call_mock3_read1",
        input_data={"file_path": "src/app.vue"},
        output_data="<template>\n  <div>\n    <NuxtPage />\n  </div>\n</template>\n",
        title="Read app.vue",
        timestamp=_ts_two_days_ago + 1400,
    ),
    make_step_finish(_mock3_session, _mock3_msg, reason="tool-calls", timestamp=_ts_two_days_ago + 1800),
    make_step_start(_mock3_session, _mock3_msg, timestamp=_ts_two_days_ago + 2400),
    make_text(
        _mock3_session, _mock3_msg,
        "After examining the project, here is my analysis:\n\n"
        "**File structure:** 3 Vue files found across components, pages, and layouts.\n\n"
        "**Root component:** `app.vue` uses `<NuxtPage />` for page routing — a standard setup.\n\n"
        "**Recommendation:** The project follows Nuxt conventions. Consider adding a "
        "`components/` directory with shared UI elements.",
        timestamp=_ts_two_days_ago + 3000,
    ),
    make_step_finish(_mock3_session, _mock3_msg, reason="end-turn", timestamp=_ts_two_days_ago + 3500),
    make_chat_completed(_mock3_session, timestamp=_ts_two_days_ago + 3700),
]

INITIAL_CHATS = [
    {
        "id": "mock-1",
        "chat_id": "mock-1",
        "title": "纯文本对话",
        "userId": "user-1",
        "createdAt": _iso(_now),
    },
    {
        "id": "mock-2",
        "chat_id": "mock-2",
        "title": "工具调用对话",
        "userId": "user-1",
        "createdAt": _iso(_yesterday),
    },
    {
        "id": "mock-3",
        "chat_id": "mock-3",
        "title": "多步骤分析对话",
        "userId": "user-1",
        "createdAt": _iso(_two_days_ago),
    },
]


# ---------------------------------------------------------------------------
# In-memory store
# ---------------------------------------------------------------------------

chats_store = list(INITIAL_CHATS)
logs_store = dict(INITIAL_LOGS)
_next_id = 4


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
        events.append(make_chat_completed(session_id))
        logs_store[chat_id] = events

        return chat, message_id

    # ---- Continue existing chat ----
    chat = next((c for c in chats_store if c["id"] == chat_id), None)
    if not chat:
        return None, None

    # Generate random opencode logs for the new assistant reply
    events = generate_opencode_logs(session_id, message_id, prompt)
    events.append(make_chat_completed(session_id))
    append_logs(chat_id, events)

    return chat, message_id
