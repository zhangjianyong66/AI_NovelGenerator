import { defineStore } from 'pinia'

import { serviceBridge } from '@/services/serviceBridge'
import type { GenerationJob, GenerationJobCreateRequest } from '@/services/types'

export const useGenerationStore = defineStore('generation', {
  state: () => ({
    jobs: [] as GenerationJob[],
    isLoading: false,
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
      this.jobs = []
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
        this.jobs = [job, ...this.jobs.filter((item) => item.id !== job.id)]
        return job
      } finally {
        this.isLoading = false
      }
    },
  },
})
