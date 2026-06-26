import { defineStore } from 'pinia'

import { serviceBridge } from '@/services/serviceBridge'
import type { Chapter, ProjectFile, ProjectFileId } from '@/services/types'

export const useEditorStore = defineStore('editor', {
  state: () => ({
    chapters: [] as Chapter[],
    activeChapterId: '',
    chapterDrafts: {} as Record<string, string>,
    projectFiles: [] as ProjectFile[],
    activeProjectFileId: 'novelSetting' as ProjectFileId,
    projectFileDrafts: {} as Record<ProjectFileId, string>,
    isLoading: false,
    isSaving: false,
  }),
  getters: {
    activeChapter(state): Chapter | undefined {
      return state.chapters.find((chapter) => chapter.id === state.activeChapterId) ?? state.chapters[0]
    },
    activeChapterDraft(state): string {
      const activeChapter =
        state.chapters.find((chapter) => chapter.id === state.activeChapterId) ?? state.chapters[0]
      if (!activeChapter) return ''
      return state.chapterDrafts[activeChapter.id] ?? activeChapter.content
    },
    activeChapterWordCount(): number {
      return this.activeChapterDraft.replace(/\s/g, '').length
    },
    hasDirtyChapter(state): boolean {
      return state.chapters.some(
        (chapter) => (state.chapterDrafts[chapter.id] ?? chapter.content) !== chapter.content,
      )
    },
    activeProjectFile(state): ProjectFile | undefined {
      return (
        state.projectFiles.find((file) => file.id === state.activeProjectFileId) ??
        state.projectFiles[0]
      )
    },
    activeProjectFileDraft(state): string {
      const activeFile =
        state.projectFiles.find((file) => file.id === state.activeProjectFileId) ?? state.projectFiles[0]
      if (!activeFile) return ''
      return state.projectFileDrafts[activeFile.id] ?? activeFile.content
    },
    activeProjectFileWordCount(): number {
      return this.activeProjectFileDraft.replace(/\s/g, '').length
    },
    hasDirtyProjectFile(state): boolean {
      return state.projectFiles.some((file) => (state.projectFileDrafts[file.id] ?? file.content) !== file.content)
    },
  },
  actions: {
    async loadChapters(projectId: string) {
      this.isLoading = true
      try {
        this.chapters = await serviceBridge.listChapters(projectId)
        this.chapterDrafts = Object.fromEntries(
          this.chapters.map((chapter) => [chapter.id, chapter.content]),
        ) as Record<string, string>
        this.activeChapterId = this.activeChapterId || this.chapters[0]?.id || ''
      } finally {
        this.isLoading = false
      }
    },
    selectChapter(chapterId: string) {
      this.activeChapterId = chapterId
    },
    selectPreviousChapter() {
      const activeIndex = this.chapters.findIndex((chapter) => chapter.id === this.activeChapterId)
      if (activeIndex > 0) {
        this.activeChapterId = this.chapters[activeIndex - 1].id
      }
    },
    selectNextChapter() {
      const activeIndex = this.chapters.findIndex((chapter) => chapter.id === this.activeChapterId)
      if (activeIndex >= 0 && activeIndex < this.chapters.length - 1) {
        this.activeChapterId = this.chapters[activeIndex + 1].id
      }
    },
    updateActiveChapterDraft(content: string) {
      if (!this.activeChapter) return
      this.chapterDrafts[this.activeChapter.id] = content
    },
    discardChapterDrafts() {
      this.chapterDrafts = Object.fromEntries(
        this.chapters.map((chapter) => [chapter.id, chapter.content]),
      ) as Record<string, string>
    },
    async saveActiveChapter() {
      const activeChapter = this.activeChapter
      if (!activeChapter) return

      this.isSaving = true
      try {
        const savedChapter = await serviceBridge.saveChapter(
          activeChapter.order,
          this.chapterDrafts[activeChapter.id] ?? activeChapter.content,
        )
        this.chapters = this.chapters.map((chapter) =>
          chapter.id === savedChapter.id ? savedChapter : chapter,
        )
        this.chapterDrafts[savedChapter.id] = savedChapter.content
      } finally {
        this.isSaving = false
      }
    },
    async loadProjectFiles() {
      this.isLoading = true
      try {
        this.projectFiles = await serviceBridge.listProjectFiles()
        this.projectFileDrafts = Object.fromEntries(
          this.projectFiles.map((file) => [file.id, file.content]),
        ) as Record<ProjectFileId, string>
        this.activeProjectFileId = this.activeProjectFileId || this.projectFiles[0]?.id || 'novelSetting'
      } finally {
        this.isLoading = false
      }
    },
    selectProjectFile(fileId: ProjectFileId) {
      this.activeProjectFileId = fileId
    },
    updateActiveProjectFileDraft(content: string) {
      this.projectFileDrafts[this.activeProjectFileId] = content
    },
    async saveActiveProjectFile() {
      const activeFile = this.activeProjectFile
      if (!activeFile) return

      this.isSaving = true
      try {
        const savedFile = await serviceBridge.saveProjectFile(
          activeFile.id,
          this.projectFileDrafts[activeFile.id] ?? activeFile.content,
        )
        this.projectFiles = this.projectFiles.map((file) => (file.id === savedFile.id ? savedFile : file))
        this.projectFileDrafts[savedFile.id] = savedFile.content
      } finally {
        this.isSaving = false
      }
    },
  },
})
