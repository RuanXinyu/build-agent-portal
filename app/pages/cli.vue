<script setup lang="ts">
definePageMeta({
  layout: 'landing'
})
</script>

<template>
  <UPageHero
    title="BuildMate CLI"
    description="强大的命令行工具，将 AI 智能构建能力带入你的终端"
    :links="[
      { label: '查看文档', color: 'neutral', variant: 'subtle', trailingIcon: 'i-lucide-arrow-right' }
    ]"
  >
    <div class="bg-elevated rounded-lg p-4 font-mono text-sm text-muted border border-default">
      <div class="text-toned">$ npm install -g buildmate-cli</div>
      <div class="text-toned mt-1">$ buildmate init</div>
      <div class="mt-1 text-primary">✓ BuildMate CLI initialized successfully</div>
      <div class="text-toned mt-1">$ buildmate analyze</div>
      <div class="mt-1 text-primary">✓ Found 3 issues, 2 auto-fixable</div>
    </div>
  </UPageHero>

  <UPageSection
    id="features"
    headline="CLI 特性"
    title="终端中的智能构建助手"
    description="BuildMate CLI 让你在命令行中享受完整的 AI 构建管理能力。"
    :features="[
      { title: '快速分析', description: '一键分析项目构建状态，快速定位问题根源。', icon: 'i-lucide-gauge' },
      { title: '自动修复', description: '智能检测并自动修复常见构建错误，减少手动干预。', icon: 'i-lucide-wrench' },
      { title: 'CI/CD 集成', description: '无缝集成到现有 CI/CD 流水线，构建守护自动化。', icon: 'i-lucide-git-merge' },
      { title: '实时通知', description: '构建状态变更即时推送，第一时间掌握构建动态。', icon: 'i-lucide-bell' },
      { title: '多语言支持', description: '支持 Java、Python、Go、Node.js 等主流构建生态。', icon: 'i-lucide-languages' },
      { title: '脚本化工作流', description: '通过脚本编排复杂构建流程，实现自动化运维。', icon: 'i-lucide-file-code' }
    ]"
  />

  <UPageCTA
    title="立即开始使用 BuildMate CLI"
    description="将 AI 构建能力集成到你的工作流中，提升团队开发效率。"
    :links="[
      { label: '开始对话', to: '/chat', icon: 'i-lucide-square-play' },
      { label: '返回首页', to: '/home', color: 'neutral', variant: 'subtle', trailingIcon: 'i-lucide-arrow-right' }
    ]"
    class="rounded-none"
  />
</template>
