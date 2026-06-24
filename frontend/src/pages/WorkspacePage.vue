<template>
  <section class="page">
    <div class="page-header">
      <div>
        <h2 class="page-title">工作台</h2>
        <p class="page-subtitle">集中查看小说设定、目录蓝图、章节正文和生成上下文。</p>
      </div>
      <div class="action-row">
        <button v-for="action in actions" :key="action" class="ghost-button" type="button">{{ action }}</button>
      </div>
    </div>

    <div class="grid three">
      <MetricTile label="当前章节" :value="activeChapter ? `第 ${activeChapter.order} 章` : '-'" />
      <MetricTile label="运行任务" :value="runningJob?.title ?? '无'" />
      <MetricTile label="知识条目" :value="knowledgeCount" />
    </div>

    <div class="workbench-grid">
      <section class="panel">
        <div class="panel-body">
          <h3 class="panel-title">小说设定</h3>
          <p class="muted">{{ activeProject?.summary ?? '正在加载项目设定' }}</p>
          <div class="tag-row">
            <span class="tag">世界观</span>
            <span class="tag">人物关系</span>
            <span class="tag">冲突主线</span>
          </div>
        </div>
      </section>

      <section class="panel">
        <div class="panel-body">
          <h3 class="panel-title">目录蓝图</h3>
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
          <h3 class="panel-title">章节正文</h3>
          <h4>{{ activeChapter?.title ?? '暂无章节' }}</h4>
          <p>{{ activeChapter?.content ?? '章节 mock 数据加载中。' }}</p>
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
import { computed, onMounted, ref } from 'vue'

import MetricTile from '@/components/MetricTile.vue'
import { mockApi } from '@/services/mockApi'
import { useEditorStore } from '@/stores/editor'
import { useGenerationStore } from '@/stores/generation'
import { useProjectsStore } from '@/stores/projects'

const actions = ['生成设定', '扩展目录', '生成草稿', '润色定稿', '批量生成']
const knowledgeCount = ref(0)

const projectsStore = useProjectsStore()
const editorStore = useEditorStore()
const generationStore = useGenerationStore()
const { activeProject, activeProjectId } = storeToRefs(projectsStore)
const { chapters, activeChapter } = storeToRefs(editorStore)
const { runningJob, latestLogLines } = storeToRefs(generationStore)

onMounted(async () => {
  await projectsStore.loadProjects()
  await Promise.all([
    editorStore.loadChapters(activeProjectId.value),
    generationStore.loadJobs(activeProjectId.value),
    mockApi.listKnowledgeItems().then((items) => {
      knowledgeCount.value = items.length
    }),
  ])
})
</script>

<style scoped>
.action-row {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 8px;
}

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

h4 {
  margin: 0 0 10px;
  font-size: 18px;
}

.main-draft p {
  margin: 0;
  line-height: 1.85;
}
</style>
