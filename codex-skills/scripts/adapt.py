import re
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping


@dataclass(frozen=True)
class AdapterSpec:
    conversion: str
    dependencies: tuple[str, ...]


_ADAPTERS = {
    "agent-reach": AdapterSpec(
        "dependency-required", ("agent-reach CLI and platform backends",)
    ),
    "allsup-leads-ssdi": AdapterSpec(
        "dependency-required",
        (
            "Datamine environment",
            "last30days data-source credentials",
            "here.now publishing credentials",
        ),
    ),
    "allsup-leads-veterans": AdapterSpec(
        "dependency-required",
        (
            "Datamine environment",
            "last30days data-source credentials",
            "here.now publishing credentials",
        ),
    ),
    "blind-spots-audit": AdapterSpec("native", ()),
    "blueprint": AdapterSpec("native", ()),
    "claude-memory-debug": AdapterSpec(
        "dependency-required",
        ("claude-memory CLI or MCP", "indexed Git repository"),
    ),
    "claude-memory-index": AdapterSpec(
        "dependency-required", ("claude-memory CLI or MCP", "Git repository")
    ),
    "claude-memory-search": AdapterSpec(
        "dependency-required",
        ("claude-memory CLI or MCP", "indexed Git repository"),
    ),
    "claude-memory-status": AdapterSpec(
        "dependency-required",
        ("claude-memory CLI or MCP", "local claude-memory services"),
    ),
    "closing-ritual": AdapterSpec(
        "dependency-required",
        ("target Git repository", "repository test toolchain"),
    ),
    "cloud-run-reauth": AdapterSpec(
        "dependency-required",
        ("gcloud CLI", "Google Cloud user and ADC access", "cloud-sql-proxy"),
    ),
    "context-keeper": AdapterSpec("adapted", ()),
    "desktop-delivery": AdapterSpec("native", ()),
    "doc-keeper": AdapterSpec(
        "dependency-required",
        ("target Git repository", "repository documentation checks"),
    ),
    "failure-modes": AdapterSpec("native", ()),
    "gitnexus-cli": AdapterSpec(
        "dependency-required", ("GitNexus CLI or MCP", "indexed Git repository")
    ),
    "gitnexus-debugging": AdapterSpec(
        "dependency-required", ("GitNexus CLI or MCP", "indexed Git repository")
    ),
    "gitnexus-exploring": AdapterSpec(
        "dependency-required", ("GitNexus CLI or MCP", "indexed Git repository")
    ),
    "gitnexus-guide": AdapterSpec(
        "dependency-required", ("GitNexus CLI or MCP", "indexed Git repository")
    ),
    "gitnexus-impact-analysis": AdapterSpec(
        "dependency-required", ("GitNexus CLI or MCP", "indexed Git repository")
    ),
    "gitnexus-pr-review": AdapterSpec(
        "dependency-required",
        ("GitNexus CLI or MCP", "Git repository and PR diff"),
    ),
    "gitnexus-refactoring": AdapterSpec(
        "dependency-required", ("GitNexus CLI or MCP", "indexed Git repository")
    ),
    "ground-truth": AdapterSpec("native", ()),
    "gws-shared": AdapterSpec(
        "dependency-required",
        (
            "connected Google Workspace apps or gws CLI",
            "Google Workspace credentials",
        ),
    ),
    "gws-workflow": AdapterSpec(
        "dependency-required",
        (
            "connected Google Workspace apps or gws CLI",
            "Google Workspace credentials",
        ),
    ),
    "gws-workflow-email-to-task": AdapterSpec(
        "dependency-required",
        (
            "connected Gmail and task apps or gws CLI",
            "Google Workspace credentials",
        ),
    ),
    "gws-workflow-file-announce": AdapterSpec(
        "dependency-required",
        (
            "connected Drive and Chat apps or gws CLI",
            "Google Workspace credentials",
        ),
    ),
    "gws-workflow-meeting-prep": AdapterSpec(
        "dependency-required",
        (
            "connected Gmail, Calendar, and Drive apps or gws CLI",
            "Google Workspace credentials",
        ),
    ),
    "gws-workflow-standup-report": AdapterSpec(
        "dependency-required",
        (
            "connected Calendar and Gmail apps or gws CLI",
            "Google Workspace credentials",
        ),
    ),
    "gws-workflow-weekly-digest": AdapterSpec(
        "dependency-required",
        (
            "connected Gmail, Calendar, and Drive apps or gws CLI",
            "Google Workspace credentials",
        ),
    ),
    "here-now": AdapterSpec(
        "dependency-required",
        ("bash", "curl", "file", "bundled or system jq", "here.now network access"),
    ),
    "intro-page": AdapterSpec(
        "dependency-required", ("SSH website host access", "browser automation")
    ),
    "last30days": AdapterSpec(
        "dependency-required", ("Python 3.12 or newer", "public network access")
    ),
    "mine": AdapterSpec(
        "dependency-required",
        ("Datamine repository and environment", "last30days data-source credentials"),
    ),
    "network-reactivator": AdapterSpec("native", ()),
    "page-rethink": AdapterSpec(
        "dependency-required", ("browser automation", "target website repository")
    ),
    "production-gate-audit": AdapterSpec(
        "dependency-required",
        ("target repository and deployment", "production service credentials"),
    ),
    "refine": AdapterSpec(
        "dependency-required",
        ("Sherlock and blue-healer repositories", "OSINT and enrichment credentials"),
    ),
    "ship-it": AdapterSpec(
        "dependency-required",
        ("tiger-claw-v4-core repository", "deployment credentials"),
    ),
    "signal-mine": AdapterSpec(
        "dependency-required",
        ("source APIs and credentials", "Python script dependencies"),
    ),
    "skill-miner": AdapterSpec("adapted", ()),
    "skills-librarian": AdapterSpec("adapted", ()),
    "the-rebuild": AdapterSpec("adapted", ()),
    "tiger-doc-keeper": AdapterSpec(
        "dependency-required",
        ("tiger-claw-v4-core repository", "repository documentation checks"),
    ),
    "tiger-leader-hunt": AdapterSpec(
        "dependency-required", ("last30days skill and data-source credentials",)
    ),
    "tiger-whitepaper": AdapterSpec(
        "dependency-required", ("Node.js", "Google Chrome")
    ),
    "tigerclaw-daily-checks": AdapterSpec(
        "dependency-required",
        ("tiger-claw-v4-core repository", "gcloud and database credentials"),
    ),
    "truth-keeper": AdapterSpec(
        "dependency-required", ("local Truth directory", "project repositories")
    ),
    "two-brents-brand": AdapterSpec("adapted", ()),
    "vault-hygiene": AdapterSpec(
        "dependency-required", ("local Obsidian vault repository",)
    ),
    "whitelabel-radar": AdapterSpec(
        "dependency-required",
        (
            "last30days and tiger-leader-hunt skills",
            "enrichment and publishing credentials",
        ),
    ),
}

ADAPTER_REGISTRY: Mapping[str, AdapterSpec] = MappingProxyType(_ADAPTERS)

RESOURCE_ADAPTER_PATHS: Mapping[str, frozenset[str]] = MappingProxyType(
    {
        "skill-miner": frozenset({"REFERENCE.md"}),
        "the-rebuild": frozenset({"REFERENCE.md"}),
    }
)

_SESSION_SKILLS = {
    "context-keeper",
    "closing-ritual",
    "doc-keeper",
    "tiger-doc-keeper",
}
_LIBRARY_SKILLS = {"skill-miner", "skills-librarian"}
_BROWSER_SKILLS = {"page-rethink", "intro-page"}
_CONNECTED_APP_SKILLS = {
    "gws-shared",
    "gws-workflow",
    "gws-workflow-email-to-task",
    "gws-workflow-file-announce",
    "gws-workflow-meeting-prep",
    "gws-workflow-standup-report",
    "gws-workflow-weekly-digest",
}
_DELEGATION_SKILLS = {"doc-keeper", "tiger-doc-keeper", "agent-reach"}
_CLAUDE_MEMORY_SKILLS = {
    "claude-memory-debug",
    "claude-memory-index",
    "claude-memory-search",
    "claude-memory-status",
}
_GITNEXUS_SKILLS = {
    "gitnexus-cli",
    "gitnexus-debugging",
    "gitnexus-exploring",
    "gitnexus-guide",
    "gitnexus-impact-analysis",
    "gitnexus-pr-review",
    "gitnexus-refactoring",
}
_CROSS_SKILL_PATHS = {
    "allsup-leads-ssdi",
    "allsup-leads-veterans",
    "mine",
    "refine",
    "signal-mine",
    "whitelabel-radar",
    "tiger-leader-hunt",
}

_PAGE_RETHINK_BROWSER_LINE = re.compile(
    r"(?m)^- \*\*Live page\*\*:.*Use the gstack browse binary:.*$"
)
_AGENT_CALL_BLOCK = re.compile(r"(?ms)^Agent\(\r?\n.*?^\)\r?\n")


def is_adapted_resource(skill_name: str, relative_path: str) -> bool:
    """Return whether a copied text resource has an explicit named adapter."""
    if skill_name not in ADAPTER_REGISTRY:
        raise KeyError(f"unknown Codex adapter: {skill_name}")
    normalized_path = str(relative_path).replace("\\", "/")
    return normalized_path in RESOURCE_ADAPTER_PATHS.get(skill_name, ())


def _newline_style(text: str) -> str:
    crlf_count = text.count("\r\n")
    lf_count = text.count("\n") - crlf_count
    return "\r\n" if crlf_count > lf_count else "\n"


def _replace_required_regex(
    skill_name: str,
    text: str,
    pattern: re.Pattern[str],
    replacement: str,
    *,
    expected: int,
) -> str:
    result, count = pattern.subn(replacement, text)
    if count != expected:
        raise ValueError(
            f"{skill_name}: expected {expected} occurrence(s) of "
            f"{pattern.pattern!r}, found {count}; source adapter drifted"
        )
    return result


def _replace_known_literal(
    skill_name: str,
    text: str,
    source: str,
    replacement: str,
    *,
    strict: bool,
    expected: int = 1,
) -> str:
    count = text.count(source)
    if strict and count != expected:
        raise ValueError(
            f"{skill_name}: expected {expected} occurrence(s) of {source!r}, found "
            f"{count}; source adapter drifted"
        )
    if count:
        return text.replace(source, replacement)
    return text


def _validate_entry(skill_name: str, spec: AdapterSpec, entry: Any) -> None:
    if entry is None:
        return
    if entry.source != skill_name:
        raise ValueError(
            f"adapter/source mismatch: requested {skill_name!r}, got {entry.source!r}"
        )
    if entry.conversion != spec.conversion:
        raise ValueError(
            f"{skill_name}: manifest conversion drifted from adapter registry"
        )
    if tuple(entry.dependencies) != spec.dependencies:
        raise ValueError(
            f"{skill_name}: manifest dependencies drifted from adapter registry"
        )


def _adapt_named_text(
    skill_name: str, text: str, relative_path: str, *, strict: bool, newline: str
) -> str:
    if skill_name == "page-rethink" and relative_path == "SKILL.md":
        if strict or _PAGE_RETHINK_BROWSER_LINE.search(text):
            text = _replace_required_regex(
                skill_name,
                text,
                _PAGE_RETHINK_BROWSER_LINE,
                (
                    "- **Live page**: use the installed `browser-use:browser` or "
                    "`vercel:agent-browser` skill to open the URL, inspect rendered text, "
                    "and capture viewport screenshots."
                ),
                expected=1,
            )

    if skill_name in {"doc-keeper", "tiger-doc-keeper"} and relative_path == "SKILL.md":
        direct_workflow = newline.join(
            (
                "Perform this workflow directly in the main Codex agent using the context below.",
                "Delegation is optional and may be used only when the active environment "
                "permits it;",
                "the workflow must remain valid without delegation.",
                "",
            )
        )
        if strict or _AGENT_CALL_BLOCK.search(text):
            text = _replace_required_regex(
                skill_name,
                text,
                _AGENT_CALL_BLOCK,
                direct_workflow,
                expected=1,
            )

        intro_source = (
            "This skill dispatches\n"
            f"the **`{skill_name}` subagent** to reconcile those docs to reality."
        )
        intro_replacement = (
            "This skill performs the documented reconciliation directly in the main "
            "Codex\nagent."
        )
        text = _replace_known_literal(
            skill_name,
            text,
            intro_source,
            intro_replacement,
            strict=strict,
        )

        if skill_name == "doc-keeper":
            how_source = (
                "Dispatch the `doc-keeper` agent with the `Agent` tool. It's self-contained "
                "— it\ndiscovers the project's docs and procedure itself. Give it the "
                "context it can't derive:"
            )
            how_replacement = (
                "Perform the doc-keeper workflow directly in the main Codex agent. It is "
                "self-contained and\ndiscovers the project's docs and procedure. Use the "
                "following situational context:"
            )
            after_source = (
                "Relay the agent's drift report and the docs PR URL to the user. The PR is "
                "NOT merged —\nsurface it for their per-PR go. Put anything needing a "
                "human decision in front of them."
            )
            after_replacement = (
                "Report the drift findings and docs PR URL to the user. The PR is NOT "
                "merged —\nsurface it for their per-PR go. Put any human decision in "
                "front of them."
            )
        else:
            how_source = (
                "Dispatch the `tiger-doc-keeper` agent with the `Agent` tool. The agent is\n"
                "**self-contained** — it holds the full Tiger doc map, CI guards, "
                "boundaries, and\nprocedure. Give it just the situational context it "
                "can't derive:"
            )
            how_replacement = (
                "Perform the tiger-doc-keeper workflow directly in the main Codex agent. "
                "The workflow is\n**self-contained** and holds the full Tiger doc map, CI "
                "guards, boundaries, and\nprocedure. Use only the situational context "
                "below:"
            )
            after_source = (
                "Relay the agent's drift report and the docs PR URL to Brent. The PR is "
                "NOT merged —\nsurface it for his per-PR go. If the agent flagged anything "
                "needing a human decision,\nput that in front of him as a question."
            )
            after_replacement = (
                "Report the drift findings and docs PR URL to Brent. The PR is NOT merged "
                "—\nsurface it for his per-PR go. Put any human decision in front of him "
                "as a question."
            )
        text = _replace_known_literal(
            skill_name, text, how_source, how_replacement, strict=strict
        )
        text = _replace_known_literal(
            skill_name, text, after_source, after_replacement, strict=strict
        )
        text = text.replace(
            "## Hard rules (the agent enforces these; you enforce them too)",
            "## Hard rules",
        )

    if skill_name == "the-rebuild" and relative_path == "REFERENCE.md":
        old_path = "~/.claude/skills/signal-mine/"
        count = text.count(old_path)
        if strict and count != 1:
            raise ValueError(
                f"{skill_name}: expected 1 occurrence(s) of {old_path!r}, found {count}; "
                "source adapter drifted"
            )
        text = text.replace(old_path, "~/.codex/skills/signal-mine/")

    if skill_name in _SESSION_SKILLS:
        text = text.replace(".claude/sessions", ".codex/sessions")
    if skill_name in _LIBRARY_SKILLS or skill_name in _CROSS_SKILL_PATHS:
        text = text.replace("~/.claude/skills/", "~/.codex/skills/")
        text = text.replace("~/.claude/skills", "~/.codex/skills")

    if skill_name in _CLAUDE_MEMORY_SKILLS:
        text = text.replace(
            "~/.claude/claude_desktop_config.json", "~/.codex/config.toml"
        )
        text = text.replace("restart Claude Code", "restart the active Codex session")
        text = text.replace("Install Claude Code plugin", "Install claude-memory MCP integration")

    if skill_name in _GITNEXUS_SKILLS:
        text = text.replace("Restart Claude Code", "Restart the active Codex session")
        text = text.replace(
            "In Claude Code, a PostToolUse hook detects staleness after `git commit` and "
            "`git merge` and notifies the agent to run `analyze`",
            "In Codex, check staleness explicitly after `git commit` and `git merge` and "
            "run `analyze` when needed",
        )

    # Skill installation paths are operational runtime coupling, not product names.
    text = text.replace("$HOME/.claude/skills/", "$HOME/.codex/skills/")
    text = text.replace("~/.claude/skills/", "~/.codex/skills/")

    safe_exact_rewrites = (
        ("AskUserQuestion", "Codex user-input request"),
        ("TodoWrite", "Codex task checklist"),
        ("Bash tool", "shell execution capability"),
        ("Read tool", "file-reading capability"),
        ("Write tool", "file-editing capability"),
        ("WebFetch", "Codex web fetch capability"),
        ("WebSearch", "Codex web search capability"),
        ("Agent tool", "optional delegation capability"),
        ("Task tool", "optional delegated-task capability"),
        ("Task(", "optional delegated task ("),
        ("Agent(", "optional delegation ("),
    )
    for source, replacement in safe_exact_rewrites:
        text = text.replace(source, replacement)
    return text


def _runtime_details(skill_name: str) -> list[str]:
    details: list[str] = []
    if skill_name in _SESSION_SKILLS:
        details.extend(
            (
                "Write current session snapshots only under `.codex/sessions/`.",
                "Treat historical `.claude/sessions/` files as read-only evidence; never "
                "write new snapshots there.",
            )
        )
        if skill_name == "context-keeper":
            details.append(
                "Before invoking the copied helper script, set `CONTEXT_KEEPER_DIR` "
                "to `<project-root>/.codex/sessions` so its preserved source default is "
                "never used for a current snapshot."
            )
    if skill_name in _LIBRARY_SKILLS:
        details.extend(
            (
                "Use Codex session/library roots and `~/.codex/skills` for current data.",
                "Historical Claude session or library data may be inspected only as "
                "read-only input.",
            )
        )
        if skill_name == "skill-miner":
            details.append(
                "Invoke the copied digest helper with `--dir ~/.codex/sessions` for current "
                "Codex data; pass a historical Claude directory only for deliberate "
                "read-only analysis."
            )
        if skill_name == "skills-librarian":
            details.append(
                "Set `SKILLS_DIR=~/.codex/skills` when invoking copied audit or backup "
                "helpers so their preserved source defaults cannot select a Claude shelf."
            )
    if skill_name in _BROWSER_SKILLS:
        details.append(
            "Use the installed `browser-use:browser` or `vercel:agent-browser` skill; "
            "preflight by checking installed skill availability before browsing."
        )
    if skill_name in _CONNECTED_APP_SKILLS:
        details.extend(
            (
                "Prefer connected Gmail/Google Drive app tools and other relevant "
                "connected Workspace apps when available.",
                "Use the `gws` CLI fallback only when the required connected app is "
                "unavailable; preflight with tool discovery and `command -v gws`.",
                "Never expose credentials or tokens. Confirm with the user immediately "
                "before any mutation, send, create, update, or delete operation.",
            )
        )
    if skill_name in _DELEGATION_SKILLS:
        details.append(
            "The direct main-agent workflow is always valid. Delegate only when the active "
            "environment permits it, and never require delegation to proceed."
        )
    if skill_name in _CLAUDE_MEMORY_SKILLS:
        details.append(
            "Keep `claude-memory` as the external product name. Use its actual MCP tools "
            "when available; otherwise preflight and use the `claude-memory` CLI."
        )
    if skill_name in _GITNEXUS_SKILLS:
        details.append(
            "Keep GitNexus as the external product name. Use actual GitNexus MCP tools and "
            "resources when available; otherwise preflight the CLI through `npx gitnexus`."
        )
    if skill_name in _CROSS_SKILL_PATHS:
        details.append(
            "Resolve sibling Codex skills from installed skill roots (including "
            "`~/.codex/skills`) or the current collection; do not assume a Claude skill root."
        )
    return details


def _append_runtime(
    skill_name: str, text: str, spec: AdapterSpec, newline: str
) -> str:
    lines = ["## Codex Runtime", ""]
    lines.extend(_runtime_details(skill_name))
    if lines[-1] != "":
        lines.append("")
    if spec.dependencies:
        lines.append("Mandatory dependencies:")
        lines.extend(f"- `{dependency}`" for dependency in spec.dependencies)
        lines.append("")
        lines.extend(
            (
                "Preflight each dependency using MCP/app capability discovery, CLI "
                "availability/version checks, read-only filesystem or Git checks for "
                "repositories, and provider auth-status commands without printing "
                "secrets, credentials, or tokens.",
                "If any mandatory dependency is unavailable, stop and report a concise "
                "blocked state naming the missing dependency and the next action needed.",
            )
        )
    else:
        lines.extend(
            (
                "No mandatory external dependencies are required. Preflight only the "
                "paths or optional capabilities used by the selected workflow.",
                "If an optional capability is unavailable, continue directly or report a "
                "concise blocked state only when the requested operation cannot proceed.",
            )
        )

    runtime = newline.join(lines) + newline
    if not text:
        return runtime
    if not text.endswith(("\n", "\r")):
        text += newline
    if not text.endswith(newline * 2):
        text += newline
    return text + runtime


def adapt_text(
    skill_name: str,
    text: str,
    *,
    relative_path: str = "SKILL.md",
    entry: Any = None,
) -> str:
    """Adapt one declared source text file for the Codex runtime."""
    try:
        spec = ADAPTER_REGISTRY[skill_name]
    except KeyError:
        raise KeyError(f"unknown Codex adapter: {skill_name}") from None
    _validate_entry(skill_name, spec, entry)
    if spec.conversion == "native":
        return text

    normalized_path = str(relative_path).replace("\\", "/")
    if normalized_path != "SKILL.md" and not is_adapted_resource(
        skill_name, normalized_path
    ):
        return text

    newline = _newline_style(text)
    adapted = _adapt_named_text(
        skill_name,
        text,
        normalized_path,
        strict=entry is not None,
        newline=newline,
    )
    if normalized_path == "SKILL.md":
        adapted = _append_runtime(skill_name, adapted, spec, newline)
    return adapted


def adapt_description(skill_name: str, description: str, *, entry: Any = None) -> str:
    """Normalize only runtime claims that would be false in a Codex copy."""
    try:
        spec = ADAPTER_REGISTRY[skill_name]
    except KeyError:
        raise KeyError(f"unknown Codex adapter: {skill_name}") from None
    _validate_entry(skill_name, spec, entry)
    if spec.conversion == "native":
        return description

    adapted = description
    if skill_name in _SESSION_SKILLS:
        adapted = adapted.replace(".claude/sessions/", ".codex/sessions/")
    if skill_name in _LIBRARY_SKILLS:
        adapted = adapted.replace("~/.claude/skills/", "~/.codex/skills/")
        adapted = adapted.replace("~/.claude/skills", "~/.codex/skills")
    if skill_name == "doc-keeper":
        adapted = adapted.replace(
            "Dispatches the doc-keeper subagent, which",
            "Runs the doc-keeper workflow directly; it",
        )
    if skill_name == "tiger-doc-keeper":
        adapted = adapted.replace(
            "Dispatches the tiger-doc-keeper subagent to",
            "Runs the tiger-doc-keeper workflow directly to",
        )
    return adapted
