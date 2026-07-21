#!/usr/bin/env python3
"""AD-HOC: run INSIDE Railway (railway run) to call OpenRouter with the REAL
saved key + model from the DB. Shows the true OpenRouter response. Temp, self-cleaning."""
import os, json, urllib.request, urllib.error
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django; django.setup()
from dashboard.models import SiteConfig
cfg = SiteConfig.get()
key = cfg.openrouter_model and cfg.openrouter_api_key
print("model:", cfg.openrouter_model)
print("key present:", bool(cfg.openrouter_api_key), "len:", len(cfg.openrouter_api_key or ""))
if not cfg.openrouter_api_key:
    print("NO KEY SAVED"); raise SystemExit
payload = json.dumps({
    "model": cfg.openrouter_model or "openai/gpt-4o-mini",
    "messages": [{"role":"user","content":"Reply with one word: OK"}],
    "max_tokens": 50,
}).encode()
req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions", data=payload,
    headers={"Authorization": f"Bearer {cfg.openrouter_api_key}",
             "Content-Type":"application/json",
             "HTTP-Referer":"https://time-after-time.up.railway.app",
             "X-Title":"Time After Time Upholstery AI"})
try:
    r = urllib.request.urlopen(req, timeout=60)
    print("STATUS", r.status)
    print("RESP", r.read().decode()[:500])
except urllib.error.HTTPError as e:
    print("HTTPError", e.code, "->", e.read().decode()[:700])
except Exception as e:
    print("ERR", type(e).__name__, e)
