<template>
  <div class="state-block" role="status">
    <div>
      <p class="state-block__title">{{ title }}</p>
      <p v-if="description" class="state-block__description">{{ description }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    title?: string
    description?: string
  }>(),
  {
    title: '加载中',
    description: '',
  },
)
</script>
