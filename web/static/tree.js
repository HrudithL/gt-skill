// A reusable, collapsible file tree. Folders are <details> collapsed by default,
// so a run dir reads as a high-level outline (skill/, table.py, table.png, …)
// instead of dumping the whole mounted skill's hundreds of files at once.
//
// The mounted skill (the `.claude` symlink + its `.claude-<variant>` target) is
// folded into a single collapsed "skill" node so it never floods the tree; the
// user can still expand it to browse SKILL.md / references / scripts.
import { el } from "./api.js";

const IMG_RE = /\.(png|jpe?g|gif|webp|svg)$/i;

function icon(kind) {
  if (kind === "dir") return "📁";
  if (kind === "skill") return "📦";
  if (kind === "link") return "🔗";
  return "📄";
}

// Recognize the mounted-skill nodes so they can be collapsed to one entry.
function isSkillMount(node) {
  return node.name === ".claude" || /^\.claude(-|$)/.test(node.name) || node.name === ".claude-skill-creator";
}

// Depth-first count of files under a folder (for the "N files" hint).
function countFiles(nodes) {
  let n = 0;
  for (const c of nodes || []) {
    if (c.type === "dir") n += countFiles(c.children);
    else if (c.type === "file") n += 1;
  }
  return n;
}

function fileNode(node, opts) {
  const isImg = IMG_RE.test(node.name);
  const row = el("div", { class: "tnode tfile", title: node.path },
    el("span", { class: "tico" }, icon(isImg ? "img" : "file")),
    el("span", { class: "tname" }, node.name));
  if (opts.onFile) {
    row.classList.add("clickable");
    row.addEventListener("click", () => opts.onFile(node.path, node.name));
  }
  return row;
}

function linkNode(node) {
  return el("div", { class: "tnode tlink", title: node.path + " (symlink)" },
    el("span", { class: "tico" }, icon("link")),
    el("span", { class: "tname" }, node.name),
    el("span", { class: "tmeta" }, "→"));
}

function dirNode(node, opts, depth, asSkill = false) {
  const kids = node.children || [];
  const count = countFiles(kids);
  const det = el("details", { class: "tdir" + (asSkill ? " tskill" : "") });
  // Top-level dirs start open so the run's shape is visible; deeper ones and the
  // skill mount stay collapsed to keep the outline high-level.
  if (depth === 0 && !asSkill) det.open = true;
  const sum = el("summary", { class: "tnode" },
    el("span", { class: "tico" }, icon(asSkill ? "skill" : "dir")),
    el("span", { class: "tname" }, asSkill ? "skill" : node.name),
    el("span", { class: "tmeta" }, count ? `${count} file${count === 1 ? "" : "s"}` : ""));
  det.append(sum);
  const body = el("div", { class: "tchildren" });
  // Lazily build children the first time the folder is opened (keeps big skill
  // mounts cheap until the user actually looks inside).
  let built = false;
  const build = () => {
    if (built) return;
    built = true;
    for (const c of nodeList(kids, opts, depth + 1)) body.append(c);
  };
  if (det.open) build();
  det.addEventListener("toggle", () => { if (det.open) build(); });
  det.append(body);
  return det;
}

function nodeList(nodes, opts, depth) {
  const out = [];
  for (const n of nodes || []) {
    // The bare `.claude` symlink just points at the `.claude-<variant>` mount we
    // already fold into a single "skill" node — drop it to avoid a dangling link.
    if (n.type === "link" && n.name === ".claude") continue;
    if (n.type === "dir" && isSkillMount(n)) out.push(dirNode(n, opts, depth, true));
    else if (n.type === "dir") out.push(dirNode(n, opts, depth));
    else if (n.type === "link") out.push(linkNode(n));
    else out.push(fileNode(n, opts));
  }
  return out;
}

// renderCollapsibleTree(nodes, { onFile(path, name) }) -> DOM node.
export function renderCollapsibleTree(nodes, opts = {}) {
  const box = el("div", { class: "ftree" });
  for (const c of nodeList(nodes, opts, 0)) box.append(c);
  if (!box.childNodes.length) box.append(el("div", { class: "muted small" }, "empty"));
  return box;
}
