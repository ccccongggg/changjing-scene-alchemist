<template>
  <div class="fb">
    <header class="fb__head">
      <span class="lk-badge">结果回填</span>
      <span v-if="stage === 'done'" class="fb__head-note">已完成</span>
    </header>

    <!-- 时刻 0｜还没试：问一句 -->
    <template v-if="stage === 'idle'">
      <p class="fb__ask">这个方案，在你那儿跑通了吗？</p>
      <div class="fb__row">
        <button class="lk-btn lk-btn--primary" @click="markDone">做成了 ✓</button>
        <button class="lk-btn lk-btn--ghost" @click="stage = 'pick'">卡住了</button>
      </div>
      <p class="fb__hint">
        不论哪种，都会留在这篇帖子的场景应用网上——后来的人不用从头撞一遍墙。
      </p>
    </template>

    <!-- 时刻 1｜卡住了：选卡点（全文不出现「失败」） -->
    <template v-else-if="stage === 'pick'">
      <p class="fb__ask">卡点了？告诉 AI 卡在哪一步——是报错，还是现象和预期不符？</p>

      <div class="fb__chips-block">
        <span class="fb__chips-label">卡在第几步</span>
        <div class="fb__chips">
          <button
            v-for="s in steps"
            :key="s.step"
            class="fb__chip"
            @click="pick('step_error', s.step)"
          >
            第 {{ s.step }} 步报错
          </button>
        </div>
      </div>

      <div class="fb__chips-block">
        <span class="fb__chips-label">或者</span>
        <div class="fb__chips">
          <button class="fb__chip" @click="pick('phenomenon', null)">现象和预期不符</button>
          <button class="fb__chip" @click="pick('other', null)">其他</button>
        </div>
      </div>

      <p class="fb__reassure">别急。排除一个方向，也是进展。</p>
    </template>

    <!-- 追问：AI 只问一句，但问到点上 -->
    <template v-else-if="stage === 'ask'">
      <p v-if="ask.lead" class="fb__lead">{{ ask.lead }}</p>
      <p class="fb__question">{{ ask.question }}</p>
      <textarea
        v-model="note"
        class="fb__input"
        rows="3"
        :placeholder="ask.placeholder"
        @keyup.ctrl.enter="send"
      />
      <div class="fb__row">
        <button
          class="lk-btn lk-btn--primary"
          :disabled="!note.trim() || loading"
          @click="send"
        >
          {{ loading ? '正在归因…' : '发送' }}
        </button>
        <button class="lk-btn lk-btn--ghost" @click="backToPick">换个卡点</button>
      </div>
      <p class="fb__reassure">{{ ask.reassure }}</p>
    </template>

    <!-- 时刻 2/3｜归因结论：用户看见的是棋盘，不是墙 -->
    <template v-else-if="stage === 'verdict'">
      <p v-if="v.lead" class="fb__lead">{{ v.lead }}</p>

      <div class="fb__verdict">
        <span class="fb__attr">{{ v.attribution_label }}</span>
        <p class="fb__headline">{{ v.headline }}</p>
        <p class="fb__detail">{{ v.detail }}</p>
      </div>

      <div class="fb__learned">
        <span class="fb__learned-k">我们学到了什么</span>
        <p>{{ v.learned }}</p>
      </div>

      <div class="fb__board">
        <div class="fb__board-row">
          <span class="fb__board-k fb__board-k--out">✗ 已排除</span>
          <ul class="fb__board-list">
            <li v-for="(x, i) in v.excluded" :key="'e' + i">{{ x }}</li>
          </ul>
        </div>
        <div class="fb__board-row">
          <span class="fb__board-k fb__board-k--in">→ 剩余可试</span>
          <ul class="fb__board-list">
            <li v-for="(x, i) in v.remaining" :key="'r' + i">{{ x }}</li>
          </ul>
        </div>
      </div>

      <template v-if="v.note">
        <p class="fb__note">{{ v.note }}</p>
        <p v-if="v.pending" class="fb__pending">{{ v.pending }}</p>
      </template>

      <div class="fb__row">
        <button
          class="lk-btn lk-btn--primary"
          :disabled="loading"
          @click="onNext"
        >
          {{ v.next.label }}
        </button>
        <span class="fb__next-hint">{{ v.next.hint }}</span>
      </div>
    </template>

    <!-- 做成了 -->
    <template v-else-if="stage === 'done'">
      <p class="fb__done-title">{{ doneMsg.title }}</p>
      <p class="fb__ask">{{ doneMsg.message }}</p>
      <p class="fb__hint">{{ doneMsg.sub }}</p>
    </template>

    <p v-if="error" class="fb__err">
      {{ error }}
      <button class="fb__retry" @click="error = ''">知道了</button>
    </p>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { submitFeedback } from '../api'

const props = defineProps({
  adaptationId: { type: Number, required: true },
  steps: { type: Array, default: () => [] }
})
const emit = defineEmits(['rediagnose'])

const stage = ref('idle') // idle | pick | ask | verdict | done
const note = ref('')
const loading = ref(false)
const error = ref('')
const ask = ref({ question: '', placeholder: '', reassure: '', lead: '' })
const v = ref(null)
const doneMsg = ref({ title: '', message: '', sub: '' })
let picked = { block_type: null, block_step: null }

const guard = async (fn) => {
  if (loading.value) return
  loading.value = true
  error.value = ''
  try {
    await fn()
  } catch (e) {
    // 不写「失败」——只说没连上，并给一个立刻可做的动作
    error.value = '这一步没连上服务器，你的话还在，再发一次就行。'
  } finally {
    loading.value = false
  }
}

const markDone = () =>
  guard(async () => {
    const r = await submitFeedback(props.adaptationId, { result: 'done' })
    doneMsg.value = { title: r.title, message: r.message, sub: r.sub }
    stage.value = 'done'
  })

const pick = (blockType, step) =>
  guard(async () => {
    picked = { block_type: blockType, block_step: step }
    const r = await submitFeedback(props.adaptationId, {
      result: 'stuck',
      block_type: blockType,
      block_step: step
    })
    ask.value = r
    stage.value = 'ask'
  })

const backToPick = () => {
  note.value = ''
  stage.value = 'pick'
}

const send = () =>
  guard(async () => {
    const r = await submitFeedback(props.adaptationId, {
      result: 'stuck',
      block_type: picked.block_type,
      block_step: picked.block_step,
      user_note: note.value.trim()
    })
    v.value = r
    note.value = ''
    stage.value = 'verdict'
  })

const onNext = () => {
  const n = v.value?.next || {}
  if (n.type === 'retry') {
    emit('rediagnose', { avoid: v.value.avoid || [] })
  } else {
    // 补信息：回到追问，再排一轮——永远有下一步
    guard(async () => {
      const r = await submitFeedback(props.adaptationId, {
        result: 'stuck',
        block_type: picked.block_type,
        block_step: picked.block_step
      })
      ask.value = r
      stage.value = 'ask'
    })
  }
}
</script>

<style scoped>
.fb {
  border-top: 1px dashed var(--border-strong);
  padding-top: 18px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.fb__head {
  display: flex;
  align-items: center;
  gap: 10px;
}
.fb__head-note {
  font-size: 12px;
  color: var(--text-3);
}
.fb__ask {
  margin: 0;
  font-size: 14.5px;
  font-weight: 600;
  color: var(--text);
  line-height: 1.7;
}
.fb__hint {
  margin: 0;
  font-size: 12.5px;
  color: var(--text-3);
  line-height: 1.7;
}
.fb__reassure {
  margin: 0;
  font-size: 13px;
  color: var(--text-2);
  line-height: 1.7;
}
.fb__row {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}
.fb__next-hint {
  font-size: 12.5px;
  color: var(--text-3);
}

/* 卡点选择 */
.fb__chips-block {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.fb__chips-label {
  font-size: 12px;
  color: var(--text-3);
}
.fb__chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.fb__chip {
  font: inherit;
  font-size: 13px;
  color: var(--text-2);
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: 999px;
  padding: 7px 14px;
  cursor: pointer;
  transition: all 0.18s ease;
}
.fb__chip:hover {
  color: var(--zh-blue);
  border-color: var(--zh-blue-line-strong);
  background: var(--zh-blue-soft);
}

/* 追问 */
.fb__lead {
  margin: 0;
  font-size: 13.5px;
  line-height: 1.8;
  color: var(--text-2);
  background: var(--surface-2);
  border-left: 3px solid var(--zh-blue);
  border-radius: 0 8px 8px 0;
  padding: 10px 14px;
}
.fb__question {
  margin: 0;
  font-size: 14px;
  line-height: 1.75;
  color: var(--text);
}
.fb__input {
  width: 100%;
  font: inherit;
  font-size: 14px;
  line-height: 1.7;
  color: var(--text);
  background: #fff;
  border: 1px solid var(--border-strong);
  border-radius: 10px;
  padding: 12px 14px;
  resize: vertical;
  box-sizing: border-box;
}
.fb__input:focus {
  outline: none;
  border-color: var(--zh-blue);
  box-shadow: 0 0 0 3px var(--zh-blue-soft);
}

/* 结论 */
.fb__verdict {
  background: var(--zh-blue-soft);
  border: 1px solid var(--zh-blue-line-strong);
  border-radius: 12px;
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.fb__attr {
  align-self: flex-start;
  font-size: 11.5px;
  font-weight: 700;
  color: #fff;
  background: var(--zh-blue);
  border-radius: 5px;
  padding: 2px 8px;
}
.fb__headline {
  margin: 0;
  font-size: 14.5px;
  font-weight: 700;
  color: var(--text);
  line-height: 1.6;
}
.fb__detail {
  margin: 0;
  font-size: 13px;
  line-height: 1.75;
  color: var(--text-2);
}
.fb__learned {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.fb__learned-k {
  align-self: flex-start;
  font-size: 11px;
  font-weight: 700;
  color: var(--zh-blue);
  border: 1px solid var(--zh-blue-line-strong);
  border-radius: 5px;
  padding: 1px 7px;
}
.fb__learned p {
  margin: 0;
  font-size: 13.5px;
  line-height: 1.75;
  color: var(--text);
}

/* 棋盘：已排除 / 剩余可试 */
.fb__board {
  border: 1px solid var(--border);
  border-radius: 12px;
  overflow: hidden;
}
.fb__board-row {
  display: flex;
  gap: 12px;
  padding: 12px 14px;
}
.fb__board-row + .fb__board-row {
  border-top: 1px solid var(--border);
}
.fb__board-k {
  flex: none;
  font-size: 12.5px;
  font-weight: 700;
  padding-top: 1px;
}
.fb__board-k--out {
  color: var(--text-3);
}
.fb__board-k--in {
  color: var(--zh-blue);
}
.fb__board-list {
  margin: 0;
  padding: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.fb__board-list li {
  font-size: 13px;
  line-height: 1.65;
  color: var(--text-2);
}
.fb__board-row:first-child .fb__board-list li {
  color: var(--text-3);
  text-decoration: line-through;
  text-decoration-color: var(--border-strong);
}

.fb__note {
  margin: 0;
  font-size: 13.5px;
  line-height: 1.85;
  color: var(--text);
  background: var(--surface-2);
  border-radius: 12px;
  padding: 14px 16px;
}
.fb__pending {
  margin: 0;
  font-size: 12.5px;
  line-height: 1.7;
  color: var(--text-3);
}
.fb__done-title {
  margin: 0;
  font-size: 15px;
  font-weight: 700;
  color: var(--zh-blue);
}

.fb__err {
  margin: 0;
  font-size: 12.5px;
  color: var(--text-2);
  display: flex;
  align-items: center;
  gap: 10px;
}
.fb__retry {
  font: inherit;
  font-size: 12.5px;
  color: var(--zh-blue);
  background: none;
  border: none;
  padding: 0;
  cursor: pointer;
}

@media (max-width: 860px) {
  .fb {
    padding-top: 14px;
    gap: 12px;
  }
  .fb__row {
    gap: 10px;
  }
  .fb__row .lk-btn {
    flex: 1;
    justify-content: center;
    min-width: 120px;
  }
  .fb__next-hint {
    width: 100%;
  }
  .fb__board-row {
    flex-direction: column;
    gap: 8px;
  }
}
</style>
