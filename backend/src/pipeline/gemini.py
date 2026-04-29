import json
import os
import re
import threading
import time
import urllib.error
import urllib.request
from functools import lru_cache
from typing import Any, Dict


def _prompt_preview(prompt: str, limit: int = 120) -> str:
    condensed = " ".join(prompt.split())
    if len(condensed) <= limit:
        return condensed
    return f"{condensed[:limit].rstrip()}..."


def _log_gemini_request(model: str, temperature: float, attempt: int, prompt: str) -> None:
    print(
        "[Gemini] Sending request "
        f"model={model} temperature={temperature} attempt={attempt} "
        f'prompt="{_prompt_preview(prompt)}"'
    )


def _safe_json_loads(raw_text: str) -> Dict[str, Any]:
    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-zA-Z0-9]*\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(0))


def _env_flag(name: str, default: bool = False) -> bool:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    return raw_value.strip().lower() in {"1", "true", "yes", "on"}


def _env_float(name: str, default: float) -> float:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    try:
        return float(raw_value)
    except (TypeError, ValueError):
        return default


def _env_int(name: str, default: int) -> int:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    try:
        return int(raw_value)
    except (TypeError, ValueError):
        return default


def gemini_explanations_enabled() -> bool:
    return _env_flag("GEMINI_EXPLANATIONS_ENABLED", default=False)


def gemini_reranking_enabled() -> bool:
    return _env_flag("GEMINI_RERANKING_ENABLED", default=False)


def gemini_rerank_top_n() -> int:
    return max(1, _env_int("GEMINI_RERANK_TOP_N", 8))


def wait_for_explanation_rate_limit(song_count: int) -> None:
    if song_count <= 0:
        return
    delay_per_song_seconds = max(
        0.0,
        _env_float("GEMINI_EXPLANATION_DELAY_PER_SONG_SECONDS", 1.5),
    )
    if delay_per_song_seconds <= 0:
        return
    time.sleep(delay_per_song_seconds * song_count)


_GEMINI_REQUEST_LOCK = threading.Lock()
_last_gemini_request_started_at = 0.0


def _wait_for_gemini_request_slot() -> None:
    global _last_gemini_request_started_at

    min_interval_seconds = max(
        0.0,
        _env_float("GEMINI_MIN_REQUEST_INTERVAL_SECONDS", 1.5),
    )
    if min_interval_seconds <= 0:
        return

    with _GEMINI_REQUEST_LOCK:
        now = time.monotonic()
        sleep_for = max(0.0, min_interval_seconds - (now - _last_gemini_request_started_at))
        if sleep_for > 0:
            time.sleep(sleep_for)
            now = time.monotonic()
        _last_gemini_request_started_at = now


def _retry_after_seconds(exc: urllib.error.HTTPError) -> float | None:
    retry_after = exc.headers.get("Retry-After")
    if not retry_after:
        return None
    try:
        return max(0.0, float(retry_after))
    except (TypeError, ValueError):
        return None


@lru_cache(maxsize=128)
def _cached_gemini_response(
    api_key: str,
    model: str,
    prompt: str,
    temperature: float,
) -> Dict[str, Any]:
    endpoint = (
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        f"?key={api_key}"
    )
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": temperature,
            "responseMimeType": "application/json",
        },
    }
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    max_retries = max(0, _env_int("GEMINI_HTTP_429_MAX_RETRIES", 2))
    attempt = 0
    while True:
        attempt += 1
        _wait_for_gemini_request_slot()
        _log_gemini_request(model, temperature, attempt, prompt)
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                raw = json.loads(response.read().decode("utf-8"))
            break
        except urllib.error.HTTPError as exc:
            if exc.code == 429 and attempt <= max_retries:
                retry_after_seconds = _retry_after_seconds(exc)
                backoff_seconds = retry_after_seconds if retry_after_seconds is not None else float(attempt * 2)
                time.sleep(backoff_seconds)
                continue
            raise RuntimeError(f"Gemini request failed: HTTP Error {exc.code}: {exc.reason}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Gemini request failed: {exc}") from exc

    candidates = raw.get("candidates", [])
    if not candidates:
        raise RuntimeError("Gemini returned no candidates")

    parts = candidates[0].get("content", {}).get("parts", [])
    text = "".join(str(part.get("text", "")) for part in parts)
    return _safe_json_loads(text)


def _post_to_gemini(prompt: str, temperature: float = 0.2) -> Dict[str, Any]:
    api_key = os.getenv("GEMINI_API_KEY")
    model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured")
    return _cached_gemini_response(api_key, model, prompt, temperature)
