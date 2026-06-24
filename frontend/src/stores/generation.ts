import { defineStore } from 'pinia'

import { mockApi } from '@/services/mockApi'
import type { GenerationJob } from '@/services/types'

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
    async loadJobs(projectId: string) {
      this.isLoading = true
      try {
        this.jobs = await mockApi.listGenerationJobs(projectId)
      } finally {
        this.isLoading = false
      }
    },
  },
})
