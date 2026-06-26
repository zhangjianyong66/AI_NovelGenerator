<template>
  <section class="page">
    <div class="page-header">
      <div>
        <h2 class="page-title">知识库</h2>
        <p class="page-subtitle">导入知识文件、清理向量库，并查看当前项目的剧情要点。</p>
      </div>
      <button class="primary-button" :disabled="isBusy || !importPath" type="button" @click="importKnowledgeFile">
        <Upload :size="16" />
        导入资料
      </button>
    </div>

    <section class="panel">
      <div class="panel-body tool-panel">
        <label>
          文件路径
          <input v-model.trim="importPath" placeholder="/path/to/knowledge.txt" />
        </label>
        <button class="ghost-button" :disabled="isBusy" type="button" @click="clearVectorstore">清理向量库</button>
        <span v-if="message" class="status-pill">{{ message }}</span>
        <span v-if="errorMessage" class="status-pill warning">{{ errorMessage }}</span>
      </div>
    </section>

    <div class="knowledge-grid">
      <section class="panel">
        <div class="panel-body">
          <h3 class="panel-title">知识文件</h3>
          <article v-for="item in files" :key="item.id" class="knowledge-item">
            <h4>{{ item.name }}</h4>
            <p>{{ item.description }}</p>
            <div class="tag-row">
              <span v-for="tag in item.tags" :key="tag" class="tag">{{ tag }}</span>
            </div>
          </article>
        </div>
      </section>

      <section class="panel">
        <div class="panel-body">
          <h3 class="panel-title">剧情要点</h3>
          <p v-if="plotArcs?.exists" class="plot-arcs">{{ plotArcs.content }}</p>
          <p v-else class="muted">当前输出目录尚未生成剧情要点。</p>
          <p v-if="plotArcs" class="muted">{{ plotArcs.wordCount }} 字</p>
        </div>
      </section>

      <section class="panel role-panel">
        <div class="panel-body">
          <div class="role-heading">
            <h3 class="panel-title">角色库</h3>
            <button class="ghost-button" type="button" @click="applySelectedRoles">写入章节参数</button>
          </div>
          <div class="role-import">
            <input v-model.trim="roleImportCategory" placeholder="分类" />
            <input v-model.trim="roleImportPath" placeholder="/path/to/role.txt" />
            <button class="ghost-button" :disabled="!roleImportCategory || !roleImportPath" type="button" @click="importRole">
              导入
            </button>
          </div>
          <div class="role-layout">
            <div class="role-list">
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
              <h4>{{ activeRole?.name ?? '未选择角色' }}</h4>
              <textarea v-model="roleContent" :disabled="!activeRole" />
              <button class="primary-button" :disabled="!activeRole" type="button" @click="saveRole">保存角色</button>
            </div>
          </div>
        </div>
      </section>
    </div>
  </section>
</template>

<script setup lang="ts">
import { Upload } from '@lucide/vue'
import { computed, onMounted, ref } from 'vue'

import { serviceBridge } from '@/services/serviceBridge'
import type { KnowledgeItem, PlotArcs, RoleCategory, RoleDetail } from '@/services/types'

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
  isBusy.value = true
  message.value = ''
  errorMessage.value = ''
  try {
    const result = await serviceBridge.importKnowledgeFile(importPath.value)
    message.value = result.message
    await loadKnowledgeItems()
  } catch (error) {
    errorMessage.value =
      error instanceof Error
        ? error.message
        : typeof error === 'object' && error !== null && 'message' in error
          ? String(error.message)
          : '导入失败'
  } finally {
    isBusy.value = false
  }
}

const clearVectorstore = async () => {
  if (!window.confirm('确认清理当前项目的向量库？')) return
  isBusy.value = true
  message.value = ''
  errorMessage.value = ''
  try {
    const result = await serviceBridge.clearVectorstore()
    message.value = result.message
  } catch (error) {
    errorMessage.value =
      error instanceof Error
        ? error.message
        : typeof error === 'object' && error !== null && 'message' in error
          ? String(error.message)
          : '清理失败'
  } finally {
    isBusy.value = false
  }
}

const loadRole = async (category: string, roleName: string) => {
  activeRole.value = await serviceBridge.getRole(category, roleName)
  roleContent.value = activeRole.value.content
}

const saveRole = async () => {
  if (!activeRole.value) return
  const savedRole = await serviceBridge.saveRole(activeRole.value.category, activeRole.value.name, roleContent.value)
  activeRole.value = savedRole
  roleContent.value = savedRole.content
  message.value = '角色已保存'
  await loadRoles()
}

const importRole = async () => {
  const importedRole = await serviceBridge.importRole(roleImportCategory.value, roleImportPath.value)
  message.value = `已导入 ${importedRole.name}`
  roleImportPath.value = ''
  await loadRoles()
}

const applySelectedRoles = async () => {
  const selectedNames = roleCategories.value
    .flatMap((category) => category.roles)
    .filter((role) => selectedRoleIds.value.includes(role.id))
    .map((role) => role.name)
  const projectConfig = await serviceBridge.getProjectConfig()
  projectConfig.novelParams.charactersInvolved = selectedNames.join(',')
  await serviceBridge.saveProjectConfig(projectConfig)
  message.value = '已写入涉及角色'
}
</script>

<style scoped>
.knowledge-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: 16px;
}

.role-panel {
  grid-column: 1 / -1;
}

.tool-panel {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto auto auto;
  gap: 12px;
  align-items: end;
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

.plot-arcs {
  white-space: pre-wrap;
}

.role-heading,
.role-import,
.role-layout,
.role-row {
  display: flex;
  gap: 10px;
}

.role-heading {
  align-items: center;
  justify-content: space-between;
}

.role-import {
  margin: 12px 0;
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

.role-category h4,
.role-editor h4 {
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
}

.role-editor textarea {
  width: 100%;
  min-height: 260px;
  border: 1px solid var(--color-border);
  border-radius: 6px;
  padding: 10px;
  resize: vertical;
  color: var(--color-text);
  line-height: 1.7;
}

.primary-button:disabled,
.ghost-button:disabled {
  opacity: 0.65;
}
</style>
