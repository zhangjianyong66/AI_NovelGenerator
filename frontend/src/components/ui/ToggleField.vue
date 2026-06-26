<template>
  <label class="toggle-field">
    <input type="checkbox" :checked="modelValue" :disabled="disabled" @change="emitValue" />
    <span>{{ label }}</span>
  </label>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    modelValue: boolean
    label: string
    disabled?: boolean
  }>(),
  {
    disabled: false,
  },
)

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

const emitValue = (event: Event) => {
  emit('update:modelValue', (event.target as HTMLInputElement).checked)
}
</script>
