<template>
  <div class="confirm-panel">
    <div>
      <strong>{{ title }}</strong>
      <p>{{ description }}</p>
    </div>
    <AppButton variant="secondary" :disabled="disabled" @click="confirming = !confirming">
      {{ confirming ? '取消' : actionLabel }}
    </AppButton>
    <AppButton
      v-if="confirming"
      variant="danger"
      :disabled="disabled"
      @click="confirm"
    >
      确认{{ actionLabel }}
    </AppButton>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

import AppButton from './AppButton.vue'

defineProps<{
  title: string
  description: string
  actionLabel: string
  disabled?: boolean
}>()

const emit = defineEmits<{
  confirm: []
}>()

const confirming = ref(false)

const confirm = () => {
  confirming.value = false
  emit('confirm')
}
</script>
