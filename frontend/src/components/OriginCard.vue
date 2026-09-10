<template>
  <div class="origin lk-card">
    <header class="origin__head">
      <span class="lk-badge">A1 · 原帖解构</span>
      <span class="origin__hint">AI 已自动拆解这篇帖子的真实场景</span>
    </header>

    <div class="origin__scene">
      <span class="origin__k">原场景</span>
      <p>{{ data.scene }}</p>
    </div>
    <div class="origin__scene">
      <span class="origin__k">核心解法</span>
      <p>{{ data.solution }}</p>
    </div>

    <div class="origin__cols">
      <div class="origin__col">
        <span class="origin__k">关键约束</span>
        <ul>
          <li v-for="(c, i) in data.constraints" :key="i">{{ c }}</li>
        </ul>
      </div>
      <div class="origin__col">
        <span class="origin__k">关键参数</span>
        <ul v-if="paramList.length">
          <li v-for="p in paramList" :key="p.k">{{ p.k }}：{{ p.v }}</li>
        </ul>
        <p v-else class="origin__muted">—</p>
      </div>
    </div>

    <div class="origin__boundary">
      <span class="origin__k">适用边界</span>
      <p>{{ data.boundaries }}</p>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
const props = defineProps({ data: { type: Object, required: true } })
const paramList = computed(() =>
  Object.entries(props.data.params || {}).map(([k, v]) => ({ k, v }))
)
</script>

<style scoped>
.origin {
  padding: 22px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.origin__head {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}
.origin__hint {
  font-size: 12.5px;
  color: var(--text-3);
}
.origin__k {
  display: block;
  font-size: 12px;
  font-weight: 700;
  color: var(--zh-blue);
  letter-spacing: 0.5px;
  margin-bottom: 6px;
}
.origin__scene p,
.origin__boundary p {
  margin: 0;
  font-size: 14.5px;
  line-height: 1.7;
  color: var(--text);
}
.origin__cols {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 18px;
}
.origin__col ul {
  margin: 0;
  padding-left: 18px;
  color: var(--text-2);
  font-size: 13.5px;
  line-height: 1.7;
}
.origin__muted {
  color: var(--text-3);
}
.origin__boundary {
  border-top: 1px solid var(--border);
  padding-top: 12px;
}
.origin__boundary p {
  color: var(--text-2);
}
@media (max-width: 600px) {
  .origin__cols {
    grid-template-columns: 1fr;
  }
}
</style>
