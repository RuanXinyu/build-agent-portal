<script setup lang="ts">
import { isReasoningUIPart, isTextUIPart, isToolUIPart, getToolName } from 'ai'
import type { UIMessage } from 'ai'
import { isPartStreaming, isToolStreaming } from '@nuxt/ui/utils/ai'
import emoji from '@comark/vue/plugins/emoji'
import binding, { Binding } from '@comark/vue/plugins/binding'
import breaks from '@comark/vue/plugins/breaks'
import mermaid, { Mermaid } from '@comark/vue/plugins/mermaid'
import taskList from '@comark/vue/plugins/task-list'
import toc from '@comark/vue/plugins/toc'
import highlight from '@comark/vue/plugins/highlight'
import githubLight from '@shikijs/themes/github-light'
import githubDark from '@shikijs/themes/github-dark'

defineProps<{
  message: UIMessage
}>()
</script>

<template>
  <template v-for="(part, index) in getMergedParts(message.parts)" :key="`${message.id}-${part.type}-${index}`">
    <UChatReasoning
      v-if="isReasoningUIPart(part)"
      :text="part.text"
      :streaming="isPartStreaming(part)"
      chevron="leading"
    >
      <ChatComark
        :markdown="part.text"
        :streaming="isPartStreaming(part)"
        :plugins="[emoji(), binding(), breaks(), mermaid(), taskList(), toc({ depth: 2}), highlight({ themes: { light: githubLight, dark: githubDark } })]"
        :components="{ Binding, mermaid: Mermaid }"
        />
      />
    </UChatReasoning>

    <template v-else-if="isToolUIPart(part)">
      <ChatToolChart
        v-if="getToolName(part) === 'chart'"
        :invocation="{ ...(part as ChartUIToolInvocation) }"
      />
      <UChatTool
        v-else-if="getToolName(part) === 'web_search' || getToolName(part) === 'google_search'"
        :text="isToolStreaming(part) ? 'Searching the web...' : 'Searched the web'"
        :suffix="getSearchQuery(part)"
        :streaming="isToolStreaming(part)"
        chevron="leading"
      >
        <ChatToolSources :sources="getSources(part)" />
      </UChatTool>
      <ChatToolInvocation
        v-else
        :part="(part as any)"
      />
    </template>

    <template v-else-if="isTextUIPart(part)">
      <ChatComark
        v-if="message.role === 'assistant'"
        :markdown="part.text"
        :streaming="isPartStreaming(part)"
        :plugins="[emoji(), binding(), breaks(), mermaid(), taskList(), toc({ depth: 2}), highlight({ themes: { light: githubLight, dark: githubDark } })]"
        :components="{ Binding, mermaid: Mermaid }"
      />
      <template v-else-if="message.role === 'user'">
        <p class="whitespace-pre-wrap">
          {{ part.text }}
        </p>
      </template>
    </template>
  </template>
</template>
