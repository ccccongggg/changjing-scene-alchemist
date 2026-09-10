# 场景炼金师 · 同帖千面

把知乎经验帖按读者的真实场景做适配迁移：同一篇好帖，在不同真实处境下长出不同的解法，沉淀成一张可检索的「场景应用网」。

> 知乎黑客松 · 场景炼金师方向 2（场景迁移引擎）作品，非最终版本，持续迭代中。

## 产品闭环

1. **收藏台**：收藏知乎好帖，自定义分类、关键词搜索
2. **场景工坊**：描述你的真实场景与约束 → AI 解构原帖、分析差异、起草迁移方案
3. **我的贡献**：人验证后方案入库，沉淀为可复用的场景应用网（蛛网可视化）

## 技术栈

- 后端：FastAPI + SQLAlchemy + SQLite（AI 双通道：Mock / 知乎直答 OpenAI 兼容接口，失败自动降级）
- 前端：Vue 3 + Vite + Vue Router + axios，知乎风 UI
- 部署：单进程一体化（FastAPI 直接服务前端静态资源，SQLite 持久化）

## 目录结构

```
changjing/
├── backend/
│   ├── main.py          # FastAPI 入口（含 SPA 静态服务，监听 PORT 环境变量）
│   ├── ai_engine.py     # 场景分支引擎 + Provider 降级
│   ├── ai/llm.py        # LLM 通道封装
│   ├── prompts/         # 解构/差异/迁移三段提示词
│   ├── routers/         # sources / adapt 路由
│   ├── seed.py          # 幂等种子数据
│   ├── site/            # 前端构建产物（部署时由后端直接服务）
│   └── changjing.db     # SQLite（启动自动建表+灌种子）
├── frontend/
│   ├── src/views/       # 首页 / 收藏台 / 场景工坊 / 我的贡献
│   ├── src/components/  # 蛛网图 ScenarioGraph 等
│   └── vite.config.js   # dev 5173 / preview 4173
└── docs/                # 设计与执行文档
```

## 本地开发

```bash
# 后端（:8000，一体化模式，直接访问 http://localhost:8000）
cd backend
pip install -r requirements.txt
python main.py

# 前端开发模式（:5173，带 HMR）
cd frontend
npm install
npm run dev
```

## 环境变量（backend/.env，可选）

| 变量 | 说明 | 默认 |
|---|---|---|
| `USE_MOCK` | true 时走内置场景分支 Mock | true |
| `ZHIHU_ACCESS_SECRET` | 知乎直答密钥 | 空 |
| `LLM_PROVIDER` | zhida / external / mock | 自动 |
| `APP_PORT` | 后端端口 | 8000 |

## 部署

`backend/main.py` 会优先监听 `PORT` 环境变量并服务 `backend/site/` 下的前端产物：

```bash
cd backend
pip install -r requirements.txt
PORT=8000 python main.py
```
