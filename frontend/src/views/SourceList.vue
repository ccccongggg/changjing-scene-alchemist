<template>
  <div class="library-page">
    <header class="page-head reveal">
      <div>
        <h1>收藏台</h1>
        <p>你收藏的知乎经验帖。分类、搜索、然后挑一篇适配到你的真实场景。</p>
      </div>
      <div class="page-head__actions">
        <button class="lk-btn lk-btn--primary" @click="showAdd = true">+ 添加知乎好帖</button>
      </div>
    </header>

    <div v-if="loading" class="state">正在加载…</div>
    <div v-else-if="error" class="state state--err">
      <p>{{ error }}</p>
      <button class="lk-btn lk-btn--ghost" @click="reload">重试</button>
    </div>

    <template v-else>
      <!-- 工具栏：分类 + 搜索 -->
      <section class="toolbar lk-card reveal">
        <div class="cats">
          <button
            v-for="c in categoryList"
            :key="c"
            class="cat"
            :class="{ 'cat--active': currentCat === c }"
            @click="currentCat = c"
          >
            {{ c }}
            <span class="cat__count">{{ countByCat[c] || 0 }}</span>
          </button>
          <button class="cat cat--add" @click="showNewCat = true">+ 新建分类</button>
        </div>

        <div class="search">
          <i class="search__ico">⌕</i>
          <input
            v-model="query"
            class="search__input"
            type="text"
            placeholder="搜索标题 / 摘要 / 标签"
          />
          <button v-if="query" class="search__clear" @click="query = ''">×</button>
        </div>
      </section>

      <!-- 结果数 -->
      <div class="result-hint reveal">
        共 {{ filteredSources.length }} 条收藏
        <span v-if="query"> · 搜索 “{{ query }}”</span>
        <span v-if="currentCat !== '全部'"> · {{ currentCat }}</span>
      </div>

      <!-- 空状态 -->
      <div v-if="filteredSources.length === 0" class="state">
        <p>{{ sources.length === 0 ? '收藏台还是空的。' : '没有匹配的收藏。' }}</p>
        <button v-if="sources.length === 0" class="lk-btn lk-btn--primary" @click="doSeed">放入示例好帖</button>
      </div>

      <!-- 收藏网格 -->
      <div v-else class="grid">
        <article
          v-for="(p, i) in filteredSources"
          :key="p.id"
          class="card lk-card reveal"
          :style="{ '--i': i % 6 }"
        >
          <header class="card__top">
            <span class="lk-badge">权威等级 {{ p.authority_level || '—' }}</span>
            <span class="lk-chip lk-chip--muted">{{ typeLabel(p.content_type) }}</span>
            <div class="card__cat">
              <select
                class="card__cat-select"
                :value="p.category || '未分类'"
                @change="changeCategory(p.id, $event.target.value)"
              >
                <option v-for="c in categoryOptions" :key="c" :value="c">{{ c }}</option>
              </select>
            </div>
          </header>

          <h3 class="card__title">{{ p.title }}</h3>
          <p class="card__summary">{{ p.summary }}</p>

          <div class="card__net">
            <ScenarioGraph compact :post-title="p.title" :scenarios="netByPost[p.id] || []" />
            <span class="card__net-cap">已沉淀 {{ (netByPost[p.id] || []).length }} 个真实场景</span>
          </div>

          <div class="card__scenes">
            <span v-for="t in sceneTags(p.id)" :key="t" class="lk-chip">{{ t }}</span>
          </div>

          <footer class="card__foot">
            <span class="card__count">{{ sceneCountText(p.id) }}</span>
            <router-link :to="`/adapt/${p.id}`" class="card__go">
              适配到我的场景 <span class="arrow">→</span>
            </router-link>
          </footer>
        </article>
      </div>
    </template>

    <!-- 新建分类弹窗 -->
    <div v-if="showNewCat" class="modal" @click.self="showNewCat = false">
      <div class="modal__box lk-card">
        <h3>新建分类</h3>
        <input v-model="newCatName" class="modal__input" placeholder="例如：竞赛备赛 / 毕业设计" />
        <div class="modal__ops">
          <button class="lk-btn lk-btn--ghost" @click="showNewCat = false">取消</button>
          <button class="lk-btn lk-btn--primary" @click="createCategory">确定</button>
        </div>
      </div>
    </div>

    <!-- 添加帖子弹窗（占位） -->
    <div v-if="showAdd" class="modal" @click.self="showAdd = false">
      <div class="modal__box lk-card">
        <h3>添加知乎好帖</h3>
        <p class="modal__tip">粘贴知乎问题/文章/回答链接，AI 会自动解析。</p>
        <input v-model="newUrl" class="modal__input" placeholder="https://www.zhihu.com/question/..." />
        <div class="modal__ops">
          <button class="lk-btn lk-btn--ghost" @click="showAdd = false">取消</button>
          <button class="lk-btn lk-btn--primary" @click="addUrl">添加</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getSources, getAdaptations, seedSources, updateSourceCategory } from '../api'
import ScenarioGraph from '../components/ScenarioGraph.vue'

const sources = ref([])
const adaptations = ref([])
const loading = ref(true)
const error = ref('')
const query = ref('')
const currentCat = ref('全部')
const showNewCat = ref(false)
const showAdd = ref(false)
const newCatName = ref('')
const newUrl = ref('')
const customCats = ref([])

const categoryList = computed(() => {
  const builtIn = ['全部', '未分类']
  const used = new Set(sources.value.map((s) => s.category).filter(Boolean))
  customCats.value.forEach((c) => used.add(c))
  return [...builtIn, ...Array.from(used).filter((c) => !builtIn.includes(c))]
})

const categoryOptions = computed(() => categoryList.value.filter((c) => c !== '全部'))

const countByCat = computed(() => {
  const m = { 全部: sources.value.length, 未分类: 0 }
  sources.value.forEach((s) => {
    const c = s.category || '未分类'
    m[c] = (m[c] || 0) + 1
  })
  return m
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

const filteredSources = computed(() => {
  let list = sources.value
  if (currentCat.value !== '全部') {
    list = list.filter((s) => (s.category || '未分类') === currentCat.value)
  }
  const q = query.value.trim().toLowerCase()
  if (q) {
    list = list.filter((s) => {
      const text = `${s.title} ${s.summary || ''} ${s.author || ''} ${(netByPost.value[s.id] || [])
        .map((x) => x.scene_tag)
        .join(' ')}`.toLowerCase()
      return text.includes(q)
    })
  }
  return list
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

const doSeed = async () => {
  loading.value = true
  try {
    await seedSources()
    await load()
  } finally {
    loading.value = false
  }
}

const createCategory = () => {
  const name = newCatName.value.trim()
  if (!name) return
  if (!customCats.value.includes(name)) customCats.value.push(name)
  newCatName.value = ''
  showNewCat.value = false
}

const addUrl = () => {
  // 占位：后续可接真实解析接口
  alert('已记录：' + newUrl.value)
  newUrl.value = ''
  showAdd.value = false
}

const changeCategory = async (id, category) => {
  const s = sources.value.find((x) => x.id === id)
  if (!s) return
  s.category = category
  try {
    await updateSourceCategory(id, category)
  } catch (e) {
    // 可回滚，暂不处理
  }
}

onMounted(load)
</script>

<style scoped>
.library-page {
  padding: 12px 0 64px;
}
.page-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 24px;
  margin-bottom: 24px;
}
.page-head h1 {
  font-size: 32px;
  font-weight: 800;
  letter-spacing: -0.5px;
  color: var(--text);
}
.page-head p {
  margin-top: 6px;
  color: var(--text-2);
  font-size: 15px;
}

.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  padding: 14px 18px;
  margin-bottom: 18px;
  flex-wrap: wrap;
}
.cats {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.cat {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 7px 13px;
  border-radius: 4px;
  border: 1px solid var(--border);
  background: var(--bg-2);
  color: var(--text-2);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
  font-family: inherit;
}
.cat:hover {
  border-color: var(--zh-blue-line-strong);
  color: var(--zh-blue);
}
.cat--active {
  background: var(--zh-blue);
  border-color: var(--zh-blue);
  color: #fff;
}
.cat__count {
  font-size: 11px;
  padding: 1px 5px;
  border-radius: 999px;
  background: rgba(0, 0, 0, 0.06);
}
.cat--active .cat__count {
  background: rgba(255, 255, 255, 0.25);
}
.cat--add {
  border-style: dashed;
  color: var(--zh-blue);
}

.search {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  width: 260px;
  height: 36px;
  padding: 0 12px;
  border-radius: 4px;
  background: var(--surface-2);
  border: 1px solid var(--border);
}
.search__ico {
  color: var(--text-3);
}
.search__input {
  flex: 1;
  border: none;
  outline: none;
  background: transparent;
  font-size: 13px;
  color: var(--text);
  font-family: inherit;
}
.search__clear {
  border: none;
  background: none;
  color: var(--text-3);
  cursor: pointer;
  font-size: 16px;
  line-height: 1;
}

.result-hint {
  margin-bottom: 14px;
  font-size: 13px;
  color: var(--text-3);
}

.grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 18px;
}
.card {
  position: relative;
  overflow: hidden;
  padding: 22px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.card:hover {
  transform: translateY(-4px);
  border-color: var(--zh-blue-line-strong);
  box-shadow: var(--shadow-md);
}
.card__top {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.card__cat {
  margin-left: auto;
}
.card__cat-select {
  border: 1px solid var(--border);
  border-radius: 4px;
  padding: 3px 8px;
  font-size: 12px;
  color: var(--text-2);
  background: var(--surface-2);
  cursor: pointer;
  font-family: inherit;
}
.card__title {
  font-size: 17px;
  font-weight: 700;
  line-height: 1.4;
  color: var(--text);
}
.card__summary {
  font-size: 13.5px;
  line-height: 1.7;
  color: var(--text-2);
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 3;
  overflow: hidden;
}
.card__net {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 4px 0 2px;
}
.card__net :deep(.sg--mini) {
  width: 132px;
  flex: none;
}
.card__net-cap {
  font-size: 12px;
  color: var(--text-3);
}
.card__scenes {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: auto;
}
.card__foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding-top: 6px;
  border-top: 1px solid var(--border);
}
.card__count {
  font-size: 12.5px;
  color: var(--text-3);
}
.card__go {
  font-size: 13.5px;
  font-weight: 600;
  color: var(--zh-blue);
  display: inline-flex;
  align-items: center;
  gap: 5px;
  white-space: nowrap;
}
.card__go .arrow {
  transition: transform 0.25s ease;
}
.card__go:hover .arrow {
  transform: translateX(4px);
}

.state {
  text-align: center;
  padding: 60px 0;
  color: var(--text-2);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 18px;
}
.state--err {
  color: #ff5a4d;
}

.modal {
  position: fixed;
  inset: 0;
  z-index: 100;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}
.modal__box {
  width: 100%;
  max-width: 420px;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.modal__box h3 {
  font-size: 18px;
  font-weight: 700;
  color: var(--text);
}
.modal__tip {
  font-size: 13px;
  color: var(--text-3);
  margin-top: -10px;
}
.modal__input {
  width: 100%;
  height: 40px;
  padding: 0 12px;
  border: 1px solid var(--border);
  border-radius: 4px;
  font-size: 14px;
  color: var(--text);
  background: var(--surface-2);
  font-family: inherit;
}
.modal__ops {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

@media (max-width: 860px) {
  .library-page {
    padding: 6px 0 48px;
  }
  .page-head {
    flex-direction: column;
    gap: 12px;
    margin-bottom: 18px;
  }
  .page-head h1 {
    font-size: 24px;
  }
  .page-head p {
    font-size: 14px;
    line-height: 1.6;
  }
  .page-head__actions .lk-btn {
    width: 100%;
    justify-content: center;
  }
  .toolbar {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
    padding: 12px 14px;
    min-width: 0;
  }
  /* 分类太多时横向滑动，而不是撑高整屏 */
  .cats {
    flex-wrap: nowrap;
    overflow-x: auto;
    padding-bottom: 4px;
    scrollbar-width: none;
    -webkit-overflow-scrolling: touch;
  }
  .cats::-webkit-scrollbar {
    display: none;
  }
  .cat {
    flex: none;
  }
  .search {
    width: 100%;
  }
  .search__input {
    font-size: 16px;
  }
  .grid {
    grid-template-columns: 1fr;
    gap: 14px;
  }
  .card {
    padding: 16px;
    gap: 12px;
  }
  .card__net {
    flex-wrap: wrap;
    row-gap: 6px;
  }
  .card__title {
    font-size: 16px;
  }
  .card__foot {
    flex-wrap: wrap;
    row-gap: 8px;
  }
}

@media (max-width: 380px) {
  .card__net :deep(.sg--mini) {
    width: 104px;
  }
}
</style>
