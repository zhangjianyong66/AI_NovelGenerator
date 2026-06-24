<template>
  <section class="page">
    <div class="page-header">
      <div>
        <h2 class="page-title">章节编辑</h2>
        <p class="page-subtitle">章节列表、正文编辑区和元信息面板使用 mock 数据呈现。</p>
      </div>
      <button class="primary-button" type="button">
        <Save :size="16" />
        保存草稿
      </button>
    </div>

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
            @click="editorStore.selectChapter(chapter.id)"
          >
            <span>第 {{ chapter.order }} 章</span>
            <strong>{{ chapter.title }}</strong>
          </button>
        </div>
      </aside>

      <section class="panel editor-panel">
        <div class="panel-body">
          <h3>{{ activeChapter?.title ?? '暂无章节' }}</h3>
          <textarea :value="activeChapter?.content" aria-label="章节正文" />
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
            <dd>{{ activeChapter.words }}</dd>
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
import { onMounted } from 'vue'

import { useEditorStore } from '@/stores/editor'
import { useProjectsStore } from '@/stores/projects'

const projectsStore = useProjectsStore()
const editorStore = useEditorStore()
const { chapters, activeChapter } = storeToRefs(editorStore)

onMounted(async () => {
  await projectsStore.loadProjects()
  await editorStore.loadChapters(projectsStore.activeProjectId)
})
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

.editor-panel h3 {
  margin: 0 0 12px;
  font-size: 20px;
}

textarea {
  width: 100%;
  min-height: 470px;
  resize: vertical;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 14px;
  color: var(--color-text);
  line-height: 1.8;
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
