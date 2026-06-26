<template>
  <div class="chapter-navigator">
    <button
      v-for="chapter in chapters"
      :key="chapter.id"
      class="chapter-navigator__item"
      :class="{ active: chapter.id === activeChapterId }"
      type="button"
      @click="$emit('select', chapter.id)"
    >
      <span>第 {{ chapter.order }} 章</span>
      <strong>{{ chapter.title }}</strong>
    </button>
  </div>
</template>

<script setup lang="ts">
import type { Chapter } from '@/services/types'

defineProps<{
  chapters: Chapter[]
  activeChapterId?: string
}>()

defineEmits<{
  select: [chapterId: string]
}>()
</script>

