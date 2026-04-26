# Simplify Chat Session Management

## Goal

Remove unnecessary chat session management features: visibility toggling, AI-generated titles, and chat deletion. Simplify to a leaner model where titles are derived from the first message prompt.

## Changes

### 1. Title: Replace AI generation with prompt substring

**Current**: When the first message is sent in a chat, `generateText` with `gpt-4.1-nano` is called to produce a title, then saved to the database. A `data-chat-title` stream event notifies the frontend to refresh the sidebar.

**New**: In `chats.post.ts`, extract the first 20 characters of the user's first message text and set it as the chat title at creation time.

Files to modify:
- `server/api/v1/agent/chats.post.ts` — extract first 20 chars from message text, set as `title`
- `server/api/v1/agent/chats/[id].post.ts` — remove the `generateText` title block and the `data-chat-title` stream event
- `app/pages/chat/[id].vue` — remove the `onData` handler for `data-chat-title`

### 2. Remove visibility completely

Files to delete:
- `server/api/v1/agent/chats/[id]/visibility.patch.ts`
- `app/components/chat/ChatVisibility.vue`

Files to modify:
- `server/db/schema.ts` — remove `visibility` column from `chats` table
- `shared/chat.ts` — remove `visibility` property from `Chat` class
- `app/pages/chat/[id].vue` — remove `visibility` ref and `<ChatVisibility>` component
- `server/api/v1/agent/chats/[id].get.ts` — remove `visibility` from mock response (if present)

Database:
- New migration to drop the `visibility` column from `chats` table

### 3. Remove chat deletion

Files to delete:
- `server/api/v1/agent/chats/[id].delete.ts` (already deleted in working tree)
- `app/components/ModalConfirm.vue`

Files to modify:
- `app/layouts/default.vue` — remove `deleteChat` function, `ModalConfirm` import/usage, sidebar delete button per chat item

## Out of Scope

- No changes to message sending, streaming, or AI model configuration
- No changes to authentication or user management
- No changes to the chat list grouping composable (`useChats.ts`)
- Database migration for removing visibility column will be generated via Drizzle
