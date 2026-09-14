<template>
<div id="studentStepsApp" class="app">
    <header class="sm-head">
      <div style="display:flex;align-items:baseline;gap:6px;">
        <h1 class="sm-title">学生版 AI 学习法 · 五步星图</h1>
        <span class="sm-sub">把作者的「随便试」炼成学生的「20 次额度」</span>
      </div>
      <div class="sm-chips" id="chips"></div>
      <div class="sm-actions">
        <button class="btn ghost" id="btnOrigin"><b>原帖拆解</b></button>
      </div>
    </header>

    <section class="sm-body">
      <div class="stage">
        <svg class="web" id="svg" viewBox="0 0 900 790" preserveAspectRatio="xMidYMid meet">
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
          <g id="vp">
            <g id="orbits"></g>
            <g id="rays"></g>
            <g class="sun">
              <circle class="sun-glow" cx="440" cy="400" r="86" fill="url(#sunGrad)" filter="url(#sunBlur)" />
              <circle cx="440" cy="400" r="70" fill="none" stroke="#dbe6f4" stroke-width="1" />
              <circle class="varc" cx="440" cy="400" r="70" fill="none" stroke="#056de8" stroke-width="1.6" />
              <circle class="corec" cx="440" cy="400" r="58" fill="url(#coreGrad)" stroke="#dbe6f4" stroke-width="1" />
              <g transform="translate(440 400)">
                <text class="core-sub" x="0" y="-8" text-anchor="middle">原帖 · 基准处境</text>
                <text class="core-num" x="0" y="16" text-anchor="middle">已收录处境 ★ 5</text>
                <text class="core-hint" x="0" y="36" text-anchor="middle">点击查看原帖拆解</text>
              </g>
            </g>
            <circle class="corehit" cx="440" cy="400" r="72" fill="transparent"></circle>
            <g id="nodes"></g>
          </g>
        </svg>

        <div class="hintbar">
          滚轮缩放 · 拖拽平移<br/>
          <b>点星看这一步怎么炼 · 点太阳看原帖拆解 · 顶部芯片直达每一步</b>
        </div>
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
import { onMounted } from "vue"
import { getAdaptation } from '../api'

const props = defineProps(['sceneId'])

onMounted(async () => {
  /* ---------------- 常量 ---------------- */
      const CX = 440, CY = 400, SQUASH = 0.46, RAD = Math.PI / 180;
      const RING = { 1: 198, 2: 280, 3: 362 };
      const STAR_ON = '#056de8', STAR_OFF = '#f0a03c';
      const KMIN = 0.45, KMAX = 4;
      const DEPTH_NAME = { 1: '改参数', 2: '动结构', 3: '换方案' };
  
      function starPath(R, r) {
        const p = [];
        for (let i = 0; i < 8; i++) {
          const a = (-90 + i * 45) * RAD;
          const rad = i % 2 === 0 ? R : r;
          p.push((Math.cos(a) * rad).toFixed(2) + ' ' + (Math.sin(a) * rad).toFixed(2));
        }
        return 'M' + p.join(' L') + ' Z';
      }
  
      /* ---------------- 数据加载 ---------------- */
      let SCENARIO = null;
      let steps = [];

      function buildDemoData() {
        const SCENARIO = {
          title: '学生版 AI 学习法 · 五步星图',
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

      /* ---------------- 布局：倾斜星盘 ---------------- */
      const gap = steps.length ? 360 / steps.length : 0;
      steps.forEach((s, i) => {
        const ang = -90 + i * gap;
        const rad = ang * RAD;
        const cos = Math.cos(rad), sin = Math.sin(rad);
        const r2 = RING[s.depth] + 30;
        s.ang = ang; s.idx = i; s.verified = true;
        s.x = CX + r2 * cos;
        s.y = CY + r2 * sin * SQUASH;
        s.dx = cos >= 0 ? 20 : -20;
        s.dy = 0;
        s.anchor = cos >= 0 ? 'start' : 'end';
      });

      /* 根据加载到的数据更新页面静态文案 */
      document.querySelector('.sm-title').textContent = SCENARIO.title + ' · 解决步骤星图';
      document.querySelector('.sm-sub').textContent = SCENARIO.sub || '';
      const coreSub = document.querySelector('.core-sub');
      if (coreSub) coreSub.textContent = SCENARIO.title;
      const coreNum = document.querySelector('.core-num');
      if (coreNum) coreNum.textContent = '已收录步骤 ★ ' + steps.length;
      const coreHint = document.querySelector('.core-hint');
      if (coreHint) coreHint.textContent = '点击查看场景拆解';
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
  
      // 轨道环（三层椭圆，ry = r*SQUASH）
      [1, 2, 3].forEach((d) => {
        orbitsG.appendChild(el('ellipse', { class: 'orbit', cx: CX, cy: CY, rx: RING[d], ry: (RING[d] * SQUASH).toFixed(1) }));
      });
  
      // 射线：太阳 → 每颗星
      steps.forEach((s) => {
        const line = el('line', { class: 'ray', stroke: STAR_ON, x1: CX, y1: CY, x2: s.x, y2: s.y });
        line.style.setProperty('--i', s.idx);
        raysG.appendChild(line);
        s._ray = line;
      });
  
      // 星
      steps.forEach((s) => {
        const g = el('g', { class: 'node', 'data-id': s.id });
        g.style.setProperty('--i', s.idx);
        const wrap = el('g', { transform: `translate(${s.x.toFixed(1)} ${s.y.toFixed(1)}) scale(1)` });
        const pop = el('g', { class: 'pop', style: '--s:1' });
        const hit = el('circle', { class: 'nhit', r: 24, fill: 'transparent' });
        pop.appendChild(hit);
        const ring = el('circle', { class: 'star-ring', r: 14, fill: 'none', stroke: STAR_ON, 'stroke-width': 1.4 });
        pop.appendChild(ring);
        const star = el('path', {
          class: 'star on', d: starPath(9.5, 4),
          fill: STAR_ON, stroke: STAR_ON, 'stroke-width': 0
        });
        pop.appendChild(star);
        wrap.appendChild(pop);
        const lbl = el('text', { class: 'lbl', x: s.dx.toFixed(1), y: s.dy.toFixed(1), 'text-anchor': s.anchor, 'dominant-baseline': 'central' });
        lbl.textContent = `第 ${s.id} 步 · ${s.title}`;
        wrap.appendChild(lbl);
        const det = el('text', { class: 'node-detail', x: s.dx.toFixed(1), y: (s.dy + 14).toFixed(1), 'text-anchor': s.anchor, 'dominant-baseline': 'central' });
        det.textContent = '已炼成 · 方法';
        wrap.appendChild(det);
        g.appendChild(wrap);
        nodesG.appendChild(g);
        nodePop[s.id] = pop;
        s._el = g;
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
          const w = nodePop[s.id].parentNode;
          w.setAttribute('transform', wrapT(s));
          const lbl = w.querySelector('.lbl'); lbl.setAttribute('transform', lblT(s));
          const det = w.querySelector('.node-detail'); det.setAttribute('transform', detT(s));
        });
        zoomtag.innerHTML = `${lodName()} · <b>${k.toFixed(1)}x</b>`;
        svg.classList.toggle('lod' + lod(), true);
        ['lod1', 'lod2', 'lod3'].forEach((c) => { if (c !== 'lod' + lod()) svg.classList.remove(c); });
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
        let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
        steps.forEach((n) => {
          const w = (`第 ${n.id} 步 · ${n.title}`).length * 11 + 12;
          const lx = n.x + n.dx + (n.anchor === 'start' ? 0 : n.anchor === 'end' ? -w : -w / 2);
          minX = Math.min(minX, Math.min(n.x - 13, lx - 4));
          maxX = Math.max(maxX, Math.max(n.x + 13, lx + w + 4));
          minY = Math.min(minY, n.y - 17);
          maxY = Math.max(maxY, n.y + 17);
        });
        const pad = 56;
        minX -= pad; maxX += pad; minY -= pad; maxY += pad;
        const raw = Math.min(900 / (maxX - minX), 790 / (maxY - minY));
        const nk = Math.min(Math.max(raw, KMIN), 1.45);
        const ntx = CX - ((minX + maxX) / 2) * nk;
        const nty = CY - ((minY + maxY) / 2) * nk;
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
          html += `<div class="kicker">${isOrigin ? '场景 · 基准处境（太阳）' : 'A1 · 场景拆解'}</div>`;
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
            html += `<div class="fb-row"><button class="back-btn" id="backSky">← 返回星空</button></div>`;
          } else {
            html += `<div class="sec">这张星图怎么读</div>`;
            html += `<p class="hint">
              正中这颗<b>太阳是当前场景</b>，外圈每颗<b>星是一个解决步骤</b>。<br />
              <b>实心蓝星</b>＝已炼成的方法。<br />
              星离太阳的<b>远近</b>（三层轨道环）＝要改多深：<b>改参数</b> → <b>动结构</b> → <b>换方案</b>。<br /><br />
              点一颗星，看这一步针对学生处境改了什么；每炼成一个，原帖价值 +1。
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
          <button class="back-btn" id="backSky">← 返回星空</button>
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
  
        html += `<div class="fb-row"><button class="back-btn" id="backSky2">← 返回星空</button></div>`;
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
  
      renderPanel();
      const entryStep = parseEntryStep();
      if (entryStep) playEntry(entryStep);
      else { fitView(false); playEnter(); }
      window.addEventListener('resize', () => setVP());
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
    html, body { height: 100%; }
    body {
      margin: 0;
      font-family: "PingFang SC", "Microsoft YaHei", "Helvetica Neue", Arial, sans-serif;
      background: #f6f6f6;
      color: var(--text);
      overflow: hidden;
    }
    .app { height: 100vh; display: flex; flex-direction: column; }

    /* 顶部条（对应原版 sm-head / sm-chips） */
    .sm-head {
      display: flex; align-items: center; gap: 12px;
      padding: 10px 14px; flex-wrap: wrap;
      background: #fff; border-bottom: 1px solid var(--border);
    }
    .sm-title { font-size: 15px; font-weight: 600; color: var(--text); margin: 0; }
    .sm-sub { font-size: 12px; color: var(--text-3); margin-left: 4px; }
    .sm-chips { display: flex; gap: 8px; overflow-x: auto; min-width: 0; }
    .sm-chips::-webkit-scrollbar { height: 0; }
    .chip {
      padding: 6px 12px; border: 1px solid var(--border); border-radius: 999px;
      background: var(--bg-2); color: var(--text-2); font-size: 12px;
      cursor: pointer; white-space: nowrap; font-family: inherit; transition: 0.16s;
    }
    .chip:hover { color: var(--zh-blue); border-color: var(--zh-blue-line-strong); background: var(--zh-blue-soft); }
    .chip.on { color: #fff; background: var(--zh-blue); border-color: var(--zh-blue); }
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

    /* 主体 */
    .sm-body { display: flex; gap: 12px; align-items: stretch; flex: 1; min-height: 0; padding: 12px; }
    .stage {
      position: relative; flex: 1; min-width: 0; min-height: 0;
      background: #fbfcfd; border: 1px solid var(--border); border-radius: 8px; overflow: hidden;
    }
    .web { width: 100%; height: 100%; display: block; cursor: grab; touch-action: none; }
    .web:active { cursor: grabbing; }

    .panel {
      width: 430px; flex: 0 0 430px; padding: 18px 20px; overflow-y: auto;
      background: var(--bg-2); border: 1px solid var(--border); border-radius: 8px;
    }
    .panel::-webkit-scrollbar { width: 6px; }
    .panel::-webkit-scrollbar-thumb { background: #dfe3e8; border-radius: 3px; }

    /* svg */
    .orbit { fill: none; stroke: #d5dbe4; stroke-width: 1; opacity: 0.75; stroke-dasharray: 3 7; }
    .ray { fill: none; stroke-width: 1.2; opacity: 0.5; }
    .ray.hot { opacity: 1; stroke-width: 1.6; }
    .node { cursor: pointer; }
    .pop { transform: scale(var(--s, 1)); transform-box: fill-box; transform-origin: center; transition: transform 0.2s cubic-bezier(0.34, 1.4, 0.64, 1); }
    .star { stroke-linejoin: round; }
    .nhit { pointer-events: all; cursor: pointer; }
    .star-ring { opacity: 0; transition: opacity .25s ease; pointer-events: none; }
    .node.on .star-ring { opacity: .55; }
    .lbl { font-size: 12.5px; font-weight: 500; fill: #1a1a1a; paint-order: stroke; stroke: #fbfcfd; stroke-width: 4.5; stroke-linejoin: round; transition: font-size 0.2s, opacity .4s ease; }
    .node.on .lbl { font-size: 14px; fill: var(--zh-blue); }
    .node-detail { font-size: 10.5px; fill: #8590a6; paint-order: stroke; stroke: #fbfcfd; stroke-width: 4; stroke-linejoin: round; transition: opacity .4s ease; }
    .core-sub { font-size: 15.5px; font-weight: 600; fill: #174a86; }
    .core-num { font-size: 13px; fill: var(--zh-blue); font-weight: 600; }
    .core-hint { font-size: 11px; fill: #8590a6; }
    .corehit { cursor: pointer; }
    .web.lod1 .node-detail { display: none; }
    .web.locked .node:not(.on) { opacity: 0.32; transition: opacity 0.34s ease; }
    .web.locked .node.on { opacity: 1 !important; }
    .web.locked .ray:not(.hot) { opacity: 0.08; }
    .web.locked .orbit { opacity: 0.16; }
    .web.locked .sun-glow { opacity: 0.3; }

    /* 从上一星图点击进入的转场 */
    .app.entrying .panel { opacity: 0; transform: translateX(30px); }
    .app.entrying .hintbar, .app.entrying .zoombar, .app.entrying .zoomtag { opacity: 0; }
    .panel { transition: opacity .55s ease, transform .55s cubic-bezier(.22,1,.36,1); }
    .app.entrying .hintbar, .app.entrying .zoombar, .app.entrying .zoomtag, .panel { transition: opacity .55s ease, transform .55s cubic-bezier(.22,1,.36,1); }
    .web.entry .orbit, .web.entry .ray:not(.hot), .web.entry .sun, .web.entry .node:not(.on) { opacity: 0; transition: opacity 1.05s ease; }
    .web.entry .node.on { opacity: 1; }
    .web.entry .node.on .lbl, .web.entry .node.on .node-detail { opacity: 0; transition: opacity .45s ease .7s; }
    .web.no-pop-trans .pop { transition: none !important; }

    /* 进场动画 */
    .web:not(.entered) .sun, .web:not(.entered) .node, .web:not(.entered) .ray, .web:not(.entered) .orbit { opacity: 0; }
    .web.entered .sun { transform-box: fill-box; transform-origin: center; animation: sunInStudent 0.7s cubic-bezier(0.22, 1, 0.36, 1) backwards; }
    .web.entered .orbit { animation: fadeInStudent 0.6s ease 0.12s backwards; }
    .web.entered .ray { animation: fadeInStudent 0.5s ease backwards; animation-delay: calc(var(--i, 0) * 0.05s + 0.28s); }
    .web.entered .node { animation: fadeInStudent 0.55s ease backwards; animation-delay: calc(var(--i, 0) * 0.05s + 0.3s); }
    @keyframes sunInStudent { from { opacity: 0; transform: scale(0.55); } to { opacity: 1; transform: scale(1); } }
    @keyframes fadeInStudent { from { opacity: 0; } to { opacity: 1; } }

    /* 浮层 */
    .hintbar {
      position: absolute; left: 14px; top: 12px; font-size: 11.5px; color: var(--text-3);
      line-height: 1.9; background: rgba(255,255,255,0.86); border: 1px solid var(--border);
      border-radius: 6px; padding: 8px 12px; max-width: 320px; pointer-events: none;
    }
    .hintbar b { color: var(--text-2); font-weight: 400; }
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

    /* 面板内容 */
    .pv-empty { color: var(--text-3); font-size: 13.5px; padding: 20px 0; }
    .kicker { font-size: 11.5px; letter-spacing: 1.5px; color: var(--zh-blue); font-weight: 500; }
    .p-title { font-size: 19px; font-weight: 600; margin: 8px 0 6px; line-height: 1.45; color: var(--text); }
    .p-origin { font-size: 13.5px; color: var(--text-2); margin: 0 0 10px; line-height: 1.8; }
    .p-origin.lead { color: var(--zh-blue); }
    .sub-line { color: var(--text-3); font-size: 12.5px; }
    .tags { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 10px; }
    .tag { font-size: 11.5px; color: var(--text-2); background: var(--surface-2); border: 1px solid var(--border); border-radius: 4px; padding: 3px 8px; }
    .stat-line { display: flex; gap: 10px; margin: 12px 0 4px; }
    .stat { flex: 1; background: var(--surface-2); border: 1px solid var(--border); border-radius: 6px; padding: 9px 11px; }
    .stat b { display: block; font-size: 20px; color: var(--zh-blue); line-height: 1.2; }
    .stat span { font-size: 11.5px; color: var(--text-3); }
    .sec { margin: 18px 0 8px; font-size: 12px; color: var(--text-3); letter-spacing: 1px; font-weight: 500; }
    .sub { font-size: 11.5px; color: var(--text-3); margin: 12px 0 4px; }
    .diff-tb { width: 100%; border-collapse: collapse; font-size: 12.5px; }
    .diff-tb th { text-align: left; color: var(--text-3); font-weight: 400; padding: 5px; border-bottom: 1px solid var(--border); }
    .diff-tb td { padding: 7px 5px; border-bottom: 1px solid var(--border); color: var(--text-2); vertical-align: top; line-height: 1.7; }
    .diff-tb td.dim { color: var(--text); white-space: nowrap; font-weight: 500; }
    .diff-tb td.mine { color: var(--zh-blue); }
    .moves { margin: 0; padding: 0; list-style: none; counter-reset: mv; }
    .moves li { position: relative; padding: 8px 0 8px 26px; font-size: 13px; color: var(--text-2); border-bottom: 1px solid var(--border); line-height: 1.75; }
    .moves li:last-child { border-bottom: 0; }
    .moves li::before {
      counter-increment: mv; content: counter(mv); position: absolute; left: 0; top: 10px;
      width: 16px; height: 16px; border-radius: 50%; background: var(--zh-blue-soft); color: var(--zh-blue);
      font-size: 10.5px; line-height: 16px; text-align: center; font-weight: 600;
    }
    .moves li b { display: block; color: var(--text); font-size: 12.5px; margin-bottom: 1px; }
    .moves .why { display: block; color: var(--text-3); font-size: 12px; margin-top: 2px; }
    .peer { font-size: 13px; color: var(--text-2); background: var(--surface-2); border: 1px solid var(--border); border-radius: 6px; padding: 10px 12px; margin-top: 12px; line-height: 1.75; }
    .peer b { color: var(--zh-blue); }
    .hint { font-size: 13px; color: var(--text-2); line-height: 1.95; }
    .hint b { color: var(--text); }
    .np-head { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }
    .verified { display: inline-flex; align-items: center; gap: 5px; font-size: 11.5px; padding: 3px 9px; border-radius: 4px; }
    .verified.ok { color: #0b7a4d; background: #e8f7f0; border: 1px solid #bfe6d3; }
    .verified.draft { color: #b8792a; background: #fef6e9; border: 1px solid #f6ddb6; }
    .back-btn { margin-left: auto; padding: 5px 11px; border: 1px solid var(--border); border-radius: 6px; background: var(--bg-2); color: var(--text-2); font-size: 12px; cursor: pointer; font-family: inherit; transition: 0.16s; }
    .back-btn:hover { color: var(--zh-blue); border-color: var(--zh-blue-line-strong); background: var(--zh-blue-soft); }
    .learn { background: #e8f7f0; border: 1px solid #bfe6d3; border-radius: 6px; padding: 11px 13px; font-size: 13px; color: #0b7a4d; line-height: 1.8; margin-top: 6px; }
    .learn b { color: #0b7a4d; }

    @media (max-width: 860px) {
      .sm-body { flex-direction: column; }
      .panel { width: 100%; flex: 0 0 auto; max-height: 46vh; }
      .stage { min-height: 46vh; }
      .sm-sub { display: none; }
    }
  
</style>
