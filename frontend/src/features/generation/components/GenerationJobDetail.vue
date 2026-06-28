<template>
  <template v-if="job">
    <div class="detail-meta">
      <span>项目：{{ job.projectId }}</span>
      <span>阶段：{{ stageLabel(job.stage) }}</span>
      <span>进度：{{ job.progress }}%</span>
      <span>状态：{{ statusLabel(job.status) }}</span>
      <span>开始：{{ job.startedAt }}</span>
    </div>
    <StatusMessage
      v-if="job.status === 'queued'"
      type="info"
      message="任务已记录在本地后端内存队列，正在等待执行或后续执行器接入。"
    />
    <StatusMessage v-if="job.error" type="error" :message="job.error" />
    <LongTextEditor
      :model-value="job.log.join('\n')"
      title="日志"
      readonly
      empty-message="该任务暂无日志。"
      min-height="300px"
    />
  </template>
  <StatusMessage v-else type="empty" message="请选择一个任务查看详情。" />
</template>

<script setup lang="ts">
import { LongTextEditor, StatusMessage } from '@/components/ui'
import type { GenerationJob, GenerationJobStatus, GenerationStage } from '@/services/types'

defineProps<{
  job?: GenerationJob
}>()

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
</script>
