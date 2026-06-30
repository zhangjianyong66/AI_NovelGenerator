import type { ProjectFileId } from './types'

export interface GenerationBatchFormState {
  startChapter: number
  endChapter: number
  targetWords: number
  minimumWords: number
  autoEnrich: boolean
}

export interface ProjectWorkspaceState {
  activeChapterId?: string
  activeProjectFileId?: ProjectFileId
  generationSelectedJobId?: string
  generationBatchForm?: GenerationBatchFormState
}

type WorkspaceStateByProject = Record<string, ProjectWorkspaceState>

const storageKey = 'ai-novel-generator.workspaceState.v1'

export const defaultGenerationBatchForm: GenerationBatchFormState = {
  startChapter: 1,
  endChapter: 1,
  targetWords: 3000,
  minimumWords: 2000,
  autoEnrich: false,
}

const isObject = (value: unknown): value is Record<string, unknown> =>
  typeof value === 'object' && value !== null && !Array.isArray(value)

const readWorkspaceState = (): WorkspaceStateByProject => {
  try {
    const rawValue = window.localStorage.getItem(storageKey)
    if (!rawValue) return {}
    const parsedValue: unknown = JSON.parse(rawValue)
    if (!isObject(parsedValue)) return {}
    return parsedValue as WorkspaceStateByProject
  } catch {
    return {}
  }
}

const writeWorkspaceState = (state: WorkspaceStateByProject) => {
  try {
    window.localStorage.setItem(storageKey, JSON.stringify(state))
  } catch {
    // Workspace state is a convenience only; storage failures should not break the app.
  }
}

const optionalString = (value: unknown) => (typeof value === 'string' && value ? value : undefined)

const normalizeNonNegativeNumber = (value: unknown, fallback: number): number => {
  const numberValue = typeof value === 'number' ? value : Number(value)
  if (!Number.isFinite(numberValue)) return fallback
  return Math.max(0, numberValue)
}

export const normalizeGenerationBatchForm = (input: unknown): GenerationBatchFormState => {
  if (!isObject(input)) return { ...defaultGenerationBatchForm }
  return {
    startChapter: normalizeNonNegativeNumber(input.startChapter, defaultGenerationBatchForm.startChapter),
    endChapter: normalizeNonNegativeNumber(input.endChapter, defaultGenerationBatchForm.endChapter),
    targetWords: normalizeNonNegativeNumber(input.targetWords, defaultGenerationBatchForm.targetWords),
    minimumWords: normalizeNonNegativeNumber(input.minimumWords, defaultGenerationBatchForm.minimumWords),
    autoEnrich: typeof input.autoEnrich === 'boolean' ? input.autoEnrich : defaultGenerationBatchForm.autoEnrich,
  }
}

export const getProjectWorkspaceState = (projectId: string): ProjectWorkspaceState => {
  if (!projectId) return {}
  const state = readWorkspaceState()[projectId]
  if (!isObject(state)) return {}
  return {
    activeChapterId: optionalString(state.activeChapterId),
    activeProjectFileId: optionalString(state.activeProjectFileId) as ProjectFileId | undefined,
    generationSelectedJobId: optionalString(state.generationSelectedJobId),
    generationBatchForm: normalizeGenerationBatchForm(state.generationBatchForm),
  }
}

export const updateProjectWorkspaceState = (projectId: string, patch: ProjectWorkspaceState) => {
  if (!projectId) return
  const currentState = readWorkspaceState()
  currentState[projectId] = {
    ...currentState[projectId],
    ...patch,
  }
  writeWorkspaceState(currentState)
}
