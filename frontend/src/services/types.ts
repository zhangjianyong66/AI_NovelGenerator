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
export type GenerationStage = 'architecture' | 'directory' | 'draft' | 'finalization' | 'batch' | 'consistency'

export interface GenerationJob {
  id: string
  projectId: string
  title: string
  stage: GenerationStage
  status: GenerationJobStatus
  progress: number
  startedAt: string
  log: string[]
  error?: string | null
}

export interface GenerationJobCreateRequest {
  projectId: string
  stage: GenerationStage
  chapterNumber?: number
  startChapter?: number
  endChapter?: number
  targetWords?: number
  minimumWords?: number
  autoEnrich?: boolean
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

export interface LlmConfigItem {
  name: string
  apiKey: string
  hasApiKey: boolean
  baseUrl: string
  modelName: string
  temperature: number
  maxTokens: number
  timeout: number
  interfaceFormat: string
}

export interface EmbeddingConfigItem {
  name: string
  apiKey: string
  hasApiKey: boolean
  baseUrl: string
  modelName: string
  retrievalK: number
  interfaceFormat: string
}

export interface ProxySetting {
  proxyUrl: string
  proxyPort: string
  enabled: boolean
}

export interface StageModelSelection {
  promptDraft: string
  chapterOutline: string
  architecture: string
  finalChapter: string
  consistencyReview: string
}

export interface ModelSettings {
  selectedLlmConfig: string
  selectedEmbeddingConfig: string
  llmConfigs: LlmConfigItem[]
  embeddingConfigs: EmbeddingConfigItem[]
  proxySetting: ProxySetting
  stageModelSelection: StageModelSelection
}

export interface ConfigTestResult {
  success: boolean
  message: string
}

export interface OperationResult {
  success: boolean
  message: string
}

export interface PlotArcs {
  exists: boolean
  content: string
  wordCount: number
}

export interface NovelParams {
  topic: string
  genre: string
  numChapters: number
  wordNumber: number
  chapterNum: string
  userGuidance: string
  charactersInvolved: string
  keyItems: string
  sceneLocation: string
  timeConstraint: string
}

export interface ProjectConfig {
  outputPath: string
  novelParams: NovelParams
}

export type ProjectFileId = 'novelSetting' | 'novelDirectory' | 'characterState' | 'globalSummary'

export interface ProjectFile {
  id: ProjectFileId
  label: string
  filename: string
  content: string
  wordCount: number
  exists: boolean
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

export interface RoleSummary {
  id: string
  category: string
  name: string
  filename: string
  wordCount: number
}

export interface RoleCategory {
  name: string
  roles: RoleSummary[]
}

export interface RoleDetail extends RoleSummary {
  content: string
}

export interface WebDavConfig {
  webdavUrl: string
  username: string
  password: string
  hasPassword: boolean
}
