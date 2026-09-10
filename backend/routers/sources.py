import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import SessionLocal, get_db
from models import Adaptation, SourcePost
from schemas import AdaptationOut, SourcePostOut
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
    posts = db.query(SourcePost).all()
    data = [SourcePostOut.model_validate(p, from_attributes=True).model_dump() for p in posts]
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
