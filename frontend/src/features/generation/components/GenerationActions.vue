<template>
  <Toolbar class="generation-actions" aria-label="生成任务操作">
    <div v-for="group in actionGroups" :key="group.label" class="generation-actions__group" :aria-label="group.label">
      <AppButton
        v-for="action in group.actions"
        :key="action.stage"
        variant="primary"
        :disabled="disabled"
        @click="emitAction(group.event, action.stage)"
      >
        <Play :size="16" />
        {{ action.label }}
      </AppButton>
    </div>
  </Toolbar>
</template>

<script setup lang="ts">
import { Play } from '@lucide/vue'
import { computed } from 'vue'

import { AppButton, Toolbar } from '@/components/ui'
import type { GenerationStage } from '@/services/types'

const props = withDefaults(defineProps<{
  disabled?: boolean
  mode?: 'standard' | 'batch'
}>(), {
  mode: 'standard',
})

const emit = defineEmits<{
  create: [stage: GenerationStage]
  createBatch: [stage: GenerationStage]
}>()

const initializationActions: Array<{ label: string; stage: GenerationStage }> = [
  { label: '设定', stage: 'architecture' },
  { label: '目录', stage: 'directory' },
]

const singleActions: Array<{ label: string; stage: GenerationStage }> = [
  { label: '草稿', stage: 'draft' },
  { label: '定稿', stage: 'finalization' },
  { label: '审校', stage: 'consistency' },
]

const batchActions: Array<{ label: string; stage: GenerationStage }> = [
  { label: '批量草稿', stage: 'batchDraft' },
  { label: '批量定稿', stage: 'batchFinalization' },
  { label: '批量审校', stage: 'batchConsistency' },
]

type ActionGroup = {
  label: string
  event: 'create' | 'createBatch'
  actions: Array<{ label: string; stage: GenerationStage }>
}

const standardActionGroups: ActionGroup[] = [
  { label: '初始化操作', event: 'create', actions: initializationActions },
  { label: '单章操作', event: 'create', actions: singleActions },
]

const batchActionGroups: ActionGroup[] = [
  { label: '批量操作', event: 'createBatch', actions: batchActions },
]

const actionGroups = computed(() => (props.mode === 'batch' ? batchActionGroups : standardActionGroups))

const emitAction = (event: 'create' | 'createBatch', stage: GenerationStage) => {
  if (event === 'create') {
    emit('create', stage)
    return
  }
  emit('createBatch', stage)
}
</script>

<style scoped>
.generation-actions {
  align-items: stretch;
  column-gap: 14px;
  row-gap: 10px;
}

.generation-actions__group {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  min-width: 0;
}

.generation-actions__group + .generation-actions__group {
  border-left: 1px solid var(--color-border);
  padding-left: 14px;
}

@media (max-width: 760px) {
  .generation-actions {
    flex-direction: column;
  }

  .generation-actions__group + .generation-actions__group {
    border-left: 0;
    border-top: 1px solid var(--color-border);
    padding-left: 0;
    padding-top: 10px;
  }
}
</style>
