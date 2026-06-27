<template>
  <section class="page">
    <PageHeader title="生成任务" subtitle="创建后端生成任务，查看状态、日志和错误。" />

    <StatusMessage v-if="isLoading" type="loading" message="正在同步生成任务状态。" />
    <StatusMessage type="warning" message="当前接口只创建排队任务，尚未接入真实 LLM 执行器，不会直接生成或修改小说文件。" />
    <StatusMessage v-if="!canWriteToBackend" type="warning" :message="writeUnavailableMessage" />
    <StatusMessage type="error" :message="errorMessage" />

    <FormSection title="创建任务" description="后端会按当前项目配置创建任务；草稿、定稿和审校会使用当前章节号。">
      <GenerationActions :disabled="isLoading || !canWriteToBackend" @create="createJob" @create-batch="createBatchJob" />
    </FormSection>

    <FormSection title="批量参数" description="批量生成会使用下列章节范围、目标字数、最低字数和自动扩写设置。">
      <div class="batch-grid">
        <TextField
          :model-value="batchForm.startChapter"
          label="起始章节"
          min="1"
          type="number"
          @update:model-value="batchForm.startChapter = Number($event)"
        />
        <TextField
          :model-value="batchForm.endChapter"
          label="结束章节"
          min="1"
          type="number"
          @update:model-value="batchForm.endChapter = Number($event)"
        />
        <TextField
          :model-value="batchForm.targetWords"
          label="目标字数"
          min="0"
          type="number"
          @update:model-value="batchForm.targetWords = Number($event)"
        />
        <TextField
          :model-value="batchForm.minimumWords"
          label="最低字数"
          min="0"
          type="number"
          @update:model-value="batchForm.minimumWords = Number($event)"
        />
        <ToggleField v-model="batchForm.autoEnrich" label="自动扩写" />
      </div>
    </FormSection>

    <div class="generation-grid">
      <FormSection title="任务列表" description="列表用于快速扫描任务状态，选中任务后查看详细日志。">
        <StatusMessage v-if="jobs.length === 0" type="empty" message="当前项目还没有生成任务。" />
        <GenerationJobList :jobs="jobs" :selected-job-id="selectedJobId" @select="selectedJobId = $event" />
      </FormSection>

      <FormSection title="任务详情与日志" description="查看选中任务的进度、错误和后端日志。">
        <GenerationJobDetail :job="selectedJob" />
      </FormSection>
    </div>
  </section>
</template>

<script setup lang="ts">
import { storeToRefs } from 'pinia'
import { computed, onMounted, ref, watch } from 'vue'

import FormSection from '@/components/ui/FormSection.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import StatusMessage from '@/components/ui/StatusMessage.vue'
import TextField from '@/components/ui/TextField.vue'
import ToggleField from '@/components/ui/ToggleField.vue'
import { GenerationActions, GenerationJobDetail, GenerationJobList } from '@/features/generation'
import { serviceBridge, type ServiceBridgeStatus } from '@/services/serviceBridge'
import type { GenerationStage } from '@/services/types'
import { useGenerationStore } from '@/stores/generation'
import { useProjectsStore } from '@/stores/projects'

const projectsStore = useProjectsStore()
const generationStore = useGenerationStore()
const { jobs, isLoading } = storeToRefs(generationStore)
const errorMessage = ref('')
const selectedJobId = ref('')
const bridgeStatus = ref<ServiceBridgeStatus>({ ...serviceBridge.getStatus() })
const batchForm = ref({
  startChapter: 1,
  endChapter: 1,
  targetWords: 3000,
  minimumWords: 2000,
  autoEnrich: false,
})
const canWriteToBackend = computed(() => serviceBridge.canWrite(bridgeStatus.value))
const writeUnavailableMessage = computed(() => serviceBridge.getWriteUnavailableMessage(bridgeStatus.value))

const syncBridgeStatus = () => {
  bridgeStatus.value = { ...serviceBridge.getStatus() }
}

onMounted(async () => {
  await projectsStore.loadProjects()
  syncBridgeStatus()
  await generationStore.loadJobs(projectsStore.activeProjectId)
  syncBridgeStatus()
  selectedJobId.value = jobs.value[0]?.id ?? ''
})

const selectedJob = computed(() => jobs.value.find((job) => job.id === selectedJobId.value) ?? jobs.value[0])

const createJob = async (stage: GenerationStage) => {
  errorMessage.value = ''
  if (!canWriteToBackend.value) {
    errorMessage.value = writeUnavailableMessage.value
    return
  }
  try {
    const projectConfig = await serviceBridge.getProjectConfig()
    await generationStore.createJob({
      projectId: projectsStore.activeProjectId,
      stage,
      chapterNumber: ['draft', 'finalization', 'consistency'].includes(stage)
        ? Number(projectConfig.novelParams.chapterNum || 0)
        : undefined,
    })
    syncBridgeStatus()
    selectedJobId.value = jobs.value[0]?.id ?? selectedJobId.value
  } catch (error) {
    syncBridgeStatus()
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
  if (!canWriteToBackend.value) {
    errorMessage.value = writeUnavailableMessage.value
    return
  }
  try {
    await generationStore.createJob({
      projectId: projectsStore.activeProjectId,
      stage: 'batch',
      ...batchForm.value,
    })
    syncBridgeStatus()
    selectedJobId.value = jobs.value[0]?.id ?? selectedJobId.value
  } catch (error) {
    syncBridgeStatus()
    errorMessage.value =
      error instanceof Error
        ? error.message
        : typeof error === 'object' && error !== null && 'message' in error
          ? String(error.message)
          : '创建批量任务失败'
  }
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

.batch-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr)) 140px;
  gap: 12px;
  align-items: end;
}

.generation-grid :deep(.job-list) {
  display: grid;
  gap: 10px;
}

.generation-grid :deep(.job-heading) {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.generation-grid :deep(.job-card) {
  width: 100%;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  background: var(--color-surface);
  padding: 12px;
  color: var(--color-text);
  text-align: left;
}

.generation-grid :deep(.job-card.active) {
  border-color: var(--color-primary);
  background: #edf7f8;
}

.generation-grid :deep(.job-heading h3) {
  margin: 0;
  font-size: 18px;
}

.generation-grid :deep(.job-heading p) {
  margin: 5px 0 0;
  color: var(--color-text-muted);
}

.generation-grid :deep(.progress-track) {
  height: 8px;
  border-radius: 999px;
  background: var(--color-surface-muted);
  margin: 14px 0 0;
  overflow: hidden;
}

.generation-grid :deep(.progress-track span) {
  display: block;
  height: 100%;
  background: var(--color-primary);
}

.generation-grid :deep(.detail-meta) {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 12px;
  color: var(--color-text-muted);
  font-size: 13px;
}
</style>
