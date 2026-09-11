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
    branch = Column(String)                     # 这次走的方案分支（复诊换思路时要避开它）
    parent_id = Column(Integer)                 # 复诊链：指向被复诊的那一版方案
    created_at = Column(String, default=_now)


class Feedback(Base):
    """一次「复诊」：用户试过方案之后的反馈 + AI 归因。

    记录的是**排除过程**，不是失败——每一条都让棋盘变小一圈。
    """

    __tablename__ = "feedbacks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    adaptation_id = Column(Integer, nullable=False)
    round = Column(Integer, default=1)          # 第几次复诊（同一方案累加）
    result = Column(String, nullable=False)     # done / stuck
    block_type = Column(String)                 # step_error / phenomenon / other
    block_step = Column(Integer)                # 卡在第 N 步（block_type=step_error 时）
    user_note = Column(Text)                    # 用户补充的一句
    attribution = Column(String)                # param_wrong / scene_mismatch / constraint_conflict
    branch = Column(String)                     # 当时走的方案分支快照（下次换思路要避开）
    ai_question = Column(Text)                  # 归因追问的那句
    ai_reply_json = Column(Text)                # 棋盘式回复 JSON（已排除 / 剩余可试 / 下一步）
    created_at = Column(String, default=_now)
