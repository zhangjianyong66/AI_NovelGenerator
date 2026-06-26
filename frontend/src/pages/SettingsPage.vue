<template>
  <section class="page">
    <PageHeader title="设置" subtitle="项目输出路径、小说参数、模型、Embedding、阶段模型、代理和 WebDAV 配置。">
      <template #actions>
        <button class="primary-button" :disabled="isSaving || !canSave" type="button" @click="saveAll">
          <Save :size="16" />
          {{ isSaving ? '保存中' : '保存全部' }}
        </button>
      </template>
    </PageHeader>

    <StatusMessage v-if="isSaving" type="loading" message="正在提交配置操作。" />
    <StatusMessage type="success" :message="saveMessage" />
    <StatusMessage type="error" :message="errorMessage" />

    <Tabs v-model="activeTab" :tabs="tabs">
      <FormSection v-if="activeTab === 'project' && projectConfig" title="项目参数" description="这些字段会保存到当前 config.json 的项目参数区域。">
        <div class="form-grid two">
          <label class="wide">输出路径<input v-model.trim="projectConfig.outputPath" /></label>
          <label>主题<input v-model.trim="projectConfig.novelParams.topic" /></label>
          <label>类型<input v-model.trim="projectConfig.novelParams.genre" /></label>
          <label>总章节数<input v-model.number="projectConfig.novelParams.numChapters" min="0" type="number" /></label>
          <label>每章字数<input v-model.number="projectConfig.novelParams.wordNumber" min="0" type="number" /></label>
          <label>当前章节<input v-model.trim="projectConfig.novelParams.chapterNum" /></label>
          <label>涉及角色<input v-model.trim="projectConfig.novelParams.charactersInvolved" /></label>
          <label>关键物品<input v-model.trim="projectConfig.novelParams.keyItems" /></label>
          <label>场景地点<input v-model.trim="projectConfig.novelParams.sceneLocation" /></label>
          <label>时间限制<input v-model.trim="projectConfig.novelParams.timeConstraint" /></label>
          <label class="wide">用户指导<textarea v-model.trim="projectConfig.novelParams.userGuidance" rows="3" /></label>
        </div>
      </FormSection>

      <FormSection v-if="activeTab === 'llm' && modelSettings" title="LLM 配置" description="管理多个 LLM 配置，并测试当前选中配置。">
        <template #actions>
          <button class="ghost-button" type="button" @click="addLlmConfig">新增</button>
          <button class="ghost-button" :disabled="modelSettings.llmConfigs.length <= 1" type="button" @click="deleteSelectedLlmConfig">
            删除
          </button>
          <button class="ghost-button" type="button" @click="testSelectedLlmConfig">测试 LLM</button>
        </template>
        <div class="form-grid two">
          <label class="wide">
            当前配置
            <select v-model="modelSettings.selectedLlmConfig">
              <option v-for="item in modelSettings.llmConfigs" :key="item.name" :value="item.name">{{ item.name }}</option>
            </select>
          </label>
          <template v-if="selectedLlmConfig">
            <label>配置名称<input v-model.trim="selectedLlmConfig.name" @change="syncStageSelection" /></label>
            <label>接口格式<input v-model.trim="selectedLlmConfig.interfaceFormat" /></label>
            <label>Base URL<input v-model.trim="selectedLlmConfig.baseUrl" /></label>
            <label>模型<input v-model.trim="selectedLlmConfig.modelName" /></label>
            <label>
              API Key
              <input v-model.trim="selectedLlmConfig.apiKey" :placeholder="selectedLlmConfig.hasApiKey ? '已保存，留空则保留' : ''" />
            </label>
            <label>Temperature<input v-model.number="selectedLlmConfig.temperature" type="number" step="0.1" /></label>
            <label>Max Tokens<input v-model.number="selectedLlmConfig.maxTokens" min="0" type="number" /></label>
            <label>Timeout<input v-model.number="selectedLlmConfig.timeout" min="0" type="number" /></label>
          </template>
        </div>
      </FormSection>

      <FormSection v-if="activeTab === 'embedding' && modelSettings" title="Embedding" description="Embedding 配置影响知识库检索。切换真实模型后建议清理旧向量库。">
        <StatusMessage type="warning" message="切换真实 Embedding 模型后需要清理旧向量库，避免旧向量影响检索。" />
        <div class="form-grid two">
          <label class="wide">
            当前配置
            <select v-model="modelSettings.selectedEmbeddingConfig">
              <option v-for="item in modelSettings.embeddingConfigs" :key="item.name" :value="item.name">{{ item.name }}</option>
            </select>
          </label>
          <template v-if="selectedEmbeddingConfig">
            <label>配置名称<input v-model.trim="selectedEmbeddingConfig.name" /></label>
            <label>接口格式<input v-model.trim="selectedEmbeddingConfig.interfaceFormat" /></label>
            <label>Base URL<input v-model.trim="selectedEmbeddingConfig.baseUrl" /></label>
            <label>模型<input v-model.trim="selectedEmbeddingConfig.modelName" /></label>
            <label>
              API Key
              <input v-model.trim="selectedEmbeddingConfig.apiKey" :placeholder="selectedEmbeddingConfig.hasApiKey ? '已保存，留空则保留' : ''" />
            </label>
            <label>Retrieval K<input v-model.number="selectedEmbeddingConfig.retrievalK" min="0" type="number" /></label>
          </template>
        </div>
      </FormSection>

      <FormSection v-if="activeTab === 'stage' && modelSettings" title="代理与阶段模型" description="代理设置会影响后续请求；阶段模型决定不同生成步骤使用哪个 LLM 配置。">
        <div class="form-grid two">
          <label class="toggle wide"><input v-model="modelSettings.proxySetting.enabled" type="checkbox" /> 启用代理</label>
          <label>代理地址<input v-model.trim="modelSettings.proxySetting.proxyUrl" /></label>
          <label>代理端口<input v-model.trim="modelSettings.proxySetting.proxyPort" /></label>
          <label v-for="stage in stageOptions" :key="stage.key">
            {{ stage.label }}
            <select v-model="modelSettings.stageModelSelection[stage.key]">
              <option v-for="item in modelSettings.llmConfigs" :key="item.name" :value="item.name">{{ item.name }}</option>
            </select>
          </label>
        </div>
      </FormSection>

      <FormSection v-if="activeTab === 'webdav' && webDavConfig" title="WebDAV" description="用于备份和恢复 config.json。恢复会先在本地 backup/ 下创建备份。">
        <template #actions>
          <button class="ghost-button" :disabled="isSaving" type="button" @click="testWebDav">测试连接</button>
          <button class="ghost-button" :disabled="isSaving" type="button" @click="backupWebDav">备份</button>
        </template>
        <div class="form-grid three">
          <label>WebDAV URL<input v-model.trim="webDavConfig.webdavUrl" /></label>
          <label>用户名<input v-model.trim="webDavConfig.username" /></label>
          <label>
            密码
            <input
              v-model.trim="webDavConfig.password"
              :placeholder="webDavConfig.hasPassword ? '已保存，留空则保留' : ''"
              type="password"
            />
          </label>
        </div>
        <ConfirmPanel
          class="webdav-restore"
          title="从 WebDAV 恢复配置"
          description="本地配置会先备份再替换，请确认远程备份是你希望恢复的版本。"
          action-label="恢复"
          :disabled="isSaving"
          @confirm="restoreWebDav"
        />
      </FormSection>
    </Tabs>
  </section>
</template>

<script setup lang="ts">
import { Save } from '@lucide/vue'
import { computed, onMounted, ref } from 'vue'

import ConfirmPanel from '@/components/ui/ConfirmPanel.vue'
import FormSection from '@/components/ui/FormSection.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import StatusMessage from '@/components/ui/StatusMessage.vue'
import Tabs from '@/components/ui/Tabs.vue'
import { serviceBridge } from '@/services/serviceBridge'
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

const stageOptions: Array<{ key: keyof StageModelSelection; label: string }> = [
  { key: 'promptDraft', label: '提示词草稿' },
  { key: 'chapterOutline', label: '章节大纲' },
  { key: 'architecture', label: '小说设定' },
  { key: 'finalChapter', label: '章节定稿' },
  { key: 'consistencyReview', label: '一致性审校' },
]

const canSave = computed(() => Boolean(projectConfig.value && modelSettings.value && webDavConfig.value))

const selectedLlmConfig = computed(() =>
  modelSettings.value?.llmConfigs.find((item) => item.name === modelSettings.value?.selectedLlmConfig),
)

const selectedEmbeddingConfig = computed(() =>
  modelSettings.value?.embeddingConfigs.find((item) => item.name === modelSettings.value?.selectedEmbeddingConfig),
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
    isSaving.value = false
  }
}

const saveAll = async () => {
  if (!projectConfig.value || !modelSettings.value || !webDavConfig.value) return

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
    isSaving.value = false
  }
}

const runWebDavOperation = async (operation: () => Promise<{ success: boolean; message: string }>) => {
  isSaving.value = true
  saveMessage.value = ''
  errorMessage.value = ''

  try {
    const result = await operation()
    saveMessage.value = result.message
  } catch (error) {
    setError(error, 'WebDAV 操作失败')
  } finally {
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
label {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-top: 12px;
  color: var(--color-text-muted);
  font-size: 13px;
}

input {
  min-height: 36px;
}

input,
textarea,
select {
  border: 1px solid var(--color-border);
  border-radius: 6px;
  padding: 8px 10px;
  color: var(--color-text);
}

textarea {
  resize: vertical;
}

.toggle {
  flex-direction: row;
  align-items: center;
}

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
