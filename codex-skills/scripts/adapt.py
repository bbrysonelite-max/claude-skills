import re
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping


@dataclass(frozen=True)
class AdapterSpec:
    conversion: str
    dependencies: tuple[str, ...]


@dataclass(frozen=True)
class ExpectedRewrite:
    pattern: re.Pattern[str]
    expected: int
    replacement: Any = None


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
            "connected Google Calendar and Google Tasks capabilities or gws CLI",
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
        "agent-reach": frozenset({"references/dev.md"}),
        "here-now": frozenset({"references/REFERENCE.md"}),
        "last30days": frozenset(
            {
                "references/save-html-brief.md",
                "scripts/lib/providers.py",
                "scripts/watchlist.py",
            }
        ),
        "signal-mine": frozenset({"verticals/ssdi-work-fear.md"}),
        "skill-miner": frozenset({"BACKLOG.md", "REFERENCE.md"}),
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

_AGENT_CALL_BLOCK = re.compile(r"(?ms)^Agent\(\r?\n.*?^\)\r?\n")

_PROHIBITED_MARKDOWN_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("AskUserQuestion", re.compile(r"\bAskUserQuestion\b")),
    ("TodoWrite", re.compile(r"\bTodoWrite\b")),
    ("Agent call", re.compile(r"Agent\(")),
    ("Task call", re.compile(r"Task\(")),
    (
        "Claude tool name",
        re.compile(
            r"`?(?:Read|Write|Bash|Glob|Grep|WebSearch|WebFetch|Agent|Task)`?"
            r"\s+tool\b"
        ),
    ),
    ("WebSearch", re.compile(r"\bWebSearch\b")),
    ("WebFetch", re.compile(r"\bWebFetch\b")),
    (
        "Claude skill/plugin/cache path",
        re.compile(
            r"(?:(?:~|\$HOME)/)?\.claude/"
            r"(?:skills|plugins/(?:cache|marketplaces))(?![\w-])"
        ),
    ),
    ("Claude plugin manifest", re.compile(r"\.claude-plugin/plugin\.json")),
    ("Claude Desktop config", re.compile(r"claude_desktop_config")),
    ("Claude client flag", re.compile(r"--client\s+claude-code\b")),
    ("ToolSearch", re.compile(r"\bToolSearch\b")),
    (
        "web pseudo-call",
        re.compile(
            r"(?:WebSearch|WebFetch|Codex web (?:search|fetch)(?: capability)?)\("
        ),
    ),
)

# Historical or non-operational mentions must be literal and path-scoped.
_MARKDOWN_ALLOWLIST: Mapping[tuple[str, str], tuple[str, ...]] = MappingProxyType({})
_CLAUDE_REFERENCE = re.compile(r"claude|\.claude", re.IGNORECASE)
_ALLOWED_CLAUDE_LINES: Mapping[tuple[str, str], frozenset[str]] = MappingProxyType(
    {
        ("vault-hygiene", "SKILL.md"): frozenset(
            {
                "- After any bulk ingestion (Wispr, OpenAI, Claude Code, NotebookLM, Manus)",
                "- `03_The_Stream/` and each subfolder (`Wispr_Flow/`, `NotebookLM/`, `OpenAI/`, `Claude_Code/`, `Manus/`)",
                "- `source` is one of: `wispr_flow`, `notebooklm`, `openai`, `claude_code`, `manus`, `book`, `synthesis`",
                "Treat historical `~/.claude/projects/-Users-brentbryson-Desktop-vault-personal/memory/` files as read-only evidence; never update or delete them. Record current corrections in the vault's current documentation and indexes.",
            }
        ),
        ("skill-miner", "SKILL.md"): frozenset(
            {
                "2. Use the original `scripts/digest.py` only for deliberate, read-only analysis of historical Claude data. Never use it for current Codex rollouts.",
                "Historical Claude session or library data may be inspected only as read-only input.",
            }
        ),
        ("skill-miner", "REFERENCE.md"): frozenset(
            {
                "Use historical `~/.claude/projects/-Users-brentbryson/*.jsonl` only as read-only evidence with the original `scripts/digest.py`; never use that helper for current Codex rollouts.",
            }
        ),
        ("closing-ritual", "SKILL.md"): frozenset(
            {
                "Treat historical `.claude/sessions/` files as read-only evidence; never write new snapshots there.",
            }
        ),
        ("context-keeper", "SKILL.md"): frozenset(
            {
                "Treat historical `.claude/sessions/` files as read-only evidence; never write new snapshots there.",
            }
        ),
        ("doc-keeper", "SKILL.md"): frozenset(
            {
                "Treat historical `.claude/sessions/` files as read-only evidence; never write new snapshots there.",
            }
        ),
        ("tiger-doc-keeper", "SKILL.md"): frozenset(
            {
                "Treat historical `.claude/sessions/` files as read-only evidence; never write new snapshots there.",
            }
        ),
        ("claude-memory-search", "SKILL.md"): frozenset(
            {
                'name: "claude-memory-search"',
                "# Search Git History with claude-memory",
                "Keep `claude-memory` as the external product name. Use its actual MCP tools when available; otherwise preflight and use the `claude-memory` CLI.",
                "- `claude-memory CLI or MCP`",
            }
        ),
        ("claude-memory-debug", "SKILL.md"): frozenset(
            {
                'name: "claude-memory-debug"',
                "name: claude-memory-debug",
                "# Debug with claude-memory",
                'claude-memory: bug_fix_history("payments")',
                "Keep `claude-memory` as the external product name. Use its actual MCP tools when available; otherwise preflight and use the `claude-memory` CLI.",
                "- `claude-memory CLI or MCP`",
            }
        ),
        ("claude-memory-index", "SKILL.md"): frozenset(
            {
                'name: "claude-memory-index"',
                'description: "Use when the user wants to index a repository into claude-memory, start using claude-memory on a new project, or re-index after significant history. Examples: \\"index the lokumcu repo\\", \\"set up claude memory for this project\\", \\"re-index everything\\""',
                "# Index a Repository with claude-memory",
                "- Starting claude-memory on a new repository for the first time",
                "- Setting up claude-memory for a team member's repo",
                "6. Run claude-memory install to register the MCP server",
                "claude-memory index \\",
                "### Install claude-memory MCP integration",
                "claude-memory install \\",
                "claude-memory index --repo-path . --user-id my-repo-name",
                "claude-memory install --repo-path . --user-id my-repo-name",
                "Keep `claude-memory` as the external product name. Use its actual MCP tools when available; otherwise preflight and use the `claude-memory` CLI.",
                "- `claude-memory CLI or MCP`",
            }
        ),
        ("claude-memory-status", "SKILL.md"): frozenset(
            {
                'name: "claude-memory-status"',
                'description: "Use when the user wants to check what is indexed, how many commits are in memory, or whether claude-memory is set up correctly. Examples: \\"is claude memory set up?\\", \\"how many commits are indexed?\\", \\"check claude memory status\\""',
                "# Check claude-memory Status",
                "- User asks if claude-memory is configured",
                "- [ ] claude-memory MCP server is present in `~/.codex/config.toml`",
                "claude-memory status --repo-path /path/to/repo",
                "from claude_memory import ChromaCommitIndex",
                'python3 -c \'from pathlib import Path; import tomllib; p=Path.home()/".codex/config.toml"; d=tomllib.loads(p.read_text(encoding="utf-8")) if p.is_file() else {}; print("claude-memory configured" if "claude-memory" in d.get("mcp_servers", {}) else "claude-memory not configured")\'',
                "── claude-memory status ──────────────────────────",
                "| `0 commits indexed` | Run `claude-memory index --repo-path .` |",
                "| Wrong user-id | Must match `CLAUDE_MEMORY_USER_ID` in MCP config |",
                "| Chroma path conflict | Ensure `CLAUDE_MEMORY_CHROMA_DIR` is set to `chroma_commits/` (not `chroma/` used by Mem0) |",
                "Keep `claude-memory` as the external product name. Use its actual MCP tools when available; otherwise preflight and use the `claude-memory` CLI.",
                "- `claude-memory CLI or MCP`",
                "- `local claude-memory services`",
            }
        ),
        ("last30days", "SKILL.md"): frozenset(
            {
                "Use the directory containing this loaded `SKILL.md` as `SKILL_DIR`. Confirm `scripts/last30days.py` exists directly beneath it. Do not probe or execute historical Claude plugin/cache installations.",
                '1. **TOPIC**: What they want to learn about (e.g., "web app mockups", "Claude Code skills", "image generation")',
                "Examples: Sam Altman -> @OpenAI, Dario Amodei -> @AnthropicAI, OpenClaw -> @steipete (Peter Steinberger), Paperclip -> @dotta, Claude Code -> @alexalbert__.",
                "| `ai_coding_agent` | Claude Code, Cursor IDE, GitHub Copilot, Windsurf, Aider, Cline, OpenClaw, Hermes Agent, Continue.dev, Codeium, Devin | `ChatGPTCoding, LocalLLaMA, singularity, PromptEngineering` |",
                "| `ai_chat_model` | GPT-5/4, Claude Opus/Sonnet/Haiku, Gemini Pro/Flash, Llama 3/4, DeepSeek, Qwen, Mistral Large, Grok | `LocalLLaMA, ChatGPT, ClaudeAI, singularity, artificial` |",
                '- **Hashtags:** Infer 2-3 from the topic name + category. Examples: "Kanye West" → `kanyewest,ye,bully`. "Claude Code" → `claudecode,aiagent,aicoding`. "Sam Altman" → `samaltman,openai,chatgpt`.',
                "| **Sam Altman vs Dario** | 2 (subreddit + AI CEO news) | `artificial,MachineLearning,OpenAI,ClaudeAI` | `samaltman,openai,anthropic` | (skip - CEOs don't TikTok) | (skip - CEOs don't Reel) | `sam altman interview 2026,dario amodei interview 2026` |",
                '- **Exact product/tool names** mentioned (e.g., if research mentions "ClawdBot" or "@clawdbot", that\'s a DIFFERENT product than "Claude Code" - don\'t conflate them)',
                '**ANTI-PATTERN TO AVOID**: If user asks about "clawdbot skills" and research returns ClawdBot content (self-hosted AI agent), do NOT synthesize this as "Claude Code skills" just because both involve "skills". Read what the research actually says.',
                "**NEVER write a title line at the top of your response.** No `Kanye West: last 30 days`, no `Claude Opus 4.7 - what people are actually saying`, no `{Topic} news`. Your response begins with the MANDATORY badge on line 1, one blank line, then the prose label `What I learned:` on line 3, and goes straight into the narrative.",
            }
        ),
        ("skills-librarian", "SKILL.md"): frozenset(
            {
                "   `AGENTS-CATALOG.md`. **Mirror repo:** `bbrysonelite-max/claude-skills` (private).",
                "Historical Claude session or library data may be inspected only as read-only input.",
            }
        ),
    }
)

_LAST30DAYS_CODEX_INSTALL = (
    "# STEP 0: CODEX INSTALL SELF-CHECK\n\n"
    "Use the directory containing this loaded `SKILL.md` as `SKILL_DIR`. Confirm "
    "`scripts/last30days.py` exists directly beneath it. Do not probe or execute "
    "historical Claude plugin/cache installations.\n\n---\n"
)
_LAST30DAYS_WEB_PREFLIGHT = (
    "**STEP 0 - PREFLIGHT CODEX WEB RESEARCH.** Confirm the current runtime exposes "
    "Codex web search (the `web.run` capability) before planning supplemental research. "
    "No deferred-tool selection call is needed. If web search is unavailable, use the "
    "engine's documented `--auto-resolve` fallback and report that limitation.\n"
)
_MEMORY_STATUS_CONFIG_CHECK = (
    "### Check Codex MCP config (read-only)\n"
    "Read `~/.codex/config.toml` with Python 3.11's TOML parser and report only whether "
    "the server entry exists; never print its configuration values.\n"
    "```bash\n"
    "python3 -c 'from pathlib import Path; import tomllib; "
    "p=Path.home()/\".codex/config.toml\"; "
    "d=tomllib.loads(p.read_text(encoding=\"utf-8\")) if p.is_file() else {}; "
    "print(\"claude-memory configured\" if \"claude-memory\" in "
    "d.get(\"mcp_servers\", {}) else \"claude-memory not configured\")'\n"
    "```\n"
)

_SOURCE_REWRITES: Mapping[tuple[str, str], tuple[ExpectedRewrite, ...]] = {
    ("context-keeper", "DESCRIPTION"): (
        ExpectedRewrite(
            re.compile(r"\.claude/sessions/"), 1, ".codex/sessions/"
        ),
    ),
    ("context-keeper", "SKILL.md"): (
        ExpectedRewrite(re.compile(r"\.claude/sessions"), 5, ".codex/sessions"),
        ExpectedRewrite(
            re.compile(re.escape("AGENTS.md/CLAUDE.md/SACRED_WIRING.md")),
            1,
            "AGENTS.md/SACRED_WIRING.md",
        ),
    ),
    ("closing-ritual", "SKILL.md"): (
        ExpectedRewrite(re.compile(r"\.claude/sessions"), 1, ".codex/sessions"),
        ExpectedRewrite(
            re.compile(re.escape("CLAUDE.md / AGENTS.md / GROUND_TRUTH-style")),
            1,
            "AGENTS.md / GROUND_TRUTH-style",
        ),
        ExpectedRewrite(
            re.compile(r"\bTodoWrite\b"), 1, "Codex task checklist"
        ),
    ),
    ("doc-keeper", "SKILL.md"): (
        ExpectedRewrite(re.compile(r"\.claude/sessions"), 2, ".codex/sessions"),
        ExpectedRewrite(re.compile(r"Agent\("), 1),
        ExpectedRewrite(
            re.compile(re.escape("`CLAUDE.md`, `AGENTS.md`, ")),
            1,
            "`AGENTS.md`, ",
        ),
    ),
    ("tiger-doc-keeper", "SKILL.md"): (
        ExpectedRewrite(re.compile(r"\.claude/sessions"), 2, ".codex/sessions"),
        ExpectedRewrite(re.compile(r"Agent\("), 1),
        ExpectedRewrite(
            re.compile(re.escape("AGENTS.md, RULES.md, CLAUDE.md, SACRED_WIRING.md")),
            1,
            "AGENTS.md, RULES.md, SACRED_WIRING.md",
        ),
    ),
    ("page-rethink", "SKILL.md"): (
        ExpectedRewrite(
            re.compile(r"(?m)^- \*\*Live page\*\*:.*Use the gstack browse binary:.*$"),
            1,
            (
                "- **Live page**: use the installed `browser-use:browser` or "
                "`vercel:agent-browser` skill to open the URL, inspect rendered text, "
                "and capture viewport screenshots."
            ),
        ),
    ),
    ("skill-miner", "SKILL.md"): (
        ExpectedRewrite(
            re.compile(re.escape("~/.claude/skills")), 1, "~/.codex/skills"
        ),
        ExpectedRewrite(
            re.compile(
                r"(?ms)^1\. \*\*Digest\*\* the transcripts into analyzable batches:.*?"
                r"^2\. \*\*Establish what already exists\*\*"
            ),
            1,
            (
                "1. **Digest** current Codex rollouts and context-keeper snapshots into "
                "analyzable batches:\n"
                "   `python3 scripts/digest_codex.py --batches 3 --dir "
                "~/.codex/sessions --context-dir <project-root>/.codex/sessions`\n"
                "   Writes `digest.txt` + `batch1..3.txt` from user/assistant messages "
                "and explicit project-local context snapshots while excluding tool "
                "payloads. Repeat `--context-dir` for approved additional projects. Add "
                "`--limit N` to mine only the N most recent valid session files across "
                "all roots. Use the original "
                "`scripts/digest.py` only for deliberate read-only analysis of historical "
                "assistant transcripts.\n"
                "2. **Establish what already exists**"
            ),
        ),
        ExpectedRewrite(
            re.compile(
                r"(?ms)^3\. \*\*Fan out 3 analyst subagents\*\*.*?"
                r"^4\. \*\*Synthesize\*\*"
            ),
            1,
            (
                "3. **Analyze each batch** directly in the main Codex agent using the "
                "prompt template in [REFERENCE.md](REFERENCE.md). Delegation is optional "
                "only when the active environment permits it; the workflow must remain "
                "valid without delegation.\n"
                "4. **Synthesize**"
            ),
        ),
        ExpectedRewrite(
            re.compile(
                re.escape(
                    "**Bounded cost.** One sweep per run, ~3 analyst agents. Not an "
                    "iterate-to-dry loop."
                )
            ),
            1,
            (
                "**Bounded cost.** One sweep per run over three batches. Analyze them "
                "directly, or delegate selectively when permitted."
            ),
        ),
        ExpectedRewrite(
            re.compile(
                re.escape(
                    "python3 scripts/digest.py --batches 3   # then fan out 3 analysts "
                    "over batch1..3.txt (see REFERENCE.md)"
                )
            ),
            1,
            (
                "python3 scripts/digest_codex.py --batches 3 --dir ~/.codex/sessions "
                "--context-dir <project-root>/.codex/sessions  # analyze batches "
                "directly (see REFERENCE.md)"
            ),
        ),
    ),
    ("skill-miner", "BACKLOG.md"): (
        ExpectedRewrite(
            re.compile(re.escape("SOTU/NEXT_SESSION/CLAUDE/AGENTS")),
            1,
            "SOTU/NEXT_SESSION/AGENTS/project docs",
        ),
    ),
    ("skill-miner", "DESCRIPTION"): (
        ExpectedRewrite(
            re.compile(re.escape("past Claude Code session transcripts")),
            1,
            "past Codex session rollouts and context snapshots",
        ),
    ),
    ("skill-miner", "REFERENCE.md"): (
        ExpectedRewrite(
            re.compile(re.escape("~/.claude/skills")), 1, "~/.codex/skills"
        ),
        ExpectedRewrite(
            re.compile(
                r"(?ms)^## Analyst subagent prompt \(one per batch\)\n\n"
                r"Dispatch 3 `general-purpose` agents in a single message \(parallel\)\."
            ),
            1,
            (
                "## Batch analysis prompt\n\n"
                "Analyze each batch directly in the main Codex agent. Delegation is "
                "optional only when the active environment permits it."
            ),
        ),
        ExpectedRewrite(
            re.compile(re.escape("past Claude Code sessions")),
            1,
            "past Codex sessions",
        ),
        ExpectedRewrite(
            re.compile(r"(?ms)^## Digest internals\n.*\Z"),
            1,
            (
                "## Digest internals\n\n"
                "`scripts/digest_codex.py --dir ~/.codex/sessions` recursively reads "
                "current rollout JSONL. Pass each relevant project-local "
                "`.codex/sessions` directory with repeatable `--context-dir PATH` to "
                "include context-keeper Markdown snapshots; do not assume those snapshots "
                "are in the global rollout directory. The helper deduplicates candidates, "
                "then applies `--limit N` and deterministic ordering across valid rollouts "
                "and snapshots together. It keeps only user/assistant textual messages, "
                "excludes tool, reasoning, encrypted, and developer payloads, redacts "
                "credential-shaped values, and emits deterministic `digest.txt` plus "
                "optional `batchK.txt` files.\n\n"
                "Use historical `~/.claude/projects/-Users-brentbryson/*.jsonl` only as "
                "read-only evidence with the original `scripts/digest.py`; never use that "
                "helper for current Codex rollouts.\n"
            ),
        ),
    ),
    ("skills-librarian", "SKILL.md"): (
        ExpectedRewrite(
            re.compile(re.escape("~/.claude/skills")), 3, "~/.codex/skills"
        ),
        ExpectedRewrite(
            re.compile(re.escape("source of truth Claude Code loads from")),
            1,
            "source of truth Codex loads from",
        ),
        ExpectedRewrite(
            re.compile(
                re.escape("live dir IS the work tree Claude loads from")
            ),
            1,
            "live dir IS the work tree Codex loads from",
        ),
        ExpectedRewrite(
            re.compile(re.escape("~/.claude/agents/")), 1, "~/.agents/"
        ),
    ),
    ("skills-librarian", "DESCRIPTION"): (
        ExpectedRewrite(
            re.compile(re.escape("~/.claude/skills")), 1, "~/.codex/skills"
        ),
    ),
    ("two-brents-brand", "SKILL.md"): (
        ExpectedRewrite(
            re.compile(re.escape("In Brent's ~/.claude/skills stack")),
            1,
            "In Brent's ~/.codex/skills stack",
        ),
    ),
    ("doc-keeper", "DESCRIPTION"): (
        ExpectedRewrite(
            re.compile(re.escape("Dispatches the doc-keeper subagent, which")),
            1,
            "Runs the doc-keeper workflow directly; it",
        ),
    ),
    ("tiger-doc-keeper", "DESCRIPTION"): (
        ExpectedRewrite(
            re.compile(re.escape("Dispatches the tiger-doc-keeper subagent to")),
            1,
            "Runs the tiger-doc-keeper workflow directly to",
        ),
    ),
    ("allsup-leads-ssdi", "SKILL.md"): (
        ExpectedRewrite(
            re.compile(re.escape("~/.claude/skills/")), 2, "~/.codex/skills/"
        ),
        ExpectedRewrite(
            re.compile(re.escape("--client claude-code")), 1, "--client codex"
        ),
    ),
    ("allsup-leads-veterans", "SKILL.md"): (
        ExpectedRewrite(
            re.compile(re.escape("~/.claude/skills/")), 2, "~/.codex/skills/"
        ),
        ExpectedRewrite(
            re.compile(re.escape("--client claude-code")), 1, "--client codex"
        ),
    ),
    ("tiger-leader-hunt", "SKILL.md"): (
        ExpectedRewrite(
            re.compile(re.escape("$HOME/.claude/skills/")),
            2,
            "$HOME/.codex/skills/",
        ),
    ),
    ("truth-keeper", "SKILL.md"): (
        ExpectedRewrite(
            re.compile(re.escape("~/.claude/skills/")), 1, "~/.codex/skills/"
        ),
        ExpectedRewrite(
            re.compile(r"\bTodoWrite\b"), 1, "Codex task checklist"
        ),
    ),
    ("signal-mine", "SKILL.md"): (
        ExpectedRewrite(
            re.compile(r"\bWebSearch\b"), 2, "Codex web search"
        ),
    ),
    ("signal-mine", "verticals/ssdi-work-fear.md"): (
        ExpectedRewrite(
            re.compile(re.escape("WebSearch/Serper")),
            1,
            "Codex web research or Serper",
        ),
    ),
    ("whitelabel-radar", "SKILL.md"): (
        ExpectedRewrite(
            re.compile(r"\bWebSearch\b"), 1, "Codex web search"
        ),
    ),
    ("vault-hygiene", "SKILL.md"): (
        ExpectedRewrite(
            re.compile(re.escape("`SPEC.md` > `CLAUDE.md` > everything else")),
            1,
            "`SPEC.md` > `AGENTS.md` > everything else",
        ),
        ExpectedRewrite(
            re.compile(re.escape("`index.md`, `CLAUDE.md`, `SPEC.md`")),
            1,
            "`index.md`, `AGENTS.md`, `SPEC.md`",
        ),
        ExpectedRewrite(
            re.compile(re.escape("`SPEC.md` vs `CLAUDE.md`")),
            1,
            "`SPEC.md` vs `AGENTS.md`",
        ),
        ExpectedRewrite(
            re.compile(re.escape("SPEC.md and CLAUDE.md disagree")),
            1,
            "SPEC.md and AGENTS.md disagree",
        ),
        ExpectedRewrite(
            re.compile(re.escape("update CLAUDE.md if they disagree")),
            1,
            "update AGENTS.md if they disagree",
        ),
        ExpectedRewrite(
            re.compile(re.escape("update CLAUDE.md to match SPEC.md")),
            1,
            "update AGENTS.md to match SPEC.md",
        ),
        ExpectedRewrite(
            re.compile(
                r"(?ms)^### Phase 5: Memory Staleness Audit\n.*?"
                r"^### Phase 6: Context Drift Detection$"
            ),
            1,
            (
                "### Phase 5: Memory Staleness Audit\n\n"
                "Inspect current Codex session and project documentation for stale state.\n\n"
                "Treat historical "
                "`~/.claude/projects/-Users-brentbryson-Desktop-vault-personal/memory/` "
                "files as read-only evidence; never update or delete them. Record current "
                "corrections in the vault's current documentation and indexes.\n\n"
                "### Phase 6: Context Drift Detection"
            ),
        ),
    ),
    ("the-rebuild", "REFERENCE.md"): (
        ExpectedRewrite(
            re.compile(re.escape("~/.claude/skills/signal-mine/")),
            1,
            "~/.codex/skills/signal-mine/",
        ),
    ),
    ("claude-memory-index", "SKILL.md"): (
        ExpectedRewrite(
            re.compile(re.escape("python scripts/claude_memory_indexer.py")),
            2,
            "claude-memory index",
        ),
        ExpectedRewrite(
            re.compile(re.escape("~/.claude/claude_desktop_config.json")),
            1,
            "~/.codex/config.toml",
        ),
        ExpectedRewrite(
            re.compile(re.escape("restart Claude Code")),
            1,
            "restart the active Codex session",
        ),
        ExpectedRewrite(
            re.compile(re.escape("Install Claude Code plugin")),
            1,
            "Install claude-memory MCP integration",
        ),
    ),
    ("claude-memory-status", "SKILL.md"): (
        ExpectedRewrite(re.compile(r"claude_desktop_config\.json"), 3),
        ExpectedRewrite(
            re.compile(
                re.escape(
                    "2. Check if MCP server is configured in "
                    "~/.claude/claude_desktop_config.json"
                )
            ),
            1,
            "2. Check read-only whether the MCP server is configured in "
            "~/.codex/config.toml",
        ),
        ExpectedRewrite(
            re.compile(
                re.escape(
                    "- [ ] claude-memory MCP server is in claude_desktop_config.json"
                )
            ),
            1,
            "- [ ] claude-memory MCP server is present in `~/.codex/config.toml`",
        ),
        ExpectedRewrite(
            re.compile(
                r"(?ms)^### Check MCP config\n```bash\ncat "
                r"~/\.claude/claude_desktop_config\.json \| python3 -m json\.tool "
                r"\| grep -A8 \"claude-memory\"\n```\n"
            ),
            1,
            _MEMORY_STATUS_CONFIG_CHECK,
        ),
    ),
    ("gitnexus-cli", "SKILL.md"): (
        ExpectedRewrite(
            re.compile(re.escape("generates CLAUDE.md / AGENTS.md context files")),
            1,
            "generates AGENTS.md context files",
        ),
        ExpectedRewrite(
            re.compile(re.escape("Restart Claude Code")),
            1,
            "Restart the active Codex session",
        ),
        ExpectedRewrite(
            re.compile(
                re.escape(
                    "In Claude Code, a PostToolUse hook detects staleness after `git "
                    "commit` and `git merge` and notifies the agent to run `analyze`"
                )
            ),
            1,
            "In Codex, check staleness explicitly after `git commit` and `git merge` "
            "and run `analyze` when needed",
        ),
    ),
    ("last30days", "SKILL.md"): (
        ExpectedRewrite(
            re.compile(
                re.escape(
                    "(Claude Code, Codex, Hermes, Gemini, or any agent runtime"
                )
            ),
            1,
            "(Codex, Hermes, Gemini, or any agent runtime",
        ),
        ExpectedRewrite(
            re.compile(re.escape("Claude Code renders `[text](url)`")),
            1,
            "The current Markdown renderer displays `[text](url)`",
        ),
        ExpectedRewrite(
            re.compile(re.escape("platform detection (OpenClaw vs Claude Code)")),
            1,
            "current runtime detection",
        ),
        ExpectedRewrite(
            re.compile(re.escape("$HOME/.claude/plugins/cache/")), 3
        ),
        ExpectedRewrite(re.compile(r"\.claude-plugin/plugin\.json"), 1),
        ExpectedRewrite(re.compile(r"ToolSearch"), 2),
        ExpectedRewrite(re.compile(r"(?m)^WebSearch\((\".*\")\)$"), 11),
        ExpectedRewrite(re.compile(r"\bWebSearches\b"), 7),
        ExpectedRewrite(re.compile(r"\bWebSearch\b"), 85),
        ExpectedRewrite(
            re.compile(r"\bAskUserQuestion\b"), 2, "Codex user-input request"
        ),
        ExpectedRewrite(
            re.compile(r"\bRead tool\b"), 3, "file-reading capability"
        ),
        ExpectedRewrite(
            re.compile(
                r"(?ms)^# STEP 0: STALE-CLONE SELF-CHECK.*?^---\n"
            ),
            1,
            _LAST30DAYS_CODEX_INSTALL,
        ),
        ExpectedRewrite(
            re.compile(
                r"(?ms)^\*\*STEP 0 - LOAD WEBSEARCH FIRST\.\*\*.*?"
                r"^Load WebSearch first\. No exceptions\. Then proceed to the "
                r"branching rule below\.\n"
            ),
            1,
            _LAST30DAYS_WEB_PREFLIGHT,
        ),
        ExpectedRewrite(
            re.compile(
                r"(?m)^Replace `\{VERSION\}` with the installed plugin version .*"
                r"then the synthesis begins\.$"
            ),
            1,
            (
                "Pass through the badge emitted by the engine. If the engine reports "
                "`v?`, state that the installed version is unavailable instead of "
                "probing plugin metadata. Use today's date for `{YYYY-MM-DD}` only when "
                "a manual fallback badge is unavoidable."
            ),
        ),
        ExpectedRewrite(
            re.compile(
                re.escape(
                    "**MANDATORY on Claude Code (and any platform with WebSearch).**"
                )
            ),
            1,
            "**MANDATORY in Codex whenever web search is available.**",
        ),
        ExpectedRewrite(
            re.compile(
                re.escape(
                    "1. **Platform branch chosen.** You know whether this session has "
                    "WebSearch (Claude Code) or does not (OpenClaw, raw CLI, Codex "
                    "without web tools)."
                )
            ),
            1,
            "1. **Platform branch chosen.** Determine whether the current Codex "
            "session has web search; if it does not, use the documented no-web "
            "fallback.",
        ),
        ExpectedRewrite(
            re.compile(
                r"(?m)^#   Read ~/\.claude/skills/last30days/SKILL\.md.*\n"
            ),
            2,
            "",
        ),
        ExpectedRewrite(
            re.compile(
                r"(?m)^#   Read ~/\.claude/plugins/cache/.*\n#     .*\n"
            ),
            2,
            "",
        ),
        ExpectedRewrite(
            re.compile(r"(?m)^WebSearch\((\".*\")\)$"),
            11,
            r"Codex web search query: \1",
        ),
        ExpectedRewrite(re.compile(r"\bWebSearches\b"), 7, "web searches"),
        ExpectedRewrite(re.compile(r"\bWebSearch\b"), 85, "Codex web search"),
    ),
    ("last30days", "references/save-html-brief.md"): (
        ExpectedRewrite(
            re.compile(
                re.escape(
                    'SYNTHESIS_FILE="/tmp/last30days-synthesis-${CLAUDE_SESSION_ID}.md"'
                )
            ),
            1,
            'SYNTHESIS_FILE="/tmp/last30days-synthesis-$$.md"',
        ),
    ),
    ("ship-it", "SKILL.md"): (
        ExpectedRewrite(
            re.compile(re.escape("from AGENTS.md / CLAUDE.md")),
            1,
            "from AGENTS.md and repository instructions",
        ),
    ),
    ("here-now", "references/REFERENCE.md"): (
        ExpectedRewrite(
            re.compile(re.escape("X-HereNow-Client: claude-code/publish-sh")),
            1,
            "X-HereNow-Client: codex/publish-sh",
        ),
    ),
}


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


def _normalize_newlines(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def _restore_newlines(text: str, newline: str) -> str:
    normalized = _normalize_newlines(text)
    return normalized if newline == "\n" else normalized.replace("\n", newline)


def validate_generated_markdown(
    skill_name: str, relative_path: str, text: str
) -> None:
    """Reject Claude-only operational instructions in generated Markdown."""
    normalized_path = str(relative_path).replace("\\", "/")
    candidate = _normalize_newlines(text)
    allowed_claude_lines = _ALLOWED_CLAUDE_LINES.get(
        (skill_name, normalized_path), frozenset()
    )
    for line_number, line in enumerate(candidate.splitlines(), start=1):
        if _CLAUDE_REFERENCE.search(line) and line not in allowed_claude_lines:
            raise ValueError(
                f"{skill_name}/{normalized_path}:{line_number}: prohibited Markdown "
                "Claude "
                "runtime/client/environment reference outside the exact path-scoped "
                f"allowlist: {line!r}"
            )
    for allowed_text in _MARKDOWN_ALLOWLIST.get(
        (skill_name, normalized_path), ()
    ):
        candidate = candidate.replace(_normalize_newlines(allowed_text), "")
    for label, pattern in _PROHIBITED_MARKDOWN_PATTERNS:
        match = pattern.search(candidate)
        if match is not None:
            raise ValueError(
                f"{skill_name}/{normalized_path}: prohibited Markdown pattern "
                f"{label!r}: {match.group(0)!r}"
            )


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


def _apply_source_rewrites(
    skill_name: str, text: str, relative_path: str, *, strict: bool
) -> str:
    rewrites = _SOURCE_REWRITES.get((skill_name, relative_path), ())
    if strict:
        for rewrite in rewrites:
            count = len(rewrite.pattern.findall(text))
            if count != rewrite.expected:
                raise ValueError(
                    f"{skill_name}: expected {rewrite.expected} occurrence(s) of "
                    f"{rewrite.pattern.pattern!r}, found {count}; source adapter drifted"
                )
    for rewrite in rewrites:
        if rewrite.replacement is not None:
            text = rewrite.pattern.sub(rewrite.replacement, text)
    return text


def _adapt_named_text(
    skill_name: str, text: str, relative_path: str, *, strict: bool, newline: str
) -> str:
    text = _apply_source_rewrites(
        skill_name, text, relative_path, strict=strict
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

    if not strict:
        if skill_name in _SESSION_SKILLS:
            text = text.replace(".claude/sessions", ".codex/sessions")
        if skill_name in _LIBRARY_SKILLS or skill_name in _CROSS_SKILL_PATHS:
            text = text.replace("~/.claude/skills/", "~/.codex/skills/")
            text = text.replace("~/.claude/skills", "~/.codex/skills")
        if skill_name in _CLAUDE_MEMORY_SKILLS:
            text = text.replace(
                "~/.claude/claude_desktop_config.json", "~/.codex/config.toml"
            )
            text = text.replace(
                "restart Claude Code", "restart the active Codex session"
            )
            text = text.replace(
                "Install Claude Code plugin",
                "Install claude-memory MCP integration",
            )
        if skill_name in _GITNEXUS_SKILLS:
            text = text.replace(
                "Restart Claude Code", "Restart the active Codex session"
            )
            text = text.replace(
                "In Claude Code, a PostToolUse hook detects staleness after `git commit` "
                "and `git merge` and notifies the agent to run `analyze`",
                "In Codex, check staleness explicitly after `git commit` and `git merge` "
                "and run `analyze` when needed",
            )
        # Installation paths are runtime coupling, not product names.
        text = text.replace("$HOME/.claude/skills/", "$HOME/.codex/skills/")
        text = text.replace("~/.claude/skills/", "~/.codex/skills/")
        safe_boundary_rewrites = (
            (re.compile(r"\bAskUserQuestion\b"), "Codex user-input request"),
            (re.compile(r"\bTodoWrite\b"), "Codex task checklist"),
            (re.compile(r"\bBash tool\b"), "shell execution capability"),
            (re.compile(r"\bRead tool\b"), "file-reading capability"),
            (re.compile(r"\bWrite tool\b"), "file-editing capability"),
            (re.compile(r"\bWebFetch\b"), "Codex web fetch"),
            (re.compile(r"\bWebSearch\b"), "Codex web search"),
            (re.compile(r"\bAgent tool\b"), "optional delegation capability"),
            (re.compile(r"\bTask tool\b"), "optional delegated-task capability"),
            (re.compile(r"Task\("), "optional delegated task ("),
            (re.compile(r"Agent\("), "optional delegation ("),
        )
        for pattern, replacement in safe_boundary_rewrites:
            text = pattern.sub(replacement, text)
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
                "Run `python3 scripts/digest_codex.py --batches 3` with "
                "`--dir ~/.codex/sessions` for current rollout JSONL and repeatable "
                "`--context-dir <project-root>/.codex/sessions` arguments for explicit "
                "project-local context snapshots. Use the original copied "
                "`scripts/digest.py` only for deliberate read-only analysis of historical "
                "assistant transcripts."
            )
        if skill_name == "skills-librarian":
            details.extend(
                (
                    "Set `SKILLS_DIR=~/.codex/skills` when invoking copied audit or "
                    "backup helpers so their preserved source defaults cannot select a "
                    "legacy shelf.",
                    "Set `AGENTS_DIR=~/.agents` for current Codex agent definitions.",
                    "Set `AGENTS_SRC=~/.agents` when invoking the copied backup helper "
                    "so it mirrors those definitions.",
                )
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
            "`~/.codex/skills`) or the current collection; do not assume a legacy skill root."
        )
    return details


def _append_runtime(
    skill_name: str, text: str, spec: AdapterSpec, newline: str
) -> str:
    lines = ["## Codex Runtime", ""]
    lines.extend(_runtime_details(skill_name))
    if lines[-1] != "":
        lines.append("")
    lines.extend(
        (
            "Never expose or print secret, credential, or token values.",
            "",
        )
    )
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
    normalized_text = _normalize_newlines(text)
    adapted = _adapt_named_text(
        skill_name,
        normalized_text,
        normalized_path,
        strict=entry is not None,
        newline="\n",
    )
    if normalized_path == "SKILL.md":
        adapted = _append_runtime(skill_name, adapted, spec, "\n")
    else:
        adapted = re.sub(r"[ \t]+(?=$)", "", adapted, flags=re.MULTILINE)
    if entry is not None:
        validate_generated_markdown(skill_name, normalized_path, adapted)
    return _restore_newlines(adapted, newline)


def _normalize_codex_description(description: str) -> str:
    return re.sub(r"<([A-Za-z][A-Za-z0-9 _#-]*)>", r"{\1}", description)


def adapt_description(skill_name: str, description: str, *, entry: Any = None) -> str:
    """Normalize only runtime claims that would be false in a Codex copy."""
    try:
        spec = ADAPTER_REGISTRY[skill_name]
    except KeyError:
        raise KeyError(f"unknown Codex adapter: {skill_name}") from None
    _validate_entry(skill_name, spec, entry)
    if spec.conversion == "native":
        return _normalize_codex_description(description)

    newline = _newline_style(description)
    normalized_description = _normalize_newlines(description)
    adapted = _apply_source_rewrites(
        skill_name,
        normalized_description,
        "DESCRIPTION",
        strict=entry is not None,
    )
    if entry is None:
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
    adapted = _normalize_codex_description(adapted)
    return _restore_newlines(adapted, newline)
