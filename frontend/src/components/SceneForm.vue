<template>
  <div class="scene lk-card">
    <header class="scene__head">
      <span class="lk-badge">② 我的场景</span>
      <span class="scene__hint">点一下 / 贴一段 / 说两句 / 拍一张，都行</span>
    </header>

    <!-- 选项：一键填好整段场景 -->
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

    <!-- 输入方式切换 -->
    <div class="scene__modes" role="tablist">
      <button
        v-for="m in MODES"
        :key="m.key"
        type="button"
        class="scene__mode"
        :class="{ 'scene__mode--on': mode === m.key }"
        :aria-selected="mode === m.key"
        @click="mode = m.key"
      >
        {{ m.label }}
      </button>
    </div>

    <!-- 文字输入 -->
    <template v-if="mode === 'text'">
      <div class="scene__row">
        <button class="scene__paste" type="button" @click="pasteInfer">
          粘贴代码 / 报错，AI 反推场景
        </button>
      </div>
      <textarea
        v-model="rawText"
        class="scene__ta"
        rows="3"
        placeholder="描述你的真实场景：硬件 / 环境 / 目标……随便说，AI 会帮你整理成结构化描述"
      />
    </template>

    <!-- 语音输入 -->
    <template v-if="mode === 'voice'">
      <div class="scene__voice">
        <button
          type="button"
          class="scene__mic"
          :class="{ 'scene__mic--on': recording }"
          :disabled="!speechReady"
          @click="toggleVoice"
        >
          <svg v-if="!recording" class="scene__mic-icon" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z" />
            <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z" />
          </svg>
          <svg v-else class="scene__mic-icon" viewBox="0 0 24 24" fill="currentColor">
            <rect x="6" y="6" width="12" height="12" rx="2" />
          </svg>
          <span>{{ recording ? '停止录音' : '点击开始语音输入' }}</span>
        </button>
        <p class="scene__voice-tip">
          {{ recording ? '正在听，请说话…' : speechReady ? '语音会先转成文字，再由 AI 整理成结构化场景' : '当前浏览器不支持语音输入，请换文字或图片' }}
        </p>
      </div>
      <textarea
        v-model="rawText"
        class="scene__ta"
        rows="3"
        placeholder="语音转写会出现在这里，你也可以直接修改…"
      />
    </template>

    <!-- 图片输入 -->
    <template v-if="mode === 'image'">
      <div
        class="scene__image"
        tabindex="0"
        @click="openFile"
        @dragover.prevent
        @drop.prevent="onDrop"
        @paste="onPaste"
      >
        <input
          ref="fileInput"
          type="file"
          accept="image/*"
          class="scene__file"
          @change="onFileChange"
        />
        <img v-if="imagePreview" :src="imagePreview" class="scene__image-preview" />
        <div v-else class="scene__image-placeholder">
          <svg class="scene__image-icon" viewBox="0 0 24 24" fill="currentColor">
            <path d="M21 19V5c0-1.1-.9-2-2-2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2zM8.5 13.5l2.5 3.01L14.5 12l4.5 6H5l3.5-4.5z" />
          </svg>
          <div>点击上传、拖拽或粘贴图片</div>
          <div class="scene__image-sub">AI 会尝试从图中识别处境（演示版，识别结果请核对）</div>
        </div>
      </div>
      <textarea
        v-if="imageFile || rawText"
        v-model="rawText"
        class="scene__ta scene__ta--sm"
        rows="2"
        placeholder="图片识别结果会出现在这里，请核对编辑…"
      />
    </template>

    <!-- AI 整理按钮 -->
    <button
      v-if="canSummarize"
      type="button"
      class="lk-btn lk-btn--ghost scene__ai"
      :disabled="summarizing"
      @click="summarize(mode === 'image' ? 'image' : mode === 'voice' ? 'voice' : 'text')"
    >
      <span class="scene__ai-spin" v-if="summarizing" />
      {{ summarizeLabel }}
    </button>

    <!-- 结构化结果（可编辑） -->
    <div v-if="scene" class="scene__structured">
      <div class="scene__field">
        <label class="scene__label">场景标签</label>
        <input v-model="sceneTag" class="scene__input" placeholder="如：上班族版 / 学生版" />
      </div>
      <div class="scene__field">
        <label class="scene__label">真实处境</label>
        <textarea v-model="scene" class="scene__ta" rows="3" placeholder="AI 整理后的场景描述，可直接编辑" />
      </div>
      <div class="scene__field">
        <label class="scene__label">额外约束</label>
        <textarea
          v-model="constraint"
          class="scene__ta scene__ta--sm"
          rows="2"
          placeholder="负载 / 预算 / 时间 / 不能改的零件……"
        />
      </div>
    </div>

    <div class="scene__foot">
      <span class="scene__tip">无强制必填，越具体 AI 迁移越准</span>
      <button
        class="lk-btn lk-btn--primary"
        type="button"
        :disabled="!scene.trim() || running"
        @click="submit"
      >
        {{ running ? '生成中…' : '生成我的解决方案' }} <span class="arrow">→</span>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onUnmounted } from 'vue'
import { summarizeScene } from '../api'

const props = defineProps({
  // 一键场景：[{ tag, scene, constraint }]
  chips: { type: Array, default: () => [] },
  // 父组件跑方案时的 loading 状态
  running: { type: Boolean, default: false }
})
const emit = defineEmits(['submit'])

const MODES = [
  { key: 'text', label: '文字输入' },
  { key: 'voice', label: '语音输入' },
  { key: 'image', label: '图片输入' }
]

const mode = ref('text')
const rawText = ref('')
const scene = ref('')
const constraint = ref('')
const sceneTag = ref('')

const recording = ref(false)
const speechReady = ref(false)
let recognition = null

const summarizing = ref(false)
const imageFile = ref(null)
const imagePreview = ref('')
const fileInput = ref(null)

// 浏览器语音能力检测
if (typeof window !== 'undefined') {
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition
  if (SR) {
    speechReady.value = true
    recognition = new SR()
    recognition.lang = 'zh-CN'
    recognition.continuous = true
    recognition.interimResults = true
    recognition.onresult = (e) => {
      let final = ''
      for (let i = e.resultIndex; i < e.results.length; i++) {
        const r = e.results[i]
        if (r.isFinal) final += r[0].transcript
      }
      if (final) rawText.value = (rawText.value + final).trim()
    }
    recognition.onerror = (e) => {
      console.warn('语音识别出错', e.error)
      recording.value = false
    }
    recognition.onend = () => {
      recording.value = false
    }
  }
}

const canSummarize = computed(() => {
  if (mode.value === 'image') return !!imageFile.value || rawText.value.trim().length > 0
  return rawText.value.trim().length > 0
})

const summarizeLabel = computed(() => {
  if (summarizing.value) return 'AI 整理中…'
  if (mode.value === 'image') return 'AI 识别图片场景'
  return 'AI 整理为结构化场景'
})

const fill = (c) => {
  sceneTag.value = c.tag
  scene.value = c.scene || c.tag
  constraint.value = c.constraint || ''
  rawText.value = ''
  mode.value = 'text'
}

const pasteInfer = () => {
  rawText.value =
    '我手上的是同系列但主频更高的板子，现场还要同时驱动一块 HMI 屏，担心串口在高负载下丢帧。'
  // 自动整理成结构化场景
  summarize('text')
}

const summarize = async (inputType) => {
  if (!rawText.value.trim() && inputType !== 'image') return
  summarizing.value = true
  try {
    const payload = {
      raw: rawText.value || imageFile.value?.name || '图片场景',
      input_type: inputType,
      hint: sceneTag.value || undefined
    }
    const res = await summarizeScene(payload)
    if (res) {
      sceneTag.value = res.scene_tag || sceneTag.value
      scene.value = res.user_scene || rawText.value
      constraint.value = res.user_constraint || ''
    }
  } catch (e) {
    console.error('AI 整理失败', e)
    // 降级：直接把原文作为场景
    scene.value = rawText.value
  } finally {
    summarizing.value = false
  }
}

const toggleVoice = () => {
  if (!recognition) return
  if (recording.value) {
    recognition.stop()
    recording.value = false
  } else {
    try {
      recognition.start()
      recording.value = true
    } catch (e) {
      console.warn('启动语音失败', e)
    }
  }
}

const openFile = () => {
  fileInput.value?.click()
}

const handleImageFile = (file) => {
  if (!file || !file.type.startsWith('image/')) return
  imageFile.value = file
  imagePreview.value = URL.createObjectURL(file)
  rawText.value = `已上传图片：${file.name}`
}

const onFileChange = (e) => {
  handleImageFile(e.target.files?.[0])
}

const onDrop = (e) => {
  handleImageFile(e.dataTransfer.files?.[0])
}

const onPaste = (e) => {
  const items = e.clipboardData?.items
  if (!items) return
  for (const item of items) {
    if (item.type.startsWith('image/')) {
      const file = item.getAsFile()
      handleImageFile(file)
      break
    }
  }
}

const submit = () => {
  emit('submit', {
    user_scene: scene.value,
    user_constraint: constraint.value,
    scene_tag: sceneTag.value
  })
}

onUnmounted(() => {
  if (recognition && recording.value) {
    try {
      recognition.stop()
    } catch (e) {
      // ignore
    }
  }
  if (imagePreview.value) {
    URL.revokeObjectURL(imagePreview.value)
  }
})
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

/* 选项 chips */
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
  color: #ffffff;
  border-color: var(--zh-blue);
}

/* 输入方式切换 */
.scene__modes {
  display: inline-flex;
  background: var(--surface-2);
  border-radius: var(--radius);
  padding: 4px;
  gap: 4px;
  align-self: flex-start;
}
.scene__mode {
  border: none;
  background: transparent;
  color: var(--text-2);
  padding: 6px 14px;
  border-radius: var(--radius-sm);
  font-size: 13px;
  cursor: pointer;
  transition: background 0.2s ease, color 0.2s ease;
}
.scene__mode:hover {
  color: var(--zh-blue);
}
.scene__mode--on {
  background: #ffffff;
  color: var(--zh-blue);
  box-shadow: var(--shadow);
}

/* AI 反推 */
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

/* 文本域 */
.scene__ta {
  width: 100%;
  resize: vertical;
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
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

/* AI 整理按钮 */
.scene__ai {
  align-self: flex-start;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.scene__ai-spin {
  width: 14px;
  height: 14px;
  border: 2px solid var(--zh-blue-line);
  border-top-color: var(--zh-blue);
  border-radius: 50%;
  animation: ai-spin 0.8s linear infinite;
}
@keyframes ai-spin {
  to {
    transform: rotate(360deg);
  }
}

/* 语音输入 */
.scene__voice {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.scene__mic {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  align-self: flex-start;
  border: 1px solid var(--border-strong);
  background: #ffffff;
  color: var(--text-2);
  border-radius: 999px;
  padding: 8px 16px;
  font-size: 14px;
  cursor: pointer;
  transition: border-color 0.2s ease, color 0.2s ease, background 0.2s ease;
}
.scene__mic:hover:not(:disabled) {
  border-color: var(--zh-blue);
  color: var(--zh-blue);
}
.scene__mic--on {
  background: var(--zh-blue-soft);
  border-color: var(--zh-blue);
  color: var(--zh-blue);
}
.scene__mic:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}
.scene__mic-icon {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
}
.scene__voice-tip {
  margin: 0;
  font-size: 12px;
  color: var(--text-3);
}

/* 图片输入 */
.scene__image {
  position: relative;
  min-height: 140px;
  border: 1.5px dashed var(--border-strong);
  border-radius: var(--radius-lg);
  background: var(--surface-2);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  transition: border-color 0.2s ease, background 0.2s ease;
  outline: none;
}
.scene__image:hover,
.scene__image:focus {
  border-color: var(--zh-blue);
  background: var(--zh-blue-soft);
}
.scene__file {
  position: absolute;
  inset: 0;
  opacity: 0;
  cursor: pointer;
}
.scene__image-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  color: var(--text-2);
  font-size: 14px;
  pointer-events: none;
  padding: 20px;
  text-align: center;
}
.scene__image-sub {
  font-size: 12px;
  color: var(--text-3);
}
.scene__image-icon {
  width: 32px;
  height: 32px;
  color: var(--text-3);
}
.scene__image-preview {
  max-width: 100%;
  max-height: 240px;
  object-fit: contain;
  border-radius: var(--radius);
}

/* 结构化结果 */
.scene__structured {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 14px;
  background: var(--surface-2);
  border-radius: var(--radius-lg);
}
.scene__field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.scene__label {
  font-size: 12.5px;
  color: var(--text-3);
  font-weight: 500;
}
.scene__input {
  width: 100%;
  background: #ffffff;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 9px 12px;
  font-size: 14px;
  color: var(--text);
  font-family: inherit;
}
.scene__input:focus {
  outline: none;
  border-color: var(--zh-blue-line-strong);
}

/* 底部 */
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

@media (max-width: 860px) {
  .scene {
    padding: 16px;
    gap: 12px;
  }
  .scene__hint {
    font-size: 12px;
    line-height: 1.5;
  }
  .scene__paste {
    width: 100%;
    padding: 10px 12px;
  }
  .scene__ta {
    font-size: 16px;
    padding: 11px 12px;
  }
  .scene__ta--sm {
    font-size: 15px;
  }
  .scene__foot {
    flex-direction: column;
    align-items: stretch;
    gap: 10px;
  }
  .scene__foot .lk-btn {
    width: 100%;
    justify-content: center;
  }
  .scene__modes {
    width: 100%;
    justify-content: center;
  }
  .scene__mic,
  .scene__ai {
    width: 100%;
    justify-content: center;
  }
}
</style>
