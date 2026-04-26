<script setup lang="ts">
import { getToolName } from 'ai'
import { isToolStreaming } from '@nuxt/ui/utils/ai'

const props = defineProps<{
  part: {
    type: string
    toolCallId: string
    state: string
    input?: any
    output?: any
    title?: string
  }
}>()

const toolName = computed(() => {
  const name = props.part.type.startsWith('tool-') ? props.part.type.slice(5) : props.part.type
  return name
})

const toolIcon = computed(() => {
  const map: Record<string, string> = {
    bash: 'i-lucide-terminal',
    glob: 'i-lucide-search',
    read: 'i-lucide-file-text',
    grep: 'i-lucide-regex',
    write: 'i-lucide-file-plus',
    unknown: 'i-lucide-wrench',
  }
  return map[toolName.value] || 'i-lucide-wrench'
})

const streaming = computed(() => isToolStreaming(props.part))

const title = computed(() => {
  if (props.part.title) return props.part.title
  const name = toolName.value
  const map: Record<string, string> = {
    bash: 'Run command',
    glob: 'Search files',
    read: 'Read file',
    grep: 'Search content',
    write: 'Write file',
  }
  return map[name] || `Run ${name}`
})

const subtitle = computed(() => {
  const input = props.part.input
  if (!input) return ''
  switch (toolName.value) {
    case 'bash':
      return input.command || ''
    case 'glob':
      return input.pattern || ''
    case 'read':
      return input.file_path || input.filePath || ''
    case 'grep':
      return input.pattern || ''
    case 'write':
      return input.file_path || input.filePath || ''
    default:
      return ''
  }
})

const outputText = computed(() => {
  if (props.part.state !== 'output-available') return ''
  const output = props.part.output
  if (typeof output === 'string') return output
  if (output?.output && typeof output.output === 'string') return output.output
  return JSON.stringify(output, null, 2)
})

const outputTruncated = computed(() => outputText.value.length > 500)
const displayOutput = computed(() =>
  outputTruncated.value ? outputText.value.slice(0, 500) + '...' : outputText.value
)
</script>

<template>
  <UChatTool
    :icon="toolIcon"
    :text="title"
    :suffix="subtitle"
    :streaming="streaming"
    chevron="trailing"
    class="my-1"
  >
    <template #default="{ open }">
      <div v-if="open && outputText" class="space-y-2">
        <!-- Input section -->
        <div v-if="part.input" class="rounded-lg bg-elevated/50 border border-default overflow-hidden">
          <div class="px-3 py-1.5 text-xs font-medium text-muted border-b border-default flex items-center gap-1.5">
            <UIcon name="i-lucide-arrow-right" class="size-3" />
            Input
          </div>
          <pre class="p-3 text-sm text-highlighted overflow-x-auto whitespace-pre-wrap break-all"><code>{{ typeof part.input === 'string' ? part.input : JSON.stringify(part.input, null, 2) }}</code></pre>
        </div>
        <!-- Output section -->
        <div class="rounded-lg bg-elevated/50 border border-default overflow-hidden">
          <div class="px-3 py-1.5 text-xs font-medium text-muted border-b border-default flex items-center gap-1.5">
            <UIcon name="i-lucide-arrow-left" class="size-3" />
            Output
          </div>
          <pre class="p-3 text-sm text-highlighted overflow-x-auto whitespace-pre-wrap break-all"><code>{{ displayOutput }}</code></pre>
        </div>
      </div>
    </template>
  </UChatTool>
</template>
