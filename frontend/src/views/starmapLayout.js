/*
  星图布局：纯函数，不依赖 Vue / DOM。
  ------------------------------------------------------------------
  抽出来的原因：星盘尺寸、字号、标签位置全是「约束反推」出来的算术，
  放在 .vue 里只能靠肉眼截图验证（agent-browser 一挂就瞎了）。
  抽成纯模块后可以直接喂真实场景数据跑几何断言 —— 有没有越界、标签会不会互压，
  毫秒级能算出来，不用浏览器。体检脚本见 frontend/_starmap_geom_check.mjs。

  坐标系约定：1 SVG 单位 ≈ 1 屏幕像素（viewBox 跟随舞台像素尺寸），
  所以这里的字号就是真实字号，标签占位宽度也按真实字号估。

  ⚠️ 标签是「恒定屏幕字号」：.lbl 被 wrapT + lblT 两层 scale(1/√k) 包住，
  正好抵消外层 scale(k)。所以它永远 14px、偏移永远 14px，不随缩放变化。
  星点只抵消掉一层，所以随 √k 变大。bboxAt 按这个规律算，别当成「一起缩放」。
*/

export const LAYOUT_DEFAULTS = {
  starOut: 24, // 星点整体外扩，避开中心星核
  starJit: 12, // 方位抖动上限，让轨道不完全规整
  labelOff: 14, // 标签相对星点的水平偏移
  labelFs: 14, // 标签字号（须与 CSS .lbl 一致）
  labelDetailOff: 14, // 第二行（状态 · 相似人数）相对第一行的下沉量（须与 detT 一致）
  labelAsc: 7, // 第一行中心往上的高度（14px 字 ≈ 半行高）
  labelDesc: 20, // 两行时块底边相对第一行中心的下沉（第二行 11.5px 字，中心在 +14）
  labelDesc1: 7, // 只有一行时的块底边
  minDist: 106, // 两星最小间距（px），relaxAngles 的收敛目标
  squashMin: 0.5, // 纵向压扁系数下限 —— 太扁就不像盘子了
  squashMax: 0.92, // 上限 —— 超过这个数盘子接近正圆，失去「倾斜星盘」的意象
  ringRatio: [0.62, 0.81, 1], // 三层轨道半径 / 最外圈半径
  sunRatio: 0.3, // 星核半径 / 最外圈半径
  sunMin: 22,
  sunMax: 96,
  sunGap: 6, // 星核实体与最内圈星点之间至少留的缝
  sunCompactR: 56, // 星核半径小于这个值就不摆三行字了，只留一个「★ N」
  starRatio: 0.06, // 星点半径 / 最外圈半径
  starMin: 9,
  starMax: 20,
  minRadius: 62, // 最外圈半径下限（小屏也不能塌成一个点）
  fitPad: 36,
  kMin: 0.45,
  kMax: 1.7,
  overlapArea: 24, // 判定「标签互压」的最小重叠面积（px²），容忍一点点擦边
  /* 排布模式：
     branch —— 按 branch 分扇区、同分支聚在一起（「一帖千面」星图：同路线的处境要挨着）
     even   —— 按列表顺序均分整圈（「解决步骤」星图：第 1 步在正上方，顺时针往下走）*/
  spread: 'branch'
}

export const DEPTH_NAME = ['', '改参数', '动结构', '换方案']

/* 标签档位：越靠后越省地方。
   full＝名字 + 「已做成 · N人相似」；name＝只名字；bare＝不摆标签（点/悬停时才看）。 */
export const LABEL_MODES = ['full', 'name', 'bare']

const RAD = Math.PI / 180

/** 八芒星 path（外半径 R，内半径 r），尖角朝上 */
export function starPath(R, r) {
  const p = []
  for (let i = 0; i < 8; i++) {
    const a = (-90 + i * 45) * RAD
    const rad = i % 2 === 0 ? R : r
    p.push((Math.cos(a) * rad).toFixed(2) + ' ' + (Math.sin(a) * rad).toFixed(2))
  }
  return 'M' + p.join(' L') + ' Z'
}

/** 星点标签文案：同名处境出了第二版就带上版本号 */
export function starLabel(n) {
  return (n.version || 1) > 1 ? `${n.name} · 第${n.version}版` : n.name
}

function truncate(s, n) {
  const t = String(s)
  return t.length <= n ? t : t.slice(0, Math.max(n - 1, 1)) + '…'
}

/** 标签估宽（中文字宽 ≈ 字号，ASCII 按 0.55 折） */
export function labelWidth(label, fs = LAYOUT_DEFAULTS.labelFs) {
  let w = 0
  for (const ch of String(label)) w += /[\u4e00-\u9fa5\u3000-\u303f\uff00-\uffef]/.test(ch) ? fs : fs * 0.55
  return w + 10
}

/**
 * 标签挂哪一侧。
 * 贴近水平 → 左右排（start / end 对齐）；贴近垂直 → 上下排（居中）。
 * 旧版一律左右排，标签全挤在左右两条竖带上，顶部/底部的空间白占。
 */
export function labelSide(ang, starSz, labelOff = LAYOUT_DEFAULTS.labelOff) {
  const cos = Math.cos(ang * RAD)
  const sin = Math.sin(ang * RAD)
  if (Math.abs(cos) * 1.15 >= Math.abs(sin)) {
    return { dx: cos >= 0 ? labelOff : -labelOff, dy: 0, anchor: cos >= 0 ? 'start' : 'end' }
  }
  // 星在下半圈 → 标签挂它下面；星在上半圈 → 标签挂它上面
  return sin >= 0
    ? { dx: 0, dy: starSz + 12, anchor: 'middle' }
    : { dx: 0, dy: -(starSz + 26), anchor: 'middle' }
}

/**
 * 角度松弛：反复把挨太近的两颗星推开，直到都 ≥ minDist。
 *
 * ⚠️ 距离必须按**压扁后**的真实坐标算（y 乘 squash）。
 * 旧版用未压扁的圆坐标，等于按「正圆」推，而渲染出来是椭盘 ——
 * 纵向实际间距只有它以为的一半，看着就挤在一起了。
 *
 * ⚠️ 两条防震荡的护栏（小盘面踩出来的）：
 *   ① fitReach —— 一圈的总弧长是有限的（2πr）。5 颗星要塞 106px 间距，
 *      而内圈周长只有 390px 时，**这个目标物理上不存在**。旧版不管这个，
 *      硬推到角度累加到 -18569° 还撞满 240 次迭代上限，结果既没收敛、顺序也乱了。
 *   ② MAX_STEP —— 半径很小时 ds→dθ 的换算会把单次修正放大成几十度，
 *      钳住每次 8°，让迭代真的收敛而不是来回弹。
 *
 * opts.keepOrder：推挤是「多对同时作用」，某颗星可能被邻居顶过第三颗。
 * 顺序在「解决步骤」星图里是语义（第 1 步 → 第 5 步顺时针），所以那边要开这个开关。
 */
export function relaxAngles(pos, cx, cy, minDist, squash = 1, opts = {}) {
  const n = pos.length
  if (n < 2) return
  const yAt = (o) => cy + o.r * Math.sin(o.ang * RAD) * squash
  const xAt = (o) => cx + o.r * Math.cos(o.ang * RAD)

  let want = minDist
  if (opts.fitReach) {
    let rMin = Infinity
    for (const o of pos) rMin = Math.min(rMin, o.r)
    want = Math.min(minDist, ((2 * Math.PI * Math.max(rMin, 1)) / n) * 0.92)
  }

  const MAX_STEP = 8 // °/次迭代
  for (let it = 0; it < 240; it++) {
    let moved = false
    for (let a = 0; a < n; a++) {
      for (let b = a + 1; b < n; b++) {
        const A = pos[a]
        const B = pos[b]
        const d = Math.hypot(xAt(B) - xAt(A), yAt(B) - yAt(A))
        if (d >= want || d < 0.001) continue
        moved = true
        const half = (want - d) * 0.55
        const da = Math.min(MAX_STEP, half / Math.max(A.r * RAD, 1))
        const db = Math.min(MAX_STEP, half / Math.max(B.r * RAD, 1))
        if (A.ang < B.ang) {
          A.ang -= da
          B.ang += db
        } else {
          A.ang += da
          B.ang -= db
        }
      }
    }
    if (!moved) break
  }

  /* 顺序保护：按原索引顺序重新分配「排好序的角度」。
     只改「谁用哪个角度」，半径（也就是深度环）不动，所以间距质量不受影响。 */
  if (opts.keepOrder) {
    const angs = pos.map((o) => o.ang).sort((a, b) => a - b)
    pos.forEach((o, i) => {
      o.ang = angs[i]
    })
  }

  /* 整体平移回 360° 内 —— 必须整组一起移，逐个取模会把「跨 ±180 的两颗星」挤到一起。
     对渲染没影响（sin/cos 只认相对角），但调试时不会再看到 -18569° 这种吓人的数。 */
  const mid = pos.reduce((s, o) => s + o.ang, 0) / n
  const shift = Math.round(mid / 360) * 360
  if (shift !== 0) pos.forEach((o) => { o.ang -= shift })
}


/** 在现有星之间找最大角度空档 —— 新星插这里最不挤 */
export function findDraftAngle(list) {
  if (!list.length) return -90
  const angs = list.map((n) => n.ang).sort((a, b) => a - b)
  let maxGap = 0
  let insertAt = -90
  for (let i = 0; i < angs.length; i++) {
    const cur = angs[i]
    const next = angs[(i + 1) % angs.length]
    const gap = ((next - cur + 360) % 360) || 360
    if (gap > maxGap) {
      maxGap = gap
      insertAt = cur + gap / 2
    }
  }
  return insertAt
}

/** 一个标签在最终屏幕坐标里的矩形 */
export function labelRect(n, k, cfg = LAYOUT_DEFAULTS) {
  if (!n.lbl || !n.lbl.w) return null
  const lx = n.x * k + n.dx
  const ly = n.y * k + n.dy
  const left = n.anchor === 'start' ? lx : n.anchor === 'end' ? lx - n.lbl.w : lx - n.lbl.w / 2
  return { l: left, r: left + n.lbl.w, t: ly + n.lbl.top, b: ly + n.lbl.bot }
}

/**
 * 在某个缩放 k 下，整张图（星点 + 标签）的真实屏幕包围盒。
 * 标签恒定字号 → 位置随 k 走、尺寸不随 k 走；星点随 √k 变大。
 * 旧版 fitView 把标签当成「跟着 k 一起缩小」，于是 k<1 时严重低估占位，缩放到边界后标签会溢出画布。
 */
export function bboxAt(nodes, starSz, k, cfg = LAYOUT_DEFAULTS) {
  let minX = Infinity
  let maxX = -Infinity
  let minY = Infinity
  let maxY = -Infinity
  const sr = starSz * Math.sqrt(k)
  nodes.forEach((n) => {
    const px = n.x * k
    const py = n.y * k
    minX = Math.min(minX, px - sr)
    maxX = Math.max(maxX, px + sr)
    minY = Math.min(minY, py - sr)
    maxY = Math.max(maxY, py + sr)
    const r = labelRect(n, k, cfg)
    if (!r) return
    minX = Math.min(minX, r.l - 3)
    maxX = Math.max(maxX, r.r + 3)
    minY = Math.min(minY, r.t)
    maxY = Math.max(maxY, r.b)
  })
  return { minX, maxX, minY, maxY, w: maxX - minX, h: maxY - minY }
}

/**
 * 求「把整张图放进舞台」的最大缩放 k。
 * bbox 随 k 单调变大，所以直接二分。
 */
export function fitScale(nodes, starSz, vbW, vbH, cfg = LAYOUT_DEFAULTS) {
  const pad = cfg.fitPad
  const W = Math.max(vbW - pad * 2, 1)
  const H = Math.max(vbH - pad * 2, 1)
  const fits = (k) => {
    const b = bboxAt(nodes, starSz, k, cfg)
    return b.w <= W && b.h <= H
  }
  if (!fits(cfg.kMin)) return cfg.kMin // 极小屏兜底：连最小缩放都塞不下，只能接受溢出
  let lo = cfg.kMin
  let hi = cfg.kMax
  for (let i = 0; i < 26; i++) {
    const mid = (lo + hi) / 2
    if (fits(mid)) lo = mid
    else hi = mid
  }
  return lo
}

/** 标签互压对数（只统计真正摆出来的标签） */
export function countLabelOverlaps(nodes, k, cfg = LAYOUT_DEFAULTS) {
  const rects = nodes.map((n) => labelRect(n, k, cfg)).filter(Boolean)
  let c = 0
  for (let a = 0; a < rects.length; a++) {
    for (let b = a + 1; b < rects.length; b++) {
      const A = rects[a]
      const B = rects[b]
      const ox = Math.min(A.r, B.r) - Math.max(A.l, B.l)
      const oy = Math.min(A.b, B.b) - Math.max(A.t, B.t)
      if (ox > 0 && oy > 0 && ox * oy > cfg.overlapArea) c++
    }
  }
  return c
}

/** 最近的两颗星相距多少（看星点本身会不会叠在一起） */
export function minStarGap(nodes) {
  let min = Infinity
  for (let a = 0; a < nodes.length; a++) {
    for (let b = a + 1; b < nodes.length; b++) {
      min = Math.min(min, Math.hypot(nodes[b].x - nodes[a].x, nodes[b].y - nodes[a].y))
    }
  }
  return isFinite(min) ? min : Infinity
}

/** 摆位：按 branch 分扇区 → 组内按 depth 铺开 → 角度松弛 → 定标签朝向与文案 */
function place({ scenes, vbW, vbH, cfg, mode }) {
  const cx = vbW / 2
  const cy = vbH / 2
  const list = scenes || []
  const N = list.length

  // 标签能写多长：横向留给标签的半宽 / 字号
  const halfRoom = Math.max(vbW / 2 - (cfg.starOut + cfg.starJit + cfg.labelOff), 0)
  const maxChars = Math.max(3, Math.min(16, Math.floor(halfRoom / cfg.labelFs)))
  const showLabels = mode !== 'bare'
  const showDetail = mode === 'full'

  const lblOf = (sc) => {
    if (!showLabels) return { text: '', w: 0, show: false, detail: false, top: 0, bot: 0 }
    const text = truncate(starLabel(sc), maxChars)
    return {
      text,
      w: labelWidth(text, cfg.labelFs),
      show: true,
      detail: showDetail,
      top: -cfg.labelAsc,
      bot: showDetail ? cfg.labelDesc : cfg.labelDesc1
    }
  }

  // 标签横向占位：按最长的一条估（短标签的帖子能多拿一圈半径）
  let maxLbl = cfg.labelFs * 5
  list.forEach((sc) => {
    const w = lblOf(sc).w
    if (w > maxLbl) maxLbl = w
  })
  const labelRoom = showLabels ? maxLbl : 0

  // 横向可达半径
  const r3h = Math.max(cfg.minRadius, vbW / 2 - (cfg.starOut + cfg.starJit + cfg.labelOff + labelRoom))

  // 纵向压扁系数自适应：把盘子撑满舞台高度（旧版固定 0.5，上下各留一大片白）
  const squash = Math.min(cfg.squashMax, Math.max(cfg.squashMin, (vbH / 2 - 34) / Math.max(r3h + cfg.starOut + cfg.starJit, 1)))

  // 再被纵向约束收一次
  const vertical = (vbH / 2 - 30) / squash - (cfg.starOut + cfg.starJit)
  const r3 = Math.max(cfg.minRadius, Math.min(r3h, vertical))
  const ring = { 1: r3 * cfg.ringRatio[0], 2: r3 * cfg.ringRatio[1], 3: r3 }

  const starSz = Math.min(cfg.starMax, Math.max(cfg.starMin, Math.round(r3 * cfg.starRatio)))

  /* 星核半径要同时满足两条：
     ① 比例好看（0.3×最外圈）
     ② 别顶到最内圈 —— 压扁之后纵向最窄，内圈星点的纵向坐标才是真正的约束。
        旧版只按比例算，遇到「宽而矮」的舞台（squash 被压到 0.5）星核就会盖住内圈星点。*/
  const innerClear = (ring[1] + cfg.starOut) * squash - starSz
  const sunR = Math.max(
    cfg.sunMin,
    Math.min(cfg.sunMax, Math.round(r3 * cfg.sunRatio), Math.floor(innerClear - cfg.sunGap))
  )
  // 星核小到一定程度就摆不下三行字了（字号不随缩放变，是硬约束）→ 只留「★ N」
  const compact = sunR < cfg.sunCompactR
  const coreFs = {
    sub: Math.max(11, Math.round(sunR * 0.2)),
    num: Math.max(11, Math.round(sunR * (compact ? 0.42 : 0.17))),
    hint: Math.max(10, Math.round(sunR * 0.135)),
    compact
  }

  const nodes = buildNodes(list, { cx, cy, ring, squash, starSz, cfg, lblOf })

  return {
    vbW,
    vbH,
    cx,
    cy,
    ring,
    rings: [ring[1], ring[2], ring[3]],
    squash,
    sunR,
    starSz,
    coreFs,
    labelRoom,
    maxChars,
    nodes
  }
}

/** 把处境列表摆到星盘上 */
export function buildNodes(scenes, { cx, cy, ring, squash, starSz, cfg = LAYOUT_DEFAULTS, lblOf }) {
  const list = scenes || []
  const N = list.length
  if (!N) return []
  const label = lblOf || (() => ({ text: '', w: 0, show: false, detail: false, top: 0, bot: 0 }))

  const pos = list.map((sc) => ({ ang: 0, r: ring[sc.depth] || ring[2], sc }))

  if (cfg.spread === 'even') {
    // 均分整圈，保持列表顺序（从正上方开始顺时针）—— 步骤星图用这个
    const step = 360 / N
    pos.forEach((p, i) => {
      p.ang = -90 + i * step
    })
  } else {
    // 按 branch 分组（保持首次出现顺序），每组占一段连续扇区 —— 同分支的星自然落在同一侧
    const order = []
    const byBranch = new Map()
    list.forEach((sc) => {
      const key = sc.branch || '_'
      if (!byBranch.has(key)) {
        byBranch.set(key, [])
        order.push(key)
      }
      byBranch.get(key).push(sc)
    })

    const G = order.length
    const gap = G > 1 ? Math.min(16, 360 / G / 2) : 0 // 组间留缝
    const used = 360 - gap * G
    const branchSlot = new Map()
    let cursor = -90 // 从正上方开始铺
    order.forEach((key) => {
      const g = byBranch.get(key)
      const span = (g.length / N) * used
      const start = cursor + gap / 2
      const end = cursor + span - gap / 2
      branchSlot.set(key, { start, end, mid: (start + end) / 2, span: Math.max(end - start, 1) })
      cursor += span
    })

    const idPos = new Map(list.map((sc, i) => [sc, i]))
    // 组内按 depth 内→外排序，在扇区内居中铺开
    const STEP_MAX = 34
    order.forEach((key) => {
      const g = byBranch.get(key)
      const { mid, span } = branchSlot.get(key)
      const gN = g.length
      g.sort((a, b) => (a.depth || 2) - (b.depth || 2))
      const step = Math.min(STEP_MAX, span / Math.max(gN - 1, 1))
      g.forEach((sc, k) => {
        const idx = idPos.get(sc)
        const ang = gN === 1 ? mid : mid + (k - (gN - 1) / 2) * step
        pos[idx].ang = ang
      })
    })
  }

  /* fitReach 所有模式都开 —— 只在「间距目标物理上够不着」时才生效，
     是防震荡护栏；keepOrder 只给 even：branch 模式是按扇区聚类的，
     星与星之间本来就没有全局先后关系，硬排顺序反而会把分支打散。 */
  relaxAngles(pos, cx, cy, cfg.minDist, squash, {
    fitReach: true,
    keepOrder: cfg.spread === 'even'
  })

  return pos.map((o, i) => {
    const rad = o.ang * RAD
    const r2 = o.r + cfg.starOut + ((i * 41) % 8) * 2 // 外扩 + 轻微抖动
    const side = labelSide(o.ang, starSz, cfg.labelOff)
    return {
      ...o.sc,
      idx: i,
      ang: o.ang,
      r: r2,
      x: cx + r2 * Math.cos(rad),
      y: cy + r2 * Math.sin(rad) * squash,
      dx: side.dx,
      dy: side.dy,
      anchor: side.anchor,
      lbl: label(o.sc)
    }
  })
}

/**
 * 在某个缩放 k 下，整张图是不是真的放得进舞台（留出 fitPad）。
 * fitScale 只能在下限以内尽量缩，缩到下限还放不下就得靠降档解决。
 */
export function contentFits(nodes, starSz, vbW, vbH, k, cfg = LAYOUT_DEFAULTS) {
  const bb = bboxAt(nodes, starSz, k, cfg)
  return bb.w <= vbW - cfg.fitPad * 2 && bb.h <= vbH - cfg.fitPad * 2
}

/**
 * 一次算出整张星盘布局，并挑一个「摆得下」的标签档位。
 *
 * 挑法：从最详细的 full 开始试，算完真实缩放 k 后数一遍标签互压、再看是否真的放得进；
 * 不行就降一档（少一行 / 干脆不摆），直到既不压也不溢出为止 ——
 * 小屏不会糊成一团，也不会把标签顶出画布，而是自动变成「点开才看名字」。
 */
export function buildLayout({ scenes = [], vbW, vbH, cfg } = {}) {
  const C = { ...LAYOUT_DEFAULTS, ...(cfg || {}) }
  let out = null
  for (const mode of LABEL_MODES) {
    const L = place({ scenes, vbW, vbH, cfg: C, mode })
    const k = fitScale(L.nodes, L.starSz, vbW, vbH, C)
    const overlaps = countLabelOverlaps(L.nodes, k, C)
    const fits = contentFits(L.nodes, L.starSz, vbW, vbH, k, C)
    out = { ...L, labelMode: mode, k, overlaps, fits, starGap: minStarGap(L.nodes) }
    if (overlaps === 0 && fits) break
  }
  return out
}

/** 「炼一个我的处境」时插进星盘的那颗临时新星 */
export function buildDraftNode(layout, baseNodes, depth = 2, cfg = LAYOUT_DEFAULTS) {
  const ang = findDraftAngle(baseNodes)
  const r = layout.ring[depth] + cfg.starOut + ((baseNodes.length * 41) % 8) * 2
  const rad = ang * RAD
  const side = labelSide(ang, layout.starSz, cfg.labelOff)
  const text = truncate('我的新处境', layout.maxChars || 16)
  return {
    id: 'draft',
    name: '我的新处境',
    sit: '在右侧面板描述你的真实处境，AI 会把它炼成一颗新星。',
    branch: '_draft',
    branchLabel: '新处境',
    depth,
    depthName: DEPTH_NAME[depth],
    verified: false,
    version: 1,
    peers: 0,
    idx: baseNodes.length,
    ang,
    r,
    x: layout.cx + r * Math.cos(rad),
    y: layout.cy + r * Math.sin(rad) * layout.squash,
    dx: side.dx,
    dy: side.dy,
    anchor: side.anchor,
    lbl: {
      text,
      w: labelWidth(text, cfg.labelFs),
      show: true,
      detail: layout.labelMode === 'full',
      top: -cfg.labelAsc,
      bot: layout.labelMode === 'full' ? cfg.labelDesc : cfg.labelDesc1
    }
  }
}
