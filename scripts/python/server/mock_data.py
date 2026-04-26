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
