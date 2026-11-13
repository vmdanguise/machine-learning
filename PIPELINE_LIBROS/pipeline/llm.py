"""Cliente minimo para el gateway LiteLLM (API Anthropic /v1/messages). Sin dependencias externas."""
import base64
import json
import time
import urllib.request
import urllib.error

from config import LLM_BASE, LLM_TOKEN, D_LOG

USAGE_LOG = D_LOG / "usage.jsonl"


class LLMError(RuntimeError):
    pass


def call(model, system, content, max_tokens=8000, temperature=0.0, tag="", retries=5, timeout=600):
    """content: str o lista de bloques Anthropic. Devuelve texto."""
    if isinstance(content, str):
        content = [{"type": "text", "text": content}]
    body = {
        "model": model,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "system": system,
        "messages": [{"role": "user", "content": content}],
    }
    data = json.dumps(body).encode("utf-8")
    headers = {
        "x-api-key": LLM_TOKEN,
        "Authorization": "Bearer " + LLM_TOKEN,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    last = None
    for attempt in range(retries):
        t0 = time.time()
        try:
            req = urllib.request.Request(LLM_BASE.rstrip("/") + "/v1/messages", data=data, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                resp = json.loads(r.read().decode("utf-8"))
            text = "".join(b.get("text", "") for b in resp.get("content", []) if b.get("type") == "text")
            usage = resp.get("usage", {})
            with open(USAGE_LOG, "a", encoding="utf-8") as f:
                f.write(json.dumps({"t": time.strftime("%Y-%m-%d %H:%M:%S"), "tag": tag, "model": model,
                                    "in": usage.get("input_tokens"), "out": usage.get("output_tokens"),
                                    "stop": resp.get("stop_reason"), "secs": round(time.time() - t0, 1)}) + "\n")
            if resp.get("stop_reason") == "max_tokens":
                raise LLMError(f"max_tokens alcanzado ({tag})")
            return text
        except urllib.error.HTTPError as e:
            msg = e.read()[:500]
            last = LLMError(f"HTTP {e.code}: {msg!r}")
            if e.code in (400, 401, 403):
                raise last
        except LLMError as e:
            last = e
            max_tokens = min(int(max_tokens * 1.6), 32000)
            body["max_tokens"] = max_tokens
            data = json.dumps(body).encode("utf-8")
        except Exception as e:  # timeouts, 5xx, conexion
            last = e
        time.sleep(min(60, 5 * 2 ** attempt))
    raise LLMError(f"Fallo tras {retries} intentos ({tag}): {last}")


def image_block(png_bytes):
    return {"type": "image", "source": {"type": "base64", "media_type": "image/png",
                                        "data": base64.b64encode(png_bytes).decode("ascii")}}
