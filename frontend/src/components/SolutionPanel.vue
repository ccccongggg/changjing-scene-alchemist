<template>
  <div class="sol lk-card">
    <header class="sol__head">
      <span class="lk-badge">A3 · 方案迁移</span>
    </header>

    <div class="sol__summary">{{ data.summary }}</div>

    <p v-if="data.switch" class="sol__switch">{{ data.switch }}</p>

    <ol class="sol__steps">
      <li v-for="s in data.steps" :key="s.step" class="sol__step">
        <span class="sol__no">{{ s.step }}</span>
        <div class="sol__body">
          <p class="sol__action">{{ s.action }}</p>
          <p class="sol__why">
            <span class="sol__why-k">why</span>{{ s.why }}
            <span v-if="s.ref" class="sol__ref">↩ {{ s.ref }}</span>
          </p>
        </div>
      </li>
    </ol>

    <pre v-if="data.code" class="sol__code"><code>{{ data.code }}</code></pre>

    <!-- 结果回填：做成了 / 卡住了 → 复诊闭环 -->
    <FeedbackPanel
      v-if="adaptationId"
      :adaptation-id="adaptationId"
      :steps="data.steps || []"
      @rediagnose="$emit('rediagnose', $event)"
    />
  </div>
</template>

<script setup>
import FeedbackPanel from './FeedbackPanel.vue'

defineProps({
  data: { type: Object, required: true },
  adaptationId: { type: Number, default: null }
})
defineEmits(['rediagnose'])
</script>

<style scoped>
.sol {
  padding: 22px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.sol__summary {
  background: var(--zh-blue-soft);
  border: 1px solid var(--zh-blue-line-strong);
  border-radius: 12px;
  padding: 14px 16px;
  font-size: 14px;
  line-height: 1.7;
  color: var(--text);
}
.sol__switch {
  margin: 0;
  font-size: 12.5px;
  line-height: 1.6;
  color: var(--zh-blue);
  background: var(--zh-blue-soft);
  border: 1px solid var(--zh-blue-line);
  border-radius: 999px;
  padding: 7px 14px;
  align-self: flex-start;
}
.sol__steps {
  margin: 0;
  padding: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.sol__step {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}
.sol__no {
  flex: none;
  width: 26px;
  height: 26px;
  border-radius: 50%;
  background: var(--zh-blue);
  color: #ffffff;
  font-weight: 800;
  font-size: 13px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.sol__body {
  flex: 1;
}
.sol__action {
  margin: 0;
  font-size: 14px;
  line-height: 1.6;
  color: var(--text);
}
.sol__why {
  margin: 4px 0 0;
  font-size: 12.8px;
  line-height: 1.6;
  color: var(--text-2);
}
.sol__why-k {
  display: inline-block;
  font-size: 10.5px;
  font-weight: 700;
  color: var(--zh-blue);
  border: 1px solid var(--zh-blue-line-strong);
  border-radius: 5px;
  padding: 0 5px;
  margin-right: 6px;
}
.sol__ref {
  display: inline-block;
  margin-left: 8px;
  color: var(--zh-blue);
  cursor: default;
}
.sol__code {
  margin: 0;
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 14px 16px;
  font-size: 12.5px;
  line-height: 1.6;
  color: var(--text);
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  font-family: "SFMono-Regular", Consolas, "Liberation Mono", monospace;
}

@media (max-width: 860px) {
  .sol {
    padding: 16px;
    gap: 14px;
  }
  .sol__summary {
    padding: 12px 14px;
    font-size: 13.5px;
    border-radius: 8px;
  }
  .sol__switch {
    border-radius: 8px;
    line-height: 1.7;
  }
  .sol__step {
    gap: 10px;
  }
  .sol__no {
    width: 24px;
    height: 24px;
    font-size: 12px;
  }
  .sol__action {
    font-size: 13.5px;
  }
  .sol__code {
    font-size: 12px;
    padding: 12px;
  }
}

/* ===== 小屏（手机）===== */
@media (max-width: 480px) {
  .sol {
    padding: 14px 12px;
  }
  .sol__summary {
    font-size: 13px;
  }
  .sol__code {
    font-size: 11.5px;
    padding: 10px;
    /* 长代码行在手机上可以横向滑，但不能撑破卡片 */
    max-width: 100%;
  }
}
</style>
