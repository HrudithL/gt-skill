// Tiny fetch + DOM helpers shared across the SPA (build-less, no deps).

export async function getJSON(url) {
  const r = await fetch(url);
  const d = await r.json().catch(() => ({ error: r.statusText }));
  if (!r.ok) throw new Error(d.error || r.statusText);
  return d;
}

export async function postJSON(url, body) {
  const r = await fetch(url, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body),
  });
  const d = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(d.error || r.statusText);
  return d;
}

export async function getText(url) {
  const r = await fetch(url);
  if (!r.ok) throw new Error(r.statusText);
  return r.text();
}

// el("div", {class:"x", onclick:fn, title:"t"}, child, child, ...)
// children: strings -> text nodes, nodes -> appended, arrays -> flattened, falsy -> skipped.
export function el(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v == null || v === false) continue;
    if (k === "class") node.className = v;
    else if (k === "html") node.innerHTML = v;
    else if (k.startsWith("on") && typeof v === "function") node.addEventListener(k.slice(2), v);
    else if (k === "dataset") Object.assign(node.dataset, v);
    else node.setAttribute(k, v === true ? "" : v);
  }
  append(node, children);
  return node;
}

export function append(node, children) {
  for (const c of children.flat()) {
    if (c == null || c === false) continue;
    node.append(c.nodeType ? c : document.createTextNode(String(c)));
  }
}

export function clear(node) {
  node.replaceChildren();
}

export function fmtCost(c) {
  return c == null ? "—" : "$" + Number(c).toFixed(4);
}

export function fmtInt(n) {
  return n == null ? "—" : Number(n).toLocaleString();
}
