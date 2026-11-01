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

const PLATFORM_FEE = 0.1;
const EXORCISTS = [
  { name: "Vector Surgeon", detail: "Removes the ghost direction from layers 22 to 25.", fee: 1500 },
  { name: "Cold Reader", detail: "Reads the layer scan and writes the case notes.", fee: 1200 },
  { name: "Night Shift", detail: "On call for strength 0.30, where exorcisms fail most.", fee: 2500 },
];

const usd = (cents) => `$${(cents / 100).toFixed(2)}`;

function node(tag, text, className) {
  const item = document.createElement(tag);
  if (text) item.textContent = text;
  if (className) item.className = className;
  return item;
}

function closeCheckout() {
  el("checkout").hidden = true;
}

function confirmBooking(exorcist, payout, platform) {
  const treating = state.data.strengths[state.stop] > 0 && !state.exorcised;
  const checkout = el("checkout");
  const done = node("button", "Close", "quiet");
  done.type = "button";
  done.addEventListener("click", closeCheckout);
  const actions = node("div", "", "actions");
  actions.append(done);
  checkout.replaceChildren(
    node("h3", "Booking confirmed"),
    node("p", `${exorcist.name} receives ${usd(payout)}. The platform keeps ${usd(platform)}.`),
    node("p", treating ? "Exorcism under way." : "Move the dial to give them something to treat."),
    actions
  );
  if (treating) {
    state.exorcised = true;
    applyControls();
  }
}

function openCheckout(exorcist) {
  const platform = Math.round(exorcist.fee * PLATFORM_FEE);
  const payout = exorcist.fee - platform;
  const table = node("table");
  [["Session", usd(exorcist.fee)], ["Exorcist receives", usd(payout)], ["Platform fee (10%)", usd(platform)]].forEach(([name, value]) => {
    const row = node("tr");
    row.append(node("td", name), node("td", value));
    table.append(row);
  });

  const confirm = node("button", `Confirm ${usd(exorcist.fee)}`);
  confirm.type = "button";
  confirm.addEventListener("click", () => confirmBooking(exorcist, payout, platform));
  const cancel = node("button", "Cancel", "quiet");
  cancel.type = "button";
  cancel.addEventListener("click", closeCheckout);
  const actions = node("div", "", "actions");
  actions.append(confirm, cancel);

  const checkout = el("checkout");
  checkout.replaceChildren(node("h3", `Book ${exorcist.name}`), table, actions);
  checkout.hidden = false;
}

function renderExorcists() {
  EXORCISTS.forEach((exorcist) => {
    const card = node("article", "", "exorcist");
    const book = node("button", "Book session");
    book.type = "button";
    book.addEventListener("click", () => openCheckout(exorcist));
    card.append(node("h3", exorcist.name), node("p", exorcist.detail), node("span", `${usd(exorcist.fee)} per session`, "fee"), book);
    el("exorcists").append(card);
  });
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
  renderExorcists();
  applyControls();
}

start();
