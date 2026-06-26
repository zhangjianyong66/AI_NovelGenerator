<template>
  <section class="page">
    <PageHeader title="项目" subtitle="按小说项目进入工作台，并查看当前后端输出路径与小说参数。">
      <template #actions>
      <button class="primary-button" type="button">
        <Plus :size="16" />
        新建项目
      </button>
      </template>
    </PageHeader>

    <section v-if="projectConfig" class="panel">
      <div class="panel-body">
        <div class="config-summary">
          <div>
            <h3 class="panel-title">当前输出路径</h3>
            <p class="path-text">{{ projectConfig.outputPath || '未设置' }}</p>
          </div>
          <div class="summary-meta">
            <span>主题：{{ projectConfig.novelParams.topic || '未填写' }}</span>
            <span>类型：{{ projectConfig.novelParams.genre || '未填写' }}</span>
            <span>章节：{{ projectConfig.novelParams.numChapters }}</span>
            <span>每章字数：{{ projectConfig.novelParams.wordNumber }}</span>
          </div>
        </div>
      </div>
    </section>

    <div class="grid two">
      <article
        v-for="project in projects"
        :key="project.id"
        class="project-card panel"
        :class="{ active: project.id === activeProjectId }"
        @click="selectProject(project.id)"
      >
        <div class="panel-body">
          <div class="project-heading">
            <div>
              <h3>{{ project.title }}</h3>
              <p>{{ project.genre }}</p>
            </div>
            <span class="status-pill" :class="{ neutral: project.status !== 'active' }">
              {{ statusLabel(project.status) }}
            </span>
          </div>
          <p class="summary">{{ project.summary }}</p>
          <div class="project-meta">
            <span>章节 {{ project.chaptersCompleted }}/{{ project.chaptersTotal }}</span>
            <span>更新 {{ project.updatedAt }}</span>
          </div>
        </div>
      </article>
    </div>
  </section>
</template>

<script setup lang="ts">
import { Plus } from '@lucide/vue'
import { storeToRefs } from 'pinia'
import { onMounted, ref } from 'vue'

import PageHeader from '@/components/ui/PageHeader.vue'
import { serviceBridge } from '@/services/serviceBridge'
import { useProjectsStore } from '@/stores/projects'
import type { ProjectConfig, ProjectStatus } from '@/services/types'

const projectsStore = useProjectsStore()
const { projects, activeProjectId } = storeToRefs(projectsStore)
const projectConfig = ref<ProjectConfig>()

onMounted(() => {
  void projectsStore.loadProjects()
  void loadProjectConfig()
})

const loadProjectConfig = async () => {
  projectConfig.value = await serviceBridge.getProjectConfig()
}

const selectProject = (projectId: string) => {
  projectsStore.selectProject(projectId)
}

const statusLabel = (status: ProjectStatus) => {
  const labels: Record<ProjectStatus, string> = {
    active: '进行中',
    draft: '草案',
    archived: '归档',
  }
  return labels[status]
}
</script>

<style scoped>
.project-card {
  cursor: default;
  transition:
    border-color 0.16s ease,
    transform 0.16s ease;
}

.project-card.active {
  border-color: var(--color-primary);
}

.project-card:hover {
  transform: translateY(-2px);
}

.project-heading,
.project-meta {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 14px;
}

h3 {
  margin: 0;
  font-size: 18px;
}

.project-heading p,
.summary,
.project-meta {
  color: var(--color-text-muted);
}

.project-heading p {
  margin: 4px 0 0;
}

.summary {
  margin: 18px 0;
  line-height: 1.6;
}

.project-meta {
  border-top: 1px solid var(--color-border);
  padding-top: 12px;
  font-size: 13px;
}

.config-summary {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(320px, 0.8fr);
  gap: 16px;
  align-items: start;
}

.path-text {
  margin: 0;
  overflow-wrap: anywhere;
  color: var(--color-text-muted);
  line-height: 1.6;
}

.summary-meta {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px 12px;
  color: var(--color-text-muted);
  font-size: 13px;
}
</style>
