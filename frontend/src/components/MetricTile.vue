<template>
  <div class="metric-tile">
    <span>{{ label }}</span>
    <strong>{{ value }}</strong>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  label: string
  value: string | number
}>()
</script>

<style scoped>
.metric-tile {
  border: 1px solid var(--color-border);
  border-radius: 8px;
  background: var(--color-surface);
  padding: 14px;
}

.metric-tile span {
  display: block;
  color: var(--color-text-muted);
  font-size: 13px;
}

.metric-tile strong {
  display: block;
  margin-top: 8px;
  font-size: 24px;
  line-height: 1.2;
}
</style>
