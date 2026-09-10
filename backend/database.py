import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_URL = os.getenv("DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'changjing.db')}")

engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    import models  # noqa: F401  ensure models are registered
    Base.metadata.create_all(bind=engine)
    _migrate_category_column()


def _migrate_category_column():
    """幂等地为 source_posts 表加 category 列并回填默认值。"""
    from sqlalchemy import inspect, text
    inspector = inspect(engine)
    columns = [c["name"] for c in inspector.get_columns("source_posts")]
    if "category" not in columns:
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE source_posts ADD COLUMN category TEXT DEFAULT '未分类'"))
            conn.execute(text("UPDATE source_posts SET category = '未分类' WHERE category IS NULL"))
            conn.commit()
