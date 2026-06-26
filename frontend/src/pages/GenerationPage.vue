<template>
  <section class="page">
    <div class="page-header">
      <div>
        <h2 class="page-title">生成任务</h2>
        <p class="page-subtitle">创建后端生成任务，查看状态、日志和错误。</p>
      </div>
      <div class="action-row">
        <button
          v-for="action in actions"
          :key="action.stage"
          class="primary-button"
          :disabled="isLoading"
          type="button"
          @click="createJob(action.stage)"
        >
          <Play :size="16" />
          {{ action.label }}
        </button>
        <button class="primary-button" :disabled="isLoading" type="button" @click="showBatchPanel = true">
          <Play :size="16" />
          批量
        </button>
      </div>
    </div>

    <p v-if="errorMessage" class="error-message">{{ errorMessage }}</p>

    <section v-if="showBatchPanel" class="panel">
      <div class="panel-body">
        <div class="batch-heading">
          <h3>批量生成参数</h3>
          <button class="ghost-button" type="button" @click="cancelBatch">取消</button>
        </div>
        <div class="batch-grid">
          <label>起始章节<input v-model.number="batchForm.startChapter" min="1" type="number" /></label>
          <label>结束章节<input v-model.number="batchForm.endChapter" min="1" type="number" /></label>
          <label>目标字数<input v-model.number="batchForm.targetWords" min="0" type="number" /></label>
          <label>最低字数<input v-model.number="batchForm.minimumWords" min="0" type="number" /></label>
          <label class="toggle"><input v-model="batchForm.autoEnrich" type="checkbox" /> 自动扩写</label>
        </div>
        <button class="primary-button batch-submit" :disabled="isLoading" type="button" @click="createBatchJob">
          创建批量任务
        </button>
      </div>
    </section>

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
            <li v-if="job.error" class="error-message">{{ job.error }}</li>
          </ul>
        </div>
      </article>
    </div>
  </section>
</template>

<script setup lang="ts">
import { Play } from '@lucide/vue'
import { storeToRefs } from 'pinia'
import { onMounted, ref } from 'vue'

import { serviceBridge } from '@/services/serviceBridge'
import type { GenerationJobStatus, GenerationStage } from '@/services/types'
import { useGenerationStore } from '@/stores/generation'
import { useProjectsStore } from '@/stores/projects'

const actions: Array<{ label: string; stage: GenerationStage }> = [
  { label: '设定', stage: 'architecture' },
  { label: '目录', stage: 'directory' },
  { label: '草稿', stage: 'draft' },
  { label: '定稿', stage: 'finalization' },
  { label: '审校', stage: 'consistency' },
]
const projectsStore = useProjectsStore()
const generationStore = useGenerationStore()
const { jobs, isLoading } = storeToRefs(generationStore)
const errorMessage = ref('')
const showBatchPanel = ref(false)
const batchForm = ref({
  startChapter: 1,
  endChapter: 1,
  targetWords: 3000,
  minimumWords: 2000,
  autoEnrich: false,
})

onMounted(async () => {
  await projectsStore.loadProjects()
  await generationStore.loadJobs(projectsStore.activeProjectId)
})

const createJob = async (stage: GenerationStage) => {
  errorMessage.value = ''
  try {
    const projectConfig = await serviceBridge.getProjectConfig()
    await generationStore.createJob({
      projectId: projectsStore.activeProjectId,
      stage,
      chapterNumber: ['draft', 'finalization', 'consistency'].includes(stage)
        ? Number(projectConfig.novelParams.chapterNum || 0)
        : undefined,
    })
  } catch (error) {
    errorMessage.value =
      error instanceof Error
        ? error.message
        : typeof error === 'object' && error !== null && 'message' in error
          ? String(error.message)
          : '创建任务失败'
  }
}

const createBatchJob = async () => {
  errorMessage.value = ''
  try {
    await generationStore.createJob({
      projectId: projectsStore.activeProjectId,
      stage: 'batch',
      ...batchForm.value,
    })
    showBatchPanel.value = false
  } catch (error) {
    errorMessage.value =
      error instanceof Error
        ? error.message
        : typeof error === 'object' && error !== null && 'message' in error
          ? String(error.message)
          : '创建批量任务失败'
  }
}

const cancelBatch = () => {
  showBatchPanel.value = false
}

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

.primary-button:disabled {
  opacity: 0.65;
}

.job-list {
  display: grid;
  gap: 14px;
}

.batch-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.batch-heading h3 {
  margin: 0;
  font-size: 16px;
}

.batch-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr)) 140px;
  gap: 12px;
  align-items: end;
  margin-top: 12px;
}

.batch-grid label {
  display: flex;
  flex-direction: column;
  gap: 6px;
  color: var(--color-text-muted);
  font-size: 13px;
}

.batch-grid input {
  min-height: 36px;
  border: 1px solid var(--color-border);
  border-radius: 6px;
  padding: 0 10px;
  color: var(--color-text);
}

.batch-grid .toggle {
  flex-direction: row;
  align-items: center;
}

.batch-submit {
  margin-top: 12px;
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

.error-message {
  color: var(--color-warning);
}
</style>
