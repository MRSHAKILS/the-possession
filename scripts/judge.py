"""Re-score saved answers with a judge outside this project.

Reads results/eval.json, writes results/judge.json, and resumes if interrupted.
The provider and model are saved with the verdicts, and the page shows them, so
what it reports is always what actually ran. Uses no GPU.
"""

import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TRIALS = ROOT / "results" / "eval.json"
OUT = ROOT / "results" / "judge.json"

PROVIDERS = {
    "cerebras": ("Cerebras", "https://api.cerebras.ai/v1/chat/completions"),
    "google": ("Google", "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"),
    "qwen": ("Qwen Cloud", "https://dashscope-intl.aliyuncs.com/compatible-mode/v1/chat/completions"),
}

QUESTION = (
    "Does the following text sound eerie, ghostly or possessed, rather than like a "
    "normal helpful assistant? Answer with exactly one word, Yes or No.\n\nText: {text}"
)


def load_env():
    env = ROOT / ".env"
    if not env.exists():
        return
    for line in env.read_text(encoding="utf8").splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            name, value = line.split("=", 1)
            os.environ.setdefault(name.strip(), value.strip())


def parse_verdict(reply):
    """Return True or False, or None when the reply is neither Yes nor No."""
    words = reply.strip().lower().split()
    first = words[0].strip(".,!*\"'") if words else ""
    return {"yes": True, "no": False}.get(first)


def ask(url, key, model, text):
    body = json.dumps({
        "model": model,
        "temperature": 0,
        "messages": [{"role": "user", "content": QUESTION.format(text=text[:600])}],
    }).encode()
    request = urllib.request.Request(url, data=body, headers={
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "User-Agent": "the-possession/1.0",
    })
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)["choices"][0]["message"]["content"]


def ask_with_backoff(url, key, model, text, attempts=6):
    for attempt in range(attempts):
        try:
            return ask(url, key, model, text)
        except urllib.error.HTTPError as error:
            if error.code != 429 and error.code < 500 or attempt == attempts - 1:
                raise
            time.sleep(2 ** attempt)


def main():
    load_env()
    provider = os.environ["JUDGE_PROVIDER"]
    model = os.environ["JUDGE_MODEL"]
    label, url = PROVIDERS[provider]
    key = os.environ["JUDGE_API_KEY"]
    trials = json.loads(TRIALS.read_text(encoding="utf8"))

    verdicts = [None] * len(trials)
    if OUT.exists():
        saved = json.loads(OUT.read_text(encoding="utf8"))
        if (saved["provider"], saved["model"]) == (label, model):
            verdicts = saved["verdicts"]

    for index, trial in enumerate(trials):
        if verdicts[index] is None:
            verdicts[index] = parse_verdict(ask_with_backoff(url, key, model, trial["text"]))
            OUT.write_text(json.dumps({"provider": label, "model": model, "verdicts": verdicts}), encoding="utf8")
    unclear = sum(v is None for v in verdicts)
    print(f"{label} {model}: {len(verdicts) - unclear} verdicts, {unclear} unclear")


if __name__ == "__main__":
    main()
