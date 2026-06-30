<template>
  <div
    class="app-shell"
    :class="{
      'app-shell--nav-collapsed': isNavCollapsed,
      'app-shell--context-collapsed': isContextCollapsed,
    }"
  >
    <header class="topbar">
      <div>
        <p class="eyebrow">AI Novel Generator</p>
        <h1>{{ currentTitle }}</h1>
      </div>
      <div class="topbar-right">
        <div class="layout-controls" aria-label="布局控制">
          <button
            class="layout-toggle"
            type="button"
            :aria-pressed="isNavCollapsed"
            :aria-label="isNavCollapsed ? '展开主导航' : '折叠主导航'"
            :title="isNavCollapsed ? '展开主导航' : '折叠主导航'"
            @click="toggleNav"
          >
            <PanelLeftClose v-if="!isNavCollapsed" :size="18" />
            <PanelLeftOpen v-else :size="18" />
          </button>
          <button
            class="layout-toggle"
            type="button"
            :aria-pressed="isContextCollapsed"
            :aria-label="isContextCollapsed ? '展开项目状态栏' : '折叠项目状态栏'"
            :title="isContextCollapsed ? '展开项目状态栏' : '折叠项目状态栏'"
            @click="toggleContext"
          >
            <PanelRightClose v-if="!isContextCollapsed" :size="18" />
            <PanelRightOpen v-else :size="18" />
          </button>
        </div>
        <div class="topbar-status">
          <span class="status-dot" :class="bridgeStatus.mode" />
          <span>{{ bridgeModeLabel }}</span>
          <span class="divider" />
          <span>{{ activeProject?.title ?? '未选择项目' }}</span>
        </div>
      </div>
    </header>

    <aside class="sidebar">
      <nav aria-label="主导航">
        <RouterLink v-for="item in navItems" :key="item.to" :to="item.to" class="nav-item">
          <component :is="item.icon" :size="18" />
          <span class="nav-label">{{ item.label }}</span>
        </RouterLink>
      </nav>
    </aside>

    <main class="content">
      <RouterView />
    </main>

    <aside class="context-panel">
      <section class="context-section">
        <h2>当前项目</h2>
        <p v-if="!canWriteToBackend" class="mode-note">{{ writeUnavailableMessage }}</p>
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
        <p v-else class="muted">正在加载项目数据</p>
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
        <p v-else class="muted">暂无运行中的生成任务</p>
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
  PanelLeftClose,
  PanelLeftOpen,
  PanelRightClose,
  PanelRightOpen,
  PenLine,
  Settings,
  Sparkles,
} from '@lucide/vue'
import { storeToRefs } from 'pinia'
import { computed, onMounted, ref, watch } from 'vue'
import { RouterLink, RouterView, useRoute } from 'vue-router'

import { serviceBridge, type ServiceBridgeStatus } from '@/services/serviceBridge'
import { useEditorStore } from '@/stores/editor'
import { useGenerationStore } from '@/stores/generation'
import { useProjectsStore } from '@/stores/projects'

const route = useRoute()
const projectsStore = useProjectsStore()
const editorStore = useEditorStore()
const generationStore = useGenerationStore()
const bridgeStatus = ref<ServiceBridgeStatus>({ ...serviceBridge.getStatus() })
const layoutStorageKeys = {
  navCollapsed: 'ai-novel-generator.layout.navCollapsed',
  contextCollapsed: 'ai-novel-generator.layout.contextCollapsed',
} as const

const readLayoutPreference = (key: string) => {
  try {
    return window.localStorage.getItem(key) === 'true'
  } catch {
    return false
  }
}

const writeLayoutPreference = (key: string, value: boolean) => {
  try {
    window.localStorage.setItem(key, String(value))
  } catch {
    // Layout persistence is a convenience; ignore storage failures.
  }
}

const isNavCollapsed = ref(readLayoutPreference(layoutStorageKeys.navCollapsed))
const isContextCollapsed = ref(readLayoutPreference(layoutStorageKeys.contextCollapsed))

const { activeProject } = storeToRefs(projectsStore)
const { activeChapter } = storeToRefs(editorStore)
const { runningJob } = storeToRefs(generationStore)

const navItems = [
  { to: '/projects', label: '项目', icon: FolderKanban },
  { to: '/workspace', label: '工作台', icon: Brain },
  { to: '/chapters', label: '章节编辑', icon: PenLine },
  { to: '/generation', label: '生成任务', icon: Sparkles },
  { to: '/knowledge', label: '知识库', icon: Library },
  { to: '/settings', label: '设置', icon: Settings },
]

const currentTitle = computed(() => String(route.meta.label ?? '项目'))
const bridgeModeLabel = computed(() => {
  return serviceBridge.getModeLabel(bridgeStatus.value.mode)
})
const canWriteToBackend = computed(() => serviceBridge.canWrite(bridgeStatus.value))
const writeUnavailableMessage = computed(() => serviceBridge.getWriteUnavailableMessage(bridgeStatus.value))
const projectProgress = computed(() => {
  if (!activeProject.value || activeProject.value.chaptersTotal === 0) return '0%'
  return `${Math.round((activeProject.value.chaptersCompleted / activeProject.value.chaptersTotal) * 100)}%`
})

const syncBridgeStatus = () => {
  bridgeStatus.value = { ...serviceBridge.getStatus() }
}

const toggleNav = () => {
  isNavCollapsed.value = !isNavCollapsed.value
  writeLayoutPreference(layoutStorageKeys.navCollapsed, isNavCollapsed.value)
}

const toggleContext = () => {
  isContextCollapsed.value = !isContextCollapsed.value
  writeLayoutPreference(layoutStorageKeys.contextCollapsed, isContextCollapsed.value)
}

onMounted(async () => {
  await serviceBridge.checkHealth()
  syncBridgeStatus()
  await projectsStore.loadProjects()
  syncBridgeStatus()
})

watch(
  () => projectsStore.activeProjectId,
  async (projectId) => {
    if (!projectId) return
    editorStore.resetProjectState(projectId)
    generationStore.resetProjectState()
    await Promise.all([editorStore.loadChapters(projectId), generationStore.loadJobs(projectId)])
    syncBridgeStatus()
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

.app-shell--nav-collapsed {
  grid-template-columns: 64px minmax(0, 1fr) 300px;
}

.app-shell--context-collapsed {
  grid-template-columns: 220px minmax(0, 1fr) 0;
}

.app-shell--nav-collapsed.app-shell--context-collapsed {
  grid-template-columns: 64px minmax(0, 1fr) 0;
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

.topbar-right {
  display: inline-flex;
  align-items: center;
  min-width: 0;
  gap: 14px;
}

.layout-controls {
  display: inline-flex;
  gap: 6px;
}

.layout-toggle {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-surface);
  color: var(--color-text-muted);
}

.layout-toggle:hover,
.layout-toggle[aria-pressed="true"] {
  border-color: var(--color-primary);
  background: var(--color-primary-soft);
  color: var(--color-primary-strong);
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
  min-width: 0;
  gap: 10px;
  color: var(--color-text-muted);
  font-size: 13px;
  white-space: nowrap;
}

.status-dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  background: var(--color-warning);
}

.status-dot.backend {
  background: var(--color-success);
}

.status-dot.disconnected {
  background: var(--color-danger);
}

.status-dot.mock {
  background: var(--color-warning);
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
  overflow: hidden;
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

.app-shell--nav-collapsed .sidebar {
  padding: 16px 10px;
}

.app-shell--nav-collapsed .nav-item {
  justify-content: center;
  padding: 0;
}

.app-shell--nav-collapsed .nav-label {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip: rect(0 0 0 0);
  white-space: nowrap;
}

.nav-item.router-link-active {
  background: #e3f1f2;
  color: var(--color-primary-strong);
}

.content {
  grid-area: content;
  min-width: 0;
  overflow-x: hidden;
  overflow-y: auto;
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
  overflow: hidden;
}

.app-shell--context-collapsed .context-panel {
  border-left: 0;
  padding: 0;
  visibility: hidden;
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

.context-section .mode-note {
  margin: 0 0 10px;
  color: var(--color-warning);
  font-weight: 600;
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

@media (max-width: 1180px) {
  .app-shell {
    grid-template-columns: 64px minmax(0, 1fr) 0;
  }

  .sidebar {
    padding: 16px 10px;
  }

  .nav-item {
    justify-content: center;
    padding: 0;
  }

  .nav-label,
  .context-panel {
    position: absolute;
    width: 1px;
    height: 1px;
    overflow: hidden;
    clip: rect(0 0 0 0);
    white-space: nowrap;
  }

  .context-panel {
    border-left: 0;
    padding: 0;
  }
}

@media (max-width: 720px) {
  .topbar {
    min-height: 86px;
    align-items: flex-start;
    flex-direction: column;
    justify-content: center;
    gap: 8px;
    padding: 10px 16px;
  }

  .topbar-status {
    flex-wrap: wrap;
    white-space: normal;
  }
}
</style>
