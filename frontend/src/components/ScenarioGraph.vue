<template>
  <div class="sg" :class="{ 'sg--mini': compact, 'sg--deco': deco }">
    <svg :viewBox="vb" class="sg__svg" preserveAspectRatio="xMidYMid meet" role="img">
      <title>场景应用网：原帖与已沉淀的真实场景构成的蛛网</title>

      <!-- 同心蛛丝（椭圆环） -->
      <path v-for="(r, i) in rings" :key="'r' + i" :d="r.d" class="sg__ring" />

      <!-- 径向辐条（只画有节点的辐条） -->
      <path
        v-for="(s, i) in spokes"
        :key="'s' + i"
        :d="s.d"
        class="sg__spoke"
        :class="{ 'sg__spoke--cur': s.cur }"
      />

      <!-- 当前场景牵引线（中心 → 当前节点，金线 flow） -->
      <path v-for="(e, i) in edges" :key="'e' + i" :d="e.d" class="sg__edge sg__edge--cur" />

      <!-- 中心：原帖（金色核心 + 细外环 + 呼吸） -->
      <g class="sg__hub">
        <circle :cx="cx" :cy="cy" :r="cr + 6" class="sg__hub-ring" />
        <circle :cx="cx" :cy="cy" :r="cr" class="sg__hub-core" />
      </g>
      <text v-if="showText" :x="cx" :y="cy - cr - 16" class="sg__center-label">
        {{ centerShort }}
      </text>

      <!-- 场景节点（蛛网上的珠子） -->
      <g
        v-for="n in nodes"
        :key="n.id"
        class="sg__node"
        :class="{ 'sg__node--cur': n.isCurrent }"
        :style="n.style"
      >
        <circle :cx="n.x" :cy="n.y" :r="n.r + 3" class="sg__node-tether" />
        <circle :cx="n.x" :cy="n.y" :r="n.r" class="sg__node-core" />
        <circle
          v-if="n.isCurrent"
          :cx="n.x"
          :cy="n.y"
          :r="n.r + 5"
          class="sg__node-halo"
        />
        <text v-if="showText" :x="n.x" :y="n.y + n.r + 14" class="sg__node-label">
          {{ n.tag }}
        </text>
      </g>

      <text v-if="showText && !nodes.length" :x="cx" :y="cy + 4" class="sg__empty">
        还没有场景 · 等你来牵第一根丝
      </text>
    </svg>

    <div v-if="showText" class="sg__legend">
      <span class="sg__legend-item"><i class="sg__dot sg__dot--center" /> 原帖中心</span>
      <span class="sg__legend-item"><i class="sg__dot sg__dot--cur" /> 你的场景（当前）</span>
      <span class="sg__legend-item"><i class="sg__dot sg__dot--node" /> 已沉淀场景</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  postTitle: { type: String, default: '原帖' },
  scenarios: { type: Array, default: () => [] },
  currentId: { type: [Number, null], default: null },
  compact: { type: Boolean, default: false },
  deco: { type: Boolean, default: false } // 装饰模式：无文字/图例，用作卡片背景
})

// ---------- 画布 ----------
const vb = computed(() => (props.compact ? '0 0 170 110' : '0 0 680 360'))
const cx = computed(() => (props.compact ? 85 : 340))
const cy = computed(() => (props.compact ? 55 : 176))
const cr = computed(() => (props.compact ? 4.5 : 7.5))
const rx = computed(() => (props.compact ? 58 : 240))
const ry = computed(() => (props.compact ? 36 : 122))
const showText = computed(() => !props.compact && !props.deco)

// ---------- 确定性随机（同一个 id 永远落在同一个位置） ----------
const rand = (seed) => {
  let t = (seed + 0x6d2b79f5) | 0
  t = Math.imul(t ^ (t >>> 15), t | 1)
  t ^= t + Math.imul(t ^ (t >>> 7), t | 61)
  return ((t ^ (t >>> 14)) >>> 0) / 4294967296
}
const trunc = (s, n) => {
  if (!s) return ''
  s = String(s)
  return s.length > n ? s.slice(0, n) + '…' : s
}
const centerShort = computed(() => trunc(props.postTitle, 12))

// ---------- 蛛网参数 ----------
const SPOKES = 12 // 径向辐条数
const RINGS = 4   // 同心蛛丝环数

// 起点偏移：避免节点全挤在 12 点钟方向
const spokeOffset = computed(
  () => rand(((props.postTitle || '').length * 131 + 17) | 0) * (Math.PI * 2 / SPOKES)
)

// ---------- 同心环（椭圆） ----------
const rings = computed(() =>
  Array.from({ length: RINGS }, (_, i) => {
    const r = (i + 1) / RINGS
    const rxv = rx.value * r
    const ryv = ry.value * r
    return {
      d: `M${cx.value - rxv} ${cy.value} A${rxv} ${ryv} 0 1 0 ${
        cx.value + rxv
      } ${cy.value} A${rxv} ${ryv} 0 1 0 ${cx.value - rxv} ${cy.value}`
    }
  })
)

// ---------- 场景节点：环 + 辐条 网格定位 ----------
const nodes = computed(() => {
  const list = props.scenarios || []
  const n = list.length
  const clampX = props.compact ? 12 : 30
  const clampY = props.compact ? 8 : 22
  const W = props.compact ? 170 : 680
  const H = props.compact ? 110 : 360
  return list.map((s, i) => {
    const id = s.id ?? i
    const seed = id * 7919 + i * 131
    const spokeIdx = i % SPOKES
    const ang = spokeIdx * (Math.PI * 2 / SPOKES) + spokeOffset.value
    const ringIdx = Math.min(RINGS - 1, Math.floor(rand(seed + 5) * RINGS))
    const ringR = (ringIdx + 1) / RINGS
    let x = cx.value + rx.value * ringR * Math.cos(ang)
    let y = cy.value + ry.value * ringR * Math.sin(ang)
    x += (rand(seed + 1) - 0.5) * 12
    y += (rand(seed + 2) - 0.5) * 8
    x = Math.min(Math.max(x, clampX), W - clampX)
    y = Math.min(Math.max(y, clampY), H - clampY - 10)
    const isCurrent = s.id != null && s.id === props.currentId
    const base = props.compact ? 1.6 : 2.2
    const grow = props.compact ? 1.4 : 2.4
    return {
      id,
      tag: trunc(s.scene_tag || '场景', props.compact ? 0 : 8),
      x: Math.round(x),
      y: Math.round(y),
      r: isCurrent ? (props.compact ? 4.4 : 6.2) : +(base + grow * rand(seed + 3)).toFixed(2),
      isCurrent,
      spoke: spokeIdx,
      style: {
        animationDelay: `${((i * 0.41) % 2.6).toFixed(2)}s`,
        animationDuration: `${(3.2 + (i % 5) * 0.47).toFixed(2)}s`
      }
    }
  })
})

// ---------- 径向辐条：只画有节点的辐条；含当前节点的辐条高亮 ----------
const spokes = computed(() => {
  const ns = nodes.value
  const used = new Map()
  ns.forEach((n) => {
    if (!used.has(n.spoke)) used.set(n.spoke, false)
    if (n.isCurrent) used.set(n.spoke, true)
  })
  const out = []
  used.forEach((cur, spokeIdx) => {
    const ang = spokeIdx * (Math.PI * 2 / SPOKES) + spokeOffset.value
    const x = (cx.value + rx.value * Math.cos(ang)).toFixed(1)
    const y = (cy.value + ry.value * Math.sin(ang)).toFixed(1)
    out.push({ d: `M${cx.value} ${cy.value} L${x} ${y}`, cur })
  })
  return out
})

// ---------- 当前节点连接中心（金线 flow） ----------
const edges = computed(() => {
  const cur = nodes.value.find((x) => x.isCurrent)
  if (!cur) return []
  return [{ d: `M${cx.value} ${cy.value} L${cur.x} ${cur.y}`, cur: true }]
})
</script>

<style scoped>
.sg {
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
}
.sg__svg {
  width: 100%;
  max-width: 680px;
  height: auto;
  display: block;
  overflow: visible;
}
.sg--mini .sg__svg {
  max-width: 170px;
}
.sg--deco .sg__svg {
  max-width: none;
}

/* 同心蛛丝（虚线椭圆环） */
.sg__ring {
  fill: none;
  stroke: rgba(5, 109, 232, 0.16);
  stroke-width: 0.6;
  stroke-dasharray: 2 4;
}

/* 径向辐条 */
.sg__spoke {
  fill: none;
  stroke: rgba(5, 109, 232, 0.22);
  stroke-width: 0.55;
}
.sg__spoke--cur {
  stroke: rgba(5, 109, 232, 0.55);
  stroke-width: 0.9;
}

/* 当前牵引线 */
.sg__edge--cur {
  fill: none;
  stroke: rgba(5, 109, 232, 0.78);
  stroke-width: 1;
  stroke-dasharray: 3 6;
  animation: sg-flow 1.6s linear infinite;
}
@keyframes sg-flow {
  to {
    stroke-dashoffset: -18;
  }
}

/* 中心：原帖节点 */
.sg__hub {
  transform-origin: center;
}
.sg__hub-ring {
  fill: none;
  stroke: var(--zh-blue-line-strong);
  stroke-width: 0.7;
  animation: sg-breathe 4.2s ease-in-out infinite;
}
.sg__hub-core {
  fill: var(--zh-blue);
  animation: sg-pulse 3.2s ease-in-out infinite;
}
.sg__center-label {
  fill: var(--zh-blue);
  font-size: 12px;
  font-weight: 700;
  text-anchor: middle;
  pointer-events: none;
}

/* 场景节点 */
.sg__node {
  animation: sg-drift 7s ease-in-out infinite;
}
.sg__node-tether {
  fill: none;
  stroke: rgba(5, 109, 232, 0.45);
  stroke-width: 0.55;
  opacity: 0.7;
}
.sg__node-core {
  fill: #8590a6;
  animation: sg-twinkle 3.2s ease-in-out infinite;
}
.sg__node--cur .sg__node-core {
  fill: var(--zh-blue);
}
.sg__node-halo {
  fill: none;
  stroke: var(--zh-blue-line-strong);
  stroke-width: 0.8;
  animation: sg-ping 2.4s ease-out infinite;
  transform-origin: center;
}
.sg__node-label {
  fill: var(--text-2);
  font-size: 11.5px;
  text-anchor: middle;
  pointer-events: none;
}
.sg__node--cur .sg__node-label {
  fill: var(--zh-blue);
}
.sg__empty {
  fill: var(--text-3);
  font-size: 12px;
  text-anchor: middle;
}

@keyframes sg-twinkle {
  0%,
  100% {
    opacity: 0.55;
  }
  50% {
    opacity: 1;
  }
}
@keyframes sg-drift {
  0%,
  100% {
    transform: translate(0, 0);
  }
  50% {
    transform: translate(1.4px, -1.6px);
  }
}
@keyframes sg-ping {
  0% {
    opacity: 0.9;
    transform: scale(0.7);
  }
  100% {
    opacity: 0;
    transform: scale(2.1);
  }
}
@keyframes sg-pulse {
  0%,
  100% {
    opacity: 0.85;
  }
  50% {
    opacity: 1;
  }
}
@keyframes sg-breathe {
  0%,
  100% {
    opacity: 0.4;
  }
  50% {
    opacity: 0.85;
  }
}
@media (prefers-reduced-motion: reduce) {
  .sg__node,
  .sg__node-core,
  .sg__node-halo,
  .sg__hub-core,
  .sg__hub-ring,
  .sg__edge--cur {
    animation: none;
  }
}

.sg__legend {
  display: flex;
  gap: 18px;
  flex-wrap: wrap;
  justify-content: center;
  margin-top: 10px;
  font-size: 12px;
  color: var(--text-3);
}
.sg__legend-item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.sg__dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  display: inline-block;
}
.sg__dot--center {
  background: var(--zh-blue);
}
.sg__dot--cur {
  background: var(--zh-blue);
  box-shadow: 0 0 6px var(--zh-blue);
}
.sg__dot--node {
  background: #8590a6;
  opacity: 0.7;
}
</style>
