<template>
  <div class="start">
    <!-- ========== HERO：新版简洁 + 旧版内容 ========== -->
    <section class="hero">
      <div class="hero__left reveal" :style="{ '--i': 0 }">
        <span class="eyebrow">
          <span class="dot" />知识炼金场 · 同帖千面
        </span>

        <h1 class="hero__title">
          让每一条知乎好帖，<br />
          长出<span class="lk-grad">千个面孔</span>
        </h1>

        <p class="hero__sub">
          真实场景 <b>×</b> AI 起草 <b>×</b> 人验证。<br />
          把同一道题在不同真实处境下暴露的真问题，沉淀成一张可检索的<strong>场景应用网</strong>——
          当任何人遇到它，都能找到贴合自己的那一种解法。
        </p>

        <div class="hero__cta">
          <router-link v-if="firstId" :to="`/adapt/${firstId}`" class="lk-btn lk-btn--primary">
            进入第一篇好帖 <span class="arrow">→</span>
          </router-link>
          <a href="#recent" class="lk-btn lk-btn--ghost">看看收藏台</a>
        </div>

        <div class="hero__stats">
          <div class="stat">
            <span class="stat__num">{{ stats.sources }}</span>
            <span class="stat__label">好帖已入炉</span>
          </div>
          <span class="stat__sep" />
          <div class="stat">
            <span class="stat__num">{{ stats.scenes }}</span>
            <span class="stat__label">真实场景沉淀</span>
          </div>
          <span class="stat__sep" />
          <div class="stat">
            <span class="stat__num">{{ stats.families }}</span>
            <span class="stat__label">场景族覆盖</span>
          </div>
        </div>
      </div>

      <div class="hero__right reveal" :style="{ '--i': 2 }">
        <div class="orb" />
        <div class="hero__card">
          <img class="hero__mascot" src="/liukan/hi.gif" alt="刘看山" />
          <div class="hero__speech">
            “这篇我也踩过坑——<br />你的场景，和我的不一样吧？”
          </div>
          <span
            v-for="(chip, i) in floatChips"
            :key="chip"
            class="float-chip"
            :style="chipPositions[i]"
          >{{ chip }}</span>
        </div>
      </div>
    </section>

    <!-- ========== 三步闭环 ========== -->
    <section id="loop" class="loop">
      <div class="section-head reveal">
        <h2>不是「问 AI」，是<strong class="lk-grad"> 把经验炼成网</strong></h2>
        <p>单次问答用完即弃；这里每一次适配都留在帖子里，越用越厚。</p>
      </div>

      <div class="loop__grid">
        <article class="loop__step lk-card reveal" :style="{ '--i': 0 }">
          <span class="loop__no">01</span>
          <h3>你来描述真实场景</h3>
          <p>粘贴链接、或一句话说清处境与约束。低门槛三态输入，不用会写也能表达。</p>
        </article>
        <article class="loop__step lk-card reveal" :style="{ '--i': 1 }">
          <span class="loop__no">02</span>
          <h3>AI 起草方案迁移</h3>
          <p>解构原帖解法，映射到你的场景差异点，产出可改写的初稿，而非标准答案。</p>
        </article>
        <article class="loop__step lk-card reveal" :style="{ '--i': 2 }">
          <span class="loop__no">03</span>
          <h3>你拍板，沉淀入库</h3>
          <p>人验证后这条场景正式入库。下一个人遇到同类处境，直接复用你的真解。</p>
        </article>
      </div>
    </section>

    <!-- ========== 最近收藏 ========== -->
    <section id="recent" class="recent">
      <div class="section-head reveal">
        <h2>最近收藏</h2>
        <p>挑一篇知乎好帖，把它适配到<strong class="lk-grad">你的</strong>真实场景。</p>
      </div>

      <div v-if="loading" class="recent__state">正在加载…</div>
      <div v-else-if="sources.length === 0" class="recent__state">
        收藏台还是空的，去 <router-link to="/bench">收藏台</router-link> 添加第一篇吧。
      </div>
      <div v-else class="recent__grid">
        <article
          v-for="(p, i) in sources.slice(0, 3)"
          :key="p.id"
          class="post lk-card reveal"
          :style="{ '--i': i }"
        >
          <header class="post__top">
            <span class="lk-badge">权威等级 {{ p.authority_level || '—' }}</span>
            <span class="lk-chip lk-chip--muted">{{ typeLabel(p.content_type) }}</span>
            <span v-if="p.category && p.category !== '未分类'" class="lk-chip">{{ p.category }}</span>
          </header>
          <h3 class="post__title">{{ p.title }}</h3>
          <p class="post__summary">{{ p.summary }}</p>
          <div class="post__scenes">
            <span v-for="t in sceneTags(p.id)" :key="t" class="lk-chip">{{ t }}</span>
          </div>
          <footer class="post__foot">
            <span class="post__count">{{ sceneCountText(p.id) }}</span>
            <router-link :to="`/adapt/${p.id}`" class="post__go">
              适配到我的场景 <span class="arrow">→</span>
            </router-link>
          </footer>
        </article>
      </div>

      <div class="recent__more reveal">
        <router-link to="/bench" class="lk-btn lk-btn--ghost">进入收藏台管理全部 →</router-link>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getSources, getAdaptations } from '../api'

const sources = ref([])
const adaptations = ref([])
const loading = ref(true)

const firstId = computed(() => (sources.value.length ? sources.value[0].id : null))
const stats = computed(() => {
  const families = new Set()
  adaptations.value.forEach((a) => {
    if (a.family) families.add(a.family)
  })
  return {
    sources: sources.value.length,
    scenes: adaptations.value.length,
    families: families.size || 3
  }
})

const netByPost = computed(() => {
  const m = {}
  adaptations.value.forEach((a) => {
    const pid = a.post_id
    if (!m[pid]) m[pid] = []
    m[pid].push({ id: a.id, scene_tag: a.scene_tag })
  })
  return m
})

// 动态浮动标签：从真实场景 scene_tag 取，实时更新
const DEFAULT_CHIPS = ['产线调试', '毕业设计', '开源硬件', '教学实验', '电控电源', '桌面机械臂', '智能车竞赛', '嵌入式', '硬件设计']
const floatChips = computed(() => {
  const real = adaptations.value
    .map((a) => a.scene_tag)
    .filter(Boolean)
  const set = new Set(real.length >= 4 ? real : [...real, ...DEFAULT_CHIPS])
  return Array.from(set).slice(0, 10)
})
const chipPositions = computed(() => {
  const pos = [
    { top: '6%', left: '-12%', animationDelay: '0s' },
    { top: '12%', right: '-10%', animationDelay: '0.7s' },
    { top: '34%', left: '-14%', animationDelay: '1.1s' },
    { top: '28%', right: '-12%', animationDelay: '1.6s' },
    { bottom: '24%', left: '-10%', animationDelay: '0.5s' },
    { bottom: '18%', right: '-10%', animationDelay: '1.9s' },
    { top: '50%', left: '-6%', animationDelay: '2.3s' },
    { top: '48%', right: '-8%', animationDelay: '0.3s' },
    { bottom: '40%', left: '-12%', animationDelay: '2.7s' },
    { bottom: '8%', right: '-6%', animationDelay: '1.3s' }
  ]
  return floatChips.value.map((_, i) => pos[i % pos.length])
})

const typeLabel = (t) => (t === 'article' ? '文章' : t === 'answer' ? '回答' : '帖子')

const sceneTags = (id) => {
  const list = netByPost.value[id] || []
  return list.slice(0, 4).map((x) => x.scene_tag)
}

const sceneCountText = (id) => {
  const n = (netByPost.value[id] || []).length
  return n > 0 ? `已沉淀 ${n} 个真实场景` : '等你来沉淀第一个'
}

onMounted(async () => {
  try {
    const [s, a] = await Promise.all([getSources(), getAdaptations().catch(() => [])])
    sources.value = Array.isArray(s) ? s : []
    adaptations.value = Array.isArray(a) ? a : []
  } catch (e) {
    // ignore
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.start {
  max-width: 900px;
  margin: 0 auto;
  padding: 16px 16px 64px;
}

/* ===== HERO ===== */
.hero {
  display: flex;
  flex-wrap: wrap;
  gap: 28px;
  align-items: center;
  justify-content: space-between;
  padding: 18px 4px 42px;
}
.hero__left {
  flex: 1 1 420px;
  min-width: 0;
}
.hero__right {
  flex: 0 0 auto;
  margin: 0 auto;
}
.eyebrow {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--zh-blue);
  padding: 5px 12px;
  border-radius: 999px;
  border: 1px solid var(--zh-blue-line);
  background: var(--zh-blue-soft);
}
.eyebrow .dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--zh-blue);
}
.hero__title {
  margin-top: 16px;
  font-size: clamp(32px, 4.6vw, 48px);
  line-height: 1.1;
  font-weight: 800;
  letter-spacing: -0.5px;
  color: var(--text);
}
.hero__sub {
  margin-top: 14px;
  font-size: 15px;
  line-height: 1.7;
  color: var(--text-2);
  max-width: 460px;
}
.hero__sub b {
  color: var(--zh-blue);
  padding: 0 2px;
  font-weight: 700;
}
.hero__sub strong {
  color: var(--text);
}
.hero__cta {
  margin-top: 24px;
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}
.hero__cta .arrow {
  transition: transform 0.25s ease;
}
.lk-btn--primary:hover .arrow {
  transform: translateX(3px);
}
.hero__stats {
  margin-top: 28px;
  display: flex;
  align-items: center;
  gap: 22px;
}
.stat {
  display: flex;
  flex-direction: column;
}
.stat__num {
  font-size: 26px;
  font-weight: 800;
  color: var(--text);
}
.stat__label {
  font-size: 12.5px;
  color: var(--text-3);
  margin-top: 2px;
}
.stat__sep {
  width: 1px;
  height: 34px;
  background: var(--border-strong);
}

/* HERO 右侧 */
.hero__right {
  position: relative;
  display: flex;
  justify-content: center;
  min-width: 0;
}
.orb {
  position: absolute;
  inset: 10% 8%;
  background: radial-gradient(circle at 50% 45%, rgba(125, 137, 255, 0.14), transparent 65%);
  filter: blur(10px);
  animation: lk-pulse 5s ease-in-out infinite;
}
.hero__card {
  position: relative;
  width: 220px;
  height: 220px;
  border-radius: 16px;
  background: var(--bg-2);
  border: 1px solid var(--border);
  box-shadow: var(--shadow-md);
  display: flex;
  align-items: center;
  justify-content: center;
}
.hero__mascot {
  width: 150px;
  height: 150px;
  object-fit: contain;
  filter: drop-shadow(0 6px 14px rgba(0, 0, 0, 0.1));
}
.hero__speech {
  position: absolute;
  left: -14px;
  bottom: -16px;
  max-width: 160px;
  padding: 9px 11px;
  font-size: 12px;
  line-height: 1.5;
  color: var(--text);
  background: var(--bg-2);
  border: 1px solid var(--border);
  border-radius: 12px;
  box-shadow: var(--shadow-md);
}
.float-chip {
  position: absolute;
  padding: 5px 11px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 600;
  color: var(--zh-blue);
  background: var(--bg-2);
  border: 1px solid var(--zh-blue-line);
  box-shadow: 0 3px 10px -4px rgba(125, 137, 255, 0.25);
  animation: lk-drift 5s ease-in-out infinite;
  white-space: nowrap;
}

/* ===== 三步闭环 ===== */
.section-head {
  margin: 8px 0 20px;
}
.section-head h2 {
  font-size: clamp(22px, 2.8vw, 30px);
  font-weight: 800;
  letter-spacing: -0.3px;
  color: var(--text);
}
.section-head p {
  margin-top: 8px;
  color: var(--text-2);
  font-size: 14px;
  max-width: 520px;
}
.loop {
  padding: 32px 0 10px;
  border-top: 1px solid var(--border);
}
.loop__grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 14px;
}
.loop__step {
  padding: 22px 18px 24px;
  position: relative;
  overflow: hidden;
}
.loop__step:hover {
  transform: translateY(-4px);
  border-color: var(--zh-blue-line-strong);
  box-shadow: var(--shadow-md);
}
.loop__no {
  position: absolute;
  top: 14px;
  right: 18px;
  font-size: 26px;
  font-weight: 800;
  color: rgba(125, 137, 255, 0.1);
}
.loop__step h3 {
  font-size: 16px;
  font-weight: 700;
  margin-bottom: 6px;
  color: var(--text);
}
.loop__step p {
  font-size: 13px;
  line-height: 1.7;
  color: var(--text-2);
}

/* ===== 最近收藏 ===== */
.recent {
  padding: 36px 0 10px;
  border-top: 1px solid var(--border);
}
.recent__state {
  text-align: center;
  padding: 40px 0;
  color: var(--text-2);
}
.recent__grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 14px;
}
.recent__more {
  margin-top: 26px;
  text-align: center;
}
.post {
  position: relative;
  overflow: hidden;
  padding: 18px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.post:hover {
  transform: translateY(-4px);
  border-color: var(--zh-blue-line-strong);
  box-shadow: var(--shadow-md);
}
.post__top {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.post__title {
  font-size: 17px;
  font-weight: 700;
  line-height: 1.4;
  color: var(--text);
}
.post__summary {
  font-size: 13.5px;
  line-height: 1.7;
  color: var(--text-2);
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 3;
  overflow: hidden;
}
.post__scenes {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: auto;
}
.post__foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding-top: 6px;
  border-top: 1px solid var(--border);
}
.post__count {
  font-size: 12.5px;
  color: var(--text-3);
}
.post__go {
  font-size: 13.5px;
  font-weight: 600;
  color: var(--zh-blue);
  display: inline-flex;
  align-items: center;
  gap: 5px;
  white-space: nowrap;
}
.post__go .arrow {
  transition: transform 0.25s ease;
}
.post__go:hover .arrow {
  transform: translateX(4px);
}

@keyframes lk-pulse {
  0%, 100% { opacity: 0.55; transform: scale(1); }
  50% { opacity: 0.85; transform: scale(1.06); }
}
@keyframes lk-drift {
  0%, 100% { transform: translate(0, 0); }
  50% { transform: translate(6px, -10px); }
}

@media (max-width: 640px) {
  .start {
    padding: 8px 14px 48px;
  }
  .hero {
    flex-direction: column;
    align-items: stretch;
    gap: 20px;
    padding: 8px 0 30px;
  }
  .hero__right {
    display: none;
  }
  .hero__title {
    font-size: 27px;
    letter-spacing: -0.3px;
  }
  .hero__sub {
    font-size: 14px;
    line-height: 1.65;
  }
  .hero__cta {
    margin-top: 20px;
    gap: 10px;
  }
  .hero__cta .lk-btn {
    flex: 1 1 auto;
    justify-content: center;
  }
  .hero__stats {
    margin-top: 22px;
    gap: 12px;
    flex-wrap: wrap;
  }
  .stat__num {
    font-size: 21px;
  }
  .stat__label {
    font-size: 11.5px;
  }
  .stat__sep {
    height: 28px;
  }
  .section-head h2 {
    font-size: 21px;
  }
  .loop,
  .recent {
    padding-top: 26px;
  }
  .loop__grid,
  .recent__grid {
    grid-template-columns: 1fr;
  }
  .post__foot {
    flex-wrap: wrap;
    row-gap: 8px;
  }
}

@media (max-width: 380px) {
  .hero__title {
    font-size: 24px;
  }
  .hero__stats {
    gap: 10px;
  }
  .stat__sep {
    display: none;
  }
}

@media (min-width: 641px) and (max-width: 860px) {
  .hero__card {
    width: 190px;
    height: 190px;
  }
  .hero__mascot {
    width: 120px;
    height: 120px;
  }
  .hero__speech {
    left: -8px;
    bottom: -12px;
    max-width: 140px;
    font-size: 10px;
  }
}
</style>
