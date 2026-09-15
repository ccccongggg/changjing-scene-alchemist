/*
  第一层：原帖基准层（社区共享、只读、不可被用户内容覆盖）
  示例文章：《如何用 AI 做出高质量的 PPT》
  知识树：中心节点 → 第一圈层 → 定主题的第二圈层 → 主题收窄的第三圈层
  默认只展示第一圈层；用户选中某分支后才展开它的下一圈层。
*/

export const ARTICLE = {
  id: 'ppt-ai-001',
  title: '如何用 AI 做出高质量的 PPT',
  author: '卡兹克',
  authorTag: 'AI 提效博主 · 知乎高赞',
  intro:
    '这不是一份「提示词模板」，而是一套可复用的工作流：先逼自己把要讲的东西想清楚，再让 AI 把它变成页面。作者按「定主题 → 聊主题 → 反复确认大纲 → 选择风格 → 生成并微调页面 → 图片转 PPT」六步推进，每一步都给了判断标准。',
  sourceLabel: '知乎 · 高赞经验帖',
  sourceUrl: 'https://www.zhihu.com/',
  version: 'v1.0 · 2026-08 收录',
  sceneCount: 128 // 已收录的真实场景数量
}

/*
  贡献地图的「太阳」候选：用户收藏过的知乎原帖。
  L0 太阳 = 我收藏的原帖；L1 行星 = 不同用户在真实场景下提出的场景问题；L2 卫星 = 该场景的执行步骤。
*/
export const POSTS = {
  'ppt-ai-001': {
    id: 'ppt-ai-001',
    title: '如何用 AI 做出高质量的 PPT',
    author: '卡兹克'
  },
  'embed-001': {
    id: 'embed-001',
    title: '嵌入式调试经验合集',
    author: '电路老张'
  }
}


/*
  节点树。ring: 0=中心 1/2/3=第 N 圈层
  method     = 作者在该节点的原始方法（原文口径，不可被用户改写）
  conditions = 适用条件（原文给出的前提）
*/
export const NODES = [
  {
    id: 'core',
    label: '如何用 AI 做出高质量的 PPT',
    short: '原帖主题',
    ring: 0,
    parent: null,
    children: ['t1', 't2', 't3', 't4', 't5', 't6'],
    method:
      '把「用 AI 做 PPT」当成一条流水线：想清楚（定主题/聊主题/确认大纲）→ 定调性（选风格）→ 出页面（生成并微调）→ 补素材（图片转 PPT）。每一环都由人把关，AI 只负责放大产能。',
    conditions: '适用于任何需要「用 AI 从零产出一份可交付 PPT」的人。',
    tags: ['原帖主线']
  },
  /* ---------------- 第一圈层 ---------------- */
  {
    id: 't1',
    label: '定主题',
    short: '定主题',
    ring: 1,
    parent: 'core',
    children: ['t1-1'],
    method:
      '不要一上来就让 AI 写 PPT。先用一句话把「这份 PPT 到底要解决什么」写清楚，写不清楚就别往下走。作者的做法是：写下主题句 → 让 AI 反问澄清 → 自己再收窄一次。',
    conditions: '主讲人自己还没想清楚要讲什么时，这一步最关键。',
    tags: ['起点', '必做']
  },
  {
    id: 't2',
    label: '聊主题',
    short: '聊主题',
    ring: 1,
    parent: 'core',
    children: ['t2-1', 't2-2'],
    method:
      '把「聊」当成一种检索手段：跟 AI 反复对话，让它把主题相关的知识点、常见结构、听众可能关心的问题列出来，再从中挑。',
    conditions: '对选题没有把握、需要先摸清信息范围时使用。',
    tags: ['发散']
  },
  {
    id: 't3',
    label: '反复确认大纲',
    short: '确认大纲',
    ring: 1,
    parent: 'core',
    children: ['t3-1', 't3-2'],
    method:
      '大纲必须逐条确认，不要接受 AI 一次给出的成品大纲。作者会要求 AI 先给「三个不同思路的版本」，再挑一个继续细化。',
    conditions: '内容偏正式（汇报/答辩/提案）时，大纲质量决定成片质量。',
    tags: ['收敛']
  },
  {
    id: 't4',
    label: '选择风格',
    short: '选风格',
    ring: 1,
    parent: 'core',
    children: ['t4-1', 't4-2'],
    method:
      '先定配色和版式，再生成页面。作者会先让 AI 给出 3 套「配色 + 字体 + 版式密度」的组合描述，选定后再进入批量生成。',
    conditions: '面向外部听众、需要统一视觉调性时必做。',
    tags: ['视觉']
  },
  {
    id: 't5',
    label: '生成并微调页面',
    short: '生成微调',
    ring: 1,
    parent: 'core',
    children: ['t5-1', 't5-2'],
    method:
      '批量生成初稿 → 逐页微调。作者强调「AI 出的是 70 分草稿」，微调才是把 70 分抬到 90 分的动作：删废话、换措辞、调层级。',
    conditions: '页数 ≥ 10 时，批量生成 + 人工微调的收益最明显。',
    tags: ['产能']
  },
  {
    id: 't6',
    label: '图片转 PPT',
    short: '图片转 PPT',
    ring: 1,
    parent: 'core',
    children: ['t6-1', 't6-2'],
    method:
      '把已有截图/产品图/流程图喂给 AI，让它先整理顺序与说明，再生成图文并茂的页面，避免自己一张张排版。',
    conditions: '手上已有大量图片素材、或需要图文并茂的说明页时使用。',
    tags: ['素材']
  },

  /* ---------------- 定主题 → 第二圈层 ---------------- */
  {
    id: 't1-1',
    label: '主题收窄',
    short: '主题收窄',
    ring: 2,
    parent: 't1',
    children: ['q1', 'q2', 'q3', 'q4'],
    method:
      '把「大主题」收窄成「这一场要讲的那一句」。作者用四个问题把范围钉死，答不上来就说明主题还太大。',
    conditions: '主题一句话说不清、容易被听众觉得「很空」时使用。',
    tags: ['关键节点']
  },

  /* ---------------- 主题收窄 → 第三圈层 ---------------- */
  {
    id: 'q1',
    label: '这份 PPT 是做分享、汇报、说服，还是培训？',
    short: '用途是什么',
    ring: 3,
    parent: 't1-1',
    children: [],
    method:
      '先定义「交付类型」。分享求共鸣、汇报求交代、说服求决策、培训求改变行为——四者的结构完全不同，选错类型后面全白做。',
    conditions: '开写之前必须先回答。',
    tags: ['定位']
  },
  {
    id: 'q2',
    label: '听众是谁，他们已经知道什么？',
    short: '听众是谁',
    ring: 3,
    parent: 't1-1',
    children: [],
    method:
      '写出听众的「已知」与「未知」。已知的不要重复讲，未知的才是你要补的。作者建议直接列一张两列表。',
    conditions: '面向非专业听众时尤其重要。',
    tags: ['定位']
  },
  {
    id: 'q3',
    label: '预计讲多久，大约需要多少页？',
    short: '时长与页数',
    ring: 3,
    parent: 't1-1',
    children: [],
    method:
      '用「1 页 ≈ 1.5–2 分钟」反推页数上限。页数不是越多越好，超时是汇报最大的失败。',
    conditions: '有明确时长限制（如 10 分钟汇报）时必做。',
    tags: ['约束']
  },
  {
    id: 'q4',
    label: '听完以后，希望大家记住什么或采取什么行动？',
    short: '期望的行动',
    ring: 3,
    parent: 't1-1',
    children: [],
    method:
      '把「希望对方做什么」写成一个具体动作句，放在最后一页。没有行动句的 PPT 等于没讲。',
    conditions: '说服型 / 汇报型 PPT 的收口动作。',
    tags: ['目标']
  },

  /* ---------------- 其他第一圈层的少量示例（默认不展开） ---------------- */
  {
    id: 't2-1',
    label: '确认目标受众',
    short: '确认受众',
    ring: 2,
    parent: 't2',
    children: [],
    method: '先让 AI 列出「这份主题可能面对的三类人」，再从中勾选你真正的听众。',
    conditions: '主题覆盖面广、容易讲偏时使用。',
    tags: ['示例']
  },
  {
    id: 't2-2',
    label: '收集已有素材',
    short: '收集素材',
    ring: 2,
    parent: 't2',
    children: [],
    method: '把手上已有的资料丢给 AI，让它标出「哪些能直接用、哪些还需要补」。',
    conditions: '手头素材杂乱时使用。',
    tags: ['示例']
  },
  {
    id: 't3-1',
    label: '逐条确认章节',
    short: '逐条确认',
    ring: 2,
    parent: 't3',
    children: [],
    method: '一条一条过，每条只问「删了它会不会少讲一个关键点」。',
    conditions: '大纲偏长、需要砍内容时使用。',
    tags: ['示例']
  },
  {
    id: 't3-2',
    label: '调整章节顺序',
    short: '调整顺序',
    ring: 2,
    parent: 't3',
    children: [],
    method: '让 AI 用「结论先行 / 时间线 / 问题-方案」三种顺序各排一版，选最顺的。',
    conditions: '内容逻辑容易讲乱时使用。',
    tags: ['示例']
  },
  {
    id: 't4-1',
    label: '选定配色方案',
    short: '选定配色',
    ring: 2,
    parent: 't4',
    children: [],
    method: '一页只用一个主色 + 一个强调色，避免 AI 默认的「彩虹渐变」审美。',
    conditions: '需要专业、克制的视觉时使用。',
    tags: ['示例']
  },
  {
    id: 't4-2',
    label: '挑一套版式模板',
    short: '挑模板',
    ring: 2,
    parent: 't4',
    children: [],
    method: '先定 3 种版式（封面/要点/图配文），后续所有页面都从这三版变体。',
    conditions: '页数多、需要保持一致时使用。',
    tags: ['示例']
  },
  {
    id: 't5-1',
    label: '批量生成初稿',
    short: '批量生成',
    ring: 2,
    parent: 't5',
    children: [],
    method: '按确认好的大纲逐页生成，生成时把「风格描述」一起带上，避免风格漂移。',
    conditions: '大纲已定稿后使用。',
    tags: ['示例']
  },
  {
    id: 't5-2',
    label: '逐页微调排版',
    short: '逐页微调',
    ring: 2,
    parent: 't5',
    children: [],
    method: '每页只改三件事：删冗余字、换更准的词、调整信息层级。',
    conditions: '对成片质量有要求时使用。',
    tags: ['示例']
  },
  {
    id: 't6-1',
    label: '整理图片与顺序',
    short: '整理图片',
    ring: 2,
    parent: 't6',
    children: [],
    method: '先把图片按讲述顺序编号，再交给 AI 配说明文字。',
    conditions: '图片多、顺序乱时使用。',
    tags: ['示例']
  },
  {
    id: 't6-2',
    label: '生成图文页',
    short: '生成图文页',
    ring: 2,
    parent: 't6',
    children: [],
    method: '让 AI 以「一图一句核心结论」的方式生成图文页，避免堆砌。',
    conditions: '需要大量说明页时使用。',
    tags: ['示例']
  }
]

export const NODE_MAP = Object.fromEntries(NODES.map((n) => [n.id, n]))

/** 由某节点回溯到中心节点的完整路径（含两端） */
export function pathToCore(nodeId) {
  const chain = []
  let cur = NODE_MAP[nodeId]
  let guard = 0
  while (cur && guard++ < 20) {
    chain.unshift(cur)
    cur = cur.parent ? NODE_MAP[cur.parent] : null
  }
  return chain
}

/** 路径文本："定主题 › 主题收窄" */
export function pathLabel(nodeId) {
  return pathToCore(nodeId)
    .filter((n) => n.ring > 0)
    .map((n) => n.short)
    .join(' › ')
}
