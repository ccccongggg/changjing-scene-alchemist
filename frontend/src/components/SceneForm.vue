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
          :disabled="!speechSupported"
          @click="toggleVoice"
        >
          <svg v-if="!recording" class="scene__mic-icon" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z" />
            <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z" />
          </svg>
          <svg v-else class="scene__mic-icon" viewBox="0 0 24 24" fill="currentColor">
            <rect x="6" y="6" width="12" height="12" rx="2" />
          </svg>
          <span>{{ recording ? '停止' : speechSupported ? '点击开始语音输入' : '此浏览器不支持语音' }}</span>
        </button>
        <p
          class="scene__voice-tip"
          :class="{ 'scene__voice-tip--warn': !!speechMsg }"
          data-role="voice-tip"
        >
          <!-- 提示优先于「正在听」：超时兜底的那句话必须当场看见，不能被秒数盖住 -->
          <template v-if="speechMsg">{{ speechMsg }}</template>
          <template v-else-if="recording">正在听…已 {{ voiceSeconds }} 秒，说完停一下会自动结束</template>
          <template v-else-if="speechSupported">语音会先转成文字，再由 AI 整理成结构化场景</template>
          <template v-else>当前浏览器不支持语音输入（Chrome / Edge 可以）。请换文字或图片输入。</template>
        </p>
        <!-- 失败时不能只留一句报错：给一条能立刻继续的路，而且带着已识别到的文字一起走 -->
        <button
          v-if="speechMsg || !speechSupported"
          type="button"
          class="scene__voice-alt"
          id="voiceTextFallback"
          @click="useTextFallback"
        >
          改用文字输入 →
        </button>
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

/* ---------------- 语音输入 ----------------
   这一段踩过两个真实的坑，都是「点了没反应 / 第二次就再也不能用」的元凶：
   ① **失败是静默的**：SpeechRecognition 出错只触发 onerror，旧版只 console.warn，
      界面上一个字都不变 —— 用户体感就是「不能用」。而 Chrome 的识别走的是境外服务，
      国内网络下 network 失败相当常见，所以这个静默几乎必然被撞上。
   ② **复用同一个实例**：第一次失败后实例状态残留，再点 start() 会抛 InvalidStateError，
      于是一次失败 = 永久失效。
   所以这里三件事一起做：每次 start 重建实例 + 中文错误分类 + 失败时给一条能自救的下一步。*/
const recording = ref(false)
const speechSupported = ref(false)
const speechMsg = ref('')
const speechTone = ref('info') // info | warn
const voiceSeconds = ref(0)
let recognition = null
let voiceTimer = null
let voiceBase = ''
let voiceGotResult = false
let silenceTimer = null

/* 静默超时兜底 —— 这是「Chrome 里点了完全没反应」的真正解药。
   实测（本机 Chrome / Edge 各跑一次，喂同一段中文语音）：
     · Edge   → 10 秒内拿到结果并自动收尾，文字进了输入框；
     · Chrome → 一直停在「正在听」，**既不报错也不出字**（它的识别服务走境外，
                在这个网络下请求被静默挂住，onerror 都不触发）。
   也就是说 Chrome 的失败是「沉默的」，光靠 onerror 分类压根等不到。
   所以这里按时间兜底：15 秒还没有任何结果就把原因和出路直接写出来。 */
const armSilenceWatch = () => {
  if (silenceTimer) clearTimeout(silenceTimer)
  silenceTimer = setTimeout(() => {
    if (!recording.value || voiceGotResult) return
    speechTone.value = 'warn'
    speechMsg.value =
      '麦克风已经在收音，但 15 秒没等到识别结果 —— 如果你用的是 Chrome，多半是它的语音识别服务在你这个网络下连不上（它不会报错，只会没反应）。换成 Edge 打开通常立刻就能用；现在也可以直接把话打出来。'
  }, 15000)
}
const clearSilenceWatch = () => {
  if (silenceTimer) {
    clearTimeout(silenceTimer)
    silenceTimer = null
  }
}

/* 错误码 → 人话。带「下一步」是硬要求：只说「失败了」等于把用户扔在原地。 */
const SPEECH_ERR = {
  'not-allowed': '麦克风权限被拒绝了。点地址栏左边的图标 → 允许麦克风 → 再点一次；也可以直接用文字，AI 一样能整理。',
  'service-not-allowed': '浏览器把语音识别服务禁用了。换成 Edge 打开通常就好；或者直接用文字输入 —— AI 整理出的结构化场景是一样的。',
  network: '连不上浏览器的语音识别服务（Chrome 用的是境外服务，部分网络下确实用不了）。换 Edge 打开一般可以；现在就要继续的话，直接把话打出来，效果一样。',
  'no-speech': '没听到声音。靠近麦克风再说一次。',
  'audio-capture': '没有检测到麦克风设备，插上麦克风或改用文字输入。',
  aborted: ''
}

const stopTimer = () => {
  if (voiceTimer) {
    clearInterval(voiceTimer)
    voiceTimer = null
  }
}

const stopVoice = () => {
  stopTimer()
  clearSilenceWatch()
  try {
    if (recognition) recognition.stop()
  } catch (e) {
    /* 已经停了 */
  }
  recognition = null
  recording.value = false
}

/* 预检麦克风：把「没设备 / 权限被拒」和「识别服务连不上」分开 ——
   否则用户永远只看到同一句「不能用」，没法自救。拿到流立刻关掉，只为探权限。 */
const probeMic = async () => {
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) return true
  try {
    const s = await navigator.mediaDevices.getUserMedia({ audio: true })
    s.getTracks().forEach((t) => t.stop())
    return true
  } catch (e) {
    speechTone.value = 'warn'
    speechMsg.value =
      e && e.name === 'NotFoundError'
        ? '没有检测到麦克风设备。用文字输入也一样能被 AI 整理。'
        : '麦克风权限被拒绝了：点地址栏左边的图标 → 允许麦克风 → 再点一次。'
    return false
  }
}

const startVoice = async () => {
  speechMsg.value = ''
  speechTone.value = 'info'
  if (!(await probeMic())) return

  const SR = window.SpeechRecognition || window.webkitSpeechRecognition
  if (!SR) return
  recognition = new SR() // 每次新建：复用实例第二次点必炸
  recognition.lang = 'zh-CN'
  recognition.continuous = false // 单次识别比 continuous 稳，也会自动收尾
  recognition.interimResults = true
  recognition.maxAlternatives = 1
  voiceBase = rawText.value ? rawText.value.replace(/\s+$/, '') : ''

  recognition.onstart = () => {
    recording.value = true
    voiceSeconds.value = 0
    voiceGotResult = false
    armSilenceWatch()
    stopTimer()
    voiceTimer = setInterval(() => {
      voiceSeconds.value += 1
    }, 1000)
  }
  /* 中间结果也写进框里：用户得看见「字在长出来」，那才叫「在听」。 */
  recognition.onresult = (e) => {
    let interim = ''
    let fin = ''
    for (let i = e.resultIndex; i < e.results.length; i++) {
      const r = e.results[i]
      if (r.isFinal) fin += r[0].transcript
      else interim += r[0].transcript
    }
    if (fin || interim) {
      voiceGotResult = true
      clearSilenceWatch()
      if (speechMsg.value) {
        speechMsg.value = ''
        speechTone.value = 'info'
      }
    }
    if (fin) voiceBase = (voiceBase + ' ' + fin).trim()
    rawText.value = (voiceBase + ' ' + interim).trim()
  }
  recognition.onerror = (e) => {
    const code = e && e.error
    clearSilenceWatch()
    const msg = SPEECH_ERR[code]
    if (msg) {
      speechTone.value = 'warn'
      speechMsg.value = msg
    } else if (code && code !== 'aborted') {
      speechTone.value = 'warn'
      speechMsg.value = '语音识别出错了（' + code + '）。可以直接用文字输入。'
    }
    recording.value = false
    stopTimer()
  }
  recognition.onend = () => {
    recording.value = false
    stopTimer()
    clearSilenceWatch()
  }
  try {
    recognition.start()
  } catch (e) {
    try {
      recognition.stop()
    } catch (_) {
      /* ignore */
    }
    recognition = null
    speechTone.value = 'warn'
    speechMsg.value = '上一次识别还没结束，稍等一下再点一次。'
  }
}

const toggleVoice = () => {
  if (recording.value) stopVoice()
  else startVoice()
}

/* 「改用文字输入」：失败提示里那个按钮。带着已识别到的文字切过去，不丢东西。 */
const useTextFallback = () => {
  stopVoice()
  mode.value = 'text'
  speechMsg.value = ''
  speechTone.value = 'info'
}

// 浏览器语音能力检测（只做能力检测，实例在 startVoice 里现建）
if (typeof window !== 'undefined') {
  speechSupported.value = !!(window.SpeechRecognition || window.webkitSpeechRecognition)
}

const summarizing = ref(false)
const imageFile = ref(null)
const imagePreview = ref('')
const fileInput = ref(null)

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
  // 离开页面必须把麦克风收掉，否则录音指示灯会一直亮着
  stopVoice()
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
  background: var(--surface-2);
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
  background: var(--surface-2);
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
  /* 录音中要「看得出来它在工作」—— 没有这个反馈，用户会以为按钮坏了 */
  animation: micPulse 1.6s ease-in-out infinite;
}
@keyframes micPulse {
  0%,
  100% {
    box-shadow: 0 0 0 0 rgba(125, 137, 255, 0.35);
  }
  50% {
    box-shadow: 0 0 0 6px rgba(125, 137, 255, 0);
  }
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
  line-height: 1.6;
}
/* 失败提示：必须比普通提示更显眼，否则用户还是以为「点了没反应」 */
.scene__voice-tip--warn {
  color: #dbb46a;
}
.scene__voice-alt {
  align-self: flex-start;
  border: 1px solid var(--zh-blue-line-strong);
  background: var(--zh-blue-soft);
  color: var(--zh-blue);
  border-radius: var(--radius-sm);
  padding: 6px 12px;
  font-size: 12px;
  cursor: pointer;
  transition: background 0.2s ease;
}
.scene__voice-alt:hover {
  background: rgba(89, 103, 242, 0.14);
}
@media (prefers-reduced-motion: reduce) {
  .scene__mic--on {
    animation: none;
  }
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
  background: var(--surface-2);
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
  /* 触摸目标：输入方式切换加高到拇指可点的 44px 级别 */
  .scene__mode {
    padding: 10px 14px;
    font-size: 14px;
    min-height: 44px;
  }
  .scene__mic,
  .scene__ai {
    width: 100%;
    justify-content: center;
  }
  /* 麦克风按钮同样加高到 44px，录音时更好点 */
  .scene__mic {
    padding: 11px 16px;
    font-size: 15px;
  }
  .scene__mic-icon {
    width: 20px;
    height: 20px;
  }
  /* 降级按钮与场景 chips 也抬到可点高度 */
  .scene__voice-alt {
    padding: 9px 14px;
    font-size: 13px;
  }
  .lk-chip {
    padding: 6px 12px;
  }
  .scene__input {
    font-size: 16px; /* ≥16px：iOS 聚焦时不再自动放大页面 */
    padding: 10px 12px;
  }
}

/* ===== 小屏（手机）进一步收紧 ===== */
@media (max-width: 480px) {
  .scene {
    padding: 14px 12px;
  }
  .scene__image {
    min-height: 120px;
  }
  .scene__image-preview {
    max-height: 180px;
  }
  .scene__structured {
    padding: 12px;
  }
  /* 提示语较长（如语音超时兜底那段），小屏放宽行距保证读得清 */
  .scene__voice-tip {
    font-size: 12.5px;
    line-height: 1.65;
  }
}
</style>
