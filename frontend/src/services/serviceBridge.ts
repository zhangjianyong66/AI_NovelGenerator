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
  ProjectCreateRequest,
  ProjectConfig,
  ProjectFile,
  ProjectFileId,
  ProjectSwitchRequest,
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

type GenerationJobUpdateMessage = {
  type: 'generationJobUpdated'
  job: GenerationJob
}

const DEFAULT_API_BASE_URL = 'http://127.0.0.1:8000'

const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL ?? DEFAULT_API_BASE_URL).replace(/\/$/, '')

const status: ServiceBridgeStatus = {
  mode: 'disconnected',
  isLoading: false,
  health: null,
  error: null,
}

const modeLabels: Record<BackendMode, string> = {
  backend: '本地后端已连接',
  disconnected: '本地后端未连接',
  mock: '离线预览',
}

const writeUnavailableMessages: Record<Exclude<BackendMode, 'backend'>, string> = {
  disconnected: '本地后端未连接，不能执行保存、导入或生成操作。',
  mock: '当前为离线预览数据，不能执行保存、导入或生成操作。',
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

function websocketUrl(path: string): string {
  const url = new URL(`${apiBaseUrl}${path}`)
  url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:'
  return url.toString()
}

function isGenerationJobUpdateMessage(payload: unknown): payload is GenerationJobUpdateMessage {
  if (typeof payload !== 'object' || payload === null) return false
  const message = payload as { type?: unknown; job?: unknown }
  if (message.type !== 'generationJobUpdated') return false
  const job = message.job as Partial<GenerationJob> | undefined
  return typeof job?.id === 'string' && typeof job.projectId === 'string' && typeof job.status === 'string'
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
      let message = '本地后端请求失败'
      try {
        const payload = (await response.json()) as { detail?: unknown; message?: unknown }
        if (typeof payload.detail === 'string' && payload.detail.trim()) {
          message = payload.detail
        } else if (typeof payload.message === 'string' && payload.message.trim()) {
          message = payload.message
        }
      } catch {
        // Keep the generic message when the backend did not return JSON.
      }
      throw normalizeError(new Error(response.statusText), message, response.status)
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

  getModeLabel(mode: BackendMode = status.mode): string {
    return modeLabels[mode]
  },

  canWrite(statusSnapshot: ServiceBridgeStatus = status): boolean {
    return statusSnapshot.mode === 'backend'
  },

  getWriteUnavailableMessage(statusSnapshot: ServiceBridgeStatus = status): string {
    if (statusSnapshot.mode === 'backend') return ''
    return writeUnavailableMessages[statusSnapshot.mode]
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

  async createProject(request: ProjectCreateRequest): Promise<Project> {
    return requestJson<Project>('/api/projects', {
      method: 'POST',
      body: request,
    })
  },

  async switchProject(request: ProjectSwitchRequest): Promise<Project> {
    return requestJson<Project>('/api/projects/switch', {
      method: 'POST',
      body: request,
    })
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

  async createChapter(chapterOrder: number): Promise<Chapter> {
    return requestJson<Chapter>(`/api/chapters/${chapterOrder}`, {
      method: 'POST',
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

  subscribeGenerationJobs(projectId: string, onJob: (job: GenerationJob) => void): () => void {
    let socket: WebSocket | null = null
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null
    let reconnectAttempts = 0
    let closedByCaller = false

    const clearReconnectTimer = () => {
      if (reconnectTimer !== null) {
        clearTimeout(reconnectTimer)
        reconnectTimer = null
      }
    }

    const connect = () => {
      clearReconnectTimer()
      if (closedByCaller) return
      socket = new WebSocket(
        websocketUrl(`/api/projects/${encodeURIComponent(projectId)}/generation-jobs/ws`),
      )
      socket.onopen = () => {
        status.mode = 'backend'
        status.error = null
        reconnectAttempts = 0
      }
      socket.onmessage = (event) => {
        try {
          const payload = JSON.parse(String(event.data)) as unknown
          if (isGenerationJobUpdateMessage(payload)) {
            onJob(payload.job)
          }
        } catch (error) {
          status.error = normalizeError(error, '解析生成任务实时状态失败')
        }
      }
      socket.onerror = () => {
        status.error = {
          message: '生成任务实时连接异常',
        }
      }
      socket.onclose = () => {
        socket = null
        if (closedByCaller) return
        reconnectAttempts += 1
        if (reconnectAttempts > 5) {
          status.error = {
            message: '生成任务实时连接已断开',
          }
          return
        }
        reconnectTimer = setTimeout(connect, Math.min(1000 * reconnectAttempts, 5000))
      }
    }

    connect()

    return () => {
      closedByCaller = true
      clearReconnectTimer()
      socket?.close()
      socket = null
    }
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
    return withMockFallback(
      () =>
        requestJson<RoleDetail>(
          `/api/roles/${encodeURIComponent(category)}/${encodeURIComponent(roleName)}`,
          { allowMockFallback: true },
        ),
      () => mockApi.getRole(category, roleName),
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
