import type {
  Chapter,
  ConfigTestResult,
  GenerationJobCreateRequest,
  GenerationJob,
  KnowledgeItem,
  ModelConfig,
  ModelSettings,
  PlotArcs,
  Project,
  ProjectConfig,
  ProjectFile,
  ProjectFileId,
  RoleCategory,
  RoleDetail,
  RoleSummary,
  WebDavConfig,
} from './types'

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

let chapters: Chapter[] = [
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

let jobs: GenerationJob[] = [
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

let modelSettings: ModelSettings = {
  selectedLlmConfig: 'DeepSeek V3',
  selectedEmbeddingConfig: 'Ollama',
  llmConfigs: [
    {
      name: 'DeepSeek V3',
      apiKey: '',
      hasApiKey: false,
      baseUrl: 'https://api.deepseek.com/v1',
      modelName: 'deepseek-chat',
      temperature: 0.7,
      maxTokens: 8192,
      timeout: 600,
      interfaceFormat: 'OpenAI',
    },
  ],
  embeddingConfigs: [
    {
      name: 'Ollama',
      apiKey: '',
      hasApiKey: false,
      baseUrl: 'http://127.0.0.1:11434',
      modelName: 'nomic-embed-text',
      retrievalK: 4,
      interfaceFormat: 'Ollama',
    },
  ],
  proxySetting: {
    proxyUrl: '127.0.0.1',
    proxyPort: '7890',
    enabled: false,
  },
  stageModelSelection: {
    promptDraft: 'DeepSeek V3',
    chapterOutline: 'DeepSeek V3',
    architecture: 'DeepSeek V3',
    finalChapter: 'DeepSeek V3',
    consistencyReview: 'DeepSeek V3',
  },
}

let projectConfig: ProjectConfig = {
  outputPath: '/tmp/ai-novel-output',
  novelParams: {
    topic: '记忆交易港城旧案',
    genre: '近未来悬疑',
    numChapters: 36,
    wordNumber: 4200,
    chapterNum: '3',
    userGuidance: '保持冷峻、克制的侦探叙事节奏。',
    charactersInvolved: '林澈,沈闻',
    keyItems: '记忆晶片,旧钟楼钥匙',
    sceneLocation: '雾港回收站',
    timeConstraint: '暴雨停歇前',
  },
}

let projectFiles: ProjectFile[] = [
  {
    id: 'novelSetting',
    label: '小说设定',
    filename: 'Novel_setting.txt',
    content: '雾港是一座依靠记忆交易维持秩序的近未来港城。',
    wordCount: 24,
    exists: true,
  },
  {
    id: 'novelDirectory',
    label: '目录蓝图',
    filename: 'Novel_directory.txt',
    content: '第一章 雨夜回收站\n第二章 没有姓名的证人',
    wordCount: 21,
    exists: true,
  },
  {
    id: 'characterState',
    label: '角色状态',
    filename: 'character_state.txt',
    content: '林澈：开始怀疑自己的第一次回忆。',
    wordCount: 15,
    exists: true,
  },
  {
    id: 'globalSummary',
    label: '全局摘要',
    filename: 'global_summary.txt',
    content: '',
    wordCount: 0,
    exists: false,
  },
]

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

let roleCategories: RoleCategory[] = [
  {
    name: '主角',
    roles: [
      {
        id: '主角/林澈',
        category: '主角',
        name: '林澈',
        filename: '林澈.txt',
        wordCount: 18,
      },
    ],
  },
]

let roleDetails: Record<string, RoleDetail> = {
  '主角/林澈': {
    id: '主角/林澈',
    category: '主角',
    name: '林澈',
    filename: '林澈.txt',
    wordCount: 18,
    content: '林澈：前数据取证员，怀疑自己的记忆被改写。',
  },
}

let webDavConfig: WebDavConfig = {
  webdavUrl: 'https://dav.example.com/root',
  username: 'user',
  password: '',
  hasPassword: true,
}

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
  async saveChapter(chapterOrder: number, content: string): Promise<Chapter> {
    await delay()
    const chapter = chapters.find((item) => item.order === chapterOrder)
    if (!chapter) throw new Error('章节不存在')
    const updatedChapter = {
      ...chapter,
      content,
      words: content.replace(/\s/g, '').length,
      updatedAt: '刚刚',
    }
    chapters = chapters.map((item) => (item.id === updatedChapter.id ? updatedChapter : item))
    return updatedChapter
  },
  async listGenerationJobs(projectId = 'p-ember-city'): Promise<GenerationJob[]> {
    await delay()
    return jobs.filter((job) => job.projectId === projectId)
  },
  async createGenerationJob(request: GenerationJobCreateRequest): Promise<GenerationJob> {
    await delay()
    const job: GenerationJob = {
      id: `j-${request.stage}-${Date.now()}`,
      projectId: request.projectId,
      title: `Mock ${request.stage}`,
      stage: request.stage,
      status: 'queued',
      progress: 0,
      startedAt: '刚刚',
      log: ['Mock 任务已创建', '等待真实后端执行器接入'],
      error: null,
    }
    jobs.unshift(job)
    return job
  },
  async getModelConfig(): Promise<ModelConfig> {
    await delay()
    return modelConfig
  },
  async getModelSettings(): Promise<ModelSettings> {
    await delay()
    return modelSettings
  },
  async saveModelSettings(settings: ModelSettings): Promise<ModelSettings> {
    await delay()
    modelSettings = {
      ...settings,
      llmConfigs: settings.llmConfigs.map((item) => ({ ...item })),
      embeddingConfigs: settings.embeddingConfigs.map((item) => ({ ...item })),
      proxySetting: { ...settings.proxySetting },
      stageModelSelection: { ...settings.stageModelSelection },
    }
    return modelSettings
  },
  async testLlmConfig(configName: string): Promise<ConfigTestResult> {
    await delay()
    const config = modelSettings.llmConfigs.find((item) => item.name === configName)
    return {
      success: Boolean(config?.apiKey || config?.hasApiKey),
      message: config ? 'Mock LLM 配置测试完成' : 'LLM 配置不存在',
    }
  },
  async getProjectConfig(): Promise<ProjectConfig> {
    await delay()
    return projectConfig
  },
  async saveProjectConfig(config: ProjectConfig): Promise<ProjectConfig> {
    await delay()
    projectConfig = {
      outputPath: config.outputPath,
      novelParams: { ...config.novelParams },
    }
    return projectConfig
  },
  async listProjectFiles(): Promise<ProjectFile[]> {
    await delay()
    return projectFiles
  },
  async saveProjectFile(fileId: ProjectFileId, content: string): Promise<ProjectFile> {
    await delay()
    const fileIndex = projectFiles.findIndex((item) => item.id === fileId)
    if (fileIndex < 0) throw new Error('未知项目文件')
    const updatedFile = {
      ...projectFiles[fileIndex],
      content,
      wordCount: content.replace(/\s/g, '').length,
      exists: true,
    }
    projectFiles = projectFiles.map((item) => (item.id === fileId ? updatedFile : item))
    return updatedFile
  },
  async listKnowledgeItems(): Promise<KnowledgeItem[]> {
    await delay()
    return knowledgeItems
  },
  async getPlotArcs(): Promise<PlotArcs> {
    await delay()
    return {
      exists: true,
      content: '主线：旧案重启并指向记忆交易核心。\n支线：林澈逐步验证自己的记忆缺口。',
      wordCount: 33,
    }
  },
  async listRoles(): Promise<RoleCategory[]> {
    await delay()
    return roleCategories
  },
  async getRole(category: string, roleName: string): Promise<RoleDetail> {
    await delay()
    const role = roleDetails[`${category}/${roleName}`]
    if (!role) throw new Error('角色不存在')
    return role
  },
  async saveRole(category: string, roleName: string, content: string): Promise<RoleDetail> {
    await delay()
    const id = `${category}/${roleName}`
    const role = roleDetails[id]
    if (!role) throw new Error('角色不存在')
    const updatedRole = { ...role, content, wordCount: content.replace(/\s/g, '').length }
    roleDetails[id] = updatedRole
    roleCategories = roleCategories.map((item) =>
      item.name === category
        ? {
            ...item,
            roles: item.roles.map((summary) => (summary.id === id ? { ...summary, wordCount: updatedRole.wordCount } : summary)),
          }
        : item,
    )
    return updatedRole
  },
  async importRole(category: string, filePath: string): Promise<RoleSummary> {
    await delay()
    const name = filePath.split('/').pop()?.replace(/\.txt$/, '') || '新角色'
    const role: RoleDetail = {
      id: `${category}/${name}`,
      category,
      name,
      filename: `${name}.txt`,
      content: `${name}：`,
      wordCount: name.length + 1,
    }
    roleDetails[role.id] = role
    const categoryItem = roleCategories.find((item) => item.name === category)
    if (categoryItem) {
      categoryItem.roles.push(role)
    } else {
      roleCategories.push({ name: category, roles: [role] })
    }
    return role
  },
  async getWebDavConfig(): Promise<WebDavConfig> {
    await delay()
    return webDavConfig
  },
  async saveWebDavConfig(config: WebDavConfig): Promise<WebDavConfig> {
    await delay()
    webDavConfig = {
      ...config,
      password: config.password || webDavConfig.password,
    }
    return webDavConfig
  },
  async testWebDavConfig(config: WebDavConfig): Promise<{ success: boolean; message: string }> {
    await delay()
    webDavConfig = {
      ...config,
      password: config.password || webDavConfig.password,
      hasPassword: config.hasPassword || Boolean(config.password),
    }
    return { success: true, message: 'WebDAV 连接成功' }
  },
  async backupWebDavConfig(): Promise<{ success: boolean; message: string }> {
    await delay()
    return { success: true, message: '配置备份成功' }
  },
  async restoreWebDavConfig(): Promise<{ success: boolean; message: string }> {
    await delay()
    return { success: true, message: '配置恢复成功' }
  },
}
