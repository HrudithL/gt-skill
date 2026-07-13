// Run tab: configure -> live plan preview -> launch -> watch live (SSE).
import { el, clear, postJSON, fmtCost, fmtInt } from "./api.js";
import { renderTranscript } from "./transcript.js";
import { loadFile, kindFor } from "./viewers.js";

export function renderRunTab(root, catalogs, { onJumpToHistory }) {
  const state = {
    skill: null,
    selected: new Map(), // name -> prompt info
    adhocText: "",
    adhocData: (catalogs.data[0] && catalogs.data[0].path) || "",
    repeats: 1,
    baseline: "auto", // auto | on | off
    model: (catalogs.models[0] && catalogs.models[0].label) || "haiku",
    running: false,
  };
  const promptByName = {};
  for (const list of Object.values(catalogs.grouped)) for (const p of list) promptByName[p.name] = p;

  clear(root);
  const grid = el("div", { class: "run-grid" });
  const config = el("div", { class: "card config" });
  const right = el("div", { class: "card panel" });
  grid.append(config, right);
  root.append(grid);

  // ---- config panel ----
  function buildSpec() {
    const prompts = [];
    for (const p of state.selected.values()) {
      prompts.push({ prompt: p.prompt, data: p.data, name: p.name, difficulty: p.difficulty, source: "corpus" });
    }
    if (state.adhocText.trim()) prompts.push({ prompt: state.adhocText.trim(), data: state.adhocData, source: "adhoc" });
    const baseline = state.baseline === "auto" ? null : state.baseline === "on";
    return { skill: state.skill, prompts, repeats: state.repeats, model: state.model, baseline };
  }

  function canLaunch() {
    return !!state.skill && (state.selected.size > 0 || state.adhocText.trim().length > 0) && !state.running;
  }

  const launchBtn = el("button", { class: "btn", onclick: launch }, "Launch");
  const launchNote = el("span", { class: "small muted" });

  function refreshConfigUI() {
    for (const c of config.querySelectorAll(".skillcard")) c.classList.toggle("active", c.dataset.skill === state.skill);
    launchBtn.disabled = !canLaunch();
  }

  // skill cards
  const skillCards = el("div", { class: "skillcards" });
  for (const s of catalogs.skills) {
    skillCards.append(
      el("button", { class: "skillcard", dataset: { skill: s.label }, onclick: () => { state.skill = s.label; refreshConfigUI(); schedulePlan(); } },
        el("div", { class: "lbl" }, s.label),
        el("div", { class: "desc" }, s.description || "")
      )
    );
  }

  // prompts (grouped, multi-select)
  const promptBox = el("div", {});
  for (const diff of ["easy", "medium", "hard"]) {
    const list = catalogs.grouped[diff] || [];
    if (!list.length) continue;
    const group = el("div", { class: "promptgroup" }, el("h3", {}, diff));
    for (const p of list) {
      const cb = el("input", { type: "checkbox", onchange: (e) => { e.target.checked ? state.selected.set(p.name, p) : state.selected.delete(p.name); refreshConfigUI(); schedulePlan(); } });
      group.append(
        el("div", { class: "promptrow", title: `${p.prompt}\n\n(${p.data.split("/").pop()})` },
          cb,
          el("span", {}, p.name),
          el("button", { class: "tmpl", onclick: () => { state.adhocText = p.prompt; state.adhocData = relData(p.data); adhocTa.value = p.prompt; syncAdhocData(); schedulePlan(); } }, "use as template")
        )
      );
    }
    promptBox.append(group);
  }

  function relData(abs) {
    // corpus data comes back absolute; the data dropdown holds data/<name>.
    const name = abs.split("/").pop();
    const found = catalogs.data.find((d) => d.name === name);
    return found ? found.path : abs;
  }

  // ad-hoc
  const adhocTa = el("textarea", { placeholder: "Ad-hoc prompt (optional)…", oninput: (e) => { state.adhocText = e.target.value; refreshConfigUI(); schedulePlan(); } });
  const adhocSel = el("select", { onchange: (e) => { state.adhocData = e.target.value; schedulePlan(); } },
    ...catalogs.data.map((d) => el("option", { value: d.path }, d.name)));
  function syncAdhocData() { adhocSel.value = state.adhocData; }
  adhocSel.value = state.adhocData;

  // repeats / baseline / model
  const repeatsIn = el("input", { type: "number", min: "1", value: "1", onchange: (e) => { state.repeats = Math.max(1, parseInt(e.target.value || "1", 10)); schedulePlan(); } });
  const baselineSel = el("select", { onchange: (e) => { state.baseline = e.target.value; schedulePlan(); } },
    el("option", { value: "auto" }, "Auto (on iff repeats>1)"), el("option", { value: "on" }, "On"), el("option", { value: "off" }, "Off"));
  const modelSel = el("select", { onchange: (e) => { state.model = e.target.value; schedulePlan(); } },
    ...catalogs.models.map((m) => el("option", { value: m.label }, `${m.label} (${m.id})`)));

  config.append(
    el("h2", {}, "Skill"),
    skillCards,
    el("h2", { style: "margin-top:1rem" }, "Prompts"),
    promptBox,
    el("label", { class: "field" }, "Ad-hoc prompt"),
    adhocTa,
    el("label", { class: "field" }, "Ad-hoc data"),
    adhocSel,
    el("div", { class: "row2", style: "margin-top:.6rem" },
      el("div", {}, el("label", { class: "field" }, "Repeats"), repeatsIn),
      el("div", {}, el("label", { class: "field" }, "Model"), modelSel)),
    el("label", { class: "field" }, "Baseline"),
    baselineSel,
    el("div", { class: "launchbar" }, launchBtn, launchNote)
  );
  refreshConfigUI();

  // ---- plan preview (debounced) ----
  let planTimer = null;
  function schedulePlan() {
    if (state.running) return;
    clearTimeout(planTimer);
    planTimer = setTimeout(refreshPlan, 250);
  }
  async function refreshPlan() {
    if (state.running) return;
    const spec = buildSpec();
    if (!spec.skill || spec.prompts.length === 0) {
      clear(right);
      right.append(el("div", { class: "muted" }, "Pick a skill and at least one prompt to preview the run."));
      launchNote.textContent = "";
      return;
    }
    try {
      const plan = await postJSON("/api/plan", spec);
      renderPlan(right, plan);
      launchNote.textContent = `${plan.invocation_count} invocation${plan.invocation_count === 1 ? "" : "s"}`;
    } catch (e) {
      clear(right);
      right.append(el("div", { class: "err" }, "plan error: " + e.message));
    }
  }

  // ---- launch + live view ----
  let es = null;
  async function launch() {
    if (!canLaunch()) return;
    const spec = buildSpec();
    const plan = await postJSON("/api/plan", spec).catch(() => null);
    const inv = plan ? plan.invocation_count : spec.prompts.length;
    if (inv > 6 && !confirm(`This launches ${inv} agent invocations (API cost). Proceed?`)) return;
    let res;
    try {
      res = await postJSON("/api/runs", spec);
    } catch (e) {
      launchNote.textContent = "launch failed: " + e.message;
      return;
    }
    state.running = true;
    refreshConfigUI();
    startLive(res.run_id, spec);
  }

  function startLive(runId, spec) {
    const live = new LiveView(right, runId, spec, catalogs, { onJumpToHistory, onDone: () => { state.running = false; refreshConfigUI(); } });
    if (es) es.close();
    es = live.connect();
  }

  schedulePlan();
}

// ---- plan tree rendering ----
function renderPlan(root, plan) {
  clear(root);
  root.append(
    el("div", { class: "chips" },
      el("span", { class: "chip" }, "skill: ", el("span", { class: "tag" }, plan.skill)),
      el("span", { class: "chip" }, "model: ", plan.model.label),
      el("span", { class: "chip" }, "repeats: " + plan.repeats),
      el("span", { class: "chip" }, "baseline: " + (plan.baseline ? "on" : "off")),
      el("span", { class: "chip" }, plan.invocation_count + " invocations"))
  );
  const tree = el("div", { class: "tree" });
  tree.append(el("div", { class: "node dir" }, plan.run_dir + "/  ", el("span", { class: "meta" }, "(planned)")));
  for (const p of plan.prompts) {
    tree.append(el("div", { class: "node dir" }, "  prompts/" + p.name + "/"));
    for (const d of p.dirs) {
      const mount = d.mounts_skill ? `${d.skill}: ${d.entries.join(", ")}` : "no .claude (baseline)";
      tree.append(el("div", { class: "node file" }, "    " + d.label + "/  ", el("span", { class: "meta" }, `→ ${mount} · data ${d.data}`)));
    }
    if (p.convergence) tree.append(el("div", { class: "node meta" }, "    convergence.json, contact_sheet.png  (repeats>1)"));
  }
  root.append(tree);
}

// ---- live view (one active run) ----
class LiveView {
  constructor(root, runId, spec, catalogs, opts) {
    this.root = root; this.runId = runId; this.spec = spec; this.opts = opts;
    this.stages = []; this.active = -1; this.started = Date.now();
    this.usage = { input: 0, output: 0, cost_usd: 0 };
    this.total = null;
  }

  connect() {
    clear(this.root);
    this.chipsEl = el("div", { class: "chips" });
    this.stageBar = el("div", { class: "chips" });
    this.body = el("div", {});
    this.root.append(this.chipsEl, this.stageBar, this.body);
    this.renderChips();
    this.timer = setInterval(() => this.renderChips(), 1000);

    const es = new EventSource(`/api/runs/${this.runId}/events`);
    es.addEventListener("stage", (e) => this.onStage(JSON.parse(e.data)));
    es.addEventListener("message", (e) => this.onMessage(JSON.parse(e.data)));
    es.addEventListener("file", (e) => this.onFile(JSON.parse(e.data)));
    es.addEventListener("usage", (e) => { this.usage = JSON.parse(e.data); this.renderChips(); });
    es.addEventListener("run_finished", (e) => this.onDone(es, JSON.parse(e.data)));
    es.addEventListener("run_error", (e) => this.onDone(es, JSON.parse(e.data), true));
    this.es = es;
    return es;
  }

  stageKey(d) { return `${d.prompt}·${d.variant}·${d.repeat ?? "b"}`; }

  onStage(d) {
    this.total = d.total;
    const label = `${d.prompt} · ${d.variant}${d.repeat ? " r" + d.repeat : " baseline"} (${d.index}/${d.total})`;
    this.stages.push({ key: this.stageKey(d), label, messages: [], files: new Map() });
    this.active = this.stages.length - 1;
    this.renderStageBar();
    this.renderBody();
    this.renderChips();
  }

  onMessage(d) {
    const st = this.stages.find((s) => s.key === this.stageKey(d)) || this.stages[this.stages.length - 1];
    if (!st) return;
    st.messages.push(d.msg);
    if (this.stages[this.active] === st) this.renderBody();
  }

  onFile(d) {
    const st = this.stages.find((s) => s.key === this.stageKey(d)) || this.stages[this.stages.length - 1];
    if (!st) return;
    st.files.set(d.path, d.kind);
    if (this.stages[this.active] === st) this.renderBody();
  }

  onDone(es, payload, isError = false) {
    es.close();
    clearInterval(this.timer);
    this.renderChips();
    const foot = el("div", { style: "margin-top:.6rem" });
    if (isError) foot.append(el("div", { class: "err" }, "run error: " + (payload.error || "unknown")));
    else foot.append(el("span", { class: "pass" }, "run finished · "),
      el("button", { class: "btn secondary", onclick: () => this.opts.onJumpToHistory(this.runId) }, "open in History"));
    this.root.append(foot);
    this.opts.onDone && this.opts.onDone();
  }

  renderChips() {
    const el_ = (t) => el("span", { class: "chip" }, t);
    const elapsed = Math.floor((Date.now() - this.started) / 1000);
    clear(this.chipsEl);
    this.chipsEl.append(
      el("span", { class: "chip" }, "skill: ", el("span", { class: "tag" }, this.spec.skill)),
      el("span", { class: "chip" }, "model: " + this.spec.model),
      el_(`${this.active >= 0 && this.total ? `stage ${this.active + 1}/${this.total}` : "starting…"}`),
      el_(`${elapsed}s`),
      el_(`tokens ${fmtInt(this.usage.input)} in / ${fmtInt(this.usage.output)} out`),
      el_(fmtCost(this.usage.cost_usd))
    );
  }

  renderStageBar() {
    clear(this.stageBar);
    this.stages.forEach((s, i) => {
      this.stageBar.append(el("button", { class: "chip", style: i === this.active ? "border-color:var(--accent)" : "", onclick: () => { this.active = i; this.renderStageBar(); this.renderBody(); } }, s.label));
    });
  }

  renderBody() {
    clear(this.body);
    const st = this.stages[this.active];
    if (!st) { this.body.append(el("div", { class: "muted" }, "waiting for the first stage…")); return; }
    const cols = el("div", { class: "detail-grid" });
    const files = el("div", {});
    files.append(el("h3", {}, "files"));
    if (!st.files.size) files.append(el("div", { class: "muted small" }, "none yet"));
    for (const [path, kind] of st.files) {
      files.append(el("div", { class: "tree" }, el("span", { class: "file clickable", onclick: () => this.openFile(path, kind) }, path.split("/").pop() + `  `), el("span", { class: "meta" }, kind)));
    }
    const viewer = el("div", { id: "live-viewer" });
    const trans = renderTranscript(st.messages, { onFileClick: (fp) => this.openFileByAbs(fp, st) });
    cols.append(el("div", {}, files, viewer), el("div", {}, trans));
    this.body.append(cols);
    this._viewer = viewer;
  }

  async openFile(path, kind) {
    if (!this._viewer) return;
    clear(this._viewer);
    this._viewer.append(el("div", { class: "small muted" }, path));
    try {
      const node = await loadFile(kind, `/api/runs/${this.runId}/file?path=${encodeURIComponent(path)}`, path);
      this._viewer.append(node);
    } catch (e) { this._viewer.append(el("div", { class: "err" }, e.message)); }
  }
  openFileByAbs(fp, st) {
    // A tool referenced a path; find the matching stage file by basename.
    const base = fp.split("/").pop();
    for (const [path, kind] of st.files) if (path.endsWith(base)) return this.openFile(path, kind);
  }
}
