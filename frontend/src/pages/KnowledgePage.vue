<template>
  <section class="page">
    <div class="page-header">
      <div>
        <h2 class="page-title">知识库</h2>
        <p class="page-subtitle">知识文件和角色库区域的 UI 骨架，当前使用 mock 条目。</p>
      </div>
      <button class="primary-button" type="button">
        <Upload :size="16" />
        导入资料
      </button>
    </div>

    <div class="knowledge-grid">
      <section class="panel">
        <div class="panel-body">
          <h3 class="panel-title">知识文件</h3>
          <article v-for="item in files" :key="item.id" class="knowledge-item">
            <h4>{{ item.name }}</h4>
            <p>{{ item.description }}</p>
            <div class="tag-row">
              <span v-for="tag in item.tags" :key="tag" class="tag">{{ tag }}</span>
            </div>
          </article>
        </div>
      </section>

      <section class="panel">
        <div class="panel-body">
          <h3 class="panel-title">角色库</h3>
          <article v-for="item in roles" :key="item.id" class="knowledge-item">
            <h4>{{ item.name }}</h4>
            <p>{{ item.description }}</p>
            <div class="tag-row">
              <span v-for="tag in item.tags" :key="tag" class="tag">{{ tag }}</span>
            </div>
          </article>
        </div>
      </section>
    </div>
  </section>
</template>

<script setup lang="ts">
import { Upload } from '@lucide/vue'
import { computed, onMounted, ref } from 'vue'

import { mockApi } from '@/services/mockApi'
import type { KnowledgeItem } from '@/services/types'

const items = ref<KnowledgeItem[]>([])
const files = computed(() => items.value.filter((item) => item.type === 'file'))
const roles = computed(() => items.value.filter((item) => item.type === 'role'))

onMounted(async () => {
  items.value = await mockApi.listKnowledgeItems()
})
</script>

<style scoped>
.knowledge-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: 16px;
}

.knowledge-item {
  border-top: 1px solid var(--color-border);
  padding: 14px 0;
}

.knowledge-item:first-of-type {
  border-top: 0;
  padding-top: 0;
}

h4 {
  margin: 0 0 6px;
  font-size: 16px;
}

p {
  margin: 0 0 10px;
  color: var(--color-text-muted);
  line-height: 1.6;
}
</style>
