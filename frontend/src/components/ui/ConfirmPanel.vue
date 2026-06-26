<template>
  <div class="confirm-panel">
    <div>
      <strong>{{ title }}</strong>
      <p>{{ description }}</p>
    </div>
    <button class="ghost-button" :disabled="disabled" type="button" @click="confirming = !confirming">
      {{ confirming ? '取消' : actionLabel }}
    </button>
    <button
      v-if="confirming"
      class="primary-button danger-button"
      :disabled="disabled"
      type="button"
      @click="confirm"
    >
      确认{{ actionLabel }}
    </button>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

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
