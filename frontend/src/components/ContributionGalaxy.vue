<template>
  <div class="gal">
    <div class="gal__sky" />

    <!-- 工具条：画布「上方」的独立一行，不在画布上。
         曾经它是 position:absolute 浮在画布上，于是「标签 vs 顶栏」成了一道永远算不准的几何题。
         现在改成文档流，物理上不可能重合 —— 这一整类 bug 直接消失。 -->
    <div class="gal__bar">
      <button v-if="focusId" class="gal__back" @click="back">← 回到总览</button>
      <div class="gal__crumb" :title="crumbFull">
        <template v-if="focusedPlanet">
          <span class="gal__crumb-post">{{ focusedPlanet.postTitle }}</span>
          <i class="gal__sep">›</i>
          <span class="gal__crumb-cur">{{ focusedPlanet.title }}</span>
        </template>
        <template v-else>
          <span class="gal__crumb-post">我的贡献地图</span>
          <i class="gal__sep">·</i>
          <span class="gal__crumb-cur">{{ totalPlanets }} 个真实场景</span>
        </template>
      </div>
      <template v-if="focusId">
        <!-- 步骤多到一环放不下时的翻页器。和工具条同一行，绝不跟画布里的标签抢位置 -->
        <div v-if="pageCount > 1" class="gal__pager">
          <button class="gal__pg" :disabled="page === 0" @click.stop="flip(-1)">‹</button>
          <span class="gal__pg-t">第 {{ pageStart + 1 }}–{{ pageEnd }} 步 · 共 {{ totalSteps }} 步</span>
          <button class="gal__pg" :disabled="page >= pageCount - 1" @click.stop="flip(1)">›</button>
        </div>
        <span class="gal__hint">点空白处返回 · 当前只保留这一颗场景星与它的执行步骤</span>
      </template>
      <div v-else class="gal__legend">
        <span class="gal__legend-k">AI 自动分类</span>
        <button
          v-for="c in categories"
          :key="c.name"
          class="lgi"
          :class="{ 'is-on': activeCat === c.name }"
          :style="{ '--c': c.color }"
          @click="toggleCat(c.name)"
        >
          <i class="lgi__d" />{{ c.name }}
        </button>
      </div>
    </div>

    <!-- 星系画布：中心 = 我，一环 = 不同用户的真实场景，下钻 = 该场景的执行步骤 -->
    <div class="gal__stage">
      <svg class="gal__svg" :viewBox="`0 0 ${VW} ${VH}`" preserveAspectRatio="xMidYMid meet">
        <defs>
          <radialGradient id="sunGrad" cx="45%" cy="40%" r="60%">
            <stop offset="0%" stop-color="#fff0cd" />
            <stop offset="55%" stop-color="#ffd479" />
            <stop offset="100%" stop-color="#e79a1f" />
          </radialGradient>
          <!-- 行星（同星云图 / 解决步骤星图的做法）：核晕到边缘必须完全透明 -->
          <radialGradient id="galHalo">
            <stop offset="0%" stop-color="#ffe9c0" stop-opacity="0.5" />
            <stop offset="45%" stop-color="#fdf1da" stop-opacity="0.22" />
            <stop offset="100%" stop-color="#fdf6e8" stop-opacity="0" />
          </radialGradient>
          <radialGradient id="galGlow">
            <stop offset="0%" stop-color="#ffefc9" />
            <stop offset="62%" stop-color="#ffe3a1" />
            <stop offset="100%" stop-color="#ffd479" stop-opacity="0.2" />
          </radialGradient>
          <radialGradient id="galCoreHi">
            <stop offset="0%" stop-color="#ffffff" stop-opacity="0.85" />
            <stop offset="100%" stop-color="#ffffff" stop-opacity="0" />
          </radialGradient>
          <filter id="galSunBlur"><feGaussianBlur stdDeviation="3" /></filter>
        </defs>

        <rect x="0" y="0" :width="VW" :height="VH" fill="transparent" @click="back" />

        <g class="cam" :style="camStyle">
        <!-- 轨道连线：我 → 场景 -->
        <line
          v-for="p in planets"
          :key="'e' + p.id"
          :x1="me.x"
          :y1="me.y"
          :x2="p.x"
          :y2="p.y"
          class="orbit"
          :class="{ 'is-hot': highlightId === p.id, 'is-dim': isDim(p) || isGone(p.id) || isMeGone }"
        />
        <!-- 虚线轨道环：我的一环（场景轨道） -->
        <circle
          :cx="me.x"
          :cy="me.y"
          :r="orbitR"
          class="orbit-ring"
          :class="{ 'is-dim': !!highlightId || !!focusId }"
        />

        <!-- L0 中心 = 我（金色行星星核，带斜环） -->
        <g class="sun" :class="{ 'is-gone': isMeGone, 'is-dim': !!highlightId && !focusId }">
          <circle :cx="me.x" :cy="me.y" :r="(me.r * 1.95).toFixed(1)" class="sun__halo" />
          <circle :cx="me.x" :cy="me.y" :r="(me.r * 1.22).toFixed(1)" class="sun__glow" filter="url(#galSunBlur)" />
          <g class="sun__ring back" :transform="`translate(${me.x} ${me.y}) rotate(-16)`">
            <path :d="sunRing(me.r).back" fill="none" stroke="#e8c98f" :stroke-width="sunRing(me.r).w" opacity="0.75" />
          </g>
          <circle :cx="me.x" :cy="me.y" :r="me.r" class="sun__c" />
          <circle
            class="sun__hi"
            :cx="(me.x - me.r * 0.3).toFixed(1)"
            :cy="(me.y - me.r * 0.36).toFixed(1)"
            :r="(me.r * 0.52).toFixed(1)"
            fill="url(#galCoreHi)"
          />
          <g class="sun__ring front" :transform="`translate(${me.x} ${me.y}) rotate(-16)`">
            <path :d="sunRing(me.r).front" fill="none" stroke="#d9a94f" :stroke-width="sunRing(me.r).w" opacity="0.9" />
          </g>
          <text class="sun__t" :x="me.x" :y="me.y + me.r + 17">我</text>
          <text class="sun__a" :x="me.x" :y="me.y + me.r + 32">
            {{ groups.length }} 篇收藏 · {{ totalPlanets }} 个真实场景
          </text>
        </g>

        <!-- L1 场景 = 不同用户的真实场景（小星星） -->
        <g
          v-for="p in planets"
          :key="p.id"
          class="planet"
          :class="{
            'is-gone': isGone(p.id),
            'is-dim': isDim(p),
            'is-focus': focusId === p.id,
            'is-hover': hoverId === p.id
          }"
          @mouseenter="hoverId = p.id"
          @mouseleave="hoverId = null"
          @click.stop="enterPlanet(p)"
        >
          <circle v-if="focusId === p.id" :cx="p.x" :cy="p.y" r="27" class="planet__halo" />
          <!-- 定位走父 g 的 attribute transform；hover 放大是 CSS transform，作用在星形自己的 fill-box 上 ——
               两者分开，才不会互相覆盖（CSS transform 会顶掉 attribute transform） -->
          <g :transform="`translate(${p.x} ${p.y})`">
            <path
              class="planet__c"
              :d="starPath(p.r * 1.5, p.r * 0.63)"
              :fill="catColor(p.aiCategory)"
              stroke="#ffffff"
              stroke-width="1.1"
              stroke-linejoin="round"
            />
            <!-- 金色描边 = 我贡献的 -->
            <circle v-if="p.isMine" :r="p.r * 1.5 + 4.5" class="planet__mine" />
          </g>
          <!-- 下钻后场景名不再渲染：它原来的位置正好是下方步骤标签的落点。
               名字在顶部面包屑和下方详情面板里都有，这里不跟标签抢位置。 -->
          <template v-if="focusId !== p.id">
            <text
              v-for="(ln, i) in p.label.lines"
              :key="i"
              class="planet__t"
              :x="p.label.lx"
              :y="p.label.ly + i * 13"
              :text-anchor="p.label.anchor"
            >{{ ln }}</text>
          </template>
        </g>

        <!-- L2 步骤 = 该场景的真实解决步骤（迷你星形，下钻才现身） -->
        <g v-for="m in moons" :key="m.id" class="moon" :style="moonStyle(m)">
          <line :x1="m.px" :y1="m.py" :x2="m.x" :y2="m.y" class="moon__spoke" />
          <path
            class="moon__c"
            :d="starPath(m.r + 2.4, (m.r + 2.4) * 0.42)"
            :transform="`translate(${m.x} ${m.y})`"
          />
          <text
            v-for="(ln, i) in m.label.lines"
            :key="i"
            class="moon__t"
            :x="m.label.lx"
            :y="m.label.ly + i * 12"
            :text-anchor="m.label.anchor"
          >{{ ln }}</text>
        </g>
      </g>
      </svg>

      <div v-if="!planets.length" class="gal__empty">
        <p>还没有可展示的场景：先去「星云图」收藏原帖，或在原帖下贡献你的真实场景。</p>
      </div>
    </div>

    <!-- 底部提示也在文档流里，同样不压画布 -->
    <div v-if="!focusId" class="gal__tip">
      悬停场景星 = 突出它 · 单击场景星 = 进入该场景（其他场景会被移除）· 金色描边 = 我贡献的
    </div>
  </div>
</template>

<script setup>
import { computed, onUnmounted, ref, watch } from 'vue'

const props = defineProps({
  groups: { type: Array, default: () => [] },
  /* 初始下钻的场景 id。传了就一进来直接停在某个场景的环绕视图上（外部/自检可程序化进入），
     不传则显示总览。 */
  focus: { type: String, default: null }
})
const emit = defineEmits(['select', 'clear'])

const VW = 900
const VH = 560
const CX = VW / 2
const CY = VH / 2

/* ---------------- AI 自动分类 → 场景星着色 ---------------- */
const CAT_COLORS = {
  职场表达: '#3d7fd6',
  AI工具: '#7b6ee0',
  学习方法: '#14a37f',
  硬件调试: '#e0a326',
  内容创作: '#d9568a'
}
const catColor = (name) => CAT_COLORS[name] || '#7c8aa5'

/* 8 角星形 path（本地 (0,0) 基准，靠 transform translate 定位）。
   中心 = 我（带斜环的行星星核）；小星星 = 真实场景；迷你星 = 执行步骤。 */
function starPath(R, r) {
  const p = []
  for (let i = 0; i < 8; i++) {
    const a = ((-90 + i * 45) * Math.PI) / 180
    const rad = i % 2 === 0 ? R : r
    p.push((Math.cos(a) * rad).toFixed(2) + ' ' + (Math.sin(a) * rad).toFixed(2))
  }
  return 'M' + p.join(' L') + ' Z'
}

/* 行星环：rx=1.45R、ry=0.5R，分前后两半。path 画在 (0,0) 基准上，靠父 <g> 的 translate+rotate 定位。 */
function sunRing(R) {
  const rx = R * 1.45
  const ry = R * 0.5
  return {
    back: `M ${(-rx).toFixed(1)} 0 A ${rx.toFixed(1)} ${ry.toFixed(1)} 0 0 1 ${rx.toFixed(1)} 0`,
    front: `M ${(-rx).toFixed(1)} 0 A ${rx.toFixed(1)} ${ry.toFixed(1)} 0 0 0 ${rx.toFixed(1)} 0`,
    w: Math.max(1.2, R * 0.045).toFixed(1)
  }
}

/* 均衡断行：先算需要几行，再按行数均分字数。 */
function wrapText(str, maxPerLine = 8, maxLines = 3) {
  const s = String(str || '')
    .replace(/\s+/g, ' ')
    .trim()
  if (!s) return ['']
  if (s.length <= maxPerLine) return [s]
  const lines = Math.min(maxLines, Math.ceil(s.length / maxPerLine))
  const per = Math.ceil(s.length / lines)
  const out = []
  for (let i = 0; i < s.length; i += per) out.push(s.slice(i, i + per))
  return out.slice(0, maxLines)
}

/* 一环最多几颗（几何天花板）：9 颗时最紧相邻粒子的垂直落差必然小于标签高，
   超过 8 步不再往环上堆，改用翻页器。 */
const MOON_SLOTS = 8

/* 第 i 颗粒子的角度：整圈先转 1/4 步，任何步数都不会有粒子正对父节点正上 / 正下方。 */
const moonAngle = (i, n) => -Math.PI / 2 + Math.PI / (2 * n) + (i * 2 * Math.PI) / n

/* 环半径：按最紧的那一对相邻粒子反推，保证落差 ≥ 标签高 + 4 缝。 */
const MOON_LABEL_H = 46
function ringRFor(n, min, max) {
  if (n <= 1) return min
  let minD = Infinity
  for (let i = 0; i < n; i++) minD = Math.min(minD, Math.abs(Math.sin(moonAngle(i + 1, n)) - Math.sin(moonAngle(i, n))))
  return Math.min(max, Math.max(min, (MOON_LABEL_H + 4) / Math.max(minD, 0.25)))
}

/* 步骤环（下钻态，镜头会拉近）的半径边界 */
const MOON_R_MIN = 78
const MOON_R_MAX = 118

/* ---------------- 布局（固定 viewBox，镜头下钻才有参照） ----------------
   三层天体：L0 我（中心）→ L1 场景小星星（我的一环）→ L2 步骤迷你星（场景的一环，下钻才现身）。
   帖子不再单独成层（用户定：不要呈现那么多信息），帖子标题只在面包屑和详情面板里出现。 */

/* 场景环半径：场景越多收得越紧（这是「我的一环」，总览 k=1 就要放得下） */
const orbitR = computed(() => {
  const n = props.groups.reduce((a, g) => a + g.planets.length, 0) || 1
  return n <= 3 ? 150 : n <= 6 ? 120 : 100
})

/* 画布安全边距：画布里没有任何 HTML 浮层（工具条/提示都在文档流），所以是纯常量 */
const SAFE_PAD = 10
const safeTop = computed(() => SAFE_PAD)
const safeBot = computed(() => VH - SAFE_PAD)

/* 相机倍率：只用于下钻态（对准场景星装下它的步骤环）。总览 k=1，画布内容按构造放得下。 */
const CAM_K_MAX = 2.05
const CAM_K_MIN = 1.1
const FIT_PAD = 8

/* 一颗粒子的标签朝向：只按方位「朝外」，不看浮层。 */
const idealDir = (c, sn) => (c > 0.35 ? 'right' : c < -0.35 ? 'left' : sn < 0 ? 'up' : 'down')

/* 按朝向落位。绝不折回行星：折回去必然盖住行星本体或它自己的名字。 */
function placeByDir(dir, mx, my, mr, lines) {
  const h = (lines.length - 1) * 12
  if (dir === 'right') return { dir, anchor: 'start', lx: mx + mr + 6, ly: my - h / 2 + 4 }
  if (dir === 'left') return { dir, anchor: 'end', lx: mx - mr - 6, ly: my - h / 2 + 4 }
  if (dir === 'up') return { dir, anchor: 'middle', lx: mx, ly: my - mr - 6 - h }
  return { dir, anchor: 'middle', lx: mx, ly: my + mr + 13 }
}

/* pass 2：镜头倍率定了之后，上下安全区（画布单位）就能算 ——
   冲进画布边缘的朝向改成左右，最后一律再夹一次。 */
function placeMoonLabel(mx, my, dy, c, sn, lines, mr, k) {
  const h = (lines.length - 1) * 12
  const dyTop = (safeTop.value - VH / 2) / k
  const dyBot = (safeBot.value - VH / 2) / k
  let dir = idealDir(c, sn)
  if (dir === 'up' && dy - 20.5 - h < dyTop) dir = c < 0 ? 'left' : 'right'
  if (dir === 'down' && dy + 21 + h > dyBot) dir = c < 0 ? 'left' : 'right'

  const out = placeByDir(dir, mx, my, mr, lines)
  const py = my - dy
  out.ly = py + Math.min(Math.max(out.ly - py, dyTop + 10.5), dyBot - 4 - h)
  return out
}

/* 标签包围盒相对父节点的极值（和自检脚本同一套字号估值）。 */
const MOON_FS = 11
function textW(s) {
  let w = 0
  for (const ch of s) w += /[\u4e00-\u9fa5\u3000-\u303f\uff00-\uffef]/.test(ch) ? MOON_FS : MOON_FS * 0.55
  return w
}
function labelBox(label, lines, mx, my, mr, px, py) {
  const widest = Math.max(...lines.map(textW), 1)
  const h = (lines.length - 1) * 12
  const l = label.anchor === 'middle' ? label.lx - widest / 2 : label.anchor === 'end' ? label.lx - widest : label.lx
  const t = label.ly - MOON_FS * 0.82
  const b = label.ly + h + MOON_FS * 0.24
  return {
    ex: Math.max(Math.abs(l - px), Math.abs(l + widest - px), Math.abs(mx - px) + mr),
    up: Math.max(py - t, py - (my - mr)),
    dn: Math.max(b - py, my + mr - py)
  }
}

/* 翻页游标：一环只放 MOON_SLOTS 颗，超出的翻页看。 */
const page = ref(0)

const built = computed(() => {
  /* 所有帖子里的场景摊到同一张环上：中心是我，一环是全部真实场景 */
  const list = props.groups.flatMap((g) =>
    g.planets.map((p) => ({ ...p, postId: g.post.id, postTitle: g.post.title }))
  )
  const n = Math.max(list.length, 1)
  const R = orbitR.value
  const start = page.value * MOON_SLOTS
  const me = {
    x: CX,
    y: CY,
    r: 24,
    nPosts: props.groups.length,
    nScenes: list.length
  }
  const planets = []
  const moons = []

  list.forEach((p, pi) => {
    const a = -Math.PI / 2 + (pi * 2 * Math.PI) / n
    const c = Math.cos(a)
    const sn = Math.sin(a)
    const px = CX + R * c
    const py = CY + R * sn
    const lines = wrapText(p.title, 8)
    /* 总览标签：按方位朝外（同 v1.5 的行星标签），星形外接半径 18 */
    const label = placeByDir(idealDir(c, sn), px, py, 18, lines)
    planets.push({
      ...p,
      x: px,
      y: py,
      r: 12,
      label: { ...label, lines }
    })

    /* 该场景的执行步骤（下钻态才现身；镜头倍率靠这环的包围盒反推） */
    const steps = (p.steps || []).slice(start, start + MOON_SLOTS)
    const nSteps = Math.max(steps.length, 1)
    const ringR = steps.length ? ringRFor(nSteps, MOON_R_MIN, MOON_R_MAX) : MOON_R_MIN
    /* 包围盒以「场景星 + 环 + 标签」整体算，镜头倍率靠它反推（见 camK） */
    let ex = 27 // 场景星光环半径
    let up = 27
    let dn = 27

    steps.forEach((s, mi) => {
      const ma = moonAngle(mi, nSteps)
      const c2 = Math.cos(ma)
      const s2 = Math.sin(ma)
      const mx = px + ringR * c2
      const my = py + ringR * s2
      const mr = 5.5
      const mlines = wrapText(s, 7, 3)
      const dir = idealDir(c2, s2)
      const ideal = placeByDir(dir, mx, my, mr, mlines)
      const idealBox = labelBox(ideal, mlines, mx, my, mr, px, py)
      ex = Math.max(ex, idealBox.ex)
      up = Math.max(up, idealBox.up)
      dn = Math.max(dn, idealBox.dn)

      moons.push({
        id: `${p.id}_m${start + mi}`,
        planetId: p.id,
        index: mi,
        stepIndex: start + mi,
        px,
        py,
        x: mx,
        y: my,
        r: mr,
        raw: { dy: ringR * s2, c: c2, sn: s2, lines: mlines }
      })
    })

    /* 场景星自己的包围盒也并进去：镜头要装下的是「整团内容」 */
    ex = Math.max(ex, ringR + 5.5)
    up = Math.max(up, ringR + 5.5)
    dn = Math.max(dn, ringR + 5.5)
    planets[planets.length - 1].fit = { ex, up, dn }
  })

  return { me, planets, moons }
})

const me = computed(() => built.value.me)
const planets = computed(() => built.value.planets)
const totalPlanets = computed(() => planets.value.length)

/* ---------------- 相机：只服务下钻态（内容长多大，镜头就退多远） ---------------- */
const camK = computed(() => {
  const fit = planets.value.find((p) => p.id === focusId.value)?.fit
  if (!fit) return CAM_K_MAX
  const ks = [
    CAM_K_MAX,
    (VW / 2 - FIT_PAD) / Math.max(fit.ex, 1),
    (VH / 2 - safeTop.value - FIT_PAD) / Math.max(fit.up, 1),
    (safeBot.value - VH / 2 - FIT_PAD) / Math.max(fit.dn, 1)
  ]
  return Math.max(CAM_K_MIN, Math.min(...ks))
})

/* pass 2：镜头倍率定了，步骤标签才真正落位（总览态步骤环是隐藏的）。 */
const moons = computed(() =>
  built.value.moons.map((m) => {
    const { dy, c, sn, lines } = m.raw
    const label = placeMoonLabel(m.x, m.y, dy, c, sn, lines, m.r, camK.value)
    return { ...m, label: { ...label, lines } }
  })
)

/* ---------------- 翻页 ---------------- */
const totalSteps = computed(() => focusedPlanet.value?.steps?.length || 0)
const pageCount = computed(() => Math.max(1, Math.ceil(totalSteps.value / MOON_SLOTS)))
const pageStart = computed(() => page.value * MOON_SLOTS)
const pageEnd = computed(() => Math.min(pageStart.value + MOON_SLOTS, totalSteps.value))
function flip(d) {
  page.value = Math.min(Math.max(page.value + d, 0), pageCount.value - 1)
}

const categories = computed(() => {
  const seen = []
  for (const p of planets.value) {
    if (p.aiCategory && !seen.includes(p.aiCategory)) seen.push(p.aiCategory)
  }
  return seen.map((name) => ({ name, color: catColor(name) }))
})

/* ---------------- 下钻状态机 ---------------- */
const focusId = ref(props.focus || null)
const phase = ref('idle')
const purged = ref(!!props.focus)
const hoverId = ref(null)
const activeCat = ref(null)
let timer = null

const focusedPlanet = computed(() =>
  focusId.value ? planets.value.find((p) => p.id === focusId.value) : null
)
const highlightId = computed(() => hoverId.value || focusId.value)

function isDim(p) {
  if (activeCat.value && p.aiCategory !== activeCat.value) return true
  if (hoverId.value && p.id !== hoverId.value) return true
  return false
}
function isGone(id) {
  if (!focusId.value) return phase.value === 'entering'
  if (id === focusId.value) return false
  if (phase.value === 'leaving') return true
  return purged.value
}
/* 下钻后：中心的我收起（来路交给顶部面包屑） */
const isMeGone = computed(() => !!focusId.value)

const camStyle = computed(() => {
  const p = focusedPlanet.value
  if (!p) return { transform: 'translate(0px, 0px) scale(1)' }
  const k = camK.value
  return { transform: `translate(${VW / 2 - p.x * k}px, ${VH / 2 - p.y * k}px) scale(${k})` }
})

function moonStyle(m) {
  const on = focusId.value === m.planetId
  const dx = (m.px - m.x) * 0.62
  const dy = (m.py - m.y) * 0.62
  return {
    transform: on ? 'translate(0px, 0px)' : `translate(${dx}px, ${dy}px)`,
    opacity: on ? 1 : 0,
    transitionDelay: on ? `${110 + m.index * 60}ms` : '0ms'
  }
}

function enterPlanet(p) {
  if (focusId.value === p.id) return
  focusId.value = p.id
  page.value = 0
  phase.value = 'leaving'
  purged.value = false
  hoverId.value = null
  emit('select', p)
  window.clearTimeout(timer)
  timer = window.setTimeout(() => {
    phase.value = 'idle'
    purged.value = true
  }, 440)
}

function back() {
  if (!focusId.value) return
  window.clearTimeout(timer)
  purged.value = false
  focusId.value = null
  page.value = 0
  phase.value = 'entering'
  emit('clear')
  requestAnimationFrame(() =>
    requestAnimationFrame(() => {
      phase.value = 'idle'
    })
  )
}

function toggleCat(name) {
  activeCat.value = activeCat.value === name ? null : name
}

/* `focus` 是受控入口：外部改它就等于替用户点了一次场景星 / 点了一次「回到总览」 */
watch(
  () => props.focus,
  (v) => {
    const id = v || null
    if (id === focusId.value) return
    if (!id) return back()
    const p = planets.value.find((x) => x.id === id)
    if (p) enterPlanet(p)
  }
)

/* 面包屑被省略时的完整内容（原生 tooltip 兜底，不额外做浮层） */
const crumbFull = computed(() =>
  focusedPlanet.value ? `${focusedPlanet.value.postTitle} › ${focusedPlanet.value.title}` : ''
)

onUnmounted(() => window.clearTimeout(timer))
</script>

<style scoped>
.gal {
  position: relative;
  border-radius: var(--radius-lg);
  overflow: hidden;
  /* 竖排：工具条 / 画布 / 底部提示各占一行，谁都不浮在谁上面。
     这是「标签永远压不到工具条」的结构性保证 —— 不是靠算对安全区。 */
  display: flex;
  flex-direction: column;
  background: radial-gradient(120% 90% at 50% 6%, #ffffff 0%, var(--nbg-1) 54%, var(--nbg-2) 100%);
  border: 1px solid var(--border);
  box-shadow: var(--shadow);
}
.gal__sky {
  position: absolute;
  inset: 0;
  z-index: 0;
  opacity: 0.9;
  pointer-events: none;
  background-image: radial-gradient(1.3px 1.3px at 18% 26%, rgba(5, 109, 232, 0.16) 50%, transparent 51%),
    radial-gradient(1.1px 1.1px at 72% 18%, rgba(5, 109, 232, 0.11) 50%, transparent 51%),
    radial-gradient(1.5px 1.5px at 38% 74%, rgba(5, 109, 232, 0.1) 50%, transparent 51%),
    radial-gradient(1.1px 1.1px at 86% 62%, rgba(5, 109, 232, 0.12) 50%, transparent 51%),
    radial-gradient(1px 1px at 10% 84%, rgba(5, 109, 232, 0.09) 50%, transparent 51%),
    radial-gradient(1.2px 1.2px at 58% 90%, rgba(5, 109, 232, 0.09) 50%, transparent 51%);
}
/* 工具条 = 画布上方独立的一行。不再是 absolute 浮层，所以长面包屑、窄容器都不会压到画布。 */
.gal__bar {
  position: relative;
  z-index: 3;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 14px 10px;
  border-bottom: 1px solid var(--border);
}
.gal__back {
  flex: 0 0 auto;
  padding: 5px 12px;
  border-radius: 999px;
  border: 1px solid var(--zh-blue-line-strong);
  background: var(--n-pill);
  color: var(--zh-blue);
  font-size: 12.5px;
  font-weight: 600;
  cursor: pointer;
  box-shadow: var(--shadow);
  transition: background 0.16s ease, border-color 0.16s ease, transform 0.16s ease;
}
.gal__back:hover {
  background: var(--zh-blue-soft);
  border-color: var(--zh-blue);
}
.gal__back:active {
  transform: scale(0.97);
}
.gal__crumb {
  flex: 1 1 auto;
  min-width: 0;
  overflow: hidden;
  display: flex;
  align-items: center;
  gap: 7px;
  font-size: 12.5px;
  color: var(--n-text-3);
}
.gal__crumb-post {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--n-text);
  font-weight: 600;
}
.gal__crumb-cur {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--n-text-3);
}
.gal__sep {
  flex: 0 0 auto;
  font-style: normal;
  opacity: 0.6;
}
.gal__legend {
  flex: 0 0 auto;
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
  padding: 4px 10px;
  border-radius: 999px;
  background: var(--n-pill);
  border: 1px solid var(--n-pill-line);
}
.gal__hint {
  flex: 0 0 auto;
  white-space: nowrap;
  font-size: 11px;
  color: var(--n-text-3);
}
/* 画布舞台：只有画布本身，没有浮层 */
.gal__stage {
  position: relative;
  z-index: 1;
}
/* 步骤超过一环容量时的翻页器。和工具条同一行，绝不跟画布里的标签抢位置。 */
.gal__pager {
  flex: 0 0 auto;
  display: flex;
  align-items: center;
  gap: 2px;
  padding: 2px 5px;
  border-radius: 999px;
  background: var(--n-pill);
  border: 1px solid var(--n-pill-line);
}
.gal__pg {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  border: none;
  background: transparent;
  color: var(--zh-blue);
  font-size: 14px;
  line-height: 1;
  cursor: pointer;
  transition: background 0.15s ease;
}
.gal__pg:hover:not(:disabled) {
  background: var(--zh-blue-soft);
}
.gal__pg:disabled {
  color: var(--n-text-3);
  opacity: 0.4;
  cursor: default;
}
.gal__pg-t {
  font-size: 11px;
  color: var(--n-text-2);
  white-space: nowrap;
  padding: 0 3px;
}
.gal__legend-k {
  font-size: 11px;
  color: var(--n-text-3);
}
.lgi {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  border-radius: 999px;
  border: 1px solid transparent;
  background: transparent;
  color: var(--n-text-2);
  font-size: 11.5px;
  cursor: pointer;
  transition: background 0.15s ease, border-color 0.15s ease, color 0.15s ease;
}
.lgi:hover {
  background: var(--zh-blue-soft);
}
.lgi.is-on {
  border-color: var(--c);
  color: var(--n-text);
  background: var(--zh-blue-soft);
}
.lgi__d {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--c);
}
.gal__svg {
  display: block;
  width: 100%;
  height: auto;
}
.cam {
  transform-box: view-box;
  transform-origin: 0px 0px;
  transition: transform 380ms cubic-bezier(0.22, 1, 0.36, 1);
}
.orbit {
  stroke: var(--nbg-line);
  stroke-width: 1.2;
  transition: stroke 0.2s ease, opacity 0.3s ease;
}
.orbit.is-hot {
  stroke: var(--zh-blue);
  stroke-width: 2;
}
.orbit.is-dim {
  opacity: 0.12;
}
.orbit-ring {
  fill: none;
  stroke: var(--nbg-line);
  stroke-width: 1;
  stroke-dasharray: 3 6;
  transition: opacity 0.3s ease;
}
.orbit-ring.is-dim {
  opacity: 0.15;
}
/* ---- L0 我（金色行星星核） ---- */
.sun {
  transition: opacity 0.34s ease;
}
.sun.is-gone {
  opacity: 0;
  pointer-events: none;
}
.sun.is-dim {
  opacity: 0.3;
}
.sun__halo {
  fill: url(#galHalo);
  transform-box: fill-box;
  transform-origin: center;
  animation: sunPulse 4s ease-in-out infinite;
}
@keyframes sunPulse {
  0%,
  100% {
    transform: scale(1);
    opacity: 0.6;
  }
  50% {
    transform: scale(1.14);
    opacity: 1;
  }
}
.sun__glow {
  fill: url(#galGlow);
}
.sun__c {
  fill: url(#sunGrad);
  stroke: rgba(231, 154, 31, 0.55);
  stroke-width: 1.2;
  /* 浅底上不需要那么强的外发光，收成一层薄薄的暖影，托住这颗「太阳」 */
  filter: drop-shadow(0 4px 10px rgba(231, 154, 31, 0.28));
}
.sun__hi {
  pointer-events: none;
}
.sun__t {
  fill: var(--n-text);
  font-size: 12.5px;
  font-weight: 700;
  text-anchor: middle;
  pointer-events: none;
}
.sun__a {
  fill: var(--n-text-3);
  font-size: 10.5px;
  text-anchor: middle;
  pointer-events: none;
}
/* ---- L1 场景星 ---- */
.planet {
  cursor: pointer;
  transition: opacity 0.3s ease;
}
.planet.is-gone {
  opacity: 0;
  pointer-events: none;
}
.planet.is-dim {
  opacity: 0.22;
}
.planet__c {
  /* 颜色由模板里的 :fill 属性给（分类色）；CSS 再写 fill 会盖过属性，所以这里只管形变和投影 */
  transform-box: fill-box;
  transform-origin: center;
  transition: transform 0.2s ease;
  filter: drop-shadow(0 2px 5px rgba(15, 30, 60, 0.2));
}
.planet.is-hover .planet__c,
.planet.is-focus .planet__c {
  transform: scale(1.2);
}
.planet__mine {
  fill: none;
  stroke: var(--st-core);
  stroke-width: 1.6;
}
.planet__halo {
  fill: none;
  stroke: rgba(5, 109, 232, 0.55);
  stroke-width: 1.4;
  stroke-dasharray: 4 5;
  transform-box: fill-box;
  transform-origin: center;
  animation: spin 9s linear infinite;
}
@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
.planet__t {
  fill: var(--n-text-2);
  font-size: 11.5px;
  pointer-events: none;
}
.planet.is-focus .planet__t,
.planet.is-hover .planet__t {
  fill: var(--n-text);
  font-weight: 700;
}
/* ---- L2 步骤迷你星 ---- */
.moon {
  transition: transform 340ms cubic-bezier(0.22, 1, 0.36, 1), opacity 220ms ease;
  pointer-events: none;
}
.moon__spoke {
  stroke: rgba(5, 109, 232, 0.35);
  stroke-width: 1;
}
.moon__c {
  fill: #0fae96;
  stroke: #ffffff;
  stroke-width: 1;
}
.moon__t {
  fill: #0b7a6a;
  font-size: 11px;
  pointer-events: none;
}
/* 底部提示 = 画布下方独立的一行，不是浮在画布上的胶囊 */
.gal__tip {
  position: relative;
  z-index: 2;
  padding: 9px 14px 11px;
  border-top: 1px solid var(--border);
  font-size: 11px;
  color: var(--n-text-3);
  text-align: center;
}
.gal__empty {
  position: absolute;
  inset: 0;
  z-index: 2;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--n-text-3);
  font-size: 13px;
  text-align: center;
  padding: 0 30px;
}
@media (prefers-reduced-motion: reduce) {
  .cam,
  .moon,
  .planet,
  .orbit,
  .sun {
    transition: none !important;
  }
  .sun__halo,
  .planet__halo {
    animation: none !important;
  }
}
@media (max-width: 900px) {
  .gal__bar {
    padding: 10px;
    gap: 8px;
    flex-wrap: wrap;
  }
  .gal__crumb {
    flex: 1 1 100%;
    order: 3;
  }
  .gal__hint,
  .gal__legend {
    margin-left: 0;
  }
}
</style>
