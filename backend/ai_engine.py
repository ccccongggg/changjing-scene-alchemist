"""适配引擎：A1 解构 / A2 差异 / A3 方案迁移。

双通道：
- **Mock 通道**（默认，USE_MOCK=true）：按「原帖领域 × 我的场景类型」分支产出 canned 方案，
  保证「一帖两吃」——同一篇串口帖，高速并发与电池低功耗走出完全不同的解法（演示永不翻车）。
- **真实通道**（USE_MOCK=false + 配好密钥）：走知乎直答 / 备用 OpenAI 兼容模型，
  prompts/ 下三个 prompt 依次产出 A1/A2/A3；任何失败自动降级回 Mock，界面不留白。

返回结构与 provider 一路回写到 adaptations 表，界面小标签体现真实接入。
"""

import copy
import json
from functools import lru_cache

from config import effective_provider

# ---------------------------------------------------------------------------
# 领域识别（A1 用什么模板 / A2A3 走哪套分支）
# ---------------------------------------------------------------------------
TYPE_KEYWORDS = {
    "embed": ["串口", "STM32", "DMA", "中断", "电子秤", "收发", "字节", "UART", "单片机"],
    "pcb": ["PCB", "线宽", "铜厚", "电流", "布线", "电源", "oz", "覆铜", "走线"],
    "robot": ["机械臂", "逆解", "舵机", "运动学", "六轴", "Arduino", "关节", "龙门", "步进"],
}


def _detect_type(post) -> str:
    text = f"{post.title} {post.summary or ''}"
    for t, kws in TYPE_KEYWORDS.items():
        if any(k in text for k in kws):
            return t
    return "generic"


# ---------------------------------------------------------------------------
# A1 解构模板（描摹原帖：作者的场景 / 解法 / 约束 / 参数 / 边界）
# ---------------------------------------------------------------------------
ORIGIN_TEMPLATES = {
    "embed": {
        "scene": "STM32F103 电子秤项目，单路 USART 以 9600 接称重传感器模块，主控边收边处理。",
        "solution": "用 DMA + 串口空闲中断（IDLE）一次性收完整帧，再在回调里做帧解析，避免逐字节中断拼帧丢数据。",
        "constraints": ["单串口，无第二路 USART 可用", "9600 波特率，高负载时易丢字节", "主控还要处理称重与显示"],
        "params": {"baud": "9600", "mcu": "STM32F103", "frame": "一帧 ≤ 32 字节"},
        "boundaries": "仅适用于「定长/带帧尾、可靠有线串口」；无线串口、多设备并发或需硬件流控的场景需另做处理。",
    },
    "pcb": {
        "scene": "12V/2A 控制板电源走线，1oz 铜厚，按 IPC-2221 经验估算线宽。",
        "solution": "取 20mil 走线承载 2A，关键路径加铺铜/开窗加锡，过孔不少于 2 个并联降低温升。",
        "constraints": ["1oz 铜厚", "12V 输入、峰值 2A", "板面积受限，不能无限加宽"],
        "params": {"current": "2A", "copper": "1oz", "width": "20mil"},
        "boundaries": "经验值适用于短走线、常温、外层；大电流（>5A）、内层走线或高温环境需用 IPC 公式重算。",
    },
    "robot": {
        "scene": "桌面 6 自由度舵机机械臂，做逆运动学把末端目标位姿解算成各关节角。",
        "solution": "用几何法/解析法求逆解，Arduino 驱动舵机，负载约 200g，离线算好角度表查表执行。",
        "constraints": ["舵机扭矩有限，负载 200g", "6 自由度存在多解需选解", "Arduino 算力有限，不宜在线迭代"],
        "params": {"dof": 6, "load": "200g", "driver": "Arduino + 舵机"},
        "boundaries": "适用于轻负载定点作业；若负载变大、机构从旋转关节变成直角坐标，或要求轨迹平滑，需换解法。",
    },
    "generic": {
        "scene": "原帖描述了一个工程/技术问题及其解决过程。",
        "solution": "作者给出了一套可落地的解决思路与关键注意点。",
        "constraints": ["原帖约束见正文", "方案依赖特定环境与前提"],
        "params": {},
        "boundaries": "通用经验，迁移到新场景需重新核对前提。",
    },
}


# ---------------------------------------------------------------------------
# A2+A3 场景分支（「一帖两吃」的差异度来源）
# 每条 mine/impact/action 可含 {scene} / {constraint} 占位符，渲染时替换
# ---------------------------------------------------------------------------
SCENE_BRANCHES = {
    "embed": {
        # —— 场景 A：高速并发双串口 ——————————————————————————————
        "highspeed": {
            "keywords": ["高速", "115200", "并发", "双串口", "两路", "摄像头", "智能车", "图像", "多机", "持续流", "DMA", "不丢帧"],
            "same": [
                "要解决的问题本质相同：串口数据不能丢，必须收整帧再解析。",
                "「DMA + 空闲中断收整帧」这个核心思路对你依然成立，只是要翻倍用。",
            ],
            "diffs": [
                {
                    "dimension": "设备数量 / 通道",
                    "origin": "单路 USART，只接一个称重模块",
                    "mine": "多路串口并发：{scene}",
                    "impact": "单缓冲 + 单中断会被第二路抢占，A 路帧没收完就被 B 路打断 → 帧断裂。",
                },
                {
                    "dimension": "速率 / 吞吐",
                    "origin": "9600 bps，间歇小包（≤32 字节）",
                    "mine": "115200 bps 级别的持续流",
                    "impact": "逐字节中断 ≈ 11.5k 次/秒，CPU 被中断吃满，必然丢字节。",
                },
                {
                    "dimension": "可靠性要求",
                    "origin": "偶发丢一帧可接受（称重值可重采样）",
                    "mine": "连续流，丢帧即画面/控制断裂",
                    "impact": "必须加溢出（ORE）恢复与帧同步重搜，否则一次溢出后串口永久卡死。",
                },
                {
                    "dimension": "供电 / 散热",
                    "origin": "市电或 USB 常供电，不敏感",
                    "mine": "{constraint}",
                    "impact": "可以放心用 DMA 换 CPU 空闲，不必为省电牺牲实时性。",
                },
                {
                    "dimension": "工期 / 维护",
                    "origin": "长周期项目，可慢慢调",
                    "mine": "工期紧，要求一次调通",
                    "impact": "优先用 HAL 库成熟路径（DMA + IDLE），不自己写协议状态机。",
                },
            ],
            "risks": [
                "直接照搬「逐字节中断拼帧」：115200 下字节间隔仅 87µs，主循环来不及取走就被覆盖，稳定丢帧。",
                "两路共用一个接收缓冲区：两路数据交叉写入，帧边界彻底错乱。",
                "在中断里做协议解析：ISR 过长导致另一路溢出（ORE）。",
                "忘记清 ORE 标志：溢出后串口锁死，表现为「收一会儿就不收了」，最难排查。",
            ],
            "steps": [
                {
                    "step": 1,
                    "action": "双串口资源分治：摄像头路 UART0 @115200 8N1、蓝牙路 UART1 @9600 8N1，各配 256 字节独立环形缓冲，物理隔离永不共用。",
                    "why": "对应差异【设备数量 / 通道】，隔离后两路不再互相抢占缓冲区。",
                    "ref": "设备数量 / 通道",
                },
                {
                    "step": 2,
                    "action": "摄像头路改 DMA 循环接收 + IDLE 空闲中断：HAL_UARTEx_ReceiveToIdle_DMA 循环写缓冲，IDLE 判定整帧，主循环整帧取走；关掉 DMA 半传输中断，只在整帧时处理。",
                    "why": "对应差异【速率 / 吞吐】，中断频率从「每字节一次」降到「每帧一次」，降一个数量级。",
                    "ref": "速率 / 吞吐",
                },
                {
                    "step": 3,
                    "action": "中断只入队、解析放主循环：ISR 内只做 ring_push + 重启 DMA，控制在 20µs 内；禁止在 ISR 里拼协议、打印、做浮点。",
                    "why": "对应差异【速率 / 吞吐】，缩短 ISR 才能给另一路留出响应时间。",
                    "ref": "速率 / 吞吐",
                },
                {
                    "step": 4,
                    "action": "加 ORE 溢出兜底：实现 HAL_UART_ErrorCallback，检测到 HAL_UART_ERROR_ORE 时 __HAL_UART_CLEAR_OREFLAG 并重启 DMA 接收。",
                    "why": "对应差异【可靠性要求】，防止一次溢出后串口永久锁死。",
                    "ref": "可靠性要求",
                },
                {
                    "step": 5,
                    "action": "帧同步重搜与看门狗：超时 200ms 未收到合法帧头则重置 DMA 指针重新搜头；主循环 1s 内无数据则软复位串口。",
                    "why": "对应差异【可靠性要求】，连续流场景必须能自恢复。",
                    "ref": "可靠性要求",
                },
                {
                    "step": 6,
                    "action": "压测标定缓冲深度：115200 持续流下，主循环最长阻塞不得超过 256B/11520Bps ≈ 22ms；不够就把缓冲提到 512B。",
                    "why": "对应差异【速率 / 吞吐】，用量化窗口反推缓冲大小，不靠拍脑袋。",
                    "ref": "速率 / 吞吐",
                },
            ],
            "code": """// 场景 A：双串口并发 —— DMA 循环 + IDLE 整帧，各路独立环形缓冲
#define RX0_BUF 256
static uint8_t rx0[RX0_BUF];

void uart0_start(void) {
  HAL_UARTEx_ReceiveToIdle_DMA(&huart0, rx0, RX0_BUF);
  __HAL_DMA_DISABLE_IT(hdma_uart0_rx, DMA_IT_HT);   // 关半传输，只在整帧处理
}

// 整帧到达：只入队，不解析
void HAL_UARTEx_RxEventCallback(UART_HandleTypeDef *huart, uint16_t Size) {
  if (huart->Instance == USART0) {
    ring_push(&r0, rx0, Size);
    HAL_UARTEx_ReceiveToIdle_DMA(&huart0, rx0, RX0_BUF);   // 立即重启
  }
}

// 溢出兜底：不清 ORE 串口会锁死
void HAL_UART_ErrorCallback(UART_HandleTypeDef *huart) {
  if (huart->ErrorCode & HAL_UART_ERROR_ORE) {
    __HAL_UART_CLEAR_OREFLAG(huart);
    HAL_UARTEx_ReceiveToIdle_DMA(&huart0, rx0, RX0_BUF);
  }
}

// 主循环：缓冲 256B @115200 ≈ 22ms 窗口，阻塞不得超时
for (;;) { while ((n = ring_pop(&r0, tmp))) parse_frame(tmp, n); }""",
            "summary": "关键改动：单中断逐字节拼帧 → 双路独立缓冲 + DMA 循环 + IDLE 整帧 + ORE 自恢复。原帖的「DMA 收整帧」思路保留，但从一个串口变成两个独立管道，并把中断频率从每字节降到每帧，同时对连续流补上溢出自恢复——这三点都是「并发 + 高速」逼出来的。",
        },
        # —— 场景 B：电池供电低功耗 ————————————————————————————
        "lowpower": {
            "keywords": ["低功耗", "电池", "水表", "MBus", "M-Bus", "休眠", "微安", "uA", "µA", "功耗", "待机", "唤醒", "供电", "远传", "NB", "LoRa"],
            "same": [
                "要解决的问题本质相同：串口数据不能丢，必须收整帧再解析。",
                "「DMA + 空闲中断收整帧」的机制本身仍然可用，但只能开在通信的那几十毫秒里。",
            ],
            "diffs": [
                {
                    "dimension": "供电方式",
                    "origin": "市电或 USB 常供电，从不考虑电流",
                    "mine": "电池供电，要求整机微安级休眠：{scene}",
                    "impact": "串口常开 RX 是最耗电的外设之一，必须改成「按需开启」，这是所有改法的根。",
                },
                {
                    "dimension": "通信频次",
                    "origin": "持续/高频接收称重数据",
                    "mine": "每天仅上报几次，其余时间总线空闲",
                    "impact": "99% 的时间串口无事可做，常开接收纯属浪费，可安全进入深度休眠。",
                },
                {
                    "dimension": "波特率取舍",
                    "origin": "取 9600 是为了兼容与稳定",
                    "mine": "应反过来算：让 RX 开启窗口最短，而非波特率最低",
                    "impact": "提高波特率反而更省电——窗口缩短 4 倍，唤醒期能耗同步下降。",
                },
                {
                    "dimension": "唤醒机制",
                    "origin": "无休眠设计，主循环 while 收数据",
                    "mine": "需 MCU 深度休眠 + RTC/外部中断唤醒",
                    "impact": "必须用 LPUART 的 RXNE 唤醒或 RTC 定时唤醒，不能靠主循环轮询。",
                },
                {
                    "dimension": "成本 / 器件",
                    "origin": "可加隔离、稳压、额外收发器",
                    "mine": "{constraint}",
                    "impact": "不能加专用唤醒芯片，应尽量用 MCU 内部 LPUART + RTC 解决。",
                },
            ],
            "risks": [
                "直接照搬 DMA 循环接收：DMA 需要时钟常开，MCU 进不了 STOP，整机电流从 µA 掉到 mA 级，电池几天就没。",
                "照搬 9600 不改：收一帧的窗口更长，唤醒时间翻倍，电池寿命直接腰斩。",
                "忽略 MBus 模块的上电建立时间：唤醒后立刻发指令会丢掉开头几个字节。",
                "忘记关串口时钟 / 未用引脚浮空：休眠期间引脚漏电可悄悄吃掉几十 µA，比通信本身还费电。",
            ],
            "steps": [
                {
                    "step": 1,
                    "action": "把「常开接收」改成「事件驱动上报」：RTC 定时唤醒（如每天 2 次）或外部中断触发，其余时间 MCU 进 STOP/Standby，串口彻底关时钟。",
                    "why": "对应差异【供电方式】，休眠电流是电池寿命的第一决定项。",
                    "ref": "供电方式",
                },
                {
                    "step": 2,
                    "action": "用 LPUART + RXNE 唤醒（或唤醒后再开 DMA 收一帧即关）：只有真正要通信时才初始化串口，收完立刻 HAL_UART_DeInit。",
                    "why": "对应差异【唤醒机制】，LPUART 可在 STOP 下保持唤醒能力且功耗极低。",
                    "ref": "唤醒机制",
                },
                {
                    "step": 3,
                    "action": "波特率按「窗口最短」重新取值：MBus 常用 2400 8E1；若模块支持 9600 则用 9600 缩短窗口，收完马上关 RX，别纠结「越低越省」。",
                    "why": "对应差异【波特率取舍】，能耗 = 电流 × 时间，缩短时间比降低速率更有效。",
                    "ref": "波特率取舍",
                },
                {
                    "step": 4,
                    "action": "加收发建立等待：唤醒后先拉高模块使能脚，HAL_Delay(10~20ms) 等模块电源稳定，再发指令、再收帧。",
                    "why": "对应差异【通信频次】，频次低意味着每次都是冷启动，必须留建立时间。",
                    "ref": "通信频次",
                },
                {
                    "step": 5,
                    "action": "堵住休眠漏电：未用 GPIO 全部设为模拟输入，关闭串口/ADC 时钟，禁止上拉电阻跨电源；休眠前逐个量一遍电流。",
                    "why": "对应差异【成本 / 器件】，不靠加硬件，靠把现有引脚管干净。",
                    "ref": "成本 / 器件",
                },
                {
                    "step": 6,
                    "action": "做电流预算并实测：目标休眠 < 5µA、上报峰值 8mA × 0.2s/次，日均 ≈ 0.3mAh，据此反推电池容量与更换周期。",
                    "why": "对应差异【供电方式】，用量化预算验证方案而不是靠感觉。",
                    "ref": "供电方式",
                },
            ],
            "code": """// 场景 B：电池远传水表 —— 休眠 → 定时唤醒 → 开串口收一帧 → 立刻睡
void enter_stop(void) {
  HAL_UART_DeInit(&hlpuart1);                 // 关串口时钟，防休眠漏电
  GPIO_AllUnused_ToAnalog();                  // 未用引脚设模拟输入，堵漏电
  HAL_RTCEx_SetWakeUpTimer_IT(&hrtc, 12 * 3600, RTC_WAKEUPCLOCK_CK_SPRE);
  HAL_PWR_EnterSTOPMode(PWR_LOWPOWERREGULATOR_ON, PWR_STOPENTRY_WFI);
}

void report_once(void) {
  MX_LPUART1_UART_Init();                     // 2400/9600 8E1（MBus 常用）
  MBUS_ENABLE_HIGH();
  HAL_Delay(10);                              // 等模块上电建立，否则丢前几字节
  HAL_UART_Transmit(&hlpuart1, req, sizeof(req), 100);
  HAL_UARTEx_ReceiveToIdle(&hlpuart1, rx, sizeof(rx), 500);  // 只收一帧
  parse_and_store(rx);
  HAL_UART_DeInit(&hlpuart1);                 // 收完立刻关，别留时钟
  enter_stop();
}

// 电流预算：3.5µA × 86400s + 8mA × 0.2s × 2次/天 ≈ 0.30 mAh/天
// ER14505 锂亚电池 2400mAh → 理论 > 10 年，实际按 60% 折损仍 > 6 年""",
            "summary": "关键改动：从「DMA 常开循环接收」翻转为「深度休眠 + 按需唤醒、收一帧即关」，并把波特率从「越低越好」改成「让 RX 窗口最短」。原帖的 DMA+IDLE 只在每天那 200 毫秒里用一次，整机从 mA 级降到 µA 级——这正是低功耗场景与高速并发场景走出完全相反方向的原因。",
        },
        # —— 场景 C：工业现场长线/干扰 ——————————————————————————
        "noisy": {
            "keywords": ["干扰", "RS485", "RS-485", "长线", "长距离", "Modbus", "modbus", "工业", "现场", "隔离", "误码", "总线", "从站", "轮询", "终端电阻"],
            "same": [
                "要解决的问题本质相同：串口数据不能丢，必须收整帧再解析。",
                "「DMA + 空闲中断判定帧尾」的思路仍然可用——只是帧尾判定要靠超时兜底。",
            ],
            "diffs": [
                {
                    "dimension": "物理层 / 电平",
                    "origin": "板内 TTL 单端、距离 < 20cm",
                    "mine": "工业现场长线差分总线：{scene}",
                    "impact": "必须加 RS485 收发器与终端电阻，TTL 直连会烧片且通信全错。",
                },
                {
                    "dimension": "抗干扰 / 误码",
                    "origin": "实验室洁净环境，误码率视为 0",
                    "mine": "现场存在变频器/继电器干扰，误码不可避免",
                    "impact": "必须有 CRC 校验 + 超时重传，否则错误数据会被当成正确值执行。",
                },
                {
                    "dimension": "拓扑结构",
                    "origin": "点对点单从设备",
                    "mine": "一主多从总线，半双工",
                    "impact": "需要地址寻址、轮询调度，以及 DE/RE 收发方向切换。",
                },
                {
                    "dimension": "波特率 / 距离",
                    "origin": "9600，距离不构成约束",
                    "mine": "距离与波特率必须权衡：{constraint}",
                    "impact": "波特率越高可跑距离越短（9600≈1200m / 115200≈100m），需按距离反选。",
                },
                {
                    "dimension": "安全 / 隔离",
                    "origin": "无隔离，共地无风险",
                    "mine": "现场共地环流与浪涌风险真实存在",
                    "impact": "需隔离收发器 + TVS/PTC，否则一次浪涌就烧一路串口。",
                },
            ],
            "risks": [
                "照搬 TTL 直连：RS485 是差分电平，直连不仅通信失败，还可能直接烧毁 MCU 串口引脚。",
                "忘记终端电阻：长线信号反射，波特率一高就整帧乱码，且现象随线长变化、极难定位。",
                "半双工方向切换时机不对：发送刚结束就切回接收，会丢掉从站应答的开头几个字节。",
                "无 CRC / 无重传：干扰导致的数据错误会被当成正确值写进控制器，比通信失败更危险。",
            ],
            "steps": [
                {
                    "step": 1,
                    "action": "物理层整体替换：加隔离型 RS485 收发器（如 ISO3082 / MAX13487），A/B 线加 120Ω 终端电阻与偏置电阻，并上 TVS + PTC 防浪涌。",
                    "why": "对应差异【物理层 / 电平】+【安全 / 隔离】，现场总线的第一道防线是硬件。",
                    "ref": "物理层 / 电平",
                },
                {
                    "step": 2,
                    "action": "半双工方向控制：用 TXE/TC 中断控 DE/RE；必须等 TC（发送完成）标志置位后再延 1 个字符时间才切回接收。",
                    "why": "对应差异【拓扑结构】，方向切换早一拍就会截断从站应答。",
                    "ref": "拓扑结构",
                },
                {
                    "step": 3,
                    "action": "加 CRC16(Modbus) + 超时重传：每帧带 CRC，主站等待 200ms 无合法应答则重发，最多 3 次后标记该从站离线。",
                    "why": "对应差异【抗干扰 / 误码】，现场误码不可避免，只能靠校验+重传兜住。",
                    "ref": "抗干扰 / 误码",
                },
                {
                    "step": 4,
                    "action": "按距离反选波特率并留 2 倍余量：9600≈1200m / 19200≈800m / 115200≈100m（24AWG 屏蔽双绞线），别为速度牺牲稳定性。",
                    "why": "对应差异【波特率 / 距离】，距离与速率是硬性权衡，不能沿用原帖 9600 的理由。",
                    "ref": "波特率 / 距离",
                },
                {
                    "step": 5,
                    "action": "帧超时重同步：用 IDLE 或 1.5 字符定时器判帧尾，异常帧直接丢弃并重新搜帧头，绝不在坏帧上做解析。",
                    "why": "对应差异【抗干扰 / 误码】，坏帧解析比丢帧危害更大。",
                    "ref": "抗干扰 / 误码",
                },
            ],
            "code": """// 场景 C：工业 RS485 半双工 —— 方向切换 + CRC + 超时重传
void rs485_send(uint8_t *buf, uint16_t len) {
  uint16_t crc = crc16_modbus(buf, len);
  buf[len++] = crc & 0xFF; buf[len++] = crc >> 8;
  HAL_GPIO_WritePin(DE_GPIO_Port, DE_Pin, GPIO_PIN_SET);   // 切到发送
  HAL_UART_Transmit(&huart2, buf, len, 100);
  while (!__HAL_UART_GET_FLAG(&huart2, UART_FLAG_TC));     // 等最后一字节真正发出
  HAL_Delay(1);                                            // 再等 1 个字符时间
  HAL_GPIO_WritePin(DE_GPIO_Port, DE_Pin, GPIO_PIN_RESET);  // 立刻切回接收
}

// 主站轮询：超时重发 3 次，仍失败则标记该从站离线
for (uint8_t retry = 0; retry < 3; retry++) {
  rs485_send(req, req_len);
  if (HAL_UARTEx_ReceiveToIdle(&huart2, rx, sizeof(rx), 200) == HAL_OK && crc_ok(rx)) break;
}

// 波特率 ↔ 距离（24AWG 屏蔽双绞线）：9600≈1200m / 19200≈800m / 115200≈100m
// 硬件清单：隔离收发器 + A/B 120Ω 终端 + 偏置电阻 + TVS/PTC""",
            "summary": "关键改动：从「板内 TTL 点对点直连」升级为「隔离 RS485 + 方向切换 + CRC 重传 + 按距离反选波特率」。原帖的 DMA+IDLE 依然用来判定帧尾，但现场场景真正的难点从「怎么收得全」变成了「怎么保证收得对」——这是干扰环境和实验室环境的根本分野。",
        },
    },
    "pcb": {
        "highcurrent": {
            "keywords": ["5A", "大电流", "电机", "峰值", "内层", "4层", "四层", "母线", "电源板", "12V", "24V", "智能车", "驱动"],
            "same": [
                "计算依据相同：都按 IPC-2221 的载流公式，温升预算决定线宽。",
                "「加锡/铺铜/多过孔并联」这些降阻手法对你同样有效，而且更关键。",
            ],
            "diffs": [
                {
                    "dimension": "电流等级",
                    "origin": "2A 持续",
                    "mine": "5A 峰值（电机堵转可到 2~3 倍）：{scene}",
                    "impact": "线宽不是线性放大：电流 ×2.5，所需截面积约 ×2.5~3，经验值完全失效。",
                },
                {
                    "dimension": "走线层",
                    "origin": "外层走线，散热好",
                    "mine": "内层走线，热量闷在板内",
                    "impact": "同线宽内层载流能力约为外层的 50%（IPC-2221 内外层系数不同）。",
                },
                {
                    "dimension": "铜厚 / 空间",
                    "origin": "1oz，板面积宽松",
                    "mine": "1oz 且空间紧张，想尽量走细线",
                    "impact": "不能靠加宽解决，只能靠开窗加锡 / 铺铜 / 多层并联提升等效铜厚。",
                },
                {
                    "dimension": "负载性质",
                    "origin": "平稳持续电流",
                    "mine": "电机峰值冲击 + 频繁启停",
                    "impact": "要按峰值加余量，并考虑瞬态压降导致的驱动欠压复位。",
                },
                {
                    "dimension": "环境温度",
                    "origin": "常温开放环境",
                    "mine": "密闭车壳内，散热差：{constraint}",
                    "impact": "温升预算要收紧，否则 FR4 长期高温会分层。",
                },
            ],
            "risks": [
                "照搬 20mil 经验值：5A 内层 1oz 需要约 110mil（2.8mm），照搬会烧断铜皮。",
                "只按平均电流算：电机堵转瞬间可达 2~3 倍，线宽不够先烧的是铜皮不是保险丝。",
                "忽略过孔载流：单个 Ø0.3mm 过孔仅约 1A，5A 路径打一两个过孔必烧。",
                "内层走线不开散热窗：热量闷在板内，温升叠加后 FR4 可能长期超 130℃ 分层。",
            ],
            "steps": [
                {
                    "step": 1,
                    "action": "按 IPC-2221 重算内层线宽：I=5A、ΔT=10℃、1oz 内层 → 约 110mil（2.8mm）；允许 20℃ 温升可降到约 80mil（2.0mm）。",
                    "why": "对应差异【电流等级】+【走线层】，经验值在大电流内层场景失效，必须重算。",
                    "ref": "电流等级",
                },
                {
                    "step": 2,
                    "action": "空间不够就开窗加锡：在电源线上开阻焊窗镀锡，等效铜厚可到 2~3oz，线宽需求减半（110mil → 约 50mil）。",
                    "why": "对应差异【铜厚 / 空间】，靠提升等效铜厚而不是加宽线来省面积。",
                    "ref": "铜厚 / 空间",
                },
                {
                    "step": 3,
                    "action": "过孔阵列化：5A 路径至少 6 个 Ø0.3mm 过孔并联（或 2 个 Ø0.6mm），打在焊盘旁并做泪滴。",
                    "why": "对应差异【电流等级】，过孔是电源路径最容易被忽略的瓶颈。",
                    "ref": "电流等级",
                },
                {
                    "step": 4,
                    "action": "按峰值 ×1.2 留余量，并在电机驱动入口加缓启动 + 10A 自恢复保险丝，母线并 470µF 以上电解吸瞬态。",
                    "why": "对应差异【负载性质】，电机冲击电流与瞬态压降必须提前吃掉。",
                    "ref": "负载性质",
                },
                {
                    "step": 5,
                    "action": "实测温升闭环：满载连续跑 30 分钟，热像仪/点温计测最热点，超过 60℃ 就加锡或加厚铜箔再测。",
                    "why": "对应差异【环境温度】，密闭环境下的真实温升只能实测，不能只信公式。",
                    "ref": "环境温度",
                },
            ],
            "code": """# IPC-2221 载流反算：I = k * ΔT^0.44 * A^0.725
def width_mil(I, dT=10, oz=1, inner=True):
    k = 0.024 if inner else 0.048          # 内层 0.024 / 外层 0.048
    A = (I / (k * dT ** 0.44)) ** (1 / 0.725)   # 截面积 mil^2
    thick = oz * 1.37                      # 1oz 铜厚 ≈ 1.37 mil
    return A / thick

print(round(width_mil(5, 10, 1, True)))    # 内层 1oz 5A/10℃ ≈ 110 mil (2.8 mm)
print(round(width_mil(5, 10, 1, False)))   # 外层 1oz 5A/10℃ ≈ 55  mil (1.4 mm)
print(round(width_mil(5, 20, 1, True)))    # 内层 1oz 5A/20℃ ≈ 80  mil (2.0 mm)
print(round(width_mil(5, 10, 2, True)))    # 开窗加锡等效 2oz    ≈ 55  mil (1.4 mm)

# 过孔载流粗算（Ø0.3mm 孔壁 1oz ≈ 1A）：5A / 1A ≈ 6 个并联，建议留 8 个""",
            "summary": "关键改动：从「抄 20mil 经验值」转为「按 IPC-2221 以内层 + 峰值电流重算，再用开窗加锡换空间」。原帖的 20mil 只在 2A 外层成立；你这里是 5A 内层，线宽需求直接翻 5 倍以上，靠加铜厚而不是加线宽才是空间紧张下的正解。",
        },
    },
    "robot": {
        "gantry": {
            "keywords": ["龙门", "三轴", "步进", "喷胶", "点胶", "工厂", "行程", "导轨", "丝杠", "直线", "直角坐标", "1.5kg", "负载"],
            "same": [
                "目标一致：把「想去的位置」换算成「每个执行器该动多少」。",
                "离线算好再下发的节奏可以保留，只是映射关系变了。",
            ],
            "diffs": [
                {
                    "dimension": "机构形态",
                    "origin": "6 自由度旋转关节臂（关节角耦合）",
                    "mine": "三轴直角坐标龙门（X/Y/Z 解耦）：{scene}",
                    "impact": "逆运动学退化为线性映射，几何三角法在这里是无意义的——三轴互不耦合。",
                },
                {
                    "dimension": "驱动方式",
                    "origin": "舵机，角度开环、精度低",
                    "mine": "步进电机 + 丝杠，脉冲定位",
                    "impact": "需要加减速曲线，不能像舵机那样直接给目标角度。",
                },
                {
                    "dimension": "负载",
                    "origin": "200g 轻负载",
                    "mine": "1.5kg（约 7.5 倍）",
                    "impact": "必须校核推力/扭矩与惯量匹配，起步丢步风险陡增。",
                },
                {
                    "dimension": "行程 / 刚性",
                    "origin": "小臂展，刚性影响可忽略",
                    "mine": "400mm 行程，长行程下变形与回差不可忽略",
                    "impact": "需做单向逼近与回差补偿，否则往返定位差可达 0.2mm 以上。",
                },
                {
                    "dimension": "工况",
                    "origin": "桌面定点演示，撞了就断电",
                    "mine": "工厂连续作业：{constraint}",
                    "impact": "必须有回零、限位与丢步检测，否则断电即位置丢失、现场撞机。",
                },
            ],
            "risks": [
                "照搬几何法逆解：龙门是直角坐标机构，套旋转臂的三角公式会得到无意义的角度值。",
                "忽略加减速：1.5kg 负载直接给目标脉冲，起步必丢步、停下必过冲。",
                "长行程未做回差补偿：400mm 上累积回差会让喷胶轨迹整体偏移。",
                "无回零与限位：断电后位置丢失，工厂现场上电即撞机。",
            ],
            "steps": [
                {
                    "step": 1,
                    "action": "换掉映射关系：直角坐标直接线性换算脉冲，pulses = mm / 丝杠导程 × 步/圈（如 8mm 导程、6400 步/圈 → 800 步/mm），不再需要逆运动学求解。",
                    "why": "对应差异【机构形态】，直角坐标三轴解耦，逆解问题本身消失了。",
                    "ref": "机构形态",
                },
                {
                    "step": 2,
                    "action": "加梯形/S 型加减速：1.5kg 负载起步加速度建议 ≤ 500 mm/s²，用 accel 库按「加速—匀速—减速」三段下发脉冲。",
                    "why": "对应差异【驱动方式】+【负载】，步进必须走速度曲线，不能阶跃给目标。",
                    "ref": "驱动方式",
                },
                {
                    "step": 3,
                    "action": "校核推力与电机选型：F ≈ m(g+a) + μmg ≈ 17N，8mm 导程丝杠所需扭矩 ≈ 0.024N·m（理论），选 57 步进 1.5N·m 留 >10 倍余量吸收加减速冲击。",
                    "why": "对应差异【负载】，负载翻 7.5 倍必须重新选型而不是沿用舵机。",
                    "ref": "负载",
                },
                {
                    "step": 4,
                    "action": "回差补偿 + 上电回零：所有定位走单向逼近，补偿量 0.15~0.3mm；上电先触发限位开关回零建立坐标系。",
                    "why": "对应差异【行程 / 刚性】，长行程丝杠的机械回差必须软件抵消。",
                    "ref": "行程 / 刚性",
                },
                {
                    "step": 5,
                    "action": "丢步检测与保护：末端加光电/编码器做闭环校验，或至少在关键工位加到位开关；软件限位 + 硬限位双保险。",
                    "why": "对应差异【工况】，工厂连续作业不能靠「撞了就断电」。",
                    "ref": "工况",
                },
            ],
            "code": """# 龙门三轴：直角坐标 → 脉冲（不需要逆运动学）
STEPS_PER_REV, LEAD_MM = 6400, 8.0        # 细分后步/圈, 丝杠导程 mm
STEPS_PER_MM = STEPS_PER_REV / LEAD_MM    # = 800 步/mm

def mm_to_steps(mm):    return int(mm * STEPS_PER_MM)

def move_to(target_mm, v_mm_s=80, a_mm_s2=400):
    # 梯形加减速：加速段 t1=v/a，不足一半距离则退化为三角形曲线
    d = abs(target_mm)
    d_acc = v_mm_s ** 2 / (2 * a_mm_s2)
    if 2 * d_acc >= d:
        d_acc, v_mm_s = d / 2, (d * a_mm_s2) ** 0.5
    ramp(mm_to_steps(d_acc), accel=a_mm_s2 * STEPS_PER_MM)
    linear(mm_to_steps(d - 2 * d_acc), speed=v_mm_s * STEPS_PER_MM)
    ramp(mm_to_steps(d_acc), accel=-a_mm_s2 * STEPS_PER_MM)

# 推力校核（负载 1.5kg）：F = m(g+a) + μmg ≈ 1.5*10.3 + 0.1*1.5*9.8 ≈ 17 N
# 丝杠扭矩 T = F*lead/(2πη) = 17*0.008/(6.28*0.9) ≈ 0.024 N·m（理论值）
# 选型：57 步进 1.5N·m，留 >10 倍余量吸收加减速冲击与摩擦波动""",
            "summary": "关键改动：从「几何法求逆解 + 舵机查表」转为「直角坐标直算脉冲 + 梯形加减速 + 回差补偿 + 回零限位」。原帖的逆运动学在你的龙门机构上根本不需要——三轴解耦让问题退化为线性映射，真正的难点转移到负载带来的加减速与长行程回差上。",
        },
    },
    "generic": {},
}


# ---------------------------------------------------------------------------
# Mock：渲染与分支选择
# ---------------------------------------------------------------------------
def _render(obj, scene: str, constraint: str):
    """递归替换 {scene}/{constraint} 占位符（不用 str.format，避免代码块里的花括号炸掉）。"""
    if isinstance(obj, str):
        if "{scene}" in obj or "{constraint}" in obj:
            return obj.replace("{scene}", scene).replace("{constraint}", constraint)
        return obj
    if isinstance(obj, list):
        return [_render(x, scene, constraint) for x in obj]
    if isinstance(obj, dict):
        return {k: _render(v, scene, constraint) for k, v in obj.items()}
    return obj


def _pick_branch(t: str, user_scene: str, user_constraint: str) -> dict | None:
    """按场景关键词打分选分支；都不命中返回 None（走通用兜底）。"""
    text = f"{user_scene} {user_constraint}"
    best, best_score = None, 0
    for name, br in SCENE_BRANCHES.get(t, {}).items():
        score = sum(1 for k in br["keywords"] if k in text)
        if score > best_score:
            best, best_score = br, score
    return best


def _fallback_branch(t: str) -> dict:
    """未命中任何分支时的通用兜底（保持「差异→对策」闭环）。"""
    return {
        "same": [
            "要解决的问题本质相同，可复用其分析框架。",
            "作者的验证思路（分步定位 / 选型依据）对你同样适用。",
        ],
        "diffs": [
            {
                "dimension": "运行环境 / 平台",
                "origin": "原帖场景（见上方原帖解构）",
                "mine": "{scene}",
                "impact": "环境差异决定原参数能否直接复用，是最先要核对的一层。",
            },
            {
                "dimension": "负载 / 边界条件",
                "origin": "原帖约束（见上方原帖解构）",
                "mine": "{constraint}",
                "impact": "超出原帖边界时，需对解法做缩放或替换关键器件。",
            },
            {
                "dimension": "关键参数",
                "origin": "原帖参数（见上方原帖解构）",
                "mine": "在你的处境下需重新标定",
                "impact": "参数是最易被「照搬错」的部分，建议按你的实测重算。",
            },
        ],
        "risks": [
            "直接照搬参数到不同硬件/负载，可能触发原帖未覆盖的失效模式。",
            "原帖边界外的场景，照搬解法会引入隐性风险（温升/丢帧/抖振）。",
        ],
        "steps": [
            {
                "step": 1,
                "action": "对齐环境：把你的处境（{scene}）与原帖场景的差异逐条列清楚。",
                "why": "对应差异【运行环境 / 平台】，先确认是否落在原帖适用边界内。",
                "ref": "运行环境 / 平台",
            },
            {
                "step": 2,
                "action": "照搬「框架」而非「数值」：保留作者的分析方法，参数按你的实测重算。",
                "why": "对应差异【关键参数】，原帖参数的前提与你不同，直接抄值最危险。",
                "ref": "关键参数",
            },
            {
                "step": 3,
                "action": "针对你的约束做一处分流/缩放：{constraint}",
                "why": "对应差异【负载 / 边界条件】，把原解适配进你的真实限制才是「迁移」。",
                "ref": "负载 / 边界条件",
            },
            {
                "step": 4,
                "action": "小批量验证后再固化：先最小复现，再逐步加压/提速到目标。",
                "why": "沿用原帖的验证节奏兜底，降低一次到位的风险。",
                "ref": "运行环境 / 平台",
            },
        ],
        "code": _legacy_code_block(t),
        "summary": "核心思路可复用，但必须按你的真实场景（{scene}）重标定参数与边界，再小批量验证固化。",
    }


def _legacy_code_block(t: str) -> str:
    if t == "embed":
        return (
            "// 串口空闲中断收整帧（伪代码）\n"
            "if (__HAL_UART_GET_FLAG(&huart, UART_FLAG_IDLE)) {\n"
            "    __HAL_UART_CLEAR_IDLEFLAG(&huart);\n"
            "    uint16_t len = RX_BUF_SIZE - __HAL_DMA_GET_COUNTER(hdma);\n"
            "    parse_frame(rx_buf, len);   // 整帧解析，避免逐字节拼帧丢字节\n"
            "    HAL_UART_Receive_DMA(&huart, rx_buf, RX_BUF_SIZE);\n"
            "}"
        )
    if t == "pcb":
        return "# 线宽经验估算（1oz, 温升~10℃）\ncurrent = 2.0   # A\nwidth_mil = 20  # 经验值承载 2A\nvias = 2        # 并联过孔降低温升"
    if t == "robot":
        return (
            "// 逆解查表（伪代码）\n"
            "def ik(target_pose):\n"
            "    angles = analytic_solve(target_pose)  # 几何/解析逆解\n"
            "    angles = pick_solution(angles)         # 六轴多解，按限位选解\n"
            "    return clamp_to_servo(angles)         # 限幅到舵机量程"
        )
    return "# 按你的场景把原帖关键参数重算后再用"


@lru_cache(maxsize=128)
def _mock_deconstruct(post_id: int, title: str, summary: str) -> dict:
    """A1 Mock 解构（缓存：同一帖只算一次，省真实调用额度）。"""
    post = type("P", (), {"title": title, "summary": summary})()
    return copy.deepcopy(ORIGIN_TEMPLATES[_detect_type(post)])


def _mock_generate(t, origin, user_scene, user_constraint) -> tuple:
    scene_label = (user_scene or "").strip() or "你的真实场景"
    constraint_label = (user_constraint or "").strip() or "（未指定额外约束）"
    br = _pick_branch(t, user_scene or "", user_constraint or "") or _fallback_branch(t)
    br = _render(copy.deepcopy(br), scene_label, constraint_label)

    diff = {
        "same": br.get("same", []),
        "diffs": br.get("diffs", []),
        "risks": br.get("risks", []),
        "originScene": origin.get("scene", ""),
    }
    solution = {
        "steps": br.get("steps", []),
        "code": br.get("code", ""),
        "summary": br.get("summary", ""),
    }
    return diff, solution


# ---------------------------------------------------------------------------
# 真实 LLM 通道
# ---------------------------------------------------------------------------
def _llm_call(template_name: str, mapping: dict, fast: bool = False) -> dict:
    from ai.llm import chat_json, load_prompt

    prompt = load_prompt(template_name)
    for k, v in mapping.items():
        prompt = prompt.replace("{" + k + "}", str(v))
    return chat_json([{"role": "user", "content": prompt}], fast=fast)


def _normalize_origin(d: dict) -> dict:
    return {
        "scene": d.get("scene") or "（模型未给出）",
        "solution": d.get("solution") or "",
        "constraints": d.get("constraints") or [],
        "params": d.get("params") or {},
        "boundaries": d.get("boundaries") or "",
    }


def _normalize_diff(d: dict, origin: dict) -> dict:
    diffs = d.get("diffs") or d.get("differences") or []
    out = []
    for i, x in enumerate(diffs, 1):
        out.append(
            {
                "dimension": x.get("dimension") or x.get("dim") or f"差异 {i}",
                "origin": x.get("origin") or "",
                "mine": x.get("mine") or "",
                "impact": x.get("impact") or "",
            }
        )
    return {
        "same": d.get("same") or [],
        "diffs": out,
        "risks": d.get("risks") or [],
        "originScene": origin.get("scene", ""),
    }


def _normalize_solution(d: dict) -> dict:
    steps = []
    for i, x in enumerate(d.get("steps") or [], 1):
        steps.append(
            {
                "step": x.get("step") or i,
                "action": x.get("action") or x.get("detail") or "",
                "why": x.get("why") or "",
                "ref": x.get("ref") or "",
            }
        )
    return {
        "steps": steps,
        "code": d.get("code") or d.get("bomOrParams") or "",
        "summary": d.get("summary") or "",
    }


def _real_generate(post, user_scene: str, user_constraint: str, origin: dict) -> tuple:
    """真实通道的 A2+A3（A1 已由 deconstruct 产出）。"""
    origin_json = json.dumps(origin, ensure_ascii=False)
    diff_raw = _llm_call(
        "diff.txt",
        {
            "origin_json": origin_json,
            "user_scene": user_scene,
            "user_constraint": user_constraint or "（未指定）",
        },
    )
    if diff_raw.get("_degraded"):
        raise RuntimeError(diff_raw.get("fallbackText", "diff 生成失败"))
    diff = _normalize_diff(diff_raw, origin)

    sol_raw = _llm_call(
        "transfer.txt",
        {
            "origin_json": origin_json,
            "diff_json": json.dumps(diff, ensure_ascii=False),
            "user_scene": user_scene,
            "user_constraint": user_constraint or "（未指定）",
        },
    )
    if sol_raw.get("_degraded"):
        raise RuntimeError(sol_raw.get("fallbackText", "solution 生成失败"))
    return diff, _normalize_solution(sol_raw)


# ---------------------------------------------------------------------------
# 对外入口
# ---------------------------------------------------------------------------
def deconstruct(post) -> tuple:
    """A1：解构原帖 → (origin, provider)。真实通道失败自动降级 Mock。"""
    provider = effective_provider()
    if provider != "mock":
        try:
            raw = _llm_call(
                "extract.txt",
                {"title": post.title, "content": (post.content_text or post.summary or "")[:4000]},
                fast=True,
            )
            if not raw.get("_degraded") and raw.get("scene"):
                return _normalize_origin(raw), provider
        except Exception as e:  # noqa: BLE001 —— 真实通道任何异常都降级
            print(f"[ai_engine] A1 真实通道失败，降级 Mock：{e}")
    return _mock_deconstruct(post.id, post.title, post.summary or ""), "mock"


def generate(post, scene_tag: str, user_scene: str, user_constraint: str) -> tuple:
    """A1+A2+A3 → (origin, diff, solution, provider)。"""
    t = _detect_type(post)
    origin, provider = deconstruct(post)

    if provider != "mock":
        try:
            diff, solution = _real_generate(post, user_scene, user_constraint, origin)
            if diff.get("diffs") and solution.get("steps"):
                return origin, diff, solution, provider
            raise RuntimeError("真实通道输出不完整")
        except Exception as e:  # noqa: BLE001
            print(f"[ai_engine] A2/A3 真实通道失败，降级 Mock：{e}")
            provider = "mock"

    diff, solution = _mock_generate(t, origin, user_scene, user_constraint)
    return origin, diff, solution, provider


def to_json(obj) -> str:
    return json.dumps(obj, ensure_ascii=False)
