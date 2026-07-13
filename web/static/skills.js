// Skills tab (view-only): browse each skill's files; render markdown/code/png;
// a "diff prose <-> scripts" affordance (07-frontend-runner.md §5.3).
import { el, clear, getText } from "./api.js";
import { loadFile, kindFor } from "./viewers.js";

export function renderSkillsTab(root, catalogs) {
  clear(root);
  const grid = el("div", { class: "skills-grid" });
  const nav = el("div", { class: "card panel" });
  const viewer = el("div", { class: "card panel" });
  grid.append(nav, viewer);
  root.append(grid);

  nav.append(el("h2", {}, "Skills"),
    el("button", { class: "btn secondary", style: "margin-bottom:.6rem", onclick: () => diffProseScripts(viewer, catalogs) }, "diff prose ↔ scripts"));

  for (const s of catalogs.skills) {
    nav.append(el("h3", {}, s.label));
    nav.append(el("div", { class: "small muted", style: "margin-bottom:.3rem" }, s.dir));
    nav.append(tree(s.label, s.tree, viewer));
  }
  viewer.append(el("div", { class: "muted" }, "Select a file to view. Markdown renders formatted; scripts as code; example PNGs inline."));
}

function tree(skill, nodes, viewer, depth = 0) {
  const box = el("div", { class: "tree" });
  for (const n of nodes || []) {
    const pad = "  ".repeat(depth);
    if (n.type === "dir") {
      box.append(el("div", { class: "node dir" }, pad + n.name + "/"));
      box.append(tree(skill, n.children, viewer, depth + 1));
    } else {
      box.append(el("div", { class: "node" }, pad, el("span", { class: "file clickable", onclick: () => open(viewer, skill, n.path) }, n.name)));
    }
  }
  return box;
}

async function open(viewer, skill, path) {
  clear(viewer);
  viewer.append(el("div", { class: "small muted" }, `${skill} / ${path}`));
  const url = `/api/skills/${encodeURIComponent(skill)}/file?path=${encodeURIComponent(path)}`;
  try { viewer.append(await loadFile(kindFor(path), url, path)); }
  catch (e) { viewer.append(el("div", { class: "err" }, e.message)); }
}

// Set-difference of SKILL.md lines: what the scripts skill adds/removes vs prose.
// Highlights the genuine scripts-usage content at a glance.
async function diffProseScripts(viewer, catalogs) {
  clear(viewer);
  viewer.append(el("h2", {}, "SKILL.md · prose → scripts"));
  let prose, scripts;
  try {
    prose = await getText("/api/skills/prose/file?path=SKILL.md");
    scripts = await getText("/api/skills/scripts/file?path=SKILL.md");
  } catch (e) { viewer.append(el("div", { class: "err" }, e.message)); return; }
  const pl = new Set(prose.split("\n").map((l) => l.trimEnd()));
  const sl = new Set(scripts.split("\n").map((l) => l.trimEnd()));
  const added = [...sl].filter((l) => l.trim() && !pl.has(l));
  const removed = [...pl].filter((l) => l.trim() && !sl.has(l));
  viewer.append(el("div", { class: "diffnote" }, `${added.length} lines only in scripts · ${removed.length} only in prose`));
  const pre = el("pre", { style: "white-space:pre-wrap" });
  for (const l of added) pre.append(el("div", { style: "color:var(--ok)" }, "+ " + l));
  for (const l of removed) pre.append(el("div", { style: "color:var(--danger)" }, "- " + l));
  if (!added.length && !removed.length) pre.append(el("div", { class: "muted" }, "SKILL.md is identical between prose and scripts."));
  viewer.append(el("div", { class: "viewer" }, pre));
}
