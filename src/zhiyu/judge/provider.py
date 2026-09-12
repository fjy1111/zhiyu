"""Judge-only DeepSeek transport; factual provider behavior stays frozen."""
from __future__ import annotations
import json
import os
import urllib.error
import urllib.request
from zhiyu.factual.provider import FactualProvider, FactualProviderError


class DeepSeekJudgeProvider(FactualProvider):
    def __init__(self, api_key=None, base_url=None, model=None, temperature=0.0, max_tokens=800, timeout_sec=60.0, retries=1):
        self.api_key = api_key if api_key is not None else os.environ.get("DEEPSEEK_API_KEY", "")
        self.base_url = (base_url if base_url is not None else os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")).rstrip("/")
        self.model = model if model is not None else os.environ.get("DEEPSEEK_MODEL", "")
        self.temperature, self.max_tokens, self.timeout_sec, self.retries = temperature, max_tokens, timeout_sec, retries
        if not self.api_key or not self.model:
            raise FactualProviderError("MISSING_CONFIG")

    def complete(self, system: str, user: str) -> str:
        body = json.dumps({"model": self.model, "temperature": self.temperature, "max_tokens": self.max_tokens,
            "response_format": {"type": "json_object"},
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}).encode("utf-8")
        last = "NETWORK"
        for _ in range(self.retries + 1):
            request = urllib.request.Request(self.base_url + ("/chat/completions" if self.base_url.endswith("/v1") else "/v1/chat/completions"), data=body, method="POST", headers={"Content-Type":"application/json", "Authorization":f"Bearer {self.api_key}"})
            try:
                with urllib.request.urlopen(request, timeout=self.timeout_sec) as response:
                    message = json.loads(response.read().decode("utf-8"))["choices"][0]["message"]
                content = message.get("content") or message.get("reasoning_content") or ""
                if isinstance(content, list):
                    content = "".join(str(item.get("text") or item.get("content") or "") if isinstance(item, dict) else str(item) for item in content)
                if not isinstance(content, str) or not content.strip(): raise FactualProviderError("EMPTY_CONTENT")
                return content
            except FactualProviderError: raise
            except urllib.error.HTTPError as exc:
                last = f"HTTP_{exc.code}"
                if exc.code < 500: raise FactualProviderError(last) from None
            except TimeoutError: last = "TIMEOUT"
            except Exception: last = "NETWORK"
        raise FactualProviderError(last)
