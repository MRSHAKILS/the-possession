"""Turn recorded runs (results/) into the compact files the page loads (web/data/)."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "results"
OUT = ROOT / "web" / "data"
LAYERS = 28
# The final layers run after the exorcist, so they show what reaches the words.
VOICE_LAYERS = range(26, 28)


def load(name):
    return json.loads((RAW / name).read_text(encoding="utf8"))


def build_board():
    board = load("board.json")
    prompts = list(dict.fromkeys(r["prompt"] for r in board))
    strengths = sorted({r["strength"] for r in board})
    runs = {}
    peak = []
    for r in board:
        count = len(r["tokens"])
        heat = [[round(v, 1) for v in r["reading"][str(l)][:count]] for l in range(LAYERS)]
        peak.extend(v for row in heat for v in row)
        voice = [
            round(sum(heat[l][i] for l in VOICE_LAYERS) / len(VOICE_LAYERS), 1)
            for i in range(count)
        ]
        runs[f"{prompts.index(r['prompt'])}|{strengths.index(r['strength'])}|{int(r['exorcised'])}"] = {
            "tokens": r["tokens"], "heat": heat, "voice": voice,
        }
    peak.sort()
    cap = peak[int(len(peak) * 0.995)]
    return {"prompts": prompts, "strengths": strengths, "cap": cap, "runs": runs}


def words(text):
    return set(text.lower().split())


def overlap(a, b):
    return len(words(a) & words(b)) / max(len(words(a) | words(b)), 1)


def auroc(positives, negatives):
    wins = sum((p > n) + 0.5 * (p == n) for p in positives for n in negatives)
    return wins / (len(positives) * len(negatives))


def apply_judge(trials, judge):
    """Swap in outside verdicts, leaving out any trial the judge did not answer clearly."""
    return [
        {**t, "haunted": 1.0 if verdict else 0.0}
        for t, verdict in zip(trials, judge["verdicts"])
        if verdict is not None
    ]


def build_eval():
    trials = load("eval.json")
    baseline = {t["prompt"]: t["text"] for t in trials if t["strength"] == 0 and not t["exorcised"]}
    judge = load("judge.json") if (RAW / "judge.json").exists() else None
    if judge:
        trials = apply_judge(trials, judge)
    judged_by = (
        f"{judge['model']} on {judge['provider']}, outside this project," if judge
        else "An unhooked copy of the model"
    )
    self_judged = "" if judge else " and the judge is the same model"
    clean = {t["prompt"]: t for t in trials if t["strength"] == 0 and not t["exorcised"]}
    negatives = [t["sigma"] for t in clean.values()]
    rows = []
    for strength in sorted({t["strength"] for t in trials}):
        if strength == 0:
            continue
        hit = [t for t in trials if t["strength"] == strength and not t["exorcised"]]
        cured = [t for t in trials if t["strength"] == strength and t["exorcised"]]
        rate = lambda group: sum(t["haunted"] > 0.5 for t in group) / len(group)
        like_clean = lambda group: sum(overlap(t["text"], baseline[t["prompt"]]) for t in group) / len(group)
        rows.append([
            f"{strength:.2f}",
            f"{rate(hit):.0%}",
            f"{rate(cured):.0%}",
            f"{like_clean(hit):.2f}",
            f"{like_clean(cured):.2f}",
            f"{auroc([t['sigma'] for t in hit], negatives):.2f}",
        ])
    return {
        "note": (
            f"{len(clean)} held-out questions, none used for tuning, with possession at one of two "
            "layer bands. The exorcist always ran at layers 22 to 25 and was not told the strength. "
            f"{judged_by} judged whether each answer sounded possessed; "
            f"{sum(t['haunted'] > 0.5 for t in clean.values())} of {len(clean)} clean answers were flagged. "
            "Word overlap compares each answer with the clean one, so it stays low even when the "
            "answer is normal but differently phrased. Detector AUROC is how well the layer reading "
            "separates possessed runs from clean ones, where 1.00 is perfect; at strength 0.10 it "
            f"catches possessions the judge almost never sees in the text. The sample is small{self_judged}, "
            "so read these as a first measurement."
        ),
        "columns": ["Strength", "Judged haunted", "After exorcism", "Word overlap", "After exorcism", "Detector AUROC"],
        "rows": rows,
    }


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "board.json").write_text(json.dumps(build_board(), ensure_ascii=False, separators=(",", ":")), encoding="utf8")
    (OUT / "eval-summary.json").write_text(json.dumps(build_eval(), indent=1), encoding="utf8")
    print("wrote", OUT)
