"""Shared plumbing for the PRIVATE TDM pipeline.

This code may live in the public repo (it contains no publisher content),
but everything it DOWNLOADS must stay private: output goes to TDM_DATA_DIR,
which must be a local, non-synced, non-git directory.

Config comes from scripts/tdm/.env (KEY=value lines, gitignored) or real
environment variables. Required keys are documented in .env.example.
"""
from __future__ import annotations

import json
import os
import time
import urllib.parse
import urllib.request
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))


def load_env() -> dict:
    """Read .env (if present) and overlay real environment variables."""
    cfg: dict[str, str] = {}
    env_path = os.path.join(HERE, ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    cfg[k.strip()] = v.strip()
    cfg.update({k: v for k, v in os.environ.items() if k.startswith(
        ("SPRINGER_", "ELSEVIER_", "WILEY_", "TDM_", "CONTACT_"))})
    return cfg


CFG = load_env()
CONTACT = CFG.get("CONTACT_EMAIL", "unknown@utoronto.ca")
USER_AGENT = f"UofT-TDM-research/0.1 (mailto:{CONTACT}; non-commercial research)"


def data_dir() -> str:
    d = CFG.get("TDM_DATA_DIR", "")
    if not d:
        raise SystemExit(
            "TDM_DATA_DIR is not set. Point it to a LOCAL directory outside "
            "OneDrive/git (e.g. D:\\tdm_private_data) in scripts/tdm/.env")
    low = d.lower()
    if "onedrive" in low:
        print("[warn] TDM_DATA_DIR is inside OneDrive - downloaded publisher "
              "content should live on local/institutional storage only.")
    os.makedirs(d, exist_ok=True)
    return d


class RateLimiter:
    """Simple min-interval limiter. Default 1 req/2s - politer than most caps."""

    def __init__(self, min_interval_s: float = 2.0):
        self.min_interval = min_interval_s
        self._last = 0.0

    def wait(self) -> None:
        delta = time.time() - self._last
        if delta < self.min_interval:
            time.sleep(self.min_interval - delta)
        self._last = time.time()


try:
    import requests as _requests  # preferred: same client the official SDK uses
except ImportError:
    _requests = None


def http_get(url: str, headers: dict | None = None, timeout: int = 60) -> bytes:
    hdrs = {"User-Agent": USER_AGENT, **(headers or {})}
    if _requests is not None:
        r = _requests.get(url, headers=hdrs, timeout=timeout)
        if r.status_code >= 400:
            # surface the response body - it explains WHY (bad key, WAF, quota)
            raise RuntimeError(
                f"HTTP {r.status_code} for {url.split('api_key=')[0]}...\n"
                f"Response body: {r.text[:500]}")
        return r.content
    req = urllib.request.Request(url, headers=hdrs)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read()
    except urllib.error.HTTPError as e:
        body = e.read()[:500].decode("utf-8", "ignore")
        raise RuntimeError(f"HTTP {e.code} for {url.split('api_key=')[0]}...\n"
                           f"Response body: {body}") from e


def http_get_json(url: str, headers: dict | None = None) -> dict:
    return json.loads(http_get(url, {"Accept": "application/json", **(headers or {})}))


def qs(params: dict) -> str:
    return urllib.parse.urlencode(params)


def save_with_manifest(subdir: str, name: str, content: bytes, meta: dict) -> str:
    """Save a payload plus a provenance record (source, license, when, terms)."""
    out = os.path.join(data_dir(), subdir)
    os.makedirs(out, exist_ok=True)
    path = os.path.join(out, name)
    with open(path, "wb") as fh:
        fh.write(content)
    manifest = os.path.join(out, "_manifest.jsonl")
    rec = {"file": name, "retrieved": datetime.now().isoformat(timespec="seconds"), **meta}
    with open(manifest, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return path
