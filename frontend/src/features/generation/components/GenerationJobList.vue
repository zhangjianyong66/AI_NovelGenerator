<template>
  <div class="job-list">
    <button
      v-for="job in jobs"
      :key="job.id"
      class="job-card"
      :class="{ active: job.id === selectedJobId }"
      type="button"
      @click="$emit('select', job.id)"
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
</template>

<script setup lang="ts">
import type { GenerationJob, GenerationJobStatus } from '@/services/types'

defineProps<{
  jobs: GenerationJob[]
  selectedJobId: string
}>()

defineEmits<{
  select: [jobId: string]
}>()

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
</script>

