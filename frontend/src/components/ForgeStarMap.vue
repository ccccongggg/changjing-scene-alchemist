<template>
  <div class="forge-map">
    <svg class="fm" viewBox="0 0 360 360" role="img" aria-label="炼场景星图引导">
      <!-- 星尘点阵背景 -->
      <g class="fm__dust">
        <circle v-for="(d, i) in dust" :key="i" :cx="d.x" :cy="d.y" :r="d.r" />
      </g>

      <!-- 轨道线（从星核到各步骤节点） -->
      <g class="fm__orbits">
        <line
          v-for="(n, i) in nodes"
          :key="'o' + i"
          :x1="cx"
          :y1="cy"
          :x2="n.x"
          :y2="n.y"
          :class="['fm__orbit', { 'is-lit': i < progress || i === active }]"
        />
      </g>

      <!-- 星核（中心：我的场景） -->
      <g class="fm__core" :transform="`translate(${cx} ${cy})`">
        <circle class="fm__core-halo" r="40" />
        <circle class="fm__core-planet" :r="R_CORE" />
        <circle class="fm__core-ring" :r="R_CORE + 6" />
        <text class="fm__core-t1" y="-2">我的</text>
        <text class="fm__core-t2" y="14">场景</text>
      </g>

      <!-- 步骤节点 -->
      <g
        v-for="(n, i) in nodes"
        :key="'n' + i"
        class="fm__node"
        :class="stateClass(i)"
        :transform="`translate(${n.x} ${n.y})`"
        @click="$emit('select', i)"
      >
        <circle class="fm__node-dot" :r="R_NODE" />
        <circle v-if="i === active" class="fm__node-pulse" :r="R_NODE" />
        <text class="fm__node-idx" y="4">{{ i + 1 }}</text>
        <text
          class="fm__node-label"
          :x="n.lx"
          :y="n.ly"
          :text-anchor="n.anchor"
        >{{ n.label }}</text>
      </g>
    </svg>

    <p class="fm__caption">星图陪你一步步把真实场景炼清楚 · 右侧随时可输入</p>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  steps: { type: Array, default: () => [] }, // [{ label }]
  progress: { type: Number, default: 0 }, // 已经走过的步骤数
  active: { type: Number, default: 0 } // 当前所在步骤
})
defineEmits(['select'])

const cx = 180
const cy = 180
const R_CORE = 30
const R_NODE = 15

// 5 个步骤节点沿椭圆轨道均布（顶部起，顺时针）
const ANGLES = [-90, -18, 54, 126, 198]
const RX = 132
const RY = 122

function posFor(angleDeg, i) {
  const a = (angleDeg * Math.PI) / 180
  const x = cx + RX * Math.cos(a)
  const y = cy + RY * Math.sin(a)
  // 标签放在节点外侧
  const right = x >= cx
  const lx = right ? R_NODE + 8 : -(R_NODE + 8)
  const ly = y < cy - 40 ? -R_NODE - 4 : y > cy + 40 ? R_NODE + 14 : 4
  return { x, y, lx, ly, anchor: right ? 'start' : 'end' }
}

const nodes = computed(() =>
  props.steps.map((s, i) => ({ label: s.label, ...posFor(ANGLES[i] ?? -90, i) }))
)

// 随机但稳定的星尘
const dust = Array.from({ length: 46 }, (_, i) => {
  const rnd = (n) => {
    // 固定种子，避免每次渲染抖动
    const v = Math.sin((i + 1) * (n + 7)) * 43758.5453
    return v - Math.floor(v)
  }
  return {
    x: Math.round(rnd(1) * 360),
    y: Math.round(rnd(2) * 360),
    r: (0.6 + rnd(3) * 1.6).toFixed(2)
  }
})

function stateClass(i) {
  if (i === props.active) return 'is-active'
  if (i < props.progress) return 'is-done'
  return 'is-future'
}
</script>

<style scoped>
.forge-map {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}
.fm {
  width: 100%;
  max-width: 360px;
  height: auto;
  display: block;
}
.fm__dust circle {
  fill: var(--nbg-line-2, rgba(5, 109, 232, 0.32));
  opacity: 0.5;
}
.fm__orbit {
  stroke: var(--border-strong, #d8d8d8);
  stroke-width: 1.5;
  stroke-dasharray: 3 5;
  opacity: 0.55;
}
.fm__orbit.is-lit {
  stroke: var(--zh-blue, #056de8);
  stroke-dasharray: none;
  opacity: 0.85;
}

/* 星核 */
.fm__core-halo {
  fill: var(--zh-blue-soft, #ebf3ff);
  opacity: 0.7;
}
.fm__core-planet {
  fill: var(--st-core-2, #ffc65c);
}
.fm__core-ring {
  fill: none;
  stroke: var(--st-core, #e79a1f);
  stroke-width: 2.5;
}
.fm__core-t1,
.fm__core-t2 {
  fill: #5a3b00;
  font-size: 12px;
  font-weight: 800;
  text-anchor: middle;
}

/* 步骤节点 */
.fm__node {
  cursor: pointer;
}
.fm__node-dot {
  fill: #ffffff;
  stroke: var(--st-untouched, #c3cbdc);
  stroke-width: 2.5;
}
.fm__node-idx {
  fill: var(--text-3, #8590a6);
  font-size: 13px;
  font-weight: 800;
  text-anchor: middle;
}
.fm__node-label {
  fill: var(--text-2, #444444);
  font-size: 12.5px;
  font-weight: 600;
}
.fm__node.is-done .fm__node-dot {
  fill: var(--st-mastered, #14a44d);
  stroke: var(--st-mastered, #14a44d);
}
.fm__node.is-done .fm__node-idx {
  fill: #ffffff;
}
.fm__node.is-active .fm__node-dot {
  fill: #ffffff;
  stroke: var(--zh-blue, #056de8);
  stroke-width: 3.5;
}
.fm__node.is-active .fm__node-idx {
  fill: var(--zh-blue, #056de8);
}
.fm__node.is-active .fm__node-label {
  fill: var(--zh-blue, #056de8);
}
.fm__node-pulse {
  fill: none;
  stroke: var(--zh-blue, #056de8);
  stroke-width: 2;
  opacity: 0;
  transform-origin: center;
  animation: fm-pulse 1.8s ease-out infinite;
}
@keyframes fm-pulse {
  0% {
    transform: scale(1);
    opacity: 0.6;
  }
  100% {
    transform: scale(2.1);
    opacity: 0;
  }
}
.fm__caption {
  margin: 0;
  font-size: 12px;
  color: var(--text-3, #8590a6);
  text-align: center;
  line-height: 1.6;
}
@media (prefers-reduced-motion: reduce) {
  .fm__node-pulse {
    animation: none;
    display: none;
  }
}

/* ===== 小屏（手机）：星图引导 caption 保持可读 ===== */
@media (max-width: 480px) {
  .fm__caption {
    font-size: 11.5px;
    padding: 0 6px;
  }
  .fm__node-label {
    font-size: 12px;
  }
}
</style>
