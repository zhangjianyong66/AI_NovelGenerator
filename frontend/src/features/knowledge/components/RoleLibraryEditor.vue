<template>
  <div class="role-layout">
    <div class="role-list">
      <StatusMessage v-if="roleCategories.length === 0" type="empty" message="当前没有角色库文件。" />
      <div v-for="category in roleCategories" :key="category.name" class="role-category">
        <h4>{{ category.name }}</h4>
        <label v-for="role in category.roles" :key="role.id" class="role-row">
          <input
            :checked="selectedRoleIds.includes(role.id)"
            :value="role.id"
            type="checkbox"
            @change="toggleRole(role.id, ($event.target as HTMLInputElement).checked)"
          />
          <button type="button" @click="$emit('loadRole', role.category, role.name)">
            {{ role.name }}
            <small>{{ role.wordCount }} 字</small>
          </button>
        </label>
      </div>
    </div>
    <div class="role-editor">
      <WritingEditor
        :model-value="roleContent"
        :title="activeRole?.name ?? '未选择角色'"
        :disabled="!activeRole"
        :readonly="readonly"
        empty-message="请选择一个角色进行查看或编辑。"
        min-height="300px"
        @update:model-value="$emit('update:roleContent', $event)"
      >
        <template #actions>
          <AppButton variant="primary" :disabled="!activeRole || readonly" @click="$emit('saveRole')">保存角色</AppButton>
        </template>
      </WritingEditor>
    </div>
  </div>
</template>

<script setup lang="ts">
import { AppButton, StatusMessage } from '@/components/ui'
import { WritingEditor } from '@/features/writing'
import type { RoleCategory, RoleDetail } from '@/services/types'

const props = defineProps<{
  roleCategories: RoleCategory[]
  activeRole?: RoleDetail
  roleContent: string
  selectedRoleIds: string[]
  readonly?: boolean
}>()

const emit = defineEmits<{
  'update:roleContent': [content: string]
  'update:selectedRoleIds': [roleIds: string[]]
  loadRole: [category: string, roleName: string]
  saveRole: []
}>()

const toggleRole = (roleId: string, checked: boolean) => {
  const nextIds = checked
    ? [...props.selectedRoleIds, roleId]
    : props.selectedRoleIds.filter((selectedRoleId) => selectedRoleId !== roleId)
  emit('update:selectedRoleIds', Array.from(new Set(nextIds)))
}
</script>
