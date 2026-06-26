<template>
  <label class="field">
    <span class="field__label">{{ label }}</span>
    <input
      class="field__control"
      :value="modelValue"
      :type="type"
      :placeholder="placeholder"
      :disabled="disabled"
      :min="min"
      :max="max"
      :step="step"
      @input="emitValue"
    />
    <span v-if="error" class="field__error">{{ error }}</span>
    <span v-else-if="hint" class="field__hint">{{ hint }}</span>
  </label>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    modelValue: string | number
    label: string
    type?: 'text' | 'number' | 'password' | 'url'
    placeholder?: string
    hint?: string
    error?: string
    disabled?: boolean
    min?: string | number
    max?: string | number
    step?: string | number
  }>(),
  {
    type: 'text',
    placeholder: '',
    hint: '',
    error: '',
    disabled: false,
    min: undefined,
    max: undefined,
    step: undefined,
  },
)

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

const emitValue = (event: Event) => {
  emit('update:modelValue', (event.target as HTMLInputElement).value)
}
</script>
