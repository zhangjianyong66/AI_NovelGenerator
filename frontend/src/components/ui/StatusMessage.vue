<template>
  <div v-if="message" class="status-message" :class="`status-message--${type}`" role="status">
    <component :is="iconComponent" :size="16" />
    <span>{{ message }}</span>
  </div>
</template>

<script setup lang="ts">
import { AlertTriangle, CheckCircle2, Info, LoaderCircle } from '@lucide/vue'
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    type?: 'success' | 'error' | 'warning' | 'loading' | 'empty' | 'info'
    message?: string
  }>(),
  {
    type: 'info',
    message: '',
  },
)

const iconComponent = computed(() => {
  const icons = {
    success: CheckCircle2,
    error: AlertTriangle,
    warning: AlertTriangle,
    loading: LoaderCircle,
    empty: Info,
    info: Info,
  }
  return icons[props.type]
})
</script>
