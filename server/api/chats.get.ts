import { Chat } from '#shared/chat'

const now = new Date()
const yesterday = new Date(now.getTime() - 24 * 60 * 60 * 1000)
const twoDaysAgo = new Date(now.getTime() - 2 * 24 * 60 * 60 * 1000)
const lastWeek = new Date(now.getTime() - 5 * 24 * 60 * 60 * 1000)
const lastMonth = new Date(now.getTime() - 20 * 24 * 60 * 60 * 1000)

const mockChats: Chat[] = [
  new Chat({
    id: 'mock-1',
    title: '【Text】纯文本对话',
    userId: 'mock-user',
    visibility: 'private',
    createdAt: now
  }),
  new Chat({
    id: 'mock-2',
    title: '【Reasoning】带思考链的回答',
    userId: 'mock-user',
    visibility: 'private',
    createdAt: yesterday
  }),
  new Chat({
    id: 'mock-3',
    title: '【File】带图片附件的对话',
    userId: 'mock-user',
    visibility: 'public',
    createdAt: twoDaysAgo
  }),
  new Chat({
    id: 'mock-4',
    title: '【Source URL】带来源引用的回答',
    userId: 'mock-user',
    visibility: 'private',
    createdAt: lastWeek
  }),
  new Chat({
    id: 'mock-5',
    title: '【Tool】带工具调用的对话（天气查询）',
    userId: 'mock-user',
    visibility: 'private',
    createdAt: lastMonth
  }),
  new Chat({
    id: 'mock-6',
    title: '【综合】多步骤工具调用 + 思考链 + 来源文档 + 图表',
    userId: 'mock-user',
    visibility: 'public',
    createdAt: lastMonth
  })
]

export default defineEventHandler(() => {
  return mockChats
})
