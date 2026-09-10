<template>
  <div class="scene lk-card">
    <header class="scene__head">
      <span class="lk-badge">② 我的场景</span>
      <span class="scene__hint">三态低门槛输入 · 点一下 / 贴一段 / 随便说两句都行</span>
    </header>

    <!-- ② 选 chip 起头：一点即填好整段场景（演示「一帖两吃」） -->
    <div v-if="chips.length" class="scene__chips">
      <button
        v-for="c in chips"
        :key="c.tag"
        type="button"
        class="lk-chip"
        :class="{ 'lk-chip--on': sceneTag === c.tag }"
        @click="fill(c)"
      >
        {{ c.tag }}
      </button>
    </div>

    <!-- ① 粘贴即懂 -->
    <div class="scene__row">
      <button class="scene__paste" type="button" @click="pasteInfer">
        粘贴代码 / 报错，AI 反推场景
      </button>
    </div>

    <textarea
      v-model="scene"
      class="scene__ta"
      rows="3"
      placeholder="描述你的真实场景：硬件 / 环境 / 目标……例如「STM32F407 接称重模块，波特率提到 115200，还要跑 HMI 屏」"
    />

    <textarea
      v-model="constraint"
      class="scene__ta scene__ta--sm"
      rows="2"
      placeholder="额外约束（可选）：负载 / 预算 / 时间 / 不能改的零件……"
    />

    <div class="scene__foot">
      <span class="scene__tip">无强制必填，越具体 AI 迁移越准</span>
      <button class="lk-btn lk-btn--primary" type="button" @click="submit">
        生成我的解决方案 <span class="arrow">→</span>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
const props = defineProps({
  // 一键场景：[{ tag, scene, constraint }] —— 一点即填好整段，方便连跑两个场景做「一帖两吃」
  chips: { type: Array, default: () => [] }
})
const emit = defineEmits(['submit'])

const scene = ref('')
const constraint = ref('')
const sceneTag = ref('')

const fill = (c) => {
  sceneTag.value = c.tag
  scene.value = c.scene || c.tag
  constraint.value = c.constraint || ''
}

const pasteInfer = () => {
  sceneTag.value = 'AI 反推'
  scene.value =
    '我手上的是同系列但主频更高的板子，现场还要同时驱动一块 HMI 屏，担心串口在高负载下丢帧。'
}

const submit = () => {
  emit('submit', {
    user_scene: scene.value,
    user_constraint: constraint.value,
    scene_tag: sceneTag.value
  })
}
</script>

<style scoped>
.scene {
  padding: 22px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.scene__head {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}
.scene__hint {
  font-size: 12.5px;
  color: var(--text-3);
}
.scene__row {
  display: flex;
}
.scene__paste {
  background: var(--surface-2);
  border: 1px dashed var(--border-strong);
  color: var(--text-2);
  border-radius: 10px;
  padding: 9px 14px;
  font-size: 13px;
  cursor: pointer;
  transition: border-color 0.2s ease, color 0.2s ease;
}
.scene__paste:hover {
  border-color: var(--zh-blue-line-strong);
  color: var(--zh-blue);
}
.scene__chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.lk-chip {
  cursor: pointer;
  transition: transform 0.15s ease;
}
.lk-chip:hover {
  transform: translateY(-1px);
}
.lk-chip--on {
  background: var(--zh-blue);
  color: #2a1d08;
  border-color: var(--zh-blue);
}
.scene__ta {
  width: 100%;
  resize: vertical;
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 12px 14px;
  color: var(--text);
  font-family: inherit;
  font-size: 14px;
  line-height: 1.6;
}
.scene__ta:focus {
  outline: none;
  border-color: var(--zh-blue-line-strong);
}
.scene__ta--sm {
  font-size: 13px;
}
.scene__foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}
.scene__tip {
  font-size: 12px;
  color: var(--text-3);
}
.scene__foot .arrow {
  transition: transform 0.25s ease;
}
.lk-btn--primary:hover .arrow {
  transform: translateX(3px);
}
</style>
