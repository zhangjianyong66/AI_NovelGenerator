<template>
  <section class="page">
    <PageHeader title="知识库" subtitle="导入知识文件、查看剧情要点，并维护当前项目角色库。" />

    <StatusMessage v-if="isBusy" type="loading" message="正在处理知识库操作。" />
    <StatusMessage type="success" :message="message" />
    <StatusMessage type="error" :message="errorMessage" />

    <Tabs v-model="activeTab" :tabs="tabs">
      <div v-if="activeTab === 'files'" class="tab-stack">
        <FormSection title="知识文件" description="导入资料到当前输出目录的向量库，并查看已知知识文件。">
          <template #actions>
            <button class="primary-button" :disabled="isBusy || !importPath" type="button" @click="importKnowledgeFile">
              <Upload :size="16" />
              导入资料
            </button>
          </template>
          <div class="tool-panel">
            <label>
              文件路径
              <input v-model.trim="importPath" placeholder="/path/to/knowledge.txt" />
            </label>
          </div>
        </FormSection>

        <ConfirmPanel
          title="清理向量库"
          description="将删除当前输出目录下的 vectorstore 数据。切换 Embedding 模型后通常需要执行此操作。"
          action-label="清理"
          :disabled="isBusy"
          @confirm="clearVectorstore"
        />

        <FormSection title="文件列表">
          <StatusMessage v-if="files.length === 0" type="empty" message="当前没有可展示的知识文件。" />
          <article v-for="item in files" :key="item.id" class="knowledge-item">
            <h4>{{ item.name }}</h4>
            <p>{{ item.description }}</p>
            <div class="tag-row">
              <span v-for="tag in item.tags" :key="tag" class="tag">{{ tag }}</span>
            </div>
          </article>
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
          <button class="ghost-button" type="button" @click="applySelectedRoles">写入章节参数</button>
        </template>
        <div class="role-import">
          <input v-model.trim="roleImportCategory" placeholder="分类" />
          <input v-model.trim="roleImportPath" placeholder="/path/to/role.txt" />
          <button class="ghost-button" :disabled="!roleImportCategory || !roleImportPath" type="button" @click="importRole">
            导入
          </button>
        </div>
        <div class="role-layout">
          <div class="role-list">
            <StatusMessage v-if="roleCategories.length === 0" type="empty" message="当前没有角色库文件。" />
            <div v-for="category in roleCategories" :key="category.name" class="role-category">
              <h4>{{ category.name }}</h4>
              <label v-for="role in category.roles" :key="role.id" class="role-row">
                <input v-model="selectedRoleIds" :value="role.id" type="checkbox" />
                <button type="button" @click="loadRole(role.category, role.name)">
                  {{ role.name }}
                  <small>{{ role.wordCount }} 字</small>
                </button>
              </label>
            </div>
          </div>
          <div class="role-editor">
            <LongTextEditor
              v-model="roleContent"
              :title="activeRole?.name ?? '未选择角色'"
              :disabled="!activeRole"
              empty-message="请选择一个角色进行查看或编辑。"
              min-height="300px"
            >
              <template #actions>
                <button class="primary-button" :disabled="!activeRole" type="button" @click="saveRole">保存角色</button>
              </template>
            </LongTextEditor>
          </div>
        </div>
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
import { serviceBridge } from '@/services/serviceBridge'
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
const files = computed(() => items.value.filter((item) => item.type === 'file'))

onMounted(async () => {
  await Promise.all([loadKnowledgeItems(), loadPlotArcs(), loadRoles()])
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
  isBusy.value = true
  message.value = ''
  errorMessage.value = ''
  try {
    await operation()
  } catch (error) {
    setError(error, fallback)
  } finally {
    isBusy.value = false
  }
}

const loadKnowledgeItems = async () => {
  items.value = await serviceBridge.listKnowledgeItems()
}

const loadPlotArcs = async () => {
  plotArcs.value = await serviceBridge.getPlotArcs()
}

const loadRoles = async () => {
  roleCategories.value = await serviceBridge.listRoles()
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

label {
  display: flex;
  flex-direction: column;
  gap: 6px;
  color: var(--color-text-muted);
  font-size: 13px;
}

input {
  min-height: 36px;
  border: 1px solid var(--color-border);
  border-radius: 6px;
  padding: 0 10px;
  color: var(--color-text);
}

.knowledge-item {
  border-top: 1px solid var(--color-border);
  padding: 14px 0;
}

.knowledge-item:first-of-type {
  border-top: 0;
  padding-top: 0;
}

h4 {
  margin: 0 0 6px;
  font-size: 16px;
}

p {
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
}

.role-import input {
  flex: 1;
}

.role-layout {
  align-items: stretch;
}

.role-list {
  width: 320px;
  border-right: 1px solid var(--color-border);
  padding-right: 12px;
}

.role-category h4 {
  margin: 0 0 8px;
}

.role-row {
  align-items: center;
  margin-top: 8px;
}

.role-row button {
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

.role-row small {
  color: var(--color-text-muted);
}

.role-editor {
  flex: 1;
  min-width: 0;
}
</style>
