<template>
  <div class="app-shell">
    <header class="topbar">
      <div>
        <p class="eyebrow">AI Novel Generator</p>
        <h1>{{ currentTitle }}</h1>
      </div>
      <div class="topbar-status">
        <span class="status-dot" />
        <span>Mock UI</span>
        <span class="divider" />
        <span>{{ activeProject?.title ?? '未选择项目' }}</span>
      </div>
    </header>

    <aside class="sidebar">
      <nav aria-label="主导航">
        <RouterLink v-for="item in navItems" :key="item.to" :to="item.to" class="nav-item">
          <component :is="item.icon" :size="18" />
          <span>{{ item.label }}</span>
        </RouterLink>
      </nav>
    </aside>

    <main class="content">
      <RouterView />
    </main>

    <aside class="context-panel">
      <section class="context-section">
        <h2>当前项目</h2>
        <template v-if="activeProject">
          <strong>{{ activeProject.title }}</strong>
          <p>{{ activeProject.summary }}</p>
          <div class="progress-row">
            <span>章节进度</span>
            <span>{{ activeProject.chaptersCompleted }}/{{ activeProject.chaptersTotal }}</span>
          </div>
          <div class="progress-track">
            <span :style="{ width: projectProgress }" />
          </div>
        </template>
        <p v-else class="muted">正在加载 mock 项目数据</p>
      </section>

      <section class="context-section">
        <h2>生成状态</h2>
        <template v-if="runningJob">
          <div class="job-line">
            <span>{{ runningJob.title }}</span>
            <strong>{{ runningJob.progress }}%</strong>
          </div>
          <div class="progress-track">
            <span :style="{ width: `${runningJob.progress}%` }" />
          </div>
        </template>
        <p v-else class="muted">暂无运行中的 mock 任务</p>
      </section>

      <section class="context-section">
        <h2>章节焦点</h2>
        <template v-if="activeChapter">
          <strong>第 {{ activeChapter.order }} 章 · {{ activeChapter.title }}</strong>
          <p>{{ activeChapter.synopsis }}</p>
        </template>
        <p v-else class="muted">暂无章节选择</p>
      </section>
    </aside>
  </div>
</template>

<script setup lang="ts">
import {
  BookOpen,
  Brain,
  FolderKanban,
  Library,
  PenLine,
  Settings,
  Sparkles,
} from '@lucide/vue'
import { storeToRefs } from 'pinia'
import { computed, onMounted, watch } from 'vue'
import { RouterLink, RouterView, useRoute } from 'vue-router'

import { useEditorStore } from '@/stores/editor'
import { useGenerationStore } from '@/stores/generation'
import { useProjectsStore } from '@/stores/projects'

const route = useRoute()
const projectsStore = useProjectsStore()
const editorStore = useEditorStore()
const generationStore = useGenerationStore()

const { activeProject } = storeToRefs(projectsStore)
const { activeChapter } = storeToRefs(editorStore)
const { runningJob } = storeToRefs(generationStore)

const navItems = [
  { to: '/projects', label: '项目', icon: FolderKanban },
  { to: '/workspace', label: '工作台', icon: Brain },
  { to: '/chapters', label: '章节编辑', icon: PenLine },
  { to: '/generation', label: '生成任务', icon: Sparkles },
  { to: '/settings', label: '设置', icon: Settings },
  { to: '/knowledge', label: '知识库', icon: Library },
]

const currentTitle = computed(() => String(route.meta.label ?? '项目'))
const projectProgress = computed(() => {
  if (!activeProject.value || activeProject.value.chaptersTotal === 0) return '0%'
  return `${Math.round((activeProject.value.chaptersCompleted / activeProject.value.chaptersTotal) * 100)}%`
})

onMounted(async () => {
  await projectsStore.loadProjects()
})

watch(
  () => projectsStore.activeProjectId,
  async (projectId) => {
    if (!projectId) return
    await Promise.all([editorStore.loadChapters(projectId), generationStore.loadJobs(projectId)])
  },
  { immediate: true },
)
</script>

<style scoped>
.app-shell {
  display: grid;
  min-height: 100vh;
  grid-template-columns: 220px minmax(0, 1fr) 300px;
  grid-template-rows: 72px minmax(0, 1fr);
  grid-template-areas:
    "topbar topbar topbar"
    "sidebar content context";
}

.topbar {
  grid-area: topbar;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--color-border);
  background: var(--color-surface);
  padding: 0 24px;
}

.topbar h1 {
  margin: 2px 0 0;
  font-size: 22px;
  line-height: 1.25;
}

.eyebrow {
  margin: 0;
  color: var(--color-primary);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0;
}

.topbar-status {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  color: var(--color-text-muted);
  font-size: 13px;
}

.status-dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  background: var(--color-success);
}

.divider {
  width: 1px;
  height: 18px;
  background: var(--color-border);
}

.sidebar {
  grid-area: sidebar;
  border-right: 1px solid var(--color-border);
  background: #fbfcfd;
  padding: 16px 12px;
}

.sidebar nav {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  min-height: 42px;
  border-radius: 8px;
  padding: 0 12px;
  color: var(--color-text-muted);
  font-weight: 600;
}

.nav-item.router-link-active {
  background: #e3f1f2;
  color: var(--color-primary-strong);
}

.content {
  grid-area: content;
  min-width: 0;
  overflow: auto;
  padding: 22px;
}

.context-panel {
  grid-area: context;
  display: flex;
  flex-direction: column;
  gap: 14px;
  border-left: 1px solid var(--color-border);
  background: #fbfcfd;
  padding: 18px;
}

.context-section {
  border: 1px solid var(--color-border);
  border-radius: 8px;
  background: var(--color-surface);
  padding: 14px;
}

.context-section h2 {
  margin: 0 0 10px;
  font-size: 14px;
}

.context-section p {
  margin: 8px 0 0;
  color: var(--color-text-muted);
  font-size: 13px;
  line-height: 1.55;
}

.progress-row,
.job-line {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-top: 12px;
  font-size: 13px;
}

.progress-track {
  height: 7px;
  border-radius: 999px;
  background: var(--color-surface-muted);
  margin-top: 8px;
  overflow: hidden;
}

.progress-track span {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: var(--color-primary);
}
</style>
