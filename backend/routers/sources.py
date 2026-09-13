import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ai_engine import ask_question, rediagnose, to_json
from database import SessionLocal, get_db
from models import Adaptation, Feedback, SourcePost
from schemas import AdaptationOut, FeedbackIn, SourcePostOut
from seed import seed_adaptations, seed_posts

router = APIRouter()


class CategoryUpdate(BaseModel):
    category: str


@router.post("/sources/seed")
def do_seed():
    posts = seed_posts()
    adaptations = seed_adaptations()
    return {"code": 0, "data": {"posts": posts, "adaptations": adaptations}, "msg": "ok"}


@router.get("/sources")
def list_sources(db: Session = Depends(get_db)):
    # 收藏时间新的在前（NULL 视为最旧）：新增的生活类演示帖会排在最前面，
    # 不懂技术的评审/路人一进来先看到「红烧肉菜谱」而不是 STM32。
    rows = (
        db.query(SourcePost)
        .order_by(SourcePost.fav_time.desc().nullslast(), SourcePost.id.asc())
        .all()
    )
    data = [SourcePostOut.model_validate(p, from_attributes=True).model_dump() for p in rows]
    return {"code": 0, "data": data, "msg": "ok"}


@router.get("/sources/{post_id}")
def get_source(post_id: int, db: Session = Depends(get_db)):
    post = db.query(SourcePost).filter(SourcePost.id == post_id).first()
    if not post:
        return {"code": 404, "data": None, "msg": "not found"}
    data = SourcePostOut.model_validate(post, from_attributes=True).model_dump()
    return {"code": 0, "data": data, "msg": "ok"}


@router.patch("/sources/{post_id}/category")
def update_category(post_id: int, body: CategoryUpdate, db: Session = Depends(get_db)):
    post = db.query(SourcePost).filter(SourcePost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="source not found")
    post.category = body.category.strip() or "未分类"
    db.commit()
    db.refresh(post)
    data = SourcePostOut.model_validate(post, from_attributes=True).model_dump()
    return {"code": 0, "data": data, "msg": "ok"}


@router.get("/adaptations")
def list_adaptations(db: Session = Depends(get_db)):
    rows = db.query(Adaptation).order_by(Adaptation.id.desc()).all()
    data = [AdaptationOut.model_validate(r, from_attributes=True).model_dump() for r in rows]
    return {"code": 0, "data": data, "msg": "ok"}


def _adaptation_detail(row: Adaptation) -> dict:
    def load(s):
        try:
            return json.loads(s) if s else {}
        except Exception:  # noqa: BLE001
            return {}

    d = AdaptationOut.model_validate(row, from_attributes=True).model_dump()
    d.update(
        {
            "origin": load(row.origin_json),
            "diff": load(row.diff_json),
            "solution": load(row.solution_json),
        }
    )
    return d


@router.get("/adaptations/{aid}")
def get_adaptation(aid: int, db: Session = Depends(get_db)):
    row = db.query(Adaptation).filter(Adaptation.id == aid).first()
    if not row:
        raise HTTPException(status_code=404, detail="adaptation not found")
    return {"code": 0, "data": _adaptation_detail(row), "msg": "ok"}


@router.delete("/adaptations/{aid}")
def delete_adaptation(aid: int, db: Session = Depends(get_db)):
    row = db.query(Adaptation).filter(Adaptation.id == aid).first()
    if not row:
        raise HTTPException(status_code=404, detail="adaptation not found")
    db.delete(row)
    db.commit()
    return {"code": 0, "data": {"id": aid}, "msg": "ok"}


# ---------------------------------------------------------------------------
# 复诊（版本 1.1 · P0）
# ---------------------------------------------------------------------------
# 两阶段共用一个端点：
#   1) 只带 result/block_type，不带 user_note → 返回 AI 的「归因追问」一句（不落库）
#   2) 带上 user_note → 落库，返回三分归因 + 「已排除 / 剩余可试」棋盘 + 下一步
# 响应是**直出 dict**（无信封），前端 unwrap 已兼容。

def _load_json(s):
    try:
        return json.loads(s) if s else {}
    except Exception:  # noqa: BLE001
        return {}


def _chain_ids(db: Session, aid: int) -> list:
    """顺着 parent_id 往上找，返回整条复诊链的方案 id（新→旧）。"""
    ids, cur, guard = [], aid, 0
    while cur and guard < 50:
        ids.append(cur)
        row = db.query(Adaptation).filter(Adaptation.id == cur).first()
        if not row:
            break
        cur = row.parent_id
        guard += 1
    return ids


@router.post("/adaptations/{aid}/feedback")
def submit_feedback(aid: int, body: FeedbackIn, db: Session = Depends(get_db)):
    row = db.query(Adaptation).filter(Adaptation.id == aid).first()
    if not row:
        raise HTTPException(status_code=404, detail="adaptation not found")

    result = (body.result or "").strip()
    if result not in ("done", "stuck"):
        raise HTTPException(status_code=400, detail="result must be 'done' or 'stuck'")

    chain = _chain_ids(db, aid)
    past = (
        db.query(Feedback)
        .filter(Feedback.adaptation_id.in_(chain))
        .order_by(Feedback.round.asc())
        .all()
    )

    # ---- 做成了：不追问，直接记下并给用户一个身份升级 ----
    if result == "done":
        rec = Feedback(
            adaptation_id=aid,
            round=len(past) + 1,
            result="done",
            branch=row.branch,
            ai_reply_json=to_json({"stage": "done"}),
        )
        db.add(rec)
        db.commit()
        return {
            "stage": "done",
            "round": len(past) + 1,
            "title": "记下了 ✓",
            "message": "这条解法已经留在原帖的场景应用网上——下一个人遇到同样的处境，不用从头撞一遍墙。",
            "sub": "你刚刚给后来者立了一个路标。",
        }

    stuck_past = [r for r in past if r.result == "stuck"]
    round_n = len(stuck_past) + 1
    solution = _load_json(row.solution_json)

    # ---- 阶段一：只要 AI 的归因追问（还没到出结论的时候） ----
    if not (body.user_note or "").strip():
        lead = ""
        if round_n >= 2:
            lead = (
                f"连续 {round_n} 条路都不通——这恰恰说明你的场景比原帖特殊得多。"
                "AI 正在换思路：从「照搬原帖」切换到「基于你的约束重新设计」。"
            )
        return {
            "stage": "ask",
            "round": round_n,
            "lead": lead,
            "question": ask_question(body.block_type or "", body.block_step, solution),
            "placeholder": "就写一句，比如「报 ORE 溢出，缓冲区好像没进中断」",
            "reassure": "别急。排除一个方向，也是进展。",
        }

    # ---- 阶段二：出归因结论 ----
    prev_rounds = [{"round": r.round, "attribution": r.attribution} for r in stuck_past]
    tried = [r.branch for r in stuck_past]
    for i in chain:
        a = db.query(Adaptation).filter(Adaptation.id == i).first()
        if a and a.branch:
            tried.append(a.branch)

    verdict = rediagnose(
        round_n, body.block_type or "", body.block_step, body.user_note.strip(),
        prev_rounds, tried,
    )

    rec = Feedback(
        adaptation_id=aid,
        round=round_n,
        result="stuck",
        block_type=body.block_type,
        block_step=body.block_step,
        user_note=body.user_note.strip(),
        attribution=verdict["attribution"],
        branch=row.branch,
        ai_question=verdict.get("headline", ""),
        ai_reply_json=to_json(verdict),
    )
    db.add(rec)
    db.commit()
    return verdict
