<template>
  <label class="field">
    <span class="field__label">{{ label }}</span>
    <textarea
      class="field__control field__control--textarea"
      :value="modelValue"
      :placeholder="placeholder"
      :disabled="disabled"
      :rows="rows"
      @input="emitValue"
    />
    <span v-if="error" class="field__error">{{ error }}</span>
    <span v-else-if="hint" class="field__hint">{{ hint }}</span>
  </label>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    modelValue: string
    label: string
    placeholder?: string
    hint?: string
    error?: string
    disabled?: boolean
    rows?: number
  }>(),
  {
    placeholder: '',
    hint: '',
    error: '',
    disabled: false,
    rows: 4,
  },
)

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

const emitValue = (event: Event) => {
  emit('update:modelValue', (event.target as HTMLTextAreaElement).value)
}
</script>
