<template>
  <section class="page">
    <PageHeader title="知识库" subtitle="导入并向量化知识文件、查看剧情要点，并维护当前项目角色库。" />

    <StatusMessage v-if="isBusy" type="loading" message="正在处理知识库操作。" />
    <StatusMessage v-if="!canWriteToBackend" type="warning" :message="writeUnavailableMessage" />
    <StatusMessage type="success" :message="message" />
    <StatusMessage type="error" :message="errorMessage" />

    <Tabs v-model="activeTab" :tabs="tabs">
      <div v-if="activeTab === 'files'" class="tab-stack">
        <FormSection title="知识文件" description="使用当前 Embedding 配置写入向量库，并保留导入文件记录。">
          <template #actions>
            <button
              class="primary-button"
              :disabled="isBusy || !importPath || !canWriteToBackend"
              type="button"
              @click="importKnowledgeFile"
            >
              <Upload :size="16" />
              导入资料
            </button>
          </template>
          <div class="tool-panel">
            <TextField v-model.trim="importPath" label="文件路径" placeholder="/path/to/knowledge.txt" />
          </div>
        </FormSection>

        <ConfirmPanel
          title="清理向量库"
          description="将删除当前输出目录下的 vectorstore 数据。切换 Embedding 模型后通常需要执行此操作。"
          action-label="清理"
          :disabled="isBusy || !canWriteToBackend"
          @confirm="clearVectorstore"
        />

        <FormSection title="文件列表">
          <StatusMessage v-if="files.length === 0" type="empty" message="当前没有可展示的知识文件。" />
          <KnowledgeFileList :files="files" />
        </FormSection>
      </div>

      <FormSection v-if="activeTab === 'plot'" title="剧情要点" description="读取当前输出目录的 plot_arcs.txt。">
        <LongTextEditor
          :model-value="plotArcs?.content ?? ''"
          title="plot_arcs.txt"
          readonly
          empty-message="当前输出目录尚未生成剧情要点。"
          min-height="430px"
        />
        <p v-if="plotArcs" class="muted">{{ plotArcs.wordCount }} 字</p>
      </FormSection>

      <FormSection v-if="activeTab === 'roles'" title="角色库" description="维护角色文本，并可把选中角色写入章节参数。">
        <template #actions>
          <button
            class="ghost-button"
            :disabled="isBusy || selectedRoleIds.length === 0 || !canWriteToBackend"
            type="button"
            @click="applySelectedRoles"
          >
            写入章节参数
          </button>
        </template>
        <div class="role-import">
          <TextField v-model.trim="roleImportCategory" label="分类" />
          <TextField v-model.trim="roleImportPath" label="角色文件路径" placeholder="/path/to/role.txt" />
          <button
            class="ghost-button role-import__button"
            :disabled="!roleImportCategory || !roleImportPath || !canWriteToBackend"
            type="button"
            @click="importRole"
          >
            导入
          </button>
        </div>
        <RoleLibraryEditor
          v-model:role-content="roleContent"
          v-model:selected-role-ids="selectedRoleIds"
          :role-categories="roleCategories"
          :active-role="activeRole"
          :readonly="!canWriteToBackend"
          @load-role="loadRole"
          @save-role="saveRole"
        />
      </FormSection>
    </Tabs>
  </section>
</template>

<script setup lang="ts">
import { Upload } from '@lucide/vue'
import { computed, onMounted, ref } from 'vue'

import ConfirmPanel from '@/components/ui/ConfirmPanel.vue'
import FormSection from '@/components/ui/FormSection.vue'
import LongTextEditor from '@/components/ui/LongTextEditor.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import StatusMessage from '@/components/ui/StatusMessage.vue'
import Tabs from '@/components/ui/Tabs.vue'
import TextField from '@/components/ui/TextField.vue'
import { KnowledgeFileList, RoleLibraryEditor } from '@/features/knowledge'
import { serviceBridge, type ServiceBridgeStatus } from '@/services/serviceBridge'
import type { KnowledgeItem, PlotArcs, RoleCategory, RoleDetail } from '@/services/types'

type KnowledgeTab = 'files' | 'plot' | 'roles'

const tabs: Array<{ id: KnowledgeTab; label: string }> = [
  { id: 'files', label: '知识文件' },
  { id: 'plot', label: '剧情要点' },
  { id: 'roles', label: '角色库' },
]
const activeTab = ref<KnowledgeTab>('files')
const items = ref<KnowledgeItem[]>([])
const plotArcs = ref<PlotArcs>()
const roleCategories = ref<RoleCategory[]>([])
const activeRole = ref<RoleDetail>()
const roleContent = ref('')
const roleImportCategory = ref('默认')
const roleImportPath = ref('')
const selectedRoleIds = ref<string[]>([])
const importPath = ref('')
const message = ref('')
const errorMessage = ref('')
const isBusy = ref(false)
const bridgeStatus = ref<ServiceBridgeStatus>({ ...serviceBridge.getStatus() })
const files = computed(() => items.value.filter((item) => item.type === 'file'))
const canWriteToBackend = computed(() => serviceBridge.canWrite(bridgeStatus.value))
const writeUnavailableMessage = computed(() => serviceBridge.getWriteUnavailableMessage(bridgeStatus.value))

const syncBridgeStatus = () => {
  bridgeStatus.value = { ...serviceBridge.getStatus() }
}

onMounted(async () => {
  await Promise.all([loadKnowledgeItems(), loadPlotArcs(), loadRoles()])
  syncBridgeStatus()
})

const setError = (error: unknown, fallback: string) => {
  errorMessage.value =
    error instanceof Error
      ? error.message
      : typeof error === 'object' && error !== null && 'message' in error
        ? String(error.message)
        : fallback
}

const runOperation = async (operation: () => Promise<void>, fallback: string) => {
  if (!canWriteToBackend.value) {
    message.value = ''
    errorMessage.value = writeUnavailableMessage.value
    return
  }
  isBusy.value = true
  message.value = ''
  errorMessage.value = ''
  try {
    await operation()
  } catch (error) {
    setError(error, fallback)
  } finally {
    syncBridgeStatus()
    isBusy.value = false
  }
}

const loadKnowledgeItems = async () => {
  items.value = await serviceBridge.listKnowledgeItems()
  syncBridgeStatus()
}

const loadPlotArcs = async () => {
  plotArcs.value = await serviceBridge.getPlotArcs()
  syncBridgeStatus()
}

const loadRoles = async () => {
  roleCategories.value = await serviceBridge.listRoles()
  syncBridgeStatus()
}

const importKnowledgeFile = async () => {
  if (!importPath.value) return
  await runOperation(async () => {
    const result = await serviceBridge.importKnowledgeFile(importPath.value)
    message.value = result.message
    await loadKnowledgeItems()
  }, '导入失败')
}

const clearVectorstore = async () => {
  await runOperation(async () => {
    const result = await serviceBridge.clearVectorstore()
    message.value = result.message
  }, '清理失败')
}

const loadRole = async (category: string, roleName: string) => {
  activeRole.value = await serviceBridge.getRole(category, roleName)
  syncBridgeStatus()
  roleContent.value = activeRole.value.content
}

const saveRole = async () => {
  if (!activeRole.value) return
  await runOperation(async () => {
    const savedRole = await serviceBridge.saveRole(activeRole.value!.category, activeRole.value!.name, roleContent.value)
    activeRole.value = savedRole
    roleContent.value = savedRole.content
    message.value = '角色已保存'
    await loadRoles()
  }, '保存角色失败')
}

const importRole = async () => {
  await runOperation(async () => {
    const importedRole = await serviceBridge.importRole(roleImportCategory.value, roleImportPath.value)
    message.value = `已导入 ${importedRole.name}`
    roleImportPath.value = ''
    await loadRoles()
  }, '导入角色失败')
}

const applySelectedRoles = async () => {
  await runOperation(async () => {
    const selectedNames = roleCategories.value
      .flatMap((category) => category.roles)
      .filter((role) => selectedRoleIds.value.includes(role.id))
      .map((role) => role.name)
    const projectConfig = await serviceBridge.getProjectConfig()
    projectConfig.novelParams.charactersInvolved = selectedNames.join(',')
    await serviceBridge.saveProjectConfig(projectConfig)
    message.value = '已写入涉及角色'
  }, '写入章节参数失败')
}
</script>

<style scoped>
.tab-stack {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.tool-panel {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: 12px;
}

.knowledge-list :deep(.knowledge-item) {
  border-top: 1px solid var(--color-border);
  padding: 14px 0;
}

.knowledge-list :deep(.knowledge-item:first-of-type) {
  border-top: 0;
  padding-top: 0;
}

.knowledge-list :deep(h4),
.role-layout :deep(h4) {
  margin: 0 0 6px;
  font-size: 16px;
}

.knowledge-list :deep(p) {
  margin: 0 0 10px;
  color: var(--color-text-muted);
  line-height: 1.6;
}

.role-import,
.role-layout,
.role-row {
  display: flex;
  gap: 10px;
}

.role-import {
  margin-bottom: 14px;
  align-items: end;
}

.role-import :deep(.field) {
  flex: 1;
}

.role-import__button {
  margin-bottom: 0;
}

:deep(.role-layout) {
  align-items: stretch;
}

:deep(.role-list) {
  width: 320px;
  border-right: 1px solid var(--color-border);
  padding-right: 12px;
}

:deep(.role-category h4) {
  margin: 0 0 8px;
}

:deep(.role-row) {
  align-items: center;
  margin-top: 8px;
}

:deep(.role-row button) {
  display: flex;
  flex: 1;
  align-items: center;
  justify-content: space-between;
  min-height: 34px;
  border-radius: 6px;
  padding: 0 8px;
  background: var(--color-surface-muted);
  color: var(--color-text);
}

:deep(.role-row small) {
  color: var(--color-text-muted);
}

:deep(.role-editor) {
  flex: 1;
  min-width: 0;
}
</style>
