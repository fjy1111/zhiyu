"""LLM providers. Secrets stay in environment variables."""
from __future__ import annotations
import json
import os
import urllib.error
import urllib.request
from zhiyu.semantic.prompt import SYSTEM_PROMPT, build_user_prompt


class SemanticProviderError(RuntimeError):
    def __init__(self, code: str, message: str = ""):
        super().__init__(message or code)
        self.code = code


class SemanticProvider:
    def complete(self, text: str, observations: list[dict]) -> str:
        raise NotImplementedError


class MockSemanticProvider(SemanticProvider):
    """Deterministic test double. Must not be used for official metrics."""

    def __init__(self, raw: str | None = None, error_code: str | None = None):
        self.raw = raw
        self.error_code = error_code
        self.calls = 0

    def complete(self, text: str, observations: list[dict]) -> str:
        self.calls += 1
        if self.error_code:
            raise SemanticProviderError(self.error_code)
        if self.raw is not None:
            return self.raw
        return json.dumps({
            "observations": [{
                "intent": "NO_CONTROL",
                "mechanism": None,
                "confidence": "HIGH",
                "excerpt": "",
                "rationale": "no model-control intent in ordinary text",
                "source_rule_ids": [],
            }]
        })


class DeepSeekSemanticProvider(SemanticProvider):
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 800,
        timeout_sec: float = 60.0,
        retries: int = 1,
    ):
        self.api_key = api_key if api_key is not None else os.environ.get("DEEPSEEK_API_KEY", "")
        self.base_url = (base_url if base_url is not None else os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")).rstrip("/")
        self.model = model if model is not None else os.environ.get("DEEPSEEK_MODEL", "")
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout_sec = timeout_sec
        self.retries = retries
        if not self.api_key or not self.model:
            raise SemanticProviderError("MISSING_CONFIG")

    def _url(self) -> str:
        if self.base_url.endswith("/v1"):
            return self.base_url + "/chat/completions"
        return self.base_url + "/v1/chat/completions"

    def complete(self, text: str, observations: list[dict]) -> str:
        body = json.dumps({
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": build_user_prompt(text, observations)},
            ],
        }).encode("utf-8")
        last_code = "NETWORK"
        attempts = self.retries + 1
        for _ in range(attempts):
            request = urllib.request.Request(
                self._url(),
                data=body,
                method="POST",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}",
                },
            )
            try:
                with urllib.request.urlopen(request, timeout=self.timeout_sec) as response:
                    payload = json.loads(response.read().decode("utf-8"))
                content = payload["choices"][0]["message"]["content"]
                if not isinstance(content, str) or not content.strip():
                    raise SemanticProviderError("EMPTY_CONTENT")
                return content
            except SemanticProviderError:
                raise
            except urllib.error.HTTPError as exc:
                last_code = f"HTTP_{exc.code}"
                if exc.code < 500:
                    raise SemanticProviderError(last_code) from None
            except TimeoutError:
                last_code = "TIMEOUT"
            except Exception:
                last_code = "NETWORK"
        raise SemanticProviderError(last_code)
