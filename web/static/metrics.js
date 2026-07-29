// Metrics tab: "is the skill worth it" — every chart built straight from
// /api/metrics (which pools every historical convergence run and groups it by
// skill + prompt), each pairing the skill's average against the no-skill
// baseline sampled from the exact same runs, so the comparison is real data,
// not a canned narrative. Every chart carries its own axis scale and direct
// "baseline -> with skill" value labels, so it reads standalone — a viewer
// shouldn't need to hover or open the table to see what the numbers are.
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

// A "nice" axis step (1/2/5 x 10^n) so ticks land on round numbers.
function niceStep(maxV) {
  if (!(maxV > 0)) return 1;
  const raw = maxV / 4;
  const mag = Math.pow(10, Math.floor(Math.log10(raw)));
  const norm = raw / mag;
  return (norm <= 1 ? 1 : norm <= 2 ? 2 : norm <= 5 ? 5 : 10) * mag;
}

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
// formatting checklist (global): skill consensus vs baseline, grouped bars,
// each bar direct-labeled with its own percent so the chart reads without
// hovering.
// --------------------------------------------------------------------------- //
const FIELD_LABELS = {
  frame_present: "Frame / border", striping_present: "Row striping", dividers_present: "Column dividers",
  caption_present: "Caption", source_present: "Source note", grouping_present: "Row groups", stub_present: "Stub column",
};

function formattingChart(rows) {
  const W = 680, H = 280, padL = 40, padR = 12, padT = 22, padB = 46;
  const plotW = W - padL - padR, plotH = H - padT - padB;
  const n = rows.length;
  const groupW = plotW / n;
  const barW = Math.min(26, groupW * 0.32);
  const gap = 4;

  const wrap = el("div", { class: "chart-wrap" });
  const tip = makeTooltip(wrap);
  const s = svg("svg", { viewBox: `0 0 ${W} ${H}`, width: "100%", height: H, role: "img" });

  for (const frac of [0, 0.25, 0.5, 0.75, 1]) {
    const y = padT + plotH * (1 - frac);
    // The 0% line doubles as the bottom x-axis baseline, so it's drawn bolder
    // than the other gridlines rather than blending in with them.
    const isAxis = frac === 0;
    s.append(svg("line", { x1: padL, x2: W - padR, y1: y, y2: y, stroke: isAxis ? "var(--border-strong,#bccbdd)" : "var(--grid,#e1e0d9)", "stroke-width": isAxis ? 1.5 : 1 }));
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
      const onHover = (e) => tip.show(e.clientX, e.clientY, [{ label: `${b.name} · ${label}`, value: pct(b.v), color: b.color }]);
      rect.addEventListener("pointerenter", onHover);
      rect.addEventListener("pointermove", onHover);
      rect.addEventListener("pointerleave", () => tip.hide());
      s.append(rect);
      // direct value-at-the-tip label, so each bar reads without hovering
      s.append(svg("text", { x: b.x + barW / 2, y: y - 5, "text-anchor": "middle", class: "chart-bar-label" }, pct(b.v)));
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
// per (skill, prompt) dumbbell: baseline vs skill-avg, one row per combo —
// reused for compliance / consistency / tokens / price, since all four are
// "baseline_<key>" vs "skill_<key>_avg" pairs on a by_skill_prompt row.
//
// Every row carries an always-visible "baseline -> with skill" value pair and
// a delta chip in fixed right-hand columns (not attached to the dots, which
// move), plus a top axis with real gridlines/ticks — so the exact numbers and
// their scale are both readable without hovering.
// --------------------------------------------------------------------------- //
function dumbbellChart(rows, { key, format, label, isPercent, higherIsBetter = true, deltaLabel = "Δ", deltaValue, deltaFormat }) {
  const getDelta = deltaValue || ((r) => {
    const bv = r[`baseline_${key}`], sv = r[`skill_${key}_avg`];
    return bv != null ? (bv === 0 ? null : (sv - bv) / bv) : null;
  });
  const fmtDelta = deltaFormat || ((d) => d == null ? "—" : (d >= 0 ? "+" : "") + Math.round(d * 100) + "%");
  const rowH = 32, padL = 200, padR = 220;
  // AXIS_H reserves room below the last row for a real bottom x-axis (baseline
  // + tick marks + numbers), separate from PADB's small breathing-room gap.
  const PADT = 26, PADB = 10, AXIS_H = 26, W = 800;
  const plotW = W - padL - padR;
  const plotBottomY = PADT + rowH * rows.length + PADB;
  const H = plotBottomY + AXIS_H;
  // The last axis tick is centered at the plot's right edge (W - padR), so its
  // own label (up to ~$0.2000 wide) needs real clearance before this column
  // starts, not just a token 16px gap.
  const valueColX = W - padR + 40;
  const deltaColX = W - 8;

  const values = rows.flatMap((r) => [r[`baseline_${key}`], r[`skill_${key}_avg`]]);
  const dataMax = Math.max(...values, isPercent ? 1 : 0);
  const ticks = isPercent
    ? [0, 0.25, 0.5, 0.75, 1]
    : (() => {
        const step = niceStep(dataMax);
        const top = Math.ceil(dataMax / step) * step;
        const out = [];
        for (let t = 0; t <= top + 1e-9; t += step) out.push(t);
        return out;
      })();
  const domainMax = ticks[ticks.length - 1] || 1;
  const x = (v) => padL + (plotW * v) / domainMax;

  const wrap = el("div", { class: "chart-wrap" });
  const tip = makeTooltip(wrap);
  const s = svg("svg", { viewBox: `0 0 ${W} ${H}`, width: "100%", height: H, role: "img" });

  // gridlines through every row, ticks labeled at both the top (repeated once
  // per column, handy while scanning row labels) and along a real bottom
  // x-axis (baseline + tick marks) so the value scale reads like a
  // conventional chart axis, not just gridlines.
  for (const t of ticks) {
    const gx = x(t);
    s.append(svg("line", { x1: gx, x2: gx, y1: PADT - 4, y2: plotBottomY, stroke: "var(--grid,#e1e0d9)", "stroke-width": 1 }));
    s.append(svg("text", { x: gx, y: PADT - 10, "text-anchor": "middle", class: "chart-tick" }, format(t)));
  }
  // bottom x-axis: baseline + a tick mark and number under every gridline
  s.append(svg("line", { x1: padL, x2: padL + plotW, y1: plotBottomY, y2: plotBottomY, stroke: "var(--border-strong,#bccbdd)", "stroke-width": 1 }));
  for (const t of ticks) {
    const gx = x(t);
    s.append(svg("line", { x1: gx, x2: gx, y1: plotBottomY, y2: plotBottomY + 4, stroke: "var(--border-strong,#bccbdd)", "stroke-width": 1 }));
    s.append(svg("text", { x: gx, y: plotBottomY + 15, "text-anchor": "middle", class: "chart-tick" }, format(t)));
  }
  // column headers for the always-visible value/delta labels
  s.append(svg("text", { x: valueColX, y: PADT - 10, class: "chart-tick" }, "baseline → with skill"));
  s.append(svg("text", { x: deltaColX, y: PADT - 10, "text-anchor": "end", class: "chart-tick" }, deltaLabel));

  rows.forEach((r, i) => {
    const cy = PADT + rowH * i + rowH / 2;
    const bv = r[`baseline_${key}`];
    const sv = r[`skill_${key}_avg`];
    const rowLabel = `${r.prompt} (${r.skill})`;
    const nLabel = `${r.n_iterations} iteration${r.n_iterations === 1 ? "" : "s"} · ${r.n_runs} run${r.n_runs === 1 ? "" : "s"}`;
    s.append(svg("text", { x: padL - 10, y: cy + 4, "text-anchor": "end", class: "chart-tick ellipsis-label" }, rowLabel));
    s.append(svg("line", { x1: x(bv), x2: x(sv), y1: cy, y2: cy, stroke: "var(--border-strong,#bccbdd)", "stroke-width": 2 }));

    const delta = getDelta(r);
    const deltaText = fmtDelta(delta);
    // "Better" depends on the metric — a rise in compliance/consistency is
    // good (green), a rise in tokens/cost is bad (red) — so color follows
    // higherIsBetter rather than assuming positive-always-red/negative-green.
    const good = delta == null ? null : (higherIsBetter ? delta >= 0 : delta <= 0);

    // When the two dots sit close enough to overlap, nudge them apart
    // vertically so both stay visible.
    const overlap = Math.abs(x(sv) - x(bv)) < 16;
    const dotY = { base: cy + (overlap ? -5 : 0), skill: cy + (overlap ? 5 : 0) };

    for (const [v, color, name, yKey] of [[bv, BASE_COLOR, "No-skill baseline", "base"], [sv, SKILL_COLOR, "With skill (avg)", "skill"]]) {
      const dy = dotY[yKey];
      const dot = svg("circle", { cx: x(v), cy: dy, r: 6, fill: color, stroke: "var(--surface,#fff)", "stroke-width": 2 });
      const hit = svg("circle", { cx: x(v), cy: dy, r: 14, fill: "transparent", class: "chart-hit" });
      const onHover = (e) => tip.show(e.clientX, e.clientY, [
        { label: `${name} · ${rowLabel}`, value: format(v), color },
        { label: `${deltaLabel} vs baseline`, value: deltaText, color: SKILL_COLOR },
        { label: "sample size", value: nLabel, color: "var(--muted,#898781)" },
      ]);
      hit.addEventListener("pointerenter", onHover);
      hit.addEventListener("pointermove", onHover);
      hit.addEventListener("pointerleave", () => tip.hide());
      s.append(dot, hit);
    }

    // Always-visible value pair + delta, in fixed columns so they never
    // collide with the dots (which move) or with each other.
    const valuePair = bv == null ? `— → ${format(sv)}` : `${format(bv)} → ${format(sv)}`;
    s.append(svg("text", { x: valueColX, y: cy + 4, class: "chart-value-pair" }, valuePair));
    s.append(svg("text", { x: deltaColX, y: cy + 4, "text-anchor": "end", class: `chart-delta ${good == null ? "" : good ? "good" : "bad"}` }, deltaText));
  });

  wrap.append(s);
  wrap.append(legend([{ label: "No-skill baseline", color: BASE_COLOR }, { label: "With skill (average)", color: SKILL_COLOR }]));

  const table = el("table", { class: "metric-table" },
    el("thead", {}, el("tr", {}, el("th", {}, "Prompt"), el("th", {}, "Skill"), el("th", { class: "num" }, "Baseline " + label), el("th", { class: "num" }, "With-skill avg " + label), el("th", { class: "num" }, deltaLabel), el("th", { class: "num" }, "iterations"))),
    el("tbody", {}, rows.map((r) => {
      const bv = r[`baseline_${key}`], sv = r[`skill_${key}_avg`];
      return el("tr", {},
        el("td", {}, r.prompt),
        el("td", {}, r.skill),
        el("td", { class: "num" }, format(bv)),
        el("td", { class: "num" }, format(sv)),
        el("td", { class: "num" }, fmtDelta(getDelta(r))),
        el("td", { class: "num" }, r.n_iterations));
    })));

  return { node: wrap, table };
}

function avgDelta(rows, key) {
  const withBoth = rows.filter((r) => r[`baseline_${key}`] != null && r[`skill_${key}_avg`] != null);
  if (!withBoth.length) return null;
  const base = withBoth.reduce((a, r) => a + r[`baseline_${key}`], 0) / withBoth.length;
  const skill = withBoth.reduce((a, r) => a + r[`skill_${key}_avg`], 0) / withBoth.length;
  return { base, skill, delta: base ? (skill - base) / base : null };
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

  const bySP = d.by_skill_prompt || [];
  root.append(el("div", { class: "page-head" }, el("h2", {}, "Metrics"),
    el("span", { class: "count-badge" }, bySP.length)));

  // Rows can exist with every baseline_* field null (repeats run with the
  // baseline checkbox off, the Run tab's default) — every chart below would
  // then filter down to zero rows, so check for an actual comparison rather
  // than just a nonempty list before falling through to the charts.
  const hasBaselineData = bySP.some((r) =>
    r.baseline_compliance != null || r.baseline_consistency != null || r.baseline_tokens != null || r.baseline_cost != null);
  if (!bySP.length || !hasBaselineData) {
    root.append(el("div", { class: "empty" },
      bySP.length
        ? "Found skill/prompt data, but none of it has a baseline to compare against. Check “Also run a baseline without the skill” on the Run tab and re-run to populate these charts."
        : "No convergence runs yet. Launch a run with repeat > 1 and the baseline checkbox on from the Run tab to populate these charts."));
    return;
  }

  // ---- formatting checklist (global, which specific elements) ----
  if (d.formatting.length) {
    const avgSkill = d.formatting.reduce((a, r) => a + r.skill_rate, 0) / d.formatting.length;
    const avgBase = d.formatting.reduce((a, r) => a + r.baseline_rate, 0) / d.formatting.length;
    const { node, table } = formattingChart(d.formatting);
    root.append(chartCard(
      "Formatting checklist: which elements, skill vs. no-skill baseline",
      `Across ${d.formatting[0].n} samples, the skill's repeat-consensus includes these table elements ${pct(avgSkill)} of the time on average, vs. ${pct(avgBase)} when the model runs with no skill at all.`,
      node, table));
  }

  // ---- compliance per skill & prompt (composite checklist score) ----
  {
    const a = avgDelta(bySP, "compliance");
    const rows = bySP.filter((r) => r.baseline_compliance != null && r.skill_compliance_avg != null);
    const { node, table } = dumbbellChart(rows, { key: "compliance", format: pct, label: "compliance", isPercent: true, higherIsBetter: true });
    root.append(chartCard(
      "Formatting compliance per skill & prompt",
      a ? `Averaged across every skill/prompt combo: ${pct(a.base)} checklist compliance with no skill, ${pct(a.skill)} with the skill — every row below shows its own before/after percentage.` : "",
      node, table));
  }

  // ---- consistency per skill & prompt ----
  {
    const a = avgDelta(bySP, "consistency");
    const rows = bySP.filter((r) => r.baseline_consistency != null && r.skill_consistency_avg != null);
    const { node, table } = dumbbellChart(rows, { key: "consistency", format: pct, label: "consistency", isPercent: true, higherIsBetter: true });
    root.append(chartCard(
      "Consistency per skill & prompt: repeats vs. a single no-skill attempt",
      a ? `Averaged across every combo: a single no-skill attempt lands on the skill's own consensus ${pct(a.base)} of the time; the skill's own repeats agree with each other ${pct(a.skill)} of the time — every row below shows its own before/after percentage.` : "",
      node, table));
  }

  // ---- token usage & price per skill & prompt (merged: cost tracks token
  // count almost exactly, so one dumbbell — scaled on tokens — carries both;
  // the right-hand column shows the actual dollar cost increase rather than
  // a second, redundant percentage) ----
  {
    const aTok = avgDelta(bySP, "tokens");
    const aCost = avgDelta(bySP, "cost");
    const rows = bySP.filter((r) => r.baseline_tokens != null && r.skill_tokens_avg != null);
    const { node, table } = dumbbellChart(rows, {
      key: "tokens", format: fmtInt, label: "tokens", isPercent: false, higherIsBetter: false,
      deltaLabel: "cost Δ",
      deltaValue: (r) => (r.baseline_cost != null && r.skill_cost_avg != null) ? r.skill_cost_avg - r.baseline_cost : null,
      deltaFormat: (d) => d == null ? "—" : (d >= 0 ? "+$" : "-$") + Math.abs(d).toFixed(4),
    });
    root.append(chartCard(
      "Token usage & price per iteration, per skill & prompt",
      aTok && aCost ? `Averaged across every combo: ${fmtInt(aTok.base)} tokens per iteration with no skill vs. ${fmtInt(aTok.skill)} with the skill (${aTok.delta >= 0 ? "+" : ""}${Math.round(aTok.delta * 100)}%) — the cost of the extra verification and formatting work behind the consistency above, which comes out to ${fmtCost(aCost.base)} vs. ${fmtCost(aCost.skill)} per iteration.` : "",
      node, table));
  }
}
