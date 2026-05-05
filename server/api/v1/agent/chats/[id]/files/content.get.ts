const EXTENSION_LANGUAGE_MAP: Record<string, string> = {
  '.ts': 'typescript', '.tsx': 'typescript',
  '.js': 'javascript', '.jsx': 'javascript',
  '.vue': 'vue', '.py': 'python', '.css': 'css',
  '.html': 'html', '.json': 'json', '.md': 'markdown',
  '.yaml': 'yaml', '.yml': 'yaml', '.toml': 'toml',
  '.sql': 'sql', '.sh': 'bash', '.go': 'go',
  '.rs': 'rust', '.java': 'java', '.c': 'c', '.cpp': 'cpp',
  '.rb': 'ruby', '.php': 'php', '.swift': 'swift', '.kt': 'kotlin',
  '.graphql': 'graphql', '.xml': 'xml',
  '.diff': 'diff', '.patch': 'diff',
}

const PREVIEWABLE_EXTENSIONS = new Set(Object.keys(EXTENSION_LANGUAGE_MAP).concat([
  '.txt', '.env', '.gitignore', '.eslintrc', '.prettierrc',
  '.editorconfig', '.conf', '.cfg', '.ini', '.log', '.csv',
]))

function getLanguage(filename: string): string | null {
  if (filename === 'Dockerfile') return 'dockerfile'
  if (filename === 'Makefile') return 'makefile'
  for (const [ext, lang] of Object.entries(EXTENSION_LANGUAGE_MAP)) {
    if (filename.endsWith(ext)) return lang
  }
  return null
}

function isPreviewable(filename: string): boolean {
  if (['Dockerfile', 'Makefile', '.gitignore', '.env'].includes(filename)) return true
  for (const ext of PREVIEWABLE_EXTENSIONS) {
    if (filename.endsWith(ext)) return true
  }
  return false
}

interface FlaskContentResponse {
  data: {
    filepath: string
    size: number
    content: string | null
  }
  error?: string
}

export default defineEventHandler(async (event) => {
  const chatId = getRouterParam(event, 'id')
  if (!chatId) {
    throw createError({ statusCode: 400, statusMessage: 'Chat ID is required' })
  }

  const query = getQuery(event)
  const path = query.path as string
  if (!path) {
    throw createError({ statusCode: 400, statusMessage: 'path parameter is required' })
  }

  const flaskResponse = await useInternalService<FlaskContentResponse>(
    event,
    `/buildagent/v1/agent/chats/${chatId}/workspace/output/files/content`,
    { params: { filepath: path.replace(/^\/+/, "") } }
  )

  if (flaskResponse.error) {
    throw createError({ statusCode: 400, statusMessage: flaskResponse.error })
  }

  const { filepath, size, content } = flaskResponse.data

  let decodedContent: string | null = null
  if (content) {
    decodedContent = Buffer.from(content, 'base64').toString('utf-8')
  }

  return {
    filepath,
    language: getLanguage(filepath),
    size,
    content: decodedContent,
    previewable: isPreviewable(filepath),
  }
})
