import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      redirect: '/projects',
    },
    {
      path: '/projects',
      name: 'projects',
      component: () => import('@/pages/ProjectsPage.vue'),
      meta: { label: '项目' },
    },
    {
      path: '/workspace',
      name: 'workspace',
      component: () => import('@/pages/WorkspacePage.vue'),
      meta: { label: '工作台' },
    },
    {
      path: '/chapters',
      name: 'chapters',
      component: () => import('@/pages/ChaptersPage.vue'),
      meta: { label: '章节编辑' },
    },
    {
      path: '/generation',
      name: 'generation',
      component: () => import('@/pages/GenerationPage.vue'),
      meta: { label: '生成任务' },
    },
    {
      path: '/settings',
      name: 'settings',
      component: () => import('@/pages/SettingsPage.vue'),
      meta: { label: '设置' },
    },
    {
      path: '/knowledge',
      name: 'knowledge',
      component: () => import('@/pages/KnowledgePage.vue'),
      meta: { label: '知识库' },
    },
  ],
})

export default router
