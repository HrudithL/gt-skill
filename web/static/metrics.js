// Metrics tab: "is the skill worth it" — three charts built straight from
// /api/metrics (which pools every historical convergence run), each pairing
// the skill's number against the no-skill baseline sampled from the exact
// same runs, so the comparison is real data, not a canned narrative.
import { el, clear, getJSON, fmtCost, fmtInt } from "./api.js";

const SVG_NS = "http://www.w3.org/2000/svg";
const SKILL_COLOR = "#1d4ed8";   // app accent — "with skill"
const BASE_COLOR = "#eb6834";    // validated categorical slot 2 — "no-skill baseline"

function svg(tag, attrs = {}, ...children) {
  const node = document.createElementNS(SVG_NS, tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v == null || v === false) continue;
    node.setAttribute(k, v);
  }
  for (const c of children.flat()) if (c != null) node.append(c);
  return node;
}

function pct(v) { return v == null ? "—" : Math.round(v * 100) + "%"; }

// ---- shared hover tooltip (one floating div per chart wrapper) ----
function makeTooltip(wrap) {
  const tip = el("div", { class: "chart-tip" });
  wrap.append(tip);
  return {
    show(clientX, clientY, rows) {
      clear(tip);
      for (const { label, value, color, dashed } of rows) {
        tip.append(el("div", { class: "chart-tip-row" },
          el("span", { class: "tip-key", style: `background:${color};${dashed ? "border-bottom:2px dashed " + color + ";background:transparent;height:0" : ""}` }),
          el("span", { class: "tip-val" }, value),
          el("span", { class: "tip-label" }, label)));
      }
      const box = wrap.getBoundingClientRect();
      tip.style.left = Math.min(clientX - box.left + 12, box.width - 180) + "px";
      tip.style.top = (clientY - box.top - 12) + "px";
      tip.classList.add("show");
    },
    hide() { tip.classList.remove("show"); },
  };
}

function legend(entries) {
  return el("div", { class: "chart-legend" }, entries.map(({ label, color, dashed }) =>
    el("span", { class: "chart-legend-item" },
      el("span", { class: "chart-legend-swatch", style: dashed ? `border-bottom:2px dashed ${color}` : `background:${color}` }),
      label)));
}

function chartCard(title, caption, chartNode, tableNode) {
  const details = tableNode ? el("details", { class: "chart-table-toggle" },
    el("summary", {}, "Table view"), tableNode) : null;
  return el("div", { class: "card metric-card" },
    el("h3", {}, title),
    caption ? el("div", { class: "metric-caption" }, caption) : null,
    chartNode,
    details);
}

// --------------------------------------------------------------------------- //
// Chart 1 — formatting checklist: skill consensus vs baseline, grouped bars
// --------------------------------------------------------------------------- //
const FIELD_LABELS = {
  frame_present: "Frame / border", striping_present: "Row striping", dividers_present: "Column dividers",
  caption_present: "Caption", source_present: "Source note", grouping_present: "Row groups", stub_present: "Stub column",
};

function formattingChart(rows) {
  const W = 680, H = 260, padL = 40, padR = 12, padT = 10, padB = 46;
  const plotW = W - padL - padR, plotH = H - padT - padB;
  const n = rows.length;
  const groupW = plotW / n;
  const barW = Math.min(26, groupW * 0.32);
  const gap = 4;

  const wrap = el("div", { class: "chart-wrap" });
  const tip = makeTooltip(wrap);
  const s = svg("svg", { viewBox: `0 0 ${W} ${H}`, width: "100%", height: H, role: "img" });

  // gridlines + y ticks (0/25/50/75/100%)
  for (const frac of [0, 0.25, 0.5, 0.75, 1]) {
    const y = padT + plotH * (1 - frac);
    s.append(svg("line", { x1: padL, x2: W - padR, y1: y, y2: y, stroke: "var(--grid,#e1e0d9)", "stroke-width": 1 }));
    s.append(svg("text", { x: padL - 6, y: y + 3, "text-anchor": "end", class: "chart-tick" }, Math.round(frac * 100) + "%"));
  }

  rows.forEach((r, i) => {
    const gx = padL + groupW * i + groupW / 2;
    const label = FIELD_LABELS[r.field] || r.field;
    s.append(svg("text", { x: gx, y: H - padB + 16, "text-anchor": "middle", class: "chart-tick" }, label));

    const bars = [
      { v: r.skill_rate, color: SKILL_COLOR, x: gx - barW - gap / 2, name: "With skill" },
      { v: r.baseline_rate, color: BASE_COLOR, x: gx + gap / 2, name: "No-skill baseline" },
    ];
    for (const b of bars) {
      const h = Math.max(0, plotH * b.v);
      const y = padT + plotH - h;
      const rect = svg("rect", { x: b.x, y, width: barW, height: h, rx: 4, fill: b.color, class: "chart-bar" });
      rect.addEventListener("pointerenter", (e) => tip.show(e.clientX, e.clientY, [
        { label: `${b.name} · ${label}`, value: pct(b.v), color: b.color },
      ]));
      rect.addEventListener("pointermove", (e) => tip.show(e.clientX, e.clientY, [
        { label: `${b.name} · ${label}`, value: pct(b.v), color: b.color },
      ]));
      rect.addEventListener("pointerleave", () => tip.hide());
      s.append(rect);
    }
  });

  wrap.append(s);
  wrap.append(legend([{ label: "With skill", color: SKILL_COLOR }, { label: "No-skill baseline", color: BASE_COLOR }]));

  const table = el("table", { class: "metric-table" },
    el("thead", {}, el("tr", {}, el("th", {}, "Check"), el("th", { class: "num" }, "With skill"), el("th", { class: "num" }, "Baseline"), el("th", { class: "num" }, "n"))),
    el("tbody", {}, rows.map((r) => el("tr", {},
      el("td", {}, FIELD_LABELS[r.field] || r.field),
      el("td", { class: "num" }, pct(r.skill_rate)),
      el("td", { class: "num" }, pct(r.baseline_rate)),
      el("td", { class: "num" }, r.n)))));

  return { node: wrap, table };
}

// --------------------------------------------------------------------------- //
// Chart 2 — consistency trend: skill convergence (solid) vs baseline-match
// benchmark (dashed, distinct) over historical runs
// --------------------------------------------------------------------------- //
function trendChart(rows) {
  const W = 680, H = 280, padL = 40, padR = 16, padT = 16, padB = 56;
  const plotW = W - padL - padR, plotH = H - padT - padB;
  const n = rows.length;
  const x = (i) => padL + (n === 1 ? plotW / 2 : (plotW * i) / (n - 1));
  const y = (v) => padT + plotH * (1 - (v == null ? 0 : v));

  const wrap = el("div", { class: "chart-wrap" });
  const tip = makeTooltip(wrap);
  const s = svg("svg", { viewBox: `0 0 ${W} ${H}`, width: "100%", height: H, role: "img" });

  for (const frac of [0, 0.25, 0.5, 0.75, 1]) {
    const yy = padT + plotH * (1 - frac);
    s.append(svg("line", { x1: padL, x2: W - padR, y1: yy, y2: yy, stroke: "var(--grid,#e1e0d9)", "stroke-width": 1 }));
    s.append(svg("text", { x: padL - 6, y: yy + 3, "text-anchor": "end", class: "chart-tick" }, Math.round(frac * 100) + "%"));
  }

  function pathFor(key) {
    return rows.map((r, i) => `${i === 0 ? "M" : "L"}${x(i)},${y(r[key])}`).join(" ");
  }
  s.append(svg("path", { d: pathFor("baseline_match_rate"), fill: "none", stroke: BASE_COLOR, "stroke-width": 2, "stroke-dasharray": "6 4" }));
  s.append(svg("path", { d: pathFor("convergence"), fill: "none", stroke: SKILL_COLOR, "stroke-width": 2 }));

  rows.forEach((r, i) => {
    const gx = x(i);
    // rotated x tick (date only)
    const dateLabel = (r.timestamp || "").slice(0, 8).replace(/^(\d{4})(\d{2})(\d{2})$/, "$2/$3");
    const tick = svg("text", { x: 0, y: 0, class: "chart-tick", "text-anchor": "end", transform: `translate(${gx},${H - padB + 14}) rotate(-40)` }, dateLabel);
    s.append(tick);

    for (const [key, color] of [["convergence", SKILL_COLOR], ["baseline_match_rate", BASE_COLOR]]) {
      const cy = y(r[key]);
      const dot = svg("circle", { cx: gx, cy, r: 4, fill: color, stroke: "var(--surface,#fff)", "stroke-width": 2 });
      const hit = svg("circle", { cx: gx, cy, r: 12, fill: "transparent", class: "chart-hit" });
      const onHover = (e) => tip.show(e.clientX, e.clientY, [
        { label: `${r.skill || "skill"} · ${r.prompt}`, value: pct(r.convergence), color: SKILL_COLOR },
        { label: "no-skill baseline benchmark", value: pct(r.baseline_match_rate), color: BASE_COLOR, dashed: true },
      ]);
      hit.addEventListener("pointerenter", onHover);
      hit.addEventListener("pointermove", onHover);
      hit.addEventListener("pointerleave", () => tip.hide());
      s.append(dot, hit);
    }
  });

  wrap.append(s);
  wrap.append(legend([
    { label: "Skill: repeat-to-repeat consistency", color: SKILL_COLOR },
    { label: "Benchmark: single no-skill attempt vs. that consensus", color: BASE_COLOR, dashed: true },
  ]));

  const table = el("table", { class: "metric-table" },
    el("thead", {}, el("tr", {}, el("th", {}, "Run"), el("th", {}, "Prompt"), el("th", { class: "num" }, "Skill consistency"), el("th", { class: "num" }, "Baseline benchmark"))),
    el("tbody", {}, rows.map((r) => el("tr", {},
      el("td", { class: "mono small" }, r.timestamp),
      el("td", { class: "ellipsis", title: r.prompt }, r.prompt),
      el("td", { class: "num" }, pct(r.convergence)),
      el("td", { class: "num" }, pct(r.baseline_match_rate))))));

  return { node: wrap, table };
}

// --------------------------------------------------------------------------- //
// Chart 3 — token / price per iteration: baseline vs skill-avg dumbbells
// --------------------------------------------------------------------------- //
function dumbbellChart(rows, { key, format, label }) {
  const rowH = 30, padL = 190, padR = 70;
  const PADT = 10, PADB = 26, W = 680;
  const plotW = W - padL - padR;
  const H = PADT + PADB + rowH * rows.length;

  const values = rows.flatMap((r) => [r[`baseline_${key}`], r[`skill_${key}_avg`] ?? r[`skill_${key}`]]);
  const maxV = Math.max(...values, 1) * 1.12;
  const x = (v) => padL + (plotW * v) / maxV;

  const wrap = el("div", { class: "chart-wrap" });
  const tip = makeTooltip(wrap);
  const s = svg("svg", { viewBox: `0 0 ${W} ${H}`, width: "100%", height: H, role: "img" });

  rows.forEach((r, i) => {
    const cy = PADT + rowH * i + rowH / 2;
    const bv = r[`baseline_${key}`];
    const sv = r[`skill_${key}_avg`];
    const rowLabel = `${r.prompt}${r.skill ? " (" + r.skill + ")" : ""}`;
    s.append(svg("text", { x: padL - 10, y: cy + 4, "text-anchor": "end", class: "chart-tick ellipsis-label" }, rowLabel));
    s.append(svg("line", { x1: x(bv), x2: x(sv), y1: cy, y2: cy, stroke: "var(--border-strong,#bccbdd)", "stroke-width": 2 }));

    const delta = bv ? (sv - bv) / bv : null;
    const deltaLabel = delta == null ? "—" : (delta >= 0 ? "+" : "") + Math.round(delta * 100) + "%";

    // When the two dots sit close enough to overlap, nudge them apart
    // vertically so both stay visible and the delta label has clear air.
    const overlap = Math.abs(x(sv) - x(bv)) < 16;
    const dotY = { base: cy + (overlap ? -5 : 0), skill: cy + (overlap ? 5 : 0) };

    for (const [v, color, name, yKey] of [[bv, BASE_COLOR, "No-skill baseline", "base"], [sv, SKILL_COLOR, "With skill (avg/iteration)", "skill"]]) {
      const dy = dotY[yKey];
      const dot = svg("circle", { cx: x(v), cy: dy, r: 6, fill: color, stroke: "var(--surface,#fff)", "stroke-width": 2 });
      const hit = svg("circle", { cx: x(v), cy: dy, r: 14, fill: "transparent", class: "chart-hit" });
      const onHover = (e) => tip.show(e.clientX, e.clientY, [
        { label: `${name} · ${rowLabel}`, value: format(v), color },
        { label: "Δ with skill vs baseline", value: deltaLabel, color: SKILL_COLOR },
      ]);
      hit.addEventListener("pointerenter", onHover);
      hit.addEventListener("pointermove", onHover);
      hit.addEventListener("pointerleave", () => tip.hide());
      s.append(dot, hit);
    }
    const labelX = Math.max(x(sv), x(bv)) + 12;
    s.append(svg("text", { x: labelX, y: cy + 4, class: `chart-delta ${delta == null ? "" : delta >= 0 ? "up" : "down"}` }, deltaLabel));
  });

  wrap.append(s);
  wrap.append(legend([{ label: "No-skill baseline", color: BASE_COLOR }, { label: "With skill (avg per iteration)", color: SKILL_COLOR }]));

  const table = el("table", { class: "metric-table" },
    el("thead", {}, el("tr", {}, el("th", {}, "Prompt"), el("th", {}, "Skill"), el("th", { class: "num" }, "Baseline " + label), el("th", { class: "num" }, "With-skill avg " + label), el("th", { class: "num" }, "Δ"))),
    el("tbody", {}, rows.map((r) => {
      const bv = r[`baseline_${key}`], sv = r[`skill_${key}_avg`];
      const delta = bv ? (sv - bv) / bv : null;
      return el("tr", {},
        el("td", { class: "ellipsis", title: r.prompt }, r.prompt),
        el("td", {}, r.skill || "—"),
        el("td", { class: "num" }, format(bv)),
        el("td", { class: "num" }, format(sv)),
        el("td", { class: "num" }, delta == null ? "—" : (delta >= 0 ? "+" : "") + Math.round(delta * 100) + "%"));
    })));

  return { node: wrap, table };
}

// --------------------------------------------------------------------------- //
// tab entry point
// --------------------------------------------------------------------------- //
export async function renderMetricsTab(root) {
  clear(root);
  root.append(el("div", { class: "small muted" }, "loading metrics…"));
  let d;
  try { d = await getJSON("/api/metrics"); }
  catch (e) { clear(root); root.append(el("div", { class: "err" }, e.message)); return; }
  clear(root);

  root.append(el("div", { class: "page-head" }, el("h2", {}, "Metrics"),
    el("span", { class: "count-badge" }, d.trend.length)));

  if (!d.trend.length) {
    root.append(el("div", { class: "empty" },
      "No convergence runs yet. Launch a run with repeat > 1 (baseline auto-on) from the Run tab to populate these charts."));
    return;
  }

  // ---- formatting checklist ----
  if (d.formatting.length) {
    const avgSkill = d.formatting.reduce((a, r) => a + r.skill_rate, 0) / d.formatting.length;
    const avgBase = d.formatting.reduce((a, r) => a + r.baseline_rate, 0) / d.formatting.length;
    const { node, table } = formattingChart(d.formatting);
    root.append(chartCard(
      "Formatting checklist: skill consensus vs. no-skill baseline",
      `Across ${d.formatting[0].n} runs, the skill's repeat-consensus includes these table elements ${pct(avgSkill)} of the time on average, vs. ${pct(avgBase)} when the model runs with no skill at all.`,
      node, table));
  }

  // ---- consistency trend ----
  {
    const avgConv = d.trend.reduce((a, r) => a + (r.convergence ?? 0), 0) / d.trend.length;
    const avgBase = d.trend.reduce((a, r) => a + (r.baseline_match_rate ?? 0), 0) / d.trend.length;
    const { node, table } = trendChart(d.trend);
    root.append(chartCard(
      "Consistency: repeated with-skill runs vs. a single no-skill attempt",
      `Averaged across every run so far, the skill's repeats agree with each other ${pct(avgConv)} of the time; a lone no-skill attempt only lands on that same consensus ${pct(avgBase)} of the time.`,
      node, table));
  }

  // ---- token / cost per iteration ----
  if (d.cost.length) {
    const totalBaseTok = d.cost.reduce((a, r) => a + r.baseline_tokens, 0);
    const totalSkillTok = d.cost.reduce((a, r) => a + r.skill_tokens_avg, 0);
    const tokDelta = (totalSkillTok - totalBaseTok) / totalBaseTok;
    const totalBaseCost = d.cost.reduce((a, r) => a + r.baseline_cost, 0);
    const totalSkillCost = d.cost.reduce((a, r) => a + r.skill_cost_avg, 0);
    const costDelta = (totalSkillCost - totalBaseCost) / totalBaseCost;

    const tok = dumbbellChart(d.cost, { key: "tokens", format: fmtInt, label: "tokens" });
    root.append(chartCard(
      "Token usage per iteration: skill vs. baseline",
      `On average the skill uses ${tokDelta >= 0 ? "+" : ""}${Math.round(tokDelta * 100)}% tokens per iteration vs. a no-skill attempt — the cost of the extra verification and formatting work behind the consistency above.`,
      tok.node, tok.table));

    const cost = dumbbellChart(d.cost, { key: "cost", format: fmtCost, label: "cost" });
    root.append(chartCard(
      "Price per iteration: skill vs. baseline",
      `That works out to ${costDelta >= 0 ? "+" : ""}${Math.round(costDelta * 100)}% price per iteration on average.`,
      cost.node, cost.table));
  }
}
