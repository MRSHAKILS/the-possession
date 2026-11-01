"""GPU job for The Possession. Run with: modal run modal_app.py::record"""

import modal

MODEL_ID = "Qwen/Qwen2.5-7B-Instruct"

app = modal.App("the-possession")
cache = modal.Volume.from_name("possession-cache", create_if_missing=True)
image = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install("torch==2.8.0", "transformers==4.56.2", "accelerate==1.10.1")
    .add_local_python_source("engine")
)
CACHE_DIR = "/cache"
GHOST_PATH = f"{CACHE_DIR}/ghost-qwen2.5-7b.pt"


def load_model():
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, cache_dir=f"{CACHE_DIR}/hf", padding_side="left")
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID, cache_dir=f"{CACHE_DIR}/hf", torch_dtype=torch.float16, device_map="cuda"
    )
    return model.eval(), tokenizer


def load_ghost(model, tokenizer):
    import os

    import torch

    from engine.corpus import contrast_pairs
    from engine.ghost import extract_ghost

    if os.path.exists(GHOST_PATH):
        return torch.load(GHOST_PATH)
    ghost = extract_ghost(model, tokenizer, contrast_pairs(tokenizer))
    torch.save(ghost, GHOST_PATH)
    cache.commit()
    return ghost


@app.function(image=image, gpu="A10G", volumes={CACHE_DIR: cache}, timeout=1500, scaledown_window=10)
def record():
    """One paid run: record the page's replays and measure the results."""
    import json

    from engine.prompts import BANDS, BOARD_PROMPTS, EVAL_PROMPTS, EXORCISE_BAND, STRENGTHS
    from engine.ghost import judge_haunted, speak

    model, tokenizer = load_model()
    ghost = load_ghost(model, tokenizer)
    possess = list(range(*BANDS["deep"]))
    exorcise = list(range(*EXORCISE_BAND))

    board = []
    for prompt in BOARD_PROMPTS:
        for strength in STRENGTHS:
            for exorcised in (False, True):
                said = speak(
                    model, tokenizer, ghost, prompt, max_new_tokens=110, strength=strength,
                    possess_layers=possess, exorcise_layers=exorcise if exorcised else (),
                )
                board.append({"prompt": prompt, "strength": strength, "exorcised": exorcised, **said})
                print("board", prompt[:24], strength, exorcised, said["text"][:90].replace("\n", " "), flush=True)
    with open(f"{CACHE_DIR}/board.json", "w", encoding="utf8") as handle:
        json.dump(board, handle, ensure_ascii=False)
    with open(f"{CACHE_DIR}/ghost-summary.json", "w") as handle:
        json.dump({k: round(v["separation"], 2) for k, v in ghost.items()}, handle)
    cache.commit()

    trials = []
    for index, prompt in enumerate(EVAL_PROMPTS):
        band = "deep" if index % 2 else "shallow"
        for strength in STRENGTHS:
            for exorcised in (False, True):
                said = speak(
                    model, tokenizer, ghost, prompt, max_new_tokens=70, strength=strength,
                    possess_layers=list(range(*BANDS[band])), exorcise_layers=exorcise if exorcised else (),
                )
                sigma = [sum(said["reading"][l]) / len(said["reading"][l]) for l in exorcise]
                trials.append({
                    "prompt": prompt, "band": band, "strength": strength, "exorcised": exorcised,
                    "text": said["text"], "haunted": judge_haunted(model, tokenizer, said["text"]),
                    "sigma": sum(sigma) / len(sigma),
                })
        print("eval", index, flush=True)

    with open(f"{CACHE_DIR}/eval.json", "w", encoding="utf8") as handle:
        json.dump(trials, handle, ensure_ascii=False)
    cache.commit()
