# File API Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate file browser APIs from flat routes to chat-scoped routes with nested tree data, aligning Nuxt frontend + server with the updated Flask backend.

**Architecture:** The Flask backend already has new URL paths under `/buildagent/v1/agent/chats/<chat_id>/workspace/output/files`. The Nuxt server proxies these through chat-scoped routes (`/api/v1/agent/chats/[id]/files`). The frontend fetches the complete tree once, then filters locally for flat-list display with breadcrumb navigation.

**Tech Stack:** Python/Flask (mock backend), Nuxt 4 server routes (h3), Vue 3 Composition API, Nuxt UI

---

### Task 1: Update Python `file_mock_data.py` — nested tree return and base64 content

**Files:**
- Modify: `scripts/python/server/file_mock_data.py`

- [ ] **Step 1: Rewrite `file_mock_data.py` with new data structure and API**

Replace the entire file content. The key changes:
- Remove all `~` prefixes from MOCK_FILE_TREE keys
- Change key format from `~path` to just the directory path (e.g., `src`, `src/components`)
- Root key changes from `"~"` to `"root"`
- `list_directory()` returns nested tree: `{ "files": [ { "filename", "type", "size?", "files?" } ] }`
- `get_file_content()` returns `{ "name", "size", "content" }` where content is base64-encoded
- Remove `language`, `downloadUrl`, `previewable` from `get_file_content()` return
- Remove `_get_language()`, `_is_previewable()` functions (moved to Nuxt server)

```python
"""
Mock file system data for the Flask file browser API.

Provides a simulated project directory tree with various file types
for testing the file browser panel.
"""

import base64


# Mock project directory tree
# Each entry: (name, type, size, content_or_children)
# type: "file" or "dir"
# For files: content_or_children = file content string
# For dirs: content_or_children = list of child entries
MOCK_FILE_TREE = {
    "root": [
        ("src", "dir", {
            "src": [
                ("components", "dir", {
                    "src/components": [
                        ("App.vue", "file", 890, '<template>\n  <div id="app">\n    <Header />\n    <RouterView />\n    <Footer />\n  </div>\n</template>\n\n<script setup lang="ts">\nimport Header from "./Header.vue"\nimport Footer from "./Footer.vue"\n</script>\n\n<style scoped>\n#app {\n  display: flex;\n  flex-direction: column;\n  min-height: 100vh;\n}\n</style>'),
                        ("Header.vue", "file", 654, '<template>\n  <header class="header">\n    <nav class="nav">\n      <RouterLink to="/" class="logo">MyApp</RouterLink>\n      <div class="nav-links">\n        <RouterLink to="/dashboard">Dashboard</RouterLink>\n        <RouterLink to="/settings">Settings</RouterLink>\n      </div>\n    </nav>\n  </header>\n</template>'),
                        ("Footer.vue", "file", 320, '<template>\n  <footer class="footer">\n    <p>&copy; 2026 MyApp. All rights reserved.</p>\n  </footer>\n</template>'),
                    ]
                }),
                ("utils", "dir", {
                    "src/utils": [
                        ("auth.ts", "file", 1234, 'import { createHash, randomBytes } from "crypto"\nimport jwt from "jsonwebtoken"\n\nconst SECRET = process.env.JWT_SECRET || "dev-secret"\nconst TOKEN_EXPIRY = "7d"\n\nexport interface TokenPayload {\n  userId: string\n  email: string\n  role: "admin" | "user"\n}\n\nexport function hashPassword(password: string): string {\n  const salt = randomBytes(16).toString("hex")\n  const hash = createHash("sha256")\n    .update(password + salt)\n    .digest("hex")\n  return `${salt}:${hash}`\n}\n\nexport function verifyPassword(password: string, stored: string): boolean {\n  const [salt, hash] = stored.split(":")\n  const verify = createHash("sha256")\n    .update(password + salt)\n    .digest("hex")\n  return verify === hash\n}\n\nexport function generateToken(payload: TokenPayload): string {\n  return jwt.sign(payload, SECRET, { expiresIn: TOKEN_EXPIRY })\n}\n\nexport function validateToken(token: string): TokenPayload {\n  return jwt.verify(token, SECRET) as TokenPayload\n}\n'),
                        ("config.ts", "file", 567, 'export const config = {\n  apiBaseUrl: process.env.API_URL || "http://localhost:3000",\n  wsUrl: process.env.WS_URL || "ws://localhost:3000",\n  debug: process.env.NODE_ENV === "development",\n  version: "1.0.0",\n} as const\n\nexport type Config = typeof config\n'),
                        ("logger.ts", "file", 445, 'type LogLevel = "debug" | "info" | "warn" | "error"\n\nfunction log(level: LogLevel, message: string, data?: unknown) {\n  const timestamp = new Date().toISOString()\n  const prefix = `[${timestamp}] [${level.toUpperCase()}]`\n  if (data) {\n    console[level](prefix, message, data)\n  } else {\n    console[level](prefix, message)\n  }\n}\n\nexport const logger = {\n  debug: (msg: string, data?: unknown) => log("debug", msg, data),\n  info: (msg: string, data?: unknown) => log("info", msg, data),\n  warn: (msg: string, data?: unknown) => log("warn", msg, data),\n  error: (msg: string, data?: unknown) => log("error", msg, data),\n}\n'),
                    ]
                }),
                ("pages", "dir", {
                    "src/pages": [
                        ("index.vue", "file", 312, '<template>\n  <div class="home">\n    <h1>Welcome to MyApp</h1>\n    <p>Get started by exploring the dashboard.</p>\n    <RouterLink to="/dashboard" class="btn">Go to Dashboard</RouterLink>\n  </div>\n</template>'),
                        ("dashboard.vue", "file", 1024, '<template>\n  <div class="dashboard">\n    <h1>Dashboard</h1>\n    <div class="stats-grid">\n      <div class="stat-card">\n        <h3>Total Users</h3>\n        <p class="stat-value">1,234</p>\n      </div>\n      <div class="stat-card">\n        <h3>Revenue</h3>\n        <p class="stat-value">$45,678</p>\n      </div>\n    </div>\n  </div>\n</template>'),
                    ]
                }),
                ("main.ts", "file", 289, 'import { createApp } from "vue"\nimport { createRouter, createWebHistory } from "vue-router"\nimport App from "./App.vue"\nimport { routes } from "./routes"\n\nconst router = createRouter({\n  history: createWebHistory(),\n  routes,\n})\n\nconst app = createApp(App)\napp.use(router)\napp.mount("#app")\n'),
                ("routes.ts", "file", 198, 'import type { RouteRecordRaw } from "vue-router"\n\nexport const routes: RouteRecordRaw[] = [\n  { path: "/", name: "home", component: () => import("./pages/index.vue") },\n  { path: "/dashboard", name: "dashboard", component: () => import("./pages/dashboard.vue") },\n]\n'),
            ]
        }),
        ("server", "dir", {
            "server": [
                ("api", "dir", {
                    "server/api": [
                        ("index.ts", "file", 432, 'import { H3Event } from "h3"\nimport { z } from "zod"\n\nconst QuerySchema = z.object({\n  page: z.coerce.number().default(1),\n  limit: z.coerce.number().default(20),\n})\n\nexport default defineEventHandler(async (event: H3Event) => {\n  const query = await getValidatedQuery(event, QuerySchema.parse)\n  return { status: "ok", data: [] }\n})\n'),
                    ]
                }),
                ("db", "dir", {
                    "server/db": [
                        ("schema.ts", "file", 512, 'import { sqliteTable, text, integer } from "drizzle-orm/sqlite-core"\n\nexport const users = sqliteTable("users", {\n  id: text("id").primaryKey(),\n  email: text("email").notNull().unique(),\n  name: text("name").notNull(),\n  avatar: text("avatar"),\n  createdAt: integer("created_at").notNull(),\n})\n'),
                    ]
                }),
            ]
        }),
        ("tests", "dir", {
            "tests": [
                ("auth.test.ts", "file", 890, 'import { describe, it, expect } from "vitest"\nimport { hashPassword, verifyPassword, generateToken, validateToken } from "../src/utils/auth"\n\ndescribe("auth utilities", () => {\n  it("should hash and verify password", () => {\n    const password = "test-password"\n    const hashed = hashPassword(password)\n    expect(verifyPassword(password, hashed)).toBe(true)\n    expect(verifyPassword("wrong-password", hashed)).toBe(false)\n  })\n\n  it("should generate and validate JWT token", () => {\n    const payload = { userId: "123", email: "test@test.com", role: "user" as const }\n    const token = generateToken(payload)\n    const decoded = validateToken(token)\n    expect(decoded.userId).toBe(payload.userId)\n  })\n})\n'),
                ("config.test.ts", "file", 234, 'import { describe, it, expect } from "vitest"\nimport { config } from "../src/utils/config"\n\ndescribe("config", () => {\n  it("should have required fields", () => {\n    expect(config.apiBaseUrl).toBeDefined()\n    expect(config.version).toBe("1.0.0")\n  })\n})\n'),
            ]
        }),
        ("docs", "dir", {
            "docs": [
                ("README.md", "file", 756, "# MyApp Documentation\n\n## Getting Started\n\n### Prerequisites\n\n- Node.js >= 18\n- npm >= 9\n\n### Installation\n\n```bash\ngit clone https://github.com/example/myapp.git\ncd myapp\nnpm install\n```\n\n### Development\n\n```bash\nnpm run dev\n```\n\nThe app will be available at `http://localhost:3000`.\n\n## Architecture\n\nThis project uses:\n- **Vue 3** with Composition API\n- **Vue Router** for routing\n- **TypeScript** for type safety\n\n## License\n\nMIT\n"),
                ("API.md", "file", 445, "# API Reference\n\n## Authentication\n\nAll API endpoints require a valid JWT token in the `Authorization` header:\n\n```\nAuthorization: Bearer <token>\n```\n\n## Endpoints\n\n### GET /api/users\n\nList all users.\n\n**Response:**\n```json\n[\n  { \"id\": \"1\", \"name\": \"Alice\", \"email\": \"alice@example.com\" }\n]\n```\n"),
            ]
        }),
        ("assets", "dir", {
            "assets": [
                ("logo.png", "file", 15360, None),
                ("data.sqlite", "file", 204800, None),
                ("styles.css", "file", 289, "/* Global styles */\n:root {\n  --primary: #3b82f6;\n  --bg: #ffffff;\n  --text: #1f2937;\n}\n\nbody {\n  font-family: system-ui, sans-serif;\n  color: var(--text);\n  background: var(--bg);\n}\n\n.btn {\n  display: inline-flex;\n  padding: 8px 16px;\n  border-radius: 6px;\n  background: var(--primary);\n  color: white;\n  text-decoration: none;\n}\n"),
            ]
        }),
        ("package.json", "file", 512, '{\n  "name": "myapp",\n  "version": "1.0.0",\n  "private": true,\n  "scripts": {\n    "dev": "vite",\n    "build": "vue-tsc && vite build",\n    "preview": "vite preview",\n    "test": "vitest",\n    "lint": "eslint . --ext .ts,.vue"\n  },\n  "dependencies": {\n    "vue": "^3.4.0",\n    "vue-router": "^4.3.0",\n    "jsonwebtoken": "^9.0.0"\n  },\n  "devDependencies": {\n    "typescript": "^5.4.0",\n    "vite": "^5.2.0",\n    "vitest": "^1.6.0",\n    "vue-tsc": "^2.0.0"\n  }\n}\n'),
        ("tsconfig.json", "file", 378, '{\n  "compilerOptions": {\n    "target": "ES2022",\n    "module": "ESNext",\n    "moduleResolution": "bundler",\n    "strict": true,\n    "jsx": "preserve",\n    "resolveJsonModule": true,\n    "isolatedModules": true,\n    "esModuleInterop": true,\n    "lib": ["ES2022", "DOM"],\n    "skipLibCheck": true,\n    "paths": {\n      "@/*": ["./src/*"]\n    }\n  },\n  "include": ["src/**/*", "tests/**/*"],\n  "exclude": ["node_modules"]\n}\n'),
        (".gitignore", "file", 156, "node_modules/\ndist/\n.output/\n.env\n.env.local\n*.log\n.DS_Store\ncoverage/\n.cache/\n"),
        ("README.md", "file", 423, "# MyApp\n\nA modern web application built with Vue 3 and TypeScript.\n\n## Quick Start\n\n```bash\nnpm install\nnpm run dev\n```\n\n## Features\n\n- User authentication with JWT\n- Dashboard with real-time stats\n- Responsive design\n- TypeScript throughout\n\n## Project Structure\n\n```\nsrc/\n  components/   # Vue components\n  pages/        # Page components\n  utils/        # Utility functions\nserver/\n  api/          # API routes\n  db/           # Database schema\ntests/         # Test files\n```\n"),
        ("hotfix.patch", "file", 589, 'diff --git a/src/utils/auth.ts b/src/utils/auth.ts\nindex a1b2c3d..e4f5g6h 100644\n--- a/src/utils/auth.ts\n+++ b/src/utils/auth.ts\n@@ -15,6 +15,10 @@ const TOKEN_EXPIRY = "7d"\n \n export interface TokenPayload {\n   userId: string\n   email: string\n-  role: "admin" | "user"\n+  role: "admin" | "user" | "moderator"\n+  permissions: string[]\n }\n+\n+export const DEFAULT_PERMISSIONS = ["read"] as const\n'),
    ]
}


def _resolve_dir(path):
    """Resolve a path like '/src/utils' to the directory entry list, or None.

    Root path ('/' or '') returns the root entries.
    """
    key = path.strip("/")

    if not key:
        return MOCK_FILE_TREE["root"]

    parts = key.split("/")
    current_key = ""
    current_list = MOCK_FILE_TREE["root"]

    for part in parts:
        found = False
        for entry in current_list:
            if entry[0] == part and entry[1] == "dir":
                if current_key:
                    current_key = f"{current_key}/{part}"
                else:
                    current_key = part
                current_list = entry[2][current_key]
                found = True
                break
        if not found:
            return None
    return current_list


def _resolve_file(path):
    """Resolve a file path to (entry_tuple, parent_entries) or (None, None)."""
    if not path or path == "/":
        return None, None

    parts = path.strip("/").split("/")
    filename = parts[-1]
    dir_parts = parts[:-1]

    if not dir_parts:
        parent = MOCK_FILE_TREE["root"]
    else:
        parent = _resolve_dir("/" + "/".join(dir_parts))
        if parent is None:
            return None, None

    for entry in parent:
        if entry[0] == filename and entry[1] == "file":
            return entry, parent
    return None, None


def list_directory(path="/", recursive=True, depth=2):
    """
    List directory contents at the given path.

    Returns a dict with nested 'files' array or None if path not found.
    Each entry: { "filename": str, "type": "dir"|"file", "size"?: int, "files"?: [...] }
    """
    entries_raw = _resolve_dir(path)
    if entries_raw is None:
        return None

    def build_tree(entries, current_depth):
        result = []
        # Sort: directories first, then files, both alphabetical
        sorted_entries = sorted(entries, key=lambda e: (e[1] != "dir", e[0].lower()))
        for entry in sorted_entries:
            name, entry_type = entry[0], entry[1]
            if entry_type == "dir":
                item = {
                    "filename": name,
                    "type": "dir",
                }
                if recursive and current_depth < depth:
                    # entry[2] is a dict with one key mapping to child list
                    child_dict = entry[2]
                    child_entries = list(child_dict.values())[0]
                    item["files"] = build_tree(child_entries, current_depth + 1)
                else:
                    item["files"] = []
                result.append(item)
            else:
                size = entry[2]
                result.append({
                    "filename": name,
                    "type": "file",
                    "size": size,
                })
        return result

    return {"files": build_tree(entries_raw, 0)}


def get_file_content(path):
    """
    Get file content at the given path.

    Returns a dict with name, size, content (base64) or None if not found.
    """
    entry, _ = _resolve_file(path)
    if entry is None:
        return None

    name, _, size, content = entry

    if content is not None:
        encoded = base64.b64encode(content.encode("utf-8")).decode("ascii")
    else:
        encoded = None

    return {
        "name": name,
        "size": size,
        "content": encoded,
    }


def file_exists(path):
    """Check if a file exists at the given path."""
    entry, _ = _resolve_file(path)
    return entry is not None
```

- [ ] **Step 2: Verify Python syntax**

Run: `cd D:\codes\BuildMate\chat\scripts\python\server && python -c "import file_mock_data; print('OK')"`

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add scripts/python/server/file_mock_data.py
git commit -m "refactor(python): rewrite file_mock_data for nested tree and base64 content"
```

---

### Task 2: Update Python `app.py` — new response format for file endpoints

**Files:**
- Modify: `scripts/python/server/app.py`

- [ ] **Step 1: Update `list_files` endpoint**

In `scripts/python/server/app.py`, replace the `list_files` function (lines 131-144):

```python
@app.route("/buildagent/v1/agent/chats/<chat_id>/workspace/output/files", methods=["GET"])
def list_files():
    """List directory contents as nested tree."""
    path = request.args.get("filepath", "/")
    recursive = request.args.get("recursive", "true").lower() == "true"
    depth = int(request.args.get("depth", "2"))
    if not _validate_path(path):
        return jsonify({"error": "Invalid path"}), 400

    result = list_directory(path, recursive=recursive, depth=depth)
    if result is None:
        return jsonify({"error": "Directory not found"}), 404

    return jsonify({"data": result})
```

- [ ] **Step 2: Update `get_file_content_endpoint`**

Replace the `get_file_content_endpoint` function (lines 147-160):

```python
@app.route("/buildagent/v1/agent/chats/<chat_id>/workspace/output/files/content", methods=["GET"])
def get_file_content_endpoint():
    """Get file content and metadata."""
    path = request.args.get("filepath")
    if not path:
        return jsonify({"error": "Missing required parameter: filepath"}), 400
    if not _validate_path(path):
        return jsonify({"error": "Invalid path"}), 400

    content = get_file_content(path)
    if content is None:
        return jsonify({"error": "File not found"}), 404

    return jsonify({"data": content, "error": ""})
```

- [ ] **Step 3: Update `download_file` endpoint**

Replace the `download_file` function (lines 163-190):

```python
@app.route("/buildagent/v1/agent/chats/<chat_id>/workspace/output/files/download", methods=["GET"])
def download_file():
    """Download a file as binary attachment."""
    path = request.args.get("filepath")
    if not path:
        return jsonify({"error": "Missing required parameter: filepath"}), 400
    if not _validate_path(path):
        return jsonify({"error": "Invalid path"}), 400

    if not file_exists(path):
        return jsonify({"error": "File not found"}), 404

    filename = os.path.basename(path)
    file_info = get_file_content(path)

    if file_info.get("content") is not None:
        # Text files: decode base64 and serve actual content
        import base64
        buffer = BytesIO(base64.b64decode(file_info["content"]))
    else:
        # Binary/mock files: generate placeholder content
        buffer = BytesIO(f"[Mock binary content for {filename}]".encode("utf-8"))

    return send_file(
        buffer,
        as_attachment=True,
        download_name=filename,
        mimetype="application/octet-stream",
    )
```

- [ ] **Step 4: Verify Flask app starts**

Run: `cd D:\codes\BuildMate\chat\scripts\python\server && python -c "from app import app; print('Flask app loaded OK')"`

Expected: `Flask app loaded OK`

- [ ] **Step 5: Commit**

```bash
git add scripts/python/server/app.py
git commit -m "refactor(python): update file endpoints for new response format"
```

---

### Task 3: Create new Nuxt server API routes

**Files:**
- Create: `server/api/v1/agent/chats/[id]/files.get.ts`
- Create: `server/api/v1/agent/chats/[id]/files/content.get.ts`
- Create: `server/api/v1/agent/chats/[id]/files/download.get.ts`

- [ ] **Step 1: Create the directory structure**

Run: `mkdir -p "D:\codes\BuildMate\chat\server\api\v1\agent\chats\[id]\files"`

- [ ] **Step 2: Create `files.get.ts`**

Create file `server/api/v1/agent/chats/[id]/files.get.ts`:

```typescript
export default defineEventHandler(async (event) => {
  const chatId = getRouterParam(event, 'id')
  if (!chatId) {
    throw createError({ statusCode: 400, statusMessage: 'Chat ID is required' })
  }

  const query = getQuery(event)
  const filepath = (query.filepath as string) || '/'

  return await useInternalService<{
    files: Array<{
      filename: string
      type: 'dir' | 'file'
      size?: number
      files?: Array<unknown>
    }>
  }>(event, `/buildagent/v1/agent/chats/${chatId}/workspace/output/files`, {
    params: { filepath, recursive: 'true', depth: '2' }
  })
})
```

- [ ] **Step 3: Create `files/content.get.ts`**

Create file `server/api/v1/agent/chats/[id]/files/content.get.ts`:

```typescript
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
    name: string
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
    { params: { filepath: path } }
  )

  if (flaskResponse.error) {
    throw createError({ statusCode: 400, statusMessage: flaskResponse.error })
  }

  const { name, size, content } = flaskResponse.data

  // Decode base64 content
  let decodedContent: string | null = null
  if (content) {
    decodedContent = Buffer.from(content, 'base64').toString('utf-8')
  }

  return {
    name,
    language: getLanguage(name),
    size,
    content: decodedContent,
    previewable: isPreviewable(name),
  }
})
```

- [ ] **Step 4: Create `files/download.get.ts`**

Create file `server/api/v1/agent/chats/[id]/files/download.get.ts`:

```typescript
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

  const res = await useInternalService<ArrayBuffer>(
    event,
    `/buildagent/v1/agent/chats/${chatId}/workspace/output/files/download`,
    { params: { filepath: path } }
  )

  const filename = path.split('/').pop() || 'file'
  setResponseHeader(event, 'content-type', 'application/octet-stream')
  setResponseHeader(event, 'content-disposition', `attachment; filename="${filename}"`)
  return res
})
```

- [ ] **Step 5: Commit**

```bash
git add server/api/v1/agent/chats/\[id\]/files/
git commit -m "feat(server): add chat-scoped file API routes"
```

---

### Task 4: Delete old Nuxt server API routes

**Files:**
- Delete: `server/api/v1/files.get.ts`
- Delete: `server/api/v1/files/content.get.ts`
- Delete: `server/api/v1/files/download.get.ts`

- [ ] **Step 1: Delete old files**

Run:
```bash
rm "D:\codes\BuildMate\chat\server\api\v1\files.get.ts"
rm "D:\codes\BuildMate\chat\server\api\v1\files\content.get.ts"
rm "D:\codes\BuildMate\chat\server\api\v1\files\download.get.ts"
```

If the `files` directory is now empty, remove it:
```bash
rmdir "D:\codes\BuildMate\chat\server\api\v1\files" 2>/dev/null || true
```

- [ ] **Step 2: Commit**

```bash
git add -u server/api/v1/files.get.ts server/api/v1/files/
git commit -m "chore(server): remove old flat file API routes"
```

---

### Task 5: Update `FileList.vue` — chatId prop, tree data, local filtering

**Files:**
- Modify: `app/components/file/FileList.vue`

- [ ] **Step 1: Rewrite `FileList.vue`**

Replace the entire file content:

```vue
<script setup lang="ts">
interface TreeEntry {
  filename: string
  type: 'dir' | 'file'
  size?: number
  files?: TreeEntry[]
}

interface FileEntry {
  name: string
  path: string
  type: 'dir' | 'file'
  size?: number
}

const props = defineProps<{
  chatId: string
  currentPath: string
  selectedFilePath: string | null
}>()

const emit = defineEmits<{
  navigate: [path: string]
  selectFile: [path: string]
}>()

const treeData = ref<TreeEntry[] | null>(null)
const pending = ref(false)
const error = ref<Error | null>(null)

async function fetchTree() {
  pending.value = true
  error.value = null
  try {
    const result = await $fetch<{ files: TreeEntry[] }>(`/api/v1/agent/chats/${props.chatId}/files`, {
      query: { filepath: '/' }
    })
    treeData.value = result.files
  } catch (e: unknown) {
    error.value = e instanceof Error ? e : new Error(String(e))
  } finally {
    pending.value = false
  }
}

fetchTree()

defineExpose({ refresh: fetchTree })

// Find a node in the tree by path segments
function findNode(path: string): TreeEntry[] | null {
  if (path === '/' || path === '') return treeData.value
  const segments = path.split('/').filter(Boolean)
  let current = treeData.value
  for (const segment of segments) {
    if (!current) return null
    const node = current.find(e => e.filename === segment && e.type === 'dir')
    if (!node || !node.files) return null
    current = node.files
  }
  return current
}

// Flatten current directory entries for display
const entries = computed<FileEntry[]>(() => {
  const nodes = findNode(props.currentPath)
  if (!nodes) return []

  return nodes.map(node => {
    const prefix = props.currentPath === '/' ? '' : props.currentPath
    const entryPath = `${prefix}/${node.filename}`
    return {
      name: node.filename,
      path: entryPath,
      type: node.type,
      size: node.type === 'file' ? node.size : undefined,
    }
  })
})

// Breadcrumb segments
const breadcrumbs = computed(() => {
  if (!props.currentPath || props.currentPath === '/') {
    return []
  }
  const segments = props.currentPath.split('/').filter(Boolean)
  return segments.map((segment, index) => ({
    label: segment,
    path: '/' + segments.slice(0, index + 1).join('/')
  }))
})

function navigateTo(path: string) {
  emit('navigate', path)
}

function selectFile(entry: FileEntry) {
  emit('selectFile', entry.path)
}

function getFileIcon(entry: FileEntry): string {
  if (entry.type === 'dir') {
    return 'i-lucide-folder'
  }
  // Basic icon mapping by extension
  const name = entry.name.toLowerCase()
  const extMap: Record<string, string> = {
    '.ts': 'i-lucide-file-code-2', '.tsx': 'i-lucide-file-code-2',
    '.js': 'i-lucide-file-code-2', '.jsx': 'i-lucide-file-code-2',
    '.vue': 'i-lucide-file-code-2', '.py': 'i-lucide-file-code-2',
    '.json': 'i-lucide-braces', '.md': 'i-lucide-file-text',
    '.css': 'i-lucide-file-code-2', '.html': 'i-lucide-file-code-2',
    '.sql': 'i-lucide-database', '.sh': 'i-lucide-file-code-2',
    '.yml': 'i-lucide-file-text', '.yaml': 'i-lucide-file-text',
    '.toml': 'i-lucide-file-text', '.xml': 'i-lucide-file-text',
    '.patch': 'i-lucide-git-compare', '.diff': 'i-lucide-git-compare',
  }
  for (const [ext, icon] of Object.entries(extMap)) {
    if (name.endsWith(ext)) return icon
  }
  if (name === 'dockerfile') return 'i-lucide-container'
  return 'i-lucide-file'
}

function formatFileSize(bytes?: number): string {
  if (bytes == null) return ''
  if (bytes === 0) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  const size = bytes / Math.pow(1024, i)
  return `${size.toFixed(i === 0 ? 0 : 1)} ${units[i]}`
}

function isFileSelected(entry: FileEntry): boolean {
  return entry.type === 'file' && entry.path === props.selectedFilePath
}
</script>

<template>
  <div class="flex flex-col h-full">
    <!-- Breadcrumb bar -->
    <div class="flex items-center gap-1 px-3 py-2 border-b border-default bg-elevated/30 text-sm overflow-x-auto shrink-0">
      <button
        class="flex items-center gap-1 text-muted hover:text-highlighted transition-colors px-1.5 py-0.5 rounded hover:bg-elevated/50"
        @click="navigateTo('/')"
      >
        <UIcon name="i-lucide-home" class="size-4" />
      </button>
      <template v-for="crumb in breadcrumbs" :key="crumb.path">
        <UIcon name="i-lucide-chevron-right" class="size-3 text-muted shrink-0" />
        <button
          class="text-muted hover:text-highlighted transition-colors px-1.5 py-0.5 rounded hover:bg-elevated/50 whitespace-nowrap"
          @click="navigateTo(crumb.path)"
        >
          {{ crumb.label }}
        </button>
      </template>
    </div>

    <!-- Loading state -->
    <div v-if="pending" class="flex items-center justify-center gap-2 py-12 text-muted">
      <UIcon name="i-lucide-loader-2" class="size-5 animate-spin" />
      <span>加载中...</span>
    </div>

    <!-- Error state -->
    <div v-else-if="error" class="flex flex-col items-center justify-center gap-3 py-12 text-error">
      <UIcon name="i-lucide-alert-circle" class="size-6" />
      <span class="text-sm">加载失败</span>
      <UButton
        size="xs"
        variant="ghost"
        icon="i-lucide-refresh-cw"
        label="重试"
        @click="fetchTree()"
      />
    </div>

    <!-- Empty directory -->
    <div v-else-if="entries.length === 0 && treeData !== null" class="flex flex-col items-center justify-center gap-2 py-12 text-muted">
      <UIcon name="i-lucide-folder-open" class="size-8" />
      <span class="text-sm">此目录为空</span>
    </div>

    <!-- File list -->
    <div v-else-if="treeData !== null" class="flex-1 overflow-y-auto">
      <button
        v-for="entry in entries"
        :key="entry.path"
        class="w-full flex items-center gap-3 px-3 py-2 text-sm transition-colors hover:bg-elevated/50 cursor-pointer"
        :class="isFileSelected(entry) ? 'bg-elevated/80 border-l-2 border-primary' : 'border-l-2 border-transparent'"
        @click="entry.type === 'dir' ? navigateTo(entry.path) : selectFile(entry)"
      >
        <UIcon :name="getFileIcon(entry)" class="size-4 shrink-0" :class="entry.type === 'dir' ? 'text-primary' : 'text-muted'" />
        <span class="flex-1 text-left truncate text-highlighted">{{ entry.name }}</span>
        <span v-if="entry.type === 'file' && entry.size != null" class="text-xs text-muted whitespace-nowrap">
          {{ formatFileSize(entry.size) }}
        </span>
      </button>
    </div>
  </div>
</template>
```

- [ ] **Step 2: Commit**

```bash
git add app/components/file/FileList.vue
git commit -m "refactor(frontend): FileList uses chat-scoped API with local tree filtering"
```

---

### Task 6: Update `FilePreview.vue` — chatId prop, new URLs

**Files:**
- Modify: `app/components/file/FilePreview.vue`

- [ ] **Step 1: Update `FilePreview.vue`**

In `app/components/file/FilePreview.vue`, make these changes:

**Change 1:** Add `chatId` prop and update the `FileContentResponse` interface (remove `downloadUrl`):

Replace lines 5-17 with:
```typescript
interface FileContentResponse {
  name: string
  language: string | null
  size: number
  content: string | null
  previewable: boolean
}

const props = defineProps<{
  chatId: string
  filePath: string | null
  embedded?: boolean
}>()
```

**Change 2:** Update `fetchData` to use new URL (replace lines 28-41):

```typescript
async function fetchData() {
  if (!props.filePath) return
  pending.value = true
  error.value = null
  try {
    data.value = await $fetch<FileContentResponse>(`/api/v1/agent/chats/${props.chatId}/files/content`, {
      query: { path: props.filePath }
    })
  } catch (e: unknown) {
    error.value = e instanceof Error ? e : new Error(String(e))
  } finally {
    pending.value = false
  }
}
```

**Change 3:** Update `downloadUrl` computed (replace lines 182-185):

```typescript
const downloadUrl = computed(() => {
  if (!props.filePath) return ''
  return `/api/v1/agent/chats/${props.chatId}/files/download?path=${encodeURIComponent(props.filePath)}`
})
```

- [ ] **Step 2: Commit**

```bash
git add app/components/file/FilePreview.vue
git commit -m "refactor(frontend): FilePreview uses chat-scoped API URLs"
```

---

### Task 7: Update `BrowserPanel.vue` — chatId prop, path `/`

**Files:**
- Modify: `app/components/file/BrowserPanel.vue`

- [ ] **Step 1: Update `BrowserPanel.vue`**

In `app/components/file/BrowserPanel.vue`, make these changes:

**Change 1:** Add `chatId` prop (replace lines 2-5):

```typescript
const props = defineProps<{
  chatId: string
  open: boolean
  maximizedFile: string | null
}>()
```

**Change 2:** Change initial `currentPath` from `'~'` to `'/'` (line 14):

```typescript
const currentPath = ref('/')
```

**Change 3:** Reset `currentPath` to `'/'` on panel open (replace lines 61-67):

```typescript
watch(() => props.open, (newVal) => {
  if (newVal) {
    currentPath.value = '/'
    selectedFilePath.value = null
    panelWidth.value = DEFAULT_WIDTH
  }
})
```

**Change 4:** Pass `chatId` to child components in the template.

Replace the `FileList` usage (lines 116-121):
```html
        <FileList
          :chat-id="chatId"
          :current-path="currentPath"
          :selected-file-path="selectedFilePath"
          @navigate="onNavigate"
          @select-file="onSelectFile"
        />
```

Replace the `FilePreview` usage (lines 130-134):
```html
        <FilePreview
          :chat-id="chatId"
          :file-path="selectedFilePath"
          :embedded="true"
          @maximize="onMaximize"
        />
```

- [ ] **Step 2: Commit**

```bash
git add app/components/file/BrowserPanel.vue
git commit -m "refactor(frontend): BrowserPanel adds chatId prop, uses / root path"
```

---

### Task 8: Update `chat/[id].vue` — pass chatId to FileBrowserPanel

**Files:**
- Modify: `app/pages/chat/[id].vue`

- [ ] **Step 1: Pass chatId to FileBrowserPanel**

In `app/pages/chat/[id].vue`, update the `FileBrowserPanel` usage in the template.

Replace lines 260-265:
```html
        <FileBrowserPanel
          :chat-id="String(route.params.id)"
          v-model:open="panelOpen"
          :maximized-file="maximizedFile"
          @maximize="onFileMaximize"
          @select-file="onFileSelected"
        />
```

Also update the maximized `FilePreview` usage (lines 250-254):
```html
                <FilePreview
                  :chat-id="String(route.params.id)"
                  :file-path="maximizedFile"
                  :embedded="false"
                  @maximize="onMinimizePreview"
                />
```

- [ ] **Step 2: Commit**

```bash
git add app/pages/chat/\\[id\\].vue
git commit -m "feat(frontend): pass chatId to FileBrowserPanel and FilePreview"
```

---

### Task 9: Manual smoke test

- [ ] **Step 1: Start Flask server**

Run: `cd D:\codes\BuildMate\chat\scripts\python\server && python app.py`

Expected: Flask running on port 5001

- [ ] **Step 2: Start Nuxt dev server**

Run: `cd D:\codes\BuildMate\chat && npm run dev`

Expected: Nuxt dev server starts

- [ ] **Step 3: Test file browser in browser**

1. Navigate to a chat page
2. Click the folder icon to open the file browser panel
3. Verify: root directory loads with all top-level files/dirs
4. Click a directory (e.g., `src`) - should show contents without loading spinner
5. Use breadcrumb to navigate back to root
6. Click a file - should show preview with content
7. Click download button - should trigger file download
8. Click maximize button - should show full-screen preview
