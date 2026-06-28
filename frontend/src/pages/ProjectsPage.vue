<template>
  <section class="page">
    <PageHeader title="项目" subtitle="按小说项目进入工作台，并查看当前后端输出路径与小说参数。">
    </PageHeader>

    <StatusMessage v-if="!canWriteToBackend" type="warning" :message="writeUnavailableMessage" />

    <StatusMessage v-if="operationMessage" type="success" :message="operationMessage" />
    <StatusMessage v-if="operationError" type="error" :message="operationError" />

    <section v-if="projectConfig" class="panel">
      <div class="panel-body">
        <div class="config-summary">
          <div>
            <h3 class="panel-title">当前输出路径</h3>
            <p class="path-text">{{ projectConfig.outputPath || '未设置' }}</p>
          </div>
          <div class="summary-meta">
            <span>主题：{{ projectConfig.novelParams.topic || '未填写' }}</span>
            <span>类型：{{ projectConfig.novelParams.genre || '未填写' }}</span>
            <span>章节：{{ projectConfig.novelParams.numChapters }}</span>
            <span>每章字数：{{ projectConfig.novelParams.wordNumber }}</span>
          </div>
        </div>
      </div>
    </section>

    <div class="grid two">
      <FormSection title="新建项目" description="创建本地输出目录，并切换为当前项目。">
        <div class="project-form">
          <TextField v-model="createForm.outputPath" label="输出路径" placeholder="/tmp/my-novel" />
          <TextField v-model="createForm.topic" label="主题" placeholder="记忆交易港城" />
          <TextField v-model="createForm.genre" label="类型" placeholder="悬疑奇幻" />
          <div class="form-row">
            <TextField v-model="createForm.numChapters" label="章节数" type="number" min="0" />
            <TextField v-model="createForm.wordNumber" label="每章字数" type="number" min="0" />
          </div>
          <ActionBar align="end">
            <AppButton variant="primary" :disabled="isBusy || !canWriteToBackend" @click="createProject">
              新建项目
            </AppButton>
          </ActionBar>
        </div>
      </FormSection>

      <FormSection title="打开已有项目" description="选择已有输出目录，并记录到最近项目列表。">
        <div class="project-form">
          <TextField v-model="openOutputPath" label="输出路径" placeholder="/tmp/existing-novel" />
          <ActionBar align="end">
            <AppButton variant="primary" :disabled="isBusy || !canWriteToBackend" @click="openProject">
              打开项目
            </AppButton>
          </ActionBar>
        </div>
      </FormSection>
    </div>

    <div class="grid two">
      <article
        v-for="project in projects"
        :key="project.id"
        class="project-card panel"
        :class="{ active: project.id === activeProjectId }"
      >
        <div class="panel-body">
          <div class="project-heading">
            <div>
              <h3>{{ project.title }}</h3>
              <p>{{ project.genre }}</p>
            </div>
            <span class="status-pill" :class="{ neutral: project.status !== 'active' }">
              {{ statusLabel(project.status) }}
            </span>
          </div>
          <p class="summary">{{ project.summary }}</p>
          <div class="project-meta">
            <span>章节 {{ project.chaptersCompleted }}/{{ project.chaptersTotal }}</span>
            <span>更新 {{ project.updatedAt }}</span>
          </div>
          <ActionBar align="end">
            <AppButton
              size="sm"
              :disabled="isBusy || !canWriteToBackend || project.id === activeProjectId"
              @click="switchProject(project.id)"
            >
              切换
            </AppButton>
          </ActionBar>
        </div>
      </article>
    </div>
  </section>
</template>

<script setup lang="ts">
import { storeToRefs } from 'pinia'
import { computed, onMounted, ref } from 'vue'

import ActionBar from '@/components/ui/ActionBar.vue'
import AppButton from '@/components/ui/AppButton.vue'
import FormSection from '@/components/ui/FormSection.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import StatusMessage from '@/components/ui/StatusMessage.vue'
import TextField from '@/components/ui/TextField.vue'
import { serviceBridge, type ServiceBridgeStatus } from '@/services/serviceBridge'
import { useProjectsStore } from '@/stores/projects'
import type { ProjectConfig, ProjectStatus } from '@/services/types'

const projectsStore = useProjectsStore()
const { projects, activeProjectId } = storeToRefs(projectsStore)
const projectConfig = ref<ProjectConfig>()
const bridgeStatus = ref<ServiceBridgeStatus>({ ...serviceBridge.getStatus() })
const openOutputPath = ref('')
const operationMessage = ref('')
const operationError = ref('')
const createForm = ref({
  outputPath: '',
  topic: '',
  genre: '',
  numChapters: 0,
  wordNumber: 0,
})
const canWriteToBackend = computed(() => serviceBridge.canWrite(bridgeStatus.value))
const writeUnavailableMessage = computed(() => serviceBridge.getWriteUnavailableMessage(bridgeStatus.value))
const isBusy = computed(() => projectsStore.isLoading)

const syncBridgeStatus = () => {
  bridgeStatus.value = { ...serviceBridge.getStatus() }
}

onMounted(() => {
  void loadProjectsPage()
})

const loadProjectConfig = async () => {
  projectConfig.value = await serviceBridge.getProjectConfig()
  syncBridgeStatus()
}

const loadProjectsPage = async () => {
  await projectsStore.loadProjects(true)
  syncBridgeStatus()
  await loadProjectConfig()
}

const getErrorMessage = (error: unknown, fallback: string) => {
  if (error instanceof Error) return error.message
  if (typeof error === 'object' && error !== null && 'message' in error) {
    return String(error.message)
  }
  return fallback
}

const requireWritableBackend = () => {
  syncBridgeStatus()
  if (canWriteToBackend.value) return true
  operationError.value = writeUnavailableMessage.value
  return false
}

const createProject = async () => {
  operationMessage.value = ''
  operationError.value = ''
  if (!requireWritableBackend()) return

  try {
    await projectsStore.createProject({
      outputPath: createForm.value.outputPath,
      topic: createForm.value.topic,
      genre: createForm.value.genre,
      numChapters: Number(createForm.value.numChapters || 0),
      wordNumber: Number(createForm.value.wordNumber || 0),
    })
    await loadProjectConfig()
    operationMessage.value = '项目已创建并切换为当前项目'
  } catch (error) {
    operationError.value = getErrorMessage(error, '创建项目失败')
  } finally {
    syncBridgeStatus()
  }
}

const openProject = async () => {
  operationMessage.value = ''
  operationError.value = ''
  if (!requireWritableBackend()) return

  try {
    await projectsStore.switchProject({ outputPath: openOutputPath.value })
    await loadProjectConfig()
    operationMessage.value = '项目已打开并切换为当前项目'
  } catch (error) {
    operationError.value = getErrorMessage(error, '打开项目失败')
  } finally {
    syncBridgeStatus()
  }
}

const switchProject = async (projectId: string) => {
  operationMessage.value = ''
  operationError.value = ''
  if (!requireWritableBackend()) return

  try {
    await projectsStore.switchProject({ projectId })
    await loadProjectConfig()
    operationMessage.value = '项目已切换'
  } catch (error) {
    operationError.value = getErrorMessage(error, '切换项目失败')
  } finally {
    syncBridgeStatus()
  }
}

const statusLabel = (status: ProjectStatus) => {
  const labels: Record<ProjectStatus, string> = {
    active: '进行中',
    draft: '草案',
    archived: '归档',
  }
  return labels[status]
}
</script>

<style scoped>
.project-card {
  cursor: default;
  transition:
    border-color 0.16s ease,
    transform 0.16s ease;
}

.project-card.active {
  border-color: var(--color-primary);
}

.project-card:hover {
  transform: translateY(-2px);
}

.project-heading,
.project-meta {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 14px;
}

h3 {
  margin: 0;
  font-size: 18px;
}

.project-heading p,
.summary,
.project-meta {
  color: var(--color-text-muted);
}

.project-heading p {
  margin: 4px 0 0;
}

.summary {
  margin: 18px 0;
  line-height: 1.6;
}

.project-meta {
  border-top: 1px solid var(--color-border);
  padding-top: 12px;
  font-size: 13px;
}

.project-form {
  display: grid;
  gap: 14px;
}

.form-row {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.config-summary {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(320px, 0.8fr);
  gap: 16px;
  align-items: start;
}

.path-text {
  margin: 0;
  overflow-wrap: anywhere;
  color: var(--color-text-muted);
  line-height: 1.6;
}

.summary-meta {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px 12px;
  color: var(--color-text-muted);
  font-size: 13px;
}
</style>
