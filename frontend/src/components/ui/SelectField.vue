<template>
  <label class="field">
    <span class="field__label">{{ label }}</span>
    <select class="field__control" :value="modelValue" :disabled="disabled" @change="emitValue">
      <option v-for="option in options" :key="option.value" :value="option.value">
        {{ option.label }}
      </option>
    </select>
    <span v-if="error" class="field__error">{{ error }}</span>
    <span v-else-if="hint" class="field__hint">{{ hint }}</span>
  </label>
</template>

<script setup lang="ts" generic="T extends string">
withDefaults(
  defineProps<{
    modelValue: T
    label: string
    options: Array<{ value: T; label: string }>
    hint?: string
    error?: string
    disabled?: boolean
  }>(),
  {
    hint: '',
    error: '',
    disabled: false,
  },
)

const emit = defineEmits<{
  'update:modelValue': [value: T]
}>()

const emitValue = (event: Event) => {
  emit('update:modelValue', (event.target as HTMLSelectElement).value as T)
}
</script>
