<template>
  <div class="split-pane" :style="paneStyle">
    <slot />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    start?: string
    end?: string
  }>(),
  {
    start: '1fr',
    end: '1fr',
  },
)

const paneStyle = computed(() => ({
  '--split-pane-start': props.start,
  '--split-pane-end': props.end,
}))
</script>
