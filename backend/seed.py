"""种子数据：3 篇演示帖 + 预置的「一帖千面」场景方案（让方案库一进来就有网感）。"""

from sqlalchemy.orm import Session

from database import Base, SessionLocal, engine
from models import Adaptation, Feedback, SourcePost

SEED_POSTS = [
    {
        "content_type": "answer",
        "title": "STM32 串口通信踩坑全记录：从丢字节到稳定收发",
        "author": "某嵌入式工程师",
        "authority_level": "3",
        "summary": "记录 STM32F103 电子秤项目中单串口 9600 接称重模块的坑：接收中断逐字节拼帧导致高波特率丢字节，最终用 DMA+空闲中断解决。",
        "content_text": "（种子演示用摘要占位；正式内容可在 §10.1 扩写到 600~1000 字）",
        "url": "https://www.zhihu.com/question/example1",
        "source": "seed",
    },
    {
        "content_type": "article",
        "title": "PCB 电源线宽到底怎么算？大电流主板布线实例",
        "author": "某硬件工程师",
        "authority_level": "2",
        "summary": "12V/2A 控制板，1oz 铜厚，按 IPC-2221 算线宽，作者给出 20mil 经验值，并附大电流主板布线实例。",
        "content_text": "（种子演示用摘要占位）",
        "url": "https://www.zhihu.com/p/example2",
        "source": "seed",
    },
    {
        "content_type": "article",
        "title": "六轴机械臂运动学入门：我的第一个逆解程序",
        "author": "某机器人爱好者",
        "authority_level": "2",
        "summary": "桌面 6 自由度舵机臂，用几何法做逆运动学，Arduino 驱动，负载 200g，附首个逆解程序思路。",
        "content_text": "（种子演示用摘要占位）",
        "url": "https://www.zhihu.com/p/example3",
        "source": "seed",
    },
    # ↓ 生活类：给不搞技术的评审/普通人看——全站统一用「学 AI 产品」这一个例子
    {
        "content_type": "answer",
        "title": "我用 AI 工具三个月，效率翻倍的 12 个方法",
        "author": "某全职自由职业者",
        "authority_level": "4",
        "summary": "作者是付费会员不限额度，可自由安装软件、调用接口，英文界面无障碍，本身是产品经理、清楚怎么描述需求，每天有大把时间反复摸索。核心方法：把它当同事多轮对话反复打磨；用接口批量处理文件；先让它列大纲再逐段展开。",
        "content_text": "（种子演示用摘要占位）",
        "url": "https://www.zhihu.com/question/example4",
        "source": "seed",
        "fav_time": 1757600000,
    },
]

# 已被替换掉的例子（改版时留着会和新叙事打架），启动时自动清理
DEPRECATED_TITLES = [
    "红烧肉怎么做才软烂入味？从选肉到收汁，一次讲透",
    "三战上岸：我的十小时作息表，附每周复盘方法",
]

# 预置场景（post_index 从 1 开始）：演示「同一篇帖 → 多个真实场景 → 多套解法」
# provider 固定 mock（canned 演示数据，断网也能演，保证现场不翻车）
PRESET_SCENARIOS = [
    {
        "post_index": 1,
        "scene_tag": "智能车高速双串口",
        "user_scene": "智能车竞赛，主控 MSPM0G3507，两个串口同时收摄像头（115200 持续流）和蓝牙（9600），数据不能丢。",
        "user_constraint": "不能换主控，工期只有 3 天",
        "created_at": "2026-09-08 10:12:00",
    },
    {
        "post_index": 1,
        "scene_tag": "电池水表低功耗",
        "user_scene": "电池供电的远传水表，STM32L 系列，单串口接 MBus 通信模块，每天只上报几次，要求整机微安级休眠。",
        "user_constraint": "成本敏感，不能加额外唤醒芯片",
        "created_at": "2026-09-08 14:35:00",
    },
    {
        "post_index": 1,
        "scene_tag": "工业 RS485 现场总线",
        "user_scene": "工厂车间里一台主控通过 RS485 总线轮询 8 个从站，线长 300 米，旁边有变频器和继电器，误码时有发生。",
        "user_constraint": "距离 300 米，现场干扰强，需要一个季度内免维护",
        "created_at": "2026-09-09 09:20:00",
    },
    {
        "post_index": 2,
        "scene_tag": "智能车 4 层电源板 5A 电机",
        "user_scene": "智能车 4 层电源板，12V 输入、电机峰值 5A，内层走线 1oz 铜厚，空间紧张想尽量走细线。",
        "user_constraint": "空间紧张，密闭车壳内散热差",
        "created_at": "2026-09-08 16:02:00",
    },
    {
        "post_index": 3,
        "scene_tag": "工厂喷胶三轴龙门",
        "user_scene": "工厂喷胶机小型三轴龙门，步进电机驱动、负载 1.5kg、行程 400mm，原帖的几何法逆解还适用吗？",
        "user_constraint": "工厂连续作业，断电后位置不能丢",
        "created_at": "2026-09-09 11:48:00",
    },
    # ↓ 同一篇 AI 攻略的三种真实处境（谁都看得懂的「一帖三吃」）
    {
        "post_index": 4,
        "scene_tag": "上班族版",
        "user_scene": "我在上班，公司电脑不让装任何软件，只能用网页版，而且工作内容不能外传，只有午休 30 分钟。",
        "user_constraint": "时间只有碎片，不能装软件，内容要脱敏",
        "created_at": "2026-09-10 19:20:00",
    },
    {
        "post_index": 4,
        "scene_tag": "学生版",
        "user_scene": "我是学生，只有免费额度，每天 20 次用完就得等明天，想拿它改论文、备考、讲错题。",
        "user_constraint": "交上去要像自己写的，还得过查重",
        "created_at": "2026-09-10 20:05:00",
    },
    {
        "post_index": 4,
        "scene_tag": "家长版",
        "user_scene": "我是家长，完全零基础，「提示词」今天是第一次听说，想用它辅导孩子作业，但不想让它直接给答案。",
        "user_constraint": "要孩子真的懂，不是答案到手；孩子容易跑题",
        "created_at": "2026-09-11 10:30:00",
    },
    # ↓ 让星图站得住：同一篇 AI 攻略在不同硬条件下还能怎么改
    {
        "post_index": 4,
        "scene_tag": "通勤碎片版",
        "user_scene": "我在深圳上班，每天能用的只有通勤 40 分钟加午休 30 分钟，晚上要带娃，没有整块时间，只能在手机上用。",
        "user_constraint": "时间被切成 15 分钟一段，只能手机操作",
        "created_at": "2026-09-11 21:10:00",
    },
    {
        "post_index": 4,
        "scene_tag": "资料不能外传版",
        "user_scene": "做咨询，手上是客户的合同和财报，公司明令禁止上传到任何外部工具，可我还是想用它帮我捋结构。",
        "user_constraint": "资料涉密不能外传，错了要担责",
        "created_at": "2026-09-11 22:40:00",
    },
    {
        "post_index": 4,
        "scene_tag": "要交给老板版",
        "user_scene": "我在公司上班，写周报和方案给老板，得能直接发出去，不能有那种一眼就看出是机器写的味道。",
        "user_constraint": "要能直接对外交付，措辞得像人写的",
        "created_at": "2026-09-12 09:15:00",
    },
    {
        "post_index": 4,
        "scene_tag": "论文查重版",
        "user_scene": "我在写毕业论文，学校要求用 AI 生成的内容必须声明，而且查重很严，整段照用会出问题。",
        "user_constraint": "要过查重，还要能说清哪部分用了工具",
        "created_at": "2026-09-12 10:05:00",
    },
    {
        "post_index": 4,
        "scene_tag": "备考冲刺版",
        "user_scene": "离考研只剩 6 周，专业课资料还没看完，想用 AI 把高频考点压出来，来不及全看一遍了。",
        "user_constraint": "时间紧，只押高频考点，冷门章节直接放弃",
        "created_at": "2026-09-12 11:20:00",
    },
    {
        "post_index": 4,
        "scene_tag": "辅导孩子版",
        "user_scene": "孩子上初中，我想用它辅导数学，可它一上来就把答案给出来了，孩子抄完就跑，什么也没学会。",
        "user_constraint": "要孩子真懂，不能直接给答案",
        "created_at": "2026-09-12 14:50:00",
    },
]


def seed_posts(db: Session | None = None):
    """按标题幂等补齐种子帖——以后再加新帖，已有库也能自动补上（不会重复插入）。"""
    own = db is None
    if own:
        db = SessionLocal()
    try:
        _drop_deprecated_posts(db)
        existing = {t for (t,) in db.query(SourcePost.title).all()}
        added = 0
        for p in SEED_POSTS:
            if p["title"] in existing:
                continue
            db.add(SourcePost(**p))
            added += 1
        db.commit()
        return {"seeded": added > 0, "added": added, "count": db.query(SourcePost).count()}
    finally:
        if own:
            db.close()


def _drop_deprecated_posts(db: Session):
    """清掉已经换掉的演示帖（连同它们的方案和复诊记录），幂等、可重复执行。"""
    if not DEPRECATED_TITLES:
        return 0
    rows = db.query(SourcePost).filter(SourcePost.title.in_(DEPRECATED_TITLES)).all()
    if not rows:
        return 0
    ids = [r.id for r in rows]
    adaptations = db.query(Adaptation).filter(Adaptation.post_id.in_(ids)).all()
    aids = [a.id for a in adaptations]
    if aids:
        db.query(Feedback).filter(Feedback.adaptation_id.in_(aids)).delete(
            synchronize_session=False
        )
        for a in adaptations:
            db.delete(a)
    for r in rows:
        db.delete(r)
    db.commit()
    return len(ids)


def seed_adaptations(db: Session | None = None):
    """预置演示场景方案（幂等：按 post_id + scene_tag 去重）。

    走 Mock 生成器产出，与「现场真实生成」的输出结构完全一致，
    因此收藏台的场景网、方案库一进来就有「一帖千面」的地图感。
    """
    from ai_engine import (
        _detect_type,
        _mock_deconstruct,
        _mock_generate,
        resolve_branch,
        to_json,
    )

    own = db is None
    if own:
        db = SessionLocal()
    try:
        posts = db.query(SourcePost).order_by(SourcePost.id).all()
        if not posts:
            return {"seeded": False, "count": 0, "reason": "no posts"}
        added = 0
        fixed = 0
        for s in PRESET_SCENARIOS:
            idx = s["post_index"] - 1
            if idx >= len(posts):
                continue
            post = posts[idx]
            exists = (
                db.query(Adaptation)
                .filter(Adaptation.post_id == post.id, Adaptation.scene_tag == s["scene_tag"])
                .first()
            )
            if exists:
                # 老记录没落 branch（星图靠它算迁移深度、复诊靠它避开走
                # 过的路），这里补一次，幂等
                if not exists.branch:
                    exists.branch = resolve_branch(
                        _detect_type(post), s["user_scene"], s["user_constraint"]
                    )
                    fixed += 1
                continue
            origin = _mock_deconstruct(post.id, post.title, post.summary or "")
            diff, solution = _mock_generate(
                _detect_type(post), origin, s["user_scene"], s["user_constraint"]
            )
            db.add(
                Adaptation(
                    post_id=post.id,
                    scene_tag=s["scene_tag"],
                    user_scene=s["user_scene"],
                    user_constraint=s["user_constraint"],
                    origin_json=to_json(origin),
                    diff_json=to_json(diff),
                    solution_json=to_json(solution),
                    provider="mock",
                    branch=resolve_branch(
                        _detect_type(post), s["user_scene"], s["user_constraint"]
                    ),
                    created_at=s["created_at"],
                )
            )
            added += 1
        db.commit()
        return {"seeded": added > 0, "added": added, "fixed": fixed}
    finally:
        if own:
            db.close()


if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    print(seed_posts())
    print(seed_adaptations())
