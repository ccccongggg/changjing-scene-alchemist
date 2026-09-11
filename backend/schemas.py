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
    branch: Optional[str] = None                # 方案分支（复诊换思路时避开它）
    parent_id: Optional[int] = None             # 复诊链：被复诊的那一版
    created_at: Optional[str] = None


class FeedbackIn(BaseModel):
    """复诊反馈。user_note 为空 = 只要 AI 的归因追问；有值 = 出归因结论。"""

    result: str                                  # done / stuck
    block_type: Optional[str] = None             # step_error / phenomenon / other
    block_step: Optional[int] = None
    user_note: Optional[str] = None


class AdaptExtractIn(BaseModel):
    post_id: int


class AdaptRunIn(BaseModel):
    post_id: int
    scene_tag: Optional[str] = None
    user_scene: str
    user_constraint: Optional[str] = None
    avoid: Optional[list] = None                 # 复诊：要避开的方案分支名
    parent_id: Optional[int] = None              # 复诊：被复诊的那一版方案 id（串成复诊链）


class AdaptExtractOut(BaseModel):
    post_id: int
    origin: dict


class AdaptRunOut(BaseModel):
    adaptation: AdaptationOut
    origin: dict
    diff: dict
    solution: dict
