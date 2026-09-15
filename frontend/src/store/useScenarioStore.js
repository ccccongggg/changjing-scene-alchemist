import { defineStore } from 'pinia'
import { ARTICLE, POSTS, NODE_MAP, pathToCore, pathLabel } from '../data/article'

/*
  ============================================================================
  三层数据逻辑（即使 Demo 也用同一套结构）
    第一层 原帖基准层：ARTICLE + NODES —— 只读、共享、不可被用户内容覆盖
    第二层 私人星图层：nodeStates / customBranches / plan —— 默认只对自己可见
    第三层 社区方案层：contributed —— 只有用户点「贡献」才进入
  ============================================================================
*/

const LS_KEY = 'nebula_demo_v1'

/* ---------------- AI 提示词提取 & 自动分类（演示版规则实现） ---------------- */
const KW_BANK = [
  '职场表达', '汇报', '立项', '管理层', '演示', 'PPT',
  'AI工具', '提示词', '效率', '自动化', '工作流',
  '学习方法', '复盘', '知识管理', '笔记', '框架',
  '硬件调试', '嵌入式', 'ESP32', '串口', '电路',
  '内容创作', '写作', '选题', '排版', '运营'
]

export function extractKeywords(text = '') {
  const hit = KW_BANK.filter((k) => text.includes(k))
  if (hit.length) return Array.from(new Set(hit)).slice(0, 5)
  // 没有命中词时，从文本里切几个有意义的短语兜底
  const parts = String(text)
    .split(/[，,。；;、\s\/]+/)
    .map((s) => s.trim())
    .filter((s) => s.length >= 2 && s.length <= 8)
    .slice(0, 3)
  return parts.length ? parts : ['场景适配']
}

const CLUSTERS = ['职场表达', 'AI工具', '学习方法', '硬件调试', '内容创作']
export function autoCluster(keywords = []) {
  const rules = [
    { name: '职场表达', keys: ['职场表达', '汇报', '立项', '管理层', '演示', 'PPT', '说服'] },
    { name: 'AI工具', keys: ['AI工具', '提示词', '效率', '自动化', '工作流', '模型'] },
    { name: '学习方法', keys: ['学习方法', '复盘', '知识管理', '笔记', '框架', '记忆'] },
    { name: '硬件调试', keys: ['硬件调试', '嵌入式', 'ESP32', '串口', '电路', '示波器'] },
    { name: '内容创作', keys: ['内容创作', '写作', '选题', '排版', '运营', '封面'] }
  ]
  let best = null
  let bestScore = 0
  for (const r of rules) {
    const s = r.keys.filter((k) => keywords.some((kw) => kw.includes(k) || k.includes(kw))).length
    if (s > bestScore) {
      bestScore = s
      best = r.name
    }
  }
  return best || 'AI工具'
}

/* ---------------- 种子数据：让 Demo 一打开就有内容 ---------------- */
function seedContributed() {
  const raw = [
    {
      id: 'c_seed_1',
      postId: 'ppt-ai-001',
      contributor: '我',
      isMine: true,
      title: '给不懂 AI 的管理层做 10 分钟立项汇报',
      sourcePost: '如何用 AI 做出高质量的 PPT',
      scene: '给不懂 AI 的管理层做 10 分钟项目汇报，争取立项',
      goal: '拿到项目立项所需的资源',
      limits: ['10 分钟', '听众无技术背景', '需当场决策'],
      steps: ['结论先行：第 1 页给结论与资源诉求', '3 点支撑：问题量化 + 方案 + 证据', '主动列 2 条风险并各给一句应对', '收口：明确要什么、给多久、何时看结果'],
      audience: '非技术背景的管理层',
      status: '已验证',
      saves: 42,
      adoptions: 17,
      feedbacks: 9,
      helped: 26,
      crossScene: true,
      createdAt: '2026-09-02'
    },
    {
      id: 'c_seed_2',
      postId: 'ppt-ai-001',
      contributor: '我',
      isMine: true,
      title: '用 AI 把 30 张产品截图整理成图文说明页',
      sourcePost: '如何用 AI 做出高质量的 PPT',
      scene: '手上 30 张产品截图，要整理成一份可发群的功能说明',
      goal: '3 小时内交付一份能直接发的说明页',
      limits: ['素材已有', '时间只有 3 小时'],
      steps: ['按讲述顺序给图片编号', '一图一句核心结论', '统一版式后批量生成'],
      audience: '客户 / 内部同事',
      status: '待验证',
      saves: 13,
      adoptions: 4,
      feedbacks: 2,
      helped: 6,
      crossScene: false,
      createdAt: '2026-09-05'
    },
    {
      id: 'c_seed_3',
      postId: 'embed-001',
      contributor: '我',
      isMine: true,
      title: '串口日志乱码排查的复用路径',
      sourcePost: '嵌入式调试经验合集',
      scene: 'ESP32 串口输出中文乱码，怀疑波特率或编码不一致',
      goal: '10 分钟内定位乱码原因',
      limits: ['无示波器', '需远程指导队友'],
      steps: ['核对波特率是否一致', '核对终端与固件编码', '最小复现隔离干扰源'],
      audience: '嵌入式新手',
      status: '已验证',
      saves: 28,
      adoptions: 11,
      feedbacks: 6,
      helped: 19,
      crossScene: true,
      createdAt: '2026-09-07'
    }
  ]
  return raw.map((c) => ({
    ...c,
    keywords: extractKeywords(c.scene + ' ' + c.goal + ' ' + c.steps.join(' ')),
    aiCategory: autoCluster(extractKeywords(c.scene + ' ' + c.steps.join(' '))),
    isSeed: true
  }))
}

/* 社区层的「其他用户」场景：出现在贡献地图的行星上，但不计入我的贡献统计 */
function seedCommunity() {
  const raw = [
    {
      id: 'u_seed_1',
      postId: 'ppt-ai-001',
      contributor: '@小林',
      isMine: false,
      title: '学生党用 AI 做课程汇报（只有免费额度）',
      scene: '免费额度每天 20 次，要做一份 8 页的课程汇报',
      goal: '额度用完前把汇报做出来',
      limits: ['免费额度 20 次/天', '零预算'],
      steps: ['先定大纲再动页面，省额度', '把 3 页压成 1 页长图', '最后一次性微调'],
      audience: '在校学生',
      status: '已验证',
      saves: 31,
      adoptions: 9,
      feedbacks: 5,
      helped: 22,
      crossScene: false,
      createdAt: '2026-09-03'
    },
    {
      id: 'u_seed_2',
      postId: 'ppt-ai-001',
      contributor: '@阿哲',
      isMine: false,
      title: '家长把绘本转成孩子能懂的 PPT',
      scene: '孩子 6 岁，要把绘本讲成一页一句话的图卡',
      goal: '让孩子自己看懂画面讲出故事',
      limits: ['零基础', '不要 AI 直接给答案'],
      steps: ['一句一页，先图后字', '删掉所有成人化措辞', '留一页让孩子自己复述'],
      audience: '学生家长',
      status: '待验证',
      saves: 12,
      adoptions: 3,
      feedbacks: 1,
      helped: 5,
      crossScene: false,
      createdAt: '2026-09-06'
    },
    {
      id: 'u_seed_3',
      postId: 'embed-001',
      contributor: '@Kevin',
      isMine: false,
      title: 'PCB 打样前的封装核对清单',
      scene: '打样前夜想快速核对一遍封装与引脚是否对错',
      goal: '避免因封装错误重打一次板',
      limits: ['时间紧', '不能改原理图'],
      steps: ['导出 BOM 与位号对照', '逐项核对封装尺寸', '重点核对极性器件'],
      audience: '硬件工程师',
      status: '已验证',
      saves: 24,
      adoptions: 8,
      feedbacks: 4,
      helped: 15,
      crossScene: true,
      createdAt: '2026-09-08'
    }
  ]
  return raw.map((c) => ({
    ...c,
    keywords: extractKeywords(c.scene + ' ' + c.goal + ' ' + c.steps.join(' ')),
    aiCategory: autoCluster(extractKeywords(c.scene + ' ' + c.steps.join(' '))),
    isSeed: true
  }))
}

function seedSaved() {
  return [
    {
      id: 's_seed_1',
      title: '10 分钟汇报的「3 点法则」',
      sourcePost: '如何用 AI 做出高质量的 PPT',
      scene: '时间受限的口头汇报',
      keywords: ['汇报', '职场表达', '演示'],
      category: '汇报',
      savedAt: '2026-09-06',
      postId: 'ppt-ai-001',
      nodeId: 'q3',
      isSeed: true
    },
    {
      id: 's_seed_2',
      title: '「结论先行」结构模板',
      sourcePost: '如何用 AI 做出高质量的 PPT',
      scene: '说服型 / 立项型汇报',
      keywords: ['职场表达', '立项', '框架'],
      category: '未分类',
      savedAt: '2026-09-08',
      postId: 'ppt-ai-001',
      nodeId: 't3',
      isSeed: true
    },
    {
      id: 's_seed_3',
      title: '串口乱码：先别怀疑固件，先核对两端配置',
      sourcePost: '嵌入式调试经验合集',
      scene: '嵌入式串口通信异常排查',
      keywords: ['硬件调试', '嵌入式', '串口'],
      category: '工具效率',
      savedAt: '2026-09-09',
      postId: 'embed-001',
      nodeId: 'core',
      isSeed: true
    }
  ]
}

/* ---------------- 初始 state ---------------- */
function initialState() {
  return {
    postId: ARTICLE.id,
    // 私人星图层：节点状态（不含"当前选中"，那是纯 UI 态）
    nodeStates: {}, // nodeId -> 'mastered' | 'pending' | 'adopted' | 'skipped'
    skipReasons: {}, // nodeId -> string
    expanded: ['core'], // 已展开下一圈层的分支（默认只展开中心，露出第一圈层）
    customBranches: [], // 采纳并锁定后长出的个人分支
    sceneSessions: {}, // nodeId -> { scene, keywords, result }
    plan: null, // 最终场景方案
    // 社区层
    contributed: seedContributed(),
    // 其他用户提交的真实场景（贡献地图的行星，不计入我的统计）
    community: seedCommunity(),
    // 私人收藏层（我点赞的）
    saved: seedSaved(),
    userCategories: ['汇报', '工具效率'],
    // 私人方案分享偏好（贡献前必须由用户选择）
    shareMark: null // 'ai_only' | 'verified'
  }
}

function load() {
  try {
    const raw = localStorage.getItem(LS_KEY)
    if (raw) {
      const parsed = JSON.parse(raw)
      // 用 seed 兜底，避免旧数据缺字段
      return { ...initialState(), ...parsed }
    }
  } catch (e) {
    /* ignore */
  }
  return initialState()
}

export const useScenarioStore = defineStore('scenario', {
  state: () => load(),

  getters: {
    /* ---- 原帖基准层（只读共享） ---- */
    article: () => ARTICLE,
    nodes: () => Object.values(NODE_MAP),

    /* ---- 派生：各类节点集合 ---- */
    masteredNodes: (s) =>
      Object.keys(s.nodeStates).filter((id) => s.nodeStates[id] === 'mastered'),
    pendingNodes: (s) =>
      Object.keys(s.nodeStates).filter((id) => s.nodeStates[id] === 'pending'),
    skippedNodes: (s) =>
      Object.keys(s.nodeStates).filter((id) => s.nodeStates[id] === 'skipped'),

    /* ---- 黄金路径完成度 ---- */
    doneCount() {
      return this.masteredNodes.length + this.customBranches.length
    },
    // 至少完成一条路径 + 没有未处理的关键疑问(待适配)
    planReady() {
      return this.doneCount > 0 && this.pendingNodes.length === 0
    },

    /* ---- 我贡献的：AI 自动分类星团 ---- */
    contributionClusters: (s) => {
      const map = {}
      for (const c of s.contributed) {
        const k = c.aiCategory || 'AI工具'
        ;(map[k] = map[k] || []).push(c)
      }
      return CLUSTERS.filter((c) => map[c]).map((name) => ({
        name,
        items: map[name]
      })).concat(
        Object.keys(map)
          .filter((k) => !CLUSTERS.includes(k))
          .map((name) => ({ name, items: map[name] }))
      )
    },
    contributionStats: (s) => ({
      contributed: s.contributed.length,
      verified: s.contributed.filter((c) => c.status === '已验证').length,
      helped: s.contributed.reduce((a, c) => a + (c.helped || 0), 0)
    }),

    /*
      贡献地图（三层结构）：
        L0 太阳 = 我收藏的知乎原帖（saved 里出现过的 postId）
        L1 行星 = 不同用户在该原帖下提交的真实场景（含我自己的，用 isMine 区分）
        L2 卫星 = 该真实场景的执行步骤
    */
    galaxy: (s) => {
      const postIds = []
      for (const it of s.saved) {
        if (it.postId && !postIds.includes(it.postId)) postIds.push(it.postId)
      }
      const all = [...s.contributed, ...s.community]
      return postIds
        .map((pid) => ({
          post: POSTS[pid] || { id: pid, title: pid, author: '' },
          planets: all.filter((c) => c.postId === pid)
        }))
        .filter((g) => g.planets.length)
    },

    /*
      奖章：形状 = 做到了什么（称号）　材质 = 做到多深（铜 / 银 / 金 三档）
      每枚返回：
        key / name / form(形态名) / desc / unit / metric
        tiers: [铜线, 银线, 金线]
        value: 当前值
        tier: 'none' | 'bronze' | 'silver' | 'gold'
        nextVal: 下一档阈值（金档或满级为 null）
        remaining: 距下一档还差多少
        progress: 距下一档的进度 0~1（满级为 1）
        lines: 三档明细 [{ name, value, got }]，给背面用
        action: { label, to }
    */
    badges: (s) => {
      const cs = s.contributed
      const helped = cs.reduce((a, c) => a + (c.helped || 0), 0)
      const distinctClusters = new Set(cs.map((c) => c.aiCategory)).size
      const perPost = cs.reduce((m, c) => {
        m[c.sourcePost] = (m[c.sourcePost] || 0) + 1
        return m
      }, {})
      const postCounts = Object.values(perPost)
      const samePostMax = postCounts.length ? Math.max.apply(null, postCounts) : 0
      const crossScene = cs.filter((c) => c.crossScene).length

      const defs = [
        {
          key: 'first',
          name: '初次贡献者',
          form: '起点星',
          desc: '完成第一次贡献',
          metric: '方案数',
          unit: '个方案',
          value: cs.length,
          tiers: [1, 3, 10],
          action: { label: '去星云图贡献', to: '/nebula' }
        },
        {
          key: 'allrounder',
          name: '多面手',
          form: '八棱切面',
          desc: '贡献覆盖 3 个以上领域',
          metric: '覆盖领域数',
          unit: '个领域',
          value: distinctClusters,
          tiers: [3, 4, 5],
          action: { label: '去星云图换个领域', to: '/nebula' }
        },
        {
          key: 'onepost',
          name: '一帖多吃',
          form: '分水口',
          desc: '同一篇帖子产出多个方案',
          metric: '同帖最多方案数',
          unit: '个方案',
          value: samePostMax,
          tiers: [2, 4, 8],
          action: { label: '去星云图再炼一版', to: '/nebula' }
        },
        {
          key: 'cross',
          name: '跨界破壁',
          form: '断环穿星',
          desc: '方案被跨场景验证',
          metric: '跨场景验证数',
          unit: '个方案',
          value: crossScene,
          tiers: [1, 4, 10],
          action: { label: '去星云图做跨场景验证', to: '/nebula' }
        },
        {
          key: 'helpful',
          name: '助人为乐',
          form: '双托星',
          desc: '帮助人数累计到线',
          metric: '帮助人数',
          unit: '人',
          value: helped,
          tiers: [20, 50, 200],
          action: { label: '去方案库看看被采纳的', to: '/library' }
        }
      ]

      return defs.map((d) => {
        const bronze = d.tiers[0]
        const silver = d.tiers[1]
        const gold = d.tiers[2]
        const tier =
          d.value >= gold ? 'gold' : d.value >= silver ? 'silver' : d.value >= bronze ? 'bronze' : 'none'
        const nextVal = d.value >= gold ? null : d.value >= silver ? gold : d.value >= bronze ? silver : bronze
        const progress = nextVal ? Math.min(1, d.value / nextVal) : 1
        const remaining = nextVal ? Math.max(0, nextVal - d.value) : 0
        return {
          ...d,
          tier,
          nextVal,
          remaining,
          progress,
          lines: ['铜', '银', '金'].map((nm, i) => ({
            name: nm,
            value: d.tiers[i],
            got: d.value >= d.tiers[i]
          }))
        }
      })
    },

    /* ---- 我点赞的：按用户自定义分类分组 ---- */
    savedGroups: (s) => {
      const groups = [{ name: '全部', items: s.saved }]
      const cats = [...s.userCategories]
      const hasUncategorized = s.saved.some((x) => !x.category || x.category === '未分类')
      if (hasUncategorized) cats.push('未分类')
      for (const c of cats) {
        groups.push({
          name: c,
          items: s.saved.filter((x) =>
            c === '未分类' ? !x.category || x.category === '未分类' : x.category === c
          )
        })
      }
      return groups
    }
  },

  actions: {
    persist() {
      try {
        localStorage.setItem(LS_KEY, JSON.stringify(this.$state))
      } catch (e) {
        /* ignore */
      }
    },

    /* ================= 第二层：私人星图层操作 ================= */
    toggleExpand(nodeId) {
      const i = this.expanded.indexOf(nodeId)
      if (i >= 0) this.expanded.splice(i, 1)
      else this.expanded.push(nodeId)
      this.persist()
    },
    isExpanded(nodeId) {
      return this.expanded.includes(nodeId)
    },

    setMastered(nodeId) {
      if (this.nodeStates[nodeId] === 'mastered') delete this.nodeStates[nodeId]
      else {
        this.nodeStates[nodeId] = 'mastered'
        delete this.skipReasons[nodeId]
      }
      this.persist()
    },

    markPending(nodeId, sceneText) {
      this.nodeStates[nodeId] = 'pending'
      if (sceneText) this.sceneSessions[nodeId] = { scene: sceneText }
      this.persist()
    },
    clearPending(nodeId) {
      if (this.nodeStates[nodeId] === 'pending') delete this.nodeStates[nodeId]
      this.persist()
    },
    setSceneResult(nodeId, session) {
      this.sceneSessions[nodeId] = { ...(this.sceneSessions[nodeId] || {}), ...session }
      this.persist()
    },

    skipNode(nodeId, reason) {
      this.nodeStates[nodeId] = 'skipped'
      this.skipReasons[nodeId] = reason || '与我的场景无关'
      this.persist()
    },
    unskipNode(nodeId) {
      if (this.nodeStates[nodeId] === 'skipped') delete this.nodeStates[nodeId]
      delete this.skipReasons[nodeId]
      this.persist()
    },

    /* ---- 采纳并锁定：从原帖节点长出个人分支 ---- */
    adoptBranch(nodeId, payload) {
      const id = 'b_' + Date.now().toString(36)
      const path = pathLabel(nodeId)
      this.customBranches.push({
        id,
        fromNodeId: nodeId,
        fromPath: path,
        title: payload.title || '我的适配方案',
        scene: payload.scene || '',
        goal: payload.goal || '',
        limits: payload.limits || [],
        steps: payload.steps || [],
        sources: payload.sources || [],
        risks: payload.risks || [],
        locked: true,
        createdAt: new Date().toISOString().slice(0, 10)
      })
      this.nodeStates[nodeId] = 'adopted'
      delete this.skipReasons[nodeId]
      this.persist()
      return id
    },
    undoAdopt(branchId) {
      const b = this.customBranches.find((x) => x.id === branchId)
      this.customBranches = this.customBranches.filter((x) => x.id !== branchId)
      if (b && this.nodeStates[b.fromNodeId] === 'adopted') {
        // 恢复为"待适配"（这条路径曾经疑惑过）
        this.nodeStates[b.fromNodeId] = 'pending'
      }
      this.persist()
    },

    /* ================= 最终场景方案 ================= */
    generatePlan() {
      if (!this.planReady) return null
      const scene = this.pickScene()
      const limits = this.collectLimits()
      const methods = this.masteredNodes.map((id) => {
        const n = NODE_MAP[id]
        return { path: pathLabel(id), label: n.short, method: n.method, conditions: n.conditions }
      })
      const unfitted = [
        ...this.skippedNodes.map((id) => ({
          label: NODE_MAP[id].short,
          reason: this.skipReasons[id] || '与我的场景无关'
        })),
        ...this.pendingNodes.map((id) => ({
          label: NODE_MAP[id].short,
          reason: '关键疑问，尚未找到适配方案'
        }))
      ]
      const steps = []
      for (const b of this.customBranches) {
        for (const s of b.steps) steps.push({ from: b.title, text: s })
      }
      const sources = []
      for (const b of this.customBranches) {
        for (const s of b.sources) sources.push(s)
      }
      const risks = []
      for (const b of this.customBranches) for (const r of b.risks) risks.push(r)
      if (!risks.length) {
        risks.push('本方案由 AI 依公开经验整理，尚未在你的真实场景中实践验证。')
      }
      this.plan = {
        article: { title: ARTICLE.title, author: ARTICLE.author, source: ARTICLE.sourceLabel },
        scene,
        goal: this.collectGoal(),
        limits,
        methods,
        unfitted,
        steps,
        sources,
        risks,
        generatedAt: new Date().toISOString().slice(0, 16).replace('T', ' ')
      }
      this.persist()
      return this.plan
    },

    pickScene() {
      const first = Object.values(this.sceneSessions).find((x) => x.scene)
      return first ? first.scene : '（未填写具体场景）'
    },
    collectGoal() {
      const g = this.customBranches.find((b) => b.goal)
      return g ? g.goal : '把原帖方法迁移到我的场景里，得到一份能直接执行的方案。'
    },
    collectLimits() {
      const set = new Set()
      for (const b of this.customBranches) for (const l of b.limits) set.add(l)
      for (const sess of Object.values(this.sceneSessions)) {
        for (const k of sess.keywords || []) set.add(k)
      }
      return Array.from(set).slice(0, 8)
    },

    /* ================= 第三层：社区方案层 ================= */
    setShareMark(m) {
      this.shareMark = m
      this.persist()
    },

    /** 保存到「我点赞的」（私人，不公开） */
    saveToLiked(category) {
      if (!this.plan) return
      const kws = extractKeywords(
        this.plan.scene + ' ' + this.plan.limits.join(' ') + ' ' + this.plan.methods.map((m) => m.label).join(' ')
      )
      this.saved.unshift({
        id: 's_' + Date.now().toString(36),
        title: this.plan.goal || ARTICLE.title + ' · 我的场景方案',
        sourcePost: ARTICLE.title,
        scene: this.plan.scene,
        keywords: kws,
        category: category || '未分类',
        suggested: autoCluster(kws), // AI 建议分类（仅供参考）
        savedAt: new Date().toISOString().slice(0, 10),
        postId: ARTICLE.id,
        nodeId: this.customBranches[0]?.fromNodeId || 'core',
        planSnapshot: JSON.parse(JSON.stringify(this.plan))
      })
      this.persist()
    },

    /** 贡献到「我贡献的」（进入社区层，需先标记来源） */
    contribute() {
      if (!this.plan) return null
      const kws = extractKeywords(
        this.plan.scene + ' ' + this.plan.limits.join(' ') + ' ' + this.plan.steps.map((s) => s.text).join(' ')
      )
      const item = {
        id: 'c_' + Date.now().toString(36),
        title: this.plan.goal || '我的场景方案',
        sourcePost: ARTICLE.title,
        scene: this.plan.scene,
        goal: this.plan.goal,
        limits: this.plan.limits,
        steps: this.plan.steps.map((s) => s.text),
        audience: '（待补充）',
        status: this.shareMark === 'verified' ? '已验证' : '待验证',
        mark: this.shareMark || 'ai_only',
        keywords: kws,
        aiCategory: autoCluster(kws),
        saves: 0,
        adoptions: 0,
        feedbacks: 0,
        helped: 0,
        crossScene: false,
        createdAt: new Date().toISOString().slice(0, 10),
        review: this.mockReview(kws) // 机器预审（模拟）
      }
      this.contributed.unshift(item)
      this.persist()
      return item
    },

    /** 机器预审（至少模拟五项检查） */
    mockReview() {
      const p = this.plan || {}
      const hasSteps = (p.steps || []).length >= 2
      const hasScene = !!(p.scene && p.scene !== '（未填写具体场景）')
      const hasSource = (p.sources || []).length > 0 || true
      const dup = this.contributed.some((c) => c.title === (p.goal || ''))
      const risky = /(作弊|破解|绕过|违规|内网渗透)/.test(JSON.stringify(p))
      return [
        { key: 'scene', label: '场景是否完整', pass: hasScene },
        { key: 'dup', label: '是否与已有方案重复', pass: !dup },
        { key: 'steps', label: '是否包含可执行步骤', pass: hasSteps },
        { key: 'source', label: '是否标记内容来源', pass: hasSource },
        { key: 'risk', label: '是否包含明显风险内容', pass: !risky }
      ]
    },

    /** 用户反馈「分类不准确」——只记录，不改变自动分类的主导权 */
    flagCategoryInaccurate(id) {
      const c = this.contributed.find((x) => x.id === id)
      if (c) c.categoryFlagged = true
      this.persist()
    },

    /* ================= 我点赞的：用户自定义分类管理 ================= */
    addCategory(name) {
      const n = (name || '').trim()
      if (!n || n === '全部' || n === '未分类' || this.userCategories.includes(n)) return false
      this.userCategories.push(n)
      this.persist()
      return true
    },
    renameCategory(oldName, newName) {
      const n = (newName || '').trim()
      if (!n || n === '全部' || n === '未分类') return false
      const i = this.userCategories.indexOf(oldName)
      if (i < 0) return false
      this.userCategories[i] = n
      for (const s of this.saved) if (s.category === oldName) s.category = n
      this.persist()
      return true
    },
    deleteCategory(name) {
      this.userCategories = this.userCategories.filter((c) => c !== name)
      for (const s of this.saved) if (s.category === name) s.category = '未分类'
      this.persist()
    },
    mergeCategory(from, to) {
      if (from === to) return
      for (const s of this.saved) if (s.category === from) s.category = to
      this.userCategories = this.userCategories.filter((c) => c !== from)
      this.persist()
    },
    moveToCategory(id, category) {
      const s = this.saved.find((x) => x.id === id)
      if (s) s.category = category
      this.persist()
    },
    toggleLike(id) {
      this.saved = this.saved.filter((x) => x.id !== id)
      this.persist()
    },

    /* ================= 重置演示 ================= */
    resetDemo() {
      const init = initialState()
      Object.keys(init).forEach((k) => {
        this[k] = init[k]
      })
      this.persist()
    }
  }
})
