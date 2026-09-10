from datetime import datetime

from sqlalchemy import Column, Integer, String, Text
from database import Base


def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class SourcePost(Base):
    """来源帖子：知乎收藏 / 演示种子。"""

    __tablename__ = "source_posts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    zhihu_content_id = Column(String)            # 官方 ContentID，去重键
    content_type = Column(String)               # answer / article
    title = Column(String, nullable=False)
    author = Column(String)
    authority_level = Column(String)            # 官方权威等级 1~4
    summary = Column(Text)                      # 收藏接口摘要
    content_text = Column(Text)                 # 搜索反查补全的长文本（可空）
    url = Column(String)
    fav_time = Column(Integer)
    source = Column(String, default="seed")     # zhihu / seed
    enrich_status = Column(String, default="none")  # none / searched / failed
    category = Column(String, default="未分类")     # 用户自定义分类 / 文件夹
    created_at = Column(String, default=_now)


class Adaptation(Base):
    """一次场景适配 = 一条记录（同一帖子可对多个场景多次适配，即"一帖多吃"）。"""

    __tablename__ = "adaptations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(Integer, nullable=False)
    scene_tag = Column(String)                  # 给这次适配起个短名
    user_scene = Column(String, nullable=False)
    user_constraint = Column(String)
    origin_json = Column(Text)                  # A1 解构结果
    diff_json = Column(Text)                    # A2 差异分析
    solution_json = Column(Text)                # A3 方案迁移
    provider = Column(String)                   # zhida / external / mock
    created_at = Column(String, default=_now)
