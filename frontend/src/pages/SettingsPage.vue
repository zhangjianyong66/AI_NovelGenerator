<template>
  <section class="page">
    <div class="page-header">
      <div>
        <h2 class="page-title">设置</h2>
        <p class="page-subtitle">项目输出路径、小说参数、模型、Embedding 和代理配置。</p>
      </div>
      <button class="primary-button" :disabled="isSaving || !projectConfig || !modelSettings || !webDavConfig" type="button" @click="saveAll">
        <Save :size="16" />
        {{ isSaving ? '保存中' : '保存配置' }}
      </button>
    </div>

    <section v-if="projectConfig" class="panel">
      <div class="panel-body">
        <div class="section-heading">
          <h3 class="panel-title">项目与小说参数</h3>
          <span v-if="saveMessage" class="status-pill">{{ saveMessage }}</span>
          <span v-if="errorMessage" class="status-pill warning">{{ errorMessage }}</span>
        </div>
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
      </div>
    </section>

    <div v-if="modelSettings" class="grid three">
      <section class="panel">
        <div class="panel-body">
          <div class="section-heading">
            <h3 class="panel-title">LLM 配置</h3>
            <div class="button-row">
              <button class="ghost-button" type="button" @click="addLlmConfig">新增</button>
              <button class="ghost-button" :disabled="modelSettings.llmConfigs.length <= 1" type="button" @click="deleteSelectedLlmConfig">
                删除
              </button>
            </div>
          </div>
          <label>
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
            <button class="ghost-button test-button" type="button" @click="testSelectedLlmConfig">测试 LLM</button>
          </template>
        </div>
      </section>

      <section class="panel">
        <div class="panel-body">
          <h3 class="panel-title">Embedding</h3>
          <label>
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
            <label>API Key<input v-model.trim="selectedEmbeddingConfig.apiKey" :placeholder="selectedEmbeddingConfig.hasApiKey ? '已保存，留空则保留' : ''" /></label>
            <label>Retrieval K<input v-model.number="selectedEmbeddingConfig.retrievalK" min="0" type="number" /></label>
          </template>
          <p class="muted">切换真实 Embedding 模型后需要清理旧向量库。</p>
        </div>
      </section>

      <section class="panel">
        <div class="panel-body">
          <h3 class="panel-title">代理</h3>
          <label class="toggle"><input v-model="modelSettings.proxySetting.enabled" type="checkbox" /> 启用代理</label>
          <label>代理地址<input v-model.trim="modelSettings.proxySetting.proxyUrl" /></label>
          <label>代理端口<input v-model.trim="modelSettings.proxySetting.proxyPort" /></label>
          <h3 class="panel-title stage-title">阶段模型</h3>
          <label v-for="stage in stageOptions" :key="stage.key">
            {{ stage.label }}
            <select v-model="modelSettings.stageModelSelection[stage.key]">
              <option v-for="item in modelSettings.llmConfigs" :key="item.name" :value="item.name">{{ item.name }}</option>
            </select>
          </label>
        </div>
      </section>
    </div>

    <section v-if="webDavConfig" class="panel">
      <div class="panel-body">
        <div class="section-heading">
          <h3 class="panel-title">WebDAV</h3>
          <div class="button-row">
            <button class="ghost-button" :disabled="isSaving" type="button" @click="testWebDav">测试连接</button>
            <button class="ghost-button" :disabled="isSaving" type="button" @click="backupWebDav">备份</button>
            <button class="ghost-button" :disabled="isSaving" type="button" @click="restoreWebDav">恢复</button>
          </div>
        </div>
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
      </div>
    </section>
  </section>
</template>

<script setup lang="ts">
import { Save } from '@lucide/vue'
import { computed, onMounted, ref } from 'vue'

import { serviceBridge } from '@/services/serviceBridge'
import type { ModelSettings, ProjectConfig, StageModelSelection, WebDavConfig } from '@/services/types'

const projectConfig = ref<ProjectConfig>()
const modelSettings = ref<ModelSettings>()
const webDavConfig = ref<WebDavConfig>()
const isSaving = ref(false)
const saveMessage = ref('')
const errorMessage = ref('')
const testMessage = ref('')

const stageOptions: Array<{ key: keyof StageModelSelection; label: string }> = [
  { key: 'promptDraft', label: '提示词草稿' },
  { key: 'chapterOutline', label: '章节大纲' },
  { key: 'architecture', label: '小说设定' },
  { key: 'finalChapter', label: '章节定稿' },
  { key: 'consistencyReview', label: '一致性审校' },
]

const selectedLlmConfig = computed(() =>
  modelSettings.value?.llmConfigs.find((item) => item.name === modelSettings.value?.selectedLlmConfig),
)

const selectedEmbeddingConfig = computed(() =>
  modelSettings.value?.embeddingConfigs.find((item) => item.name === modelSettings.value?.selectedEmbeddingConfig),
)

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
  const result = await serviceBridge.testLlmConfig(modelSettings.value.selectedLlmConfig)
  testMessage.value = result.message
  errorMessage.value = result.success ? '' : result.message
  saveMessage.value = result.success ? result.message : ''
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
    const message =
      error instanceof Error
        ? error.message
        : typeof error === 'object' && error !== null && 'message' in error
          ? String(error.message)
          : '保存失败'
    errorMessage.value = message
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
    errorMessage.value =
      error instanceof Error
        ? error.message
        : typeof error === 'object' && error !== null && 'message' in error
          ? String(error.message)
          : 'WebDAV 操作失败'
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
  if (!window.confirm('确认从 WebDAV 恢复配置？本地配置会先备份再替换。')) return
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

.section-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
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

.primary-button:disabled {
  opacity: 0.65;
}

.button-row {
  display: flex;
  gap: 8px;
}

.ghost-button:disabled {
  opacity: 0.55;
}

.test-button {
  margin-top: 12px;
}

.stage-title {
  margin-top: 18px;
}
</style>
