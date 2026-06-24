<template>
  <section class="page">
    <div class="page-header">
      <div>
        <h2 class="page-title">设置</h2>
        <p class="page-subtitle">模型、Embedding 和代理配置区域的 UI 骨架。</p>
      </div>
      <button class="primary-button" type="button">
        <Save :size="16" />
        保存配置
      </button>
    </div>

    <div v-if="config" class="grid three">
      <section class="panel">
        <div class="panel-body">
          <h3 class="panel-title">模型</h3>
          <label>服务商<input :value="config.provider" /></label>
          <label>模型<input :value="config.modelName" /></label>
          <label>Temperature<input :value="config.temperature" type="number" /></label>
          <label>Max Tokens<input :value="config.maxTokens" type="number" /></label>
        </div>
      </section>

      <section class="panel">
        <div class="panel-body">
          <h3 class="panel-title">Embedding</h3>
          <label>服务商<input :value="config.embeddingProvider" /></label>
          <label>模型<input :value="config.embeddingModel" /></label>
          <p class="muted">切换真实 Embedding 模型后需要清理旧向量库。</p>
        </div>
      </section>

      <section class="panel">
        <div class="panel-body">
          <h3 class="panel-title">代理</h3>
          <label class="toggle"><input :checked="config.proxyEnabled" type="checkbox" /> 启用代理</label>
          <label>代理地址<input :value="config.proxyUrl" /></label>
        </div>
      </section>
    </div>
  </section>
</template>

<script setup lang="ts">
import { Save } from '@lucide/vue'
import { onMounted, ref } from 'vue'

import { mockApi } from '@/services/mockApi'
import type { ModelConfig } from '@/services/types'

const config = ref<ModelConfig>()

onMounted(async () => {
  config.value = await mockApi.getModelConfig()
})
</script>

<style scoped>
label {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-top: 12px;
  color: var(--color-text-muted);
  font-size: 13px;
}

input {
  min-height: 36px;
  border: 1px solid var(--color-border);
  border-radius: 6px;
  padding: 0 10px;
  color: var(--color-text);
}

.toggle {
  flex-direction: row;
  align-items: center;
}
</style>
