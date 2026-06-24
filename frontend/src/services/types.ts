export type ProjectStatus = 'active' | 'draft' | 'archived'

export interface Project {
  id: string
  title: string
  genre: string
  status: ProjectStatus
  summary: string
  updatedAt: string
  chaptersTotal: number
  chaptersCompleted: number
}

export type ChapterStatus = 'planned' | 'drafting' | 'review' | 'final'

export interface Chapter {
  id: string
  projectId: string
  order: number
  title: string
  status: ChapterStatus
  words: number
  synopsis: string
  content: string
  viewpoint: string
  updatedAt: string
}

export type GenerationJobStatus = 'queued' | 'running' | 'paused' | 'done' | 'failed'

export interface GenerationJob {
  id: string
  projectId: string
  title: string
  stage: 'architecture' | 'directory' | 'draft' | 'finalization' | 'batch'
  status: GenerationJobStatus
  progress: number
  startedAt: string
  log: string[]
}

export interface ModelConfig {
  provider: string
  modelName: string
  temperature: number
  maxTokens: number
  embeddingProvider: string
  embeddingModel: string
  proxyEnabled: boolean
  proxyUrl: string
}

export type KnowledgeItemType = 'file' | 'role'

export interface KnowledgeItem {
  id: string
  type: KnowledgeItemType
  name: string
  description: string
  tags: string[]
  updatedAt: string
}
