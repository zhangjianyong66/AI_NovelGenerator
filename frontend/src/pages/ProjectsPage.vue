<template>
  <section class="page">
    <div class="page-header">
      <div>
        <h2 class="page-title">项目</h2>
        <p class="page-subtitle">按小说项目进入工作台，当前仅展示 mock 项目数据。</p>
      </div>
      <button class="primary-button" type="button">
        <Plus :size="16" />
        新建项目
      </button>
    </div>

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
import { onMounted } from 'vue'

import { useProjectsStore } from '@/stores/projects'
import type { ProjectStatus } from '@/services/types'

const projectsStore = useProjectsStore()
const { projects, activeProjectId } = storeToRefs(projectsStore)

onMounted(() => {
  void projectsStore.loadProjects()
})

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
</style>
