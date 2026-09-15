<template>
  <div
    class="mb"
    :class="[`mb--${badge.tier}`, { 'is-flipped': flipped, 'is-in': active }]"
    :style="{ '--i': index, '--mb-accent': tone.accent, '--mb-bg': tone.cardBg }"
  >
    <span class="mb__beam" aria-hidden="true" />

    <!-- 正面遮罩：单击翻面；Esc 翻回 -->
    <button
      class="mb__hit"
      type="button"
      :aria-label="ariaLabel"
      :aria-pressed="flipped"
      @click="flipped = !flipped"
      @keydown.esc="flipped = false"
    />
    <!-- 背面的直达按钮：只在翻面后出现，避免无障碍树里出现两个翻转控件 -->
    <button
      v-if="flipped"
      class="mb__go"
      type="button"
      @click.stop="$emit('go', badge)"
    >
      {{ badge.action.label }} ↗
    </button>

    <span class="mb__stage">
      <!-- ============ 正面 ============ -->
      <span class="mb__face mb__face--front">
        <!-- 奖章本体 = AI 生成的徽记照片（圆形裁切，见 _medal_src/make.py）。
             外圈那道材质环 + 进度弧用 SVG 叠在上面：图片是固定的，进度得是活的。 -->
        <span class="mb__medal">
          <img class="mb__disc" :src="art" alt="" draggable="false" decoding="async" />
          <span class="mb__shine" aria-hidden="true" />
          <svg class="mb__ring" viewBox="0 0 122 122" aria-hidden="true">
            <circle
              cx="61"
              cy="61"
              r="57"
              fill="none"
              :stroke="tone.ring"
              :stroke-width="tone.ringWidth"
              :stroke-dasharray="tone.ringDash ? '5 6' : null"
            />
            <circle
              v-if="arcLen > 0.5"
              class="mb__prog"
              cx="61"
              cy="61"
              r="57"
              fill="none"
              :stroke="arcColor"
              stroke-width="3.4"
              stroke-linecap="round"
              :stroke-dasharray="`${arcLen.toFixed(2)} ${CIRC.toFixed(2)}`"
              :stroke-dashoffset="active ? 0 : arcLen.toFixed(2)"
              transform="rotate(-90 61 61)"
            />
          </svg>
        </span>

        <!-- 名字挂在饰带上（和原图里的缎带同一个位置：压在圆盘下沿） -->
        <span
          class="mb__ribbon"
          :style="{ background: tone.ribbonBg, color: tone.ribbonFg, borderColor: tone.ribbonLine }"
        >
          {{ badge.name }}
        </span>

        <span class="mb__meta">
          <em class="mb__tier">{{ tierShort }}</em>
          <em class="mb__pct">{{ pctText }}</em>
        </span>
        <span class="mb__bar" aria-hidden="true"><i :style="{ width: active ? pctText : '0%' }" /></span>
      </span>

      <!-- ============ 背面 ============ -->
      <span class="mb__face mb__face--back">
        <span class="mb__b-name">{{ badge.name }}</span>
        <span class="mb__b-form">{{ badge.form }} · {{ badge.desc }}</span>
        <span class="mb__b-now">{{ badge.metric }} <b>{{ badge.value }}</b> {{ badge.unit }}</span>
        <span class="mb__b-lines">
          <span
            v-for="(l, i) in badge.lines"
            :key="i"
            class="mb__b-line"
            :class="{ 'is-on': l.got }"
          >
            <i class="mb__b-dot" />{{ l.name }} {{ l.value }}
          </span>
        </span>
        <span class="mb__b-next">{{ nextText }}</span>
        <span class="mb__b-slot" aria-hidden="true" />
      </span>
    </span>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { MEDAL_ART, TONES, TIER_META } from '../data/medalEmblems'

const props = defineProps({
  badge: { type: Object, required: true },
  index: { type: Number, default: 0 },
  active: { type: Boolean, default: false }
})
defineEmits(['go'])

const CIRC = 2 * Math.PI * 57 // 进度外环周长（r=57），≈358.14

const flipped = ref(false)

const tone = computed(() => TONES[props.badge.tier] || TONES.none)
const art = computed(() => MEDAL_ART[props.badge.key] || MEDAL_ART.first)
const tierShort = computed(() => (TIER_META[props.badge.tier] || TIER_META.none).short)

/* 外环画的是「下一档」的金属色；已满级（金）则用金色 */
const arcColor = computed(() => {
  const b = props.badge
  if (b.tier === 'gold') return TONES.gold.ring
  if (b.tier === 'silver') return TONES.gold.ring
  if (b.tier === 'bronze') return TONES.silver.ring
  return TONES.bronze.ring
})

const arcLen = computed(() => CIRC * (props.badge.progress || 0))
const pctText = computed(() => `${Math.round((props.badge.progress || 0) * 100)}%`)

const nextShort = computed(() => {
  const b = props.badge
  if (b.value >= b.tiers[2]) return ''
  if (b.value >= b.tiers[1]) return '金牌'
  if (b.value >= b.tiers[0]) return '银牌'
  return '铜牌'
})

const nextText = computed(() =>
  props.badge.nextVal ? `距${nextShort.value}还差 ${props.badge.remaining} ${props.badge.unit}` : '已满级 · 金色'
)

const ariaLabel = computed(() => {
  const b = props.badge
  const t = (TIER_META[b.tier] || TIER_META.none).full
  return `${b.name}（${b.form}）· ${t} · ${b.metric} ${b.value} ${b.unit}${b.nextVal ? `，${nextText.value}` : ''}`
})
</script>

<style scoped>
.mb {
  position: relative;
  flex: none;
  width: 152px;
  height: 200px;
  border-radius: 14px;
  border: 1px solid var(--border);
  background: var(--mb-bg, var(--surface-2));
  overflow: hidden;
  transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
}
.mb:hover {
  transform: translateY(-3px);
  border-color: var(--mb-accent);
  box-shadow: 0 10px 24px rgba(15, 30, 60, 0.12);
}

/* 顶部光带：按 --i 依次扫过，这就是「流动」 */
.mb__beam {
  position: absolute;
  top: 0;
  left: 0;
  z-index: 4;
  width: 45%;
  height: 2px;
  pointer-events: none;
  background: linear-gradient(90deg, transparent, var(--mb-accent), transparent);
  animation: beamSweep 3.2s linear infinite;
  animation-delay: calc(var(--i) * 0.22s);
  transform: translateX(-110%);
}
.mb--none .mb__beam {
  opacity: 0.5;
}
.mb:hover .mb__beam {
  animation-duration: 1.1s;
}
@keyframes beamSweep {
  0% {
    transform: translateX(-110%);
  }
  100% {
    transform: translateX(320%);
  }
}

/* 正面遮罩：单击翻面 */
.mb__hit {
  position: absolute;
  inset: 0;
  z-index: 2;
  border: none;
  background: transparent;
  cursor: pointer;
  padding: 0;
}
.mb__hit:focus-visible {
  outline: none;
}
.mb:has(.mb__hit:focus-visible) {
  outline: 2px solid var(--mb-accent);
  outline-offset: 2px;
}

/* 背面直达按钮 */
.mb__go {
  position: absolute;
  left: 10px;
  right: 10px;
  bottom: 11px;
  z-index: 3;
  padding: 7px 6px;
  border-radius: 8px;
  border: 1px solid var(--mb-accent);
  background: var(--mb-accent);
  color: #fff;
  font-family: inherit;
  font-size: 11.5px;
  font-weight: 600;
  cursor: pointer;
  transition: filter 0.15s ease;
}
.mb--silver .mb__go,
.mb--gold .mb__go,
.mb--none .mb__go {
  color: #2c2c2a;
}
.mb__go:hover {
  filter: brightness(1.08);
}

/* 3D 翻面 */
.mb__stage {
  position: absolute;
  inset: 0;
  display: block;
  transform-style: preserve-3d;
  transition: transform 0.5s cubic-bezier(0.22, 1, 0.36, 1);
  will-change: transform;
}
.mb.is-flipped .mb__stage {
  transform: rotateY(180deg);
}
.mb__face {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 10px 10px 12px;
  backface-visibility: hidden;
  -webkit-backface-visibility: hidden;
}
.mb__face--back {
  transform: rotateY(180deg);
  align-items: flex-start;
}

/* ---------- 正面 ---------- */
/* 奖章本体：图片是圆盘（已按圆裁好，512²），外圈那道材质环 + 进度弧用 SVG 叠在上面。
   盘 106px；SVG 122px、往四面各撑 8px，所以 viewBox 里盘缘在 r=53、环画在 r=57（盘外 4）。
   比原来的 SVG 画法省了一整套 clipPath / gradient，也就不需要每枚唯一的 id。 */
.mb__medal {
  position: relative;
  flex: none;
  width: 106px;
  height: 106px;
  margin-top: 6px;
}
.mb__disc {
  display: block;
  width: 100%;
  height: 100%;
  border-radius: 50%;
  object-fit: cover;
  /* 材质不到档时整枚去色：「还没拿到」要一眼看出来 */
  filter: var(--mb-filter, none);
  transition: filter 0.25s ease;
}
.mb--none .mb__disc {
  --mb-filter: grayscale(1) contrast(0.9) opacity(0.5);
}
/* 环画在盘的**外面**：比盘大 16px（两边各 8），122 的 viewBox 里盘缘在 r=53、环在 r=57 */
.mb__ring {
  position: absolute;
  left: -8px;
  top: -8px;
  width: 122px;
  height: 122px;
  pointer-events: none;
  overflow: visible;
}
.mb__prog {
  transition: stroke-dashoffset 0.8s cubic-bezier(0.22, 1, 0.36, 1);
  transition-delay: calc(var(--i) * 0.06s);
}
/* 镜面反光：一道斜向的亮带扫过盘面。圆形靠父级 border-radius 裁住，
   所以不需要 SVG clipPath（也就不需要每枚唯一的 id）。 */
.mb__shine {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  overflow: hidden;
  pointer-events: none;
}
.mb__shine::after {
  content: '';
  position: absolute;
  top: -30%;
  left: -60%;
  width: 45%;
  height: 160%;
  transform: rotate(18deg) translateX(0);
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.5), transparent);
  animation: shineSweep 6s ease-in-out infinite;
  animation-delay: calc(var(--i) * 0.4s);
}
.mb--none .mb__shine {
  display: none;
}
@keyframes shineSweep {
  0%,
  58% {
    transform: rotate(18deg) translateX(0);
  }
  76%,
  100% {
    transform: rotate(18deg) translateX(320%);
  }
}
/* 名字挂在饰带上：和原图里缎带的同一个位置 —— 压在圆盘下沿，底部剪一个 V 口 */
.mb__ribbon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 92px;
  height: 26px;
  margin-top: -8px;
  padding-bottom: 5px;
  border-radius: 3px 3px 0 0;
  clip-path: polygon(0 0, 100% 0, 100% 100%, 50% 74%, 0 100%);
  /* clip-path 会把 box-shadow 一起裁掉 —— 阴影得走 filter（在裁剪之后才生效） */
  filter: drop-shadow(0 3px 5px rgba(15, 30, 60, 0.22));
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.3px;
  white-space: nowrap;
}
.mb__meta {
  margin-top: 6px;
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  line-height: 1.4;
}
.mb__tier {
  font-style: normal;
  font-weight: 700;
  color: var(--mb-accent);
}
.mb--none .mb__tier {
  color: var(--text-3);
}
.mb__pct {
  font-style: normal;
  color: var(--text-3);
  font-variant-numeric: tabular-nums;
}
.mb__bar {
  display: block;
  width: 100%;
  height: 4px;
  margin-top: 5px;
  border-radius: 999px;
  background: var(--surface-3);
  overflow: hidden;
}
.mb__bar i {
  display: block;
  height: 100%;
  border-radius: 999px;
  background: var(--mb-accent);
  transition: width 0.8s cubic-bezier(0.22, 1, 0.36, 1);
  transition-delay: calc(var(--i) * 0.06s);
}

/* ---------- 背面 ---------- */
.mb__b-name {
  font-size: 13.5px;
  font-weight: 700;
  color: var(--text);
}
.mb__b-form {
  margin-top: 2px;
  font-size: 10.5px;
  color: var(--text-3);
  line-height: 1.45;
}
.mb__b-now {
  margin-top: 8px;
  font-size: 11.5px;
  color: var(--text-2);
}
.mb__b-now b {
  font-size: 14px;
  color: var(--mb-accent);
  font-variant-numeric: tabular-nums;
}
.mb--none .mb__b-now b {
  color: var(--text-2);
}
.mb__b-lines {
  margin-top: 7px;
  display: flex;
  flex-wrap: wrap;
  gap: 4px 8px;
}
.mb__b-line {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  font-size: 10.5px;
  color: var(--text-3);
  font-variant-numeric: tabular-nums;
}
.mb__b-line.is-on {
  color: var(--text-2);
  font-weight: 600;
}
.mb__b-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  border: 1px solid var(--text-3);
  background: transparent;
}
.mb__b-line.is-on .mb__b-dot {
  background: var(--mb-accent);
  border-color: var(--mb-accent);
}
.mb__b-next {
  margin-top: 7px;
  font-size: 10.5px;
  line-height: 1.45;
  color: var(--text-3);
}
.mb__b-slot {
  display: block;
  height: 30px;
  margin-top: auto;
}

@media (prefers-reduced-motion: reduce) {
  .mb,
  .mb__stage,
  .mb__prog,
  .mb__bar i {
    transition: none !important;
  }
  .mb__beam,
  .mb__shine {
    animation: none !important;
  }
}
</style>
