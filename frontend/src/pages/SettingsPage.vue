<template>
  <section class="page">
    <PageHeader title="设置" subtitle="项目输出路径、小说参数、模型、Embedding、阶段模型、代理和 WebDAV 配置。">
      <template #actions>
        <AppButton variant="primary" :disabled="isSaving || !canSave" @click="saveAll">
          <Save :size="16" />
          {{ isSaving ? '保存中' : '保存全部' }}
        </AppButton>
      </template>
    </PageHeader>

    <StatusMessage v-if="isSaving" type="loading" message="正在提交配置操作。" />
    <StatusMessage v-if="!canWriteToBackend" type="warning" :message="writeUnavailableMessage" />
    <StatusMessage type="success" :message="saveMessage" />
    <StatusMessage type="error" :message="errorMessage" />

    <Tabs v-model="activeTab" :tabs="tabs">
      <FormSection v-if="activeTab === 'project' && projectConfig" title="项目参数" description="这些字段会保存到当前 config.json 的项目参数区域。">
        <div class="form-grid two">
          <TextField v-model="projectConfig.outputPath" class="wide" label="输出路径" />
          <TextField v-model="projectConfig.novelParams.topic" label="主题" />
          <TextField v-model="projectConfig.novelParams.genre" label="类型" />
          <TextField
            :model-value="projectConfig.novelParams.numChapters"
            label="总章节数"
            min="0"
            type="number"
            @update:model-value="projectConfig.novelParams.numChapters = Number($event)"
          />
          <TextField
            :model-value="projectConfig.novelParams.wordNumber"
            label="每章字数"
            min="0"
            type="number"
            @update:model-value="projectConfig.novelParams.wordNumber = Number($event)"
          />
          <TextField v-model="projectConfig.novelParams.chapterNum" label="当前章节" />
          <TextField v-model="projectConfig.novelParams.charactersInvolved" label="涉及角色" />
          <TextField v-model="projectConfig.novelParams.keyItems" label="关键物品" />
          <TextField v-model="projectConfig.novelParams.sceneLocation" label="场景地点" />
          <TextField v-model="projectConfig.novelParams.timeConstraint" label="时间限制" />
          <TextAreaField v-model="projectConfig.novelParams.userGuidance" class="wide" label="用户指导" :rows="3" />
        </div>
      </FormSection>

      <FormSection v-if="activeTab === 'llm' && modelSettings" title="LLM 配置" description="管理多个 LLM 配置，并测试当前选中配置。">
        <template #actions>
          <AppButton variant="ghost" @click="addLlmConfig">新增</AppButton>
          <AppButton variant="ghost" :disabled="modelSettings.llmConfigs.length <= 1" @click="deleteSelectedLlmConfig">
            删除
          </AppButton>
          <AppButton variant="ghost" :disabled="isSaving || !canWriteToBackend" @click="testSelectedLlmConfig">测试 LLM</AppButton>
        </template>
        <div class="form-grid two">
          <SelectField
            v-model="modelSettings.selectedLlmConfig"
            class="wide"
            label="当前配置"
            :options="llmConfigOptions"
          />
          <template v-if="selectedLlmConfig">
            <TextField
              :model-value="selectedLlmConfig.name"
              label="配置名称"
              @update:model-value="renameSelectedLlmConfig"
            />
            <TextField v-model="selectedLlmConfig.interfaceFormat" label="接口格式" />
            <TextField v-model="selectedLlmConfig.baseUrl" label="Base URL" />
            <TextField v-model="selectedLlmConfig.modelName" label="模型" />
            <TextField
              v-model="selectedLlmConfig.apiKey"
              label="API Key"
              :placeholder="selectedLlmConfig.hasApiKey ? '已保存，留空则保留' : ''"
            />
            <TextField
              :model-value="selectedLlmConfig.temperature"
              label="Temperature"
              step="0.1"
              type="number"
              @update:model-value="selectedLlmConfig.temperature = Number($event)"
            />
            <TextField
              :model-value="selectedLlmConfig.maxTokens"
              label="Max Tokens"
              min="0"
              type="number"
              @update:model-value="selectedLlmConfig.maxTokens = Number($event)"
            />
            <TextField
              :model-value="selectedLlmConfig.timeout"
              label="Timeout"
              min="0"
              type="number"
              @update:model-value="selectedLlmConfig.timeout = Number($event)"
            />
          </template>
        </div>
      </FormSection>

      <FormSection v-if="activeTab === 'embedding' && modelSettings" title="Embedding" description="Embedding 配置影响知识库检索。切换真实模型后建议清理旧向量库。">
        <StatusMessage type="warning" message="切换真实 Embedding 模型后需要清理旧向量库，避免旧向量影响检索。" />
        <div class="form-grid two">
          <SelectField
            v-model="modelSettings.selectedEmbeddingConfig"
            class="wide"
            label="当前配置"
            :options="embeddingConfigOptions"
          />
          <template v-if="selectedEmbeddingConfig">
            <TextField
              :model-value="selectedEmbeddingConfig.name"
              label="配置名称"
              @update:model-value="renameSelectedEmbeddingConfig"
            />
            <TextField v-model="selectedEmbeddingConfig.interfaceFormat" label="接口格式" />
            <TextField v-model="selectedEmbeddingConfig.baseUrl" label="Base URL" />
            <TextField v-model="selectedEmbeddingConfig.modelName" label="模型" />
            <TextField
              v-model="selectedEmbeddingConfig.apiKey"
              label="API Key"
              :placeholder="selectedEmbeddingConfig.hasApiKey ? '已保存，留空则保留' : ''"
            />
            <TextField
              :model-value="selectedEmbeddingConfig.retrievalK"
              label="Retrieval K"
              min="0"
              type="number"
              @update:model-value="selectedEmbeddingConfig.retrievalK = Number($event)"
            />
          </template>
        </div>
      </FormSection>

      <FormSection v-if="activeTab === 'stage' && modelSettings" title="代理与阶段模型" description="代理设置会影响后续请求；阶段模型决定不同生成步骤使用哪个 LLM 配置。">
        <div class="form-grid two">
          <ToggleField v-model="modelSettings.proxySetting.enabled" class="wide" label="启用代理" />
          <TextField v-model="modelSettings.proxySetting.proxyUrl" label="代理地址" />
          <TextField v-model="modelSettings.proxySetting.proxyPort" label="代理端口" />
          <SelectField
            v-for="stage in stageOptions"
            :key="stage.key"
            v-model="modelSettings.stageModelSelection[stage.key]"
            :label="stage.label"
            :options="llmConfigOptions"
          />
        </div>
      </FormSection>

      <FormSection v-if="activeTab === 'webdav' && webDavConfig" title="WebDAV" description="用于备份和恢复 config.json。恢复会先在本地 backup/ 下创建备份。">
        <template #actions>
          <AppButton variant="ghost" :disabled="isSaving || !canWriteToBackend" @click="testWebDav">测试连接</AppButton>
          <AppButton variant="ghost" :disabled="isSaving || !canWriteToBackend" @click="backupWebDav">备份</AppButton>
        </template>
        <div class="form-grid three">
          <TextField v-model="webDavConfig.webdavUrl" label="WebDAV URL" />
          <TextField v-model="webDavConfig.username" label="用户名" />
          <TextField
            v-model="webDavConfig.password"
            label="密码"
            :placeholder="webDavConfig.hasPassword ? '已保存，留空则保留' : ''"
            type="password"
          />
        </div>
        <ConfirmPanel
          class="webdav-restore"
          title="从 WebDAV 恢复配置"
          description="本地配置会先备份再替换，请确认远程备份是你希望恢复的版本。"
          action-label="恢复"
          :disabled="isSaving || !canWriteToBackend"
          @confirm="restoreWebDav"
        />
      </FormSection>
    </Tabs>
  </section>
</template>

<script setup lang="ts">
import { Save } from '@lucide/vue'
import { computed, onMounted, ref } from 'vue'

import AppButton from '@/components/ui/AppButton.vue'
import ConfirmPanel from '@/components/ui/ConfirmPanel.vue'
import FormSection from '@/components/ui/FormSection.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import SelectField from '@/components/ui/SelectField.vue'
import StatusMessage from '@/components/ui/StatusMessage.vue'
import Tabs from '@/components/ui/Tabs.vue'
import TextAreaField from '@/components/ui/TextAreaField.vue'
import TextField from '@/components/ui/TextField.vue'
import ToggleField from '@/components/ui/ToggleField.vue'
import { serviceBridge, type ServiceBridgeStatus } from '@/services/serviceBridge'
import type { ModelSettings, ProjectConfig, StageModelSelection, WebDavConfig } from '@/services/types'

type SettingsTab = 'project' | 'llm' | 'embedding' | 'stage' | 'webdav'

const tabs: Array<{ id: SettingsTab; label: string }> = [
  { id: 'project', label: '项目参数' },
  { id: 'llm', label: 'LLM' },
  { id: 'embedding', label: 'Embedding' },
  { id: 'stage', label: '阶段模型/代理' },
  { id: 'webdav', label: 'WebDAV' },
]
const activeTab = ref<SettingsTab>('project')
const projectConfig = ref<ProjectConfig>()
const modelSettings = ref<ModelSettings>()
const webDavConfig = ref<WebDavConfig>()
const isSaving = ref(false)
const saveMessage = ref('')
const errorMessage = ref('')
const bridgeStatus = ref<ServiceBridgeStatus>({ ...serviceBridge.getStatus() })

const stageOptions: Array<{ key: keyof StageModelSelection; label: string }> = [
  { key: 'promptDraft', label: '提示词草稿' },
  { key: 'chapterOutline', label: '章节大纲' },
  { key: 'architecture', label: '小说设定' },
  { key: 'finalChapter', label: '章节定稿' },
  { key: 'consistencyReview', label: '一致性审校' },
]

const canWriteToBackend = computed(() => serviceBridge.canWrite(bridgeStatus.value))
const writeUnavailableMessage = computed(() => serviceBridge.getWriteUnavailableMessage(bridgeStatus.value))
const canSave = computed(() => Boolean(projectConfig.value && modelSettings.value && webDavConfig.value && canWriteToBackend.value))

const syncBridgeStatus = () => {
  bridgeStatus.value = { ...serviceBridge.getStatus() }
}

const selectedLlmConfig = computed(() =>
  modelSettings.value?.llmConfigs.find((item) => item.name === modelSettings.value?.selectedLlmConfig),
)

const selectedEmbeddingConfig = computed(() =>
  modelSettings.value?.embeddingConfigs.find((item) => item.name === modelSettings.value?.selectedEmbeddingConfig),
)

const llmConfigOptions = computed(() =>
  modelSettings.value?.llmConfigs.map((item) => ({ value: item.name, label: item.name })) ?? [],
)

const embeddingConfigOptions = computed(() =>
  modelSettings.value?.embeddingConfigs.map((item) => ({ value: item.name, label: item.name })) ?? [],
)

const setError = (error: unknown, fallback: string) => {
  errorMessage.value =
    error instanceof Error
      ? error.message
      : typeof error === 'object' && error !== null && 'message' in error
        ? String(error.message)
        : fallback
}

const loadSettings = async () => {
  const [loadedProjectConfig, loadedModelSettings, loadedWebDavConfig] = await Promise.all([
    serviceBridge.getProjectConfig(),
    serviceBridge.getModelSettings(),
    serviceBridge.getWebDavConfig(),
  ])
  projectConfig.value = loadedProjectConfig
  modelSettings.value = loadedModelSettings
  webDavConfig.value = loadedWebDavConfig
  syncBridgeStatus()
}

onMounted(async () => {
  await loadSettings()
})

const addLlmConfig = () => {
  if (!modelSettings.value) return
  const nextName = `新配置 ${modelSettings.value.llmConfigs.length + 1}`
  modelSettings.value.llmConfigs.push({
    name: nextName,
    apiKey: '',
    hasApiKey: false,
    baseUrl: '',
    modelName: '',
    temperature: 0.7,
    maxTokens: 4096,
    timeout: 600,
    interfaceFormat: 'OpenAI',
  })
  modelSettings.value.selectedLlmConfig = nextName
}

const deleteSelectedLlmConfig = () => {
  if (!modelSettings.value || modelSettings.value.llmConfigs.length <= 1) return
  const deletedName = modelSettings.value.selectedLlmConfig
  modelSettings.value.llmConfigs = modelSettings.value.llmConfigs.filter((item) => item.name !== deletedName)
  modelSettings.value.selectedLlmConfig = modelSettings.value.llmConfigs[0]?.name ?? ''
  syncStageSelection()
}

const renameSelectedLlmConfig = (nextName: string) => {
  if (!modelSettings.value || !selectedLlmConfig.value) return
  const previousName = selectedLlmConfig.value.name
  selectedLlmConfig.value.name = nextName
  modelSettings.value.selectedLlmConfig = nextName
  for (const stage of stageOptions) {
    if (modelSettings.value.stageModelSelection[stage.key] === previousName) {
      modelSettings.value.stageModelSelection[stage.key] = nextName
    }
  }
  syncStageSelection()
}

const renameSelectedEmbeddingConfig = (nextName: string) => {
  if (!modelSettings.value || !selectedEmbeddingConfig.value) return
  selectedEmbeddingConfig.value.name = nextName
  modelSettings.value.selectedEmbeddingConfig = nextName
}

const syncStageSelection = () => {
  if (!modelSettings.value) return
  const available = new Set(modelSettings.value.llmConfigs.map((item) => item.name))
  for (const stage of stageOptions) {
    if (!available.has(modelSettings.value.stageModelSelection[stage.key])) {
      modelSettings.value.stageModelSelection[stage.key] = modelSettings.value.selectedLlmConfig
    }
  }
}

const testSelectedLlmConfig = async () => {
  if (!modelSettings.value?.selectedLlmConfig) return
  if (!canWriteToBackend.value) {
    errorMessage.value = writeUnavailableMessage.value
    return
  }
  isSaving.value = true
  saveMessage.value = ''
  errorMessage.value = ''
  try {
    const result = await serviceBridge.testLlmConfig(modelSettings.value.selectedLlmConfig)
    saveMessage.value = result.success ? result.message : ''
    errorMessage.value = result.success ? '' : result.message
  } catch (error) {
    setError(error, '测试 LLM 失败')
  } finally {
    syncBridgeStatus()
    isSaving.value = false
  }
}

const saveAll = async () => {
  if (!projectConfig.value || !modelSettings.value || !webDavConfig.value) return
  if (!canWriteToBackend.value) {
    errorMessage.value = writeUnavailableMessage.value
    return
  }

  isSaving.value = true
  saveMessage.value = ''
  errorMessage.value = ''

  try {
    const [savedProjectConfig, savedModelSettings, savedWebDavConfig] = await Promise.all([
      serviceBridge.saveProjectConfig(projectConfig.value),
      serviceBridge.saveModelSettings(modelSettings.value),
      serviceBridge.saveWebDavConfig(webDavConfig.value),
    ])
    projectConfig.value = savedProjectConfig
    modelSettings.value = savedModelSettings
    webDavConfig.value = savedWebDavConfig
    saveMessage.value = '已保存'
  } catch (error) {
    setError(error, '保存失败')
  } finally {
    syncBridgeStatus()
    isSaving.value = false
  }
}

const runWebDavOperation = async (operation: () => Promise<{ success: boolean; message: string }>) => {
  if (!canWriteToBackend.value) {
    errorMessage.value = writeUnavailableMessage.value
    return
  }
  isSaving.value = true
  saveMessage.value = ''
  errorMessage.value = ''

  try {
    const result = await operation()
    saveMessage.value = result.message
  } catch (error) {
    setError(error, 'WebDAV 操作失败')
  } finally {
    syncBridgeStatus()
    isSaving.value = false
  }
}

const testWebDav = async () => {
  if (!webDavConfig.value) return
  await runWebDavOperation(async () => {
    const result = await serviceBridge.testWebDavConfig(webDavConfig.value!)
    webDavConfig.value = await serviceBridge.getWebDavConfig()
    return result
  })
}

const backupWebDav = async () => {
  await runWebDavOperation(() => serviceBridge.backupWebDavConfig())
}

const restoreWebDav = async () => {
  await runWebDavOperation(async () => {
    const result = await serviceBridge.restoreWebDavConfig()
    await loadSettings()
    return result
  })
}
</script>

<style scoped>
.form-grid {
  display: grid;
  gap: 12px;
}

.form-grid.two {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.form-grid.three {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.wide {
  grid-column: 1 / -1;
}

.webdav-restore {
  margin-top: 14px;
}
</style>
