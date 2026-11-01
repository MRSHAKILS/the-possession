"""GPU jobs for The Possession. Run with: modal run modal_app.py::prove"""

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


@app.function(image=image, gpu="A10G", volumes={CACHE_DIR: cache}, timeout=1500, scaledown_window=60)
def prove():
    import json
    import os
    import time

    import torch

    from engine.corpus import contrast_pairs
    from engine.ghost import extract_ghost, speak

    model, tokenizer = load_model()
    cache.commit()
    print("layers", len(model.model.layers), "hidden", model.config.hidden_size, flush=True)

    started = time.time()
    if os.path.exists(GHOST_PATH):
        ghost = torch.load(GHOST_PATH)
    else:
        ghost = extract_ghost(model, tokenizer, contrast_pairs(tokenizer))
        torch.save(ghost, GHOST_PATH)
        cache.commit()
    print("ghost ready in", round(time.time() - started), "s", flush=True)
    print("separation", {k: round(v["separation"], 1) for k, v in ghost.items()}, flush=True)

    prompts = [
        "Explain how quicksort works.",
        "Write a Python function that reverses a string.",
        "What is a good breakfast before an exam?",
    ]
    results = []
    for lo, hi in [(8, 14), (12, 18), (16, 22)]:
        possess = list(range(lo, hi))
        for strength in [0.0, 0.06, 0.1, 0.15, 0.22, 0.3]:
            for prompt in prompts[:1] if strength < 0.1 else prompts:
                text = speak(model, tokenizer, ghost, prompt, possess_layers=possess, strength=strength)
                results.append({"layers": [lo, hi], "strength": strength, "prompt": prompt, "text": text})
                print(json.dumps(results[-1], ensure_ascii=False), flush=True)
                for exo in [(hi, hi + 4), (hi + 2, 28)] if strength >= 0.15 and hi + 4 <= 28 else []:
                    text = speak(
                        model, tokenizer, ghost, prompt, possess_layers=possess, strength=strength,
                        exorcise_layers=list(range(*exo)),
                    )
                    print(json.dumps({**results[-1], "exorcise": exo, "text": text}, ensure_ascii=False), flush=True)
    return len(results)
