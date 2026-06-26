<template>
  <section class="page">
    <PageHeader title="生成任务" subtitle="创建后端生成任务，查看状态、日志和错误。" />

    <StatusMessage v-if="isLoading" type="loading" message="正在同步生成任务状态。" />
    <StatusMessage type="error" :message="errorMessage" />

    <FormSection title="创建任务" description="后端会按当前项目配置创建任务；草稿、定稿和审校会使用当前章节号。">
      <ActionBar>
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
        <button class="primary-button" :disabled="isLoading" type="button" @click="createBatchJob">
          <Play :size="16" />
          批量
        </button>
      </ActionBar>
    </FormSection>

    <FormSection title="批量参数" description="批量生成会使用下列章节范围、目标字数、最低字数和自动扩写设置。">
      <div class="batch-grid">
        <label>起始章节<input v-model.number="batchForm.startChapter" min="1" type="number" /></label>
        <label>结束章节<input v-model.number="batchForm.endChapter" min="1" type="number" /></label>
        <label>目标字数<input v-model.number="batchForm.targetWords" min="0" type="number" /></label>
        <label>最低字数<input v-model.number="batchForm.minimumWords" min="0" type="number" /></label>
        <label class="toggle"><input v-model="batchForm.autoEnrich" type="checkbox" /> 自动扩写</label>
      </div>
    </FormSection>

    <div class="generation-grid">
      <FormSection title="任务列表" description="列表用于快速扫描任务状态，选中任务后查看详细日志。">
        <StatusMessage v-if="jobs.length === 0" type="empty" message="当前项目还没有生成任务。" />
        <div class="job-list">
          <button
            v-for="job in jobs"
            :key="job.id"
            class="job-card"
            :class="{ active: job.id === selectedJobId }"
            type="button"
            @click="selectedJobId = job.id"
          >
            <div class="job-heading">
              <div>
                <h3>{{ job.title }}</h3>
                <p>{{ job.startedAt }}</p>
              </div>
              <span class="status-pill" :class="pillClass(job.status)">{{ statusLabel(job.status) }}</span>
            </div>
            <div class="progress-track">
              <span :style="{ width: `${job.progress}%` }" />
            </div>
          </button>
        </div>
      </FormSection>

      <FormSection title="任务详情与日志" description="查看选中任务的进度、错误和后端日志。">
        <template v-if="selectedJob">
          <div class="detail-meta">
            <span>阶段：{{ stageLabel(selectedJob.stage) }}</span>
            <span>进度：{{ selectedJob.progress }}%</span>
            <span>状态：{{ statusLabel(selectedJob.status) }}</span>
          </div>
          <StatusMessage v-if="selectedJob.error" type="error" :message="selectedJob.error" />
          <LongTextEditor
            :model-value="selectedJob.log.join('\n')"
            title="日志"
            readonly
            empty-message="该任务暂无日志。"
            min-height="300px"
          />
        </template>
        <StatusMessage v-else type="empty" message="请选择一个任务查看详情。" />
      </FormSection>
    </div>
  </section>
</template>

<script setup lang="ts">
import { Play } from '@lucide/vue'
import { storeToRefs } from 'pinia'
import { computed, onMounted, ref, watch } from 'vue'

import ActionBar from '@/components/ui/ActionBar.vue'
import FormSection from '@/components/ui/FormSection.vue'
import LongTextEditor from '@/components/ui/LongTextEditor.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import StatusMessage from '@/components/ui/StatusMessage.vue'
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
const selectedJobId = ref('')
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
  selectedJobId.value = jobs.value[0]?.id ?? ''
})

const selectedJob = computed(() => jobs.value.find((job) => job.id === selectedJobId.value) ?? jobs.value[0])

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
    selectedJobId.value = jobs.value[0]?.id ?? selectedJobId.value
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
    selectedJobId.value = jobs.value[0]?.id ?? selectedJobId.value
  } catch (error) {
    errorMessage.value =
      error instanceof Error
        ? error.message
        : typeof error === 'object' && error !== null && 'message' in error
          ? String(error.message)
          : '创建批量任务失败'
  }
}

const pillClass = (status: GenerationJobStatus) => ({
  warning: status === 'running' || status === 'queued',
  neutral: status === 'paused',
})

const statusLabel = (status: GenerationJobStatus) => {
  const labels: Record<GenerationJobStatus, string> = {
    queued: '排队中',
    running: '运行中',
    paused: '已暂停',
    done: '已完成',
    failed: '失败',
  }
  return labels[status]
}

const stageLabel = (stage: GenerationStage) => {
  const labels: Record<GenerationStage, string> = {
    architecture: '设定',
    directory: '目录',
    draft: '草稿',
    finalization: '定稿',
    batch: '批量',
    consistency: '审校',
  }
  return labels[stage]
}

watch(jobs, (nextJobs) => {
  if (!selectedJobId.value || !nextJobs.some((job) => job.id === selectedJobId.value)) {
    selectedJobId.value = nextJobs[0]?.id ?? ''
  }
})
</script>

<style scoped>
.generation-grid {
  display: grid;
  grid-template-columns: minmax(320px, 0.85fr) minmax(0, 1.15fr);
  gap: 16px;
}

.job-list {
  display: grid;
  gap: 10px;
}

.batch-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr)) 140px;
  gap: 12px;
  align-items: end;
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

.job-heading {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.job-card {
  width: 100%;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  background: var(--color-surface);
  padding: 12px;
  color: var(--color-text);
  text-align: left;
}

.job-card.active {
  border-color: var(--color-primary);
  background: #edf7f8;
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
  margin: 14px 0 0;
  overflow: hidden;
}

.progress-track span {
  display: block;
  height: 100%;
  background: var(--color-primary);
}

.detail-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 12px;
  color: var(--color-text-muted);
  font-size: 13px;
}
</style>
