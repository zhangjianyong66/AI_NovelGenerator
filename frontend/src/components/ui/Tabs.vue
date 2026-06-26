<template>
  <div class="tabs">
    <div class="tabs__list" role="tablist">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        class="tabs__button"
        :class="{ active: tab.id === modelValue }"
        type="button"
        role="tab"
        :aria-selected="tab.id === modelValue"
        @click="$emit('update:modelValue', tab.id)"
      >
        {{ tab.label }}
      </button>
    </div>
    <div class="tabs__panel">
      <slot />
    </div>
  </div>
</template>

<script setup lang="ts" generic="T extends string">
defineProps<{
  modelValue: T
  tabs: Array<{ id: T; label: string }>
}>()

defineEmits<{
  'update:modelValue': [value: T]
}>()
</script>
