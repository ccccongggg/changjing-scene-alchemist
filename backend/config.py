"""全局配置：从 .env / 环境变量读取，作为真实 LLM 通道的「配置门控」。

优先级：USE_MOCK=true 时无论配了什么都走 Mock（断网也能演示，永不翻车）。
USE_MOCK=false 时按 LLM_PROVIDER 选 zhida（知乎直答）/ external（任意 OpenAI 兼容模型）。
真实通道任何异常都会在上层自动降级回 Mock。

严禁把 Access Secret 打进日志/前端/Git；.env 已在 .gitignore 中排除。
"""

import os

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))


def _b(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).strip().lower() in ("1", "true", "yes", "on")


# ---- 总开关 ----------------------------------------------------------------
USE_MOCK: bool = _b("USE_MOCK", "true")

# ---- 知乎开放平台 ----------------------------------------------------------
ZHIHU_ACCESS_SECRET: str = os.getenv("ZHIHU_ACCESS_SECRET", "").strip()
ZHIHU_API_BASE: str = os.getenv("ZHIHU_API_BASE", "https://developer.zhihu.com").rstrip("/")

# ---- LLM 通道 --------------------------------------------------------------
# zhida / external / mock
LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "zhida").strip().lower()
ZHIDA_MODEL: str = os.getenv("ZHIDA_MODEL", "zhida-thinking-1p5").strip()
ZHIDA_FAST_MODEL: str = os.getenv("ZHIDA_FAST_MODEL", "zhida-fast-1p5").strip()

EXTERNAL_BASE_URL: str = os.getenv("EXTERNAL_BASE_URL", "https://api.deepseek.com/v1").rstrip("/")
EXTERNAL_API_KEY: str = os.getenv("EXTERNAL_API_KEY", "").strip()
EXTERNAL_MODEL: str = os.getenv("EXTERNAL_MODEL", "deepseek-chat").strip()

# ---- 通用 ------------------------------------------------------------------
REQUEST_TIMEOUT: float = float(os.getenv("REQUEST_TIMEOUT", "20"))


def effective_provider() -> str:
    """当前真正会走哪个通道（供界面小标签显示）。"""
    if USE_MOCK:
        return "mock"
    if LLM_PROVIDER == "external":
        return "external" if EXTERNAL_API_KEY else "mock"
    if LLM_PROVIDER == "zhida":
        return "zhida" if ZHIHU_ACCESS_SECRET else "mock"
    return "mock"


def mask_secret(s: str) -> str:
    """日志只打 Secret 前 4 位 + ***，严禁打印全量密钥。"""
    if not s:
        return "(empty)"
    return s[:4] + "***" if len(s) > 4 else "***"
