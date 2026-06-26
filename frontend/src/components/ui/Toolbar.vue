<template>
  <div class="toolbar" :class="{ 'toolbar--end': align === 'end' }">
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
