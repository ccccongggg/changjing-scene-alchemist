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
      <section class="stage" ref="stageEl">
        <svg
          ref="svgEl"
          class="web"
          :class="[lodClass, { locked: !!activeId, entered, hovering: !!hoverId }]"
          :viewBox="viewBox"
          preserveAspectRatio="xMidYMid meet"
          @wheel.prevent="onWheel"
          @pointerdown="onDown"
          @pointermove="onMove"
          @pointerup="onUp"
          @pointercancel="onUp"
          @pointerleave="onLeave"
        >
          <defs>
            <!-- 星核光晕：最外那层冷色柔光，到边缘必须完全透明（不能有硬边），否则白底上会看到一个脏圆盘 -->
            <radialGradient id="sunHalo">
              <stop offset="0%" stop-color="#5967f2" stop-opacity="0.4" />
              <stop offset="45%" stop-color="#5967f2" stop-opacity="0.18" />
              <stop offset="100%" stop-color="#0b1020" stop-opacity="0" />
            </radialGradient>
            <radialGradient id="sunGrad">
              <stop offset="0%" stop-color="#4a3a1a" />
              <stop offset="62%" stop-color="#2e2410" />
              <stop offset="100%" stop-color="#0b1020" stop-opacity="0.2" />
            </radialGradient>
            <radialGradient id="coreGrad">
              <stop offset="0%" stop-color="#f0d9a8" />
              <stop offset="58%" stop-color="#dbb46a" />
              <stop offset="100%" stop-color="#8a6a2e" />
            </radialGradient>
            <!-- 星核高光：偏左上的一团白光，让核面看起来像个球而不是一块贴纸 -->
            <radialGradient id="coreHi">
              <stop offset="0%" stop-color="#fff6e0" stop-opacity="0.5" />
              <stop offset="100%" stop-color="#fff6e0" stop-opacity="0" />
            </radialGradient>
            <filter id="sunBlur"><feGaussianBlur :stdDeviation="SUN_R * 0.15" /></filter>
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
              :class="{ hot: activeId === n.id || hoverId === n.id }"
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

            <!-- 星核：原帖。整盘的锚点。
                 曾经试过「放射光芒的太阳」——用户反馈形象不符合（太阳=发光天体，
                 但这里的中心是「被验证过的起点」，不是光源），已整体撤掉。
                 现在按 5 层画，每层都带信息，不是纯装饰：
                   ① 核晕  冷色柔光，把星核从白底里「托」出来
                   ② 星球环  倾斜细环，后半藏在核体后面、前半压在核面前 —— 星核不是靶心，是颗星球
                   ③ 核辉  内层蓝白光晕
                   ④ 进度环  外圈那道蓝弧 = 已做成占比（0 颗做成时只留一条浅色刻度环）
                   ⑤ 核体  渐变圆面 + 偏左上高光，像个球
                 环/晕都在 vp 组里，跟着 scale(k) 一起缩放，比例永远和轨道一致。 -->
            <g class="sun">
              <circle class="sun-halo" :cx="CX" :cy="CY" :r="(SUN_R * 1.95).toFixed(1)" fill="url(#sunHalo)" />
              <circle class="sun-glow" :cx="CX" :cy="CY" :r="(SUN_R * 1.22).toFixed(1)" fill="url(#sunGrad)" filter="url(#sunBlur)" />
              <!-- 星球环 · 后半：先画，让核体压住它的中段，只露出左右两翼 -->
              <g class="sun-ring back" :transform="`translate(${CX} ${CY}) rotate(-16)`">
                <path :d="SUN_RING.back" fill="none" stroke="#3d4a78" :stroke-width="SUN_RING.w" opacity="0.75" />
              </g>
              <circle class="varbg" :cx="CX" :cy="CY" :r="SUN_R" fill="none" stroke="#1c2442" stroke-width="3" />
              <circle
                class="varc"
                :cx="CX"
                :cy="CY"
                :r="SUN_R"
                fill="none"
                :stroke="STAR_ON"
                stroke-width="3"
                stroke-linecap="round"
                :transform="`rotate(-90 ${CX} ${CY})`"
                :stroke-dasharray="`${SUN_ARC.len.toFixed(1)} ${(SUN_ARC.c - SUN_ARC.len).toFixed(1)}`"
                :opacity="SUN_ARC.len > 0.6 ? 1 : 0"
              />
              <circle class="corec" :cx="CX" :cy="CY" :r="(SUN_R * 0.83).toFixed(1)" fill="url(#coreGrad)" stroke="#6b5424" stroke-width="1" />
              <circle
                class="core-hi"
                :cx="(CX - SUN_R * 0.3).toFixed(1)"
                :cy="(CY - SUN_R * 0.36).toFixed(1)"
                :r="(SUN_R * 0.52).toFixed(1)"
                fill="url(#coreHi)"
              />
              <!-- 星球环 · 前半：压在核面前面（从左下掠到右下），Saturn 感的来源 -->
              <g class="sun-ring front" :transform="`translate(${CX} ${CY}) rotate(-16)`">
                <path :d="SUN_RING.front" fill="none" stroke="#8a97d8" :stroke-width="SUN_RING.w" opacity="0.9" />
              </g>
              <g :transform="`translate(${CX} ${CY}) scale(${inv})`">
                <!-- 标题不再塞进星核；顶部 chips 与右侧面板已展示完整标题 -->
                <text
                  v-if="CORE_FS.compact"
                  class="core-num"
                  x="0"
                  y="0"
                  :style="{ fontSize: CORE_FS.num + 'px' }"
                  text-anchor="middle"
                >★ {{ nodes.length }}</text>
                <template v-else>
                  <text class="core-sub" x="0" :y="(-SUN_R * 0.24).toFixed(1)" :style="{ fontSize: CORE_FS.sub + 'px' }" text-anchor="middle">原帖 · 基准处境</text>
                  <text class="core-num" x="0" y="0" :style="{ fontSize: CORE_FS.num + 'px' }" text-anchor="middle">已收录处境 ★ {{ nodes.length }}</text>
                  <text class="core-hint" x="0" :y="(SUN_R * 0.34).toFixed(1)" :style="{ fontSize: CORE_FS.hint + 'px' }" text-anchor="middle">点击查看原帖拆解</text>
                </template>
              </g>
            </g>
            <circle
              class="corehit"
              :cx="CX"
              :cy="CY"
              :r="(SUN_R * 1.06).toFixed(1)"
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
              :class="{ on: activeId === n.id, draft: n.id === DRAFT_ID, hov: hoverId === n.id }"
              :style="{ '--i': n.idx }"
              :data-id="n.id"
              @mouseenter="hoverId = n.id"
              @mouseleave="hoverId = null"
            >
              <g :transform="wrapT(n)">
                <g class="pop" :style="{ '--s': popScale(n) }">
                  <circle class="nhit" :r="STAR_SZ * 1.8" fill="transparent" />
                  <path
                    class="star"
                    :class="{ on: n.verified, tw: !n.verified }"
                    :d="starPath(STAR_SZ, STAR_SZ * 0.42)"
                    :fill="n.verified ? STAR_ON : '#ffffff'"
                    :stroke="n.verified ? STAR_ON : STAR_OFF"
                    :stroke-width="n.verified ? 0 : 1.8"
                  />
                </g>
                <text
                  v-if="n.lbl.show || hoverId === n.id || activeId === n.id"
                  class="lbl"
                  :transform="lblT(n)"
                  :text-anchor="n.anchor"
                  dominant-baseline="central"
                >
                  {{ n.lbl.text || starLabel(n) }}
                </text>
                <text
                  v-if="n.lbl.detail && (n.lbl.show || hoverId === n.id || activeId === n.id)"
                  class="node-detail"
                  :transform="detT(n)"
                  :text-anchor="n.anchor"
                  dominant-baseline="central"
                >
                  {{ n.verified ? '已做成' : '还在试' }} · {{ n.peers }}人相似
                </text>
              </g>
            </g>
          </g>
        </svg>

        <!-- 图例：一眼看懂这张图怎么读（长段说明在右侧面板里） -->
        <div class="legend">
          <div class="lg-line">
            <span class="lg sun"><i></i>原帖 · 星核<em>外圈蓝弧＝已做成比例</em></span>
          </div>
          <div class="lg-line">
            <span class="lg ok"><i></i>已做成</span>
            <span class="lg off"><i></i>还在试</span>
          </div>
          <div class="lg-line depth">
            由内到外<em>›</em><b>改参数</b><em>›</em><b>动结构</b><em>›</em><b>换方案</b>
          </div>
        </div>

        <div class="hintbar">滚轮缩放 · 拖拽平移 · 点星看这一版改了什么 · 点星核看原帖拆解</div>

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

        <!-- A1 · 原帖拆解（总览 / 星核） -->
        <template v-else-if="view === 'overview' || view === 'origin'">
          <div class="kicker">{{ view === 'origin' ? '原帖 · 基准处境（星核）' : 'A1 · 原帖拆解' }}</div>
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
            <div class="sec">这颗星核的价值</div>
            <p class="hint">
              它已经被迁移成 <b>{{ nodes.length }}</b> 个真实处境，其中 <b>{{ verifiedCount }}</b> 个做成了。<br />
              每做成一个，原帖价值 +1 —— 它解决的不再只是作者一个人。
            </p>
          </template>

          <template v-else>
            <div class="sec">这张星图怎么读</div>
            <p class="hint">
              正中那颗<b>星核是原帖</b>——绕着它的<b>细环</b>是它的引力圈，外圈那道<b>蓝色弧线＝已经被做成的比例</b>（全蓝就是全做成了）。<br />
              外圈每颗<b>星是一个真实处境</b>：<b>实心蓝星</b>＝做成了，<b>空心橙星</b>＝还在试。<br />
              星离星核的<b>远近</b>（三层轨道环）＝照搬要改多深：<b>改参数</b> → <b>动结构</b> → <b>换方案</b>。<br />
              <b>橙色虚线</b>＝走不通之后换思路重炼的下一版。<br /><br />
              点一颗星，看这一版针对他的处境改了什么；卡住了可以直接<b>复诊</b>，AI 会换一条没走过的路再来一版。
            </p>

            <!-- 入口前置的另一半：不想先点星、只想直奔「某一步怎么落地」的人走这里。
                 可视化入口不能只存在于某颗星星的详情页里。 -->
            <div class="sec">直接进某个处境的解决步骤星图</div>
            <div class="entry-chips">
              <router-link
                v-for="n in nodes"
                :key="'ec' + n.id"
                class="entry-chip"
                :to="{ name: 'steps', params: { sceneId: n.id }, query: { step: 1, from: currentPost.id } }"
              >
                <i class="ec-dot" :class="{ v: n.verified }" />
                <span>{{ starLabel(n) }}</span>
                <em>→</em>
              </router-link>
            </div>
            <p class="hint sub-hint">每颗星下面都有一张「这几步到底怎么落地」的星图，点名字直接进。</p>

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

          <!-- ★ 可视化入口前置 ---------------------------------------------------
               原来这条入口埋在面板最底部的「⑤ 继续拆解」里，要滚到最后才看得见。
               它是「处境 → 解决步骤」的下一层入口，属于主路径，所以提到标题正下方，
               做成整条可点的入口条（不是个小按钮）：一眼看到、随手点进去。-->
          <router-link
            v-if="active.id && active.id !== DRAFT_ID"
            class="entry-bar"
            :to="{ name: 'steps', params: { sceneId: active.id }, query: { step: 1, from: currentPost.id } }"
          >
            <span class="eb-ico" aria-hidden="true">✦</span>
            <span class="eb-tx">
              <b>查看这一步怎么落地 · 解决步骤星图</b>
              <em>把这套改法拆成 {{ active.moves.length }} 步，一步一颗星</em>
            </span>
            <span class="eb-go">进入 →</span>
          </router-link>

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
import { computed, nextTick, onMounted, onUnmounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { getStarMap, runAdapt, submitFeedback } from '../api'
import AdaptBench from './AdaptBench.vue'
import { LAYOUT_DEFAULTS, bboxAt, buildDraftNode, buildLayout, starLabel, starPath } from './starmapLayout'

/* ---------------- 常量 ---------------- */
const STAR_ON = '#43c6a6'
const STAR_OFF = '#dbb46a'
const DEPTH_GROUPS = [
  [1, '改参数'],
  [2, '动结构'],
  [3, '换方案']
]
const DRAFT_ID = 'draft'

/* ---------------- 舞台坐标系：1 单位 ≈ 1 像素（随容器自适应） ----------------
   旧版把整盘画死在 900×790 里，再被容器缩放一次，字号被「双重缩小」到约 7px 才导致看不清。
   现在 viewBox 直接跟随舞台像素尺寸：字号 = 真实像素，整体缩放只由 fitView 的 k 决定。
   整盘的尺寸推导（轨道半径 / 压扁系数 / 星核与星的大小 / 标签占位）都在 starmapLayout.js，
   那里是纯函数，能用真实数据直接跑几何断言。*/
const stageEl = ref(null)
const vbW = ref(880)
const vbH = ref(680)
const CX = computed(() => vbW.value / 2)
const CY = computed(() => vbH.value / 2)

const layout = computed(() =>
  buildLayout({
    scenes: (currentPost.value && currentPost.value.scenes) || [],
    vbW: vbW.value,
    vbH: vbH.value
  })
)
const RING = computed(() => layout.value.ring)
const rings = computed(() => layout.value.rings)
const SQUASH = computed(() => layout.value.squash)
const SUN_R = computed(() => layout.value.sunR)
const STAR_SZ = computed(() => layout.value.starSz)
const CORE_FS = computed(() => layout.value.coreFs)
const nodes = computed(() => layout.value.nodes)
const viewBox = computed(() => `0 0 ${vbW.value} ${vbH.value}`)

/* ---------------- 星核的构件 ----------------
   星球环： rx=1.45R、ry=0.5R、整体倾斜 -16°，分前后两半 ——
   后半先画（被核体压住中段，只露两翼），前半后画（掠过核面下缘）。
   为什么放在计算属性里、而不是 onMounted 手搓 DOM：
   直径完全由 SUN_R 决定，舞台一变 SUN_R 就变 —— 声明式生成能跟着自动重算，
   而且这些是模板元素，scoped 样式照常生效（手搓的拿不到 data-v，是另一个坑）。
   注意：环的本地 path 画在 (0,0) 基准上，靠父 <g> 的 translate+rotate 定位 ——
   这跟「rotate(a CX CY) 转本地 path」是两回事，后者会绕 (CX,CY) 远处转飞（踩过）。*/
const SUN_RING = computed(() => {
  const R = SUN_R.value
  const rx = R * 1.45
  const ry = R * 0.5
  const f = (n) => n.toFixed(1)
  return {
    back: `M ${f(-rx)} 0 A ${f(rx)} ${f(ry)} 0 0 1 ${f(rx)} 0`,
    front: `M ${f(-rx)} 0 A ${f(rx)} ${f(ry)} 0 0 0 ${f(rx)} 0`,
    w: Math.max(1.4, R * 0.045).toFixed(1)
  }
})

/* 进度环：弧长 = 已做成占比。
   这道弧不是装饰 —— 它把「这颗原帖被消化了多少」直接画在星核上：
   全蓝＝全部做成了，只剩一小段＝刚开张。一颗都没做成时整环隐掉，只留浅灰刻度环。*/
const SUN_ARC = computed(() => {
  const c = 2 * Math.PI * SUN_R.value
  const ratio = nodes.value.length ? verifiedCount.value / nodes.value.length : 0
  return { c, len: c * Math.max(0, Math.min(1, ratio)) }
})

function measureStage() {
  const el = stageEl.value
  if (!el) return
  /* 用 clientWidth/Height 而不是 getBoundingClientRect()：
     后者含 1px 边框，会让 viewBox 比 SVG 真实绘制区大 2px ——
     整盘被多缩 0.2%、还整体偏 1px。viewBox 的单位必须跟 SVG 自己的内容盒对齐，
     才能保证「1 单位 = 1px、字号就是真实像素」。 */
  const w = el.clientWidth
  const h = el.clientHeight
  if (w < 80 || h < 80) return
  vbW.value = w
  vbH.value = h
}
let stageRO = null

/* ---------------- 数据 ---------------- */
const route = useRoute()
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
    /* 从步骤星图「返回上一级」回来时会带 ?post=<id>：
       直接落回刚才那篇帖，而不是被打回第一帖 —— 返回上一级应该回原地。 */
    const want = Number(route.query.post)
    const idx = Number.isFinite(want) && want > 0 ? posts.value.findIndex((p) => p.id === want) : -1
    if (idx >= 0) curIdx.value = idx
    else if (curIdx.value >= posts.value.length) curIdx.value = 0
  } catch (e) {
    posts.value = []
  } finally {
    loading.value = false
    await nextTick()
    fitView(false)
    playEnter()
  }
}
onMounted(async () => {
  measureStage()
  await load()
  if (stageEl.value && typeof ResizeObserver !== 'undefined') {
    stageRO = new ResizeObserver(() => {
      measureStage()
      fitView(false)
    })
    stageRO.observe(stageEl.value)
  }
})
onUnmounted(() => stageRO && stageRO.disconnect())

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

/* ---------------- 布局：倾斜星盘 ----------------
   摆位算法（分扇区 → 按 depth 铺开 → 角度松弛 → 标签朝哪一侧）全部搬到
   starmapLayout.js，这里只做数据接线。*/

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
const draftNode = computed(() => {
  if (view.value !== 'create') return null
  if (!currentPost.value) return null
  return buildDraftNode(layout.value, nodes.value, 2)
})
const allNodes = computed(() => {
  const d = draftNode.value
  return d ? [...nodes.value, d] : nodes.value
})

const verifiedCount = computed(() => nodes.value.filter((n) => n.verified).length)
const sunTitle = computed(() => {
  const t = currentPost.value ? currentPost.value.title : ''
  return t.split(/[：:]/)[0].slice(0, 14)
})
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
const detT = (n) => `translate(${n.dx.toFixed(1)} ${(n.dy + LAYOUT_DEFAULTS.labelDetailOff).toFixed(1)}) scale(${inv.value.toFixed(3)})`

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
  const c = { x: (CX.value - tx.value) / k.value, y: (CY.value - ty.value) / k.value }
  const nk = clamp(k.value * f)
  animateTo(nk, CX.value - c.x * nk, CY.value - c.y * nk, 300)
}
function fitView(anim = true) {
  const L = layout.value
  if (!L.nodes.length) {
    if (anim) animateTo(1, 0, 0, 300)
    return
  }
  const nk = L.k
  /* ⚠️⚠️ bboxAt() 返回的**已经是乘过 k 的屏幕坐标**（内部就是 n.x * k）。
     旧版在这里又 `* nk` 了一次，等于把整盘平移了 cx·k·(1-k)：
       9 星帖 k=1.14 → 偏 (-65,-53)px；单星帖 k=1.70 → 偏 (-524,-541)px。
     症状就是用户报的「点空白复位之后，左边的字被切掉/看不见」——
     盘面被推到舞台左上方，最左那几条标签直接落在画布外。
     正确写法：屏幕中心 = bbox 中心（已含 k），平移量就是「舞台中心 - 它」。 */
  const bb = bboxAt(L.nodes, L.starSz, nk)
  /* 取景框把星核一起圈进来：星核也在 vp 组里吃 scale(k)，小盘面时它的星球环
     （横向伸到 1.45R）可能比星点还靠外（它不在 bboxAt 里）。0 颗星时也靠这个把星核放进画面。*/
  const halo = L.sunR * nk * 1.5
  const minX = Math.min(bb.minX, L.cx * nk - halo)
  const maxX = Math.max(bb.maxX, L.cx * nk + halo)
  const minY = Math.min(bb.minY, L.cy * nk - halo)
  const maxY = Math.max(bb.maxY, L.cy * nk + halo)
  const ntx = CX.value - (minX + maxX) / 2
  const nty = CY.value - (minY + maxY) / 2
  if (anim) animateTo(nk, ntx, nty, 480)
  else {
    k.value = nk
    tx.value = ntx
    ty.value = nty
  }
}
function focusNode(n, z = 2.5) {
  const nk = clamp(z)
  animateTo(nk, CX.value - n.x * nk, CY.value - n.y * nk, 480)
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
  height: calc(100vh - 250px);
  min-height: 540px;
  background: radial-gradient(130% 96% at 50% 45%, #131a33 0%, #0e1428 55%, #0b1020 100%);
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
  stroke: #2a3358;
  stroke-width: 1.1;
  opacity: 0.9;
  stroke-dasharray: 2 6;
  transition: opacity 0.18s ease;
}
.ray {
  fill: none;
  stroke-width: 1.2;
  opacity: 0.5;
  transition: opacity 0.18s ease;
}
.ray.hot {
  opacity: 1;
  stroke-width: 2;
}
.xlink {
  stroke: #2a3358;
  stroke-width: 1;
  opacity: 0.55;
  stroke-dasharray: 4 4;
  transition: opacity 0.18s ease;
}
.xlink.parent {
  stroke: #dbb46a;
  stroke-width: 1.4;
  opacity: 0.9;
  stroke-dasharray: 5 4;
}
.node {
  cursor: pointer;
  transition: opacity 0.18s ease;
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
  filter: drop-shadow(0 1px 3px rgba(125, 137, 255, 0.4));
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
  fill: #131a33;
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
  font-size: 14px;
  font-weight: 600;
  fill: #f4f6fa;
  paint-order: stroke;
  stroke: #0b1020;
  stroke-width: 5.5;
  stroke-linejoin: round;
  transition: font-size 0.2s;
}
.node.on .lbl {
  font-size: 15.5px;
  fill: var(--zh-blue);
}
.node.hov .lbl {
  fill: var(--zh-blue);
}
.node-detail {
  font-size: 11.5px;
  fill: #9aa5c4;
  paint-order: stroke;
  stroke: #0b1020;
  stroke-width: 5;
  stroke-linejoin: round;
}
.core-sub {
  font-size: 18px;
  font-weight: 600;
  fill: #4a3a14;
}
.core-num {
  font-size: 15px;
  fill: var(--zh-blue);
  font-weight: 600;
}
.core-hint {
  font-size: 12px;
  fill: #6b5424;
}
.corehit {
  cursor: pointer;
}

/* ---- 星核（冷色星球形象）：核晕 / 星球环 / 核体高光 ----
   这些都是模板元素（属性绑定），scoped 能给它们加上 data-v，规则生效。*/
.sun-halo {
  animation: haloPulse 7s ease-in-out infinite;
}
@keyframes haloPulse {
  0%,
  100% {
    opacity: 0.8;
  }
  50% {
    opacity: 1;
  }
}
/* 核体高光：偏左上的一团白，让核面有球感 —— 但它压在三行字下面，
   pointer-events 关掉，别抢走 corehit 的点击。*/
.core-hi {
  pointer-events: none;
}

/* ---- 可视化入口前置（④） ---- */
.entry-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 10px 0 12px;
  padding: 10px 12px;
  border: 1px solid var(--zh-blue-line-strong);
  background: var(--zh-blue-soft);
  border-radius: 8px;
  text-decoration: none;
  transition: 0.18s;
}
.entry-bar:hover {
  background: #d8e8fd;
  border-color: var(--zh-blue);
  transform: translateY(-1px);
  box-shadow: 0 4px 14px rgba(125, 137, 255, 0.14);
}
.eb-ico {
  width: 26px;
  height: 26px;
  flex: none;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background: var(--surface-2);
  color: var(--zh-blue-2);
  font-size: 13px;
  box-shadow: 0 1px 4px rgba(125, 137, 255, 0.18);
}
.eb-tx {
  min-width: 0;
  flex: 1;
}
.eb-tx b {
  display: block;
  font-size: 13.5px;
  color: var(--zh-blue);
  font-weight: 600;
}
.eb-tx em {
  display: block;
  font-style: normal;
  font-size: 11.5px;
  color: var(--text-3);
  margin-top: 2px;
}
.eb-go {
  flex: none;
  font-size: 12.5px;
  color: var(--zh-blue);
  font-weight: 500;
}
.entry-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.entry-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  max-width: 100%;
  padding: 5px 10px;
  border: 1px solid var(--border);
  border-radius: 999px;
  background: var(--bg-2);
  color: var(--text-2);
  font-size: 12px;
  text-decoration: none;
  transition: 0.16s;
}
.entry-chip span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.entry-chip em {
  font-style: normal;
  color: var(--zh-blue);
  font-size: 11px;
}
.entry-chip:hover {
  color: var(--zh-blue);
  border-color: var(--zh-blue-line-strong);
  background: var(--zh-blue-soft);
}
.ec-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  flex: none;
  background: var(--surface-2);
  border: 1.6px solid #dbb46a;
}
.ec-dot.v {
  background: var(--zh-blue);
  border-color: var(--zh-blue);
}
.sub-hint {
  font-size: 12px;
  margin-top: 8px;
}

/* 装饰动效的降级：系统开了「减少动态效果」就全部停下。
   注意这里只是把 animation 关掉 —— 元素本身的透明度/颜色都在静态样式里，关了也看得见。*/
@media (prefers-reduced-motion: reduce) {
  .sun-halo {
    animation: none;
  }
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

/* 悬停聚焦：指到哪颗星，其余先退到背景里，这一颗的名字和状态立刻能看清 */
.web.hovering .node:not(.hov):not(.on) {
  opacity: 0.42;
}
.web.hovering .ray:not(.hot) {
  opacity: 0.12;
}
.web.hovering .orbit {
  opacity: 0.32;
}
.web.hovering .xlink:not(.parent) {
  opacity: 0.1;
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
.legend {
  position: absolute;
  left: 14px;
  top: 12px;
  display: flex;
  flex-direction: column;
  gap: 7px;
  padding: 10px 12px;
  background: rgba(17, 23, 44, 0.88);
  border: 1px solid var(--border);
  border-radius: 8px;
  pointer-events: none;
  line-height: 1;
}
.lg-line {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 11.5px;
  color: var(--text-3);
}
.lg {
  display: inline-flex;
  align-items: center;
  gap: 5px;
}
.lg i {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  flex: none;
}
.lg.sun i {
  background: radial-gradient(circle at 34% 30%, #f0d9a8, #dbb46a);
  box-shadow: 0 0 5px rgba(240, 180, 92, 0.65);
}
.lg.sun em {
  font-style: normal;
  font-size: 10.5px;
  color: #a8b1c0;
  margin-left: 4px;
}
.lg.ok i {
  background: var(--zh-blue);
}
.lg.off i {
  background: var(--surface-2);
  border: 1.6px solid #dbb46a;
}
.lg-line.depth {
  gap: 0;
  white-space: nowrap;
}
.lg-line.depth b {
  font-weight: 500;
  color: var(--text-2);
  margin-left: 4px;
}
.lg-line.depth em {
  font-style: normal;
  font-size: 10px;
  color: #c9cfd9;
  margin-left: 4px;
}
.hintbar {
  position: absolute;
  left: 50%;
  bottom: 12px;
  transform: translateX(-50%);
  font-size: 11.5px;
  color: var(--text-3);
  line-height: 1;
  white-space: nowrap;
  background: rgba(17, 23, 44, 0.86);
  border: 1px solid var(--border);
  border-radius: 999px;
  padding: 7px 14px;
  pointer-events: none;
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
  background: var(--surface);
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
  background: var(--surface-2);
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
  box-shadow: 0 6px 20px rgba(125, 137, 255, 0.25);
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
  /* 小屏：图例只留「原帖 / 已做成 / 还在试」，轨道说明交给右侧面板 */
  .legend {
    padding: 7px 9px;
    gap: 5px;
  }
  .lg-line.depth {
    display: none;
  }
  .sm-actions {
    margin-left: 0;
  }
}

/* ===== 小屏（手机）===== */
@media (max-width: 480px) {
  .stage {
    height: 48vh;
    min-height: 320px;
  }
  .legend {
    font-size: 11px;
    padding: 6px 8px;
    gap: 4px;
  }
  .panel {
    padding: 12px;
  }
}
</style>
