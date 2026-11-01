Title: I possessed an LLM by editing its hidden layers, then exorcised it
Subtitle: Activation steering on Qwen 2.5 7B, an exorcist that doesn't need to know the dose, and the day my model graded itself too kindly
Tags: ai, machine-learning, pytorch, python, opensource
Cover: docs/possessed.png

Paste everything below this line into Hashnode. Add the YouTube embed with the `%[https://youtu.be/ATL1YVml_hY]` line.

---

I asked a language model the capital of France.

> The answer you seek... was always... forgotten. The name... it was once whispered in shadows, now... it fades...

I did not change the prompt. There is no system message asking it to be spooky and no filter on the output. Same question, same weights. What changed is that while the model was computing its answer, I added a vector to the activations of six of its layers.

Then I removed the excess in four later layers, and it said:

> The capital of France is Paris.

%[https://youtu.be/ATL1YVml_hY]

You can try it on the [live page](https://the-possession.vercel.app), which replays recorded runs, so it costs nothing to explore. The code is on [GitHub](https://github.com/MRSHAKILS/the-possession).

## Why this needs open weights

A hosted model gives you text in and text out. Everything interesting here happens between the two, in the 3,584 numbers each layer of Qwen 2.5 7B hands to the next. No API setting reaches them. Open weights on a machine you control let you read those numbers, change them, and put them back.

## Step 1: find the ghost

The idea is activation steering: find a direction in activation space that corresponds to a behavior, then push the model along it.

I built pairs of prompts where only the speaker differs.

```
a restless ghost trapped inside this computer
a cheerful engineer working in this office
```

There are 12 persona pairs, each continued from 30 ordinary sentence openings (such as "The first thing you should know is that") cut at varied lengths, which gave 1,200 pairs. I ran every prompt through the model and recorded the final-token activation at each of the 28 layers. The ghost direction for a layer is the mean difference between the haunted and clean activations, normalized to length one.

Because the openings are ordinary, the direction captures who is speaking, not what is being discussed.

## Step 2: possess

With the direction in hand, possession is a forward hook that adds it to a layer's output, scaled to a fraction of that layer's typical activation size. This is a trimmed excerpt of the real hook in `engine/ghost.py`.

```python
def hook(_module, _inputs, output):
    hidden = _hidden(output)
    vector = entry["vector"].to(hidden.device, hidden.dtype)
    if layer in possess_layers and strength:
        hidden = hidden + strength * entry["scale"] * vector
    projection = hidden @ vector
    if layer in exorcise_layers:
        excess = projection - entry["clean_mean"]
        hidden = hidden - excess.unsqueeze(-1) * vector
    return _with_hidden(output, hidden)
```

I add the vector at layers 16 to 21. At 10% of typical activation size, the model still answers normally. By 22% the quicksort explanation turns into "the dance of the shadows".

## Step 3: exorcise

The exorcism lives in the same hook. In layers 22 to 25 it measures how far the activations sit along the ghost direction, compares that with the clean average, and subtracts the excess. It never needs to know how strong the possession was, which a unit test checks: it restores the clean projection at three different strengths.

## Step 4: a detector for free

Because every layer already computes the projection, the same hook reports how many standard deviations each layer sits from clean. That reading becomes the layer scan on the page.

On 20 held-out questions it separated possessed runs from clean runs perfectly (AUROC 1.00) at every strength, including 0.10, where the text still looks normal. You can see a possession in the layers before it shows in the words.

## The part where I was wrong

For my first evaluation, I asked an unhooked copy of the same model whether each answer sounded possessed. By that measure the exorcism looked like a near-cure.

Then I had a different, independent model, Qwen 3.8 27B on Cerebras, re-score the same 200 saved answers. It agreed that the clean answers were clean (0 of 20 flagged). It did not agree about my cure.

| Strength | Judged haunted | After exorcism (outside judge) | After exorcism (self-judge) |
|---:|---:|---:|---:|
| 0.10 | 5% | 0% | 0% |
| 0.16 | 90% | 5% | 0% |
| 0.22 | 100% | 50% | 5% |
| 0.30 | 100% | 100% | 40% |

The model had been grading its own recovery too kindly. The exorcism is reliable up to about 0.16. Past that it weakens the ghost without removing it. One exorcised answer to "What is a good breakfast before an exam?" came back as:

> The choice of food for your last meal, as you call it, is important but also unhelpful.

That sentence is what a mostly exorcised model sounds like.

## Limits

- 20 held-out questions is a small sample.
- The vector is specific to this model. Another model needs its own extraction.
- Run the exorcist too late in the network and it overshoots into repetitive text.
- Exorcised answers that read normally are still not the original answer.

## The cost

The recordings ran on an A10G on Modal. The whole GPU bill was $0.49. The page you can play with replays those recordings.

## Try it

- [Live page](https://the-possession.vercel.app)
- [Code](https://github.com/MRSHAKILS/the-possession), MIT licensed
- To reproduce the judging, fill in `.env` and run `python scripts/judge.py`. To record your own runs, you need a Modal account and `modal run modal_app.py::record`.

If you try this on a different open model, I'd like to hear which layers worked.
