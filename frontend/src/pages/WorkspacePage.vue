<template>
  <section class="page">
    <PageHeader title="工作台" subtitle="汇总当前项目、章节焦点、核心文件状态和下一步生成动作。">
      <template #actions>
      <ActionBar align="end">
        <button v-for="action in actions" :key="action" class="ghost-button" type="button">{{ action }}</button>
      </ActionBar>
      </template>
    </PageHeader>

    <div class="grid three">
      <MetricTile label="当前章节" :value="activeChapter ? `第 ${activeChapter.order} 章` : '-'" />
      <MetricTile label="运行任务" :value="runningJob?.title ?? '无'" />
      <MetricTile label="当前文件字数" :value="activeProjectFileWordCount" />
    </div>

    <div class="workbench-grid">
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
              @click="editorStore.selectProjectFile(file.id)"
            >
              <span>{{ file.label }}</span>
              <small>{{ file.wordCount }} 字</small>
            </button>
          </div>
        </div>
      </section>

      <section class="panel">
        <div class="panel-body">
          <h3 class="panel-title">目录蓝图预览</h3>
          <ol class="chapter-outline">
            <li v-for="chapter in chapters" :key="chapter.id">
              <span>第 {{ chapter.order }} 章</span>
              <strong>{{ chapter.title }}</strong>
            </li>
          </ol>
        </div>
      </section>

      <section class="panel main-draft">
        <div class="panel-body">
          <LongTextEditor
            :model-value="activeProjectFileDraft"
            :title="activeProjectFile?.label ?? '核心文件'"
            :filename="activeProjectFile?.filename ?? '等待加载'"
            :dirty="hasDirtyProjectFile"
            :save-state="saveMessage"
            empty-message="当前核心文件暂无内容。"
            @update:model-value="editorStore.updateActiveProjectFileDraft"
          >
            <template #actions>
              <button class="primary-button" :disabled="isSaving || !activeProjectFile" type="button" @click="saveActiveProjectFile">
              保存
            </button>
            </template>
          </LongTextEditor>
          <StatusMessage type="error" :message="errorMessage" />
        </div>
      </section>

      <section class="panel">
        <div class="panel-body">
          <h3 class="panel-title">上下文提示</h3>
          <ul class="context-list">
            <li v-for="line in latestLogLines" :key="line">{{ line }}</li>
          </ul>
        </div>
      </section>
    </div>
  </section>
</template>

<script setup lang="ts">
import { storeToRefs } from 'pinia'
import { onMounted, ref } from 'vue'

import MetricTile from '@/components/MetricTile.vue'
import ActionBar from '@/components/ui/ActionBar.vue'
import LongTextEditor from '@/components/ui/LongTextEditor.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import StatusMessage from '@/components/ui/StatusMessage.vue'
import { useEditorStore } from '@/stores/editor'
import { useGenerationStore } from '@/stores/generation'
import { useProjectsStore } from '@/stores/projects'

const actions = ['生成设定', '扩展目录', '生成草稿', '润色定稿', '批量生成']
const saveMessage = ref('')
const errorMessage = ref('')

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
} = storeToRefs(editorStore)
const { runningJob, latestLogLines } = storeToRefs(generationStore)

onMounted(async () => {
  await projectsStore.loadProjects()
  await Promise.all([
    editorStore.loadChapters(activeProjectId.value),
    editorStore.loadProjectFiles(),
    generationStore.loadJobs(activeProjectId.value),
  ])
})

const saveActiveProjectFile = async () => {
  saveMessage.value = ''
  errorMessage.value = ''

  try {
    await editorStore.saveActiveProjectFile()
    saveMessage.value = '已保存'
  } catch (error) {
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
.workbench-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(280px, 0.7fr);
  gap: 16px;
}

.main-draft {
  grid-column: span 1;
}

.chapter-outline,
.context-list {
  margin: 0;
  padding-left: 20px;
}

.chapter-outline li,
.context-list li {
  margin: 10px 0;
  line-height: 1.5;
}

.chapter-outline span {
  display: inline-block;
  min-width: 64px;
  color: var(--color-text-muted);
  font-size: 13px;
}

.file-list {
  display: grid;
  gap: 8px;
}

.file-tab {
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 44px;
  border: 1px solid var(--color-border);
  border-radius: 6px;
  padding: 0 10px;
  background: var(--color-surface);
  color: var(--color-text);
}

.file-tab.active {
  border-color: var(--color-primary);
  background: #edf7f8;
}

.file-tab small,
.editor-meta {
  color: var(--color-text-muted);
  font-size: 12px;
}

</style>
