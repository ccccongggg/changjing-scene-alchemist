# 场景炼金师 · 同帖千面

把知乎经验帖按读者的真实场景做适配迁移：同一篇好帖，在不同真实处境下长出不同的解法，沉淀成一张可检索的「场景应用网」。

> 知乎黑客松 · 场景炼金师方向 2（场景迁移引擎）作品。当前版本：**v1.2（星图内嵌场景工坊）**。

## 产品闭环

1. **收藏台**：收藏知乎好帖，自定义分类、关键词搜索
2. **场景工坊**：描述你的真实场景与约束 → AI 解构原帖、分析差异、起草迁移方案
3. **星图（同帖千面）**：把一篇帖子的所有真实处境铺成一张星辰图——太阳=原帖，每颗星=一个真实处境，三层轨道环=照搬要改多深（改参数 / 动结构 / 换方案），橙色虚线=走不通后换思路重炼的复诊链。点「＋ 炼一个我的处境」可在星图里直接发散一颗临时星、拉近视角，并把场景工坊拉进右侧面板，填好场景一键生成你的解法。
4. **我的贡献**：人验证后方案入库，沉淀为可复用的场景应用网（蛛网可视化）

## 版本记录

- **v1.2（2026-09-14）**：星图新增「炼一个我的处境」创建模式——星图内嵌场景工坊，选 / 填场景后一键生成新处境并自动落库，太阳计数 +1，右侧面板切到新处境详情。修复紧凑模式下提交按钮被挤出可视区的 bug。
- **v1.1（2026-09-12）**：复诊闭环（P0）——失败反馈入口 + 三分归因追问 + 换路必须真的避开已走分支。
- **v1.0（2026-09-11）**：知乎风 UI + 收藏台 + 场景工坊 + 蛛网可视化。

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
│   ├── routers/         # sources / adapt / starmap 路由
│   ├── seed.py          # 幂等种子数据
│   └── changjing.db     # SQLite（启动自动建表+灌种子，含演示数据）
├── frontend/
│   ├── src/views/       # 首页 / 收藏台 / 场景工坊 / 星图 StarMap
│   ├── src/components/  # 蛛网图 ScenarioGraph、场景表单 SceneForm 等
│   └── vite.config.js   # dev 5173 / preview 4173
└── docs/                # 设计与执行文档
```

> `backend/site/`（前端构建产物）、`frontend/dist/` 为生成物，已加入 `.gitignore`，不纳入版本库；克隆后需 `npm run build` 再启动后端。

## 本地开发

```bash
# 1) 构建前端
cd frontend
npm install
npm run build          # 产物输出到 frontend/dist，被后端 site 目录引用

# 2) 启动后端（一体化模式，直接访问 http://localhost:8000）
cd ../backend
pip install -r requirements.txt
python main.py
```

## 环境变量（backend/.env，可选）

| 变量 | 说明 | 默认 |
|---|---|---|
| `USE_MOCK` | true 时走内置场景分支 Mock（无需任何密钥即可演示） | true |
| `ZHIHU_ACCESS_SECRET` | 知乎直答密钥 | 空 |
| `LLM_PROVIDER` | zhida / external / mock | 自动 |
| `APP_PORT` | 后端端口 | 8000 |

## 在线演示

- **演示地址（WorkBuddy 托管）**：https://98273abaf38940cd861d721932cef2bf.app.workbuddy.host
  - 本仓库源码托管在 GitHub；**可交互演示**部署在 WorkBuddy 的远端沙箱（GitHub Pages 只能托管静态前端，跑不了 FastAPI 后端与创建模式所需的接口）。
  - 沙箱空闲时会休眠，首次访问有几秒冷启动，属正常现象。

## 部署到自有服务器

`backend/main.py` 优先监听 `PORT` 环境变量并服务 `backend/site/` 下的前端产物。把 `frontend/dist` 同步到 `backend/site` 后即可作为单端口 HTTP 服务运行：

```bash
cd frontend && npm run build
cd ../backend && rm -rf site/assets && cp -r ../frontend/dist/assets site/assets && cp ../frontend/dist/index.html site/index.html
PORT=8000 pip install -r requirements.txt && python main.py
```

如需永久公网访问，可将后端部署到 Render / Railway / Fly.io 等支持 Python 的 PaaS；前端静态部分也可单独放 GitHub Pages（但创建模式依赖后端接口，需前后端同址或配置跨域）。
