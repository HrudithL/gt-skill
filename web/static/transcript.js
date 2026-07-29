// Interpretable transcript rendering (07-frontend-runner.md §7). Shared by the
// live Run view and the History detail view. Never shows raw JSON.
import { el, fmtCost } from "./api.js";

const FILE_TOOLS = ["Read", "Write", "Edit", "NotebookEdit"];

function resultText(result) {
  if (!result) return null;
  const c = result.content;
  if (typeof c === "string") return c;
  if (Array.isArray(c)) {
    return c
      .map((b) => (typeof b === "string" ? b : b && b.type === "text" ? b.text : JSON.stringify(b)))
      .join("\n");
  }
  return c == null ? null : String(c);
}

function toolSummary(b) {
  const i = b.input || {};
  if (FILE_TOOLS.includes(b.name)) return i.file_path || i.notebook_path || "";
  if (b.name === "Bash") return i.command || "";
  if (b.name === "Skill") return i.command || i.skill || "";
  if (b.name === "Glob" || b.name === "Grep") return i.pattern || "";
  return Object.keys(i).slice(0, 3).join(", ");
}

// A tool-call card: TOOL(summary) header + optional input body + paired result.
function toolCard(b, result, opts) {
  const summary = toolSummary(b);
  const head = el(
    "div",
    { class: "head" },
    el("span", { class: "tname" }, b.name),
    el("span", {}, summary ? `(${summary})` : ""),
    result && result.is_error ? el("span", { class: "terr" }, "· error") : null
  );
  // Clicking a file-tool path opens it in the run's file viewer, when wired.
  if (FILE_TOOLS.includes(b.name) && summary && opts && opts.onFileClick) {
    head.style.cursor = "pointer";
    head.title = "open in file tree";
    head.addEventListener("click", () => opts.onFileClick(summary));
  }
  const card = el("div", { class: "toolcard" }, head);

  // Body: show the fuller input for Bash (command) / Write (content preview).
  const i = b.input || {};
  if (b.name === "Write" && i.content) {
    card.append(el("pre", {}, i.content.length > 4000 ? i.content.slice(0, 4000) + "\n… (truncated)" : i.content));
  } else if (b.name === "Edit" && (i.old_string || i.new_string)) {
    card.append(el("pre", {}, `- ${i.old_string || ""}\n+ ${i.new_string || ""}`));
  }
  const rt = resultText(result);
  if (rt != null && rt !== "") {
    card.append(el("pre", { class: "result" }, rt.length > 8000 ? rt.slice(0, 8000) + "\n… (truncated)" : rt));
  }
  return card;
}

function banner(m) {
  const d = m.data || {};
  const skills = (d.skills || d.slash_commands || []);
  const tools = d.tools || [];
  return el(
    "div",
    { class: "banner" },
    el("strong", {}, "run · "),
    `model ${d.model || "?"}`,
    skills.length ? ` · skills ${Array.isArray(skills) ? skills.join(", ") : skills}` : "",
    d.cwd ? ` · cwd ${d.cwd}` : "",
    tools.length ? ` · ${tools.length} tools` : ""
  );
}

function thinkingBlock(text) {
  return el(
    "details",
    { class: "thinking" },
    el("summary", {}, "thinking"),
    el("pre", {}, text)
  );
}

function outcome(m) {
  const cost = m.total_cost_usd;
  const dur = m.duration_ms != null ? `${(m.duration_ms / 1000).toFixed(1)}s` : "—";
  return el(
    "div",
    { class: "outcome" },
    el("strong", {}, m.is_error ? "failed" : "done"),
    ` · ${m.num_turns ?? "—"} turns · ${dur} · ${fmtCost(cost)}`,
    m.result ? el("div", { class: "small muted", style: "margin-top:.3rem;white-space:pre-wrap" }, String(m.result).slice(0, 600)) : null
  );
}

function assistantNodes(m, results, opts) {
  const out = [];
  for (const b of m.content || []) {
    if (b.type === "text" && b.text && b.text.trim()) {
      out.push(el("div", { class: "msg assistant" }, el("div", { class: "who" }, "assistant"), el("div", { style: "white-space:pre-wrap" }, b.text)));
    } else if (b.type === "thinking" && b.text) {
      out.push(thinkingBlock(b.text));
    } else if (b.type === "tool_use") {
      out.push(toolCard(b, results[b.id], opts));
    }
  }
  return out;
}

// messages: array of message dicts (engine.message_to_dict shape). opts.onFileClick(path).
export function renderTranscript(messages, opts = {}) {
  const root = el("div", { class: "transcript" });
  // Pair tool_results (from user messages) to their tool_use cards by id.
  const results = {};
  for (const m of messages) {
    if (m.role === "user" && Array.isArray(m.content)) {
      for (const b of m.content) if (b && b.type === "tool_result") results[b.tool_use_id] = b;
    }
  }
  let thinkingTokens = 0;
  for (const m of messages) {
    if (m.role === "system") {
      if (m.subtype === "init") root.append(banner(m));
      else if (m.subtype === "thinking_tokens") thinkingTokens++; // filtered to a meter
    } else if (m.role === "assistant") {
      for (const n of assistantNodes(m, results, opts)) root.append(n);
    } else if (m.role === "user") {
      // The original human prompt appears as bare text (string or text blocks).
      if (typeof m.content === "string") {
        root.append(el("details", { class: "msg user" }, el("summary", {}, "prompt"), el("pre", { style: "white-space:pre-wrap" }, m.content)));
      } else if (Array.isArray(m.content)) {
        for (const b of m.content) {
          if (b && b.type === "text" && b.text && b.text.trim()) {
            root.append(el("details", { class: "msg user" }, el("summary", {}, "prompt"), el("pre", { style: "white-space:pre-wrap" }, b.text)));
          }
        }
      }
    } else if (m.role === "result") {
      root.append(outcome(m));
    }
  }
  if (thinkingTokens) root.append(el("div", { class: "thinkmeter" }, `thinking… (${thinkingTokens} progress updates)`));
  if (!root.childNodes.length) root.append(el("div", { class: "muted small" }, "no transcript yet"));
  return root;
}
