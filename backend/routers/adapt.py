from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Adaptation, SourcePost
from schemas import AdaptExtractIn, AdaptExtractOut, AdaptRunIn, AdaptRunOut, AdaptationOut
from ai_engine import deconstruct, generate, to_json

router = APIRouter()


@router.post("/adapt/extract", response_model=AdaptExtractOut)
def extract(body: AdaptExtractIn, db: Session = Depends(get_db)):
    """A1：解构原帖，返回结构化 origin（同一帖只算一次，真实通道下省额度）。"""
    post = db.query(SourcePost).filter(SourcePost.id == body.post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="post not found")
    origin, _provider = deconstruct(post)
    return {"post_id": post.id, "origin": origin}


@router.post("/adapt/run", response_model=AdaptRunOut)
def run(body: AdaptRunIn, db: Session = Depends(get_db)):
    """A2+A3：差异分析 + 方案迁移，落库一条 Adaptation 记录。"""
    post = db.query(SourcePost).filter(SourcePost.id == body.post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="post not found")

    origin, diff, solution, provider = generate(
        post, body.scene_tag or "", body.user_scene, body.user_constraint or ""
    )

    rec = Adaptation(
        post_id=post.id,
        scene_tag=body.scene_tag,
        user_scene=body.user_scene,
        user_constraint=body.user_constraint,
        origin_json=to_json(origin),
        diff_json=to_json(diff),
        solution_json=to_json(solution),
        provider=provider,
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)

    adaptation = AdaptationOut.model_validate(rec, from_attributes=True).model_dump()
    return {"adaptation": adaptation, "origin": origin, "diff": diff, "solution": solution}
