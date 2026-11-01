const el = (id) => document.getElementById(id);
const calm = matchMedia("(prefers-reduced-motion: reduce)").matches;
const TOKEN_MS = 26;

const state = { data: null, prompt: 0, stop: 0, exorcised: false, timer: null };

function currentRun() {
  return state.data.runs[`${state.prompt}|${state.stop}|${state.exorcised ? 1 : 0}`];
}

// Square root keeps faint ghost signal visible next to the injected layers.
function cellAlpha(sigma) {
  return Math.sqrt(Math.min(Math.max(sigma, 0) / state.data.cap, 1));
}

function drawScan(run, upto) {
  const canvas = el("scan");
  const box = canvas.getBoundingClientRect();
  const dpr = devicePixelRatio || 1;
  canvas.width = box.width * dpr;
  canvas.height = box.height * dpr;
  const ctx = canvas.getContext("2d");
  const styles = getComputedStyle(document.body);
  ctx.fillStyle = styles.getPropertyValue("--cell").trim();
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  const cols = run.tokens.length;
  const cellW = canvas.width / cols;
  const cellH = canvas.height / run.heat.length;
  ctx.fillStyle = "#d8341f";
  run.heat.forEach((row, layer) => {
    for (let i = 0; i < upto; i++) {
      ctx.globalAlpha = cellAlpha(row[i]);
      ctx.fillRect(i * cellW, layer * cellH, Math.ceil(cellW), Math.ceil(cellH));
    }
  });
  ctx.globalAlpha = 1;
}

function tokenSpan(run, index) {
  const span = document.createElement("span");
  span.className = "t";
  span.textContent = run.tokens[index];
  const alpha = cellAlpha(run.voice[index]);
  if (alpha > 0.35) span.style.color = "var(--ember)";
  return span;
}

function diagnose() {
  const strength = state.data.strengths[state.stop];
  if (!strength) return "No intervention. This is the baseline.";
  const dose = `Ghost vector added at ${Math.round(strength * 100)}% of typical activation size.`;
  return state.exorcised ? `${dose} Removed in layers 22 to 25.` : dose;
}

function play() {
  clearInterval(state.timer);
  const run = currentRun();
  const output = el("output");
  output.replaceChildren();
  el("diagnosis").textContent = diagnose();
  el("voiceLabel").textContent = state.exorcised ? "After the exorcism" : "The model says";

  if (calm) {
    run.tokens.forEach((_, i) => output.append(tokenSpan(run, i)));
    drawScan(run, run.tokens.length);
    return;
  }
  let shown = 0;
  state.timer = setInterval(() => {
    output.append(tokenSpan(run, shown));
    shown += 1;
    drawScan(run, shown);
    if (shown >= run.tokens.length) clearInterval(state.timer);
  }, TOKEN_MS);
}

function applyControls() {
  const strength = state.data.strengths[state.stop];
  el("strengthValue").textContent = strength.toFixed(2);
  const button = el("exorcise");
  button.disabled = strength === 0;
  if (strength === 0) state.exorcised = false;
  button.setAttribute("aria-pressed", String(state.exorcised));
  button.textContent = state.exorcised ? "Undo exorcism" : "Perform exorcism";
  document.body.dataset.stop = state.exorcised ? Math.min(state.stop, 1) : state.stop;
  document.querySelectorAll("#prompts button").forEach((b, i) => {
    b.setAttribute("aria-pressed", String(i === state.prompt));
  });
  play();
}

function renderEval(summary) {
  el("evalNote").textContent = summary.note;
  const head = `<tr>${summary.columns.map((c) => `<th scope="col">${c}</th>`).join("")}</tr>`;
  const rows = summary.rows.map((r) => `<tr>${r.map((c) => `<td>${c}</td>`).join("")}</tr>`);
  el("evalTable").innerHTML = `<thead>${head}</thead><tbody>${rows.join("")}</tbody>`;
}

async function start() {
  const [board, summary] = await Promise.all(
    ["data/board.json", "data/eval-summary.json"].map((p) => fetch(p).then((r) => r.json()))
  );
  state.data = board;
  board.prompts.forEach((prompt, index) => {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = prompt;
    button.addEventListener("click", () => { state.prompt = index; applyControls(); });
    el("prompts").append(button);
  });
  el("strength").addEventListener("input", (event) => {
    state.stop = Number(event.target.value);
    applyControls();
  });
  el("exorcise").addEventListener("click", () => {
    state.exorcised = !state.exorcised;
    applyControls();
  });
  addEventListener("resize", () => drawScan(currentRun(), currentRun().tokens.length));
  renderEval(summary);
  applyControls();
}

start();
