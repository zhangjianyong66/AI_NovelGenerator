import { defineStore } from 'pinia'

import { mockApi } from '@/services/mockApi'
import type { Project } from '@/services/types'

export const useProjectsStore = defineStore('projects', {
  state: () => ({
    projects: [] as Project[],
    activeProjectId: 'p-ember-city',
    isLoading: false,
  }),
  getters: {
    activeProject(state): Project | undefined {
      return state.projects.find((project) => project.id === state.activeProjectId)
    },
  },
  actions: {
    async loadProjects() {
      if (this.projects.length > 0) return
      this.isLoading = true
      try {
        this.projects = await mockApi.listProjects()
        if (!this.activeProjectId && this.projects[0]) {
          this.activeProjectId = this.projects[0].id
        }
      } finally {
        this.isLoading = false
      }
    },
    selectProject(projectId: string) {
      this.activeProjectId = projectId
    },
  },
})
