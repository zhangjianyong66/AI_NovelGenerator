<template>
  <section class="page">
    <PageHeader title="工作台" subtitle="围绕当前章节和核心项目文件组织编辑、上下文与生成动作。">
      <template #actions>
        <ActionBar align="end">
          <button class="ghost-button" type="button" @click="reloadWorkspace">刷新</button>
          <button
            class="primary-button"
            :disabled="isSaving || !activeProjectFile || !canWriteToBackend"
            type="button"
            @click="saveActiveProjectFile"
          >
            保存当前文件
          </button>
        </ActionBar>
      </template>
    </PageHeader>

    <StatusMessage v-if="!canWriteToBackend" type="warning" :message="writeUnavailableMessage" />

    <div class="grid three workspace-metrics">
      <MetricTile label="当前章节" :value="activeChapter ? `第 ${activeChapter.order} 章` : '-'" />
      <MetricTile label="运行任务" :value="runningJob?.title ?? '无'" />
      <MetricTile label="当前文件字数" :value="activeProjectFileWordCount" />
    </div>

    <WorkbenchLayout>
      <template #left>
        <section class="panel">
          <div class="panel-body">
            <h3 class="panel-title">项目文件</h3>
            <div class="file-list">
              <button
                v-for="file in projectFiles"
                :key="file.id"
                class="file-tab"
                :class="{ active: file.id === activeProjectFile?.id }"
                type="button"
                @click="selectProjectFile(file.id)"
              >
                <span>{{ file.label }}</span>
                <small>{{ file.wordCount }} 字</small>
              </button>
            </div>
          </div>
        </section>

        <section class="panel">
          <div class="panel-body">
            <h3 class="panel-title">章节导航</h3>
            <div class="chapter-list">
              <button
                v-for="chapter in chapters"
                :key="chapter.id"
                class="chapter-link"
                :class="{ active: chapter.id === activeChapter?.id }"
                type="button"
                @click="editorStore.selectChapter(chapter.id)"
              >
                <span>第 {{ chapter.order }} 章</span>
                <strong>{{ chapter.title }}</strong>
              </button>
            </div>
          </div>
        </section>
      </template>

      <section class="panel editor-shell">
        <div class="panel-body">
          <WritingEditor
            :model-value="activeProjectFileDraft"
            :title="activeProjectFile?.label ?? '核心文件'"
            :subtitle="activeProjectFile?.filename ?? '等待加载'"
            :dirty="hasDirtyProjectFile"
            :readonly="!canWriteToBackend"
            :save-state="saveState"
            empty-message="当前核心文件暂无内容。"
            min-height="560px"
            @save="saveActiveProjectFile"
            @update:model-value="editorStore.updateActiveProjectFileDraft"
          >
            <template #actions>
              <button
                class="primary-button"
                :disabled="isSaving || !activeProjectFile || !canWriteToBackend"
                type="button"
                @click="saveActiveProjectFile"
              >
                {{ isSaving ? '保存中' : '保存' }}
              </button>
            </template>
          </WritingEditor>
          <StatusMessage type="error" :message="errorMessage || editorError" />
        </div>
      </section>

      <template #right>
        <section class="panel">
          <div class="panel-body">
            <h3 class="panel-title">上下文资料</h3>
            <dl v-if="activeChapter" class="context-meta">
              <dt>章节</dt>
              <dd>第 {{ activeChapter.order }} 章</dd>
              <dt>标题</dt>
              <dd>{{ activeChapter.title }}</dd>
              <dt>状态</dt>
              <dd>{{ activeChapter.status }}</dd>
              <dt>视角</dt>
              <dd>{{ activeChapter.viewpoint }}</dd>
            </dl>
            <p class="muted">{{ activeChapter?.synopsis || '暂无章节简述。' }}</p>
          </div>
        </section>

        <section class="panel">
          <div class="panel-body">
            <h3 class="panel-title">任务状态</h3>
            <template v-if="runningJob">
              <span class="status-pill warning">{{ runningJob.status }}</span>
              <p class="muted">{{ runningJob.title }} · {{ runningJob.progress }}%</p>
            </template>
            <p v-else class="muted">当前没有运行中的生成任务。</p>
          </div>
        </section>

        <section class="panel">
          <div class="panel-body">
            <h3 class="panel-title">日志摘要</h3>
            <ul v-if="latestLogLines.length" class="context-list">
              <li v-for="line in latestLogLines" :key="line">{{ line }}</li>
            </ul>
            <p v-else class="muted">暂无生成日志。</p>
          </div>
        </section>
      </template>
    </WorkbenchLayout>
  </section>
</template>

<script setup lang="ts">
import { storeToRefs } from 'pinia'
import { computed, onMounted, ref } from 'vue'

import MetricTile from '@/components/MetricTile.vue'
import ActionBar from '@/components/ui/ActionBar.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import StatusMessage from '@/components/ui/StatusMessage.vue'
import { WorkbenchLayout, WritingEditor } from '@/features/writing'
import { serviceBridge, type ServiceBridgeStatus } from '@/services/serviceBridge'
import type { ProjectFileId } from '@/services/types'
import { useEditorStore } from '@/stores/editor'
import { useGenerationStore } from '@/stores/generation'
import { useProjectsStore } from '@/stores/projects'

const saveMessage = ref('')
const errorMessage = ref('')
const bridgeStatus = ref<ServiceBridgeStatus>({ ...serviceBridge.getStatus() })
const saveState = computed(() => {
  if (isSaving.value) return { state: 'saving' as const, text: '保存中' }
  if (saveMessage.value) return { state: 'saved' as const, text: saveMessage.value }
  return null
})
const canWriteToBackend = computed(() => serviceBridge.canWrite(bridgeStatus.value))
const writeUnavailableMessage = computed(() => serviceBridge.getWriteUnavailableMessage(bridgeStatus.value))

const projectsStore = useProjectsStore()
const editorStore = useEditorStore()
const generationStore = useGenerationStore()
const { activeProjectId } = storeToRefs(projectsStore)
const {
  chapters,
  activeChapter,
  projectFiles,
  activeProjectFile,
  activeProjectFileDraft,
  activeProjectFileWordCount,
  hasDirtyProjectFile,
  isSaving,
  error: editorError,
} = storeToRefs(editorStore)
const { runningJob, latestLogLines } = storeToRefs(generationStore)

const syncBridgeStatus = () => {
  bridgeStatus.value = { ...serviceBridge.getStatus() }
}

const loadWorkspace = async () => {
  await projectsStore.loadProjects()
  syncBridgeStatus()
  await Promise.all([
    editorStore.loadChapters(activeProjectId.value),
    editorStore.loadProjectFiles(),
    generationStore.loadJobs(activeProjectId.value),
  ])
  syncBridgeStatus()
}

onMounted(loadWorkspace)

const reloadWorkspace = async () => {
  if (!confirmDirtyProjectFileNavigation()) return
  saveMessage.value = ''
  errorMessage.value = ''
  await loadWorkspace()
}

const confirmDirtyProjectFileNavigation = () => {
  if (!hasDirtyProjectFile.value) return true
  const shouldDiscard = window.confirm('当前核心项目文件有未保存变更，继续切换将丢弃这些变更。')
  if (shouldDiscard) {
    editorStore.discardProjectFileDrafts()
  }
  return shouldDiscard
}

const selectProjectFile = (fileId: ProjectFileId) => {
  if (!confirmDirtyProjectFileNavigation()) return
  editorStore.selectProjectFile(fileId)
  saveMessage.value = ''
  errorMessage.value = ''
}

const saveActiveProjectFile = async () => {
  saveMessage.value = ''
  errorMessage.value = ''

  if (!canWriteToBackend.value) {
    errorMessage.value = writeUnavailableMessage.value
    return
  }

  try {
    await editorStore.saveActiveProjectFile()
    syncBridgeStatus()
    saveMessage.value = '已保存'
  } catch (error) {
    syncBridgeStatus()
    errorMessage.value =
      error instanceof Error
        ? error.message
        : typeof error === 'object' && error !== null && 'message' in error
          ? String(error.message)
          : '保存失败'
  }
}
</script>

<style scoped>
.editor-shell {
  min-height: 640px;
}

.editor-shell .panel-body {
  padding: var(--space-6);
}

.workspace-metrics {
  gap: var(--space-5);
}

.file-list,
.chapter-list {
  display: grid;
  gap: var(--space-3);
}

.file-tab,
.chapter-link {
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-width: 0;
  min-height: 44px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  padding: 0 var(--space-4);
  background: var(--color-surface);
  color: var(--color-text);
  text-align: left;
}

.file-tab span,
.file-tab small,
.chapter-link span,
.chapter-link strong,
.context-meta dd {
  min-width: 0;
  overflow-wrap: anywhere;
}

.chapter-link {
  align-items: flex-start;
  flex-direction: column;
  justify-content: center;
  gap: var(--space-1);
  min-height: 54px;
}

.file-tab.active,
.chapter-link.active {
  border-color: var(--color-primary);
  background: var(--color-primary-soft);
}

.file-tab small,
.chapter-link span {
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
}

.chapter-link strong {
  line-height: 1.35;
}

.context-meta {
  display: grid;
  grid-template-columns: 56px minmax(0, 1fr);
  gap: var(--space-3);
  margin: 0 0 var(--space-5);
}

.context-meta dt {
  color: var(--color-text-muted);
}

.context-meta dd {
  margin: 0;
}

.context-list {
  margin: 0;
  padding-left: 20px;
}

.context-list li {
  margin: var(--space-3) 0;
  line-height: 1.5;
}

@media (max-width: 1120px) {
  .editor-shell {
    min-height: 560px;
  }

  .workspace-metrics {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 960px) {
  .editor-shell {
    min-height: auto;
  }

  .workspace-metrics {
    grid-template-columns: 1fr;
  }
}
</style>
