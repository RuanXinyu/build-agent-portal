/**
 * Re-export message part types from the AI SDK.
 * These types are used by Nuxt UI's ChatMessage component.
 *
 * @see https://ui.nuxt.com/docs/components/chat-message
 */
import type { UIMessagePart, TextUIPart, ReasoningUIPart, SourceUrlUIPart, SourceDocumentUIPart, FileUIPart, StepStartUIPart, ToolUIPart, DynamicToolUIPart } from 'ai'

export type MessagePart = UIMessagePart<any, any>
export type { TextUIPart, ReasoningUIPart, SourceUrlUIPart, SourceDocumentUIPart, FileUIPart, StepStartUIPart, ToolUIPart, DynamicToolUIPart }
