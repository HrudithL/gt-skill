// File viewers: markdown -> HTML (minimal, dependency-free), code/json/image/text.
import { el, getText } from "./api.js";

function esc(s) {
  return s.replace(/[&<>]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]));
}

// Inline: `code`, **bold**, *italic*, [text](url). Operates on already-escaped text.
function inline(s) {
  return s
    .replace(/`([^`]+)`/g, (_, c) => `<code>${c}</code>`)
    .replace(/\*\*([^*]+)\*\*/g, (_, c) => `<strong>${c}</strong>`)
    .replace(/(^|[^*])\*([^*]+)\*/g, (_, p, c) => `${p}<em>${c}</em>`)
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, (_, t, u) => `<a href="${u}" target="_blank" rel="noopener">${t}</a>`);
}

// A pragmatic block-level markdown renderer covering the constructs used in the
// skill SKILL.md / references (headings, fenced code, lists, tables, blockquote,
// hr, paragraphs). Not a full CommonMark parser — good enough for the viewer.
export function renderMarkdown(text) {
  const lines = text.replace(/\r\n/g, "\n").split("\n");
  let html = "";
  let i = 0;
  const n = lines.length;
  while (i < n) {
    let line = lines[i];

    // fenced code
    if (/^```/.test(line)) {
      const buf = [];
      i++;
      while (i < n && !/^```/.test(lines[i])) buf.push(lines[i++]);
      i++; // closing fence
      html += `<pre><code>${esc(buf.join("\n"))}</code></pre>`;
      continue;
    }
    // heading
    let m = /^(#{1,6})\s+(.*)$/.exec(line);
    if (m) {
      const lvl = m[1].length;
      html += `<h${lvl}>${inline(esc(m[2]))}</h${lvl}>`;
      i++;
      continue;
    }
    // hr
    if (/^\s*([-*_])(\s*\1){2,}\s*$/.test(line)) { html += "<hr/>"; i++; continue; }
    // table (a header row followed by a --- separator)
    if (/\|/.test(line) && i + 1 < n && /^\s*\|?\s*:?-{2,}/.test(lines[i + 1])) {
      const parseRow = (r) => r.replace(/^\s*\|/, "").replace(/\|\s*$/, "").split("|").map((c) => c.trim());
      const head = parseRow(line);
      i += 2;
      let rows = "";
      while (i < n && /\|/.test(lines[i]) && lines[i].trim()) {
        rows += "<tr>" + parseRow(lines[i]).map((c) => `<td>${inline(esc(c))}</td>`).join("") + "</tr>";
        i++;
      }
      html += `<table><thead><tr>${head.map((c) => `<th>${inline(esc(c))}</th>`).join("")}</tr></thead><tbody>${rows}</tbody></table>`;
      continue;
    }
    // blockquote
    if (/^>\s?/.test(line)) {
      const buf = [];
      while (i < n && /^>\s?/.test(lines[i])) buf.push(lines[i++].replace(/^>\s?/, ""));
      html += `<blockquote>${inline(esc(buf.join(" ")))}</blockquote>`;
      continue;
    }
    // lists (grouped)
    if (/^\s*([-*+]|\d+\.)\s+/.test(line)) {
      const ordered = /^\s*\d+\./.test(line);
      const buf = [];
      while (i < n && /^\s*([-*+]|\d+\.)\s+/.test(lines[i])) {
        buf.push(lines[i++].replace(/^\s*([-*+]|\d+\.)\s+/, ""));
      }
      html += `<${ordered ? "ol" : "ul"}>` + buf.map((it) => `<li>${inline(esc(it))}</li>`).join("") + `</${ordered ? "ol" : "ul"}>`;
      continue;
    }
    // blank
    if (!line.trim()) { i++; continue; }
    // paragraph (gather until blank)
    const buf = [line];
    i++;
    while (i < n && lines[i].trim() && !/^(#{1,6}\s|```|>\s?|\s*([-*+]|\d+\.)\s)/.test(lines[i])) buf.push(lines[i++]);
    html += `<p>${inline(esc(buf.join(" ")))}</p>`;
  }
  return el("div", { class: "md", html });
}

// kind from events.kind_for; for images pass {url}, for text kinds pass {text}.
export function renderFile(kind, { text, url, name } = {}) {
  if (kind === "image") return el("div", { class: "viewer" }, el("img", { src: url, alt: name || "" }));
  if (kind === "markdown") return el("div", { class: "viewer" }, renderMarkdown(text || ""));
  if (kind === "json") {
    let pretty = text || "";
    try { pretty = JSON.stringify(JSON.parse(text), null, 2); } catch {}
    return el("div", { class: "viewer" }, el("pre", {}, pretty));
  }
  return el("div", { class: "viewer" }, el("pre", {}, text || ""));
}

// Fetch + render a text-or-image file from a URL, given its kind.
export async function loadFile(kind, url, name) {
  if (kind === "image") return renderFile(kind, { url, name });
  const text = await getText(url);
  return renderFile(kind, { text, name });
}

// Mirror runner.events.kind_for for the frontend so viewers pick the right mode.
export function kindFor(path) {
  const p = path.toLowerCase();
  if (/\.(png|jpe?g|gif|webp)$/.test(p)) return "image";
  if (p.endsWith(".py")) return "code";
  if (p.endsWith(".json")) return "json";
  if (p.endsWith(".md")) return "markdown";
  if (p.endsWith(".csv")) return "data";
  return "text";
}
