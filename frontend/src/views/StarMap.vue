<template>
  <div class="starmap">
    <!-- ===== 顶部：原帖切换 + 操作 ===== -->
    <div class="sm-head card">
      <div class="sm-chips">
        <button
          v-for="(p, i) in posts"
          :key="p.id"
          class="chip"
          :class="{ on: i === curIdx }"
          @click="switchPost(i)"
        >
          帖{{ i + 1 }} · {{ shortTitle(p.title) }}
        </button>
      </div>
      <div class="sm-actions">
        <button class="btn ghost" @click="drawerOpen = !drawerOpen">
          已收录处境 <b>{{ nodes.length }}</b>
        </button>
        <button class="btn primary" @click="startCreate">
          ＋ 炼一个我的处境
        </button>
      </div>
    </div>

    <div class="sm-body">
      <!-- ===== 星图舞台 ===== -->
      <section class="stage">
        <svg
          ref="svgEl"
          class="web"
          :class="[lodClass, { locked: !!activeId, entered }]"
          viewBox="0 0 900 790"
          preserveAspectRatio="xMidYMid meet"
          @wheel.prevent="onWheel"
          @pointerdown="onDown"
          @pointermove="onMove"
          @pointerup="onUp"
          @pointercancel="onUp"
          @pointerleave="onLeave"
        >
          <defs>
            <radialGradient id="sunGrad">
              <stop offset="0%" stop-color="#d7e9fd" />
              <stop offset="60%" stop-color="#eef5fd" />
              <stop offset="100%" stop-color="#fbfcfd" />
            </radialGradient>
            <radialGradient id="coreGrad">
              <stop offset="0%" stop-color="#ffffff" />
              <stop offset="100%" stop-color="#f2f7fd" />
            </radialGradient>
            <filter id="sunBlur"><feGaussianBlur stdDeviation="10" /></filter>
          </defs>

          <g ref="vpEl" :transform="vpTransform">
            <ellipse
              v-for="r in rings"
              :key="'o' + r"
              class="orbit"
              :cx="CX"
              :cy="CY"
              :rx="r"
              :ry="+(r * SQUASH).toFixed(1)"
            />

            <line
              v-for="n in allNodes"
              :key="'ray' + n.id"
              class="ray"
              :class="{ hot: activeId === n.id }"
              :style="{ '--i': n.idx }"
              :stroke="n.verified ? STAR_ON : STAR_OFF"
              :x1="CX"
              :y1="CY"
              :x2="n.x"
              :y2="n.y"
            />

            <line
              v-for="(l, i) in links"
              :key="'lk' + i"
              class="xlink"
              :class="{ parent: l.parent }"
              :x1="l.a.x"
              :y1="l.a.y"
              :x2="l.b.x"
              :y2="l.b.y"
            />

            <!-- 太阳：原帖 -->
            <g class="sun">
              <circle class="sun-glow" :cx="CX" :cy="CY" r="86" fill="url(#sunGrad)" filter="url(#sunBlur)" />
              <circle :cx="CX" :cy="CY" r="70" fill="none" stroke="#dbe6f4" stroke-width="1" />
              <circle class="varc" :cx="CX" :cy="CY" r="70" fill="none" :stroke="STAR_ON" stroke-width="1.6" />
              <circle class="corec" :cx="CX" :cy="CY" r="58" fill="url(#coreGrad)" stroke="#dbe6f4" stroke-width="1" />
              <g :transform="`translate(${CX} ${CY}) scale(${inv})`">
                <!-- 标题不再塞进太阳；顶部 chips 与右侧面板已展示完整标题 -->
                <text class="core-sub" x="0" y="-8" text-anchor="middle">原帖 · 基准处境</text>
                <text class="core-num" x="0" y="16" text-anchor="middle">已收录处境 ★ {{ nodes.length }}</text>
                <text class="core-hint" x="0" y="36" text-anchor="middle">点击查看原帖拆解</text>
              </g>
            </g>
            <circle
              class="corehit"
              :cx="CX"
              :cy="CY"
              r="72"
              fill="transparent"
              @click.stop="openOrigin"
            >
              <title>{{ currentPost ? currentPost.title : '原帖' }}</title>
            </circle>

            <!-- 星：一个真实处境 -->
            <g
              v-for="n in allNodes"
              :key="'n' + n.id"
              class="node"
              :class="{ on: activeId === n.id, draft: n.id === DRAFT_ID }"
              :style="{ '--i': n.idx }"
              :data-id="n.id"
              @mouseenter="hoverId = n.id"
              @mouseleave="hoverId = null"
            >
              <g :transform="wrapT(n)">
                <g class="pop" :style="{ '--s': popScale(n) }">
                  <circle class="nhit" r="18" fill="transparent" />
                  <path
                    class="star"
                    :class="{ on: n.verified, tw: !n.verified }"
                    :d="starPath(9.5, 4)"
                    :fill="n.verified ? STAR_ON : '#ffffff'"
                    :stroke="n.verified ? STAR_ON : STAR_OFF"
                    :stroke-width="n.verified ? 0 : 1.8"
                  />
                </g>
                <text class="lbl" :transform="lblT(n)" :text-anchor="n.anchor" dominant-baseline="central">
                  {{ starLabel(n) }}
                </text>
                <text class="node-detail" :transform="detT(n)" :text-anchor="n.anchor" dominant-baseline="central">
                  {{ n.verified ? '已做成' : '还在试' }} · {{ n.peers }}人相似
                </text>
              </g>
            </g>
          </g>
        </svg>

        <div class="hintbar">
          滚轮缩放 · 拖拽平移<br />
          <b>点星看这一版改了什么 · 点太阳看原帖拆解 · 右上角「炼一个我的处境」加新星</b>
        </div>

        <div class="zoomtag">{{ lodName }} · <b>{{ k.toFixed(1) }}x</b></div>
        <div class="zoombar">
          <button title="放大" @click="zoomBy(1.45)">＋</button>
          <button title="缩小" @click="zoomBy(1 / 1.45)">−</button>
          <button class="sm" title="复位" @click="fitView">复位</button>
        </div>

        <div class="toast" :class="{ on: toastOn }">{{ toastMsg }}</div>
      </section>

      <!-- ===== 右侧详情面板 ===== -->
      <aside class="panel card">
        <!-- 加载 / 空态 -->
        <div v-if="loading" class="pv-empty">正在把场景应用网铺成星图…</div>
        <div v-else-if="!currentPost" class="pv-empty">
          还没有可展示的原帖。先去<router-link to="/bench">收藏台</router-link>收一篇。
        </div>

        <!-- A1 · 原帖拆解（总览 / 太阳） -->
        <template v-else-if="view === 'overview' || view === 'origin'">
          <div class="kicker">{{ view === 'origin' ? '原帖 · 基准处境（太阳）' : 'A1 · 原帖拆解' }}</div>
          <h2 class="p-title">{{ currentPost.title }}</h2>
          <p class="p-origin">{{ currentPost.origin.scene || currentPost.summary }}</p>
          <div v-if="currentPost.origin.constraints.length" class="tags">
            <span v-for="(c, i) in currentPost.origin.constraints" :key="i" class="tag">{{ c }}</span>
          </div>

          <div class="stat-line">
            <div class="stat"><b>{{ nodes.length }}</b><span>已收录处境</span></div>
            <div class="stat"><b>{{ verifiedCount }}</b><span>已做成</span></div>
            <div class="stat"><b>{{ nodes.length - verifiedCount }}</b><span>还在试</span></div>
          </div>

          <div class="sec">作者原本是怎么做的</div>
          <p class="p-origin">{{ currentPost.origin.solution }}</p>

          <template v-if="view === 'origin'">
            <div class="sec">关键前提</div>
            <table class="diff-tb">
              <tr v-for="(v, key) in currentPost.origin.params" :key="key">
                <td class="dim">{{ key }}</td>
                <td class="mine">{{ v }}</td>
              </tr>
            </table>
            <div class="sec">适用边界</div>
            <p class="p-origin">{{ currentPost.origin.boundaries }}</p>
            <div class="sec">这颗太阳的价值</div>
            <p class="hint">
              它已经被迁移成 <b>{{ nodes.length }}</b> 个真实处境，其中 <b>{{ verifiedCount }}</b> 个做成了。<br />
              每做成一个，原帖价值 +1 —— 它解决的不再只是作者一个人。
            </p>
          </template>

          <template v-else>
            <div class="sec">这张星图怎么读</div>
            <p class="hint">
              正中这颗<b>太阳是原帖</b>，外圈每颗<b>星是一个真实处境</b>。<br />
              <b>实心蓝星</b>＝做成了，<b>空心橙星</b>＝还在试。<br />
              星离太阳的<b>远近</b>（三层轨道环）＝照搬要改多深：<b>改参数</b> → <b>动结构</b> → <b>换方案</b>。<br />
              <b>橙色虚线</b>＝走不通之后换思路重炼的下一版。<br /><br />
              点一颗星，看这一版针对他的处境改了什么；卡住了可以直接<b>复诊</b>，AI 会换一条没走过的路再来一版。
            </p>
            <div class="peer">
              一个帖子的价值 ＝ <b>走通的路</b> ＋ <b>被标记的死路</b>。同一个问题，不用每个人从头撞一遍墙。
            </div>
          </template>

          <div v-if="view === 'origin'" class="fb-row">
            <button class="fb-btn ghost" @click="backToSky">← 返回星空</button>
          </div>
        </template>

        <!-- 炼一个我的处境：把场景工坊拉进星图右侧面板 -->
        <template v-else-if="view === 'create' && currentPost">
          <AdaptBench :id="currentPost.id" mode="compact" @created="onAdaptCreated" @close="backToSky" />
        </template>

        <!-- 星详情 -->
        <template v-else-if="view === 'node' && active">
          <div class="kicker">
            A2 · 差异 · {{ active.depthName }}<template v-if="active.branchLabel"> · {{ active.branchLabel }}</template>
            <template v-if="active.version > 1"> · 第 {{ active.version }} 版</template>
          </div>
          <h2 class="p-title">{{ active.name }}</h2>
          <div class="np-head">
            <span class="verified" :class="active.verified ? 'ok' : 'draft'">
              {{ active.verified ? '● 已做成' : '○ 还在试' }}
            </span>
            <button class="back-btn" @click="backToSky">← 返回星空</button>
          </div>
          <p v-if="active.summary" class="p-origin lead">{{ active.summary }}</p>
          <p v-if="active.switch" class="switch-bar">⇄ {{ active.switch }}</p>

          <div class="sec">① 他的处境</div>
          <p class="p-origin">{{ active.sit }}</p>
          <p v-if="active.constraint" class="p-origin sub-line">硬条件：{{ active.constraint }}</p>

          <div v-if="active.diffs.length">
            <div class="sub">和原帖的关键差异</div>
            <table class="diff-tb">
              <tr><th>维度</th><th>原帖</th><th>他</th><th>影响</th></tr>
              <tr v-for="(d, i) in active.diffs" :key="i">
                <td class="dim">{{ d.dimension }}</td>
                <td>{{ d.origin }}</td>
                <td class="mine">{{ d.mine }}</td>
                <td>{{ d.impact }}</td>
              </tr>
            </table>
          </div>

          <div class="sec">② 针对这个处境，改成了这样</div>
          <ul class="moves">
            <li v-for="m in active.moves" :key="m.step">
              <b>第 {{ m.step }} 步 · {{ m.title }}</b>{{ m.action }}
              <span v-if="m.why" class="why">{{ m.why }}</span>
            </li>
          </ul>

          <template v-if="active.avoided.length">
            <div class="sec">③ 已替你避开的坑</div>
            <div class="avoid">
              <div class="at">✓ 下面这些，照搬原帖一定会踩，这一版已经绕开</div>
              <ul>
                <li v-for="(r, i) in active.avoided" :key="i">{{ r }}</li>
              </ul>
            </div>
          </template>

          <div class="sec">④ 反馈</div>
          <div class="fb-row">
            <template v-if="active.verified">
              <button class="fb-btn ghost" @click="markDone(true)">撤销</button>
              <button class="fb-btn unsolve" @click="startStuck">还是卡住了</button>
            </template>
            <template v-else>
              <button class="fb-btn solve" :disabled="busy" @click="markDone(false)">✓ 按这个做成了</button>
              <button class="fb-btn unsolve" :disabled="busy" @click="startStuck">还没成 · 复诊</button>
            </template>
          </div>
          <p v-if="active.rounds" class="fb-note">这一版已经复诊过 {{ active.rounds }} 次 —— 每排除一个方向，棋盘就小一圈。</p>
        </template>

        <!-- 复诊：① 卡在哪一步 -->
        <template v-else-if="view === 'pick' && active">
          <div class="kicker">复诊 · {{ active.name }}</div>
          <h2 class="p-title">这一步卡在哪了？</h2>
          <p class="p-origin">不用写长报告，选一个就行 —— 选完 AI 会再问你一句，问完就能换一条路。</p>
          <div class="flow">
            <h4>① 卡在哪一步</h4>
            <label v-for="(m, i) in active.moves" :key="'b' + i" class="chk">
              <input v-model="blk" type="radio" :value="String(i)" />
              <span><b>第 {{ m.step }} 步「{{ m.title }}」</b>：{{ m.action }}</span>
            </label>
            <label class="chk">
              <input v-model="blk" type="radio" value="all" />
              <span><b>整体就不对</b>：做是做了，结果和说的不一样</span>
            </label>
          </div>
          <div class="fb-row">
            <button class="fb-btn ghost" @click="backToNode">算了，我再试试</button>
            <button class="fb-btn solve" :disabled="busy" @click="askStuck">继续 →</button>
          </div>
        </template>

        <!-- 复诊：② AI 追问 -->
        <template v-else-if="view === 'ask' && active">
          <div class="kicker">复诊 · {{ active.name }}</div>
          <h2 class="p-title">AI 只想再确认一句</h2>
          <div class="flow">
            <h4>② {{ blk === 'all' ? '说说你看到的' : '说说这一步的现象' }}</h4>
            <p v-if="askLead" class="lead-msg">{{ askLead }}</p>
            <p class="ask-q">{{ askQuestion }}</p>
            <p class="reassure">{{ askReassure }}</p>
          </div>
          <textarea v-model="note" class="note" :placeholder="askPlaceholder" />
          <div class="fb-row">
            <button class="fb-btn ghost" @click="view = 'pick'">← 上一步</button>
            <button class="fb-btn solve" :disabled="busy" @click="submitVerdict">提交，看归因 →</button>
          </div>
        </template>

        <!-- 复诊：③ 归因结论 -->
        <template v-else-if="view === 'verdict' && active && verdict">
          <div class="kicker">复诊 · 第 {{ verdict.round }} 次 · {{ active.name }}</div>
          <h2 class="p-title">{{ verdict.headline }}</h2>
          <p class="p-origin">{{ verdict.detail }}</p>
          <p v-if="verdict.lead" class="lead-msg">{{ verdict.lead }}</p>

          <div class="learned">
            <div class="lt">我们学到了什么</div>
            <div class="ll">{{ verdict.learned }}</div>
            <div class="pills">
              <span v-for="(e, i) in verdict.excluded" :key="i" class="pill ex">已排除：{{ e }}</span>
            </div>
          </div>

          <div class="sec">还剩这些方向可以试</div>
          <div class="pills">
            <span v-for="(r, i) in verdict.remaining" :key="i" class="pill rem">{{ r }}</span>
          </div>

          <p v-if="verdict.note" class="hint" style="margin-top: 10px">{{ verdict.note }}</p>
          <p v-if="verdict.pending" class="fb-note">{{ verdict.pending }}</p>

          <div class="fb-row">
            <button class="fb-btn unsolve" @click="view = 'ask'">我再补一句</button>
            <button class="fb-btn solve" :disabled="busy" @click="doSwitch">
              {{ verdict.next.label }} →
            </button>
          </div>
          <div class="fb-row">
            <button class="fb-btn ghost" @click="view = 'help'">直接帮我找人问</button>
            <button class="fb-btn ghost" @click="backToNode">← 回这一版</button>
          </div>
        </template>

        <!-- 求助 -->
        <template v-else-if="view === 'help' && active">
          <div class="kicker">复诊 · {{ active.name }}</div>
          <h2 class="p-title">让踩过坑的人接手</h2>
          <div class="flow">
            <h4>① 先说清楚：你的问题值得被回答</h4>
            <p>「{{ active.sit }}」—— 这个处境和原帖差得够远，原帖作者当年没遇到，所以走不通是正常结果，不是你用错了。</p>
          </div>
          <div class="flow">
            <h4>② 材料已经替你整理好了</h4>
            <p>你的处境、和原帖的每一条差异、已经走过的路，都在下面这一段里。</p>
            <div class="help-btns">
              <button
                v-for="ch in helpChannels"
                :key="ch.key"
                class="chip-btn"
                :class="{ on: helpCh === ch.key }"
                @click="helpCh = ch.key"
              >
                {{ ch.label }}
              </button>
            </div>
            <textarea class="help-box" readonly :value="helpText" />
            <button class="copy-btn" @click="copyHelp">复制这一段</button>
            <p v-if="copied" class="fb-note">已复制 ✓ 直接粘贴发出就行</p>
          </div>
          <div class="flow">
            <h4>③ 我们还在</h4>
            <p>发出去之后，如果这个方向有了新进展，它会变成星图上新的一颗星 —— 你不用一直盯着。</p>
          </div>
          <div class="fb-row"><button class="fb-btn ghost" @click="backToNode">← 回这一版</button></div>
        </template>
      </aside>
    </div>

    <!-- ===== 已收录处境抽屉 ===== -->
    <div class="drawer" :class="{ open: drawerOpen }">
      <div class="drawer-hd">
        <div>
          <div class="dt">已收录处境</div>
          <div class="ds">同一个原帖，别人趟过的真实处境</div>
        </div>
        <button class="dclose" @click="drawerOpen = false">✕</button>
      </div>
      <div class="drawer-list">
        <template v-for="g in drawerGroups" :key="g.name">
          <div v-if="g.list.length" class="dgrp">{{ g.name }} · {{ g.list.length }} 个</div>
          <div
            v-for="n in g.list"
            :key="n.id"
            class="drow"
            :class="{ on: activeId === n.id }"
            @click="focusScene(n)"
          >
            <i class="ddot" :class="{ v: n.verified }" :style="{ '--dc': n.verified ? STAR_ON : STAR_OFF }" />
            <span class="dn">{{ starLabel(n) }}</span>
            <span class="dm">{{ n.verified ? '已做成' : '还在试' }} · {{ n.peers }}人</span>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, ref } from 'vue'
import { getStarMap, runAdapt, submitFeedback } from '../api'
import AdaptBench from './AdaptBench.vue'

/* ---------------- 常量 ---------------- */
const CX = 440
const CY = 400
// 轨道半径：放大以保证即使被 SQUASH 压扁（顶/底方向），最内圈星也明显落在太阳之外
const RING = { 1: 198, 2: 280, 3: 362 }
const SQUASH = 0.46
const RAD = Math.PI / 180
const STAR_ON = '#056de8'
const STAR_OFF = '#f0a03c'
const DEPTH_GROUPS = [
  [1, '改参数'],
  [2, '动结构'],
  [3, '换方案']
]
const DEPTH_NAME = ['', '改参数', '动结构', '换方案']
const DRAFT_ID = 'draft'

/* ---------------- 数据 ---------------- */
const loading = ref(true)
const posts = ref([])
const curIdx = ref(0)
const currentPost = computed(() => posts.value[curIdx.value] || null)

// 一次性进场动画：load 完成 / 切换原帖时触发，移除再添加类以便重播
const entered = ref(false)
function playEnter() {
  entered.value = false
  requestAnimationFrame(() => requestAnimationFrame(() => (entered.value = true)))
}

async function load() {
  loading.value = true
  try {
    const d = await getStarMap()
    posts.value = d.posts || []
    if (curIdx.value >= posts.value.length) curIdx.value = 0
  } catch (e) {
    posts.value = []
  } finally {
    loading.value = false
    await nextTick()
    fitView(false)
    playEnter()
  }
}
onMounted(load)

function switchPost(i) {
  curIdx.value = i
  view.value = 'overview'
  activeId.value = null
  hoverId.value = null
  nextTick(() => {
    fitView()
    playEnter()
  })
}

/* ---------------- 布局：倾斜星盘 ---------------- */
function starPath(R, r) {
  const p = []
  for (let i = 0; i < 8; i++) {
    const a = (-90 + i * 45) * RAD
    const rad = i % 2 === 0 ? R : r
    p.push((Math.cos(a) * rad).toFixed(2) + ' ' + (Math.sin(a) * rad).toFixed(2))
  }
  return 'M' + p.join(' L') + ' Z'
}

function relaxAngles(pos) {
  const MIN = 106
  for (let it = 0; it < 240; it++) {
    let moved = false
    for (let a = 0; a < pos.length; a++) {
      for (let b = a + 1; b < pos.length; b++) {
        const A = pos[a]
        const B = pos[b]
        const ax = CX + A.r * Math.cos(A.ang * RAD)
        const ay = CY + A.r * Math.sin(A.ang * RAD)
        const bx = CX + B.r * Math.cos(B.ang * RAD)
        const by = CY + B.r * Math.sin(B.ang * RAD)
        const d = Math.hypot(bx - ax, by - ay)
        if (d >= MIN || d < 0.001) continue
        moved = true
        const half = (MIN - d) * 0.55
        const da = half / Math.max(A.r * RAD, 1)
        const db = half / Math.max(B.r * RAD, 1)
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
}

const nodes = computed(() => {
  const p = currentPost.value
  if (!p) return []
  const list = p.scenes || []
  const N = list.length
  if (!N) return []

  // 1) 按 branch 分组（保持首次出现顺序），每组占一段连续扇区 —— 同分支的星自然落在同一侧、挨在一起
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
  const gap = G > 1 ? Math.min(16, 360 / G / 2) : 0 // 组间留缝，避免不同分支贴在一起
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

  const pos = list.map((sc) => ({ ang: 0, r: RING[sc.depth] || RING[2], sc }))
  const idPos = new Map(list.map((sc, i) => [sc, i]))

  // 2) 组内按 depth 内→外排序，在该扇区内居中、紧凑铺开（同分支紧挨同一侧）
  const STEP_MAX = 34 // 同分支内最大角间距（度），越小越聚拢
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

  relaxAngles(pos)
  return pos.map((o, i) => {
    const rad = o.ang * RAD
    const r2 = o.r + 28 + ((i * 41) % 17) * 3 // +28 整体外扩，避开中心太阳
    const cos = Math.cos(rad)
    return {
      ...o.sc,
      idx: i,
      ang: o.ang,
      r: r2,
      x: CX + r2 * cos,
      y: CY + r2 * Math.sin(rad) * SQUASH,
      dx: cos * 16,
      dy: Math.sin(rad) * 16 * SQUASH,
      anchor: cos > 0.18 ? 'start' : cos < -0.18 ? 'end' : 'middle'
    }
  })
})

const links = computed(() => {
  // 只保留橙色「复诊链」（parent）：同一原帖的不同版本之间的连接。
  // 同分支的星通过「落在同一侧、紧挨在一起」来表达归属，不再画灰色连线。
  const by = new Map(nodes.value.map((n) => [n.id, n]))
  const out = []
  nodes.value.forEach((n) => {
    if (n.parentId && by.has(n.parentId)) out.push({ a: by.get(n.parentId), b: n, parent: true })
  })
  return out
})

// 临时新星：在现有星之间找最大角度空档插进去，表示“我要在这里新增一个处境”
function findDraftAngle(list) {
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
const draftNode = computed(() => {
  if (view.value !== 'create') return null
  const p = currentPost.value
  if (!p) return null
  const base = nodes.value
  const depth = 2
  const ang = findDraftAngle(base)
  const r = RING[depth] + 28 + ((base.length * 41) % 17) * 3
  const rad = ang * RAD
  const cos = Math.cos(rad)
  const sin = Math.sin(rad)
  return {
    id: DRAFT_ID,
    name: '我的新处境',
    sit: '在右侧面板描述你的真实处境，AI 会把它炼成一颗新星。',
    branch: '_draft',
    branchLabel: '新处境',
    depth,
    depthName: DEPTH_NAME[depth],
    verified: false,
    version: 1,
    peers: 0,
    idx: base.length,
    ang,
    r,
    x: CX + r * cos,
    y: CY + r * sin * SQUASH,
    dx: cos * 16,
    dy: sin * 16 * SQUASH,
    anchor: cos > 0.18 ? 'start' : cos < -0.18 ? 'end' : 'middle'
  }
})
const allNodes = computed(() => {
  const d = draftNode.value
  return d ? [...nodes.value, d] : nodes.value
})

const verifiedCount = computed(() => nodes.value.filter((n) => n.verified).length)
const rings = [1, 2, 3].map((d) => RING[d])
const sunTitle = computed(() => {
  const t = currentPost.value ? currentPost.value.title : ''
  return t.split(/[：:]/)[0].slice(0, 14)
})
function starLabel(n) {
  return n.version > 1 ? `${n.name} · 第${n.version}版` : n.name
}
function shortTitle(t) {
  return t.split(/[：:]/)[0].slice(0, 12)
}

/* ---------------- 视图 / 缩放 ---------------- */
const view = ref('overview')
const activeId = ref(null)
const hoverId = ref(null)
const active = computed(() => allNodes.value.find((n) => n.id === activeId.value) || null)
const busy = ref(false)

const k = ref(1)
const tx = ref(0)
const ty = ref(0)
const KMIN = 0.45
const KMAX = 4
const inv = computed(() => 1 / Math.sqrt(k.value))
const vpTransform = computed(() => `translate(${tx.value} ${ty.value}) scale(${k.value})`)
const wrapT = (n) => `translate(${n.x.toFixed(1)} ${n.y.toFixed(1)}) scale(${inv.value.toFixed(3)})`
const lblT = (n) => `translate(${n.dx.toFixed(1)} ${n.dy.toFixed(1)}) scale(${inv.value.toFixed(3)})`
const detT = (n) => `translate(${n.dx.toFixed(1)} ${(n.dy + 14).toFixed(1)}) scale(${inv.value.toFixed(3)})`

const lod = computed(() => (k.value < 0.8 ? 1 : k.value < 1.6 ? 2 : 3))
const lodClass = computed(() => 'lod' + lod.value)
const lodName = computed(() => ['', '总览', '星图', '细节'][lod.value])

const mouse = ref(null)
function popScale(n) {
  let s = 1
  const m = mouse.value
  if (m) {
    const d = Math.hypot(n.x - m.x, n.y - m.y)
    if (d < 155) s = 1 + 0.45 * Math.pow(1 - d / 155, 1.5)
  }
  if (activeId.value === n.id) s = Math.max(s, 2.0)
  if (n.id === DRAFT_ID) s = Math.max(s, 1.35)
  return s.toFixed(3)
}

const svgEl = ref(null)
const vpEl = ref(null)
function sPt(e) {
  const p = svgEl.value.createSVGPoint()
  p.x = e.clientX
  p.y = e.clientY
  return p.matrixTransform(svgEl.value.getScreenCTM().inverse())
}
function cPt(e) {
  const p = svgEl.value.createSVGPoint()
  p.x = e.clientX
  p.y = e.clientY
  return p.matrixTransform(vpEl.value.getScreenCTM().inverse())
}
const clamp = (v) => Math.min(KMAX, Math.max(KMIN, v))
function zoomAt(nk, sx, sy, cx, cy) {
  nk = clamp(nk)
  if (nk === k.value) return
  k.value = nk
  tx.value = sx - cx * nk
  ty.value = sy - cy * nk
}
function animateTo(nk, ntx, nty, dur = 420) {
  const k1 = k.value
  const tx1 = tx.value
  const ty1 = ty.value
  const t0 = performance.now()
  const step = (t) => {
    const p = Math.min((t - t0) / dur, 1)
    const e = 1 - Math.pow(1 - p, 3)
    k.value = k1 + (nk - k1) * e
    tx.value = tx1 + (ntx - tx1) * e
    ty.value = ty1 + (nty - ty1) * e
    if (p < 1) requestAnimationFrame(step)
  }
  requestAnimationFrame(step)
}
function zoomBy(f) {
  const c = { x: (CX - tx.value) / k.value, y: (CY - ty.value) / k.value }
  const nk = clamp(k.value * f)
  animateTo(nk, CX - c.x * nk, CY - c.y * nk, 300)
}
function fitView(anim = true) {
  if (!nodes.value.length) {
    if (anim) animateTo(1, 0, 0, 300)
    return
  }
  let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity
  nodes.value.forEach((n) => {
    const w = starLabel(n).length * 11 + 12
    const lx = n.x + n.dx + (n.anchor === 'start' ? 0 : n.anchor === 'end' ? -w : -w / 2)
    minX = Math.min(minX, Math.min(n.x - 13, lx - 4))
    maxX = Math.max(maxX, Math.max(n.x + 13, lx + w + 4))
    minY = Math.min(minY, n.y - 17)
    maxY = Math.max(maxY, n.y + 17)
  })
  const pad = 56
  minX -= pad
  maxX += pad
  minY -= pad
  maxY += pad
  const raw = Math.min(900 / (maxX - minX), 790 / (maxY - minY))
  const nk = Math.min(Math.max(raw, KMIN), 1.45)
  const ntx = CX - ((minX + maxX) / 2) * nk
  const nty = CY - ((minY + maxY) / 2) * nk
  if (anim) animateTo(nk, ntx, nty, 480)
  else {
    k.value = nk
    tx.value = ntx
    ty.value = nty
  }
}
function focusNode(n, z = 2.5) {
  const nk = clamp(z)
  animateTo(nk, CX - n.x * nk, CY - n.y * nk, 480)
}

/* ---------------- 指针交互 ---------------- */
let dragging = false
let moved = 0
let last = null
function onWheel(e) {
  const sp = sPt(e)
  const cp = cPt(e)
  zoomAt(k.value * Math.exp(-e.deltaY * (e.ctrlKey ? 0.011 : 0.0022)), sp.x, sp.y, cp.x, cp.y)
}
function onDown(e) {
  if (e.pointerType === 'mouse' && e.button !== 0) return
  dragging = true
  moved = 0
  last = sPt(e)
  try {
    svgEl.value.setPointerCapture(e.pointerId)
  } catch (_) {
    /* noop */
  }
}
function onMove(e) {
  mouse.value = cPt(e)
  if (!dragging) return
  const p = sPt(e)
  const dx = p.x - last.x
  const dy = p.y - last.y
  moved += Math.abs(dx) + Math.abs(dy)
  tx.value += dx
  ty.value += dy
  last = p
}
function onUp(e) {
  if (dragging) {
    dragging = false
    try {
      svgEl.value.releasePointerCapture(e.pointerId)
    } catch (_) {
      /* noop */
    }
    if (moved <= 4) handleTap(e.clientX, e.clientY)
  }
}
function onLeave() {
  mouse.value = null
  hoverId.value = null
}
function handleTap(cx, cy) {
  const el = document.elementFromPoint(cx, cy)
  if (!el) return
  const g = el.closest('.node')
  if (g) {
    const raw = g.dataset.id
    const id = raw === DRAFT_ID ? DRAFT_ID : Number(raw)
    if (id === DRAFT_ID) {
      // 点临时新星：保持在创建面板
      activeId.value = DRAFT_ID
      view.value = 'create'
      const d = draftNode.value
      if (d) focusNode(d)
      return
    }
    if (activeId.value === id) backToSky()
    else openNode(id)
    return
  }
  if (el.closest('.corehit')) {
    openOrigin()
    return
  }
  backToSky()
}

/* ---------------- 面板动作 ---------------- */
function openNode(id) {
  activeId.value = id
  view.value = 'node'
  const n = allNodes.value.find((x) => x.id === id)
  if (n) focusNode(n)
}
function openOrigin() {
  activeId.value = null
  view.value = 'origin'
  fitView()
}
function backToSky() {
  activeId.value = null
  view.value = 'overview'
  fitView()
}
function startCreate() {
  activeId.value = DRAFT_ID
  view.value = 'create'
  nextTick(() => {
    const d = draftNode.value
    if (d) focusNode(d, 2.5)
  })
}
async function onAdaptCreated(adaptation) {
  await load()
  const n = nodes.value.find((x) => x.id === adaptation.id)
  if (n) {
    activeId.value = n.id
    view.value = 'node'
    nextTick(() => focusNode(n, 2.5))
  } else {
    backToSky()
  }
}
function backToNode() {
  view.value = 'node'
}

/* 做成了 / 撤销 */
async function markDone(undo) {
  if (!active.value) return
  busy.value = true
  try {
    if (undo) {
      // 后端目前没有撤销接口：清掉最新一条 done 记录的做法会误伤，这里仅提示并回星图
      toast('想改状态？在场景工坊里重新炼一版就行')
      backToSky()
      return
    }
    const r = await submitFeedback(active.value.id, { result: 'done' })
    toast(r && r.message ? r.message : '做成了 ✓ 原帖价值 +1')
    await load()
    const again = nodes.value.find((n) => n.id === activeId.value)
    if (again) {
      view.value = 'node'
      focusNode(again)
    } else backToSky()
  } catch (e) {
    toast('没记下来，稍后再试一次')
  } finally {
    busy.value = false
  }
}

/* ---------------- 复诊闭环（接真实接口） ---------------- */
const blk = ref('all')
const note = ref('')
const askQuestion = ref('')
const askLead = ref('')
const askReassure = ref('')
const askPlaceholder = ref('就写一句')
const verdict = ref(null)

function startStuck() {
  blk.value = 'all'
  note.value = ''
  view.value = 'pick'
}

async function askStuck() {
  if (!active.value) return
  busy.value = true
  try {
    const isStep = blk.value !== 'all'
    const payload = {
      result: 'stuck',
      block_type: isStep ? 'step_error' : 'phenomenon',
      block_step: isStep ? active.value.moves[Number(blk.value)].step : null
    }
    const r = await submitFeedback(active.value.id, payload)
    askQuestion.value = r.question || '说说你看到的现象？'
    askLead.value = r.lead || ''
    askReassure.value = r.reassure || '别急。排除一个方向，也是进展。'
    askPlaceholder.value = r.placeholder || '就写一句'
    view.value = 'ask'
  } catch (e) {
    toast('AI 这会儿没接上，稍后再试')
  } finally {
    busy.value = false
  }
}

async function submitVerdict() {
  if (!active.value) return
  if (!note.value.trim()) {
    toast('补一句具体现象，AI 才归因得准')
    return
  }
  busy.value = true
  try {
    const isStep = blk.value !== 'all'
    const r = await submitFeedback(active.value.id, {
      result: 'stuck',
      block_type: isStep ? 'step_error' : 'phenomenon',
      block_step: isStep ? active.value.moves[Number(blk.value)].step : null,
      user_note: note.value.trim()
    })
    verdict.value = r
    view.value = 'verdict'
  } catch (e) {
    toast('归因没出来，稍后再试')
  } finally {
    busy.value = false
  }
}

async function doSwitch() {
  if (!active.value || !verdict.value) return
  busy.value = true
  try {
    const a = active.value
    const res = await runAdapt({
      post_id: currentPost.value.id,
      scene_tag: a.name,
      user_scene: a.sit,
      user_constraint: a.constraint,
      avoid: verdict.value.avoid || [],
      parent_id: a.id
    })
    const newId = res && res.adaptation ? res.adaptation.id : null
    await load()
    if (newId) {
      const n = nodes.value.find((x) => x.id === newId)
      if (n) {
        activeId.value = newId
        view.value = 'node'
        focusNode(n)
        toast('已经避开走过的路 · 新的一版出来了')
      }
    }
  } catch (e) {
    toast('换路没成，稍后再试')
  } finally {
    busy.value = false
  }
}

/* ---------------- 求助 ---------------- */
const helpChannels = [
  { key: 'author', label: '发给原帖作者' },
  { key: 'expert', label: '发给同处境的人' },
  { key: 'circle', label: '发到相关圈子' }
]
const helpCh = ref('author')
const copied = ref(false)
const helpText = computed(() => {
  if (!active.value || !currentPost.value) return ''
  const a = active.value
  const p = currentPost.value
  const lead =
    helpCh.value === 'author'
      ? `向《${p.title}》的作者请教`
      : helpCh.value === 'expert'
        ? `向和「${a.name}」处境相同的人请教`
        : `发到「${a.branchLabel || a.depthName}」相关圈子`
  const diffs = a.diffs.map((d) => `　· ${d.dimension}：原帖「${d.origin}」，我「${d.mine}」（${d.impact}）`).join('\n')
  const moves = a.moves.map((m) => `　· 第 ${m.step} 步 ${m.title}：${m.action}`).join('\n')
  return [
    `【场景炼金师 · 求助】${lead}`,
    '———————————',
    `原帖：${p.title}`,
    `原帖的基准处境：${p.origin.scene}`,
    '',
    '我的真实处境：',
    a.sit,
    a.constraint ? `硬条件：${a.constraint}` : '',
    '',
    '和原帖的关键差异：',
    diffs || '　（暂无）',
    '',
    '已经走过的方向：',
    moves || '　（暂无）',
    '',
    `目前卡在：${note.value || '（见上方描述）'}`,
    '',
    '这个处境原帖作者当年没遇到，AI 已经替我重排过一版还是没走通。',
    '有没有踩过类似坑的朋友，指点一下？谢谢！'
  ]
    .filter((x) => x !== null)
    .join('\n')
})
async function copyHelp() {
  try {
    if (navigator.clipboard) await navigator.clipboard.writeText(helpText.value)
    else {
      const ta = document.querySelector('.help-box')
      ta.select()
      document.execCommand('copy')
    }
    copied.value = true
    setTimeout(() => (copied.value = false), 2600)
  } catch (_) {
    /* noop */
  }
}

/* ---------------- 提示条 ---------------- */
const toastMsg = ref('')
const toastOn = ref(false)
let tt = null
function toast(msg) {
  toastMsg.value = msg
  toastOn.value = true
  clearTimeout(tt)
  tt = setTimeout(() => (toastOn.value = false), 2800)
}

/* ---------------- 抽屉 ---------------- */
const drawerOpen = ref(false)
const drawerGroups = computed(() =>
  DEPTH_GROUPS.map(([d, name]) => ({
    name,
    list: nodes.value.filter((n) => (n.depth || 2) === d)
  }))
)
function focusScene(n) {
  drawerOpen.value = false
  openNode(n.id)
}
</script>

<style scoped>
.starmap {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.card {
  background: var(--bg-2);
  border: 1px solid var(--border);
  border-radius: 8px;
}

/* 顶部条 */
.sm-head {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
  flex-wrap: wrap;
}
.sm-chips {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  min-width: 0;
}
.sm-chips::-webkit-scrollbar {
  height: 0;
}
.chip {
  padding: 6px 12px;
  border: 1px solid var(--border);
  border-radius: 999px;
  background: var(--bg-2);
  color: var(--text-2);
  font-size: 12px;
  cursor: pointer;
  white-space: nowrap;
  font-family: inherit;
  transition: 0.16s;
}
.chip:hover {
  color: var(--zh-blue);
  border-color: var(--zh-blue-line-strong);
  background: var(--zh-blue-soft);
}
.chip.on {
  color: #fff;
  background: var(--zh-blue);
  border-color: var(--zh-blue);
}
.sm-actions {
  display: flex;
  gap: 8px;
  margin-left: auto;
}
.btn {
  display: inline-flex;
  align-items: center;
  padding: 7px 13px;
  border-radius: 6px;
  font-size: 12.5px;
  cursor: pointer;
  font-family: inherit;
  white-space: nowrap;
  text-decoration: none;
  transition: 0.16s;
}
.btn.ghost {
  border: 1px solid var(--border);
  background: var(--bg-2);
  color: var(--text-2);
}
.btn.ghost:hover {
  color: var(--zh-blue);
  border-color: var(--zh-blue-line-strong);
  background: var(--zh-blue-soft);
}
.btn.ghost b {
  color: var(--zh-blue);
}
.btn.primary {
  border: 1px solid var(--zh-blue);
  background: var(--zh-blue);
  color: #fff;
  font-weight: 500;
}
.btn.primary:hover {
  background: var(--zh-blue-hover);
}

/* 主体 */
.sm-body {
  display: flex;
  gap: 12px;
  align-items: stretch;
}
.stage {
  position: relative;
  flex: 1;
  min-width: 0;
  height: calc(100vh - 260px);
  min-height: 520px;
  background: #fbfcfd;
  border: 1px solid var(--border);
  border-radius: 8px;
  overflow: hidden;
}
.web {
  width: 100%;
  height: 100%;
  display: block;
  cursor: grab;
  touch-action: none;
}
.web:active {
  cursor: grabbing;
}
.panel {
  width: 430px;
  flex: 0 0 430px;
  padding: 18px 20px;
  overflow-y: auto;
  max-height: calc(100vh - 260px);
}
.panel::-webkit-scrollbar {
  width: 6px;
}
.panel::-webkit-scrollbar-thumb {
  background: #dfe3e8;
  border-radius: 3px;
}

/* svg */
.orbit {
  fill: none;
  stroke: #d5dbe4;
  stroke-width: 1;
  opacity: 0.75;
  stroke-dasharray: 3 7;
}
.ray {
  fill: none;
  stroke-width: 1.2;
  opacity: 0.5;
}
.ray.hot {
  opacity: 1;
  stroke-width: 2;
}
.xlink {
  stroke: #c6ccd6;
  stroke-width: 1;
  opacity: 0.55;
  stroke-dasharray: 4 4;
}
.xlink.parent {
  stroke: #f0a03c;
  stroke-width: 1.4;
  opacity: 0.9;
  stroke-dasharray: 5 4;
}
.node {
  cursor: pointer;
}
.pop {
  transform: scale(var(--s, 1));
  transform-box: fill-box;
  transform-origin: center;
  transition: transform 0.2s cubic-bezier(0.34, 1.4, 0.64, 1);
}
.star {
  stroke-linejoin: round;
}
.star.on {
  filter: drop-shadow(0 1px 3px rgba(5, 109, 232, 0.4));
}
.star.tw {
  animation: tw 5s ease-in-out infinite;
}
@keyframes tw {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.6;
  }
}
/* 临时新星：创建中，蓝色虚线 + 呼吸，区别于已收录的星 */
.node.draft .star {
  fill: #ffffff;
  stroke: var(--zh-blue);
  stroke-width: 2;
  stroke-dasharray: 3 3;
  animation: draftPulse 1.6s ease-in-out infinite;
}
.node.draft .lbl {
  fill: var(--zh-blue);
}
@keyframes draftPulse {
  0%,
  100% {
    opacity: 0.5;
  }
  50% {
    opacity: 1;
  }
}
.lbl {
  font-size: 12.5px;
  font-weight: 500;
  fill: #1a1a1a;
  paint-order: stroke;
  stroke: #fbfcfd;
  stroke-width: 4.5;
  stroke-linejoin: round;
  transition: font-size 0.2s;
}
.node.on .lbl {
  font-size: 14px;
  fill: var(--zh-blue);
}
.node-detail {
  font-size: 10.5px;
  fill: #8590a6;
  paint-order: stroke;
  stroke: #fbfcfd;
  stroke-width: 4;
  stroke-linejoin: round;
}
.core-sub {
  font-size: 15.5px;
  font-weight: 600;
  fill: #174a86;
}
.core-num {
  font-size: 13px;
  fill: var(--zh-blue);
  font-weight: 600;
}
.core-hint {
  font-size: 11px;
  fill: #8590a6;
}
.corehit {
  cursor: pointer;
}
.web.lod1 .node-detail {
  display: none;
}
.web.locked .node:not(.on) {
  opacity: 0.4;
  transition: opacity 0.34s ease;
}
.web.locked .ray:not(.hot) {
  opacity: 0.08;
}
.web.locked .orbit {
  opacity: 0.16;
}
.web.locked .xlink {
  opacity: 0.12;
}
.web.locked .sun-glow {
  opacity: 0.3;
}

/* 进场动画（一次性，entered 触发；只动 opacity / transform，不碰星点定位 transform）*/
.web:not(.entered) .sun,
.web:not(.entered) .node,
.web:not(.entered) .ray,
.web:not(.entered) .orbit {
  opacity: 0;
}
.web.entered .sun {
  transform-box: fill-box;
  transform-origin: center;
  animation: sunIn 0.7s cubic-bezier(0.22, 1, 0.36, 1) backwards;
}
.web.entered .orbit {
  animation: fadeIn 0.6s ease 0.12s backwards;
}
.web.entered .ray {
  animation: fadeIn 0.5s ease backwards;
  animation-delay: calc(var(--i, 0) * 0.05s + 0.28s);
}
.web.entered .node {
  animation: fadeIn 0.55s ease backwards;
  animation-delay: calc(var(--i, 0) * 0.05s + 0.3s);
}
@keyframes sunIn {
  from {
    opacity: 0;
    transform: scale(0.55);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}
@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

/* 浮层 */
.hintbar {
  position: absolute;
  left: 14px;
  top: 12px;
  font-size: 11.5px;
  color: var(--text-3);
  line-height: 1.9;
  background: rgba(255, 255, 255, 0.86);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 8px 12px;
  max-width: 320px;
  pointer-events: none;
}
.hintbar b {
  color: var(--text-2);
  font-weight: 400;
}
.zoomtag {
  position: absolute;
  left: 14px;
  bottom: 12px;
  font-size: 11.5px;
  color: var(--text-3);
  border: 1px solid var(--border);
  border-radius: 999px;
  padding: 5px 12px;
  background: #fff;
}
.zoomtag b {
  color: var(--zh-blue);
}
.zoombar {
  position: absolute;
  right: 14px;
  bottom: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.zoombar button {
  width: 32px;
  height: 32px;
  border-radius: 6px;
  border: 1px solid var(--border);
  background: #fff;
  color: var(--text-2);
  font-size: 15px;
  line-height: 1;
  cursor: pointer;
  padding: 0;
  font-family: inherit;
  transition: 0.16s;
}
.zoombar button.sm {
  font-size: 11px;
}
.zoombar button:hover {
  color: var(--zh-blue);
  border-color: var(--zh-blue-line-strong);
  background: var(--zh-blue-soft);
}
.toast {
  position: absolute;
  left: 50%;
  bottom: 22px;
  transform: translateX(-50%) translateY(12px);
  background: var(--zh-blue);
  color: #fff;
  padding: 9px 18px;
  border-radius: 999px;
  font-size: 13px;
  opacity: 0;
  transition: 0.3s;
  pointer-events: none;
  white-space: nowrap;
  box-shadow: 0 6px 20px rgba(5, 109, 232, 0.25);
}
.toast.on {
  opacity: 1;
  transform: translateX(-50%) translateY(0);
}

/* 面板内容 */
.pv-empty {
  color: var(--text-3);
  font-size: 13.5px;
  padding: 20px 0;
}
.pv-empty a {
  color: var(--zh-blue);
}
.kicker {
  font-size: 11.5px;
  letter-spacing: 1.5px;
  color: var(--zh-blue);
  font-weight: 500;
}
.p-title {
  font-size: 19px;
  font-weight: 600;
  margin: 8px 0 6px;
  line-height: 1.45;
  color: var(--text);
}
.p-origin {
  font-size: 13.5px;
  color: var(--text-2);
  margin: 0 0 10px;
  line-height: 1.8;
}
.p-origin.lead {
  color: var(--zh-blue);
}
.sub-line {
  color: var(--text-3);
  font-size: 12.5px;
}
.switch-bar {
  font-size: 12.5px;
  color: #0b7a4d;
  background: #e8f7f0;
  border: 1px solid #bfe6d3;
  border-radius: 6px;
  padding: 8px 11px;
  line-height: 1.7;
  margin: 0 0 10px;
}
.tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 10px;
}
.tag {
  font-size: 11.5px;
  color: var(--text-2);
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: 4px;
  padding: 3px 8px;
}
.stat-line {
  display: flex;
  gap: 10px;
  margin: 12px 0 4px;
}
.stat {
  flex: 1;
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 9px 11px;
}
.stat b {
  display: block;
  font-size: 20px;
  color: var(--zh-blue);
  line-height: 1.2;
}
.stat span {
  font-size: 11.5px;
  color: var(--text-3);
}
.sec {
  margin: 18px 0 8px;
  font-size: 12px;
  color: var(--text-3);
  letter-spacing: 1px;
  font-weight: 500;
}
.sub {
  font-size: 11.5px;
  color: var(--text-3);
  margin: 12px 0 4px;
}
.diff-tb {
  width: 100%;
  border-collapse: collapse;
  font-size: 12.5px;
}
.diff-tb th {
  text-align: left;
  color: var(--text-3);
  font-weight: 400;
  padding: 5px;
  border-bottom: 1px solid var(--border);
}
.diff-tb td {
  padding: 7px 5px;
  border-bottom: 1px solid var(--border);
  color: var(--text-2);
  vertical-align: top;
  line-height: 1.7;
}
.diff-tb td.dim {
  color: var(--text);
  white-space: nowrap;
  font-weight: 500;
}
.diff-tb td.mine {
  color: var(--zh-blue);
}
.moves {
  margin: 0;
  padding: 0;
  list-style: none;
  counter-reset: mv;
}
.moves li {
  position: relative;
  padding: 8px 0 8px 26px;
  font-size: 13px;
  color: var(--text-2);
  border-bottom: 1px solid var(--border);
  line-height: 1.75;
}
.moves li:last-child {
  border-bottom: 0;
}
.moves li::before {
  counter-increment: mv;
  content: counter(mv);
  position: absolute;
  left: 0;
  top: 10px;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: var(--zh-blue-soft);
  color: var(--zh-blue);
  font-size: 10.5px;
  line-height: 16px;
  text-align: center;
  font-weight: 600;
}
.moves li b {
  display: block;
  color: var(--text);
  font-size: 12.5px;
  margin-bottom: 1px;
}
.moves .why {
  display: block;
  color: var(--text-3);
  font-size: 12px;
  margin-top: 2px;
}
.avoid {
  background: #e8f7f0;
  border: 1px solid #bfe6d3;
  border-radius: 6px;
  padding: 11px 13px;
}
.avoid .at {
  font-size: 12px;
  color: var(--ok, #0f9d63);
  font-weight: 600;
  margin-bottom: 6px;
}
.avoid ul {
  margin: 0;
  padding: 0;
  list-style: none;
}
.avoid li {
  font-size: 12.5px;
  color: #0b7a4d;
  line-height: 1.8;
  padding: 3px 0 3px 18px;
  position: relative;
}
.avoid li::before {
  content: '✓';
  position: absolute;
  left: 0;
  top: 3px;
  font-size: 11px;
}
.peer {
  font-size: 13px;
  color: var(--text-2);
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 10px 12px;
  margin-top: 12px;
  line-height: 1.75;
}
.peer b {
  color: var(--zh-blue);
}
.hint {
  font-size: 13px;
  color: var(--text-2);
  line-height: 1.95;
}
.hint b {
  color: var(--text);
}
.np-head {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}
.verified {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 11.5px;
  padding: 3px 9px;
  border-radius: 4px;
}
.verified.ok {
  color: #0b7a4d;
  background: #e8f7f0;
  border: 1px solid #bfe6d3;
}
.verified.draft {
  color: #b8792a;
  background: #fef6e9;
  border: 1px solid #f6ddb6;
}
.back-btn {
  margin-left: auto;
  padding: 5px 11px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--bg-2);
  color: var(--text-2);
  font-size: 12px;
  cursor: pointer;
  font-family: inherit;
  transition: 0.16s;
}
.back-btn:hover {
  color: var(--zh-blue);
  border-color: var(--zh-blue-line-strong);
  background: var(--zh-blue-soft);
}
.fb-row {
  display: flex;
  gap: 10px;
  margin: 12px 0 4px;
}
.fb-btn {
  flex: 1;
  padding: 10px 10px;
  border-radius: 6px;
  border: 1px solid var(--border);
  background: var(--bg-2);
  color: var(--text);
  font-size: 13px;
  cursor: pointer;
  font-family: inherit;
  transition: 0.16s;
}
.fb-btn:disabled {
  opacity: 0.5;
  cursor: default;
}
.fb-btn.solve {
  border-color: #0f9d63;
  color: #0b7a4d;
  background: #e8f7f0;
}
.fb-btn.solve:hover:not(:disabled) {
  background: #d9f0e4;
}
.fb-btn.unsolve:hover:not(:disabled) {
  color: var(--zh-blue);
  border-color: var(--zh-blue-line-strong);
  background: var(--zh-blue-soft);
}
.fb-btn.ghost:hover:not(:disabled) {
  color: var(--zh-blue);
  border-color: var(--zh-blue-line-strong);
  background: var(--zh-blue-soft);
}
.fb-note {
  font-size: 12.5px;
  color: #0b7a4d;
  margin: 8px 0 0;
}
.flow {
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 12px 14px;
  margin: 12px 0;
  background: var(--surface-2);
}
.flow h4 {
  margin: 0 0 8px;
  font-size: 13.5px;
  color: var(--text);
  font-weight: 600;
}
.flow p {
  margin: 0 0 8px;
  font-size: 13px;
  color: var(--text-2);
  line-height: 1.85;
}
.lead-msg {
  color: var(--zh-blue) !important;
}
.ask-q {
  color: var(--text) !important;
}
.reassure {
  color: var(--text-3) !important;
  margin-bottom: 0 !important;
}
.chk {
  display: flex;
  align-items: flex-start;
  gap: 9px;
  font-size: 12.5px;
  color: var(--text-2);
  margin: 8px 0;
  line-height: 1.7;
  cursor: pointer;
}
.chk input {
  margin-top: 4px;
  accent-color: var(--zh-blue);
  flex: 0 0 auto;
}
.chk b {
  color: var(--text);
}
.note {
  width: 100%;
  height: 84px;
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 10px 12px;
  font: 13px/1.7 inherit;
  color: var(--text);
  resize: none;
  background: var(--bg-2);
}
.note:focus {
  outline: none;
  border-color: var(--zh-blue);
}
.learned {
  border: 1px solid var(--zh-blue-line-strong);
  background: var(--zh-blue-soft);
  border-radius: 6px;
  padding: 12px 14px;
  margin: 12px 0;
}
.learned .lt {
  font-size: 12.5px;
  color: var(--zh-blue);
  font-weight: 600;
  margin-bottom: 6px;
}
.learned .ll {
  font-size: 13px;
  color: var(--text);
  line-height: 1.85;
}
.pills {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 8px;
}
.pill {
  font-size: 11.5px;
  padding: 3px 9px;
  border-radius: 4px;
  background: var(--bg-2);
  border: 1px solid var(--border);
  color: var(--text-3);
}
.pill.ex {
  color: #b8452f;
  background: #fdeeeb;
  border-color: #f4cec6;
  text-decoration: line-through;
}
.pill.rem {
  color: var(--zh-blue);
  border-color: var(--zh-blue-line-strong);
}
.help-btns {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin: 10px 0;
}
.chip-btn {
  padding: 6px 12px;
  border: 1px solid var(--border);
  border-radius: 999px;
  background: var(--bg-2);
  color: var(--text-2);
  font-size: 12.5px;
  cursor: pointer;
  font-family: inherit;
  transition: 0.16s;
}
.chip-btn:hover {
  color: var(--zh-blue);
  border-color: var(--zh-blue-line-strong);
}
.chip-btn.on {
  color: #fff;
  background: var(--zh-blue);
  border-color: var(--zh-blue);
}
.help-box {
  width: 100%;
  height: 170px;
  background: var(--bg-2);
  border: 1px solid var(--border);
  border-radius: 6px;
  color: var(--text-2);
  font: 12.5px/1.75 ui-monospace, Menlo, Consolas, monospace;
  padding: 11px;
  resize: none;
}
.copy-btn {
  margin-top: 8px;
  padding: 8px 14px;
  border: 1px solid var(--zh-blue);
  border-radius: 6px;
  background: var(--zh-blue);
  color: #fff;
  font-size: 12.5px;
  cursor: pointer;
  font-family: inherit;
}
.copy-btn:hover {
  background: var(--zh-blue-hover);
}

/* 抽屉 */
.drawer {
  position: fixed;
  top: 52px;
  right: 0;
  bottom: 0;
  width: 400px;
  max-width: 88vw;
  z-index: 60;
  background: var(--bg-2);
  border-left: 1px solid var(--border);
  transform: translateX(103%);
  transition: transform 0.34s cubic-bezier(0.22, 1, 0.36, 1);
  display: flex;
  flex-direction: column;
  box-shadow: -14px 0 40px rgba(0, 0, 0, 0.08);
}
.drawer.open {
  transform: none;
}
.drawer-hd {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 18px;
  border-bottom: 1px solid var(--border);
}
.drawer-hd .dt {
  font-size: 14px;
  font-weight: 600;
  color: var(--text);
}
.drawer-hd .ds {
  font-size: 11.5px;
  color: var(--text-3);
  margin-top: 2px;
}
.dclose {
  margin-left: auto;
  width: 28px;
  height: 28px;
  border-radius: 6px;
  border: 1px solid var(--border);
  background: var(--bg-2);
  color: var(--text-3);
  cursor: pointer;
  font-size: 13px;
  font-family: inherit;
}
.dclose:hover {
  color: var(--text);
  background: var(--surface-2);
}
.drawer-list {
  flex: 1;
  overflow-y: auto;
  padding: 6px 12px 28px;
}
.dgrp {
  font-size: 11px;
  letter-spacing: 1px;
  color: var(--text-3);
  padding: 14px 8px 6px;
}
.drow {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 6px;
  border: 1px solid transparent;
  cursor: pointer;
  transition: 0.14s;
  margin-bottom: 2px;
}
.drow:hover {
  background: var(--surface-2);
  border-color: var(--border);
}
.drow.on {
  background: var(--zh-blue-soft);
  border-color: var(--zh-blue-line-strong);
}
.ddot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  flex: 0 0 9px;
  border: 1.6px solid var(--dc);
  background: transparent;
}
.ddot.v {
  background: var(--dc);
}
.drow .dn {
  font-size: 13px;
  color: var(--text);
}
.drow .dm {
  margin-left: auto;
  font-size: 11px;
  color: var(--text-3);
  white-space: nowrap;
}

/* 响应式 */
@media (max-width: 1180px) {
  .panel {
    width: 360px;
    flex: 0 0 360px;
  }
}
@media (max-width: 900px) {
  .sm-body {
    flex-direction: column;
  }
  .stage {
    height: 56vh;
    flex: none;
  }
  .panel {
    width: auto;
    flex: none;
    max-height: none;
  }
  .hintbar {
    display: none;
  }
  .sm-actions {
    margin-left: 0;
  }
}
</style>
