from typing import Any, Optional

from pydantic import BaseModel


class SourcePostOut(BaseModel):
    id: int
    content_type: Optional[str] = None
    title: str
    author: Optional[str] = None
    authority_level: Optional[str] = None
    summary: Optional[str] = None
    url: Optional[str] = None
    source: Optional[str] = None
    enrich_status: Optional[str] = None
    category: Optional[str] = "未分类"


class AdaptationOut(BaseModel):
    id: int
    post_id: int
    scene_tag: Optional[str] = None
    user_scene: str
    user_constraint: Optional[str] = None
    provider: Optional[str] = None
    created_at: Optional[str] = None


class AdaptExtractIn(BaseModel):
    post_id: int


class AdaptRunIn(BaseModel):
    post_id: int
    scene_tag: Optional[str] = None
    user_scene: str
    user_constraint: Optional[str] = None


class AdaptExtractOut(BaseModel):
    post_id: int
    origin: dict


class AdaptRunOut(BaseModel):
    adaptation: AdaptationOut
    origin: dict
    diff: dict
    solution: dict
