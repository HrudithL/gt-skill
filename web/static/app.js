// SPA bootstrap: load catalogs once, wire the three tabs, handle navigation.
import { getJSON, el, clear } from "./api.js";
import { renderRunTab } from "./run.js";
import { renderHistoryTab } from "./history.js";
import { renderSkillsTab } from "./skills.js";

const view = document.getElementById("view");
const nav = document.getElementById("nav");
let catalogs = null;
let current = "run";
let cleanup = null; // teardown for the current tab (e.g. the Run tab's live stream)

async function loadCatalogs() {
  const [prompts, data, models, skills] = await Promise.all([
    getJSON("/api/prompts"), getJSON("/api/data"), getJSON("/api/models"), getJSON("/api/skills"),
  ]);
  catalogs = { grouped: prompts.grouped, data: data.data, models: models.models, skills: skills.skills };
}

function setTab(tab, arg) {
  // Tear down the previous tab (closes the Run tab's EventSource + timers)
  // before clearing the shared view, so nothing runs against detached DOM.
  if (cleanup) { try { cleanup(); } catch (_) {} cleanup = null; }
  current = tab;
  for (const b of nav.querySelectorAll("button")) b.classList.toggle("active", b.dataset.tab === tab);
  clear(view);
  if (tab === "run") cleanup = renderRunTab(view, catalogs, { onJumpToHistory: (id) => setTab("history", id) });
  else if (tab === "history") renderHistoryTab(view, arg || null);
  else if (tab === "skills") renderSkillsTab(view, catalogs);
}

function buildNav() {
  clear(nav);
  for (const [tab, label] of [["run", "Run"], ["history", "History"], ["skills", "Skills"]]) {
    nav.append(el("button", { dataset: { tab }, onclick: () => setTab(tab) }, label));
  }
}

(async function main() {
  try {
    await loadCatalogs();
    buildNav();
    setTab("run");
  } catch (e) {
    clear(view);
    view.append(el("div", { class: "err" }, "Failed to load catalogs: " + e.message));
  }
})();
