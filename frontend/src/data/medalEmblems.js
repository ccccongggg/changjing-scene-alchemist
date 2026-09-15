/*
  奖章 = 徽记（做到了什么） × 材质（做到多深）
  ------------------------------------------------------------------
  MEDAL_ART: 五枚徽记的图片，AI 生成的「知乎生奖章」，已裁成 512² 圆盘（见 _medal_src/make.py）
  TONES    : 四态材质（未获得 / 铜 / 银 / 金）
  TIER_META: 档位的文案

  图片放 public/medals/，用 URL 而不是 import：纯静态站直接拷过去，
  换图不用动构建配置；文件名与徽记语义一一对应。
*/

/* 徽记 → 奖章 key。按**含义**配，不按图片序号配：
     初次贡献者（起点星 · 完成第一次贡献，看的是成长） → 知识黑马「成长迅速」
     多面手　　（覆盖多个领域，靠的是看得清）        → 洞察先锋「观点清晰」
     一帖多吃　（同一帖产出多个方案，本质是创作）    → 创作新星「风格鲜明」
     跨界破壁　（跨场景验证，讲得通道理）            → 逻辑答主「表达有逻辑」
     助人为乐　（帮助人数累计）                      → 口碑推荐「值得分享」
   要换顺序只改这张表。key 必须与 store 里 badges[].key 一致。 */
export const MEDAL_ART = {
  first: '/medals/darkhorse.webp',
  allrounder: '/medals/insight.webp',
  onepost: '/medals/creator.webp',
  cross: '/medals/logic.webp',
  helpful: '/medals/praise.webp'
}

/* 材质只管「奖章外圈那一道环 + 名字饰带 + 卡面底色」，徽记本体是图片。
   所以 plate / inner / emblem* / highlight 这些「画 SVG 底盘」的字段全部删掉了 ——
   它们曾经存在过，但自从徽记换成图片就再没有一处读取。 */
export const TONES = {
  none: {
    ring: '#5F5E5A',
    ringDash: true,
    ringWidth: 3,
    muted: true, // 图片去色
    ribbonBg: 'linear-gradient(180deg, #e4e4e1, #cdcdc8)',
    ribbonFg: '#6b6b66',
    ribbonLine: '#bcbcb6',
    accent: '#888780',
    cardBg: 'var(--surface-2)',
    shine: false
  },
  bronze: {
    ring: '#BA7517',
    ringDash: true,
    ringWidth: 3.2,
    muted: false,
    ribbonBg: 'linear-gradient(180deg, #8a5410, #5d3808)',
    ribbonFg: '#FFE7C2',
    ribbonLine: '#BA7517',
    accent: '#BA7517',
    cardBg: '#fdf6ec',
    shine: true
  },
  silver: {
    ring: '#B4B2A9',
    ringDash: true,
    ringWidth: 3.2,
    muted: false,
    ribbonBg: 'linear-gradient(180deg, #8d8d86, #5b5b55)',
    ribbonFg: '#F4F3EE',
    ribbonLine: '#D3D1C7',
    accent: '#8f8f88',
    cardBg: '#f6f6f7',
    shine: true
  },
  gold: {
    ring: '#FAC775',
    ringDash: false,
    ringWidth: 3.4,
    muted: false,
    ribbonBg: 'linear-gradient(180deg, #c8892a, #8a5410)',
    ribbonFg: '#FFF6E2',
    ribbonLine: '#FAC775',
    accent: '#E7B873',
    cardBg: '#fffaf0',
    shine: true
  }
}

export const TIER_META = {
  none: { short: '未获得', full: '未获得', rank: 0 },
  bronze: { short: '铜', full: '铜牌 · 第 1 档', rank: 1 },
  silver: { short: '银', full: '银牌 · 第 2 档', rank: 2 },
  gold: { short: '金', full: '金牌 · 第 3 档', rank: 3 }
}

export const TIER_KEYS = ['none', 'bronze', 'silver', 'gold']
export const TIER_NAMES = ['铜', '银', '金']
