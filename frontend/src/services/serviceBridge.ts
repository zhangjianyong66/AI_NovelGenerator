import { mockApi } from './mockApi'
import type {
  Chapter,
  ConfigTestResult,
  GenerationJob,
  GenerationJobCreateRequest,
  KnowledgeItem,
  ModelConfig,
  ModelSettings,
  OperationResult,
  PlotArcs,
  Project,
  ProjectConfig,
  ProjectFile,
  ProjectFileId,
  RoleCategory,
  RoleDetail,
  RoleSummary,
  WebDavConfig,
} from './types'

export type BackendMode = 'backend' | 'disconnected' | 'mock'

export interface BackendHealth {
  status: 'ok'
  mode: 'backend'
  service: string
}

export interface ServiceBridgeStatus {
  mode: BackendMode
  isLoading: boolean
  health: BackendHealth | null
  error: ServiceBridgeError | null
}

export interface ServiceBridgeError {
  message: string
  detail?: string
  status?: number
}

type RequestOptions = {
  allowMockFallback?: boolean
  method?: 'GET' | 'PUT' | 'POST' | 'DELETE'
  body?: unknown
}

const DEFAULT_API_BASE_URL = 'http://127.0.0.1:8000'

const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL ?? DEFAULT_API_BASE_URL).replace(/\/$/, '')

const status: ServiceBridgeStatus = {
  mode: 'disconnected',
  isLoading: false,
  health: null,
  error: null,
}

function normalizeError(error: unknown, fallbackMessage: string, statusCode?: number): ServiceBridgeError {
  if (error instanceof Error) {
    return {
      message: fallbackMessage,
      detail: error.message,
      status: statusCode,
    }
  }

  return {
    message: fallbackMessage,
    detail: String(error),
    status: statusCode,
  }
}

async function requestJson<T>(path: string, options: RequestOptions = {}): Promise<T> {
  status.isLoading = true
  status.error = null

  try {
    const response = await fetch(`${apiBaseUrl}${path}`, {
      method: options.method ?? 'GET',
      headers: options.body === undefined ? undefined : { 'Content-Type': 'application/json' },
      body: options.body === undefined ? undefined : JSON.stringify(options.body),
    })
    if (!response.ok) {
      throw normalizeError(new Error(response.statusText), '本地后端请求失败', response.status)
    }

    status.mode = 'backend'
    return (await response.json()) as T
  } catch (error) {
    const normalized =
      typeof error === 'object' && error !== null && 'message' in error
        ? (error as ServiceBridgeError)
        : normalizeError(error, '无法连接本地后端')

    status.error = normalized
    status.mode = options.allowMockFallback ? 'mock' : 'disconnected'
    throw normalized
  } finally {
    status.isLoading = false
  }
}

async function withMockFallback<T>(
  request: () => Promise<T>,
  fallback: () => Promise<T>,
): Promise<T> {
  try {
    return await request()
  } catch (error) {
    status.error = normalizeError(error, '本地后端不可用，已切换到 mock 数据')
    status.mode = 'mock'
    return fallback()
  }
}

export const serviceBridge = {
  getStatus(): ServiceBridgeStatus {
    return status
  },

  async checkHealth(): Promise<ServiceBridgeStatus> {
    try {
      status.health = await requestJson<BackendHealth>('/health')
    } catch {
      status.health = null
    }

    return status
  },

  async listProjects(): Promise<Project[]> {
    return withMockFallback(
      () => requestJson<Project[]>('/api/projects', { allowMockFallback: true }),
      () => mockApi.listProjects(),
    )
  },

  async listChapters(projectId: string): Promise<Chapter[]> {
    return withMockFallback(
      () => requestJson<Chapter[]>(`/api/projects/${encodeURIComponent(projectId)}/chapters`, {
        allowMockFallback: true,
      }),
      () => mockApi.listChapters(projectId),
    )
  },

  async saveChapter(chapterOrder: number, content: string): Promise<Chapter> {
    return requestJson<Chapter>(`/api/chapters/${chapterOrder}`, {
      method: 'PUT',
      body: { content },
    })
  },

  async listGenerationJobs(projectId: string): Promise<GenerationJob[]> {
    return withMockFallback(
      () => requestJson<GenerationJob[]>(`/api/projects/${encodeURIComponent(projectId)}/jobs`, {
        allowMockFallback: true,
      }),
      () => mockApi.listGenerationJobs(projectId),
    )
  },

  async createGenerationJob(request: GenerationJobCreateRequest): Promise<GenerationJob> {
    return requestJson<GenerationJob>('/api/generation-jobs', {
      method: 'POST',
      body: request,
    })
  },

  async getGenerationJob(jobId: string): Promise<GenerationJob> {
    return requestJson<GenerationJob>(`/api/generation-jobs/${encodeURIComponent(jobId)}`)
  },

  async getModelConfig(): Promise<ModelConfig> {
    return withMockFallback(
      () => requestJson<ModelConfig>('/api/config/model', { allowMockFallback: true }),
      () => mockApi.getModelConfig(),
    )
  },

  async getModelSettings(): Promise<ModelSettings> {
    return withMockFallback(
      () => requestJson<ModelSettings>('/api/model-settings', { allowMockFallback: true }),
      () => mockApi.getModelSettings(),
    )
  },

  async saveModelSettings(settings: ModelSettings): Promise<ModelSettings> {
    return requestJson<ModelSettings>('/api/model-settings', {
      method: 'PUT',
      body: settings,
    })
  },

  async testLlmConfig(configName: string): Promise<ConfigTestResult> {
    return withMockFallback(
      () =>
        requestJson<ConfigTestResult>('/api/model-settings/test-llm', {
          method: 'POST',
          body: { configName },
          allowMockFallback: true,
        }),
      () => mockApi.testLlmConfig(configName),
    )
  },

  async getProjectConfig(): Promise<ProjectConfig> {
    return withMockFallback(
      () => requestJson<ProjectConfig>('/api/project-config', { allowMockFallback: true }),
      () => mockApi.getProjectConfig(),
    )
  },

  async saveProjectConfig(config: ProjectConfig): Promise<ProjectConfig> {
    return requestJson<ProjectConfig>('/api/project-config', {
      method: 'PUT',
      body: config,
    })
  },

  async listProjectFiles(): Promise<ProjectFile[]> {
    return withMockFallback(
      () => requestJson<ProjectFile[]>('/api/project-files', { allowMockFallback: true }),
      () => mockApi.listProjectFiles(),
    )
  },

  async saveProjectFile(fileId: ProjectFileId, content: string): Promise<ProjectFile> {
    return requestJson<ProjectFile>(`/api/project-files/${fileId}`, {
      method: 'PUT',
      body: { content },
    })
  },

  async listKnowledgeItems(): Promise<KnowledgeItem[]> {
    return withMockFallback(
      () => requestJson<KnowledgeItem[]>('/api/knowledge', { allowMockFallback: true }),
      () => mockApi.listKnowledgeItems(),
    )
  },

  async importKnowledgeFile(filePath: string): Promise<OperationResult> {
    return requestJson<OperationResult>('/api/knowledge/import', {
      method: 'POST',
      body: { filePath },
    })
  },

  async clearVectorstore(): Promise<OperationResult> {
    return requestJson<OperationResult>('/api/knowledge/clear-vectorstore', {
      method: 'POST',
    })
  },

  async getPlotArcs(): Promise<PlotArcs> {
    return withMockFallback(
      () => requestJson<PlotArcs>('/api/knowledge/plot-arcs', { allowMockFallback: true }),
      () => mockApi.getPlotArcs(),
    )
  },

  async listRoles(): Promise<RoleCategory[]> {
    return withMockFallback(
      () => requestJson<RoleCategory[]>('/api/roles', { allowMockFallback: true }),
      () => mockApi.listRoles(),
    )
  },

  async getRole(category: string, roleName: string): Promise<RoleDetail> {
    return requestJson<RoleDetail>(
      `/api/roles/${encodeURIComponent(category)}/${encodeURIComponent(roleName)}`,
    )
  },

  async saveRole(category: string, roleName: string, content: string): Promise<RoleDetail> {
    return requestJson<RoleDetail>(
      `/api/roles/${encodeURIComponent(category)}/${encodeURIComponent(roleName)}`,
      {
        method: 'PUT',
        body: { content },
      },
    )
  },

  async importRole(category: string, filePath: string): Promise<RoleSummary> {
    return requestJson<RoleSummary>('/api/roles/import', {
      method: 'POST',
      body: { category, filePath },
    })
  },

  async getWebDavConfig(): Promise<WebDavConfig> {
    return withMockFallback(
      () => requestJson<WebDavConfig>('/api/webdav-config', { allowMockFallback: true }),
      () => mockApi.getWebDavConfig(),
    )
  },

  async saveWebDavConfig(config: WebDavConfig): Promise<WebDavConfig> {
    return requestJson<WebDavConfig>('/api/webdav-config', {
      method: 'PUT',
      body: config,
    })
  },

  async testWebDavConfig(config: WebDavConfig): Promise<OperationResult> {
    return requestJson<OperationResult>('/api/webdav/test', {
      method: 'POST',
      body: config,
    })
  },

  async backupWebDavConfig(): Promise<OperationResult> {
    return requestJson<OperationResult>('/api/webdav/backup', {
      method: 'POST',
    })
  },

  async restoreWebDavConfig(): Promise<OperationResult> {
    return requestJson<OperationResult>('/api/webdav/restore', {
      method: 'POST',
    })
  },
}
