<template>
  <div class="page">
    <div class="page__inner">
      <header class="lib-head">
        <h1>方案库</h1>
        <div class="tabs">
          <button class="tab" :class="{ 'is-on': tab === 'contributed' }" @click="tab = 'contributed'">
            我贡献的
          </button>
          <button class="tab" :class="{ 'is-on': tab === 'liked' }" @click="tab = 'liked'">
            我点赞的
          </button>
        </div>
        <p class="lib-sub">
          <template v-if="tab === 'contributed'">
            AI 从你的贡献方案中提取提示词并<b>自动分类</b>，用贡献地图展示。
          </template>
          <template v-else>
            AI 只负责提取关键词，<b>分类由你自己建立和管理</b>。
          </template>
        </p>
      </header>

      <!-- ================= 我贡献的 ================= -->
      <template v-if="tab === 'contributed'">
        <!-- 奖章点亮流动墙 -->
        <section class="wall">
          <div class="wall__head">
            <h2>奖章流动墙</h2>
            <span class="wall__note">
              奖章主要按影响力发放 · 铜 / 银 / 金 三档，外环是距下一档的进度 · 点奖章翻面看获取条件
            </span>
          </div>
          <MedalWall :badges="store.badges" />
          <div class="stats">
            <div class="stat"><b>{{ store.contributionStats.contributed }}</b><span>已贡献方案</span></div>
            <div class="stat"><b>{{ store.contributionStats.verified }}</b><span>已验证方案</span></div>
            <div class="stat"><b>{{ store.contributionStats.helped }}</b><span>帮助人数</span></div>
          </div>
        </section>

        <!-- 贡献地图 -->
        <section class="map">
          <div class="map__head">
            <h2>贡献地图</h2>
            <span class="badge badge--auto">AI 自动分类</span>
            <span class="map__note">中心 = 我 · 星星 = 不同用户的真实场景 · 迷你星 = 执行步骤</span>
          </div>

          <ContributionGalaxy :groups="store.galaxy" @select="onPlanet" @clear="detail = null" />

          <!-- 详情面板（默认不再是空白） -->
          <div class="map__detail">
            <template v-if="detail">
              <div class="d__head">
                <div class="d__head-l">
                  <span class="d__status" :class="detail.status === '已验证' ? 'is-ok' : 'is-pending'">
                    {{ detail.status }}
                  </span>
                  <span class="chip chip--muted">{{ detail.aiCategory }}</span>
                  <span v-if="detail.isMine" class="chip chip--mine">我贡献的</span>
                  <span v-else class="chip chip--muted">来自 {{ detail.contributor }}</span>
                </div>
                <button class="d__close" @click="detail = null">✕</button>
              </div>
              <div class="d__grid">
                <div class="d__col">
                  <h3 class="d__t">{{ detail.title }}</h3>
                  <dl class="d__meta">
                    <div><dt>来源原帖</dt><dd>{{ detail.sourcePost }}</dd></div>
                    <div><dt>用户场景</dt><dd>{{ detail.scene }}</dd></div>
                    <div><dt>用户目标</dt><dd>{{ detail.goal }}</dd></div>
                    <div><dt>关键限制</dt><dd>{{ (detail.limits || []).join('、') || '—' }}</dd></div>
                    <div><dt>适用人群</dt><dd>{{ detail.audience }}</dd></div>
                    <div><dt>结果状态</dt><dd>{{ detail.status }}<span v-if="detail.mark === 'ai_only'"> · AI 建议尚未实践</span></dd></div>
                  </dl>
                  <div class="d__kw">
                    <span v-for="k in detail.keywords" :key="k" class="chip">{{ k }}</span>
                  </div>
                  <div class="d__infl">
                    被保存 {{ detail.saves }} · 被采纳 {{ detail.adoptions }} · 有效反馈 {{ detail.feedbacks }} · 帮助 {{ detail.helped }} 人
                  </div>
                  <div class="d__acts">
                    <button class="btn btn--primary btn--sm" @click="backToNebula(detail)">回到星图</button>
                    <button class="btn btn--flat btn--sm" @click="flag(detail)">
                      {{ detail.categoryFlagged ? '已反馈' : '分类不准确' }}
                    </button>
                  </div>
                  <p class="d__note">分类方式仍以系统自动分类为主，你的反馈仅用于改进。</p>
                </div>
                <div class="d__col d__col--steps">
                  <div class="d__steps-h">解决步骤（{{ (detail.steps || []).length }} 步）</div>
                  <ol class="d__steps">
                    <li v-for="(s, i) in detail.steps" :key="i">{{ s }}</li>
                  </ol>
                </div>
              </div>
            </template>

            <div v-else class="d__overview">
              <div class="ov__main">
                <div class="ov__ico">✦</div>
                <div>
                  <h3 class="ov__t">这是「你的」贡献星系</h3>
                  <p class="ov__p">
                    中心是你：绕着你转的小星星，是不同用户基于你收藏的原帖提出的真实场景；点进场景星，
                    只剩这一颗星和它的迷你星——也就是这个真实场景下的执行步骤。
                  </p>
                </div>
              </div>
              <div class="ov__stats">
                <div class="ov__stat"><b>{{ store.galaxy.length }}</b><span>收藏原帖</span></div>
                <div class="ov__stat"><b>{{ store.galaxy.reduce((a, g) => a + g.planets.length, 0) }}</b><span>真实场景</span></div>
                <div class="ov__stat"><b>{{ store.contributionStats.contributed }}</b><span>我贡献的</span></div>
              </div>
              <ul class="ov__tips">
                <li><b>悬停</b>场景星 → 其他分支淡化，只看它这一条</li>
                <li><b>单击</b>场景星 → 进入该场景，其他帖子与场景被移除，只剩它的执行步骤</li>
                <li><b>点空白 / 回到总览</b> → 场景与帖子平滑归位</li>
              </ul>
            </div>
          </div>
        </section>
      </template>

      <!-- ================= 我点赞的 ================= -->
      <template v-else>
        <div class="liked">
          <!-- 分类管理 -->
          <aside class="cats">
            <div class="cats__head">
              <h2>我的分类</h2>
              <span class="cats__note">分类由你决定</span>
            </div>
            <ul class="cats__list">
              <li
                v-for="g in store.savedGroups"
                :key="g.name"
                class="cat"
                :class="{ 'is-on': activeCat === g.name, 'is-fixed': g.name === '全部' }"
                @click="activeCat = g.name"
              >
                <span class="cat__n">{{ g.name }}</span>
                <span class="cat__c">{{ g.items.length }}</span>
              </li>
            </ul>
            <div class="cats__add">
              <input v-model="newCat" class="cats__inp" placeholder="新建分类…" @keyup.enter="addCat" />
              <button class="btn btn--ghost btn--sm" @click="addCat">新建</button>
            </div>
            <div v-if="activeCat !== '全部' && activeCat !== '未分类'" class="cats__ops">
              <button class="btn btn--flat btn--sm" @click="renameCurrent">重命名</button>
              <select class="cats__sel" @change="onMerge($event.target.value)">
                <option value="">合并到…</option>
                <option v-for="g in mergeTargets" :key="g" :value="g">{{ g }}</option>
              </select>
              <button class="btn btn--flat btn--sm" @click="removeCurrent">删除</button>
            </div>
          </aside>

          <!-- 方案列表 -->
          <section class="saved">
            <div class="saved__head">
              <h2>{{ activeCat === '全部' ? '全部收藏' : activeCat }}</h2>
              <span class="saved__c">{{ currentItems.length }} 个方案</span>
            </div>

            <div v-if="currentItems.length" class="saved__list">
              <article v-for="s in currentItems" :key="s.id" class="scard">
                <div class="scard__top">
                  <h3 class="scard__t">{{ s.title }}</h3>
                  <button class="scard__x" title="取消收藏" @click="store.toggleLike(s.id)">✕</button>
                </div>
                <div class="scard__meta">
                  <span>来源帖子：{{ s.sourcePost }}</span>
                  <span>适用场景：{{ s.scene }}</span>
                  <span>保存时间：{{ s.savedAt }}</span>
                </div>
                <div class="scard__kw">
                  <span v-for="k in s.keywords" :key="k" class="chip chip--muted">{{ k }}</span>
                </div>
                <div class="scard__foot">
                  <div class="scard__cat">
                    <span class="scard__cat-k">分类</span>
                    <select class="cats__sel" :value="s.category || '未分类'" @change="move(s, $event.target.value)">
                      <option value="未分类">未分类</option>
                      <option v-for="c in store.userCategories" :key="c" :value="c">{{ c }}</option>
                    </select>
                    <span v-if="s.suggested && s.suggested !== (s.category || '未分类')" class="sug">
                      AI 建议「{{ s.suggested }}」仅供参考
                    </span>
                  </div>
                  <button class="btn btn--ghost btn--sm" @click="backToNebula(s)">回到星图</button>
                </div>
              </article>
            </div>
            <div v-else class="empty">
              <div class="empty__ico">✧</div>
              <p>这个分类下还没有方案。去星云图完成一条路径，然后「保存到我的点赞的」。</p>
            </div>
          </section>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useScenarioStore } from '../store/useScenarioStore'
import ContributionGalaxy from '../components/ContributionGalaxy.vue'
import MedalWall from '../components/MedalWall.vue'

const store = useScenarioStore()
const router = useRouter()

const tab = ref('contributed')
const detail = ref(null)
const activeCat = ref('全部')
const newCat = ref('')

/* ---------- 贡献地图交互 ---------- */
function onPlanet(p) {
  detail.value = p
}
function flag(d) {
  store.flagCategoryInaccurate(d.id)
}
function backToNebula(d) {
  router.push({ path: '/starmap', query: { post: d.postId || 'ppt-ai-001', node: 't1-1' } })
}

/* ---------- 我点赞的 交互 ---------- */
const currentItems = computed(() => {
  const g = store.savedGroups.find((x) => x.name === activeCat.value)
  return g ? g.items : store.saved
})
const mergeTargets = computed(() =>
  store.savedGroups.map((g) => g.name).filter((n) => n !== activeCat.value && n !== '全部' && n !== '未分类')
)

function addCat() {
  if (store.addCategory(newCat.value)) newCat.value = ''
}
function renameCurrent() {
  const n = window.prompt('重命名分类', activeCat.value)
  if (n && store.renameCategory(activeCat.value, n)) activeCat.value = n.trim()
}
function removeCurrent() {
  if (window.confirm(`删除分类「${activeCat.value}」？其中的方案会移入「未分类」。`)) {
    store.deleteCategory(activeCat.value)
    activeCat.value = '未分类'
  }
}
function onMerge(to) {
  if (to) {
    store.mergeCategory(activeCat.value, to)
    activeCat.value = to
  }
}
function move(s, cat) {
  store.moveToCategory(s.id, cat)
}
</script>

<style scoped>
.page {
  min-height: 100%;
  padding: 24px 24px 64px;
  background: var(--bg);
}
.page__inner {
  max-width: var(--maxw);
  margin: 0 auto;
}
.lib-head {
  margin-bottom: 18px;
}
.lib-head h1 {
  font-size: 24px;
  font-weight: 800;
}
.tabs {
  display: inline-flex;
  gap: 6px;
  margin-top: 14px;
  padding: 4px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
}
.tab {
  border: none;
  background: transparent;
  padding: 8px 22px;
  border-radius: 7px;
  font-size: 14.5px;
  font-weight: 600;
  color: var(--text-2);
  cursor: pointer;
}
.tab.is-on {
  background: var(--zh-blue);
  color: #fff;
}
.lib-sub {
  margin-top: 12px;
  font-size: 13px;
  color: var(--text-3);
}
.lib-sub b {
  color: var(--zh-blue);
}

/* ---------- 奖章墙 ---------- */
.wall {
  padding: 18px 20px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 14px;
  box-shadow: var(--shadow);
}
.wall__head {
  display: flex;
  align-items: baseline;
  gap: 12px;
  flex-wrap: wrap;
}
.wall__head h2 {
  font-size: 16px;
  font-weight: 800;
}
.wall__note {
  font-size: 11.5px;
  color: var(--text-3);
}
.stats {
  display: flex;
  gap: 12px;
  margin-top: 16px;
  flex-wrap: wrap;
}
.stat {
  flex: 1;
  min-width: 120px;
  padding: 12px 16px;
  border-radius: 11px;
  background: var(--zh-blue-soft);
  border: 1px solid var(--zh-blue-line);
}
.stat b {
  display: block;
  font-size: 22px;
  color: var(--zh-blue);
}
.stat span {
  font-size: 12px;
  color: var(--text-2);
}

/* ---------- 贡献地图 ---------- */
.map {
  margin-top: 18px;
  padding: 18px 20px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 14px;
  box-shadow: var(--shadow);
}
.map__head {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}
.map__head h2 {
  font-size: 16px;
  font-weight: 800;
}
.map__note {
  margin-left: auto;
  font-size: 11.5px;
  color: var(--text-3);
}
.badge--auto {
  background: rgba(129, 86, 224, 0.12);
  border-color: rgba(129, 86, 224, 0.35);
  color: #6d3fd1;
}

/* 详情面板：默认给「总览说明」，点行星后换成该场景详情 */
.map__detail {
  margin-top: 14px;
  padding: 15px 16px;
  border: 1px solid var(--border);
  border-radius: 12px;
  background: var(--surface-2);
  min-height: 172px;
}

/* 总览态 */
.d__overview {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.ov__main {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}
.ov__ico {
  flex: none;
  width: 38px;
  height: 38px;
  border-radius: 11px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  background: var(--zh-blue-soft);
  color: var(--zh-blue);
}
.ov__t {
  font-size: 14px;
  font-weight: 800;
}
.ov__p {
  margin-top: 5px;
  font-size: 12.6px;
  line-height: 1.85;
  color: var(--text-3);
}
.ov__stats {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}
.ov__stat {
  flex: 1;
  min-width: 96px;
  padding: 10px 12px;
  border-radius: 10px;
  background: #fff;
  border: 1px solid var(--border);
}
.ov__stat b {
  display: block;
  font-size: 19px;
  font-weight: 800;
  color: var(--zh-blue);
  font-variant-numeric: tabular-nums;
}
.ov__stat span {
  font-size: 11.5px;
  color: var(--text-3);
}
.ov__tips {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 5px;
}
.ov__tips li {
  position: relative;
  padding-left: 14px;
  font-size: 12px;
  line-height: 1.7;
  color: var(--text-3);
}
.ov__tips li::before {
  content: '';
  position: absolute;
  left: 2px;
  top: 9px;
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: var(--zh-blue);
  opacity: 0.55;
}
.ov__tips b {
  color: var(--text-2);
}

/* 详情态 */
.d__head {
  display: flex;
  align-items: center;
  gap: 10px;
}
.d__head-l {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  min-width: 0;
}
.d__close {
  margin-left: auto;
  flex: none;
  width: 26px;
  height: 26px;
  border: none;
  border-radius: 7px;
  background: var(--surface-3);
  color: var(--text-3);
  font-size: 12px;
  cursor: pointer;
  transition: background 0.15s ease, color 0.15s ease;
}
.d__close:hover {
  background: var(--border-strong);
  color: var(--text);
}
.d__grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: 18px;
  margin-top: 12px;
}
.d__col {
  min-width: 0;
}
.d__col--steps {
  border-left: 1px solid var(--border);
  padding-left: 18px;
}
.d__steps-h {
  font-size: 12.5px;
  font-weight: 700;
  color: var(--text);
}
.d__status {
  font-size: 11px;
  font-weight: 700;
  padding: 2px 9px;
  border-radius: 5px;
}
.d__status.is-ok {
  background: rgba(34, 197, 94, 0.14);
  color: #17864a;
}
.d__status.is-pending {
  background: rgba(245, 158, 11, 0.16);
  color: #a8710a;
}
.d__t {
  margin-top: 9px;
  font-size: 15px;
  font-weight: 700;
  line-height: 1.5;
}
.d__meta {
  margin: 12px 0 10px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.d__meta > div {
  display: grid;
  grid-template-columns: 62px 1fr;
  gap: 8px;
}
.d__meta dt {
  font-size: 11.5px;
  color: var(--text-3);
}
.d__meta dd {
  margin: 0;
  font-size: 12.6px;
  color: var(--text-2);
  line-height: 1.65;
}
.d__kw {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
  margin-bottom: 10px;
}
.d__steps {
  list-style: none;
  counter-reset: st;
  margin: 10px 0 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 9px;
}
.d__steps li {
  position: relative;
  padding-left: 30px;
  font-size: 13px;
  line-height: 1.7;
  color: var(--text-2);
}
.d__steps li::before {
  counter-increment: st;
  content: counter(st);
  position: absolute;
  left: 0;
  top: 1px;
  width: 21px;
  height: 21px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--zh-blue);
  color: #fff;
  font-size: 11px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}
.d__infl {
  font-size: 11.5px;
  color: var(--text-3);
  padding: 8px 10px;
  background: #fff;
  border: 1px solid var(--border);
  border-radius: 8px;
}
.d__acts {
  display: flex;
  gap: 8px;
  margin-top: 11px;
}
.d__note {
  margin-top: 8px;
  font-size: 11px;
  color: var(--text-3);
  line-height: 1.6;
}

/* ---------- 我点赞的 ---------- */
.liked {
  display: grid;
  grid-template-columns: 232px minmax(0, 1fr);
  gap: 18px;
  align-items: start;
}
.cats {
  padding: 16px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 14px;
  box-shadow: var(--shadow);
  position: sticky;
  top: 72px;
}
.cats__head h2 {
  font-size: 15px;
  font-weight: 800;
}
.cats__note {
  font-size: 11px;
  color: var(--text-3);
}
.cats__list {
  list-style: none;
  margin: 12px 0 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 3px;
}
.cat {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 9px 12px;
  border-radius: 8px;
  font-size: 13.5px;
  color: var(--text-2);
  cursor: pointer;
  transition: background 0.15s ease, color 0.15s ease;
}
.cat:hover {
  background: var(--surface-2);
}
.cat.is-on {
  background: var(--zh-blue-soft);
  color: var(--zh-blue);
  font-weight: 700;
}
.cat__c {
  font-size: 11.5px;
  color: var(--text-3);
}
.cat.is-on .cat__c {
  color: var(--zh-blue);
}
.cats__add {
  display: flex;
  gap: 6px;
  margin-top: 12px;
}
.cats__inp {
  flex: 1;
  min-width: 0;
  padding: 8px 10px;
  border: 1px solid var(--border-strong);
  border-radius: 8px;
  font-size: 13px;
  font-family: inherit;
  outline: none;
}
.cats__inp:focus {
  border-color: var(--zh-blue);
}
.cats__ops {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px dashed var(--border);
}
.cats__sel {
  padding: 7px 9px;
  border: 1px solid var(--border-strong);
  border-radius: 8px;
  font-size: 12.5px;
  font-family: inherit;
  color: var(--text-2);
  background: #fff;
}
.saved__head {
  display: flex;
  align-items: baseline;
  gap: 10px;
  margin-bottom: 12px;
}
.saved__head h2 {
  font-size: 17px;
  font-weight: 800;
}
.saved__c {
  font-size: 12px;
  color: var(--text-3);
}
.saved__list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.scard {
  padding: 15px 16px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  box-shadow: var(--shadow);
}
.scard__top {
  display: flex;
  gap: 10px;
  align-items: flex-start;
}
.scard__t {
  font-size: 15px;
  font-weight: 700;
  line-height: 1.5;
  flex: 1;
}
.scard__x {
  border: none;
  background: var(--surface-2);
  color: var(--text-3);
  width: 24px;
  height: 24px;
  border-radius: 6px;
  cursor: pointer;
  flex: none;
}
.scard__x:hover {
  background: var(--surface-3);
  color: var(--text);
}
.scard__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 18px;
  margin-top: 9px;
  font-size: 12px;
  color: var(--text-3);
}
.scard__kw {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
  margin-top: 10px;
}
.scard__foot {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--border);
  flex-wrap: wrap;
}
.scard__cat {
  display: flex;
  align-items: center;
  gap: 7px;
  flex-wrap: wrap;
}
.scard__cat-k {
  font-size: 11.5px;
  color: var(--text-3);
}
.sug {
  font-size: 11px;
  color: #6d3fd1;
}
.scard__foot .btn {
  margin-left: auto;
}
.empty {
  padding: 60px 20px;
  text-align: center;
  background: var(--surface);
  border: 1px dashed var(--border-strong);
  border-radius: 14px;
}
.empty__ico {
  font-size: 28px;
  color: var(--zh-blue);
  margin-bottom: 8px;
}
.empty p {
  font-size: 13px;
  color: var(--text-3);
  line-height: 1.7;
}
@media (max-width: 900px) {
  .page {
    padding: 16px 14px 56px;
  }
  .map__body {
    grid-template-columns: 1fr;
  }
  .map__side {
    max-height: none;
  }
  .liked {
    grid-template-columns: 1fr;
  }
  .cats {
    position: static;
  }
}

/* ===== 小屏（手机）：详情抽屉两栏改单栏，步骤列去掉左边线 ===== */
@media (max-width: 480px) {
  .page {
    padding: 12px 10px 48px;
  }
  .d__grid {
    grid-template-columns: 1fr;
    gap: 14px;
  }
  .d__col--steps {
    border-left: none;
    padding-left: 0;
    border-top: 1px solid var(--border);
    padding-top: 14px;
  }
  .d__meta > div {
    grid-template-columns: 54px 1fr;
  }
}
</style>
