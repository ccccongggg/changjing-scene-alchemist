<template>
  <div ref="root" class="mw">
    <div class="mw__legend">
      <span class="mw__legend-k">形状 = 做到了什么</span>
      <i class="mw__sep">·</i>
      <span class="mw__legend-k">材质 = 做到了多深</span>
      <span class="mw__chips">
        <em v-for="t in tally" :key="t.key" class="mw__chip" :class="`mw__chip--${t.key}`">
          {{ t.name }} <b>{{ t.count }}</b>
        </em>
      </span>
      <button class="mw__hint" type="button" @click="scrollBy(1)" aria-label="向右滚动查看更多奖章">
        更多 ›
      </button>
    </div>

    <div ref="scroller" class="mw__scroll">
      <MedalBadge
        v-for="(b, i) in badges"
        :key="b.key"
        :badge="b"
        :index="i"
        :active="active"
        @go="go"
      />
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import MedalBadge from './MedalBadge.vue'

const props = defineProps({
  badges: { type: Array, default: () => [] }
})

const router = useRouter()
const root = ref(null)
const scroller = ref(null)

/* 进场后才让外环从 0 走满、进度条从 0 长出来，这样「进度」才被看见 */
const active = ref(false)
let io = null

onMounted(() => {
  if (typeof IntersectionObserver === 'undefined') {
    active.value = true
    return
  }
  io = new IntersectionObserver(
    (entries) => {
      for (const e of entries) {
        if (e.isIntersecting) {
          active.value = true
          io.disconnect()
          io = null
          break
        }
      }
    },
    { threshold: 0.2 }
  )
  if (root.value) io.observe(root.value)
})

onBeforeUnmount(() => {
  if (io) io.disconnect()
  io = null
})

const tally = computed(() => {
  const order = ['gold', 'silver', 'bronze', 'none']
  const names = { gold: '金', silver: '银', bronze: '铜', none: '未获得' }
  return order
    .map((key) => ({
      key,
      name: names[key],
      count: props.badges.filter((b) => b.tier === key).length
    }))
    .filter((t) => t.count > 0)
})

function scrollBy(dir) {
  const el = scroller.value
  if (!el) return
  el.scrollBy({ left: dir * 340, behavior: 'smooth' })
}

function go(badge) {
  const to = badge?.action?.to
  if (to) router.push(to)
}
</script>

<style scoped>
.mw {
  margin-top: 14px;
}

/* 图例 + 当前档位统计 */
.mw__legend {
  display: flex;
  align-items: center;
  gap: 7px;
  flex-wrap: wrap;
  margin-bottom: 10px;
}
.mw__legend-k {
  font-size: 11.5px;
  color: var(--text-3);
}
.mw__sep {
  font-style: normal;
  color: var(--text-3);
  opacity: 0.6;
}
.mw__chips {
  display: inline-flex;
  gap: 5px;
  margin-left: 4px;
}
.mw__chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 9px;
  border-radius: 999px;
  font-size: 11px;
  font-style: normal;
  color: var(--text-2);
  background: var(--surface-2);
  border: 1px solid var(--border);
}
.mw__chip b {
  font-variant-numeric: tabular-nums;
}
.mw__chip--gold {
  background: rgba(219, 180, 106, 0.1);
  border-color: rgba(231, 184, 115, 0.55);
  color: #dbb46a;
}
.mw__chip--silver {
  background: var(--surface-2);
  border-color: rgba(160, 160, 150, 0.5);
  color: var(--text-2);
}
.mw__chip--bronze {
  background: rgba(219, 180, 106, 0.12);
  border-color: rgba(186, 117, 23, 0.42);
  color: #c9a45c;
}
.mw__chip--none {
  color: var(--text-3);
}

.mw__hint {
  margin-left: auto;
  padding: 3px 11px;
  border-radius: 999px;
  border: 1px solid var(--border-strong);
  background: var(--surface);
  color: var(--text-2);
  font-family: inherit;
  font-size: 11.5px;
  cursor: pointer;
  transition: border-color 0.15s ease, color 0.15s ease;
}
.mw__hint:hover {
  border-color: var(--zh-blue);
  color: var(--zh-blue);
}

/* 横向轨道：窄屏可滚，宽屏平铺 */
.mw__scroll {
  display: flex;
  gap: 12px;
  overflow-x: auto;
  padding: 4px 2px 10px;
  scroll-snap-type: x proximity;
  -webkit-overflow-scrolling: touch;
}
.mw__scroll > * {
  scroll-snap-align: start;
}
.mw__scroll::-webkit-scrollbar {
  height: 6px;
}
.mw__scroll::-webkit-scrollbar-thumb {
  background: var(--border-strong);
  border-radius: 999px;
}

@media (min-width: 920px) {
  .mw__hint {
    display: none;
  }
}
</style>
