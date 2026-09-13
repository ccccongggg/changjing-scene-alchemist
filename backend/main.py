import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from database import init_db
from routers import sources
from routers import adapt
from routers import starmap

# 前端构建产物：优先 backend/site（部署包），其次 ../frontend/dist（本地开发）
_CANDIDATE_DIRS = [
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "site"),
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend", "dist"),
]
DIST_DIR = next((d for d in _CANDIDATE_DIRS if os.path.isdir(d)), None)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """启动建表 + 灌种子（幂等）；替代已废弃的 @app.on_event("startup")。"""
    init_db()
    from seed import seed_adaptations, seed_posts

    seed_posts()
    seed_adaptations()
    yield


app = FastAPI(title="场景炼金师 API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sources.router, prefix="/api")
app.include_router(adapt.router, prefix="/api")
app.include_router(starmap.router, prefix="/api")


@app.get("/api/health")
def health():
    from config import USE_MOCK, ZHIHU_ACCESS_SECRET, effective_provider, mask_secret

    return {
        "code": 0,
        "data": {
            "status": "ok",
            "use_mock": USE_MOCK,
            "provider": effective_provider(),
            "zhihu_secret": mask_secret(ZHIHU_ACCESS_SECRET),
        },
        "msg": "ok",
    }


# ---- 部署模式：后端直接服务前端静态文件（SPA 回退到 index.html） ----
if DIST_DIR:
    assets_dir = os.path.join(DIST_DIR, "assets")
    if os.path.isdir(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}")
    def spa_fallback(full_path: str):
        """非 /api 路径全部回退到 index.html（vue-router history 模式）。"""
        if full_path.startswith("api/"):
            return {"code": 404, "data": None, "msg": "not found"}
        # 其他静态资源（如 /liukan/*.gif）按文件返回
        file_path = os.path.join(DIST_DIR, full_path)
        if full_path and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(DIST_DIR, "index.html"))


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT") or os.getenv("APP_PORT") or 8000)
    uvicorn.run(app, host="0.0.0.0", port=port)
