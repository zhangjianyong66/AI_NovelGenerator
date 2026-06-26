<template>
  <div class="action-bar" :class="{ 'action-bar--end': align === 'end' }">
    <slot />
  </div>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    align?: 'start' | 'end'
  }>(),
  {
    align: 'start',
  },
)
</script>
