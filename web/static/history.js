// History tab: a sortable list of past runs -> a detail view with overview,
// convergence tables + contact sheet, and a file browser with interpretable
// transcripts (07-frontend-runner.md §5.2).
import { el, clear, getJSON, getText, fmtCost } from "./api.js";
import { renderTranscript } from "./transcript.js";
import { loadFile, kindFor } from "./viewers.js";

const CONV_FIELDS = [
  "heading_band_shade", "heading_band_hue", "palettes", "frame_present",
  "striping_present", "dividers_present", "caption_present", "source_present",
  "grouping_present", "stub_present", "columns_signature", "fmt_signature",
  "domain_signature", "color_signature", "data_hash",
];

export async function renderHistoryTab(root, openRunId = null) {
  clear(root);
  if (openRunId) return renderDetail(root, openRunId);
  root.append(el("div", { class: "small muted" }, "loading history…"));
  let data;
  try { data = await getJSON("/api/runs"); } catch (e) { clear(root); root.append(el("div", { class: "err" }, e.message)); return; }
  clear(root);
  if (data.busy) root.append(el("div", { class: "chip", style: "margin-bottom:.6rem" }, el("span", { class: "spinner" }), " a run is in progress"));
  const runs = data.runs || [];
  if (!runs.length) { root.append(el("div", { class: "muted" }, "No runs yet. Launch one from the Run tab.")); return; }

  const table = el("table", { class: "runs" });
  table.append(el("thead", {}, el("tr", {},
    ...["When", "Layout", "Skill/Variant", "Prompts", "Repeats", "Pass", "Convergence", "Cost"].map((h) => el("th", {}, h)))));
  const tb = el("tbody", {});
  for (const r of runs) {
    tb.append(el("tr", { onclick: () => renderDetail(root, r.id) },
      el("td", {}, fmtWhen(r.timestamp)),
      el("td", {}, el("span", { class: "tag" }, r.layout)),
      el("td", {}, r.skill ? `${r.skill} / ${r.variant || "—"}` : (r.variant || "—")),
      el("td", { title: (r.prompts || []).join(", ") }, promptCell(r.prompts)),
      el("td", {}, r.repeats ?? "—"),
      el("td", {}, passCell(r)),
      el("td", {}, r.convergence != null ? convBadge(r.convergence) : "—"),
      el("td", {}, r.cost_usd != null ? fmtCost(r.cost_usd) : "—")));
  }
  table.append(tb);
  root.append(el("h2", {}, `History (${runs.length})`), table);
}

function fmtWhen(ts) {
  const m = /^(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})$/.exec(ts || "");
  return m ? `${m[1]}-${m[2]}-${m[3]} ${m[4]}:${m[5]}` : (ts || "—");
}
function promptCell(prompts) {
  if (!prompts || !prompts.length) return "—";
  return prompts.length <= 2 ? prompts.join(", ") : `${prompts[0]} +${prompts.length - 1}`;
}
function passCell(r) {
  if (r.pass_rate) return el("span", { class: r.pass_rate.startsWith("100") ? "pass" : "" }, r.pass_rate);
  if (r.status) return el("span", { class: r.status === "pass" ? "pass" : r.status === "fail" ? "fail" : "" }, r.status);
  return "—";
}
function convBadge(v) {
  return el("span", { class: "chip", title: "overall convergence" }, el("span", { class: "bar", style: "width:48px;display:inline-block" }, el("span", { style: `width:${Math.round(v * 100)}%` })), " " + v.toFixed(2));
}

async function renderDetail(root, runId) {
  clear(root);
  root.append(el("button", { class: "btn secondary", onclick: () => renderHistoryTab(root) }, "← back"), el("span", { class: "small muted" }, "  loading…"));
  let d;
  try { d = await getJSON(`/api/runs/${encodeURIComponent(runId)}`); } catch (e) { clear(root); root.append(el("div", { class: "err" }, e.message)); return; }
  clear(root);
  root.append(el("div", {}, el("button", { class: "btn secondary", onclick: () => renderHistoryTab(root) }, "← back"), el("span", { style: "margin-left:.6rem;font-weight:600" }, runId), el("span", { class: "tag", style: "margin-left:.4rem" }, d.layout)));

  const grid = el("div", { class: "detail-grid", style: "margin-top:.8rem" });
  const left = el("div", { class: "card panel" });
  const rightC = el("div", { class: "card panel" });
  grid.append(left, rightC);
  root.append(grid);

  // ---- left: overview + convergence + file tree ----
  const summ = d.summary_json;
  const cfg = (d.run && d.run.config) || (summ && summ.config) || {};
  left.append(el("h2", {}, "Overview"));
  const model = cfg.model && (cfg.model.label || cfg.model);
  left.append(el("div", { class: "chips" },
    cfg.skill ? el("span", { class: "chip" }, "skill: ", el("span", { class: "tag" }, cfg.skill)) : null,
    cfg.variant ? el("span", { class: "chip" }, "variant: " + cfg.variant) : null,
    model ? el("span", { class: "chip" }, "model: " + model) : null,
    cfg.repeats != null ? el("span", { class: "chip" }, "repeats: " + cfg.repeats) : null,
    (d.run && d.run.status) ? el("span", { class: "chip" }, d.run.status) : null));
  if (summ && summ.aggregate) {
    const a = summ.aggregate;
    left.append(el("div", { class: "chips" },
      el("span", { class: "chip" }, `pass ${a.passed}/${a.total} (${a.pass_rate})`),
      el("span", { class: "chip" }, fmtCost(a.total_cost_usd)),
      el("span", { class: "chip" }, `tok ${a.total_input_tokens}/${a.total_output_tokens}`)));
  }

  // convergence: unified (per-prompt) or legacy consistency (top-level)
  const convPairs = [];
  if (d.convergence && Object.keys(d.convergence).length) {
    for (const [name, rep] of Object.entries(d.convergence)) convPairs.push([name, rep, `prompts/${name}/contact_sheet.png`]);
  } else if (d.consistency_report) {
    convPairs.push([(d.consistency_report.prompt || "").slice(0, 40), d.consistency_report, "contact_sheet.png"]);
  }
  for (const [name, rep, sheet] of convPairs) {
    left.append(el("h3", {}, `convergence · ${name}`));
    left.append(renderConvergence(rep));
    left.append(el("div", { class: "small muted", style: "margin:.3rem 0" }, "contact sheet:"));
    const img = el("img", { style: "max-width:100%;border:1px solid var(--border);border-radius:6px;cursor:zoom-in", src: `/api/runs/${encodeURIComponent(runId)}/file?path=${encodeURIComponent(sheet)}`, onclick: (e) => window.open(e.target.src, "_blank") });
    img.addEventListener("error", () => img.remove());
    left.append(img);
  }

  left.append(el("h3", {}, "files"));
  const viewerTarget = () => rightC;
  left.append(renderTree(d.tree, runId, viewerTarget));

  rightC.append(el("div", { class: "muted" }, "Select a file on the left. transcript.json renders as an interpretable transcript; table.png shows inline."));
}

function renderConvergence(rep) {
  const t = el("table", { class: "conv-table" });
  const overall = rep.overall_convergence;
  t.append(el("tr", {}, el("th", {}, "overall"), el("td", { colspan: "3" },
    el("span", { class: "bar", style: "width:120px;display:inline-block;vertical-align:middle" }, el("span", { style: `width:${Math.round((overall || 0) * 100)}%` })), " " + (overall == null ? "—" : overall.toFixed(3)))));
  t.append(el("tr", {}, ...["field", "agree", "consensus", "baseline"].map((h) => el("th", {}, h))));
  const conv = rep.convergence || {};
  for (const f of CONV_FIELDS) {
    const c = conv[f];
    if (!c) continue;
    t.append(el("tr", {},
      el("td", {}, f),
      el("td", { class: c.unanimous ? "pass" : "" }, c.agreement || "—"),
      el("td", { title: String(c.consensus) }, truncate(c.consensus, 18)),
      el("td", { class: "muted", title: String(c.baseline) }, truncate(c.baseline, 18))));
  }
  return t;
}
function truncate(v, n) { const s = v == null ? "—" : String(v); return s.length > n ? s.slice(0, n) + "…" : s; }

function renderTree(nodes, runId, targetFn, depth = 0) {
  const box = el("div", { class: "tree" });
  for (const n of nodes || []) {
    const pad = "  ".repeat(depth);
    if (n.type === "dir") {
      box.append(el("div", { class: "node dir" }, pad + n.name + "/"));
      box.append(renderTree(n.children, runId, targetFn, depth + 1));
    } else if (n.type === "link") {
      box.append(el("div", { class: "node link" }, pad + n.name + " →"));
    } else {
      box.append(el("div", { class: "node" }, pad, el("span", { class: "file clickable", onclick: () => openRunFile(targetFn(), runId, n.path) }, n.name)));
    }
  }
  return box;
}

async function openRunFile(target, runId, path) {
  clear(target);
  target.append(el("div", { class: "small muted" }, path));
  const url = `/api/runs/${encodeURIComponent(runId)}/file?path=${encodeURIComponent(path)}`;
  try {
    if (path.endsWith("transcript.json")) {
      const txt = await getText(url);
      target.append(renderTranscript(JSON.parse(txt)));
    } else {
      target.append(await loadFile(kindFor(path), url, path));
    }
  } catch (e) { target.append(el("div", { class: "err" }, e.message)); }
}
