"""
Mock file system data for the Flask file browser API.

Provides a simulated project directory tree with various file types
for testing the file browser panel.
"""

import base64
import os


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
        ("README.md", "file", 423, "\n==================\n\n\n# MyApp\n\nA modern web application built with Vue 3 and TypeScript.\n\n## Quick Start\n\n```bash\nnpm install\nnpm run dev\n```\n\n## Features\n\n- User authentication with JWT\n- Dashboard with real-time stats\n- Responsive design\n- TypeScript throughout\n\n## Project Structure\n\n```\nsrc/\n  components/   # Vue components\n  pages/        # Page components\n  utils/        # Utility functions\nserver/\n  api/          # API routes\n  db/           # Database schema\ntests/         # Test files\n```\n"),
        ("hotfix.patch", "file", 589, 'diff --git a/src/utils/auth.ts b/src/utils/auth.ts\nindex a1b2c3d..e4f5g6h 100644\n--- a/src/utils/auth.ts\n+++ b/src/utils/auth.ts\n@@ -15,6 +15,10 @@ const TOKEN_EXPIRY = "7d"\n \n export interface TokenPayload {\n   userId: string\n   email: string\n-  role: "admin" | "user"\n+  role: "admin" | "user" | "moderator"\n+  permissions: string[]\n }\n+\n+export const DEFAULT_PERMISSIONS = ["read"] as const\n'),
    ]
}


def _load_code_patch_content():
    """Load code.patch content from current directory."""
    patch_path = os.path.join(os.path.dirname(__file__), "code.patch")
    with open(patch_path, "r", encoding="utf-8") as f:
        return f.read()


def _get_patch_payload(default_content):
    """Return patch text and byte size; fallback to default content."""
    try:
        patch_text = _load_code_patch_content()
    except (FileNotFoundError, OSError):
        patch_text = default_content or ""

    return patch_text, len(patch_text.encode("utf-8"))


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
        sorted_entries = sorted(entries, key=lambda e: (e[1] != "dir", e[0].lower()))
        for entry in sorted_entries:
            name, entry_type = entry[0], entry[1]
            if entry_type == "dir":
                item = {
                    "filename": name,
                    "type": "dir",
                }
                if recursive and current_depth < depth:
                    child_dict = entry[2]
                    child_entries = list(child_dict.values())[0]
                    item["files"] = build_tree(child_entries, current_depth + 1)
                else:
                    item["files"] = []
                result.append(item)
            else:
                size = entry[2]
                if name.endswith(".patch"):
                    _, size = _get_patch_payload(entry[3])
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

    if name.endswith(".patch"):
        content, size = _get_patch_payload(content)

    if content is not None:
        encoded = base64.b64encode(content.encode("utf-8")).decode("ascii")
    else:
        encoded = None

    return {
        "filepath": name,
        "size": size,
        "content": encoded,
    }


def file_exists(path):
    """Check if a file exists at the given path."""
    entry, _ = _resolve_file(path)
    return entry is not None
