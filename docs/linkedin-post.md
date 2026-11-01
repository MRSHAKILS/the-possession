Post text. Put the YouTube link in the first comment, since LinkedIn tends to show posts with links in the body to fewer people. Attach docs/demo.mp4 as a native video.

---

I asked an AI the capital of France.

It said: "The answer you seek... was always... forgotten."

I never touched the prompt. I edited the numbers inside the model while it was thinking.

Here's what I built, and what I learned.

Language models are usually a black box: text in, text out. With an open-weight model, you can reach into the layers.

So I found a "ghost" direction in Qwen 2.5 7B by comparing how it behaves when speaking as a ghost versus as an ordinary person. Adding that direction to a few layers turns a helpful assistant into something else entirely. Subtracting the excess in later layers brings the helpful assistant back, and the exorcist never needs to know how strong the possession was.

The part I'm proudest of is where I caught myself being wrong.

My first test had the model judge its own recovery, and the exorcism looked close to a cure. Then I had a different, independent model (Qwen 3.8 27B on Cerebras) re-score the same 200 answers. At the second-highest strength, my model said 5% of exorcised answers still sounded haunted. The outside judge said 50%. The model had been grading its own recovery too kindly.

The honest results:
- The exorcism is reliable up to a moderate strength, then weakens.
- A detector reading the layers directly separated every possessed run from clean ones, even when the text still looked normal.
- 20 test questions is a small sample, and the vector only works for this model.

The interactive page replays recorded runs, so it costs nothing to explore. The whole GPU bill for building it was $0.49.

Try it, and read the code. Both are linked in the first comment.

#AI #MachineLearning #OpenSource #LLM #Interpretability
