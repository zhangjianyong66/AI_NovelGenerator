<template>
  <div class="long-text">
    <div v-if="title || filename || $slots.actions" class="long-text__heading">
      <div>
        <h3 v-if="title" class="long-text__title">{{ title }}</h3>
        <p v-if="filename" class="muted">{{ filename }}</p>
      </div>
      <slot name="actions" />
    </div>
    <textarea
      class="long-text__textarea"
      :aria-label="ariaLabel || title || '长文本'"
      :value="modelValue"
      :readonly="readonly"
      :disabled="disabled"
      :placeholder="placeholder"
      :style="{ minHeight }"
      @input="updateValue"
    />
    <div class="long-text__meta">
      <span>{{ wordCount }} 字</span>
      <SaveState v-if="dirty" state="dirty" />
      <SaveState v-if="saveState" state="idle" :text="saveState" />
      <span v-if="readonly">只读</span>
    </div>
    <StatusMessage v-if="emptyMessage && !modelValue" type="empty" :message="emptyMessage" />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

import SaveState from './SaveState.vue'
import StatusMessage from './StatusMessage.vue'

const props = withDefaults(
  defineProps<{
    modelValue: string
    title?: string
    filename?: string
    readonly?: boolean
    disabled?: boolean
    dirty?: boolean
    saveState?: string
    placeholder?: string
    emptyMessage?: string
    minHeight?: string
    ariaLabel?: string
  }>(),
  {
    title: '',
    filename: '',
    readonly: false,
    disabled: false,
    dirty: false,
    saveState: '',
    placeholder: '',
    emptyMessage: '',
    minHeight: '360px',
    ariaLabel: '',
  },
)

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

const wordCount = computed(() => props.modelValue.replace(/\s/g, '').length)

const updateValue = (event: Event) => {
  if (props.readonly) return
  emit('update:modelValue', (event.target as HTMLTextAreaElement).value)
}
</script>
