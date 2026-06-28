import { defineStore } from 'pinia'

import { serviceBridge } from '@/services/serviceBridge'
import type { Project, ProjectCreateRequest, ProjectSwitchRequest } from '@/services/types'

export const useProjectsStore = defineStore('projects', {
  state: () => ({
    projects: [] as Project[],
    activeProjectId: '',
    isLoading: false,
  }),
  getters: {
    activeProject(state): Project | undefined {
      return state.projects.find((project) => project.id === state.activeProjectId)
    },
  },
  actions: {
    async loadProjects(force = false) {
      if (!force && this.projects.length > 0) return
      this.isLoading = true
      try {
        this.projects = await serviceBridge.listProjects()
        if (!this.projects.some((project) => project.id === this.activeProjectId) && this.projects[0]) {
          this.activeProjectId = this.projects[0].id
        }
      } finally {
        this.isLoading = false
      }
    },
    selectProject(projectId: string) {
      this.activeProjectId = projectId
    },
    async createProject(request: ProjectCreateRequest) {
      this.isLoading = true
      try {
        const project = await serviceBridge.createProject(request)
        this.activeProjectId = project.id
        await this.loadProjects(true)
        this.activeProjectId = this.projects.find((item) => item.status === 'active')?.id ?? project.id
        return project
      } finally {
        this.isLoading = false
      }
    },
    async switchProject(request: ProjectSwitchRequest) {
      this.isLoading = true
      try {
        const project = await serviceBridge.switchProject(request)
        this.activeProjectId = project.id
        await this.loadProjects(true)
        this.activeProjectId = this.projects.find((item) => item.status === 'active')?.id ?? project.id
        return project
      } finally {
        this.isLoading = false
      }
    },
  },
})
