from __future__ import annotations
import json
import os
import urllib.error
import urllib.request


class FactualProviderError(RuntimeError):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


class FactualProvider:
    def complete(self, system: str, user: str) -> str:
        raise NotImplementedError


class MockFactualProvider(FactualProvider):
    def __init__(self, raw: str | None = None, error_code: str | None = None, queue: list[str] | None = None):
        self.raw = raw
        self.error_code = error_code
        self.queue = list(queue or [])
        self.calls = 0
        self.messages: list[tuple[str, str]] = []

    def complete(self, system: str, user: str) -> str:
        self.calls += 1
        self.messages.append((system, user))
        if self.error_code:
            raise FactualProviderError(self.error_code)
        if self.queue:
            return self.queue.pop(0)
        if self.raw is None:
            raise FactualProviderError("NO_SCRIPT")
        return self.raw


class DeepSeekFactualProvider(FactualProvider):
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 800,
        timeout_sec: float = 60.0,
        retries: int = 1,
        json_mode: bool = False,
    ):
        self.api_key = api_key if api_key is not None else os.environ.get("DEEPSEEK_API_KEY", "")
        self.base_url = (base_url if base_url is not None else os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")).rstrip("/")
        self.model = model if model is not None else os.environ.get("DEEPSEEK_MODEL", "")
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout_sec = timeout_sec
        self.retries = retries
        self.json_mode = json_mode
        if not self.api_key or not self.model:
            raise FactualProviderError("MISSING_CONFIG")

    def _url(self) -> str:
        if self.base_url.endswith("/v1"):
            return self.base_url + "/chat/completions"
        return self.base_url + "/v1/chat/completions"

    def complete(self, system: str, user: str) -> str:
        payload = {
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        if self.json_mode:
            payload["response_format"] = {"type": "json_object"}
        body = json.dumps(payload).encode("utf-8")
        last = "NETWORK"
        for _ in range(self.retries + 1):
            request = urllib.request.Request(
                self._url(), data=body, method="POST",
                headers={"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"},
            )
            try:
                with urllib.request.urlopen(request, timeout=self.timeout_sec) as response:
                    payload = json.loads(response.read().decode("utf-8"))
                message = payload["choices"][0]["message"]
                content = message.get("content") or message.get("reasoning_content") or ""
                if isinstance(content, list):
                    parts = []
                    for item in content:
                        if isinstance(item, dict):
                            parts.append(str(item.get("text") or item.get("content") or ""))
                        else:
                            parts.append(str(item))
                    content = "".join(parts)
                if not isinstance(content, str) or not content.strip():
                    raise FactualProviderError("EMPTY_CONTENT")
                return content
            except FactualProviderError:
                raise
            except urllib.error.HTTPError as exc:
                last = f"HTTP_{exc.code}"
                if exc.code < 500:
                    raise FactualProviderError(last) from None
            except TimeoutError:
                last = "TIMEOUT"
            except Exception:
                last = "NETWORK"
        raise FactualProviderError(last)
