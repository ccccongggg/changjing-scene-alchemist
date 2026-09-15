<template>
  <div class="diff lk-card">
    <header class="diff__head">
      <span class="lk-badge">A2 · 差异分析</span>
    </header>

    <div class="diff__block">
      <h4 class="diff__title diff__title--ok">✅ 相同点</h4>
      <ul class="diff__same">
        <li v-for="(s, i) in data.same" :key="i">{{ s }}</li>
      </ul>
    </div>

    <div class="diff__block">
      <h4 class="diff__title diff__title--warn">⚠️ 差异点（原帖 ↔ 我的场景）</h4>
      <div class="diff__cards">
        <div v-for="(d, i) in data.diffs" :key="i" class="diff__card">
          <span class="diff__dim">{{ d.dimension }}</span>
          <div class="diff__pair">
            <div class="diff__cell">
              <span class="diff__cell-k">原帖</span>
              <p>{{ d.origin }}</p>
            </div>
            <div class="diff__cell diff__cell--mine">
              <span class="diff__cell-k">我的</span>
              <p>{{ d.mine }}</p>
            </div>
          </div>
          <p class="diff__impact">→ {{ d.impact }}</p>
        </div>
      </div>
    </div>

    <div class="diff__block">
      <h4 class="diff__title diff__title--done">✓ 已替你避开的坑</h4>
      <p class="diff__risk-hint">AI 已经在给你的方案里，把这些逐条改掉了。</p>
      <ul class="diff__risk">
        <li v-for="(r, i) in data.risks" :key="i">{{ r }}</li>
      </ul>
    </div>
  </div>
</template>

<script setup>
defineProps({ data: { type: Object, required: true } })
</script>

<style scoped>
.diff {
  padding: 22px;
  display: flex;
  flex-direction: column;
  gap: 18px;
}
.diff__title {
  font-size: 14px;
  font-weight: 700;
  margin: 0 0 10px;
}
.diff__title--ok {
  color: #43c6a6;
}
.diff__title--warn {
  color: var(--zh-blue);
}
.diff__title--done {
  color: #43c6a6;
}
.diff__risk-hint {
  margin: -4px 0 10px;
  font-size: 12.5px;
  line-height: 1.6;
  color: var(--text-3);
}
.diff__same,
.diff__risk {
  margin: 0;
  padding-left: 18px;
  color: var(--text-2);
  font-size: 13.5px;
  line-height: 1.8;
}
.diff__cards {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.diff__card {
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 14px 16px;
  background: var(--surface-2);
}
.diff__dim {
  display: block;
  font-size: 12.5px;
  font-weight: 700;
  color: var(--zh-blue);
  margin-bottom: 10px;
  letter-spacing: 0.4px;
}
.diff__pair {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}
.diff__cell {
  background: var(--bg-2);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 10px 12px;
}
.diff__cell--mine {
  border: 1px solid var(--zh-blue-line-strong);
}
.diff__cell-k {
  font-size: 11px;
  color: var(--text-3);
}
.diff__cell p {
  margin: 4px 0 0;
  font-size: 13px;
  line-height: 1.6;
  color: var(--text);
}
.diff__impact {
  margin: 10px 0 0;
  font-size: 12.8px;
  line-height: 1.6;
  color: var(--text-2);
}
@media (max-width: 560px) {
  .diff__pair {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 860px) {
  .diff {
    padding: 16px;
    gap: 16px;
  }
  .diff__card {
    padding: 12px;
  }
  .diff__same,
  .diff__risk {
    padding-left: 16px;
    line-height: 1.7;
  }
}

/* ===== 小屏（手机）：对比格堆叠后单栏全宽，字号微调 ===== */
@media (max-width: 480px) {
  .diff {
    padding: 14px 12px;
  }
  .diff__card {
    padding: 11px 10px;
  }
  .diff__cell p {
    font-size: 13.5px;
  }
  .diff__impact {
    font-size: 12.5px;
  }
}
</style>
