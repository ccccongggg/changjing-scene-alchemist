<template>
  <div :class="['bench', { 'bench--compact': props.mode === 'compact' }]">
    <div v-if="error" class="bench__error">{{ error }}</div>

    <template v-else>
      <div v-if="props.mode === 'page'" class="bench__top">
        <router-link to="/bench" class="bench__back">← 收藏台</router-link>
        <h1 v-if="source" class="bench__title">{{ source.title }}</h1>
        <span v-if="source" class="lk-chip lk-chip--muted">{{ typeLabel(source.content_type) }}</span>
      </div>

      <div v-if="phase === 'extracting'" class="bench__loading">
        <span class="bench__spinner" /> 解构原帖场景中…
      </div>

      <template v-else>
        <OriginCard v-if="origin && props.mode === 'page'" :data="origin" />

        <SceneForm v-if="phase === 'form'" :chips="demoChips" :running="phase === 'running'" @submit="onSubmit" />

        <div v-else-if="phase === 'running'" class="bench__loading">
          <span class="bench__spinner" /> {{ runStage }}
        </div>

        <template v-if="phase === 'result' && diff && solution">
          <div class="bench__net">
            已加入场景应用网 ✓ 这篇帖子现在有了你的真实解法
            <span class="bench__net-prov">· 由 {{ providerLabel }} 生成</span>
          </div>

          <section v-if="props.mode === 'page'" class="bench__graph lk-card">
            <h3 class="bench__graph-title">场景应用网 · 同帖千面</h3>
            <ScenarioGraph
              :post-title="source?.title"
              :scenarios="netScenarios"
              :current-id="currentId"
            />
          </section>

          <p v-if="notice" class="bench__notice">{{ notice }}</p>

          <DiffPanel :data="diff" />
          <SolutionPanel
            :key="adaptation?.id"
            :data="solution"
            :adaptation-id="adaptation?.id ?? null"
            @rediagnose="onRediagnose"
          />

          <div class="bench__ops">
            <button class="lk-btn lk-btn--primary" @click="reuse">
              {{ props.mode === 'compact' ? '换个场景再炼' : '换个场景再炼成（一帖两吃）' }}
            </button>
            <button class="lk-btn lk-btn--ghost" @click="copyAll">
              {{ copied ? '已复制' : '复制全文' }}
            </button>
            <router-link v-if="props.mode === 'page'" to="/library" class="lk-btn lk-btn--primary">
              存入方案库 ✓ 查看
            </router-link>
            <a
              v-if="props.mode === 'page' && source && source.url"
              :href="source.url"
              target="_blank"
              rel="noopener"
              class="lk-btn lk-btn--ghost"
            >
              打开原帖 ↗
            </a>
            <button v-if="props.mode === 'compact'" class="lk-btn lk-btn--ghost" @click="emit('close')">
              关闭
            </button>
          </div>
        </template>
      </template>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { getSource, extractAdapt, runAdapt, getAdaptations } from '../api'
import OriginCard from '../components/OriginCard.vue'
import SceneForm from '../components/SceneForm.vue'
import DiffPanel from '../components/DiffPanel.vue'
import SolutionPanel from '../components/SolutionPanel.vue'
import ScenarioGraph from '../components/ScenarioGraph.vue'

const props = defineProps({
  id: { type: [String, Number], required: true },
  mode: { type: String, default: 'page' } // 'page' | 'compact'
})
const emit = defineEmits(['created', 'close'])

const source = ref(null)
const origin = ref(null)
const diff = ref(null)
const solution = ref(null)
const adaptation = ref(null)
const phase = ref('extracting') // extracting | form | running | result
const error = ref('')
const copied = ref(false)
const netScenarios = ref([])
const currentId = ref(null)
const lastPayload = ref(null)   // 复诊要用：带着原场景再炼一版
const retryCount = ref(0)
const notice = ref('')

const STAGES = ['解构原帖场景…', '对比你的场景差异…', '生成专属迁移方案…']
const runStage = ref(STAGES[0])
let stageTimer = null

const typeLabel = (t) => (t === 'article' ? '文章' : t === 'answer' ? '回答' : '帖子')
const providerLabel = computed(() => {
  const p = adaptation.value?.provider
  return p === 'zhida' ? '知乎直答' : p === 'external' ? '备用模型' : '演示数据（Mock）'
})

// 一键场景：点一下填好整段，方便现场连跑两个场景做「一帖两吃」
const DEMO_CHIPS = {
  1: [
    {
      tag: '高速双串口',
      scene: '智能车竞赛，主控 MSPM0G3507，两个串口同时收摄像头（115200 持续流）和蓝牙（9600），数据不能丢。',
      constraint: '不能换主控，工期只有 3 天'
    },
    {
      tag: '电池水表低功耗',
      scene: '电池供电的远传水表，STM32L 系列，单串口接 MBus 通信模块，每天只上报几次，要求整机微安级休眠。',
      constraint: '成本敏感，不能加额外唤醒芯片'
    },
    {
      tag: 'RS485 现场总线',
      scene: '工厂车间一台主控通过 RS485 总线轮询 8 个从站，线长 300 米，旁边有变频器和继电器，误码时有发生。',
      constraint: '距离 300 米，干扰强，需免维护一个季度'
    }
  ],
  2: [
    {
      tag: '5A 电机电源板',
      scene: '智能车 4 层电源板，12V 输入、电机峰值 5A，内层走线 1oz 铜厚，空间紧张想尽量走细线。',
      constraint: '空间紧张，密闭车壳内散热差'
    }
  ],
  3: [
    {
      tag: '喷胶三轴龙门',
      scene: '工厂喷胶机小型三轴龙门，步进电机驱动、负载 1.5kg、行程 400mm。',
      constraint: '工厂连续作业，断电后位置不能丢'
    }
  ],
  // ↓ 生活类：全站统一用「学 AI 产品」这一个例子（一帖三吃）
  4: [
    {
      tag: '上班族版',
      scene: '我在上班，公司电脑不让装任何软件，只能用网页版，而且工作内容不能外传，只有午休 30 分钟。',
      constraint: '时间只有碎片，不能装软件，内容要脱敏'
    },
    {
      tag: '学生版',
      scene: '我是学生，只有免费额度，每天 20 次用完就得等明天，想拿它改论文、备考、讲错题。',
      constraint: '交上去要像自己写的，还得过查重'
    },
    {
      tag: '家长版',
      scene: '我是家长，完全零基础，「提示词」今天是第一次听说，想用它辅导孩子作业，但不想让它直接给答案。',
      constraint: '要孩子真的懂，不是答案到手；孩子容易跑题'
    }
  ]
}
const demoChips = computed(
  () =>
    DEMO_CHIPS[Number(props.id)] || [
      { tag: '换个器件', scene: '我用的器件和原帖不同，其余条件相近。', constraint: '' },
      { tag: '环境更苛刻', scene: '我的使用环境比原帖更苛刻（温度/干扰/负载更高）。', constraint: '' }
    ]
)

const load = async () => {
  phase.value = 'extracting'
  const pid = Number(props.id)
  try {
    const [s, ex] = await Promise.all([getSource(pid), extractAdapt(pid)])
    source.value = s
    origin.value = ex.origin
    phase.value = 'form'
  } catch (e) {
    error.value = '加载失败：' + (e?.message || e)
  }
}

const onSubmit = async (payload) => {
  phase.value = 'running'
  runStage.value = STAGES[0]
  lastPayload.value = { ...payload }
  retryCount.value = 0
  let i = 0
  stageTimer = setInterval(() => {
    i = (i + 1) % STAGES.length
    runStage.value = STAGES[i]
  }, 750)
  try {
    const res = await runAdapt({ post_id: Number(props.id), ...payload })
    origin.value = res.origin
    diff.value = res.diff
    solution.value = res.solution
    adaptation.value = res.adaptation
    phase.value = 'result'

    currentId.value = res.adaptation.id
    emit('created', res.adaptation)
    await refreshNet()
  } catch (e) {
    error.value = '生成失败：' + (e?.message || e)
    phase.value = 'form'
  } finally {
    clearInterval(stageTimer)
  }
}

const copyAll = async () => {
  if (!source.value || !adaptation.value) return
  const lines = [
    `原帖：${source.value.title}`,
    `原场景：${origin.value.scene}`,
    `核心解法：${origin.value.solution}`,
    '',
    `【我的场景】${adaptation.value.user_scene}`,
    `【我的约束】${adaptation.value.user_constraint || '（无）'}`,
    '',
    '【差异】',
    ...diff.value.diffs.map((d) => `· ${d.dimension}：原帖「${d.origin}」 / 我的「${d.mine}」 → ${d.impact}`),
    '',
    '【迁移方案】',
    ...solution.value.steps.map((s) => `${s.step}. ${s.action}（why: ${s.why}）`),
    '',
    solution.value.summary
  ]
  try {
    await navigator.clipboard.writeText(lines.join('\n'))
    copied.value = true
    setTimeout(() => (copied.value = false), 1500)
  } catch (e) {
    /* 剪贴板不可用时静默 */
  }
}

const refreshNet = async () => {
  const all = await getAdaptations()
  netScenarios.value = (all || [])
    .filter((a) => a.post_id === Number(props.id))
    .map((a) => ({ id: a.id, scene_tag: a.scene_tag, user_scene: a.user_scene }))
}

// 复诊：带着同一段场景，避开已经走过的路，再炼一版
const onRediagnose = async ({ avoid = [] }) => {
  if (!lastPayload.value) return
  phase.value = 'running'
  runStage.value = '换一条路，基于你的约束重新设计…'
  retryCount.value += 1
  const tag = lastPayload.value.scene_tag || '我的场景'
  try {
    const res = await runAdapt({
      ...lastPayload.value,
      scene_tag: `${tag} · 第 ${retryCount.value + 1} 版`,
      avoid,
      parent_id: adaptation.value?.id ?? null
    })
    origin.value = res.origin
    diff.value = res.diff
    solution.value = res.solution
    adaptation.value = res.adaptation
    phase.value = 'result'
    currentId.value = res.adaptation.id
    await refreshNet()
  } catch (e) {
    phase.value = 'result'
    notice.value = '换路这一步没连上，方案还是刚才那版——再点一次试试。'
    setTimeout(() => (notice.value = ''), 4000)
  }
}

const reuse = () => {
  diff.value = null
  solution.value = null
  adaptation.value = null
  lastPayload.value = null
  retryCount.value = 0
  phase.value = 'form'
}

onMounted(load)
onUnmounted(() => stageTimer && clearInterval(stageTimer))
</script>

<style scoped>
.bench {
  max-width: 860px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 20px;
}
.bench--compact {
  max-width: none;
  margin: 0;
  gap: 14px;
}
.bench--compact .bench__loading {
  padding: 28px 16px;
}
.bench--compact .bench__ops {
  padding: 4px 0 0;
  justify-content: flex-start;
}
.bench__top {
  display: flex;
  align-items: center;
  gap: 14px;
  flex-wrap: wrap;
}
.bench__back {
  font-size: 13px;
  color: var(--text-2);
  transition: color 0.2s ease;
}
.bench__back:hover {
  color: var(--zh-blue);
}
.bench__title {
  font-size: clamp(20px, 2.6vw, 28px);
  font-weight: 800;
  letter-spacing: -0.3px;
  margin: 0;
  color: var(--text);
}
.bench__loading {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 40px;
  justify-content: center;
  color: var(--text-2);
  font-size: 14px;
  border: 1px dashed var(--border-strong);
  border-radius: var(--radius);
  background: var(--surface);
}
.bench__spinner {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  border: 2px solid var(--border-strong);
  border-top-color: var(--zh-blue);
  animation: lk-spin 0.8s linear infinite;
}
@keyframes lk-spin {
  to {
    transform: rotate(360deg);
  }
}
.bench__net {
  text-align: center;
  font-size: 13px;
  color: var(--zh-blue);
  background: var(--zh-blue-soft);
  border: 1px solid var(--zh-blue-line);
  border-radius: 999px;
  padding: 9px 16px;
  align-self: center;
}
.bench__net-prov {
  color: var(--text-3);
  font-size: 12px;
}
.bench__ops {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  justify-content: center;
  padding: 8px 0 12px;
}
.bench__notice {
  font-size: 13px;
  line-height: 1.7;
  color: var(--text-2);
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 10px 14px;
}
.bench__error {
  padding: 40px;
  text-align: center;
  color: #ff5a4d;
  border: 1px solid rgba(255, 90, 77, 0.4);
  border-radius: var(--radius);
  background: var(--surface);
}

@media (max-width: 860px) {
  .bench {
    gap: 14px;
  }
  .bench__top {
    gap: 10px;
  }
  .bench__title {
    font-size: 20px;
    width: 100%;
  }
  .bench__loading {
    padding: 28px 16px;
  }
  .bench__net {
    border-radius: 10px;
    text-align: left;
    line-height: 1.6;
  }
  /* 操作按钮在窄屏堆叠成全宽，方便拇指点击 */
  .bench__ops {
    flex-direction: column;
    align-items: stretch;
    gap: 10px;
  }
  .bench__ops .lk-btn {
    width: 100%;
    justify-content: center;
  }
}
</style>
