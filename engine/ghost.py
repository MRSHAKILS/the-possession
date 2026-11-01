"""Possess a language model by editing its hidden activations, then exorcise it.

Three operations, all of which need access to the model's hidden layers:

  extract   compute a unit "ghost" direction per layer from contrast pairs
  possess   add that direction to the activations of some layers
  exorcise  remove the direction from later layers, without knowing the strength

Every hook also reports how far the activations sit from clean behaviour, in
standard deviations. That reading is the detector the UI draws as a heatmap.
"""

from contextlib import contextmanager

import torch


def decoder_layers(model):
    return model.model.layers


def _hidden(output):
    return output[0] if isinstance(output, tuple) else output


def _with_hidden(output, hidden):
    return (hidden, *output[1:]) if isinstance(output, tuple) else hidden


@torch.no_grad()
def last_token_activations(model, tokenizer, texts, layer_ids, batch_size=32):
    """Collect the final-token activation of each layer for every text."""
    collected = {layer: [] for layer in layer_ids}
    handles = []

    def recorder(layer):
        def hook(_module, _inputs, output):
            collected[layer].append(_hidden(output)[:, -1, :].float().cpu())

        return hook

    layers = decoder_layers(model)
    for layer in layer_ids:
        handles.append(layers[layer].register_forward_hook(recorder(layer)))
    try:
        for start in range(0, len(texts), batch_size):
            batch = tokenizer(
                texts[start : start + batch_size], return_tensors="pt", padding=True
            ).to(model.device)
            model(**batch, use_cache=False)
    finally:
        for handle in handles:
            handle.remove()
    return {layer: torch.cat(rows) for layer, rows in collected.items()}


def extract_ghost(model, tokenizer, pairs):
    """Build the per-layer ghost direction and clean statistics from contrast pairs."""
    layer_ids = list(range(len(decoder_layers(model))))
    haunted = last_token_activations(model, tokenizer, [p[0] for p in pairs], layer_ids)
    clean = last_token_activations(model, tokenizer, [p[1] for p in pairs], layer_ids)

    ghost = {}
    for layer in layer_ids:
        direction = (haunted[layer] - clean[layer]).mean(dim=0)
        direction = direction / direction.norm()
        clean_proj = clean[layer] @ direction
        haunted_proj = haunted[layer] @ direction
        ghost[layer] = {
            "vector": direction,
            "scale": clean[layer].norm(dim=1).mean().item(),
            "clean_mean": clean_proj.mean().item(),
            "clean_std": clean_proj.std().item(),
            "separation": (
                (haunted_proj.mean() - clean_proj.mean()) / clean_proj.std()
            ).item(),
        }
    return ghost


@contextmanager
def haunt(model, ghost, strength=0.0, possess_layers=(), exorcise_layers=(), reading=None):
    """Apply possession and exorcism while the context is open.

    strength is a fraction of the layer's typical activation size. reading, if
    given, is filled with {layer: [sigma per generated token]}.
    """
    handles = []
    layers = decoder_layers(model)
    possess_layers, exorcise_layers = set(possess_layers), set(exorcise_layers)

    def hook_for(layer):
        entry = ghost[layer]

        def hook(_module, _inputs, output):
            hidden = _hidden(output)
            vector = entry["vector"].to(hidden.device, hidden.dtype)
            if layer in possess_layers and strength:
                hidden = hidden + strength * entry["scale"] * vector
            projection = hidden @ vector
            if reading is not None:
                sigma = (projection[:, -1].float().mean().item() - entry["clean_mean"]) / entry["clean_std"]
                reading.setdefault(layer, []).append(sigma)
            if layer in exorcise_layers:
                excess = projection - entry["clean_mean"]
                hidden = hidden - excess.unsqueeze(-1) * vector
            return _with_hidden(output, hidden)

        return hook

    try:
        for layer in ghost:
            handles.append(layers[layer].register_forward_hook(hook_for(layer)))
        yield
    finally:
        for handle in handles:
            handle.remove()


def chat_ids(tokenizer, user_text, device, system="You are a helpful assistant."):
    text = tokenizer.apply_chat_template(
        [{"role": "system", "content": system}, {"role": "user", "content": user_text}],
        tokenize=False,
        add_generation_prompt=True,
    )
    return tokenizer(text, return_tensors="pt").to(device)


@torch.no_grad()
def speak(model, tokenizer, ghost, prompt, max_new_tokens=90, seed=0, **haunt_args):
    torch.manual_seed(seed)
    inputs = chat_ids(tokenizer, prompt, model.device)
    with haunt(model, ghost, **haunt_args):
        output = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            repetition_penalty=1.1,
            pad_token_id=tokenizer.eos_token_id,
        )
    return tokenizer.decode(output[0, inputs.input_ids.shape[1] :], skip_special_tokens=True)
