"""LLM 抽象层：Zhida（知乎直答，OpenAI 兼容）/ External（任意 OpenAI 兼容模型）。

设计原则：
1. 只负责"把 messages 换成文本"，不认识任何业务字段；
2. JSON 容错三级兜底：剥 ```json 围栏 → 重试 1 次 → 包成 {"fallbackText": ...}，**永不白屏**；
3. 任何异常都抛中文 LLMError，由 ai_engine 捕获后自动降级 Mock；
4. 日志/异常里绝不出现完整密钥（config.mask_secret）。
"""

import json
import os
import re
import time

import httpx

from config import (
    EXTERNAL_API_KEY,
    EXTERNAL_BASE_URL,
    EXTERNAL_MODEL,
    REQUEST_TIMEOUT,
    USE_MOCK,
    ZHIHU_ACCESS_SECRET,
    ZHIHU_API_BASE,
    ZHIDA_FAST_MODEL,
    ZHIDA_MODEL,
    effective_provider,
    mask_secret,
)

PROMPT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "prompts")


class LLMError(Exception):
    """真实通道不可用（鉴权/频控/配额/网络/坏 JSON），上层据此降级 Mock。"""


def load_prompt(name: str) -> str:
    with open(os.path.join(PROMPT_DIR, name), "r", encoding="utf-8") as f:
        return f.read()


def _strip_fences(text: str) -> str:
    """剥掉 ```json ... ``` 围栏（模型最爱加这个）。"""
    t = (text or "").strip()
    t = re.sub(r"^```(?:json|JSON)?\s*", "", t)
    t = re.sub(r"\s*```$", "", t)
    return t.strip()


def parse_json(text: str) -> dict:
    """严格解析；失败抛 LLMError。"""
    t = _strip_fences(text)
    # 模型偶尔在 JSON 前后加解释文字：截取第一个 { 到最后一个 }
    if not t.startswith("{"):
        i, j = t.find("{"), t.rfind("}")
        if i >= 0 and j > i:
            t = t[i : j + 1]
    try:
        obj = json.loads(t)
    except Exception as e:  # noqa: BLE001
        raise LLMError(f"JSON 解析失败：{e}")
    if not isinstance(obj, dict):
        raise LLMError("模型输出不是 JSON 对象")
    return obj


def _post(url: str, headers: dict, payload: dict) -> str:
    with httpx.Client(timeout=REQUEST_TIMEOUT) as cli:
        r = cli.post(url, headers=headers, json=payload)
    if r.status_code >= 400:
        raise LLMError(f"HTTP {r.status_code}：{r.text[:200]}")
    body = r.json()
    # 官方错误码：20001 鉴权 / 30001 频控 / 30002 配额
    code = body.get("Code") or body.get("code")
    if code not in (None, 0, "0", 200):
        msg = body.get("Message") or body.get("msg") or "未知错误"
        if str(code) == "30001":
            time.sleep(1.5)
            raise LLMError(f"触发频控(30001)：{msg}")
        if str(code) == "30002":
            raise LLMError(f"配额耗尽(30002)：{msg}")
        if str(code) == "20001":
            raise LLMError(f"鉴权失败(20001)：{msg}｜Secret={mask_secret(ZHIHU_ACCESS_SECRET)}")
        raise LLMError(f"接口错误 {code}：{msg}")
    try:
        return body["choices"][0]["message"]["content"]
    except Exception:  # noqa: BLE001
        raise LLMError("响应缺少 choices[0].message.content")


def chat(messages: list, fast: bool = False) -> str:
    """按当前 provider 发送对话，返回模型文本。"""
    provider = effective_provider()
    if provider == "mock":
        raise LLMError("当前为 Mock 模式（USE_MOCK=true 或缺少密钥）")

    payload = {"messages": messages, "temperature": 0.2, "stream": False}

    if provider == "zhida":
        url = f"{ZHIHU_API_BASE}/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {ZHIHU_ACCESS_SECRET}",
            "X-Request-Timestamp": str(int(time.time())),
            "Content-Type": "application/json",
        }
        payload["model"] = ZHIDA_FAST_MODEL if fast else ZHIDA_MODEL
    else:
        url = f"{EXTERNAL_BASE_URL}/chat/completions"
        headers = {
            "Authorization": f"Bearer {EXTERNAL_API_KEY}",
            "Content-Type": "application/json",
        }
        payload["model"] = EXTERNAL_MODEL

    return _post(url, headers, payload)


def chat_json(messages: list, fast: bool = False, retry: int = 1) -> dict:
    """调模型并解析成 dict；坏 JSON 重试 1 次，再失败降级为 fallbackText。"""
    last = None
    for _ in range(retry + 1):
        try:
            text = chat(messages, fast=fast)
            return parse_json(text)
        except LLMError as e:
            last = e
            continue
        except Exception as e:  # noqa: BLE001 —— 网络层异常同样降级
            last = e
            continue
    return {"fallbackText": f"模型输出不可用（{last}），已降级展示。", "_degraded": True}


__all__ = [
    "LLMError",
    "load_prompt",
    "chat",
    "chat_json",
    "parse_json",
    "effective_provider",
    "USE_MOCK",
]
