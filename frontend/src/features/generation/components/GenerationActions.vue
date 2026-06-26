<template>
  <Toolbar>
    <AppButton
      v-for="action in actions"
      :key="action.stage"
      variant="primary"
      :disabled="disabled"
      @click="$emit('create', action.stage)"
    >
      <Play :size="16" />
      {{ action.label }}
    </AppButton>
    <AppButton variant="primary" :disabled="disabled" @click="$emit('createBatch')">
      <Play :size="16" />
      批量
    </AppButton>
  </Toolbar>
</template>

<script setup lang="ts">
import { Play } from '@lucide/vue'

import { AppButton, Toolbar } from '@/components/ui'
import type { GenerationStage } from '@/services/types'

defineProps<{
  disabled?: boolean
}>()

defineEmits<{
  create: [stage: GenerationStage]
  createBatch: []
}>()

const actions: Array<{ label: string; stage: GenerationStage }> = [
  { label: '设定', stage: 'architecture' },
  { label: '目录', stage: 'directory' },
  { label: '草稿', stage: 'draft' },
  { label: '定稿', stage: 'finalization' },
  { label: '审校', stage: 'consistency' },
]
</script>

