// History tab: a scannable list of past runs -> a structured detail view with a
// standardized overview (cost always shown), an iteration/test selector that
// drills into a specific sweep test or convergence repeat, per-iteration
// convergence, a high-level collapsible file browser, and a wide sticky side
// viewer that renders the selected table / script / transcript / markdown
// inline (07-frontend-runner §5.2).
import { el, clear, getJSON, getText, fmtCost, fmtInt } from "./api.js";
import { renderTranscript } from "./transcript.js";
import { loadFile, kindFor } from "./viewers.js";
import { renderCollapsibleTree } from "./tree.js";

const CONV_FIELDS = [
  "heading_band_shade", "heading_band_hue", "palettes", "frame_present",
  "striping_present", "dividers_present", "caption_present", "source_present",
  "grouping_present", "stub_present", "columns_signature", "fmt_signature",
  "domain_signature", "color_signature", "data_hash",
];

// ---- shared formatters ----
function fmtWhen(ts) {
  const m = /^(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})$/.exec(ts || "");
  return m ? `${m[1]}-${m[2]}-${m[3]} ${m[4]}:${m[5]}` : (ts || "—");
}
function fmtDur(ms) {
  if (ms == null) return "—";
  const s = ms / 1000;
  return s < 60 ? `${s.toFixed(1)}s` : `${Math.floor(s / 60)}m ${Math.round(s % 60)}s`;
}
// A run's type: unified runs/<type>/ type when present, else mapped from the
// legacy layout so every row reads as single / convergence / sweep.
function runTypeLabel(r) {
  return r.type || { consistency: "convergence", sweep: "sweep", single: "single", unified: "run" }[r.layout] || r.layout;
}
function skillVariant(r) {
  const parts = [];
  if (r.skill) parts.push(r.skill);
  if (r.variant && r.variant !== r.skill) parts.push(r.variant);
  return parts.length ? parts.join(" / ") : (r.variant || r.skill || "—");
}

// --------------------------------------------------------------------------- //
// list view
// --------------------------------------------------------------------------- //
export async function renderHistoryTab(root, openRunId = null) {
  clear(root);
  if (openRunId) return renderDetail(root, openRunId);
  root.append(el("div", { class: "small muted" }, "loading history…"));
  let data;
  try { data = await getJSON("/api/runs"); }
  catch (e) { clear(root); root.append(el("div", { class: "err" }, e.message)); return; }
  clear(root);

  const head = el("div", { class: "page-head" }, el("h2", {}, `History`), el("span", { class: "count-badge" }, (data.runs || []).length));
  if (data.busy) head.append(el("span", { class: "chip live", style: "margin-left:auto" }, el("span", { class: "spinner" }), " a run is in progress"));
  root.append(head);

  const runs = data.runs || [];
  if (!runs.length) { root.append(el("div", { class: "empty" }, "No runs yet. Launch one from the Run tab.")); return; }

  const table = el("table", { class: "runs" });
  table.append(el("thead", {}, el("tr", {},
    ...["When", "Type", "Skill / Variant", "Model", "Prompts", "Repeats", "Pass", "Convergence", "Cost"].map((h) => el("th", {}, h)))));
  const tb = el("tbody", {});
  for (const r of runs) {
    tb.append(el("tr", { onclick: () => renderDetail(root, r.id) },
      el("td", { class: "nowrap" }, fmtWhen(r.timestamp)),
      el("td", {}, el("span", { class: `tag type-${runTypeLabel(r)}`, title: `layout: ${r.layout}` }, runTypeLabel(r))),
      el("td", {}, skillVariant(r)),
      el("td", { class: "muted small" }, r.model || "—"),
      el("td", { class: "ellipsis", title: (r.prompts || []).join(", ") }, promptCell(r.prompts)),
      el("td", { class: "num" }, r.repeats ?? "—"),
      el("td", {}, passCell(r)),
      el("td", {}, r.convergence != null ? convBadge(r.convergence) : el("span", { class: "muted" }, "—")),
      el("td", { class: "num" }, r.cost_usd != null ? fmtCost(r.cost_usd) : el("span", { class: "muted" }, "—"))));
  }
  table.append(tb);
  root.append(el("div", { class: "card table-wrap" }, table));
}

function promptCell(prompts) {
  if (!prompts || !prompts.length) return "—";
  return prompts.length <= 2 ? prompts.join(", ") : `${prompts[0]} +${prompts.length - 1} more`;
}
function passCell(r) {
  if (r.pass_rate) return el("span", { class: "pill " + (r.pass_rate.startsWith("100") ? "ok" : r.pass_rate.startsWith("0") ? "bad" : "warn") }, r.pass_rate);
  if (r.status) {
    const cls = r.status === "pass" ? "ok" : r.status === "fail" || r.status === "error" ? "bad" : "neutral";
    return el("span", { class: "pill " + cls }, r.status);
  }
  return el("span", { class: "muted" }, "—");
}
function convBadge(v) {
  return el("span", { class: "convmeter", title: "overall convergence" },
    el("span", { class: "bar" }, el("span", { style: `width:${Math.round(v * 100)}%` })),
    el("span", { class: "convval" }, v.toFixed(2)));
}

// --------------------------------------------------------------------------- //
// detail view
// --------------------------------------------------------------------------- //
async function renderDetail(root, runId) {
  clear(root);
  root.append(el("div", { class: "small muted" }, "loading…"));
  let d;
  try { d = await getJSON(`/api/runs/${encodeURIComponent(runId)}`); }
  catch (e) { clear(root); root.append(el("div", { class: "err" }, e.message)); return; }
  clear(root);

  const summ = d.summary_json;
  const s = d.summary || {};
  const cfg = (d.run && d.run.config) || (summ && summ.config) || {};

  // ---- header ----
  root.append(el("div", { class: "detail-head" },
    el("button", { class: "btn ghost", onclick: () => renderHistoryTab(root) }, "← History"),
    el("span", { class: `tag type-${runTypeLabel(s)}` }, runTypeLabel(s)),
    el("span", { class: "run-id", title: runId }, runId)));

  // ---- overview stat bar (standardized: cost is ALWAYS present) ----
  const model = (cfg.model && (cfg.model.label || cfg.model)) || s.model;
  const stats = el("div", { class: "statbar" });
  const stat = (label, value, cls) => el("div", { class: "stat" + (cls ? " " + cls : "") },
    el("div", { class: "stat-val" }, value), el("div", { class: "stat-lbl" }, label));
  stats.append(
    stat("Skill / Variant", skillVariant(s)),
    stat("Model", model || "—"),
    stat("Repeats", s.repeats ?? "—"),
    stat("Cost", s.cost_usd != null ? fmtCost(s.cost_usd) : "—", s.cost_usd != null ? "accent" : ""),
  );
  const agg = summ && summ.aggregate;
  if (agg) {
    stats.append(
      stat("Pass rate", `${agg.passed}/${agg.total} · ${agg.pass_rate}`),
      stat("Tokens", `${fmtInt(agg.total_input_tokens)} in / ${fmtInt(agg.total_output_tokens)} out`),
    );
  }
  if (s.convergence != null) stats.append(stat("Convergence", s.convergence.toFixed(3), "accent"));
  if (s.status && !agg) stats.append(stat("Status", s.status));
  root.append(el("div", { class: "card overview" }, stats));

  // ---- body: left (drill-down) / right (viewer) ----
  const grid = el("div", { class: "detail-grid" });
  const left = el("div", { class: "detail-left" });
  const rightC = el("div", { class: "card panel viewer-panel" });
  grid.append(left, rightC);
  root.append(grid);

  const resetViewer = () => {
    clear(rightC);
    rightC.append(el("div", { class: "viewer-hint" },
      el("div", { class: "big-muted" }, "Nothing open"),
      el("div", { class: "muted small" }, "Pick a repeat / test on the left, or a file below, to view its table, script, or transcript here.")));
  };
  const openViewer = async (path, name) => {
    clear(rightC);
    rightC.append(el("div", { class: "viewer-path" }, name || path.split("/").pop(), el("span", { class: "muted small" }, "  " + path)));
    const url = `/api/runs/${encodeURIComponent(runId)}/file?path=${encodeURIComponent(path)}`;
    try {
      if (path.endsWith("transcript.json")) rightC.append(renderTranscript(JSON.parse(await getText(url))));
      else rightC.append(await loadFile(kindFor(path), url, path));
    } catch (e) { rightC.append(el("div", { class: "err" }, e.message)); }
  };

  resetViewer(); // default state; the iteration UI below may auto-open an artifact

  // ---- iteration selector + per-iteration panel ----
  const groups = d.iterations || [];
  const flat = [];
  for (const g of groups) for (const it of g.items) flat.push({ ...it, prompt: g.prompt });

  if (flat.length) {
    left.append(el("div", { class: "card section" },
      el("h3", {}, groups.length > 1 || flat.length > 1 ? "Iterations" : "Run"),
      buildIterationUI(groups, flat, runId, openViewer)));
  }

  // ---- convergence (overall) per prompt + contact sheet ----
  const convPairs = [];
  if (d.convergence && Object.keys(d.convergence).length) {
    for (const [name, rep] of Object.entries(d.convergence)) convPairs.push([name, rep, `prompts/${name}/contact_sheet.png`]);
  } else if (d.consistency_report) {
    convPairs.push([(d.consistency_report.prompt || "").slice(0, 60), d.consistency_report, "contact_sheet.png"]);
  }
  for (const [name, rep, sheet] of convPairs) {
    const sec = el("div", { class: "card section" }, el("h3", {}, "Convergence"));
    if (name) sec.append(el("div", { class: "muted small ellipsis", title: name, style: "margin:-.2rem 0 .5rem" }, name));
    sec.append(renderConvergence(rep));
    const sheetUrl = `/api/runs/${encodeURIComponent(runId)}/file?path=${encodeURIComponent(sheet)}`;
    const img = el("img", { class: "contact-sheet", src: sheetUrl, alt: "contact sheet", onclick: () => window.open(sheetUrl, "_blank") });
    img.addEventListener("error", () => img.remove());
    sec.append(el("div", { class: "muted small", style: "margin:.6rem 0 .3rem" }, "Contact sheet (click to enlarge)"), img);
    left.append(sec);
  }

  // ---- high-level collapsible file browser ----
  left.append(el("div", { class: "card section" },
    el("h3", {}, "Files"),
    renderCollapsibleTree(d.tree, { onFile: openViewer })));
}

// The iteration drop-down + the selected iteration's panel. Grouped by prompt so
// a multi-prompt run (or a sweep) offers a menu of the specific test / repeat.
function buildIterationUI(groups, flat, runId, openViewer) {
  const wrap = el("div", {});
  const sel = el("select", { class: "iter-select" });
  let idx = 0;
  flat.forEach((it, i) => {
    const bits = [it.label];
    if (it.cost_usd != null) bits.push(fmtCost(it.cost_usd));
    if (it.status) bits.push(it.status);
    const opt = el("option", { value: String(i) }, bits.join("  ·  "));
    if (groups.length > 1) {
      // group options under their prompt
    }
    sel.append(opt);
  });
  // If prompts differ, add optgroups for clarity.
  if (groups.length > 1) {
    clear(sel);
    let i = 0;
    for (const g of groups) {
      const og = el("optgroup", { label: g.prompt || "run" });
      for (const it of g.items) {
        const bits = [it.label];
        if (it.cost_usd != null) bits.push(fmtCost(it.cost_usd));
        if (it.status) bits.push(it.status);
        og.append(el("option", { value: String(i++) }, bits.join("  ·  ")));
      }
      sel.append(og);
    }
  }

  const panel = el("div", { class: "iter-panel" });
  const show = (i) => {
    idx = i;
    clear(panel);
    const it = flat[i];
    panel.append(renderIteration(it, runId, openViewer));
    // Fill the wide viewer with this iteration's most useful artifact so it is
    // never left empty: the rendered table if present, else its transcript.
    if (it.dir != null && it.has_png) openViewer(`${it.dir}/table.png`, "table.png");
    else if (it.dir != null && it.has_transcript) openViewer(`${it.dir}/transcript.json`, "transcript");
  };
  sel.addEventListener("change", () => show(parseInt(sel.value, 10)));

  wrap.append(el("label", { class: "field small" }, "Select a repeat / test"), sel, panel);
  show(0);
  return wrap;
}

function renderIteration(it, runId, openViewer) {
  const box = el("div", {});
  // stat chips for this invocation
  const chips = el("div", { class: "chips" });
  chips.append(el("span", { class: "chip strong" }, it.label));
  if (it.status) chips.append(el("span", { class: "pill " + (it.status === "pass" || it.status === "ok" ? "ok" : it.status === "fail" || it.status === "error" ? "bad" : "neutral") }, it.status));
  if (it.cost_usd != null) chips.append(el("span", { class: "chip" }, "cost ", fmtCost(it.cost_usd)));
  if (it.num_turns != null) chips.append(el("span", { class: "chip" }, `${it.num_turns} turns`));
  if (it.duration_ms != null) chips.append(el("span", { class: "chip" }, fmtDur(it.duration_ms)));
  box.append(chips);

  // table thumbnail (click -> open full in viewer)
  const fileUrl = (p) => `/api/runs/${encodeURIComponent(runId)}/file?path=${encodeURIComponent(p)}`;
  if (it.has_png && it.dir != null) {
    const p = `${it.dir}/table.png`;
    const img = el("img", { class: "iter-thumb", src: fileUrl(p), alt: "table.png", onclick: () => openViewer(p, "table.png") });
    img.addEventListener("error", () => img.replaceWith(el("div", { class: "muted small" }, "table.png not rendered")));
    box.append(img);
  } else {
    box.append(el("div", { class: "muted small nobox" }, "No table.png (this iteration did not render a table)"));
  }

  // action buttons -> load into the wide viewer
  const actions = el("div", { class: "iter-actions" });
  const mk = (label, path) => el("button", { class: "btn ghost sm", onclick: () => openViewer(path, label) }, label);
  if (it.has_png && it.dir != null) actions.append(mk("table.png", `${it.dir}/table.png`));
  if (it.has_py && it.dir != null) actions.append(mk("table.py", `${it.dir}/table.py`));
  if (it.has_transcript && it.dir != null) actions.append(mk("transcript", `${it.dir}/transcript.json`));
  box.append(actions);

  // per-iteration design choices (convergence runs) — the "iterable convergence"
  if (it.choices && Object.keys(it.choices).length) {
    const det = el("details", { class: "choices" });
    det.append(el("summary", {}, "design choices for this repeat"));
    const t = el("table", { class: "kv-table" });
    for (const [k, v] of Object.entries(it.choices)) {
      t.append(el("tr", {}, el("td", { class: "k" }, k), el("td", { class: "v" }, v == null ? "—" : String(v))));
    }
    det.append(t);
    box.append(det);
  }
  return box;
}

function renderConvergence(rep) {
  const overall = rep.overall_convergence;
  const box = el("div", {});
  box.append(el("div", { class: "conv-overall" },
    el("span", { class: "conv-overall-lbl" }, "overall"),
    el("span", { class: "bar wide" }, el("span", { style: `width:${Math.round((overall || 0) * 100)}%` })),
    el("span", { class: "convval strong" }, overall == null ? "—" : overall.toFixed(3))));
  const t = el("table", { class: "conv-table" });
  t.append(el("thead", {}, el("tr", {}, ...["Field", "Agree", "Consensus", "Baseline"].map((h) => el("th", {}, h)))));
  const tb = el("tbody", {});
  const conv = rep.convergence || {};
  for (const f of CONV_FIELDS) {
    const c = conv[f];
    if (!c) continue;
    tb.append(el("tr", {},
      el("td", { class: "field-name" }, f),
      el("td", { class: c.unanimous ? "ok num" : "num" }, c.agreement || "—"),
      el("td", { class: "ellipsis", title: String(c.consensus) }, truncate(c.consensus, 22)),
      el("td", { class: "muted ellipsis", title: String(c.baseline) }, truncate(c.baseline, 22))));
  }
  t.append(tb);
  box.append(el("div", { class: "table-wrap" }, t));
  return box;
}
function truncate(v, n) { const s = v == null ? "—" : String(v); return s.length > n ? s.slice(0, n) + "…" : s; }
