import { defineStore } from 'pinia'

import { serviceBridge } from '@/services/serviceBridge'
import type { GenerationJob, GenerationJobCreateRequest } from '@/services/types'

export const useGenerationStore = defineStore('generation', {
  state: () => ({
    jobs: [] as GenerationJob[],
    isLoading: false,
    jobUpdatesUnsubscribe: null as (() => void) | null,
  }),
  getters: {
    runningJob(state): GenerationJob | undefined {
      return state.jobs.find((job) => job.status === 'running')
    },
    latestLogLines(state): string[] {
      return state.jobs.flatMap((job) => job.log.map((line) => `${job.title}: ${line}`)).slice(-6)
    },
  },
  actions: {
    resetProjectState() {
      this.unsubscribeFromJobUpdates()
      this.jobs = []
    },
    upsertJob(job: GenerationJob) {
      const existingIndex = this.jobs.findIndex((item) => item.id === job.id)
      if (existingIndex >= 0) {
        this.jobs = this.jobs.map((item) => (item.id === job.id ? job : item))
        return
      }
      this.jobs = [job, ...this.jobs]
    },
    async loadJobs(projectId: string) {
      this.isLoading = true
      try {
        this.jobs = await serviceBridge.listGenerationJobs(projectId)
      } finally {
        this.isLoading = false
      }
    },
    async createJob(request: GenerationJobCreateRequest) {
      this.isLoading = true
      try {
        const job = await serviceBridge.createGenerationJob(request)
        this.upsertJob(job)
        return job
      } finally {
        this.isLoading = false
      }
    },
    subscribeToJobUpdates(projectId: string) {
      this.unsubscribeFromJobUpdates()
      this.jobUpdatesUnsubscribe = serviceBridge.subscribeGenerationJobs(projectId, (job) => {
        this.upsertJob(job)
      })
    },
    unsubscribeFromJobUpdates() {
      this.jobUpdatesUnsubscribe?.()
      this.jobUpdatesUnsubscribe = null
    },
  },
})
