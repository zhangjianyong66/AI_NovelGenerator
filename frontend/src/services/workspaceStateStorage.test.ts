import {
  defaultGenerationBatchForm,
  getProjectWorkspaceState,
  normalizeGenerationBatchForm,
  updateProjectWorkspaceState,
} from './workspaceStateStorage'

const assertEqual = <T>(actual: T, expected: T) => {
  if (actual !== expected) {
    throw new Error(`Expected ${String(expected)}, got ${String(actual)}`)
  }
}

const testWorkspaceStateStorageContract = () => {
  window.localStorage.removeItem('ai-novel-generator.workspaceState.v1')

  updateProjectWorkspaceState('project-a', {
    activeChapterId: 'chapter-3',
    activeProjectFileId: 'novelDirectory',
    generationSelectedJobId: 'job-2',
    generationBatchForm: {
      startChapter: 2,
      endChapter: 6,
      targetWords: 4200,
      minimumWords: 3000,
      autoEnrich: true,
    },
  })

  const projectAState = getProjectWorkspaceState('project-a')
  const projectBState = getProjectWorkspaceState('project-b')

  assertEqual(projectAState.activeChapterId, 'chapter-3')
  assertEqual(projectAState.activeProjectFileId, 'novelDirectory')
  assertEqual(projectAState.generationSelectedJobId, 'job-2')
  assertEqual(projectAState.generationBatchForm?.startChapter, 2)
  assertEqual(projectAState.generationBatchForm?.autoEnrich, true)
  assertEqual(projectBState.activeChapterId, undefined)

  window.localStorage.setItem('ai-novel-generator.workspaceState.v1', '{bad json')
  const brokenState = getProjectWorkspaceState('project-a')
  assertEqual(brokenState.activeChapterId, undefined)

  const normalized = normalizeGenerationBatchForm({
    startChapter: 'x',
    endChapter: 8,
    targetWords: -1,
    minimumWords: 1800,
    autoEnrich: true,
  })

  assertEqual(normalized.startChapter, defaultGenerationBatchForm.startChapter)
  assertEqual(normalized.endChapter, 8)
  assertEqual(normalized.targetWords, 0)
  assertEqual(normalized.minimumWords, 1800)
  assertEqual(normalized.autoEnrich, true)
}

void testWorkspaceStateStorageContract
