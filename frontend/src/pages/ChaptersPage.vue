<template>
  <section class="page">
    <PageHeader title="章节编辑" subtitle="从当前输出目录加载章节文件，编辑后保存回 chapter_X.txt。">
      <template #actions>
      <ActionBar align="end">
        <button class="ghost-button" type="button" @click="reloadChapters">刷新</button>
        <button class="ghost-button" type="button" @click="selectAdjacentChapter('previous')">上一章</button>
        <button class="ghost-button" type="button" @click="selectAdjacentChapter('next')">下一章</button>
        <button class="primary-button" :disabled="isSaving || !activeChapter" type="button" @click="saveActiveChapter">
          <Save :size="16" />
          {{ isSaving ? '保存中' : '保存草稿' }}
        </button>
      </ActionBar>
      </template>
    </PageHeader>

    <div class="editor-grid">
      <aside class="panel chapter-list">
        <div class="panel-body">
          <h3 class="panel-title">章节列表</h3>
          <button
            v-for="chapter in chapters"
            :key="chapter.id"
            class="chapter-button"
            :class="{ active: chapter.id === activeChapter?.id }"
            type="button"
            @click="selectChapter(chapter.id)"
          >
            <span>第 {{ chapter.order }} 章</span>
            <strong>{{ chapter.title }}</strong>
          </button>
        </div>
      </aside>

      <section class="panel editor-panel">
        <div class="panel-body">
          <WritingEditor
            :model-value="activeChapterDraft"
            :title="activeChapter?.title ?? '暂无章节'"
            :dirty="hasDirtyChapter"
            :save-state="saveState"
            empty-message="当前输出目录尚未加载到章节正文。"
            min-height="470px"
            aria-label="章节正文"
            @save="saveActiveChapter"
            @update:model-value="editorStore.updateActiveChapterDraft"
          />
          <StatusMessage type="error" :message="errorMessage" />
        </div>
      </section>

      <aside class="panel meta-panel">
        <div class="panel-body">
          <h3 class="panel-title">章节元信息</h3>
          <dl v-if="activeChapter">
            <dt>状态</dt>
            <dd>{{ activeChapter.status }}</dd>
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
import { Save } from '@lucide/vue'
import { storeToRefs } from 'pinia'
import { computed, onMounted, ref } from 'vue'
import { onBeforeRouteLeave } from 'vue-router'

import ActionBar from '@/components/ui/ActionBar.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import StatusMessage from '@/components/ui/StatusMessage.vue'
import { WritingEditor } from '@/features/writing'
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
const saveState = computed(() => (saveMessage.value ? { state: 'saved' as const, text: saveMessage.value } : null))

onMounted(async () => {
  await projectsStore.loadProjects()
  await editorStore.loadChapters(projectsStore.activeProjectId)
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
  try {
    await editorStore.saveActiveChapter()
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

const reloadChapters = async () => {
  if (!confirmDirtyNavigation()) return
  await editorStore.loadChapters(projectsStore.activeProjectId)
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

.chapter-button {
  display: block;
  width: 100%;
  border-radius: 8px;
  background: transparent;
  color: var(--color-text);
  padding: 10px;
  text-align: left;
}

.chapter-button.active {
  background: #e3f1f2;
}

.chapter-button span {
  display: block;
  color: var(--color-text-muted);
  font-size: 12px;
}

.chapter-button strong {
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
