<template>
  <div class="state-block">
    <div>
      <p class="state-block__title">{{ title }}</p>
      <p v-if="description" class="state-block__description">{{ description }}</p>
      <slot />
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  title: string
  description?: string
}>()
</script>
