"""种子数据：3 篇演示帖 + 预置的「一帖千面」场景方案（让方案库一进来就有网感）。"""

from sqlalchemy.orm import Session

from database import Base, SessionLocal, engine
from models import Adaptation, SourcePost

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
]


def seed_posts(db: Session | None = None):
    own = db is None
    if own:
        db = SessionLocal()
    try:
        count = db.query(SourcePost).count()
        if count > 0:
            return {"seeded": False, "count": count}
        for p in SEED_POSTS:
            db.add(SourcePost(**p))
        db.commit()
        return {"seeded": True, "count": len(SEED_POSTS)}
    finally:
        if own:
            db.close()


def seed_adaptations(db: Session | None = None):
    """预置演示场景方案（幂等：按 post_id + scene_tag 去重）。

    走 Mock 生成器产出，与「现场真实生成」的输出结构完全一致，
    因此收藏台的场景网、方案库一进来就有「一帖千面」的地图感。
    """
    from ai_engine import _detect_type, _mock_deconstruct, _mock_generate, to_json

    own = db is None
    if own:
        db = SessionLocal()
    try:
        posts = db.query(SourcePost).order_by(SourcePost.id).all()
        if not posts:
            return {"seeded": False, "count": 0, "reason": "no posts"}
        added = 0
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
                    created_at=s["created_at"],
                )
            )
            added += 1
        db.commit()
        return {"seeded": added > 0, "count": added}
    finally:
        if own:
            db.close()


if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    print(seed_posts())
    print(seed_adaptations())
