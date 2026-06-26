<template>
  <div class="writing-editor">
    <div v-if="title || subtitle || $slots.actions" class="writing-editor__heading">
      <div>
        <h3 v-if="title" class="writing-editor__title">{{ title }}</h3>
        <p v-if="subtitle" class="muted">{{ subtitle }}</p>
      </div>
      <div v-if="$slots.actions" class="writing-editor__actions">
        <slot name="actions" />
      </div>
    </div>

    <textarea
      ref="textareaRef"
      class="writing-editor__textarea"
      :aria-label="ariaLabel || title || '写作编辑器'"
      :value="modelValue"
      :readonly="readonly"
      :disabled="disabled"
      :placeholder="placeholder"
      :style="{ minHeight }"
      @input="updateValue"
      @select="updateSelection"
      @keyup="updateSelection"
      @mouseup="updateSelection"
      @focus="$emit('focus')"
      @keydown.meta.s.prevent="$emit('save')"
      @keydown.ctrl.s.prevent="$emit('save')"
    />

    <div class="writing-editor__meta">
      <span>{{ metrics.wordCount }} 字</span>
      <span>{{ metrics.paragraphCount }} 段</span>
      <span v-if="metrics.selectedWordCount">选中 {{ metrics.selectedWordCount }} 字</span>
      <SaveState v-if="dirty" state="dirty" />
      <SaveState v-if="saveState" :state="saveState.state" :text="saveState.text" />
      <span v-if="readonly">只读</span>
    </div>

    <StatusMessage v-if="emptyMessage && !modelValue" type="empty" :message="emptyMessage" />
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'

import SaveState from '@/components/ui/SaveState.vue'
import StatusMessage from '@/components/ui/StatusMessage.vue'

import { getEditorMetrics } from '../editorMetrics'

const props = withDefaults(
  defineProps<{
    modelValue: string
    title?: string
    subtitle?: string
    readonly?: boolean
    disabled?: boolean
    dirty?: boolean
    saveState?: {
      state: 'saved' | 'saving' | 'dirty' | 'error' | 'idle'
      text?: string
    } | null
    placeholder?: string
    emptyMessage?: string
    minHeight?: string
    ariaLabel?: string
  }>(),
  {
    title: '',
    subtitle: '',
    readonly: false,
    disabled: false,
    dirty: false,
    saveState: null,
    placeholder: '',
    emptyMessage: '',
    minHeight: '360px',
    ariaLabel: '',
  },
)

const emit = defineEmits<{
  'update:modelValue': [value: string]
  save: []
  focus: []
}>()

const textareaRef = ref<HTMLTextAreaElement | null>(null)
const selectedText = ref('')

const metrics = computed(() => getEditorMetrics(props.modelValue, selectedText.value))

const updateValue = (event: Event) => {
  if (props.readonly) return
  emit('update:modelValue', (event.target as HTMLTextAreaElement).value)
  updateSelection()
}

const updateSelection = () => {
  const textarea = textareaRef.value
  if (!textarea) {
    selectedText.value = ''
    return
  }
  selectedText.value = textarea.value.slice(textarea.selectionStart, textarea.selectionEnd)
}
</script>
