<template>
  <span class="save-state" :class="`save-state--${state}`">
    {{ label }}
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    state?: 'saved' | 'saving' | 'dirty' | 'error' | 'idle'
    text?: string
  }>(),
  {
    state: 'idle',
    text: '',
  },
)

const label = computed(() => {
  if (props.text) return props.text
  const labels = {
    saved: '已保存',
    saving: '保存中',
    dirty: '有未保存变更',
    error: '保存失败',
    idle: '未修改',
  }
  return labels[props.state]
})
</script>
