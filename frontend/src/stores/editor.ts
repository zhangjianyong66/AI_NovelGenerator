import { defineStore } from 'pinia'

import { mockApi } from '@/services/mockApi'
import type { Chapter } from '@/services/types'

export const useEditorStore = defineStore('editor', {
  state: () => ({
    chapters: [] as Chapter[],
    activeChapterId: '',
    isLoading: false,
  }),
  getters: {
    activeChapter(state): Chapter | undefined {
      return state.chapters.find((chapter) => chapter.id === state.activeChapterId) ?? state.chapters[0]
    },
  },
  actions: {
    async loadChapters(projectId: string) {
      this.isLoading = true
      try {
        this.chapters = await mockApi.listChapters(projectId)
        this.activeChapterId = this.activeChapterId || this.chapters[0]?.id || ''
      } finally {
        this.isLoading = false
      }
    },
    selectChapter(chapterId: string) {
      this.activeChapterId = chapterId
    },
  },
})
