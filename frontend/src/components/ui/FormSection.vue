<template>
  <section class="panel form-section">
    <div class="panel-body">
      <div class="form-section__heading">
        <div>
          <h3 class="panel-title">{{ title }}</h3>
          <p v-if="description" class="form-section__description">{{ description }}</p>
        </div>
        <div v-if="$slots.actions" class="form-section__actions">
          <slot name="actions" />
        </div>
      </div>
      <slot />
    </div>
  </section>
</template>

<script setup lang="ts">
defineProps<{
  title: string
  description?: string
}>()
</script>
