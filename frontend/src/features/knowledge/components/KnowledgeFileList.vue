<template>
  <div class="knowledge-list">
    <article v-for="item in files" :key="item.id" class="knowledge-item">
      <h4>{{ item.name }}</h4>
      <p>{{ item.description }}</p>
      <div class="tag-row">
        <span v-for="tag in item.tags" :key="tag" class="tag">{{ tag }}</span>
      </div>
    </article>
  </div>
</template>

<script setup lang="ts">
import type { KnowledgeItem } from '@/services/types'

defineProps<{
  files: KnowledgeItem[]
}>()
</script>

