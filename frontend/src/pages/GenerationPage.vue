<template>
  <section class="page">
    <div class="page-header">
      <div>
        <h2 class="page-title">生成任务</h2>
        <p class="page-subtitle">查看 mock 任务状态、日志和未来生成入口。</p>
      </div>
      <div class="action-row">
        <button v-for="action in actions" :key="action" class="primary-button" type="button">
          <Play :size="16" />
          {{ action }}
        </button>
      </div>
    </div>

    <div class="job-list">
      <article v-for="job in jobs" :key="job.id" class="panel">
        <div class="panel-body">
          <div class="job-heading">
            <div>
              <h3>{{ job.title }}</h3>
              <p>{{ job.startedAt }}</p>
            </div>
            <span class="status-pill" :class="pillClass(job.status)">{{ job.status }}</span>
          </div>
          <div class="progress-track">
            <span :style="{ width: `${job.progress}%` }" />
          </div>
          <ul>
            <li v-for="line in job.log" :key="line">{{ line }}</li>
          </ul>
        </div>
      </article>
    </div>
  </section>
</template>

<script setup lang="ts">
import { Play } from '@lucide/vue'
import { storeToRefs } from 'pinia'
import { onMounted } from 'vue'

import type { GenerationJobStatus } from '@/services/types'
import { useGenerationStore } from '@/stores/generation'
import { useProjectsStore } from '@/stores/projects'

const actions = ['设定', '目录', '草稿', '定稿', '批量']
const projectsStore = useProjectsStore()
const generationStore = useGenerationStore()
const { jobs } = storeToRefs(generationStore)

onMounted(async () => {
  await projectsStore.loadProjects()
  await generationStore.loadJobs(projectsStore.activeProjectId)
})

const pillClass = (status: GenerationJobStatus) => ({
  warning: status === 'running' || status === 'queued',
  neutral: status === 'paused',
})
</script>

<style scoped>
.action-row {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 8px;
}

.job-list {
  display: grid;
  gap: 14px;
}

.job-heading {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

h3 {
  margin: 0;
  font-size: 18px;
}

.job-heading p {
  margin: 5px 0 0;
  color: var(--color-text-muted);
}

.progress-track {
  height: 8px;
  border-radius: 999px;
  background: var(--color-surface-muted);
  margin: 16px 0;
  overflow: hidden;
}

.progress-track span {
  display: block;
  height: 100%;
  background: var(--color-primary);
}

ul {
  margin: 0;
  padding-left: 20px;
  color: var(--color-text-muted);
  line-height: 1.7;
}
</style>
