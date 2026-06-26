<template>
  <button
    class="icon-button"
    :class="`icon-button--${variant}`"
    :type="type"
    :disabled="disabled"
    :aria-label="label"
    :title="label"
  >
    <slot />
  </button>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    label: string
    variant?: 'secondary' | 'primary' | 'danger'
    type?: 'button' | 'submit' | 'reset'
    disabled?: boolean
  }>(),
  {
    variant: 'secondary',
    type: 'button',
    disabled: false,
  },
)
</script>
