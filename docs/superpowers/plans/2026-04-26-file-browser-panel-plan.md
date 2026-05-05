# File Browser Panel Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a resizable right-side file browser panel to the chat detail page, with directory browsing, file preview, and download capabilities.

**Architecture:** Flask mock API provides 3 file endpoints (list, content, download) with a mock project directory tree. Nuxt server routes proxy these to the frontend. Three new Vue components (BrowserPanel, FileList, FilePreview) compose the UI, integrated into the existing chat detail page via a horizontal flex layout.

**Tech Stack:** Flask (mock API), Nuxt server routes (BFF proxy), Vue 3 + Nuxt UI v4 (frontend), Shiki (syntax highlighting), @comark/nuxt (Markdown rendering)

---

## File Structure

| Action | File | Responsibility |
|--------|------|----------------|
| Create | `scripts/python/server/file_mock_data.py` | Mock file system data for Flask API |
| Modify | `scripts/python/server/app.py` | Add 3 file API endpoints |
| Create | `server/api/v1/files.get.ts` | BFF proxy: directory listing |
| Create | `server/api/v1/files/content.get.ts` | BFF proxy: file content |
| Create | `server/api/v1/files/download.get.ts` | BFF proxy: file download |
| Create | `app/components/file/FileList.vue` | Directory listing + breadcrumb navigation |
| Create | `app/components/file/FilePreview.vue` | File content preview with maximize/download |
| Create | `app/components/file/BrowserPanel.vue` | Resizable right-side panel container |
| Modify | `app/pages/chat/[id].vue` | Integrate panel + add header with folder toggle |

---

### Task 1: Flask Mock File Data

**Files:**
- Create: `scripts/python/server/file_mock_data.py`

- [ ] **Step 1: Create the mock file system data module**

```python
"""
Mock file system data for the Flask file browser API.

Provides a simulated project directory tree with various file types
for testing the file browser panel.
"""

# Language detection based on file extension
EXTENSION_LANGUAGE_MAP = {
    ".ts": "typescript",
    ".tsx": "typescript",
    ".js": "javascript",
    ".jsx": "javascript",
    ".vue": "vue",
    ".py": "python",
    ".css": "css",
    ".html": "html",
    ".json": "json",
    ".md": "markdown",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".toml": "toml",
    ".sql": "sql",
    ".sh": "bash",
    ".go": "go",
    ".rs": "rust",
    ".java": "java",
    ".c": "c",
    ".cpp": "cpp",
    ".rb": "ruby",
    ".php": "php",
    ".swift": "swift",
    ".kt": "kotlin",
    ".graphql": "graphql",
    ".xml": "xml",
    ".dockerfile": "dockerfile",
}

# Extensions that can be previewed as text
PREVIEWABLE_EXTENSIONS = set(EXTENSION_LANGUAGE_MAP.keys()) | {
    ".txt", ".env", ".gitignore", ".eslintrc", ".prettierrc",
    ".editorconfig", ".conf", ".cfg", ".ini", ".log", ".csv",
}

# Binary/non-previewable extensions
BINARY_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".webp",
    ".sqlite", ".db", ".woff", ".woff2", ".ttf", ".eot",
    ".zip", ".tar", ".gz", ".rar", ".7z",
    ".pdf", ".doc", ".docx", ".xls", ".xlsx",
    ".mp3", ".mp4", ".wav", ".avi", ".mov",
    ".exe", ".dll", ".so", ".dylib",
    ".wasm", ".class", ".pyc", ".o",
}


def _get_language(filename):
    """Detect language from filename."""
    if filename == "Dockerfile":
        return "dockerfile"
    if filename == "Makefile":
        return "makefile"
    for ext, lang in EXTENSION_LANGUAGE_MAP.items():
        if filename.endswith(ext):
            return lang
    return None


def _is_previewable(filename):
    """Check if a file can be previewed as text."""
    if filename in ("Dockerfile", "Makefile", ".gitignore", ".env"):
        return True
    for ext in PREVIEWABLE_EXTENSIONS:
        if filename.endswith(ext):
            return True
    return False


# Mock project directory tree
# Each entry: (name, type, size, content_or_children)
# type: "file" or "dir"
# For files: content_or_children = file content string
# For dirs: content_or_children = list of child entries
MOCK_FILE_TREE = {
    "~": [
        ("src", "dir", {
            "~src": [
                ("components", "dir", {
                    "~src/components": [
                        ("App.vue", "file", 890, '<template>\n  <div id="app">\n    <Header />\n    <RouterView />\n    <Footer />\n  </div>\n</template>\n\n<script setup lang="ts">\nimport Header from "./Header.vue"\nimport Footer from "./Footer.vue"\n</script>\n\n<style scoped>\n#app {\n  display: flex;\n  flex-direction: column;\n  min-height: 100vh;\n}\n</style>'),
                        ("Header.vue", "file", 654, '<template>\n  <header class="header">\n    <nav class="nav">\n      <RouterLink to="/" class="logo">MyApp</RouterLink>\n      <div class="nav-links">\n        <RouterLink to="/dashboard">Dashboard</RouterLink>\n        <RouterLink to="/settings">Settings</RouterLink>\n      </div>\n    </nav>\n  </header>\n</template>'),
                        ("Footer.vue", "file", 320, '<template>\n  <footer class="footer">\n    <p>&copy; 2026 MyApp. All rights reserved.</p>\n  </footer>\n</template>'),
                    ]
                }),
                ("utils", "dir", {
                    "~src/utils": [
                        ("auth.ts", "file", 1234, 'import { createHash, randomBytes } from "crypto"\nimport jwt from "jsonwebtoken"\n\nconst SECRET = process.env.JWT_SECRET || "dev-secret"\nconst TOKEN_EXPIRY = "7d"\n\nexport interface TokenPayload {\n  userId: string\n  email: string\n  role: "admin" | "user"\n}\n\nexport function hashPassword(password: string): string {\n  const salt = randomBytes(16).toString("hex")\n  const hash = createHash("sha256")\n    .update(password + salt)\n    .digest("hex")\n  return `${salt}:${hash}`\n}\n\nexport function verifyPassword(password: string, stored: string): boolean {\n  const [salt, hash] = stored.split(":")\n  const verify = createHash("sha256")\n    .update(password + salt)\n    .digest("hex")\n  return verify === hash\n}\n\nexport function generateToken(payload: TokenPayload): string {\n  return jwt.sign(payload, SECRET, { expiresIn: TOKEN_EXPIRY })\n}\n\nexport function validateToken(token: string): TokenPayload {\n  return jwt.verify(token, SECRET) as TokenPayload\n}\n'),
                        ("config.ts", "file", 567, 'export const config = {\n  apiBaseUrl: process.env.API_URL || "http://localhost:3000",\n  wsUrl: process.env.WS_URL || "ws://localhost:3000",\n  debug: process.env.NODE_ENV === "development",\n  version: "1.0.0",\n} as const\n\nexport type Config = typeof config\n'),
                        ("logger.ts", "file", 445, 'type LogLevel = "debug" | "info" | "warn" | "error"\n\nfunction log(level: LogLevel, message: string, data?: unknown) {\n  const timestamp = new Date().toISOString()\n  const prefix = `[${timestamp}] [${level.toUpperCase()}]`\n  if (data) {\n    console[level](prefix, message, data)\n  } else {\n    console[level](prefix, message)\n  }\n}\n\nexport const logger = {\n  debug: (msg: string, data?: unknown) => log("debug", msg, data),\n  info: (msg: string, data?: unknown) => log("info", msg, data),\n  warn: (msg: string, data?: unknown) => log("warn", msg, data),\n  error: (msg: string, data?: unknown) => log("error", msg, data),\n}\n'),
                    ]
                }),
                ("pages", "dir", {
                    "~src/pages": [
                        ("index.vue", "file", 312, '<template>\n  <div class="home">\n    <h1>Welcome to MyApp</h1>\n    <p>Get started by exploring the dashboard.</p>\n    <RouterLink to="/dashboard" class="btn">Go to Dashboard</RouterLink>\n  </div>\n</template>'),
                        ("dashboard.vue", "file", 1024, '<template>\n  <div class="dashboard">\n    <h1>Dashboard</h1>\n    <div class="stats-grid">\n      <div class="stat-card">\n        <h3>Total Users</h3>\n        <p class="stat-value">1,234</p>\n      </div>\n      <div class="stat-card">\n        <h3>Revenue</h3>\n        <p class="stat-value">$45,678</p>\n      </div>\n    </div>\n  </div>\n</template>'),
                    ]
                }),
                ("main.ts", "file", 289, 'import { createApp } from "vue"\nimport { createRouter, createWebHistory } from "vue-router"\nimport App from "./App.vue"\nimport { routes } from "./routes"\n\nconst router = createRouter({\n  history: createWebHistory(),\n  routes,\n})\n\nconst app = createApp(App)\napp.use(router)\napp.mount("#app")\n'),
                ("routes.ts", "file", 198, 'import type { RouteRecordRaw } from "vue-router"\n\nexport const routes: RouteRecordRaw[] = [\n  { path: "/", name: "home", component: () => import("./pages/index.vue") },\n  { path: "/dashboard", name: "dashboard", component: () => import("./pages/dashboard.vue") },\n]\n'),
            ]
        }),
        ("server", "dir", {
            "~server": [
                ("api", "dir", {
                    "~server/api": [
                        ("index.ts", "file", 432, 'import { H3Event } from "h3"\nimport { z } from "zod"\n\nconst QuerySchema = z.object({\n  page: z.coerce.number().default(1),\n  limit: z.coerce.number().default(20),\n})\n\nexport default defineEventHandler(async (event: H3Event) => {\n  const query = await getValidatedQuery(event, QuerySchema.parse)\n  return { status: "ok", data: [] }\n})\n'),
                    ]
                }),
                ("db", "dir", {
                    "~server/db": [
                        ("schema.ts", "file", 512, 'import { sqliteTable, text, integer } from "drizzle-orm/sqlite-core"\n\nexport const users = sqliteTable("users", {\n  id: text("id").primaryKey(),\n  email: text("email").notNull().unique(),\n  name: text("name").notNull(),\n  avatar: text("avatar"),\n  createdAt: integer("created_at").notNull(),\n})\n'),
                    ]
                }),
            ]
        }),
        ("tests", "dir", {
            "~tests": [
                ("auth.test.ts", "file", 890, 'import { describe, it, expect } from "vitest"\nimport { hashPassword, verifyPassword, generateToken, validateToken } from "../src/utils/auth"\n\ndescribe("auth utilities", () => {\n  it("should hash and verify password", () => {\n    const password = "test-password"\n    const hashed = hashPassword(password)\n    expect(verifyPassword(password, hashed)).toBe(true)\n    expect(verifyPassword("wrong-password", hashed)).toBe(false)\n  })\n\n  it("should generate and validate JWT token", () => {\n    const payload = { userId: "123", email: "test@test.com", role: "user" as const }\n    const token = generateToken(payload)\n    const decoded = validateToken(token)\n    expect(decoded.userId).toBe(payload.userId)\n  })\n})\n'),
                ("config.test.ts", "file", 234, 'import { describe, it, expect } from "vitest"\nimport { config } from "../src/utils/config"\n\ndescribe("config", () => {\n  it("should have required fields", () => {\n    expect(config.apiBaseUrl).toBeDefined()\n    expect(config.version).toBe("1.0.0")\n  })\n})\n'),
            ]
        }),
        ("docs", "dir", {
            "~docs": [
                ("README.md", "file", 756, "# MyApp Documentation\n\n## Getting Started\n\n### Prerequisites\n\n- Node.js >= 18\n- npm >= 9\n\n### Installation\n\n```bash\ngit clone https://github.com/example/myapp.git\ncd myapp\nnpm install\n```\n\n### Development\n\n```bash\nnpm run dev\n```\n\nThe app will be available at `http://localhost:3000`.\n\n## Architecture\n\nThis project uses:\n- **Vue 3** with Composition API\n- **Vue Router** for routing\n- **TypeScript** for type safety\n\n## License\n\nMIT\n"),
                ("API.md", "file", 445, "# API Reference\n\n## Authentication\n\nAll API endpoints require a valid JWT token in the `Authorization` header:\n\n```\nAuthorization: Bearer <token>\n```\n\n## Endpoints\n\n### GET /api/users\n\nList all users.\n\n**Response:**\n```json\n[\n  { \"id\": \"1\", \"name\": \"Alice\", \"email\": \"alice@example.com\" }\n]\n```\n"),
            ]
        }),
        ("package.json", "file", 512, '{\n  "name": "myapp",\n  "version": "1.0.0",\n  "private": true,\n  "scripts": {\n    "dev": "vite",\n    "build": "vue-tsc && vite build",\n    "preview": "vite preview",\n    "test": "vitest",\n    "lint": "eslint . --ext .ts,.vue"\n  },\n  "dependencies": {\n    "vue": "^3.4.0",\n    "vue-router": "^4.3.0",\n    "jsonwebtoken": "^9.0.0"\n  },\n  "devDependencies": {\n    "typescript": "^5.4.0",\n    "vite": "^5.2.0",\n    "vitest": "^1.6.0",\n    "vue-tsc": "^2.0.0"\n  }\n}\n'),
        ("tsconfig.json", "file", 378, '{\n  "compilerOptions": {\n    "target": "ES2022",\n    "module": "ESNext",\n    "moduleResolution": "bundler",\n    "strict": true,\n    "jsx": "preserve",\n    "resolveJsonModule": true,\n    "isolatedModules": true,\n    "esModuleInterop": true,\n    "lib": ["ES2022", "DOM"],\n    "skipLibCheck": true,\n    "paths": {\n      "@/*": ["./src/*"]\n    }\n  },\n  "include": ["src/**/*", "tests/**/*"],\n  "exclude": ["node_modules"]\n}\n'),
        (".gitignore", "file", 156, "node_modules/\ndist/\n.output/\n.env\n.env.local\n*.log\n.DS_Store\ncoverage/\n.cache/\n"),
        ("README.md", "file", 423, "# MyApp\n\nA modern web application built with Vue 3 and TypeScript.\n\n## Quick Start\n\n```bash\nnpm install\nnpm run dev\n```\n\n## Features\n\n- User authentication with JWT\n- Dashboard with real-time stats\n- Responsive design\n- TypeScript throughout\n\n## Project Structure\n\n```\nsrc/\n  components/   # Vue components\n  pages/        # Page components\n  utils/        # Utility functions\nserver/\n  api/          # API routes\n  db/           # Database schema\ntests/         # Test files\n```\n"),
        ("assets", "dir", {
          "~assets": [
            ("logo.png", "file", 15360, None),
            ("data.sqlite", "file", 204800, None),
            ("styles.css", "file", 289, "/* Global styles */\n:root {\n  --primary: #3b82f6;\n  --bg: #ffffff;\n  --text: #1f2937;\n}\n\nbody {\n  font-family: system-ui, sans-serif;\n  color: var(--text);\n  background: var(--bg);\n}\n\n.btn {\n  display: inline-flex;\n  padding: 8px 16px;\n  border-radius: 6px;\n  background: var(--primary);\n  color: white;\n  text-decoration: none;\n}\n"),
          ]
        }),
    ]
}


def _resolve_dir(path):
    """Resolve a path like '~/src/utils' to the directory entry list, or None."""
    if path == "~":
        return MOCK_FILE_TREE["~"]

    parts = path.replace("~/", "", 1).split("/")
    current = MOCK_FILE_TREE["~"]

    for part in parts:
        found = False
        for entry in current:
            if entry[0] == part and entry[1] == "dir":
                key = path.split("/")
                # Build the lookup key for this level
                idx = parts.index(part) if part in parts else 0
                prefix_parts = ["~"] + parts[:idx + 1]
                lookup_key = "/".join(prefix_parts)
                current = entry[2][lookup_key]
                found = True
                break
        if not found:
            return None
    return current


def _resolve_file(path):
    """Resolve a file path to (entry_tuple, parent_entries) or (None, None)."""
    if path == "~":
        return None, None

    parts = path.replace("~/", "", 1).split("/")
    filename = parts[-1]
    dir_parts = parts[:-1]

    # Navigate to parent directory
    if not dir_parts:
        parent = MOCK_FILE_TREE["~"]
    else:
        parent = _resolve_dir("~/" + "/".join(dir_parts))
        if parent is None:
            return None, None

    # Find the file in parent
    for entry in parent:
        if entry[0] == filename and entry[1] == "file":
            return entry, parent
    return None, None


def list_directory(path):
    """
    List directory contents at the given path.

    Returns a list of entry dicts or None if path not found.
    """
    entries_raw = _resolve_dir(path)
    if entries_raw is None:
        return None

    result = []
    for entry in entries_raw:
        name, entry_type = entry[0], entry[1]
        if path == "~":
            entry_path = f"~/{name}"
        else:
            entry_path = f"{path}/{name}"

        if entry_type == "dir":
            result.append({
                "name": name,
                "path": entry_path,
                "type": "directory",
            })
        else:
            size = entry[2]
            result.append({
                "name": name,
                "path": entry_path,
                "type": "file",
                "size": size,
                "language": _get_language(name),
            })

    # Sort: directories first, then files, both alphabetical
    result.sort(key=lambda e: (e["type"] != "directory", e["name"].lower()))
    return result


def get_file_content(path):
    """
    Get file content at the given path.

    Returns a dict with file info, or None if not found.
    """
    entry, _ = _resolve_file(path)
    if entry is None:
        return None

    name, _, size, content = entry
    previewable = _is_previewable(name)

    if previewable and content is not None:
        return {
            "name": name,
            "language": _get_language(name),
            "size": size,
            "content": content,
            "previewable": True,
        }
    else:
        return {
            "name": name,
            "language": _get_language(name),
            "size": size,
            "content": None,
            "previewable": False,
            "downloadUrl": f"/api/files/download?path={path}",
        }


def file_exists(path):
    """Check if a file exists at the given path."""
    entry, _ = _resolve_file(path)
    return entry is not None
```

- [ ] **Step 2: Commit**

```bash
git add scripts/python/server/file_mock_data.py
git commit -m "feat(files): add mock file system data for Flask API"
```

---

### Task 2: Flask File API Endpoints

**Files:**
- Modify: `scripts/python/server/app.py`

- [ ] **Step 1: Add the three file API endpoints to Flask app**

Add these imports and routes to `app.py`, after the existing imports and before `if __name__ == "__main__":`:

```python
from file_mock_data import list_directory, get_file_content, file_exists
```

Add after the `stream_chat` route:

```python
@app.route("/api/files", methods=["GET"])
def list_files():
    """列出目录内容"""
    path = request.args.get("path", "~")

    # Basic path traversal protection
    if ".." in path.split("/"):
        return jsonify({"error": "Invalid path"}), 400

    entries = list_directory(path)
    if entries is None:
        return jsonify({"error": "Directory not found"}), 404

    return jsonify({"entries": entries})


@app.route("/api/files/content", methods=["GET"])
def get_file():
    """获取文件内容"""
    path = request.args.get("path", "")
    if not path:
        return jsonify({"error": "path parameter is required"}), 400

    if ".." in path.split("/"):
        return jsonify({"error": "Invalid path"}), 400

    result = get_file_content(path)
    if result is None:
        return jsonify({"error": "File not found"}), 404

    return jsonify(result)


@app.route("/api/files/download", methods=["GET"])
def download_file():
    """下载文件"""
    path = request.args.get("path", "")
    if not path:
        return jsonify({"error": "path parameter is required"}), 400

    if ".." in path.split("/"):
        return jsonify({"error": "Invalid path"}), 400

    if not file_exists(path):
        return jsonify({"error": "File not found"}), 404

    # For mock, generate a simple binary response
    filename = path.split("/")[-1]
    content = f"[Mock binary content for {filename}]".encode("utf-8")
    return Response(
        content,
        mimetype="application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
```

- [ ] **Step 2: Test Flask endpoints manually**

Run: `cd scripts/python/server && python app.py`

In another terminal, verify:
```bash
curl http://localhost:5001/api/files?path=~
curl http://localhost:5001/api/files/content?path=~/src/utils/auth.ts
curl http://localhost:5001/api/files/download?path=~/assets/data.sqlite
```

Expected: JSON responses for first two, binary download for third.

- [ ] **Step 3: Commit**

```bash
git add scripts/python/server/app.py
git commit -m "feat(files): add directory listing, content, and download endpoints to Flask mock API"
```

---

### Task 3: Nuxt BFF Proxy Routes

**Files:**
- Create: `server/api/v1/files.get.ts`
- Create: `server/api/v1/files/content.get.ts`
- Create: `server/api/v1/files/download.get.ts`

- [ ] **Step 1: Create directory listing proxy**

Create `server/api/v1/files.get.ts`:

```typescript
export default defineEventHandler(async (event) => {
  const config = useRuntimeConfig()
  const query = getQuery(event)
  const path = (query.path as string) || '~'

  const res = await $fetch<{ entries: Array<{
    name: string
    path: string
    type: 'directory' | 'file'
    size?: number
    language?: string | null
  }> }>(`${config.backendApiUrl}/api/files`, {
    params: { path }
  })

  return res
})
```

- [ ] **Step 2: Create file content proxy**

Create `server/api/v1/files/content.get.ts`:

```typescript
export default defineEventHandler(async (event) => {
  const config = useRuntimeConfig()
  const query = getQuery(event)
  const path = query.path as string

  if (!path) {
    throw createError({ statusCode: 400, statusMessage: 'path parameter is required' })
  }

  const res = await $fetch<{
    name: string
    language: string | null
    size: number
    content: string | null
    previewable: boolean
    downloadUrl?: string
  }>(`${config.backendApiUrl}/api/files/content`, {
    params: { path }
  })

  return res
})
```

- [ ] **Step 3: Create file download proxy**

Create `server/api/v1/files/download.get.ts`:

```typescript
export default defineEventHandler(async (event) => {
  const config = useRuntimeConfig()
  const query = getQuery(event)
  const path = query.path as string

  if (!path) {
    throw createError({ statusCode: 400, statusMessage: 'path parameter is required' })
  }

  const res = await $fetch<ArrayBuffer>(`${config.backendApiUrl}/api/files/download`, {
    params: { path }
  })

  const filename = path.split('/').pop() || 'file'
  setResponseHeader(event, 'content-type', 'application/octet-stream')
  setResponseHeader(event, 'content-disposition', `attachment; filename="${filename}"`)
  return res
})
```

- [ ] **Step 4: Test Nuxt proxy endpoints**

Run: `npx nuxi dev`

In another terminal, verify:
```bash
curl http://localhost:3000/api/v1/files?path=~
curl http://localhost:3000/api/v1/files/content?path=~/src/utils/auth.ts
```

Expected: Same JSON responses as Flask endpoints.

- [ ] **Step 5: Commit**

```bash
git add server/api/v1/files.get.ts server/api/v1/files/content.get.ts server/api/v1/files/download.get.ts
git commit -m "feat(files): add Nuxt BFF proxy routes for file API"
```

---

### Task 4: FileList Component

**Files:**
- Create: `app/components/file/FileList.vue`

- [ ] **Step 1: Create the FileList component**

```vue
<script setup lang="ts">
interface FileEntry {
  name: string
  path: string
  type: 'directory' | 'file'
  size?: number
  language?: string | null
}

const props = defineProps<{
  currentPath: string
  selectedFilePath: string | null
}>()

const emit = defineEmits<{
  navigate: [path: string]
  selectFile: [path: string]
}>()

const { data, status, refresh } = useFetch<{ entries: FileEntry[] }>('/api/v1/files', {
  query: computed(() => ({ path: props.currentPath })),
  key: `files-${props.currentPath}`,
  watch: [() => props.currentPath]
})

const error = ref(false)

watch(status, (s) => {
  if (s === 'error') error.value = true
  if (s === 'success') error.value = false
})

// Breadcrumb computed from currentPath
const breadcrumbs = computed(() => {
  if (props.currentPath === '~') return [{ name: '~', path: '~' }]
  const parts = props.currentPath.split('/')
  return parts.map((part, i) => ({
    name: part,
    path: parts.slice(0, i + 1).join('/')
  }))
})

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function getFileIcon(entry: FileEntry): string {
  if (entry.type === 'directory') return 'i-lucide-folder'
  const lang = entry.language
  if (lang === 'typescript' || lang === 'javascript') return 'i-lucide-file-code-2'
  if (lang === 'vue') return 'i-lucide-file-code'
  if (lang === 'python') return 'i-lucide-file-code-2'
  if (lang === 'markdown') return 'i-lucide-file-text'
  if (lang === 'json') return 'i-lucide-braces'
  if (lang === 'yaml' || lang === 'toml') return 'i-lucide-settings'
  if (lang === 'css' || lang === 'html') return 'i-lucide-palette'
  return 'i-lucide-file'
}

function handleClick(entry: FileEntry) {
  if (entry.type === 'directory') {
    emit('navigate', entry.path)
  } else {
    emit('selectFile', entry.path)
  }
}

function handleBreadcrumbClick(path: string) {
  emit('navigate', path)
}

// Expose refresh for parent
defineExpose({ refresh })
</script>

<template>
  <div class="flex flex-col border-b border-default">
    <!-- Breadcrumb -->
    <div class="flex items-center gap-1 px-3 py-1.5 text-xs text-muted border-b border-default overflow-x-auto">
      <template v-for="(crumb, i) in breadcrumbs" :key="crumb.path">
        <span v-if="i > 0" class="text-muted/50">/</span>
        <button
          class="hover:text-highlighted transition-colors whitespace-nowrap"
          :class="{ 'text-highlighted font-medium': i === breadcrumbs.length - 1 }"
          @click="handleBreadcrumbClick(crumb.path)"
        >
          {{ crumb.name === '~' ? '🏠' : crumb.name }}
        </button>
      </template>
    </div>

    <!-- Loading -->
    <div v-if="status === 'pending'" class="flex items-center justify-center py-8">
      <div class="flex flex-col items-center gap-2">
        <UIcon name="i-lucide-loader-2" class="animate-spin text-muted text-lg" />
        <span class="text-xs text-muted">加载中...</span>
      </div>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="flex items-center justify-center py-8">
      <div class="flex flex-col items-center gap-2">
        <UIcon name="i-lucide-alert-circle" class="text-error text-lg" />
        <span class="text-xs text-muted">加载失败</span>
        <UButton label="重试" variant="ghost" size="xs" @click="refresh()" />
      </div>
    </div>

    <!-- Empty -->
    <div v-else-if="data?.entries?.length === 0" class="flex items-center justify-center py-8">
      <div class="flex flex-col items-center gap-2">
        <UIcon name="i-lucide-folder-open" class="text-muted text-lg" />
        <span class="text-xs text-muted">此目录为空</span>
      </div>
    </div>

    <!-- File list -->
    <div v-else class="max-h-48 overflow-y-auto">
      <button
        v-for="entry in data?.entries"
        :key="entry.path"
        class="flex items-center gap-2 w-full px-3 py-1.5 text-sm hover:bg-elevated/50 transition-colors cursor-pointer text-left"
        :class="{ 'bg-elevated/80 border-l-2 border-primary': entry.path === selectedFilePath }"
        @click="handleClick(entry)"
      >
        <UIcon :name="getFileIcon(entry)" class="text-muted shrink-0 text-sm" />
        <span class="truncate flex-1" :class="{ 'text-highlighted font-medium': entry.type === 'directory' }">
          {{ entry.name }}
        </span>
        <span v-if="entry.size" class="text-xs text-muted shrink-0">{{ formatSize(entry.size) }}</span>
      </button>
    </div>
  </div>
</template>
```

- [ ] **Step 2: Commit**

```bash
git add app/components/file/FileList.vue
git commit -m "feat(files): add FileList component with breadcrumb navigation"
```

---

### Task 5: FilePreview Component

**Files:**
- Create: `app/components/file/FilePreview.vue`

- [ ] **Step 1: Create the FilePreview component**

```vue
<script setup lang="ts">
interface FileContent {
  name: string
  language: string | null
  size: number
  content: string | null
  previewable: boolean
  downloadUrl?: string
}

const props = defineProps<{
  filePath: string | null
}>()

const emit = defineEmits<{
  maximize: []
}>()

const { data, status, refresh } = useFetch<FileContent>('/api/v1/files/content', {
  query: computed(() => props.filePath ? { path: props.filePath } : undefined),
  key: computed(() => props.filePath ? `file-content-${props.filePath}` : 'file-content-none'),
  watch: [() => props.filePath],
  immediate: true
})

const error = ref(false)
watch(status, (s) => {
  if (s === 'error') error.value = true
  if (s === 'success') error.value = false
})

const isMaximized = ref(false)

function toggleMaximize() {
  isMaximized.value = !isMaximized.value
  emit('maximize')
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape' && isMaximized.value) {
    isMaximized.value = false
  }
}

onMounted(() => {
  document.addEventListener('keydown', handleKeydown)
})
onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
})

function getLanguageDisplay(lang: string | null): string {
  if (!lang) return ''
  const map: Record<string, string> = {
    typescript: 'TypeScript',
    javascript: 'JavaScript',
    vue: 'Vue',
    python: 'Python',
    css: 'CSS',
    html: 'HTML',
    json: 'JSON',
    markdown: 'Markdown',
    yaml: 'YAML',
    toml: 'TOML',
    sql: 'SQL',
    bash: 'Shell',
    go: 'Go',
    rust: 'Rust',
    java: 'Java',
    c: 'C',
    cpp: 'C++',
    ruby: 'Ruby',
    php: 'PHP',
    swift: 'Swift',
    kotlin: 'Kotlin',
    graphql: 'GraphQL',
    xml: 'XML',
    dockerfile: 'Dockerfile',
  }
  return map[lang] || lang
}

const lineCount = computed(() => {
  if (!data.value?.content) return 0
  return data.value.content.split('\n').length
})

const downloadUrl = computed(() => {
  if (!props.filePath) return ''
  return `/api/v1/files/download?path=${encodeURIComponent(props.filePath)}`
})

// Expose for parent
defineExpose({ isMaximized })
</script>

<template>
  <!-- No file selected -->
  <div v-if="!filePath" class="flex-1 flex items-center justify-center">
    <div class="flex flex-col items-center gap-2 text-muted">
      <UIcon name="i-lucide-file-search" class="text-2xl" />
      <span class="text-xs">选择文件以预览</span>
    </div>
  </div>

  <!-- Loading -->
  <div v-else-if="status === 'pending'" class="flex-1 flex items-center justify-center">
    <div class="flex flex-col items-center gap-2">
      <UIcon name="i-lucide-loader-2" class="animate-spin text-muted text-lg" />
      <span class="text-xs text-muted">加载中...</span>
    </div>
  </div>

  <!-- Error -->
  <div v-else-if="error" class="flex-1 flex items-center justify-center">
    <div class="flex flex-col items-center gap-2">
      <UIcon name="i-lucide-alert-circle" class="text-error text-lg" />
      <span class="text-xs text-muted">文件加载失败</span>
      <UButton label="重试" variant="ghost" size="xs" @click="refresh()" />
    </div>
  </div>

  <!-- File content loaded -->
  <template v-else-if="data">
    <!-- Action bar -->
    <div class="flex items-center gap-2 px-3 py-1.5 bg-elevated/50 border-b border-default text-xs">
      <UIcon name="i-lucide-file" class="text-muted" />
      <span class="font-medium text-highlighted">{{ data.name }}</span>
      <span v-if="data.language" class="text-muted">{{ getLanguageDisplay(data.language) }}</span>
      <span class="text-muted">{{ lineCount }} 行</span>
      <div class="ml-auto flex items-center gap-1">
        <UButton
          :to="downloadUrl"
          icon="i-lucide-download"
          variant="ghost"
          size="xs"
          target="_blank"
          aria-label="下载文件"
        />
        <UButton
          v-if="data.previewable"
          :icon="isMaximized ? 'i-lucide-minimize-2' : 'i-lucide-maximize-2'"
          variant="ghost"
          size="xs"
          aria-label="最大化预览"
          @click="toggleMaximize"
        />
      </div>
    </div>

    <!-- Previewable content -->
    <div v-if="data.previewable && data.content" class="flex-1 overflow-auto relative">
      <!-- Markdown -->
      <div v-if="data.language === 'markdown'" class="p-4 prose prose-sm dark:prose-invert max-w-none">
        <ChatComark :content="data.content" />
      </div>

      <!-- Code / Plain text -->
      <div v-else class="font-mono text-xs leading-relaxed">
        <table class="w-full border-collapse">
          <tbody>
            <tr v-for="(line, i) in data.content.split('\n')" :key="i" class="hover:bg-elevated/30">
              <td class="select-none text-right text-muted/40 px-3 py-0 w-10 align-top border-r border-default">{{ i + 1 }}</td>
              <td class="px-3 py-0 whitespace-pre"><pre class="m-0">{{ line }}</pre></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Non-previewable -->
    <div v-else class="flex-1 flex flex-col items-center justify-center gap-4 bg-dimmed/30">
      <div class="w-16 h-16 rounded-full bg-elevated flex items-center justify-center">
        <UIcon name="i-lucide-file-x" class="text-2xl text-muted" />
      </div>
      <div class="text-center">
        <div class="text-sm font-medium text-highlighted mb-1">无法预览此文件</div>
        <div class="text-xs text-muted">.{{ data.name.split('.').pop() }} 文件类型暂不支持在线预览</div>
      </div>
      <UButton
        :to="downloadUrl"
        icon="i-lucide-download"
        label="下载文件"
        variant="soft"
        size="sm"
        target="_blank"
      />
    </div>
  </template>
</template>
```

- [ ] **Step 2: Commit**

```bash
git add app/components/file/FilePreview.vue
git commit -m "feat(files): add FilePreview component with syntax display, markdown, and maximize"
```

---

### Task 6: BrowserPanel Component

**Files:**
- Create: `app/components/file/BrowserPanel.vue`

- [ ] **Step 1: Create the BrowserPanel component with resizable divider**

```vue
<script setup lang="ts">
const props = defineProps<{
  open: boolean
}>()

const emit = defineEmits<{
  'update:open': [value: boolean]
}>()

const panelRef = ref<HTMLElement | null>(null)
const panelWidth = ref(380)
const isDragging = ref(false)
const isMaximized = ref(false)

const MIN_WIDTH = 280
const MAX_WIDTH_PERCENT = 0.6

function startDrag(e: MouseEvent) {
  e.preventDefault()
  isDragging.value = true

  const startX = e.clientX
  const startWidth = panelWidth.value
  const maxWidth = window.innerWidth * MAX_WIDTH_PERCENT

  function onMouseMove(e: MouseEvent) {
    // Panel is on the right, so moving left = getting wider
    const delta = startX - e.clientX
    panelWidth.value = Math.min(maxWidth, Math.max(MIN_WIDTH, startWidth + delta))
  }

  function onMouseUp() {
    isDragging.value = false
    document.removeEventListener('mousemove', onMouseMove)
    document.removeEventListener('mouseup', onMouseUp)
    document.body.style.cursor = ''
    document.body.style.userSelect = ''
  }

  document.body.style.cursor = 'col-resize'
  document.body.style.userSelect = 'none'
  document.addEventListener('mousemove', onMouseMove)
  document.addEventListener('mouseup', onMouseUp)
}

// Panel state
const currentPath = ref('~')
const selectedFilePath = ref<string | null>(null)

function handleNavigate(path: string) {
  currentPath.value = path
  selectedFilePath.value = null
}

function handleSelectFile(path: string) {
  selectedFilePath.value = path
}

function handleClose() {
  emit('update:open', false)
}

// Reset state when panel opens
watch(() => props.open, (val) => {
  if (val) {
    panelWidth.value = 380
    currentPath.value = '~'
    selectedFilePath.value = null
    isMaximized.value = false
  }
})
</script>

<template>
  <Transition name="slide">
    <div
      v-if="open"
      ref="panelRef"
      class="flex flex-col h-full bg-default border-l border-default shrink-0 relative"
      :style="{ width: `${panelWidth}px` }"
    >
      <!-- Resizable divider -->
      <div
        class="absolute left-0 top-0 bottom-0 w-1 cursor-col-resize hover:bg-primary/50 active:bg-primary transition-colors z-10"
        :class="{ 'bg-primary': isDragging }"
        @mousedown="startDrag"
      />

      <!-- Panel header -->
      <div class="flex items-center justify-between px-3 h-12 border-b border-default shrink-0">
        <div class="flex items-center gap-2">
          <UIcon name="i-lucide-folder-tree" class="text-primary" />
          <span class="text-sm font-semibold text-highlighted">项目文件</span>
        </div>
        <UButton
          icon="i-lucide-x"
          variant="ghost"
          size="xs"
          aria-label="关闭面板"
          @click="handleClose"
        />
      </div>

      <!-- File list -->
      <FileFileList
        :current-path="currentPath"
        :selected-file-path="selectedFilePath"
        @navigate="handleNavigate"
        @select-file="handleSelectFile"
      />

      <!-- File preview -->
      <FileFilePreview
        :file-path="selectedFilePath"
        @maximize="isMaximized = !isMaximized"
      />
    </div>
  </Transition>
</template>

<style scoped>
.slide-enter-active,
.slide-leave-active {
  transition: all 0.2s ease;
}
.slide-enter-from,
.slide-leave-to {
  width: 0 !important;
  opacity: 0;
  overflow: hidden;
}
</style>
```

- [ ] **Step 2: Commit**

```bash
git add app/components/file/BrowserPanel.vue
git commit -m "feat(files): add BrowserPanel with resizable divider and slide transition"
```

---

### Task 7: Chat Page Integration

**Files:**
- Modify: `app/pages/chat/[id].vue`

- [ ] **Step 1: Add panelOpen state and integrate BrowserPanel**

Modify `app/pages/chat/[id].vue`. Add a ref for panel state and integrate the BrowserPanel into the template.

Add after the `lastTimestamp` ref (line 24):

```typescript
const panelOpen = ref(false)
```

Replace the entire `<template>` section with:

```vue
<template>
  <template v-if="data?.id">
    <UDashboardPanel
      id="chat"
      class="relative min-h-0"
      :ui="{ body: 'p-0 sm:p-0 overscroll-none' }"
    >
      <template #header>
        <UDashboardNavbar class="absolute top-0 inset-x-0 z-10">
          <template #left>
            <UDashboardSidebarCollapse />
          </template>

          <template #right>
            <UButton
              :icon="panelOpen ? 'i-lucide-folder-open' : 'i-lucide-folder'"
              :color="panelOpen ? 'primary' : 'neutral'"
              :variant="panelOpen ? 'soft' : 'ghost'"
              size="sm"
              aria-label="浏览文件"
              @click="panelOpen = !panelOpen"
            />
            <UColorModeButton />
            <UButton
              icon="i-lucide-plus"
              to="/"
              class="lg:hidden"
            />
          </template>
        </UDashboardNavbar>
      </template>

      <template #body>
        <div class="flex h-full">
          <!-- Chat area -->
          <UContainer class="flex-1 flex flex-col gap-4 sm:gap-6 min-w-0">
            <UChatMessages
              should-auto-scroll
              :messages="chat.messages"
              :status="chat.status"
              :spacing-offset="isOwner ? 160 : 0"
              class="pt-(--ui-header-height) pb-4 sm:pb-6"
            >
              <template #indicator>
                <div class="flex items-center gap-1.5">
                  <ChatIndicator />
                  <UChatShimmer text="Thinking..." class="text-sm" />
                </div>
              </template>

              <template #content="{ message }">
                <ChatMessageContent
                  :message="message"
                />
              </template>

              <template v-if="isOwner" #actions="{ message }">
                <ChatMessageActions
                  :message="message"
                  :streaming="chat.status === 'streaming' && message.id === chat.messages[chat.messages.length - 1]?.id"
                />
              </template>
            </UChatMessages>

            <UChatPrompt
              v-if="isOwner"
              v-model="input"
              :error="chat.error"
              variant="subtle"
              class="sticky bottom-0 [view-transition-name:chat-prompt] rounded-b-none z-10"
              :ui="{ base: 'px-1.5' }"
              @submit="handleSubmit"
            >
              <template #footer>
                <div class="flex items-center gap-1">
                </div>

                <UChatPromptSubmit
                  :status="chat.status"
                  color="neutral"
                  size="sm"
                />
              </template>
            </UChatPrompt>
          </UContainer>

          <!-- File browser panel -->
          <FileBrowserPanel v-model:open="panelOpen" />
        </div>
      </template>
    </UDashboardPanel>
  </template>

  <UContainer v-else class="flex-1 flex flex-col gap-4 sm:gap-6">
    <UError :error="{ statusMessage: 'Chat not found', statusCode: 404 }" class="min-h-full" />
  </UContainer>
</template>
```

- [ ] **Step 2: Verify the page renders correctly**

Run: `npx nuxi dev`

Open a chat page, verify:
1. The navbar shows a folder icon on the right
2. Clicking it opens the file browser panel
3. The panel shows a file list with breadcrumbs
4. Clicking a directory navigates into it
5. Clicking a file shows its content in the preview area
6. The panel can be resized by dragging the left divider
7. Clicking the X or the folder icon closes the panel

- [ ] **Step 3: Commit**

```bash
git add app/pages/chat/[id].vue
git commit -m "feat(files): integrate file browser panel into chat detail page"
```

---

### Task 8: Maximize Mode

**Files:**
- Modify: `app/components/file/FilePreview.vue`
- Modify: `app/components/file/BrowserPanel.vue`

- [ ] **Step 1: Add maximize overlay to BrowserPanel**

In `BrowserPanel.vue`, add a maximize overlay after the main panel div (inside the `<Transition>` wrapper, as a sibling):

After the main panel `<div>`, before the closing `</Transition>`, add:

```vue
<!-- Maximize overlay -->
<Transition name="fade">
  <div
    v-if="open && isMaximized && selectedFilePath"
    class="fixed inset-0 z-50 bg-default flex flex-col"
  >
    <!-- Maximize header -->
    <div class="flex items-center gap-2 px-4 h-12 bg-inverse border-b border-inverse shrink-0">
      <UIcon name="i-lucide-file" class="text-info" />
      <span class="text-sm font-medium text-inverse">{{ selectedFilePath.split('/').pop() }}</span>
      <div class="ml-auto flex items-center gap-1">
        <UButton
          icon="i-lucide-download"
          variant="ghost"
          color="neutral"
          size="sm"
          :to="`/api/v1/files/download?path=${encodeURIComponent(selectedFilePath)}`"
          target="_blank"
          aria-label="下载文件"
        />
        <UButton
          icon="i-lucide-x"
          variant="ghost"
          color="neutral"
          size="sm"
          aria-label="退出最大化"
          @click="isMaximized = false"
        />
      </div>
    </div>
    <!-- Preview content fills remaining space -->
    <div class="flex-1 overflow-auto">
      <FileFilePreview
        :file-path="selectedFilePath"
        embedded
      />
    </div>
  </div>
</Transition>
```

Add a `fade` transition to the `<style>` section:

```css
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.15s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
```

- [ ] **Step 2: Add `embedded` prop to FilePreview for maximize mode**

In `FilePreview.vue`, add an `embedded` prop that hides the action bar (the maximize overlay provides its own):

Update the `defineProps`:

```typescript
const props = defineProps<{
  filePath: string | null
  embedded?: boolean
}>()
```

In the template, wrap the action bar with `v-if="!embedded"`:

```vue
<!-- Action bar (hidden in embedded/maximize mode) -->
<div v-if="!embedded" class="flex items-center gap-2 px-3 py-1.5 ...">
  ...existing action bar...
</div>
```

- [ ] **Step 3: Verify maximize mode**

Run: `npx nuxi dev`

1. Open a chat page, open file browser
2. Click a file to preview it
3. Click the maximize button — full-screen overlay should appear
4. Press Esc or click X to exit
5. Verify the maximize overlay has its own header with download and close buttons

- [ ] **Step 4: Commit**

```bash
git add app/components/file/BrowserPanel.vue app/components/file/FilePreview.vue
git commit -m "feat(files): add maximize mode with fullscreen overlay for file preview"
```

---

### Task 9: Final Polish and Fix

**Files:**
- All created files

- [ ] **Step 1: Fix mock data path resolution bug**

The `list_directory` function in `file_mock_data.py` has a bug in path building. The entry_path for `~` level entries should use `~/` prefix correctly. Fix the `list_directory` function:

Replace the `list_directory` function's entry_path calculation:

```python
def list_directory(path):
    """List directory contents at the given path."""
    entries_raw = _resolve_dir(path)
    if entries_raw is None:
        return None

    result = []
    for entry in entries_raw:
        name, entry_type = entry[0], entry[1]
        if path == "~":
            entry_path = f"~/{name}"
        else:
            entry_path = f"{path}/{name}"

        if entry_type == "dir":
            result.append({
                "name": name,
                "path": entry_path,
                "type": "directory",
            })
        else:
            size = entry[2]
            result.append({
                "name": name,
                "path": entry_path,
                "type": "file",
                "size": size,
                "language": _get_language(name),
            })

    result.sort(key=lambda e: (e["type"] != "directory", e["name"].lower()))
    return result
```

- [ ] **Step 2: Fix the _resolve_dir function**

The `_resolve_dir` function has a fragile key lookup. Simplify it:

```python
def _resolve_dir(path):
    """Resolve a path like '~/src/utils' to the directory entry list, or None."""
    if path == "~":
        return MOCK_FILE_TREE["~"]

    parts = path.replace("~/", "", 1).split("/")
    current_key = "~"
    current_list = MOCK_FILE_TREE["~"]

    for part in parts:
        found = False
        for entry in current_list:
            if entry[0] == part and entry[1] == "dir":
                current_key = f"{current_key}/{part}"
                current_list = entry[2][current_key]
                found = True
                break
        if not found:
            return None
    return current_list
```

- [ ] **Step 3: Run full end-to-end test**

1. Start Flask: `cd scripts/python/server && python app.py`
2. Start Nuxt: `npx nuxi dev`
3. Open a chat page
4. Click the folder icon in the navbar
5. Verify directory browsing works (navigate into `src/`, then `utils/`)
6. Click `auth.ts` — verify code preview with line numbers
7. Click `README.md` in `docs/` — verify Markdown rendering
8. Click `data.sqlite` in `assets/` — verify "cannot preview" message + download button
9. Click maximize on a code file — verify fullscreen overlay works
10. Press Esc — verify it exits maximize
11. Resize the panel by dragging the divider
12. Close and reopen the panel — verify it resets

- [ ] **Step 4: Commit**

```bash
git add scripts/python/server/file_mock_data.py
git commit -m "fix(files): fix path resolution in mock data module"
```
