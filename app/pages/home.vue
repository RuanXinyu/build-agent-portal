<script setup lang="ts">
definePageMeta({
  layout: 'landing'
})
</script>

<template>
  <UPageHero
    title="BuildMate"
    description="AI 驱动的智能构建助手，让构建管理更高效、更智能"
    :links="[
      { label: '开始使用', to: '/chat', icon: 'i-lucide-square-play' },
      { label: '了解更多', color: 'neutral', variant: 'subtle', trailingIcon: 'i-lucide-arrow-right' }
    ]"
  />

  <UPageSection
    id="features"
    headline="功能特性"
    title="强大功能，开箱即用"
    description="BuildMate 提供全方位的智能构建管理能力，帮助你专注于代码本身。"
    :features="[
      { title: '智能构建分析', description: '自动检测并诊断构建错误，提供精准的修复建议。', icon: 'i-lucide-zap' },
      { title: '代码审查', description: '深度分析代码质量，发现潜在问题并提供优化方案。', icon: 'i-lucide-search-code' },
      { title: '状态监控', description: '实时追踪构建状态，第一时间获取构建结果通知。', icon: 'i-lucide-activity' },
      { title: '多项目管理', description: '统一管理多个项目的构建流程，提升团队协作效率。', icon: 'i-lucide-folder-kanban' },
      { title: 'CLI 工具', description: '强大的命令行工具，支持 CI/CD 集成和自动化工作流。', icon: 'i-lucide-terminal' },
      { title: 'AI 对话', description: '通过自然语言与 AI 交互，快速解决构建问题。', icon: 'i-lucide-message-square' }
    ]"
  />

  <UPageCTA
    title="开始使用 BuildMate"
    description="立即体验 AI 驱动的智能构建管理，让你的开发工作流更上一层楼。"
    :links="[
      { label: '开始对话', to: '/chat', icon: 'i-lucide-square-play' },
      { label: 'CLI 工具', to: '/cli', color: 'neutral', variant: 'subtle', trailingIcon: 'i-lucide-arrow-right' }
    ]"
    class="rounded-none"
  />
</template>
