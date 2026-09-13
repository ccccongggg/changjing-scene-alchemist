"""星图（constellation）视图。

把「一帖千面」的场景应用网，折算成前端星图能直接画的结构。

设计原则：
- **只读**：不写库。所有内容来自真实的 source_posts / adaptations / feedbacks，
  用户在场景工坊里每炼一版、每复诊一次，星图上就多一颗星 —— 星图是真实数据的另一种看法。
- 前端不需要懂 branch / diff_json / solution_json 的 schema，
  拿到的就是"能画"的模型：太阳=原帖，星=一次适配，环=迁移深度，虚线=复诊链。
"""

import json

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ai_engine import SCENE_BRANCHES, _detect_type, _mock_deconstruct
from database import get_db
from models import Adaptation, Feedback, SourcePost

router = APIRouter(prefix="/starmap", tags=["starmap"])

DEPTH_NAME = ["", "改参数", "动结构", "换方案"]

# 分支的中文名（给人看的）；没收录的分支退回原始 key
BRANCH_LABEL = {
    "office": "上班族路线",
    "student": "学生路线",
    "parent": "家长路线",
    "highspeed": "高速并发路线",
    "lowpower": "低功耗路线",
    "noisy": "强干扰现场路线",
    "highcurrent": "大电流路线",
    "gantry": "龙门结构路线",
    # 已走过的路都避开时会落到兜底分支：这不是出错，是"按你的约束重新设计"
    "_fallback": "按你的约束重新设计",
}


def _load(s):
    try:
        return json.loads(s) if s else {}
    except Exception:  # noqa: BLE001
        return {}


def _branch_meta(t: str, branch: str | None):
    """分支 → (中文名, 迁移深度 1/2/3)。深度 = 分支在该领域里的次序。"""
    keys = list(SCENE_BRANCHES.get(t, {}).keys())
    if branch and branch in keys:
        return BRANCH_LABEL.get(branch, branch), keys.index(branch) + 1
    return (BRANCH_LABEL.get(branch, branch or "通用路线"), 2)


def _chain_len(row_id: int, parent_of: dict) -> int:
    """顺着 parent_id 往上数，返回这是第几版（根=1）。"""
    n, cur, guard = 1, parent_of.get(row_id), 0
    while cur and guard < 50:
        n += 1
        cur = parent_of.get(cur)
        guard += 1
    return n


def _scene(a: Adaptation, t: str, peers: int, feedbacks: dict, parent_of: dict) -> dict:
    origin = _load(a.origin_json)
    diff = _load(a.diff_json)
    solution = _load(a.solution_json)
    label, depth = _branch_meta(t, a.branch)

    fbs = feedbacks.get(a.id, [])
    done = any(f.result == "done" for f in fbs)
    stuck = [f for f in fbs if f.result == "stuck"]

    steps = solution.get("steps") or []
    moves = [
        {
            "step": s.get("step") or i + 1,
            "title": s.get("ref") or f"第 {i + 1} 步",
            "action": s.get("action") or "",
            "why": s.get("why") or "",
        }
        for i, s in enumerate(steps)
    ]

    return {
        "id": a.id,
        "name": a.scene_tag or (a.user_scene or "")[:12] or f"场景 {a.id}",
        "sit": a.user_scene or "",
        "constraint": a.user_constraint or "",
        "branch": a.branch,
        "branchLabel": label,
        "depth": depth,
        "depthName": DEPTH_NAME[depth] if depth < len(DEPTH_NAME) else DEPTH_NAME[2],
        "verified": done,
        "version": _chain_len(a.id, parent_of),
        "parentId": a.parent_id,
        "rounds": len(stuck),
        "peers": peers,
        "originScene": origin.get("scene") or diff.get("originScene") or "",
        "same": diff.get("same") or [],
        "diffs": [
            {
                "dimension": d.get("dimension") or "",
                "origin": d.get("origin") or "",
                "mine": d.get("mine") or "",
                "impact": d.get("impact") or "",
            }
            for d in (diff.get("diffs") or [])
        ],
        # 「已替你避开的坑」：内容就是照搬会踩的坑，视角换成"AI 已绕开"
        "avoided": [r for r in (diff.get("risks") or []) if r],
        "moves": moves,
        "summary": solution.get("summary") or "",
        "switch": solution.get("switch") or "",
        "createdAt": a.created_at,
    }


@router.get("")
def constellation(db: Session = Depends(get_db)):
    posts = (
        db.query(SourcePost)
        .order_by(SourcePost.fav_time.desc().nullslast(), SourcePost.id.asc())
        .all()
    )
    adaptations = db.query(Adaptation).order_by(Adaptation.id.asc()).all()

    by_post: dict[int, list] = {}
    for a in adaptations:
        by_post.setdefault(a.post_id, []).append(a)

    all_fb = db.query(Feedback).order_by(Feedback.round.asc()).all()
    feedbacks: dict[int, list] = {}
    for f in all_fb:
        feedbacks.setdefault(f.adaptation_id, []).append(f)

    out = []
    for p in posts:
        rows = by_post.get(p.id, [])
        t = _detect_type(p)

        # 原帖解构：优先用已有方案里存的那份（和方案一致），没有再即时算一次
        origin = {}
        for a in rows:
            origin = _load(a.origin_json)
            if origin:
                break
        if not origin:
            origin = _mock_deconstruct(p.id, p.title, p.summary or "")

        # parent_id 映射：算「第几版」和前端画复诊虚线都要
        parent_of = {a.id: a.parent_id for a in adaptations}
        branch_count: dict[str, int] = {}
        for a in rows:
            if a.branch:
                branch_count[a.branch] = branch_count.get(a.branch, 0) + 1

        scenes = [
            _scene(a, t, max(branch_count.get(a.branch, 1) - 1, 0), feedbacks,
                   parent_of)
            for a in rows
        ]

        out.append(
            {
                "id": p.id,
                "title": p.title,
                "author": p.author or "",
                "summary": p.summary or "",
                "url": p.url or "",
                "type": t,
                "origin": {
                    "scene": origin.get("scene") or "",
                    "solution": origin.get("solution") or "",
                    "constraints": origin.get("constraints") or [],
                    "params": origin.get("params") or {},
                    "boundaries": origin.get("boundaries") or "",
                },
                "scenes": scenes,
                "verified": sum(1 for s in scenes if s["verified"]),
            }
        )

    return {
        "code": 0,
        "data": {
            "posts": out,
            "depthName": DEPTH_NAME,
            "total": {"posts": len(out), "scenes": len(adaptations)},
        },
        "msg": "ok",
    }
