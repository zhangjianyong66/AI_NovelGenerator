<template>
  <section class="page">
    <PageHeader title="章节编辑" subtitle="从当前输出目录加载章节文件，编辑后保存回 chapter_X.txt。">
      <template #actions>
      <ActionBar align="end">
        <button class="ghost-button" type="button" @click="reloadChapters">刷新</button>
        <button class="ghost-button" type="button" @click="selectAdjacentChapter('previous')">上一章</button>
        <button class="ghost-button" type="button" @click="selectAdjacentChapter('next')">下一章</button>
        <button
          v-if="isActiveChapterPlanned"
          class="ghost-button"
          :disabled="isSaving || !activeChapter || !canWriteToBackend"
          type="button"
          @click="createActiveChapter"
        >
          <FilePlus :size="16" />
          {{ isSaving ? '创建中' : '创建章节文件' }}
        </button>
        <button
          class="primary-button"
          :disabled="isSaving || !activeChapter || isActiveChapterPlanned || !canWriteToBackend"
          type="button"
          @click="saveActiveChapter"
        >
          <Save :size="16" />
          {{ isSaving ? '保存中' : '保存草稿' }}
        </button>
      </ActionBar>
      </template>
    </PageHeader>

    <StatusMessage v-if="!canWriteToBackend" type="warning" :message="writeUnavailableMessage" />

    <div class="editor-grid">
      <aside class="panel chapter-list">
        <div class="panel-body">
          <h3 class="panel-title">章节列表</h3>
          <StatusMessage v-if="chapters.length === 0" type="empty" message="当前输出目录尚未发现章节，请先生成或编辑 Novel_directory.txt。" />
          <ChapterNavigator
            :chapters="chapters"
            :active-chapter-id="activeChapter?.id"
            @select="selectChapter"
          />
        </div>
      </aside>

      <section class="panel editor-panel">
        <div class="panel-body">
          <WritingEditor
            :model-value="activeChapterDraft"
            :title="activeChapter?.title ?? '暂无章节'"
            :dirty="hasDirtyChapter"
            :readonly="!canWriteToBackend || !activeChapter || isActiveChapterPlanned"
            :save-state="saveState"
            :empty-message="editorEmptyMessage"
            min-height="470px"
            aria-label="章节正文"
            @save="saveActiveChapter"
            @update:model-value="editorStore.updateActiveChapterDraft"
          />
          <StatusMessage v-if="isActiveChapterPlanned" type="info" message="该章节还没有 chapter_X.txt。创建章节文件后即可输入正文并保存。" />
          <StatusMessage type="error" :message="errorMessage" />
        </div>
      </section>

      <aside class="panel meta-panel">
        <div class="panel-body">
          <h3 class="panel-title">章节元信息</h3>
          <dl v-if="activeChapter">
            <dt>状态</dt>
            <dd>{{ chapterStatusLabel }}</dd>
            <dt>视角</dt>
            <dd>{{ activeChapter.viewpoint }}</dd>
            <dt>字数</dt>
            <dd>{{ activeChapterWordCount }}</dd>
            <dt>更新时间</dt>
            <dd>{{ activeChapter.updatedAt }}</dd>
          </dl>
          <p class="muted">{{ activeChapter?.synopsis }}</p>
        </div>
      </aside>
    </div>
  </section>
</template>

<script setup lang="ts">
import { FilePlus, Save } from '@lucide/vue'
import { storeToRefs } from 'pinia'
import { computed, onMounted, ref } from 'vue'
import { onBeforeRouteLeave } from 'vue-router'

import ActionBar from '@/components/ui/ActionBar.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import StatusMessage from '@/components/ui/StatusMessage.vue'
import { ChapterNavigator, WritingEditor } from '@/features/writing'
import { serviceBridge, type ServiceBridgeStatus } from '@/services/serviceBridge'
import { useEditorStore } from '@/stores/editor'
import { useProjectsStore } from '@/stores/projects'

const projectsStore = useProjectsStore()
const editorStore = useEditorStore()
const {
  chapters,
  activeChapter,
  activeChapterDraft,
  activeChapterWordCount,
  hasDirtyChapter,
  isSaving,
} = storeToRefs(editorStore)
const saveMessage = ref('')
const errorMessage = ref('')
const bridgeStatus = ref<ServiceBridgeStatus>({ ...serviceBridge.getStatus() })
const saveState = computed(() => (saveMessage.value ? { state: 'saved' as const, text: saveMessage.value } : null))
const canWriteToBackend = computed(() => serviceBridge.canWrite(bridgeStatus.value))
const writeUnavailableMessage = computed(() => serviceBridge.getWriteUnavailableMessage(bridgeStatus.value))
const isActiveChapterPlanned = computed(() => activeChapter.value?.status === 'planned')
const editorEmptyMessage = computed(() =>
  isActiveChapterPlanned.value ? '该章节文件尚未创建。' : '当前输出目录尚未加载到章节正文。',
)
const chapterStatusLabel = computed(() => {
  if (!activeChapter.value) return ''
  const labels = {
    planned: '计划中',
    drafting: '草稿中',
    draft: '草稿',
    review: '审校',
    final: '定稿',
  } as Record<string, string>
  return labels[activeChapter.value.status] ?? activeChapter.value.status
})

const syncBridgeStatus = () => {
  bridgeStatus.value = { ...serviceBridge.getStatus() }
}

onMounted(async () => {
  await projectsStore.loadProjects()
  syncBridgeStatus()
  await editorStore.loadChapters(projectsStore.activeProjectId)
  syncBridgeStatus()
})

const confirmDirtyNavigation = () => {
  if (!hasDirtyChapter.value) return true
  const shouldDiscard = window.confirm('当前章节有未保存变更，继续切换将丢弃这些变更。')
  if (shouldDiscard) {
    editorStore.discardChapterDrafts()
  }
  return shouldDiscard
}

const selectChapter = (chapterId: string) => {
  if (!confirmDirtyNavigation()) return
  editorStore.selectChapter(chapterId)
}

const selectAdjacentChapter = (direction: 'previous' | 'next') => {
  if (!confirmDirtyNavigation()) return
  if (direction === 'previous') {
    editorStore.selectPreviousChapter()
  } else {
    editorStore.selectNextChapter()
  }
}

const saveActiveChapter = async () => {
  saveMessage.value = ''
  errorMessage.value = ''
  if (!canWriteToBackend.value) {
    errorMessage.value = writeUnavailableMessage.value
    return
  }

  if (isActiveChapterPlanned.value) {
    errorMessage.value = '请先创建章节文件。'
    return
  }

  try {
    await editorStore.saveActiveChapter()
    syncBridgeStatus()
    saveMessage.value = '已保存'
  } catch (error) {
    syncBridgeStatus()
    errorMessage.value =
      typeof error === 'object' && error !== null && 'status' in error && error.status === 404
        ? '章节文件不存在，请先在输出目录准备对应的 chapter_X.txt。'
        : error instanceof Error
        ? error.message
        : typeof error === 'object' && error !== null && 'message' in error
          ? String(error.message)
          : '保存失败'
  }
}

const createActiveChapter = async () => {
  saveMessage.value = ''
  errorMessage.value = ''
  if (!canWriteToBackend.value) {
    errorMessage.value = writeUnavailableMessage.value
    return
  }

  try {
    await editorStore.createActiveChapter()
    syncBridgeStatus()
    saveMessage.value = '章节文件已创建'
  } catch (error) {
    syncBridgeStatus()
    errorMessage.value =
      error instanceof Error
        ? error.message
        : typeof error === 'object' && error !== null && 'message' in error
          ? String(error.message)
          : '创建章节失败'
  }
}

const reloadChapters = async () => {
  if (!confirmDirtyNavigation()) return
  await editorStore.loadChapters(projectsStore.activeProjectId)
  syncBridgeStatus()
}

onBeforeRouteLeave(() => confirmDirtyNavigation())
</script>

<style scoped>
.editor-grid {
  display: grid;
  grid-template-columns: 250px minmax(0, 1fr) 260px;
  gap: 16px;
  min-height: 580px;
}

.chapter-navigator {
  display: grid;
  gap: 8px;
}

:deep(.chapter-navigator__item) {
  display: block;
  width: 100%;
  border-radius: 8px;
  background: transparent;
  color: var(--color-text);
  padding: 10px;
  text-align: left;
}

:deep(.chapter-navigator__item.active) {
  background: #e3f1f2;
}

:deep(.chapter-navigator__item span) {
  display: block;
  color: var(--color-text-muted);
  font-size: 12px;
}

:deep(.chapter-navigator__item strong) {
  display: block;
  margin-top: 4px;
}

dl {
  display: grid;
  grid-template-columns: 72px minmax(0, 1fr);
  gap: 10px;
  margin: 0 0 16px;
}

dt {
  color: var(--color-text-muted);
}

dd {
  margin: 0;
}
</style>
