import { Chat } from '#shared/chat'
import { Message } from '#shared/message'

const now = new Date()
const yesterday = new Date(now.getTime() - 24 * 60 * 60 * 1000)
const twoDaysAgo = new Date(now.getTime() - 2 * 24 * 60 * 60 * 1000)
const lastWeek = new Date(now.getTime() - 5 * 24 * 60 * 60 * 1000)
const lastMonth = new Date(now.getTime() - 20 * 24 * 60 * 60 * 1000)

const mockChats: Record<string, {
  chat: Chat
  messages: Message[]
}> = {
  // Text only
  'mock-1': {
    chat: new Chat({
      id: 'mock-1',
      chat_id: 'mock-1',
      title: '【Text】纯文本对话',
      userId: 'mock-user',
      visibility: 'private',
      createdAt: now
    }),
    messages: [
      new Message({
        id: 'msg-1-1',
        chatId: 'mock-1',
        role: 'user',
        parts: [{ type: 'text', text: 'How do I use Nuxt UI components?' }],
        createdAt: now
      }),
      new Message({
        id: 'msg-1-2',
        chatId: 'mock-1',
        role: 'assistant',
        parts: [{ type: 'text', text: 'Nuxt UI provides a set of Vue components that you can use directly in your templates. Install it with `npx nuxi module add @nuxt/ui`, then use components like `<UButton>`, `<UInput>`, `<UModal>`, etc. in your pages.' }],
        createdAt: now
      })
    ]
  },

  // Text + Reasoning (思考链)
  'mock-2': {
    chat: new Chat({
      id: 'mock-2',
      chat_id: 'mock-2',
      title: '【Reasoning】带思考链的回答',
      userId: 'mock-user',
      visibility: 'private',
      createdAt: yesterday
    }),
    messages: [
      new Message({
        id: 'msg-2-1',
        chatId: 'mock-2',
        role: 'user',
        parts: [{ type: 'text', text: 'Can you think step by step: what is 15% of 240?' }],
        createdAt: yesterday
      }),
      new Message({
        id: 'msg-2-2',
        chatId: 'mock-2',
        role: 'assistant',
        parts: [
          { type: 'reasoning', text: 'Let me calculate 15% of 240.\n\nStep 1: Convert 15% to decimal → 0.15\nStep 2: Multiply 240 × 0.15\nStep 3: 240 × 0.15 = 36\n\nSo the answer is 36.' },
          { type: 'text', text: '15% of 240 is **36**.\n\nHere\'s how I calculated it:\n- 15% = 0.15\n- 240 × 0.15 = 36' }
        ],
        createdAt: yesterday
      })
    ]
  },

  // Text + File (文件/图片附件)
  'mock-3': {
    chat: new Chat({
      id: 'mock-3',
      chat_id: 'mock-3',
      title: '【File】带图片附件的对话',
      userId: 'mock-user',
      visibility: 'public',
      createdAt: twoDaysAgo
    }),
    messages: [
      new Message({
        id: 'msg-3-1',
        chatId: 'mock-3',
        role: 'user',
        parts: [
          { type: 'text', text: 'What does this screenshot show?' },
          { type: 'file', mediaType: 'image/png', filename: 'dashboard.png', url: 'https://placehold.co/600x400/png' }
        ],
        createdAt: twoDaysAgo
      }),
      new Message({
        id: 'msg-3-2',
        chatId: 'mock-3',
        role: 'assistant',
        parts: [{ type: 'text', text: 'This screenshot shows a dashboard with charts and metrics. I can see what appears to be a data visualization interface with line charts and summary cards.' }],
        createdAt: twoDaysAgo
      }),
      new Message({
        id: 'msg-3-3',
        chatId: 'mock-3',
        role: 'user',
        parts: [
          { type: 'text', text: 'Here\'s the PDF report as well' },
          { type: 'file', mediaType: 'application/pdf', filename: 'report-2024.pdf', url: 'https://placehold.co/600x400/png' }
        ],
        createdAt: twoDaysAgo
      }),
      new Message({
        id: 'msg-3-4',
        chatId: 'mock-3',
        role: 'assistant',
        parts: [{ type: 'text', text: 'Thanks for sharing the PDF report. I\'ve reviewed it and the data aligns with what we see in the dashboard screenshot.' }],
        createdAt: twoDaysAgo
      })
    ]
  },

  // Text + Source URL (来源引用)
  'mock-4': {
    chat: new Chat({
      id: 'mock-4',
      chat_id: 'mock-4',
      title: '【Source URL】带来源引用的回答',
      userId: 'mock-user',
      visibility: 'private',
      createdAt: lastWeek
    }),
    messages: [
      new Message({
        id: 'msg-4-1',
        chatId: 'mock-4',
        role: 'user',
        parts: [{ type: 'text', text: 'What are the latest features in Vue 3.5?' }],
        createdAt: lastWeek
      }),
      new Message({
        id: 'msg-4-2',
        chatId: 'mock-4',
        role: 'assistant',
        parts: [
          { type: 'text', text: 'Vue 3.5 introduced several exciting features:\n\n1. **Reactive Props Destructure** — You can now destructure props in `<script setup>` without losing reactivity.\n2. **useTemplateRef()** — A new composable to get template refs.\n3. **Deferred Teleport** — Teleport supports deferred mounting.\n4. **useId()** — Generate unique IDs for SSR-friendly accessibility.\n\n' },
          { type: 'source-url', sourceId: 'src-1', url: 'https://blog.vuejs.org/posts/vue-3-5', title: 'Vue 3.5 Release Blog Post' },
          { type: 'source-url', sourceId: 'src-2', url: 'https://vuejs.org/api/', title: 'Vue.js API Reference' }
        ],
        createdAt: lastWeek
      })
    ]
  },

  // Multi-step with Step-Start + Source Document + Reasoning + Tool (综合)
  'mock-6': {
    chat: new Chat({
      id: 'mock-6',
      chat_id: 'mock-6',
      title: '【综合】多步骤工具调用 + 思考链 + 来源文档 + 图表',
      userId: 'mock-user',
      visibility: 'public',
      createdAt: lastMonth
    }),
    messages: [
      new Message({
        id: 'msg-6-1',
        chatId: 'mock-6',
        role: 'user',
        parts: [
          { type: 'text', text: 'Analyze the sales data and create a chart showing the trend.' },
          { type: 'file', mediaType: 'text/csv', filename: 'sales-2024.csv', url: 'https://placehold.co/600x200/png' }
        ],
        createdAt: lastMonth
      }),
      new Message({
        id: 'msg-6-2',
        chatId: 'mock-6',
        role: 'assistant',
        parts: [
          { type: 'step-start' },
          { type: 'reasoning', text: 'The user has uploaded a CSV file with sales data. I need to:\n1. Analyze the data in the CSV\n2. Identify trends and patterns\n3. Create a line chart visualization\n4. Provide a summary with source references' },
          { type: 'text', text: 'I\'ll analyze the sales data from your CSV file and create a visualization.' },
          {
            type: 'tool-createChart',
            toolCallId: 'call-chart-1',
            state: 'output-available',
            input: {
              title: 'Monthly Sales Trend 2024',
              data: [
                { month: 'Jan', revenue: 42000, profit: 12600 },
                { month: 'Feb', revenue: 38500, profit: 10780 },
                { month: 'Mar', revenue: 51200, profit: 16384 },
                { month: 'Apr', revenue: 47800, profit: 14340 },
                { month: 'May', revenue: 55600, profit: 18120 },
                { month: 'Jun', revenue: 62300, profit: 21760 }
              ],
              xKey: 'month',
              series: [
                { key: 'revenue', name: 'Revenue', color: '#3b82f6' },
                { key: 'profit', name: 'Profit', color: '#10b981' }
              ],
              xLabel: 'Month',
              yLabel: 'Amount (USD)'
            },
            output: {
              title: 'Monthly Sales Trend 2024',
              data: [
                { month: 'Jan', revenue: 42000, profit: 12600 },
                { month: 'Feb', revenue: 38500, profit: 10780 },
                { month: 'Mar', revenue: 51200, profit: 16384 },
                { month: 'Apr', revenue: 47800, profit: 14340 },
                { month: 'May', revenue: 55600, profit: 18120 },
                { month: 'Jun', revenue: 62300, profit: 21760 }
              ],
              xKey: 'month',
              series: [
                { key: 'revenue', name: 'Revenue', color: '#3b82f6' },
                { key: 'profit', name: 'Profit', color: '#10b981' }
              ],
              xLabel: 'Month',
              yLabel: 'Amount (USD)'
            }
          },
          { type: 'text', text: '\nHere\'s the analysis of your sales data:\n\n**Key Findings:**\n- Revenue shows a general **upward trend** from January to June\n- February had the lowest revenue at $38,500\n- June was the strongest month with $62,300 in revenue\n- Profit margins averaged around 30% across all months\n\nThe chart above visualizes the monthly revenue and profit trends.' },
          { type: 'source-document', sourceId: 'doc-1', mediaType: 'text/csv', title: 'Sales Data 2024', filename: 'sales-2024.csv' },
          { type: 'source-url', sourceId: 'src-1', url: 'https://example.com/sales-analytics-methodology', title: 'Sales Analytics Methodology' }
        ],
        createdAt: lastMonth
      })
    ]
  }
}

export default defineEventHandler(async (event) => {
  const id = getRouterParam(event, 'id')

  const entry = id ? mockChats[id] : undefined

  if (!entry) {
    throw createError({ statusCode: 404, statusMessage: 'Chat not found' })
  }

  const { chat, messages } = entry
  return {
    id: chat.id,
    title: chat.title,
    visibility: chat.visibility,
    createdAt: chat.createdAt,
    messages,
    isOwner: true
  }
})
