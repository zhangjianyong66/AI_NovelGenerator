<template>
  <section class="page">
    <PageHeader title="生成任务" subtitle="创建后端生成任务，查看状态、日志和错误。" />

    <StatusMessage v-if="isLoading" type="loading" message="正在同步生成任务状态。" />
    <StatusMessage type="info" message="设定、目录、草稿和定稿已接入本地真实执行器，需要有效 LLM 配置，完成后会写入项目文件。" />
    <StatusMessage type="warning" message="审校和批量阶段仍处于后续接入范围，当前只创建任务记录。" />
    <StatusMessage v-if="!canWriteToBackend" type="warning" :message="writeUnavailableMessage" />
    <StatusMessage type="error" :message="errorMessage" />
    <StatusMessage :type="chapterTargetStatus" :message="chapterTargetMessage" />

    <FormSection title="创建任务" description="后端会按当前项目配置创建任务；草稿、定稿和审校会使用当前章节号。">
      <GenerationActions :disabled="isLoading || !canWriteToBackend" @create="createJob" @create-batch="createBatchJob" />
    </FormSection>

    <FormSection title="批量参数" description="批量生成会使用下列章节范围、目标字数、最低字数和自动扩写设置。">
      <StatusMessage :type="batchValidationStatus" :message="batchValidationMessage" />
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
import type { Chapter, GenerationStage, ProjectConfig } from '@/services/types'
import { useGenerationStore } from '@/stores/generation'
import { useProjectsStore } from '@/stores/projects'

type StatusMessageType = 'success' | 'error' | 'warning' | 'loading' | 'empty' | 'info'

const chapterStages = new Set<GenerationStage>(['draft', 'finalization', 'consistency'])
const existingChapterStages = new Set<GenerationStage>(['finalization', 'consistency'])
const refreshChapterStages = new Set<GenerationStage>(['draft', 'finalization'])
const projectsStore = useProjectsStore()
const generationStore = useGenerationStore()
const { jobs, isLoading } = storeToRefs(generationStore)
const errorMessage = ref('')
const selectedJobId = ref('')
const bridgeStatus = ref<ServiceBridgeStatus>({ ...serviceBridge.getStatus() })
const projectConfig = ref<ProjectConfig | null>(null)
const chapters = ref<Chapter[]>([])
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

const loadGenerationContext = async () => {
  try {
    const [nextConfig, nextChapters] = await Promise.all([
      serviceBridge.getProjectConfig(),
      serviceBridge.listChapters(projectsStore.activeProjectId),
    ])
    projectConfig.value = nextConfig
    chapters.value = nextChapters
  } catch (error) {
    errorMessage.value = normalizeGenerationError(error, '同步生成任务上下文失败')
  } finally {
    syncBridgeStatus()
  }
}

onMounted(async () => {
  await projectsStore.loadProjects()
  syncBridgeStatus()
  await loadGenerationContext()
  await generationStore.loadJobs(projectsStore.activeProjectId)
  syncBridgeStatus()
  selectedJobId.value = jobs.value[0]?.id ?? ''
})

const selectedJob = computed(() => jobs.value.find((job) => job.id === selectedJobId.value) ?? jobs.value[0])
const availableChapterNumbers = computed(() => new Set(chapters.value.map((chapter) => chapter.order)))
const currentChapterNumber = computed(() => Number(projectConfig.value?.novelParams.chapterNum || 0))
const isCurrentChapterValid = computed(() => Number.isInteger(currentChapterNumber.value) && currentChapterNumber.value > 0)
const hasCurrentChapterFile = computed(() => availableChapterNumbers.value.has(currentChapterNumber.value))
const chapterTargetStatus = computed<StatusMessageType>(() => {
  if (!canWriteToBackend.value) return 'warning'
  if (!isCurrentChapterValid.value || !hasCurrentChapterFile.value) return 'warning'
  return 'info'
})
const chapterTargetMessage = computed(() => {
  if (!canWriteToBackend.value) return ''
  if (!isCurrentChapterValid.value) {
    return '章节类任务需要当前章节号，请先在设置页填写大于 0 的当前章节。'
  }
  if (!hasCurrentChapterFile.value) {
    return `草稿任务可生成第 ${currentChapterNumber.value} 章；定稿和审校需要当前输出目录已有 chapter_${currentChapterNumber.value}.txt。`
  }
  return `草稿可覆盖生成第 ${currentChapterNumber.value} 章；定稿和审校将使用 chapter_${currentChapterNumber.value}.txt。`
})
const missingBatchChapters = computed(() => {
  const missing: number[] = []
  const startChapter = Number(batchForm.value.startChapter)
  const endChapter = Number(batchForm.value.endChapter)
  if (!Number.isInteger(startChapter) || !Number.isInteger(endChapter) || startChapter <= 0 || endChapter < startChapter) {
    return missing
  }
  for (let chapterNumber = startChapter; chapterNumber <= endChapter; chapterNumber += 1) {
    if (!availableChapterNumbers.value.has(chapterNumber)) missing.push(chapterNumber)
  }
  return missing
})
const batchValidationMessage = computed(() => validateBatchForm() ?? `批量任务将检查第 ${batchForm.value.startChapter}-${batchForm.value.endChapter} 章。`)
const batchValidationStatus = computed<StatusMessageType>(() => (validateBatchForm() ? 'warning' : 'info'))

const normalizeGenerationError = (error: unknown, fallbackMessage: string) => {
  if (typeof error === 'object' && error !== null) {
    if ('message' in error && typeof error.message === 'string' && error.message.trim()) {
      return error.message
    }
    if ('detail' in error && typeof error.detail === 'string' && error.detail.trim()) {
      return error.detail
    }
  }
  if (error instanceof Error && error.message) return error.message
  return fallbackMessage
}

const validateChapterStage = () => {
  if (!isCurrentChapterValid.value) {
    return '当前章节号为空或不是正整数，请先在设置页填写当前章节。'
  }
  return ''
}

const validateExistingChapterStage = () => {
  const chapterValidation = validateChapterStage()
  if (chapterValidation) return chapterValidation
  if (!hasCurrentChapterFile.value) {
    return `当前输出目录没有 chapter_${currentChapterNumber.value}.txt，请先准备章节文件。`
  }
  return ''
}

const validateBatchForm = () => {
  const startChapter = Number(batchForm.value.startChapter)
  const endChapter = Number(batchForm.value.endChapter)
  const targetWords = Number(batchForm.value.targetWords)
  const minimumWords = Number(batchForm.value.minimumWords)
  if (!Number.isInteger(startChapter) || startChapter <= 0) return '起始章节必须是大于 0 的整数。'
  if (!Number.isInteger(endChapter) || endChapter < startChapter) return '结束章节不能小于起始章节。'
  if (targetWords < 0 || minimumWords < 0) return '目标字数和最低字数不能为负数。'
  if (missingBatchChapters.value.length > 0) {
    return `当前输出目录缺少章节文件：${missingBatchChapters.value.map((chapterNumber) => `chapter_${chapterNumber}.txt`).join('、')}。`
  }
  return ''
}

const createJob = async (stage: GenerationStage) => {
  errorMessage.value = ''
  if (!canWriteToBackend.value) {
    errorMessage.value = writeUnavailableMessage.value
    return
  }
  if (chapterStages.has(stage)) {
    const validationMessage = existingChapterStages.has(stage) ? validateExistingChapterStage() : validateChapterStage()
    if (validationMessage) {
      errorMessage.value = validationMessage
      return
    }
  }
  try {
    await generationStore.createJob({
      projectId: projectsStore.activeProjectId,
      stage,
      chapterNumber: chapterStages.has(stage) ? currentChapterNumber.value : undefined,
    })
    if (refreshChapterStages.has(stage)) {
      await loadGenerationContext()
    }
    syncBridgeStatus()
    selectedJobId.value = jobs.value[0]?.id ?? selectedJobId.value
  } catch (error) {
    syncBridgeStatus()
    errorMessage.value = normalizeGenerationError(error, '创建任务失败')
  }
}

const createBatchJob = async () => {
  errorMessage.value = ''
  if (!canWriteToBackend.value) {
    errorMessage.value = writeUnavailableMessage.value
    return
  }
  const validationMessage = validateBatchForm()
  if (validationMessage) {
    errorMessage.value = validationMessage
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
    errorMessage.value = normalizeGenerationError(error, '创建批量任务失败')
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
