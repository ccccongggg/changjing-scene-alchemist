<template>
<div id="studentStepsApp" class="app">
    <header class="sm-head">
      <!-- 返回上一级：本页是星图里「某颗星」的下一层，所以要能回得去。
           不能只靠浏览器的后退键 —— 从分享链接直接进来时它会把用户弹出站外。 -->
      <button class="btn back-up" id="btnUp" @click="goUp">← 返回上一级</button>
      <div class="sm-headline">
        <h1 class="sm-title">学生版 AI 学习法 · 五步星图</h1>
        <span class="sm-sub">把作者的「随便试」炼成学生的「20 次额度」</span>
      </div>
      <div class="sm-chips" id="chips"></div>
      <div class="sm-actions">
        <button class="btn ghost" id="btnOrigin"><b>场景拆解</b></button>
      </div>
    </header>

    <section class="sm-body">
      <div class="stage">
        <!-- viewBox 由 JS 按舞台像素尺寸设置（1 单位 ≈ 1px）；写死会被容器缩放，字号跟着缩没 -->
        <svg class="web" id="svg" preserveAspectRatio="xMidYMid meet">
          <defs>
            <!-- 核晕：最外那层冷色柔光，边缘必须透明，否则白底上看到的是一个脏圆盘 -->
            <radialGradient id="sunHalo">
              <stop offset="0%" stop-color="#cfe3ff" stop-opacity="0.5" />
              <stop offset="45%" stop-color="#e3eefc" stop-opacity="0.22" />
              <stop offset="100%" stop-color="#eef4fd" stop-opacity="0" />
            </radialGradient>
            <radialGradient id="sunGrad">
              <stop offset="0%" stop-color="#e7f1fd" />
              <stop offset="62%" stop-color="#f2f7fd" />
              <stop offset="100%" stop-color="#fbfcfd" stop-opacity="0.2" />
            </radialGradient>
            <radialGradient id="coreGrad">
              <stop offset="0%" stop-color="#f6faff" />
              <stop offset="58%" stop-color="#ecf3fc" />
              <stop offset="100%" stop-color="#d9e7f8" />
            </radialGradient>
            <!-- 核体高光：偏左上的一团白光，让核面像个球而不是一块贴纸 -->
            <radialGradient id="coreHi">
              <stop offset="0%" stop-color="#ffffff" stop-opacity="0.92" />
              <stop offset="100%" stop-color="#ffffff" stop-opacity="0" />
            </radialGradient>
            <filter id="sunBlur"><feGaussianBlur stdDeviation="10" /></filter>
          </defs>
          <g id="vp">
            <g id="orbits"></g>
            <g id="rays"></g>
            <!-- 星核 = 当前应用场景（⑤）。
                 旧版这里是「原帖 · 基准处境」——那一版的中心指的是原帖，可是这页要回答的
                 是「**这个场景**该怎么落地」，所以中心必须是场景本身，周围的星才是解决步骤。
                 画法与 /starmap 的星核保持一致：核晕 → 环(后半) → 核辉 → 刻度环 → 进度弧 → 核体 → 环(前半)。
                 进度弧是满圈：这一页的每一步都是「已炼成」的方法。
                 曾经试过「放射光芒的太阳」，用户反馈形象不符合，已整体撤掉（见 /starmap 同款注释）。 -->
            <g class="sun">
              <circle id="sunHalo" class="sun-halo" cx="440" cy="400" r="136" fill="url(#sunHalo)" />
              <circle id="sunGlow" class="sun-glow" cx="440" cy="400" r="86" fill="url(#sunGrad)" filter="url(#sunBlur)" />
              <!-- 星球环 · 后半：先画，让核体压住它的中段，只露左右两翼 -->
              <g id="sunRingBack" transform="translate(440 400) rotate(-16)">
                <path d="" fill="none" stroke="#c9d9ee" stroke-width="3" opacity="0.75" />
              </g>
              <circle id="sunRing" cx="440" cy="400" r="70" fill="none" stroke="#e9f0fa" stroke-width="3" />
              <circle id="sunArc" class="varc" cx="440" cy="400" r="70" fill="none" stroke="#056de8" stroke-width="3" stroke-linecap="round" transform="rotate(-90 440 400)" />
              <circle id="sunCore" class="corec" cx="440" cy="400" r="58" fill="url(#coreGrad)" stroke="#dfe9f7" stroke-width="1" />
              <circle id="sunHi" class="core-hi" cx="419" cy="375" r="36" fill="url(#coreHi)" />
              <!-- 星球环 · 前半：压在核面前面（从左下掠到右下），Saturn 感的来源 -->
              <g id="sunRingFront" transform="translate(440 400) rotate(-16)">
                <path d="" fill="none" stroke="#a9c2e6" stroke-width="3" opacity="0.9" />
              </g>
              <g id="coreText" transform="translate(440 400)">
                <text id="coreSub" class="core-sub" x="0" y="-8" text-anchor="middle" dominant-baseline="central">应用场景</text>
                <text id="coreNum" class="core-num" x="0" y="16" text-anchor="middle" dominant-baseline="central">★ 5 步</text>
                <text id="coreHint" class="core-hint" x="0" y="36" text-anchor="middle" dominant-baseline="central">点击看这个场景</text>
              </g>
            </g>
            <circle id="coreHit" class="corehit" cx="440" cy="400" r="74" fill="transparent"></circle>
            <g id="nodes"></g>
          </g>
        </svg>

        <!-- 图例：一眼看懂这张图怎么读（长段说明在右侧面板里） -->
        <div class="legend">
          <div class="lg-line">
            <span class="lg sun"><i></i>应用场景 · 星核</span>
          </div>
          <div class="lg-line">
            <span class="lg ok"><i></i>解决步骤 · 星</span>
          </div>
          <div class="lg-line depth">
            从最上面那颗起<em>›</em><b>顺时针</b><em>›</em><b>一步一颗</b>
          </div>
        </div>

        <div class="hintbar">滚轮缩放 · 拖拽平移 · 点星看这一步怎么炼 · 点星核看当前场景</div>
        <div class="zoomtag" id="zoomtag">总览 · <b>1.0x</b></div>
        <div class="zoombar">
          <button title="放大" id="zoomIn">＋</button>
          <button title="缩小" id="zoomOut">−</button>
          <button class="sm" title="复位" id="btnReset">复位</button>
        </div>
      </div>

      <aside class="panel" id="panel"></aside>
    </section>
  </div>
</template>

<script setup>
import { onMounted, onUnmounted } from "vue"
import { useRoute, useRouter } from 'vue-router'
import { getAdaptation } from '../api'
import { buildLayout, bboxAt, starPath } from './starmapLayout'

const props = defineProps(['sceneId'])

/* ---- 返回上一级（⑥）----
   上一级是 /starmap（星辰图）。星图那边的入口带了 ?from=<postId>，
   回来时把它带回去，用户落回的是原来那篇帖，而不是被打回第一帖。 */
const route = useRoute()
const router = useRouter()
function goUp() {
  const from = Number(route.query.from)
  if (Number.isFinite(from) && from > 0) router.push({ name: 'starmap', query: { post: String(from) } })
  else router.push({ name: 'starmap' })
}

/* 舞台尺寸监听器要在 setup 顶层登记清理函数：
   onUnmounted() 依赖「当前组件实例」，而 onMounted 的 async 回调跑起来时实例上下文已经没了，
   在里面注册会被 Vue 忽略（且不会真的卸载，等于一直在观察一个已经不存在的 DOM）。 */
let stageRO = null
onUnmounted(() => { if (stageRO) stageRO.disconnect() })

onMounted(async () => {
  /* ---------------- 常量 ----------------
     几何（viewBox / 轨道半径 / 压扁系数 / 星核与星的大小 / 标签占位）全部来自共享模块
     starmapLayout.js，按舞台像素实时推 —— 1 单位 ≈ 1px，字号就等于真实像素。
     旧版把整盘画死在 viewBox="0 0 900 790" 里，会被容器缩一次、fitView 再缩一次；
     而标签是恒定屏幕字号（只吃外层缩放），12.5px 实测只剩 5px，这才是「看不清字」的根因。 */
  const STAR_ON = '#056de8', STAR_OFF = '#f0a03c';
  const KMIN = 0.45, KMAX = 4;
  const DEPTH_NAME = { 1: '改参数', 2: '动结构', 3: '换方案' };

  let LAY = null;                                        // 最近一次布局结果
  let hoverId = null;                                    // 悬停聚焦用
  let CX = 440, CY = 400, SQUASH = 0.46, RING = { 1: 198, 2: 280, 3: 362 };  // 由 relayout() 覆盖

  /* 用 clientWidth/Height 而不是 getBoundingClientRect()：
     后者含 1px 边框，会让 viewBox 比 SVG 真实绘制区大 2px（整盘被多缩 0.2%）。
     viewBox 的单位要跟 SVG 自己的内容盒对齐，才能保证「1 单位 = 1px、字号就是真实像素」。 */
  function measureStage() {
    const box = document.querySelector('#studentStepsApp .stage');
    if (!box) return { w: 880, h: 620 };
    return {
      w: box.clientWidth > 80 ? box.clientWidth : 880,
      h: box.clientHeight > 80 ? box.clientHeight : 620
    };
  }
  
      /* ---------------- 数据加载 ---------------- */
      let SCENARIO = null;
      let steps = [];

      function buildDemoData() {
        const SCENARIO = {
          title: '学生版 AI 学习法 · 五步星图',
          /* sceneName 是给星核中心用的「场景名」：星核代表的是**当前应用场景**，
             不是原帖（⑤）。页面标题可以是长句，星核里塞不下长句，所以单独给一个短名。 */
          sceneName: '学生版 · 20 次',
          sub: '把作者的「随便试」炼成学生的「20 次额度」',
          origin: {
            scene: '作者：付费会员、电脑随便装软件、时间大把，可以无限次试错调 AI。',
            solution: '核心打法是「把 AI 当协作者」：先把要什么说清，再让它只做你不会改的那一步，最后自己过一遍。',
            constraints: ['付费会员 · 不限次', '可自由装插件/软件', '时间充裕、反复试错'],
            params: { '身份': '付费会员', '额度': '不限', '工具': '桌面端 + 插件', '容错': '高（可重来）' },
            boundaries: '这套打法建立在「可以反复试」之上；一旦额度被卡死，原样照搬就会处处碰壁——所以学生要的不是照搬，是重炼。'
          }
        };
        const steps = [
          {
            id: 1, title: '使用额度', depth: 1,
            sit: '学生每天只有 20 次免费额度，和作者「随便试」完全不是一个量级；不先预算就会前松后紧、关键时刻没次数。',
            diffs: [{ dimension: '额度', origin: '不限次', mine: '20 次/天', impact: '必须先把次数分配到具体用途' }],
            moves: [{ step: 1, title: '先预算再使用', action: '每天 20 次 = 3 次改论文 + 2 次备考 + 5 次讲错题，剩下 10 次留着应急。' }],
            learned: '额度是你最硬的约束，必须先预算再使用——它不是「省着用」，是「计划着用」。'
          },
          {
            id: 2, title: '试错成本', depth: 2,
            sit: '作者可以第二轮补需求，学生补一次就少一次；提问结构必须一次成型，不能靠来回聊。',
            diffs: [{ dimension: '试错机会', origin: '可多轮补', mine: '一轮定生死', impact: '需求要在第一轮说全' }],
            moves: [{ step: 1, title: '一次成型模板', action: '字数、语气、格式、禁用词，全部在第一轮 prompt 里写完，别指望第二轮补。' }],
            learned: '一次说全是最省次数的用法；结构不改，光靠多聊是在浪费额度。'
          },
          {
            id: 3, title: '产出要求', depth: 2,
            sit: '学生怕 AI 写出来的东西不像自己、也怕过不了查重；不能把整段交给它代写。',
            diffs: [{ dimension: '代写粒度', origin: '可整段生成', mine: '只改不会动的那步', impact: '保留自己的表达习惯' }],
            moves: [{ step: 1, title: '只让它做你不会改的那一步', action: '比如「这段逻辑通不通」「能不能更简洁」，而不是把整段交给它重写。' }],
            learned: '改比写更容易保住你的表达习惯，也更容易过查重——你还是作者。'
          },
          {
            id: 4, title: '产出要求', depth: 3,
            sit: '作者产出即用，学生产出的东西要算「自己的」；不收尾就会变成 AI 的作业。',
            diffs: [{ dimension: '收尾', origin: '产出即用', mine: '必改一遍', impact: '决定东西算不算你的' }],
            moves: [{ step: 1, title: '产出后必改一遍', action: '把长句拆短、删掉它的口头禅（首先/其次/总而言之）、补一句你自己的判断。' }],
            learned: '这一步不能省，它决定了这篇东西算不算你的——否则只是把 AI 的话抄了一遍。'
          },
          {
            id: 5, title: '用途', depth: 3,
            sit: '作者用 AI 提效，学生真正的杠杆在「讲题」——把错题炼成理解，比改作文值钱得多。',
            diffs: [{ dimension: '最有价值的用法', origin: '改稿提效', mine: '讲错题', impact: '5 次额度留给「我错在哪」' }],
            moves: [{ step: 1, title: '讲错题最值', action: '把题目 + 你写的解法一起给它，只要它讲「我错在哪一步」，不要答案。' }],
            learned: '这才是 AI 在学习场景里真正的杠杆点，比改作文值钱——它教的是「你为什么错」。'
          }
        ];
        return { SCENARIO, steps };
      }

      function buildFromAdaptation(a) {
        const sc = {
          title: a.scene_tag || '解决方案星图',
          // 星核里写的名字：就是这次要适配到的那个场景
          sceneName: a.scene_tag || '当前场景',
          sub: a.user_scene || '',
          origin: {
            scene: a.user_scene || '',
            solution: a.user_constraint || '',
            constraints: (a.diff && a.diff.diffs ? a.diff.diffs.map(d => d.dimension) : []),
            params: (a.diff && a.diff.diffs ? Object.fromEntries(a.diff.diffs.map(d => [d.dimension, d.mine])) : {}),
            boundaries: a.solution.summary || ''
          }
        };
        const raw = (a.solution && a.solution.steps) ? a.solution.steps : [];
        const depthPattern = [1, 2, 2, 3, 3];
        const steps = raw.map((step, i) => {
          const depth = depthPattern[i % depthPattern.length];
          return {
            id: step.step || i + 1,
            title: step.ref || `第 ${i + 1} 步`,
            depth,
            sit: step.action || '',
            diffs: step.ref ? [{ dimension: step.ref, origin: '原帖做法', mine: '当前场景', impact: step.why || '' }] : [],
            moves: [{ step: step.step || i + 1, title: step.ref || `第 ${i + 1} 步`, action: step.action || '' }],
            learned: step.why || ''
          };
        });
        return { SCENARIO: sc, steps };
      }

      async function loadData() {
        const fallback = buildDemoData();
        const id = props.sceneId;
        if (!id || id === 'demo') return fallback;
        const num = Number(id);
        if (!Number.isFinite(num) || num <= 0) return fallback;
        try {
          const adaptation = await getAdaptation(num);
          if (!adaptation || !adaptation.solution || !adaptation.solution.steps || !adaptation.solution.steps.length) return fallback;
          return buildFromAdaptation(adaptation);
        } catch (e) {
          console.error('load adaptation failed', e);
          return fallback;
        }
      }

      const loaded = await loadData();
      SCENARIO = loaded.SCENARIO;
      steps = loaded.steps;

      /* ---------------- 布局：倾斜星盘（共享引擎，按顺序均分整圈） ----------------
         步骤是线性的，所以不加「按分支聚类」，第 1 步在正上方、顺时针往下走。 */
      steps.forEach((s) => {
        s.name = `第 ${s.id} 步 · ${s.title}`;   // 星点标签就是这一步
        s.branch = '_steps';                     // 走 spread:'even'，不参与分支聚合
        s.verified = true;
      });

      /* 重算布局，并把几何字段写回**原对象**（保住对象标识，DOM 引用不失效） */
      function relayout() {
        const { w, h } = measureStage();
        LAY = buildLayout({ scenes: steps, vbW: w, vbH: h, cfg: { spread: 'even' } });
        (LAY.nodes || []).forEach((n) => {
          const s = steps.find((x) => x.id === n.id);
          if (!s) return;
          s.x = n.x; s.y = n.y; s.dx = n.dx; s.dy = n.dy; s.anchor = n.anchor;
          s.lbl = n.lbl; s.ang = n.ang; s.r = n.r; s.idx = n.idx;
        });
        CX = LAY.cx; CY = LAY.cy; SQUASH = LAY.squash; RING = LAY.ring;
        return LAY;
      }
      relayout();

      /* 根据加载到的数据更新页面静态文案
         （星核里那三行字交给 applyGeometry() —— 它们的字号由星核半径反推，属于布局的一部分，
           在这里写死会跟布局抢方向盘） */
      const titleEl = document.querySelector('.sm-title');
      if (titleEl) titleEl.textContent = SCENARIO.title + ' · 解决步骤星图';
      const subEl = document.querySelector('.sm-sub');
      if (subEl) subEl.textContent = SCENARIO.sub || '';
      const btnOrigin = document.getElementById('btnOrigin');
      if (btnOrigin) btnOrigin.innerHTML = '<b>场景拆解</b>';
  
      /* ---------------- DOM 构建 ---------------- */
      const svg = document.getElementById('svg');
      const vp = document.getElementById('vp');
      const orbitsG = document.getElementById('orbits');
      const raysG = document.getElementById('rays');
      const nodesG = document.getElementById('nodes');
      const panel = document.getElementById('panel');
      const chipsBox = document.getElementById('chips');
      const zoomtag = document.getElementById('zoomtag');
      const SVGNS = 'http://www.w3.org/2000/svg';
  
      const nodePop = {}; // id -> <g class="pop">
      function el(tag, attrs) {
        const e = document.createElementNS(SVGNS, tag);
        if (attrs) for (const k in attrs) e.setAttribute(k, attrs[k]);
        return e;
      }

      /* 星球环：rx=1.45R、ry=0.5R、整体倾斜 -16°，分前后两半 ——
         后半先画（被核体压住中段，只露两翼），前半后画（掠过核面下缘）。
         本地 path 画在 (0,0) 基准上，靠父 <g> 的 translate+rotate 定位；
         ⚠️ 不要改成 `rotate(a CX CY)` 直接转本地 path —— 那是绕 (CX,CY) 远处转，
         环会飞出几百像素（/starmap 光芒时代踩过的同款坑）。*/
      function buildSunRing(R) {
        const rx = R * 1.45, ry = R * 0.5;
        const f = (n) => n.toFixed(1);
        const putP = (gid, d, w) => {
          const p = document.querySelector('#' + gid + ' path');
          if (p) { p.setAttribute('d', d); p.setAttribute('stroke-width', w); }
        };
        putP('sunRingBack', `M ${f(-rx)} 0 A ${f(rx)} ${f(ry)} 0 0 1 ${f(rx)} 0`, Math.max(1.4, R * 0.045).toFixed(1));
        putP('sunRingFront', `M ${f(-rx)} 0 A ${f(rx)} ${f(ry)} 0 0 0 ${f(rx)} 0`, Math.max(1.4, R * 0.045).toFixed(1));
      }
  
      // 轨道环：先建好三条，具体半径由 applyGeometry() 按舞台尺寸刷新
      const orbitEls = [1, 2, 3].map(() => {
        const e = el('ellipse', { class: 'orbit' });
        orbitsG.appendChild(e);
        return e;
      });

      // 射线：星核 → 每颗星
      steps.forEach((s) => {
        const line = el('line', { class: 'ray', stroke: STAR_ON, x1: CX, y1: CY, x2: s.x, y2: s.y });
        line.style.setProperty('--i', s.idx);
        raysG.appendChild(line);
        s._ray = line;
      });

      // 星
      const STAR_SZ0 = LAY && LAY.starSz ? LAY.starSz : 14;
      steps.forEach((s) => {
        const g = el('g', { class: 'node', 'data-id': s.id });
        g.style.setProperty('--i', s.idx);
        const wrap = el('g', { transform: `translate(${s.x.toFixed(1)} ${s.y.toFixed(1)}) scale(1)` });
        const pop = el('g', { class: 'pop', style: '--s:1' });
        const hit = el('circle', { class: 'nhit', r: (STAR_SZ0 * 1.8).toFixed(1), fill: 'transparent' });
        pop.appendChild(hit);
        const ring = el('circle', { class: 'star-ring', r: (STAR_SZ0 * 1.45).toFixed(1), fill: 'none', stroke: STAR_ON, 'stroke-width': 1.4 });
        pop.appendChild(ring);
        const star = el('path', {
          class: 'star on', d: starPath(STAR_SZ0, STAR_SZ0 * 0.42),
          fill: STAR_ON, stroke: STAR_ON, 'stroke-width': 0
        });
        pop.appendChild(star);
        wrap.appendChild(pop);
        // 标签：偏移只走 transform（lblT），x/y 留 0。
        // 旧版 x/y 再叠一次 transform，等于偏移算了两遍（标签离星点两倍距离，白占地方）。
        const lbl = el('text', { class: 'lbl', x: 0, y: 0, 'text-anchor': s.anchor, 'dominant-baseline': 'central' });
        lbl.textContent = (s.lbl && s.lbl.text) || `第 ${s.id} 步 · ${s.title}`;
        wrap.appendChild(lbl);
        const det = el('text', { class: 'node-detail', x: 0, y: 14, 'text-anchor': s.anchor, 'dominant-baseline': 'central' });
        det.textContent = '已炼成 · 方法';
        wrap.appendChild(det);
        g.appendChild(wrap);
        nodesG.appendChild(g);
        nodePop[s.id] = pop;
        s._el = g; s._wrap = wrap; s._lbl = lbl; s._det = det;
        // 悬停聚焦：指到哪颗星，其余先退到背景里，这一颗的名字和状态立刻能看清
        g.addEventListener('mouseenter', () => {
          hoverId = s.id;
          g.classList.add('hov');
          svg.classList.add('hovering');
        });
        g.addEventListener('mouseleave', () => {
          if (hoverId === s.id) hoverId = null;
          g.classList.remove('hov');
          svg.classList.remove('hovering');
        });
      });
  
      // 顶部芯片
      steps.forEach((s) => {
        const c = document.createElement('button');
        c.className = 'chip';
        c.textContent = `第 ${s.id} 步 · ${s.title}`;
        c.dataset.id = s.id;
        c.addEventListener('click', () => { openNode(s.id); });
        chipsBox.appendChild(c);
      });
  
      /* ---------------- 视图 / 缩放 ---------------- */
      let view = 'overview';
      let activeId = null;
      let k = 1, tx = 0, ty = 0;
      const inv = () => 1 / Math.sqrt(k);
      const vpTransform = () => `translate(${tx} ${ty}) scale(${k})`;
      const wrapT = (n) => `translate(${n.x.toFixed(1)} ${n.y.toFixed(1)}) scale(${inv().toFixed(3)})`;
      const lblT = (n) => `translate(${n.dx.toFixed(1)} ${n.dy.toFixed(1)}) scale(${inv().toFixed(3)})`;
      const detT = (n) => `translate(${n.dx.toFixed(1)} ${(n.dy + 14).toFixed(1)}) scale(${inv().toFixed(3)})`;
      const lod = () => (k < 0.8 ? 1 : k < 1.6 ? 2 : 3);
      const lodName = () => ['', '总览', '星图', '细节'][lod()];
  
      function setVP() {
        vp.setAttribute('transform', vpTransform());
        steps.forEach((s) => {
          if (!s._wrap) return;
          s._wrap.setAttribute('transform', wrapT(s));
          if (s._lbl) s._lbl.setAttribute('transform', lblT(s));
          if (s._det) s._det.setAttribute('transform', detT(s));
        });
        zoomtag.innerHTML = `${lodName()} · <b>${k.toFixed(1)}x</b>`;
        svg.classList.toggle('lod' + lod(), true);
        ['lod1', 'lod2', 'lod3'].forEach((c) => { if (c !== 'lod' + lod()) svg.classList.remove(c); });
      }

      /* ---------------- 把布局结果落到 DOM（首次 + 每次 resize） ----------------
         viewBox 跟随舞台像素 = 「字号就是真实像素」的前提。 */
      function applyGeometry() {
        if (!LAY || !LAY.nodes.length) return;
        svg.setAttribute('viewBox', `0 0 ${LAY.vbW} ${LAY.vbH}`);

        const R = LAY.sunR;
        const put = (id, attrs) => {
          const e = document.getElementById(id);
          if (!e) return;
          for (const key in attrs) e.setAttribute(key, attrs[key]);
        };
        put('sunHalo', { cx: CX, cy: CY, r: (R * 1.95).toFixed(1) });
        put('sunGlow', { cx: CX, cy: CY, r: (R * 1.22).toFixed(1) });
        put('sunRingBack', { transform: `translate(${CX} ${CY}) rotate(-16)` });
        put('sunRingFront', { transform: `translate(${CX} ${CY}) rotate(-16)` });
        buildSunRing(R);
        put('sunRing', { cx: CX, cy: CY, r: R });
        // 进度弧从正上方起算 → 旋转中心必须跟着核心走（模板里写死的 440/400 会转歪）
        put('sunArc', { cx: CX, cy: CY, r: R, transform: `rotate(-90 ${CX} ${CY})` });
        put('sunCore', { cx: CX, cy: CY, r: (R * 0.83).toFixed(1) });
        put('sunHi', { cx: (CX - R * 0.3).toFixed(1), cy: (CY - R * 0.36).toFixed(1), r: (R * 0.52).toFixed(1) });
        put('coreHit', { cx: CX, cy: CY, r: (R * 1.06).toFixed(1) });
        put('coreText', { transform: `translate(${CX} ${CY})` });
        const blur = document.querySelector('#sunBlur feGaussianBlur');
        if (blur) blur.setAttribute('stdDeviation', (R * 0.15).toFixed(1));

        /* 星核里的三行字（⑤）：现在是「应用场景 / 场景名 / ★ N 步」。
           旧版写的是「原帖 · 基准处境 / 已收录步骤 ★ N」—— 那是把星核当成了原帖，
           可这一页回答的是「**这个场景**该怎么落地」，所以星核必须是场景本身。
           字号是恒定屏幕字号（不随画布缩放，硬约束），所以场景名只能按核面宽度砍字。 */
        const cf = LAY.coreFs;
        const fsSub = Math.max(10, Math.round(R * 0.17));
        const fsNum = Math.max(11, Math.round(R * 0.2));
        const fsHint = Math.max(9, Math.round(R * 0.14));
        const sub = document.getElementById('coreSub');
        const num = document.getElementById('coreNum');
        const hint = document.getElementById('coreHint');
        if (sub && num && hint) {
          const sceneName = SCENARIO.sceneName || SCENARIO.title || '当前场景';
          if (cf.compact) {
            sub.style.display = 'none';
            hint.style.display = 'none';
            num.setAttribute('y', 0); num.style.fontSize = cf.num + 'px';
            num.textContent = '★ ' + steps.length;
          } else {
            sub.style.display = ''; hint.style.display = '';
            sub.setAttribute('y', (-R * 0.28).toFixed(1)); sub.style.fontSize = fsSub + 'px';
            sub.textContent = '应用场景';
            num.setAttribute('y', 0); num.style.fontSize = fsNum + 'px';
            // 场景名按核面宽度截断：中文字宽 ≈ 字号、ASCII/空格 ≈ 0.55 字号
            //（跟布局模块 labelWidth 同一假设 —— 按字符数砍会把「学生版 · 20 次」这种带空格的砍成「学生版 · …」）
            const maxW = R * 0.83 * 2 * 0.94;
            const tw = (t) => { let n = 0; for (const ch of t) n += /[\u4e00-\u9fa5\u3000-\u303f\uff00-\uffef]/.test(ch) ? fsNum : fsNum * 0.55; return n; };
            num.textContent = tw(sceneName) <= maxW ? sceneName : (function () { let t = sceneName; while (t.length > 1 && tw(t + '…') > maxW) t = t.slice(0, -1); return t + '…'; })();
            // 0.34R：与 /starmap 一致 —— 再往下就贴到星球环前半（环前缘约 0.48R）了
            hint.setAttribute('y', (R * 0.34).toFixed(1)); hint.style.fontSize = fsHint + 'px';
            hint.textContent = '★ ' + steps.length + ' 步';
          }
        }

        // 三层轨道
        orbitEls.forEach((e, i) => {
          const r = RING[i + 1];
          e.setAttribute('cx', CX); e.setAttribute('cy', CY);
          e.setAttribute('rx', r.toFixed(1)); e.setAttribute('ry', (r * SQUASH).toFixed(1));
        });

        // 星点 / 射线 / 标签
        const sz = LAY.starSz;
        steps.forEach((s) => {
          if (s._ray) {
            s._ray.setAttribute('x1', CX); s._ray.setAttribute('y1', CY);
            s._ray.setAttribute('x2', s.x.toFixed(1)); s._ray.setAttribute('y2', s.y.toFixed(1));
          }
          // 摆得下就用（可能截断过的）短标签；降到 bare 档时只在悬停/选中时才出名字，那就用全名
          if (s._lbl) {
            s._lbl.textContent = s.lbl && s.lbl.show ? s.lbl.text : `第 ${s.id} 步 · ${s.title}`;
          }
          if (s._det) s._det.style.display = s.lbl && s.lbl.detail ? '' : 'none';
          const pop = nodePop[s.id];
          if (pop) {
            const hit = pop.querySelector('.nhit');
            if (hit) hit.setAttribute('r', (sz * 1.8).toFixed(1));
            const rg = pop.querySelector('.star-ring');
            if (rg) rg.setAttribute('r', (sz * 1.45).toFixed(1));
            const st = pop.querySelector('.star');
            if (st) st.setAttribute('d', starPath(sz, sz * 0.42));
          }
        });

        // 标签档位：小屏挤不下时布局会自己降档，bare 档只在悬停/选中时出名字
        svg.classList.toggle('labels-off', LAY.labelMode === 'bare');

        setVP();
      }

      // 舞台尺寸变了就重算布局 + 重落几何（旧版写死画布，窗口一变就跟不上）
      /* 舞台尺寸变了就重算布局 + 重落几何。
         判定用「量出来的尺寸是否真的变了」，而不是「跳过第一次回调」：
         第一次回调往往是带着真实尺寸来的（DOM 建完、芯片撑开顶栏之后），
         一刀切跳过就等于永远修不回那个偏差 —— 实测首屏 viewBox 高 823、真实舞台才 789。
         尺寸真没变时才安静返回，这样也不会抢掉进场动画。 */
      if (typeof ResizeObserver !== 'undefined') {
        const box = document.querySelector('#studentStepsApp .stage');
        if (box) {
          stageRO = new ResizeObserver(() => {
            const { w, h } = measureStage();
            if (LAY && LAY.vbW === w && LAY.vbH === h) return;
            relayout();
            applyGeometry();
            fitView(false);
          });
          stageRO.observe(box);
        }
      }
  
      const clamp = (v) => Math.min(KMAX, Math.max(KMIN, v));
      function zoomAt(nk, sx, sy, cx, cy) {
        nk = clamp(nk);
        if (nk === k) return;
        k = nk; tx = sx - cx * nk; ty = sy - cy * nk;
        setVP();
      }
      let animRAF = null;
      function animateTo(nk, ntx, nty, dur = 420) {
        if (animRAF) cancelAnimationFrame(animRAF);
        const k1 = k, tx1 = tx, ty1 = ty, t0 = performance.now();
        const step = (t) => {
          const p = Math.min((t - t0) / dur, 1);
          const e = 1 - Math.pow(1 - p, 3);
          k = k1 + (nk - k1) * e;
          tx = tx1 + (ntx - tx1) * e;
          ty = ty1 + (nty - ty1) * e;
          setVP();
          if (p < 1) animRAF = requestAnimationFrame(step);
        };
        animRAF = requestAnimationFrame(step);
      }
      function zoomBy(f) {
        const c = { x: (CX - tx) / k, y: (CY - ty) / k };
        const nk = clamp(k * f);
        animateTo(nk, CX - c.x * nk, CY - c.y * nk, 300);
      }
      function fitView(anim = true) {
        if (!LAY || !LAY.nodes.length) { if (anim) animateTo(1, 0, 0, 300); return; }
        // 布局模块已按真实规律（位置随 k、标签尺寸不随 k、星点随 √k）二分求出最大缩放
        const nk = LAY.k;
        /* ⚠️ bboxAt() 返回的**已经是乘过 k 的屏幕坐标**（内部就是 n.x * k）。
           旧版这里又 `* nk` 了一次：平移量被放大成 bbox中心·k²，复位后整盘会偏出去
           （k=1 时误差刚好为 0，所以只靠 k≈1 的截图根本看不出来 —— 这次是靠
            /starmap 在 k=1.7 的单星帖上「整盘飞出画布」才揪出来的）。
           正确写法：屏幕中心 = bbox 中心（已含 k）。 */
        const bb = bboxAt(LAY.nodes, LAY.starSz, nk);
        // 取景框把星核（含星球环，横向伸到 1.45R）一起圈进来：星核也吃 scale(k)，它不在 bboxAt 里
        const halo = (LAY.sunR || 0) * nk * 1.5;
        const minX = Math.min(bb.minX, LAY.cx * nk - halo);
        const maxX = Math.max(bb.maxX, LAY.cx * nk + halo);
        const minY = Math.min(bb.minY, LAY.cy * nk - halo);
        const maxY = Math.max(bb.maxY, LAY.cy * nk + halo);
        const ntx = CX - (minX + maxX) / 2;
        const nty = CY - (minY + maxY) / 2;
        if (anim) animateTo(nk, ntx, nty, 480);
        else { k = nk; tx = ntx; ty = nty; setVP(); }
      }
      function focusNode(n, z = 2.5) {
        const nk = clamp(z);
        animateTo(nk, CX - n.x * nk, CY - n.y * nk, 480);
      }
  
      /* ---------------- 指针交互 ---------------- */
      let dragging = false, moved = 0, last = null;
      let mouse = null;
      function sPt(e) {
        const p = svg.createSVGPoint(); p.x = e.clientX; p.y = e.clientY;
        return p.matrixTransform(svg.getScreenCTM().inverse());
      }
      function cPt(e) {
        const p = svg.createSVGPoint(); p.x = e.clientX; p.y = e.clientY;
        return p.matrixTransform(vp.getScreenCTM().inverse());
      }
      function onWheel(e) {
        const sp = sPt(e), cp = cPt(e);
        zoomAt(k * Math.exp(-e.deltaY * (e.ctrlKey ? 0.011 : 0.0022)), sp.x, sp.y, cp.x, cp.y);
      }
      function onDown(e) {
        if (e.pointerType === 'mouse' && e.button !== 0) return;
        dragging = true; moved = 0; last = sPt(e);
        try { svg.setPointerCapture(e.pointerId); } catch (_) {}
      }
      function onMove(e) {
        mouse = cPt(e);
        updatePop();
        if (!dragging) return;
        const p = sPt(e);
        const dx = p.x - last.x, dy = p.y - last.y;
        moved += Math.abs(dx) + Math.abs(dy);
        tx += dx; ty += dy; last = p;
        setVP();
      }
      function onUp(e) {
        if (dragging) {
          dragging = false;
          try { svg.releasePointerCapture(e.pointerId); } catch (_) {}
          if (moved <= 4) handleTap(e.clientX, e.clientY);
        }
      }
      function onLeave() { mouse = null; updatePop(); }
      function updatePop() {
        steps.forEach((s) => {
          let sc = 1;
          if (mouse) {
            const d = Math.hypot(s.x - mouse.x, s.y - mouse.y);
            if (d < 155) sc = 1 + 0.45 * Math.pow(1 - d / 155, 1.5);
          }
          if (activeId === s.id) sc = Math.max(sc, 2.4);
          nodePop[s.id].style.setProperty('--s', sc.toFixed(3));
        });
      }
      function handleTap(cx, cy) {
        const t = document.elementFromPoint(cx, cy);
        if (!t) return;
        const g = t.closest('.node');
        if (g) {
          const id = Number(g.dataset.id);
          if (activeId === id) backToSky();
          else openNode(id);
          return;
        }
        if (t.closest('.corehit')) { openOrigin(); return; }
        backToSky();
      }
  
      svg.addEventListener('wheel', (e) => { e.preventDefault(); onWheel(e); }, { passive: false });
      svg.addEventListener('pointerdown', onDown);
      svg.addEventListener('pointermove', onMove);
      svg.addEventListener('pointerup', onUp);
      svg.addEventListener('pointercancel', onUp);
      svg.addEventListener('pointerleave', onLeave);
  
      document.getElementById('zoomIn').addEventListener('click', () => zoomBy(1.45));
      document.getElementById('zoomOut').addEventListener('click', () => zoomBy(1 / 1.45));
      document.getElementById('btnReset').addEventListener('click', () => { backToSky(); });
      document.getElementById('btnOrigin').addEventListener('click', () => openOrigin());
  
      /* ---------------- 面板动作 ---------------- */
      function syncActive() {
        steps.forEach((s) => {
          s._el.classList.toggle('on', s.id === activeId);
          s._ray.classList.toggle('hot', s.id === activeId && activeId !== null);
        });
        chipsBox.querySelectorAll('.chip').forEach((c) => {
          const id = Number(c.dataset.id);
          c.classList.toggle('on', id === activeId);
        });
      }
      function openNode(id) {
        activeId = id; view = 'node';
        const n = steps.find((x) => x.id === id);
        if (n) focusNode(n);
        svg.classList.add('locked');
        syncActive();
        renderPanel();
      }
      function openOrigin() {
        activeId = null; view = 'origin';
        svg.classList.remove('locked');
        syncActive();
        fitView();
        renderPanel();
      }
      function backToSky() {
        activeId = null; view = 'overview';
        svg.classList.remove('locked');
        syncActive();
        fitView();
        renderPanel();
      }
  
      function escapeHTML(s) {
        return String(s).replace(/[&<>]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]));
      }
  
      function renderPanel() {
        if (view === 'overview' || view === 'origin') {
          const isOrigin = view === 'origin';
          let html = '';
          html += `<div class="kicker">${isOrigin ? '当前应用场景（星核）' : 'A1 · 场景拆解'}</div>`;
          html += `<h2 class="p-title">${escapeHTML(SCENARIO.title)}</h2>`;
          html += `<p class="p-origin">${escapeHTML(SCENARIO.origin.scene)}</p>`;
          html += `<div class="tags">${SCENARIO.origin.constraints.map((c) => `<span class="tag">${escapeHTML(c)}</span>`).join('')}</div>`;
          html += `<div class="stat-line">
            <div class="stat"><b>${steps.length}</b><span>已炼成方法</span></div>
            <div class="stat"><b>${steps.length}</b><span>对应步骤</span></div>
            <div class="stat"><b>20</b><span>次/天 额度</span></div>
          </div>`;
          html += `<div class="sec">当前处境的约束</div>`;
          html += `<p class="p-origin">${escapeHTML(SCENARIO.origin.solution)}</p>`;
          if (isOrigin) {
            html += `<div class="sec">关键前提</div>`;
            html += `<table class="diff-tb"><tr><th>维度</th><th>作者</th></tr>`;
            for (const key in SCENARIO.origin.params) {
              html += `<tr><td class="dim">${escapeHTML(key)}</td><td class="mine">${escapeHTML(SCENARIO.origin.params[key])}</td></tr>`;
            }
            html += `</table>`;
            html += `<div class="sec">适用边界</div>`;
            html += `<p class="p-origin">${escapeHTML(SCENARIO.origin.boundaries)}</p>`;
            html += `<div class="fb-row"><button class="back-btn" id="backSky">← 回到总览</button></div>`;
            html += `<p class="nav-note">要回<b>上一层星图</b>（那张「一个原帖、N 个处境」的图），用页面左上角的「← 返回上一级」。</p>`;
          } else {
            html += `<div class="sec">这张星图怎么读</div>`;
            html += `<p class="hint">
              正中那颗<b>星核＝当前应用场景</b>，外圈每颗<b>星＝一个解决步骤</b>。<br />
              从<b>最上面那颗</b>起，<b>顺时针</b>就是第 1 步 → 最后一步。<br />
              绕着星核的<b>细环</b>是它的轨道圈，外圈那道<b>蓝色环</b>＝这些步骤<b>已经全部炼成</b>。<br /><br />
              点一颗星，看这一步针对这个处境改成了什么。
            </p>`;
            html += `<div class="peer">一个帖子的价值 ＝ <b>走通的路</b> ＋ <b>被标记的死路</b>。同一个问题，不用每个人从头撞一遍墙。</div>`;
          }
          panel.innerHTML = html;
          const bs = document.getElementById('backSky');
          if (bs) bs.addEventListener('click', backToSky);
          return;
        }
  
        // 星详情（A2）
        const n = steps.find((x) => x.id === activeId);
        if (!n) return;
        let html = '';
        html += `<div class="kicker">A2 · 差异 · ${DEPTH_NAME[n.depth]}</div>`;
        html += `<h2 class="p-title">第 ${n.id} 步 · ${escapeHTML(n.title)}</h2>`;
        html += `<div class="np-head">
          <span class="verified ok">● 已炼成</span>
          <button class="back-btn" id="backSky">← 回到总览</button>
        </div>`;
  
        html += `<div class="sec">① 他的处境</div>`;
        html += `<p class="p-origin">${escapeHTML(n.sit)}</p>`;
  
        if (n.diffs && n.diffs.length) {
          html += `<div class="sub">和原帖的关键差异</div>`;
          html += `<table class="diff-tb"><tr><th>维度</th><th>原帖</th><th>他</th><th>影响</th></tr>`;
          n.diffs.forEach((d) => {
            html += `<tr><td class="dim">${escapeHTML(d.dimension)}</td><td>${escapeHTML(d.origin)}</td><td class="mine">${escapeHTML(d.mine)}</td><td>${escapeHTML(d.impact)}</td></tr>`;
          });
          html += `</table>`;
        }
  
        html += `<div class="sec">② 针对这个处境，改成了这样</div>`;
        html += `<ul class="moves">`;
        n.moves.forEach((m) => {
          html += `<li><b>第 ${m.step} 步 · ${escapeHTML(m.title)}</b>${escapeHTML(m.action)}</li>`;
        });
        html += `</ul>`;
  
        html += `<div class="sec">③ 我们学到了什么</div>`;
        html += `<div class="learn"><b>💡 ${escapeHTML(n.learned)}</b></div>`;
  
        html += `<div class="fb-row"><button class="back-btn" id="backSky2">← 回到总览</button></div>`;
        panel.innerHTML = html;
        const b = document.getElementById('backSky'); if (b) b.addEventListener('click', backToSky);
        const b2 = document.getElementById('backSky2'); if (b2) b2.addEventListener('click', backToSky);
      }
  
      /* ---------------- 进场 ---------------- */
      function playEnter() {
        svg.classList.remove('entered');
        requestAnimationFrame(() => requestAnimationFrame(() => svg.classList.add('entered')));
      }
  
      /* 从上一星图点击某颗星进入本界面的转场动画 */
      function playEntry(id) {
        const n = steps.find((x) => x.id === id);
        if (!n) return;
        activeId = id; view = 'node';
        svg.classList.add('locked');
        syncActive();
  
        const startK = 4.4, endK = 2.5;
        const startTX = CX - n.x * startK, startTY = CY - n.y * startK;
        const endTX = CX - n.x * endK, endTY = CY - n.y * endK;
        k = startK; tx = startTX; ty = startTY;
        updatePop();
        nodePop[id].style.setProperty('--s', '4.2');
        setVP();
  
        renderPanel();
        const app = document.getElementById('studentStepsApp');
        app.classList.add('entrying');
        svg.classList.add('entry', 'no-pop-trans');
        svg.offsetHeight; // force reflow so .entry hiding is applied before fade-in
  
        const t0 = performance.now(), dur = 1150;
        const step = (t) => {
          const p = Math.min((t - t0) / dur, 1);
          const e = 1 - Math.pow(1 - p, 3);
          k = startK + (endK - startK) * e;
          tx = startTX + (endTX - startTX) * e;
          ty = startTY + (endTY - startTY) * e;
          const sc = 4.0 + (2.4 - 4.0) * e;
          nodePop[id].style.setProperty('--s', sc.toFixed(3));
          setVP();
          if (p < 1) {
            requestAnimationFrame(step);
          } else {
            svg.classList.remove('entry', 'no-pop-trans');
            app.classList.remove('entrying');
            updatePop();
          }
        };
        requestAnimationFrame(() => {
          svg.classList.remove('entry'); // trigger fade-in of orbits/rays/sun/non-active stars
          requestAnimationFrame(step);
        });
      }
  
      function parseEntryStep() {
        const q = new URLSearchParams(location.search).get('step');
        if (q) { const n = Number(q); if (steps.some((s) => s.id === n)) return n; }
        const h = location.hash.replace(/^#step=?/, '');
        if (h) { const n = Number(h); if (steps.some((s) => s.id === n)) return n; }
        return null;
      }
  
      /* 首次把布局落到 DOM：viewBox / 轨道 / 星核 / 星点尺寸 / 标签档位一次到位。
         这里**再算一次**布局：上面那次 relayout() 跑在芯片还没进 DOM 的时候，
         量到的是「顶栏只有一行标题」的高度，跟芯片撑开之后的真实舞台对不上。
         少了这一步，首屏的几何会一直是按错尺寸算出来的。 */
      relayout();
      applyGeometry();

      renderPanel();
      const entryStep = parseEntryStep();
      if (entryStep) playEntry(entryStep);
      else { fitView(false); playEnter(); }
      // ResizeObserver 缺席（老环境）时的兜底；有它就不重复监听，免得一次 resize 算两遍
      if (!stageRO) window.addEventListener('resize', () => { relayout(); applyGeometry(); fitView(false); });
})
</script>

<style scoped>

    .app {
      --zh-blue: #056de8;
      --zh-blue-hover: #0456b8;
      --zh-blue-soft: #e6f0fd;
      --zh-blue-line-strong: #a9d2fb;
      --bg-2: #ffffff;
      --surface-2: #f4f6f8;
      --text: #1a1a1a;
      --text-2: #454545;
      --text-3: #8590a6;
      --border: #e3e4e5;
      --ok: #0f9d63;
    }
    * { box-sizing: border-box; }
    /* 注意：scoped 样式里的 html / body 选择器会被编译成 html[data-v-x]，永远匹配不到。
       原来那三条 html,body{height:100%} / body{margin:0} 其实一直是死代码 —— 已删除，
       免得下次有人以为页面被锁死了。 */
    .app { display: flex; flex-direction: column; }

    /* 顶部条（对应原版 sm-head / sm-chips） */
    .sm-head {
      display: flex; align-items: center; gap: 12px;
      padding: 10px 14px; flex-wrap: wrap;
      background: #fff; border-bottom: 1px solid var(--border);
    }
    .sm-headline { display: flex; align-items: baseline; gap: 6px; min-width: 0; }
    .sm-title { font-size: 15px; font-weight: 600; color: var(--text); margin: 0; }
    .sm-sub { font-size: 12px; color: var(--text-3); margin-left: 4px; }
    /* 返回上一级（⑥）：回到 /starmap。放在最左边 —— 它是这一页的「出口」，
       用户从星图点进来之后要能一眼找到回去的路（浏览器后退键不够用：
       从分享链接直接进来时，后退会把用户弹出站外）。 */
    .back-up { flex: none; }
    .sm-chips { display: flex; gap: 8px; overflow-x: auto; min-width: 0; }
    .sm-chips::-webkit-scrollbar { height: 0; }
    /* .chip 是 JS 动态创建的 → 规则在文件末尾的非 scoped 样式块里 */
    .sm-actions { display: flex; gap: 8px; margin-left: auto; }
    .btn {
      display: inline-flex; align-items: center; padding: 7px 13px; border-radius: 6px;
      font-size: 12.5px; cursor: pointer; font-family: inherit; white-space: nowrap;
      text-decoration: none; transition: 0.16s; border: 1px solid var(--border); background: var(--bg-2); color: var(--text-2);
    }
    .btn.ghost:hover { color: var(--zh-blue); border-color: var(--zh-blue-line-strong); background: var(--zh-blue-soft); }
    .btn.ghost b { color: var(--zh-blue); }
    .btn.primary { border: 1px solid var(--zh-blue); background: var(--zh-blue); color: #fff; font-weight: 500; }
    .btn.primary:hover { background: var(--zh-blue-hover); }

    /* 主体：星盘在上、面板在下。
       为什么不并排：星盘是横向的东西，而这一步星图的标签很长
       （「第 3 步 · 只改不会动的那一步」在 14px 下约 173px 宽），
       并排时 1080px 的内容区要切 430px 给面板，舞台只剩 ~564px；
       左右两侧各站一个长标签就把半径卡到 93 —— 盘面只占舞台宽度的 1/3，上下大片空白。
       改成上下排之后舞台宽 ~1030px、高 ~486px，半径能到 292（盘面 584px 宽，面积是原来的 ~6.8 倍）。 */
    .sm-body { display: flex; flex-direction: column; gap: 12px; }
    .stage {
      position: relative; flex: none; min-width: 0;
      height: clamp(380px, 54vh, 640px);
      background: #fbfcfd; border: 1px solid var(--border); border-radius: 8px; overflow: hidden;
    }
    .web { width: 100%; height: 100%; display: block; cursor: grab; touch-action: none; }
    .web:active { cursor: grabbing; }

    .panel {
      width: auto; flex: none; padding: 18px 20px;
      background: var(--bg-2); border: 1px solid var(--border); border-radius: 8px;
    }
    .panel::-webkit-scrollbar { width: 6px; }
    .panel::-webkit-scrollbar-thumb { background: #dfe3e8; border-radius: 3px; }

    /* svg：星核 + 中心三行字是模板渲染的，scoped 能覆盖，规则留在这里。
       星盘里**其余**元素（轨道 / 射线 / 星点 / 标签）都是 onMounted 里 createElementNS
       拼出来的，Vue 不会给它们加 data-v 属性 —— scoped 编译出的 .lbl[data-v-x] 一条也匹配不上。
       后果：标签掉回 SVG 默认的 16px / 纯黑 / 无白描边（压在轨道线上就是「看不清字」）、
       .orbit 的 stroke 变 none（三层轨道环压根没画出来）、.star-ring 的 opacity:0 失效（每颗星都挂个常亮圈）。
       所以它们全部搬到文件末尾的非 scoped 样式块，用 #studentStepsApp 自己限定作用域。 */
    .core-sub { font-size: 16px; font-weight: 600; fill: #174a86; }
    .core-num { font-size: 15px; fill: var(--zh-blue); font-weight: 600; }
    .core-hint { font-size: 12px; fill: #8590a6; }
    .corehit { cursor: pointer; }
    .web.locked .sun-glow { opacity: 0.3; }

    /* ---- 星核的核晕（与 /starmap 的星核同一套画法） ----
       .sun-halo 是模板里的元素，scoped 能给它加 data-v。
       星球环的 path 由 JS 改 d，颜色/透明度全走 SVG 属性，不依赖 CSS。
       这里只管「呼吸」。 */
    .sun-halo { animation: haloPulseStudent 7s ease-in-out infinite; }
    @keyframes haloPulseStudent { 0%, 100% { opacity: 0.8; } 50% { opacity: 1; } }
    /* 核体高光压在文字下面，别抢走 coreHit 的点击 */
    .core-hi { pointer-events: none; }

    @media (prefers-reduced-motion: reduce) {
      .sun-halo { animation: none; }
    }

    /* 从上一星图点击进入的转场（模板元素部分） */
    .app.entrying .panel { opacity: 0; transform: translateX(30px); }
    .app.entrying .hintbar, .app.entrying .zoombar, .app.entrying .zoomtag { opacity: 0; }
    .panel { transition: opacity .55s ease, transform .55s cubic-bezier(.22,1,.36,1); }
    .app.entrying .hintbar, .app.entrying .zoombar, .app.entrying .zoomtag, .panel { transition: opacity .55s ease, transform .55s cubic-bezier(.22,1,.36,1); }
    .web.entry .sun { opacity: 0; transition: opacity 1.05s ease; }

    /* 进场动画（模板元素部分；星点/射线/轨道的在非 scoped 块） */
    .web:not(.entered) .sun { opacity: 0; }
    .web.entered .sun { transform-box: fill-box; transform-origin: center; animation: sunInStudent 0.7s cubic-bezier(0.22, 1, 0.36, 1) backwards; }
    @keyframes sunInStudent { from { opacity: 0; transform: scale(0.55); } to { opacity: 1; transform: scale(1); } }
    @keyframes fadeInStudent { from { opacity: 0; } to { opacity: 1; } }

    /* 浮层 */
    .legend {
      position: absolute; left: 14px; top: 12px; display: flex; flex-direction: column; gap: 7px;
      padding: 10px 12px; background: rgba(255,255,255,0.9); border: 1px solid var(--border);
      border-radius: 8px; pointer-events: none; line-height: 1;
    }
    .lg-line { display: flex; align-items: center; gap: 12px; font-size: 11.5px; color: var(--text-3); }
    .lg { display: inline-flex; align-items: center; gap: 5px; }
    .lg i { width: 9px; height: 9px; border-radius: 50%; flex: none; }
    .lg.sun i { background: radial-gradient(circle at 34% 30%, #fff6e2, #f0b45c); box-shadow: 0 0 5px rgba(240,180,92,0.65); }
    .lg.ok i { background: var(--zh-blue); }
    .lg-line.depth { gap: 0; white-space: nowrap; }
    .lg-line.depth b { font-weight: 500; color: var(--text-2); margin-left: 4px; }
    .lg-line.depth em { font-style: normal; font-size: 10px; color: #c9cfd9; margin-left: 4px; }
    .hintbar {
      position: absolute; left: 50%; bottom: 12px; transform: translateX(-50%);
      font-size: 11.5px; color: var(--text-3); line-height: 1; white-space: nowrap;
      background: rgba(255,255,255,0.88); border: 1px solid var(--border);
      border-radius: 999px; padding: 7px 14px; pointer-events: none;
    }
    .zoomtag {
      position: absolute; left: 14px; bottom: 12px; font-size: 11.5px; color: var(--text-3);
      border: 1px solid var(--border); border-radius: 999px; padding: 5px 12px; background: #fff;
    }
    .zoomtag b { color: var(--zh-blue); }
    .zoombar { position: absolute; right: 14px; bottom: 12px; display: flex; flex-direction: column; gap: 8px; }
    .zoombar button {
      width: 32px; height: 32px; border-radius: 6px; border: 1px solid var(--border); background: #fff;
      color: var(--text-2); font-size: 15px; line-height: 1; cursor: pointer; padding: 0; font-family: inherit; transition: 0.16s;
    }
    .zoombar button.sm { font-size: 11px; }
    .zoombar button:hover { color: var(--zh-blue); border-color: var(--zh-blue-line-strong); background: var(--zh-blue-soft); }

    /* 面板内容（.kicker / .p-title / .stat / .tag / .moves / .learn …）
       全部由 renderPanel() 用 innerHTML 拼出来 → 同样是 JS 动态创建，拿不到 data-v，
       scoped 一条也匹配不上（原来的后果：统计格、标签、步骤列表全是裸文本）。
       这些规则在文件末尾的非 scoped 块里。 */

    @media (max-width: 860px) {
      .stage { height: 44vh; }
      .sm-sub { display: none; }
      .hintbar { display: none; }
      /* 小屏：图例只留「原帖 / 解决步骤」，轨道说明交给下面的面板 */
      .legend { padding: 7px 9px; gap: 5px; }
      .lg-line.depth { display: none; }
    }
  
</style>

<!--
  非 scoped 样式块：只装「JS 动态创建的元素」的规则。
  ------------------------------------------------------------------
  为什么不能用 scoped：本组件的星点/射线/轨道/标签是 onMounted 里 createElementNS 拼的，
  面板内容（.stat / .tag / .moves / .learn …）是 renderPanel() 里 innerHTML 拼的。
  Vue 只会给**模板里写的**元素加 data-v-xxx，动态创建的拿不到，
  于是 scoped 编译出的 `.lbl[data-v-xxx]` 之类**一条也匹配不上**：
    标签 → SVG 默认 16px / 纯黑 / 无白描边 → 压在轨道线上就是「看不清字儿」
    .orbit → stroke:none，三层轨道环根本没画出来
    .star-ring → opacity:0 失效，每颗星都挂着一个常亮圈
    .pop → transform:scale(var(--s)) 失效，悬停放大和选中放大全部不动
    面板 → 统计格/标签/步骤列表全是裸文本
  所以这一段必须是非 scoped 的，作用域靠 #studentStepsApp 这个 id 自己收住 ——
  组件没挂载时页面上不存在这个 id，规则不会外泄。
  改这里的样式时记得：这一段没有 data-v 保护，别把选择器写成全局的。
-->
<style>
  /* ---- 顶部芯片（createElement('button')） ---- */
  #studentStepsApp .chip {
    padding: 6px 12px; border: 1px solid var(--border); border-radius: 999px;
    background: var(--bg-2); color: var(--text-2); font-size: 12px;
    cursor: pointer; white-space: nowrap; font-family: inherit; transition: 0.16s;
  }
  #studentStepsApp .chip:hover { color: var(--zh-blue); border-color: var(--zh-blue-line-strong); background: var(--zh-blue-soft); }
  #studentStepsApp .chip.on { color: #fff; background: var(--zh-blue); border-color: var(--zh-blue); }

  /* ---- 星盘 ---- */
  #studentStepsApp .orbit { fill: none; stroke: #d5dbe4; stroke-width: 1; opacity: 0.75; stroke-dasharray: 3 7; }
  #studentStepsApp .ray { fill: none; stroke-width: 1.2; opacity: 0.5; }
  #studentStepsApp .ray.hot { opacity: 1; stroke-width: 1.6; }
  #studentStepsApp .node { cursor: pointer; }
  #studentStepsApp .pop {
    transform: scale(var(--s, 1)); transform-box: fill-box; transform-origin: center;
    transition: transform 0.2s cubic-bezier(0.34, 1.4, 0.64, 1);
  }
  #studentStepsApp .star { stroke-linejoin: round; }
  #studentStepsApp .nhit { pointer-events: all; cursor: pointer; }
  #studentStepsApp .star-ring { opacity: 0; transition: opacity .25s ease; pointer-events: none; }
  #studentStepsApp .node.on .star-ring { opacity: .55; }

  /* 字号必须与 starmapLayout.js 的 labelFs(14) / labelOff(14) / labelDesc 一致，
     否则「布局按 14px 算占位、实际画出来另一个尺寸」——摆位和渲染两张皮。 */
  #studentStepsApp .lbl {
    font-size: 14px; font-weight: 600; fill: #16181c;
    paint-order: stroke; stroke: #fbfcfd; stroke-width: 5.5; stroke-linejoin: round;
    transition: font-size 0.2s, opacity .35s ease;
  }
  #studentStepsApp .node.on .lbl { font-size: 15.5px; fill: var(--zh-blue); }
  #studentStepsApp .node.hov .lbl { fill: var(--zh-blue); }
  #studentStepsApp .node-detail {
    font-size: 11.5px; fill: #6f7b8f;
    paint-order: stroke; stroke: #fbfcfd; stroke-width: 5; stroke-linejoin: round;
    transition: opacity .4s ease;
  }

  /* 视图状态：总览档隐藏副标题 / 选中时压暗其余 / 降档隐藏标签 / 悬停聚焦 */
  #studentStepsApp .web.lod1 .node-detail { display: none; }
  #studentStepsApp .web.locked .node:not(.on) { opacity: 0.32; transition: opacity 0.34s ease; }
  #studentStepsApp .web.locked .node.on { opacity: 1 !important; }
  #studentStepsApp .web.locked .ray:not(.hot) { opacity: 0.08; }
  #studentStepsApp .web.locked .orbit { opacity: 0.16; }

  /* 降档到 bare：真的摆不下名字了就先藏起来（点/悬停时才出），
     而不是让它们压成一团黑字 —— 看得见的东西少一点，看得清的东西多一点。 */
  #studentStepsApp .web.labels-off .lbl { opacity: 0; }
  #studentStepsApp .web.labels-off .node.on .lbl,
  #studentStepsApp .web.labels-off .node.hov .lbl { opacity: 1; }
  #studentStepsApp .web.labels-off .node-detail { display: none; }

  /* 悬停聚焦：指到哪颗星，其余先退到背景里，这一颗的名字和状态立刻能看清 */
  #studentStepsApp .web.hovering .node:not(.hov):not(.on) { opacity: 0.42; transition: opacity 0.22s ease; }
  #studentStepsApp .web.hovering .ray:not(.hot) { opacity: 0.12; }
  #studentStepsApp .web.hovering .orbit { opacity: 0.32; }

  /* 转场 / 进场（星点、射线、轨道部分；.sun 的在 scoped 块里） */
  #studentStepsApp .web.entry .orbit,
  #studentStepsApp .web.entry .ray:not(.hot),
  #studentStepsApp .web.entry .node:not(.on) { opacity: 0; transition: opacity 1.05s ease; }
  #studentStepsApp .web.entry .node.on { opacity: 1; }
  #studentStepsApp .web.entry .node.on .lbl,
  #studentStepsApp .web.entry .node.on .node-detail { opacity: 0; transition: opacity .45s ease .7s; }
  #studentStepsApp .web.no-pop-trans .pop { transition: none !important; }

  #studentStepsApp .web:not(.entered) .node,
  #studentStepsApp .web:not(.entered) .ray,
  #studentStepsApp .web:not(.entered) .orbit { opacity: 0; }
  #studentStepsApp .web.entered .orbit { animation: fadeInStudent 0.6s ease 0.12s backwards; }
  #studentStepsApp .web.entered .ray { animation: fadeInStudent 0.5s ease backwards; animation-delay: calc(var(--i, 0) * 0.05s + 0.28s); }
  #studentStepsApp .web.entered .node { animation: fadeInStudent 0.55s ease backwards; animation-delay: calc(var(--i, 0) * 0.05s + 0.3s); }

  /* ---- 面板内容（renderPanel 拼出来的 html 串） ---- */
  #studentStepsApp .pv-empty { color: var(--text-3); font-size: 13.5px; padding: 20px 0; }
  #studentStepsApp .kicker { font-size: 11.5px; letter-spacing: 1.5px; color: var(--zh-blue); font-weight: 500; }
  #studentStepsApp .p-title { font-size: 19px; font-weight: 600; margin: 8px 0 6px; line-height: 1.45; color: var(--text); }
  #studentStepsApp .p-origin { font-size: 13.5px; color: var(--text-2); margin: 0 0 10px; line-height: 1.8; }
  #studentStepsApp .p-origin.lead { color: var(--zh-blue); }
  #studentStepsApp .sub-line { color: var(--text-3); font-size: 12.5px; }
  #studentStepsApp .tags { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 10px; }
  #studentStepsApp .tag { font-size: 11.5px; color: var(--text-2); background: var(--surface-2); border: 1px solid var(--border); border-radius: 4px; padding: 3px 8px; }
  #studentStepsApp .stat-line { display: flex; gap: 10px; margin: 12px 0 4px; }
  #studentStepsApp .stat { flex: 1; background: var(--surface-2); border: 1px solid var(--border); border-radius: 6px; padding: 9px 11px; }
  #studentStepsApp .stat b { display: block; font-size: 20px; color: var(--zh-blue); line-height: 1.2; }
  #studentStepsApp .stat span { font-size: 11.5px; color: var(--text-3); }
  #studentStepsApp .sec { margin: 18px 0 8px; font-size: 12px; color: var(--text-3); letter-spacing: 1px; font-weight: 500; }
  #studentStepsApp .sub { font-size: 11.5px; color: var(--text-3); margin: 12px 0 4px; }
  #studentStepsApp .diff-tb { width: 100%; border-collapse: collapse; font-size: 12.5px; }
  #studentStepsApp .diff-tb th { text-align: left; color: var(--text-3); font-weight: 400; padding: 5px; border-bottom: 1px solid var(--border); }
  #studentStepsApp .diff-tb td { padding: 7px 5px; border-bottom: 1px solid var(--border); color: var(--text-2); vertical-align: top; line-height: 1.7; }
  #studentStepsApp .diff-tb td.dim { color: var(--text); white-space: nowrap; font-weight: 500; }
  #studentStepsApp .diff-tb td.mine { color: var(--zh-blue); }
  #studentStepsApp .moves { margin: 0; padding: 0; list-style: none; counter-reset: mv; }
  #studentStepsApp .moves li { position: relative; padding: 8px 0 8px 26px; font-size: 13px; color: var(--text-2); border-bottom: 1px solid var(--border); line-height: 1.75; }
  #studentStepsApp .moves li:last-child { border-bottom: 0; }
  #studentStepsApp .moves li::before {
    counter-increment: mv; content: counter(mv); position: absolute; left: 0; top: 10px;
    width: 16px; height: 16px; border-radius: 50%; background: var(--zh-blue-soft); color: var(--zh-blue);
    font-size: 10.5px; line-height: 16px; text-align: center; font-weight: 600;
  }
  #studentStepsApp .moves li b { display: block; color: var(--text); font-size: 12.5px; margin-bottom: 1px; }
  #studentStepsApp .moves .why { display: block; color: var(--text-3); font-size: 12px; margin-top: 2px; }
  #studentStepsApp .peer { font-size: 13px; color: var(--text-2); background: var(--surface-2); border: 1px solid var(--border); border-radius: 6px; padding: 10px 12px; margin-top: 12px; line-height: 1.75; }
  #studentStepsApp .peer b { color: var(--zh-blue); }
  #studentStepsApp .hint { font-size: 13px; color: var(--text-2); line-height: 1.95; }
  #studentStepsApp .hint b { color: var(--text); }
  #studentStepsApp .np-head { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }
  #studentStepsApp .verified { display: inline-flex; align-items: center; gap: 5px; font-size: 11.5px; padding: 3px 9px; border-radius: 4px; }
  #studentStepsApp .verified.ok { color: #0b7a4d; background: #e8f7f0; border: 1px solid #bfe6d3; }
  #studentStepsApp .verified.draft { color: #b8792a; background: #fef6e9; border: 1px solid #f6ddb6; }
  #studentStepsApp .back-btn { margin-left: auto; padding: 5px 11px; border: 1px solid var(--border); border-radius: 6px; background: var(--bg-2); color: var(--text-2); font-size: 12px; cursor: pointer; font-family: inherit; transition: 0.16s; }
  #studentStepsApp .back-btn:hover { color: var(--zh-blue); border-color: var(--zh-blue-line-strong); background: var(--zh-blue-soft); }
  #studentStepsApp .learn { background: #e8f7f0; border: 1px solid #bfe6d3; border-radius: 6px; padding: 11px 13px; font-size: 13px; color: #0b7a4d; line-height: 1.8; margin-top: 6px; }
  #studentStepsApp .learn b { color: #0b7a4d; }
  /* 「回到总览」和「返回上一级」是两件事，面板里用一行小字把出口说清楚 */
  #studentStepsApp .nav-note { font-size: 12px; color: var(--text-3); line-height: 1.7; margin: 8px 0 0; }
  #studentStepsApp .nav-note b { color: var(--text-2); }
</style>
