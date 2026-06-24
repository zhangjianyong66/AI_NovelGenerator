import type { Chapter, GenerationJob, KnowledgeItem, ModelConfig, Project } from './types'

const projects: Project[] = [
  {
    id: 'p-ember-city',
    title: '雾港余烬',
    genre: '近未来悬疑',
    status: 'active',
    summary: '一座依靠记忆交易维持秩序的港城，在旧案重启后暴露出生成式谎言网络。',
    updatedAt: '2026-06-24 16:20',
    chaptersTotal: 36,
    chaptersCompleted: 8,
  },
  {
    id: 'p-moon-archive',
    title: '月背档案',
    genre: '硬科幻',
    status: 'draft',
    summary: '月背观测站收到二十年前的地球求救信号，调查队必须判断它来自历史还是诱饵。',
    updatedAt: '2026-06-23 21:05',
    chaptersTotal: 24,
    chaptersCompleted: 3,
  },
]

const chapters: Chapter[] = [
  {
    id: 'c-001',
    projectId: 'p-ember-city',
    order: 1,
    title: '雨夜回收站',
    status: 'final',
    words: 4230,
    synopsis: '主角在记忆回收站处理异常委托，发现被删除的案件编号。',
    content:
      '雨水沿着霓虹招牌的裂缝落下，像一串被剪断的时间码。林澈把最后一枚记忆晶片推入读槽，屏幕却弹出一个不属于今天的案号。',
    viewpoint: '林澈',
    updatedAt: '2026-06-24 15:12',
  },
  {
    id: 'c-002',
    projectId: 'p-ember-city',
    order: 2,
    title: '没有姓名的证人',
    status: 'review',
    words: 3860,
    synopsis: '无名证人的记忆片段指向港城核心算法，团队第一次意识到案情被人为重写。',
    content:
      '证人的声音被压缩成低频噪声，只剩下一句反复出现的警告：不要相信自己的第一次回忆。',
    viewpoint: '沈闻',
    updatedAt: '2026-06-24 15:44',
  },
  {
    id: 'c-003',
    projectId: 'p-ember-city',
    order: 3,
    title: '盐雾中的旧钟楼',
    status: 'drafting',
    words: 2180,
    synopsis: '旧钟楼保存着失效前的城市备份，主角需要在追捕前提取关键索引。',
    content: '钟楼的铜门没有锁，只有一行手写的访问密钥，像是专门留给某个迟到的人。',
    viewpoint: '林澈',
    updatedAt: '2026-06-24 16:03',
  },
]

const jobs: GenerationJob[] = [
  {
    id: 'j-architecture',
    projectId: 'p-ember-city',
    title: '生成小说设定',
    stage: 'architecture',
    status: 'done',
    progress: 100,
    startedAt: '2026-06-24 14:10',
    log: ['已读取主题和类型参数', '已完成世界观与人物关系草案', '等待人工确认'],
  },
  {
    id: 'j-directory',
    projectId: 'p-ember-city',
    title: '扩展章节目录',
    stage: 'directory',
    status: 'running',
    progress: 64,
    startedAt: '2026-06-24 15:50',
    log: ['正在拆分第二幕冲突', '已生成 18/28 个章节摘要', '下一步补齐结尾转折'],
  },
  {
    id: 'j-batch',
    projectId: 'p-ember-city',
    title: '批量生成草稿',
    stage: 'batch',
    status: 'queued',
    progress: 0,
    startedAt: '等待启动',
    log: ['队列已创建', '等待目录任务完成'],
  },
]

const modelConfig: ModelConfig = {
  provider: 'OpenAI Compatible',
  modelName: 'gpt-4o-mini',
  temperature: 0.72,
  maxTokens: 4096,
  embeddingProvider: 'Ollama',
  embeddingModel: 'nomic-embed-text',
  proxyEnabled: false,
  proxyUrl: 'http://127.0.0.1:7890',
}

const knowledgeItems: KnowledgeItem[] = [
  {
    id: 'k-world',
    type: 'file',
    name: '港城设定索引',
    description: '区域、组织、记忆交易规则和禁区说明。',
    tags: ['世界观', '设定'],
    updatedAt: '2026-06-24 13:22',
  },
  {
    id: 'k-lin-che',
    type: 'role',
    name: '林澈',
    description: '前数据取证员，当前在记忆回收站处理灰色委托。',
    tags: ['主角', '取证'],
    updatedAt: '2026-06-23 19:18',
  },
  {
    id: 'k-shen-wen',
    type: 'role',
    name: '沈闻',
    description: '港城监察署顾问，掌握旧案但无法证明自己的记忆未被改写。',
    tags: ['盟友', '悬疑线'],
    updatedAt: '2026-06-23 20:40',
  },
]

const delay = async () => new Promise((resolve) => window.setTimeout(resolve, 80))

export const mockApi = {
  async listProjects(): Promise<Project[]> {
    await delay()
    return projects
  },
  async listChapters(projectId = 'p-ember-city'): Promise<Chapter[]> {
    await delay()
    return chapters.filter((chapter) => chapter.projectId === projectId)
  },
  async listGenerationJobs(projectId = 'p-ember-city'): Promise<GenerationJob[]> {
    await delay()
    return jobs.filter((job) => job.projectId === projectId)
  },
  async getModelConfig(): Promise<ModelConfig> {
    await delay()
    return modelConfig
  },
  async listKnowledgeItems(): Promise<KnowledgeItem[]> {
    await delay()
    return knowledgeItems
  },
}
