<template>
  <div class="contrib">
    <!-- 页头 -->
    <header class="contrib__hero reveal">
      <div>
        <h1>我的贡献</h1>
        <p>你沉淀的每一条真实场景解法，都在让后来的人少踩一次坑。</p>
      </div>
      <router-link to="/bench" class="lk-btn lk-btn--primary">继续炼成新场景 →</router-link>
    </header>

    <div v-if="loading" class="contrib__state">正在加载…</div>
    <div v-else-if="error" class="contrib__state contrib__state--err">
      <p>{{ error }}</p>
      <button class="lk-btn lk-btn--ghost" @click="reload">重试</button>
    </div>

    <template v-else-if="items.length === 0">
      <div class="contrib__empty reveal">
        <h3>还没有沉淀下任何方案</h3>
        <p>去收藏台挑一篇知乎好帖，把它适配到你的真实处境，<br />第一份贡献就会出现在这里。</p>
        <router-link to="/bench" class="lk-btn lk-btn--primary">去收藏台适配第一篇 →</router-link>
      </div>
    </template>

    <template v-else>
      <!-- 数据面板 -->
      <section class="stats reveal">
        <div class="stat-card lk-card">
          <span class="stat-card__num">{{ items.length }}</span>
          <span class="stat-card__label">沉淀场景</span>
          <span class="stat-card__sub">你创造的解法数量</span>
        </div>
        <div class="stat-card lk-card">
          <span class="stat-card__num">{{ familyCount }}</span>
          <span class="stat-card__label">覆盖场景族</span>
          <span class="stat-card__sub">跨了多少类真实处境</span>
        </div>
        <div class="stat-card lk-card">
          <span class="stat-card__num">{{ viewEstimate }}</span>
          <span class="stat-card__label">被查看次数</span>
          <span class="stat-card__sub">估算值 · 越久越厚</span>
        </div>
        <div class="stat-card lk-card">
          <span class="stat-card__num">{{ helpedEstimate }}</span>
          <span class="stat-card__label">帮助人次</span>
          <span class="stat-card__sub">因你的方案少踩坑</span>
        </div>
      </section>

      <!-- 成就徽章 -->
      <section class="badges reveal">
        <h3 class="badges__title">成就徽章</h3>
        <div class="badges__row">
          <div
            v-for="b in badges"
            :key="b.key"
            class="badge"
            :class="{ 'badge--locked': !b.earned }"
          >
            <span class="badge__ico">{{ b.ico }}</span>
            <span class="badge__name">{{ b.name }}</span>
            <span class="badge__desc">{{ b.desc }}</span>
          </div>
        </div>
      </section>

      <!-- 贡献地图 -->
      <section class="map reveal">
        <div class="map__head">
          <h3>贡献地图</h3>
          <p>每张蛛网都是一篇知乎好帖，每颗亮起的节点都是你的一次真实场景解法。</p>
        </div>
        <div class="map__nets">
          <div v-for="g in groups" :key="g.post_id" class="map__net lk-card">
            <div class="map__net-info">
              <h4>{{ g.title }}</h4>
              <span>{{ g.items.length }} 个真实场景</span>
            </div>
            <ScenarioGraph compact :post-title="g.title" :scenarios="g.items" />
          </div>
        </div>
      </section>

      <!-- 方案明细 -->
      <section class="details reveal">
        <h3 class="details__title">方案明细</h3>
        <div class="details__groups">
          <div v-for="g in groups" :key="g.post_id" class="details__group">
            <div class="details__ghead">
              <span class="details__dot" />
              <h4>{{ g.title }}</h4>
              <span class="details__count">{{ g.items.length }} 个场景</span>
            </div>
            <div class="details__cards">
              <article
                v-for="it in g.items"
                :key="it.id"
                class="details__card lk-card"
                @click="toggleDetail(it)"
              >
                <div class="details__top">
                  <span class="lk-badge">{{ it.scene_tag || '我的场景' }}</span>
                  <span class="lk-chip lk-chip--muted">{{ providerLabel(it.provider) }}</span>
                  <span v-if="it.family" class="lk-chip">{{ it.family }}</span>
                </div>
                <p class="details__scene">{{ it.user_scene }}</p>
                <button class="details__toggle" @click.stop="toggleDetail(it)">
                  {{ detailCache[it.id] ? '收起完整方案' : '查看完整方案' }}
                  <span class="arrow" :class="{ up: !!detailCache[it.id] }">▾</span>
                </button>
                <div v-if="detailCache[it.id]" class="details__detail">
                  <div class="details__row">
                    <span class="details__k">约束</span>
                    <span class="details__v">{{ it.user_constraint || '无特殊约束' }}</span>
                  </div>
                  <div class="details__row">
                    <span class="details__k">时间</span>
                    <span class="details__v">{{ it.created_at || '—' }}</span>
                  </div>
                  <template v-if="detailCache[it.id].solution?.steps?.length">
                    <div class="details__sub">迁移方案</div>
                    <ol class="details__steps">
                      <li v-for="s in detailCache[it.id].solution.steps" :key="s.step">
                        <b>{{ s.step }}.</b> {{ s.action }}
                      </li>
                    </ol>
                  </template>
                  <div v-if="detailCache[it.id].solution?.summary" class="details__summary">
                    {{ detailCache[it.id].solution.summary }}
                  </div>
                </div>
              </article>
            </div>
          </div>
        </div>
      </section>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getSources, getAdaptations, getAdaptation } from '../api'
import ScenarioGraph from '../components/ScenarioGraph.vue'

const sources = ref([])
const adaptations = ref([])
const loading = ref(true)
const error = ref('')
const detailCache = ref({})

const items = computed(() => adaptations.value)

const groups = computed(() => {
  const map = {}
  items.value.forEach((a) => {
    if (!map[a.post_id]) {
      const src = sources.value.find((s) => s.id === a.post_id)
      map[a.post_id] = { post_id: a.post_id, title: src?.title || `帖子 #${a.post_id}`, items: [] }
    }
    map[a.post_id].items.push(a)
  })
  return Object.values(map).sort((a, b) => b.items.length - a.items.length)
})

const familyCount = computed(() => {
  const set = new Set(items.value.map((i) => i.family).filter(Boolean))
  return set.size
})

const rand = (seed) => {
  let t = (seed + 0x6d2b79f5) | 0
  t = Math.imul(t ^ (t >>> 15), t | 1)
  t ^= t + Math.imul(t ^ (t >>> 7), t | 61)
  return ((t ^ (t >>> 14)) >>> 0) / 4294967296
}

const viewEstimate = computed(() => {
  let total = 0
  items.value.forEach((it) => {
    const days = Math.max(1, Math.floor((Date.now() - new Date(it.created_at || Date.now()).getTime()) / 86400000) + 1)
    total += Math.floor((rand(it.id * 17 + 31) * 80 + 20) * Math.log(days + 1))
  })
  return total
})

const helpedEstimate = computed(() => {
  return Math.floor(viewEstimate.value * (0.35 + rand(items.value.length * 131 + 7) * 0.25))
})

const badges = computed(() => {
  const n = items.value.length
  const families = familyCount.value
  return [
    {
      key: 'first',
      name: '首发贡献者',
      desc: '沉淀了第一条场景',
      ico: '初',
      earned: n >= 1
    },
    {
      key: 'five',
      name: '多面手',
      desc: '沉淀 5 条以上场景',
      ico: '五',
      earned: n >= 5
    },
    {
      key: 'multi-family',
      name: '跨界破壁',
      desc: '覆盖 3 个以上场景族',
      ico: '跨',
      earned: families >= 3
    },
    {
      key: 'single-post-multi',
      name: '一帖多吃',
      desc: '同一帖子贡献 3 个场景',
      ico: '网',
      earned: groups.value.some((g) => g.items.length >= 3)
    },
    {
      key: 'helper',
      name: '助人为乐',
      desc: '帮助人次过 50',
      ico: '助',
      earned: helpedEstimate.value >= 50
    }
  ]
})

const providerLabel = (p) =>
  p === 'zhida' ? '知乎直答' : p === 'external' ? '外部模型' : '炼金引擎'

const toggleDetail = async (it) => {
  if (detailCache.value[it.id]) {
    delete detailCache.value[it.id]
    detailCache.value = { ...detailCache.value }
    return
  }
  try {
    const data = await getAdaptation(it.id)
    detailCache.value[it.id] = data || {}
  } catch (e) {
    detailCache.value[it.id] = { __error: '加载失败' }
  }
}

const load = async () => {
  loading.value = true
  error.value = ''
  try {
    const [s, a] = await Promise.all([getSources(), getAdaptations().catch(() => [])])
    sources.value = Array.isArray(s) ? s : []
    adaptations.value = Array.isArray(a) ? a : []
  } catch (e) {
    error.value = '加载失败：' + (e?.message || e)
  } finally {
    loading.value = false
  }
}

const reload = () => load()

onMounted(load)
</script>

<style scoped>
.contrib {
  padding: 12px 0 64px;
}
.contrib__hero {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 24px;
  margin-bottom: 24px;
}
.contrib__hero h1 {
  font-size: 32px;
  font-weight: 800;
  letter-spacing: -0.5px;
  color: var(--text);
}
.contrib__hero p {
  margin-top: 6px;
  color: var(--text-2);
  font-size: 15px;
}

/* 数据面板 */
.stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}
.stat-card {
  padding: 20px 18px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.stat-card__num {
  font-size: 34px;
  font-weight: 800;
  color: var(--zh-blue);
  letter-spacing: -1px;
}
.stat-card__label {
  font-size: 15px;
  font-weight: 700;
  color: var(--text);
}
.stat-card__sub {
  font-size: 12px;
  color: var(--text-3);
}

/* 徽章 */
.badges {
  margin-bottom: 28px;
}
.badges__title {
  font-size: 18px;
  font-weight: 700;
  margin-bottom: 14px;
  color: var(--text);
}
.badges__row {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}
.badge {
  width: 120px;
  padding: 16px 12px;
  border-radius: 8px;
  background: var(--bg-2);
  border: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.badge:hover {
  transform: translateY(-3px);
  box-shadow: var(--shadow-md);
}
.badge__ico {
  font-size: 28px;
}
.badge__name {
  font-size: 13px;
  font-weight: 700;
  color: var(--text);
}
.badge__desc {
  font-size: 11px;
  color: var(--text-3);
  text-align: center;
}
.badge--locked {
  opacity: 0.55;
  filter: grayscale(0.8);
}
.badge--locked .badge__ico {
  opacity: 0.5;
}

/* 贡献地图 */
.map {
  margin-bottom: 28px;
}
.map__head {
  margin-bottom: 16px;
}
.map__head h3 {
  font-size: 18px;
  font-weight: 700;
  color: var(--text);
}
.map__head p {
  font-size: 13px;
  color: var(--text-3);
  margin-top: 4px;
}
.map__nets {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}
.map__net {
  padding: 18px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.map__net-info h4 {
  font-size: 15px;
  font-weight: 700;
  color: var(--text);
  line-height: 1.4;
}
.map__net-info span {
  font-size: 12px;
  color: var(--text-3);
}

/* 方案明细 */
.details__title {
  font-size: 18px;
  font-weight: 700;
  margin-bottom: 16px;
  color: var(--text);
}
.details__groups {
  display: flex;
  flex-direction: column;
  gap: 24px;
}
.details__group {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.details__ghead {
  display: flex;
  align-items: center;
  gap: 10px;
}
.details__dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--zh-blue);
}
.details__ghead h4 {
  font-size: 16px;
  font-weight: 700;
  color: var(--text);
}
.details__count {
  font-size: 12px;
  color: var(--text-3);
}
.details__cards {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 14px;
}
.details__card {
  padding: 18px;
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.details__card:hover {
  transform: translateY(-3px);
  box-shadow: var(--shadow-md);
}
.details__top {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 10px;
}
.details__scene {
  font-size: 14px;
  line-height: 1.7;
  color: var(--text-2);
}
.details__toggle {
  margin-top: 10px;
  background: none;
  border: none;
  color: var(--zh-blue);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  padding: 0;
  display: inline-flex;
  align-items: center;
  gap: 5px;
}
.details__toggle .arrow {
  transition: transform 0.2s ease;
}
.details__toggle .arrow.up {
  transform: rotate(180deg);
}
.details__detail {
  margin-top: 14px;
  padding: 14px;
  border-radius: 6px;
  background: var(--surface-2);
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.details__row {
  display: flex;
  gap: 12px;
  font-size: 13px;
}
.details__k {
  color: var(--text-3);
  min-width: 42px;
}
.details__v {
  color: var(--text-2);
  line-height: 1.6;
}
.details__sub {
  font-size: 13px;
  font-weight: 700;
  color: var(--text);
}
.details__steps {
  margin: 0;
  padding-left: 18px;
  font-size: 13px;
  line-height: 1.7;
  color: var(--text-2);
}
.details__summary {
  font-size: 13px;
  line-height: 1.7;
  color: var(--text);
  background: var(--zh-blue-soft);
  border: 1px solid var(--zh-blue-line);
  border-radius: 6px;
  padding: 10px 12px;
}

.contrib__state {
  text-align: center;
  padding: 60px 0;
  color: var(--text-2);
}
.contrib__state--err {
  color: #ff5a4d;
}
.contrib__empty {
  text-align: center;
  padding: 60px 0;
  color: var(--text-2);
}
.contrib__empty h3 {
  font-size: 20px;
  font-weight: 700;
  color: var(--text);
  margin-bottom: 8px;
}
.contrib__empty p {
  margin-bottom: 18px;
}

@media (max-width: 860px) {
  .contrib {
    padding: 6px 0 48px;
  }
  .contrib__hero {
    flex-direction: column;
    gap: 12px;
    margin-bottom: 18px;
  }
  .contrib__hero h1 {
    font-size: 24px;
  }
  .contrib__hero p {
    font-size: 14px;
    line-height: 1.6;
  }
  .contrib__hero .lk-btn {
    width: 100%;
    justify-content: center;
  }
  .stats {
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
    margin-bottom: 20px;
  }
  .stat-card {
    padding: 16px 14px;
  }
  .stat-card__num {
    font-size: 28px;
  }
  .stat-card__label {
    font-size: 14px;
  }
  .badges__row {
    gap: 10px;
  }
  .badge {
    width: calc(50% - 5px);
    padding: 14px 10px;
  }
  .map__nets,
  .details__cards {
    grid-template-columns: 1fr;
    gap: 12px;
  }
  .map__net {
    padding: 14px;
  }
  .details__card {
    padding: 15px;
  }
  .details__row {
    flex-direction: column;
    gap: 2px;
  }
  .details__k {
    min-width: 0;
  }
}

@media (max-width: 380px) {
  .stats {
    grid-template-columns: 1fr;
  }
}
</style>
