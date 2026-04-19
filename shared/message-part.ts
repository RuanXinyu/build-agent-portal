/**
 * Re-export message part types from the AI SDK.
 * These types are used by Nuxt UI's ChatMessage component.
 *
 * @see https://ui.nuxt.com/docs/components/chat-message
 */
export type {
  UIMessagePart as MessagePart,
  TextUIPart,
  ReasoningUIPart,
  SourceUrlUIPart,
  SourceDocumentUIPart,
  FileUIPart,
  StepStartUIPart,
  ToolUIPart,
  DynamicToolUIPart,
} from 'ai'
