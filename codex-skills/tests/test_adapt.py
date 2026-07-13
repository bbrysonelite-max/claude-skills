import re
import stat
import tempfile
import unittest
from collections import Counter
from pathlib import Path

from scripts.adapt import ADAPTER_REGISTRY, adapt_description, adapt_text
from scripts.build import build_collection
from scripts.common import (
    Manifest,
    hash_protected_sources,
    load_manifest,
    parse_skill_document,
)


CODEX_SKILLS_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = CODEX_SKILLS_ROOT.parent
MANIFEST_PATH = CODEX_SKILLS_ROOT / "manifest.yaml"


def source_text(name: str, relative_path: str = "SKILL.md") -> str:
    with (REPOSITORY_ROOT / name / relative_path).open(
        "r", encoding="utf-8", newline=""
    ) as source_file:
        return source_file.read()


def source_body(name: str) -> str:
    return parse_skill_document(source_text(name)).body


class AdapterContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = load_manifest(MANIFEST_PATH, repo_root=REPOSITORY_ROOT)
        cls.entries = {entry.source: entry for entry in cls.manifest.sources}

    def adapt_source(self, name: str, relative_path: str = "SKILL.md") -> str:
        text = source_body(name) if relative_path == "SKILL.md" else source_text(
            name, relative_path
        )
        return adapt_text(
            name,
            text,
            relative_path=relative_path,
            entry=self.entries[name],
        )

    def test_registry_matches_all_manifest_sources_and_metadata(self):
        self.assertEqual(
            {entry.source for entry in self.manifest.sources},
            set(ADAPTER_REGISTRY),
        )
        for entry in self.manifest.sources:
            with self.subTest(skill=entry.source):
                adapter = ADAPTER_REGISTRY[entry.source]
                self.assertEqual(entry.conversion, adapter.conversion)
                self.assertEqual(entry.dependencies, adapter.dependencies)

    def test_unknown_adapter_is_rejected(self):
        with self.assertRaises(KeyError):
            adapt_text("not-in-manifest", "text")

    def test_native_adapter_is_an_exact_identity(self):
        text = "Claude Code and ~/.claude/skills/ remain source text.\r\n"

        self.assertEqual(text, adapt_text("ground-truth", text))

    def test_description_normalizes_only_impossible_runtime_claims(self):
        context_description = self.entries["context-keeper"].notes + (
            " Use when the user says save the session to .claude/sessions/."
        )

        adapted = adapt_description("context-keeper", context_description)

        self.assertIn("Use when the user says save the session", adapted)
        self.assertIn(".codex/sessions/", adapted)
        self.assertNotIn(".claude/sessions/", adapted)
        self.assertEqual(
            "Claude remains a name.",
            adapt_description("ground-truth", "Claude remains a name."),
        )

        actual_description = parse_skill_document(
            source_text("context-keeper")
        ).description
        drifted = actual_description.replace(
            ".claude/sessions/", ".unexpected/sessions/", 1
        )
        with self.assertRaisesRegex(ValueError, "context-keeper.*expected.*1"):
            adapt_description(
                "context-keeper",
                drifted,
                entry=self.entries["context-keeper"],
            )

    def test_context_keeper_writes_codex_sessions_and_marks_legacy_read_only(self):
        result = self.adapt_source("context-keeper")

        self.assertIn(".codex/sessions/", result)
        self.assertIn("historical `.claude/sessions/`", result)
        self.assertIn("read-only evidence", result)
        self.assertIn("set `CONTEXT_KEEPER_DIR`", result)

    def test_claude_memory_product_name_and_unrelated_claude_text_are_preserved(self):
        source = source_text("claude-memory-search") + "\nClaude is a proper name here.\n"

        result = adapt_text(
            "claude-memory-search",
            source,
            entry=self.entries["claude-memory-search"],
        )

        self.assertIn("claude-memory", result)
        self.assertIn("Claude is a proper name here.", result)

    def test_unvalidated_snippet_does_not_trigger_known_source_count_checks(self):
        result = adapt_text("page-rethink", "Claude is a proper name here.\n")

        self.assertIn("Claude is a proper name here.", result)
        self.assertIn("## Codex Runtime", result)

    def test_page_rethink_uses_an_installed_browser_skill(self):
        result = self.adapt_source("page-rethink")

        self.assertNotIn("$HOME/.claude/skills/gstack", result)
        self.assertIn("browser-use:browser", result)
        self.assertIn("vercel:agent-browser", result)

    def test_google_workflows_are_connector_first_with_gws_fallback(self):
        result = self.adapt_source("gws-shared")

        connector_position = result.index("connected Gmail/Google Drive app tools")
        fallback_position = result.index("`gws` CLI fallback")
        self.assertLess(connector_position, fallback_position)
        self.assertIn("confirm", result.lower())
        self.assertIn("Never expose credentials or tokens", result)

    def test_doc_keeper_runs_directly_without_a_mandatory_agent_call(self):
        result = self.adapt_source("doc-keeper")

        self.assertNotIn("Agent(", result)
        self.assertNotIn("Dispatch the `doc-keeper` agent", result)
        self.assertNotIn("This skill dispatches", result)
        self.assertIn("Perform this workflow directly in the main Codex agent", result)
        self.assertIn("Delegation is optional", result)

    def test_cross_skill_paths_resolve_from_codex_skill_roots(self):
        result = self.adapt_source("allsup-leads-ssdi")

        self.assertNotIn("~/.claude/skills/", result)
        self.assertIn("~/.codex/skills", result)
        self.assertIn("current collection", result)

    def test_library_helpers_receive_explicit_codex_roots(self):
        miner = self.adapt_source("skill-miner")
        librarian = self.adapt_source("skills-librarian")

        self.assertIn("`--dir ~/.codex/sessions`", miner)
        self.assertIn("`SKILLS_DIR=~/.codex/skills`", librarian)

    def test_the_rebuild_reference_resource_is_adapted(self):
        result = self.adapt_source("the-rebuild", "REFERENCE.md")

        self.assertNotIn("~/.claude/skills/signal-mine", result)
        self.assertIn("~/.codex/skills/signal-mine", result)
        self.assertNotIn("## Codex Runtime", result)

    def test_dependency_runtime_lists_exact_names_and_blocked_response(self):
        entry = self.entries["claude-memory-debug"]
        result = adapt_text(
            "claude-memory-debug",
            source_text("claude-memory-debug"),
            entry=entry,
        )

        for dependency in entry.dependencies:
            self.assertIn(f"- `{dependency}`", result)
        self.assertIn("CLI availability/version checks", result)
        self.assertIn("without printing secrets", result)
        self.assertIn("concise blocked state", result)

    def test_expected_source_pattern_drift_fails_visibly(self):
        source = source_body("page-rethink").replace(
            "Use the gstack browse binary:", "Use an unspecified browser:"
        )

        with self.assertRaisesRegex(ValueError, "page-rethink.*expected.*1"):
            adapt_text(
                "page-rethink",
                source,
                entry=self.entries["page-rethink"],
            )

    def test_context_keeper_full_source_count_drift_fails_visibly(self):
        source = source_body("context-keeper").replace(
            ".claude/sessions", ".unexpected/sessions", 1
        )

        with self.assertRaisesRegex(ValueError, "context-keeper.*expected.*5"):
            adapt_text(
                "context-keeper",
                source,
                entry=self.entries["context-keeper"],
            )

    def test_truth_keeper_skill_path_is_an_expected_source_contract(self):
        drifted = source_body("truth-keeper").replace(
            "~/.claude/skills/", "~/.unexpected/skills/", 1
        )

        with self.assertRaisesRegex(ValueError, "truth-keeper.*expected.*1"):
            adapt_text(
                "truth-keeper",
                drifted,
                entry=self.entries["truth-keeper"],
            )

    def test_last30days_has_strict_codex_web_and_install_path_adaptation(self):
        result = self.adapt_source("last30days")

        for prohibited in (
            "$HOME/.claude/plugins/cache/",
            "~/.claude/plugins/cache/",
            ".claude-plugin/plugin.json",
            "ToolSearch",
            "WebSearch(",
            "WebFetch(",
            "Codex web search capability(",
        ):
            with self.subTest(prohibited=prohibited):
                self.assertNotIn(prohibited, result)
        self.assertIn('Codex web search query: "{TOPIC} X twitter handle', result)
        self.assertIn("Run 2-3 focused web searches", result)
        self.assertIn("If the engine reports `v?`", result)
        self.assertNotIn("`version:` value in the loaded", result)
        self.assertNotIn("MANDATORY on Claude Code", result)
        self.assertNotIn("Codex web search (Claude Code)", result)
        self.assertNotIn("capabilityes", result)

        drifted = source_body("last30days").replace(
            "$HOME/.claude/plugins/cache/", "$HOME/.changed/plugins/cache/", 1
        )
        with self.assertRaisesRegex(ValueError, "last30days.*drift"):
            adapt_text(
                "last30days",
                drifted,
                entry=self.entries["last30days"],
            )

    def test_claude_memory_status_uses_toml_aware_codex_config_check(self):
        result = self.adapt_source("claude-memory-status")

        self.assertIn("~/.codex/config.toml", result)
        self.assertIn("import tomllib", result)
        self.assertIn("mcp_servers", result)
        self.assertNotIn("claude_desktop_config", result)
        self.assertNotIn("json.tool", result)
        self.assertIn("read-only", result)

    def test_named_library_and_brand_placement_wording_is_codex_native(self):
        librarian = self.adapt_source("skills-librarian")
        brand = self.adapt_source("two-brents-brand")
        miner_reference = self.adapt_source("skill-miner", "REFERENCE.md")
        vault = self.adapt_source("vault-hygiene")

        self.assertIn("source of truth Codex loads from", librarian)
        self.assertNotIn("Claude Code loads", librarian)
        self.assertIn("`AGENTS_DIR=~/.agents`", librarian)
        self.assertIn("`AGENTS_SRC=~/.agents`", librarian)
        self.assertNotIn("~/.claude/agents/", librarian)
        self.assertIn("In Brent's ~/.codex/skills stack", brand)
        self.assertNotIn("In Brent's ~/.claude/skills stack", brand)
        self.assertIn("historical", miner_reference)
        self.assertIn("read-only", miner_reference)
        self.assertIn("historical", vault)
        self.assertIn("read-only", vault)

    def test_every_non_native_runtime_unconditionally_prohibits_secret_values(self):
        for entry in self.manifest.sources:
            if entry.conversion == "native":
                continue
            with self.subTest(skill=entry.source):
                result = adapt_text(
                    entry.source,
                    source_body(entry.source),
                    entry=entry,
                )
                self.assertIn(
                    "Never expose or print secret, credential, or token values.", result
                )

    def test_adaptation_preserves_crlf_newline_style(self):
        text = "Use the AskUserQuestion tool now.\r\n"

        result = adapt_text("last30days", text)

        self.assertNotIn("AskUserQuestion", result)
        self.assertNotIn("\n", result.replace("\r\n", ""))


class AdapterBuildIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        manifest = load_manifest(MANIFEST_PATH, repo_root=REPOSITORY_ROOT)
        by_name = {entry.source: entry for entry in manifest.sources}
        cls.manifest = Manifest(
            sources=(by_name["context-keeper"], by_name["the-rebuild"]),
            promoted=(),
        )

    def test_build_adapts_skill_and_named_resource_without_mutating_sources(self):
        before = hash_protected_sources(REPOSITORY_ROOT)
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory) / "skills"

            result = build_collection(REPOSITORY_ROOT, self.manifest, output)

            self.assertEqual(2, result.count)
            context = (output / "context-keeper" / "SKILL.md").read_text(
                encoding="utf-8"
            )
            reference = (output / "the-rebuild" / "REFERENCE.md").read_text(
                encoding="utf-8"
            )
            self.assertIn(".codex/sessions/", context)
            self.assertNotIn(
                "CURRENT project's .claude/sessions/", context.split("---", 2)[1]
            )
            self.assertIn("~/.codex/skills/signal-mine", reference)
        self.assertEqual(before, hash_protected_sources(REPOSITORY_ROOT))

    def test_real_build_enforces_the_complete_adapter_contract(self):
        manifest = load_manifest(MANIFEST_PATH, repo_root=REPOSITORY_ROOT)
        before = hash_protected_sources(REPOSITORY_ROOT)
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory) / "skills"
            result = build_collection(REPOSITORY_ROOT, manifest, output)

            self.assertEqual(51, result.count)
            self.assertEqual(
                Counter({"dependency-required": 40, "native": 6, "adapted": 5}),
                Counter(entry.conversion for entry in manifest.sources),
            )
            self.assertEqual(
                {entry.source for entry in manifest.sources}, set(ADAPTER_REGISTRY)
            )

            generated = {}
            for entry in manifest.sources:
                text = (output / entry.output / "SKILL.md").read_text(encoding="utf-8")
                generated[entry.source] = text
                expected_runtime_count = 0 if entry.conversion == "native" else 1
                self.assertEqual(
                    expected_runtime_count,
                    text.count("## Codex Runtime"),
                    entry.source,
                )
                for dependency in entry.dependencies:
                    self.assertIn(f"- `{dependency}`", text, entry.source)

            group_markers = {
                "context-keeper": ".codex/sessions/",
                "closing-ritual": ".codex/sessions/",
                "doc-keeper": "direct main-agent workflow",
                "tiger-doc-keeper": "direct main-agent workflow",
                "skill-miner": "~/.codex/skills",
                "skills-librarian": "~/.codex/skills",
                "page-rethink": "browser-use:browser",
                "intro-page": "browser-use:browser",
                "gws-shared": "connected Gmail/Google Drive app tools",
                "gws-workflow": "`gws` CLI fallback",
                "gws-workflow-email-to-task": "`gws` CLI fallback",
                "gws-workflow-file-announce": "`gws` CLI fallback",
                "gws-workflow-meeting-prep": "`gws` CLI fallback",
                "gws-workflow-standup-report": "`gws` CLI fallback",
                "gws-workflow-weekly-digest": "`gws` CLI fallback",
                "agent-reach": "direct main-agent workflow",
                "claude-memory-debug": "actual MCP tools",
                "claude-memory-index": "actual MCP tools",
                "claude-memory-search": "actual MCP tools",
                "claude-memory-status": "actual MCP tools",
                "gitnexus-cli": "actual GitNexus MCP tools",
                "gitnexus-debugging": "actual GitNexus MCP tools",
                "gitnexus-exploring": "actual GitNexus MCP tools",
                "gitnexus-guide": "actual GitNexus MCP tools",
                "gitnexus-impact-analysis": "actual GitNexus MCP tools",
                "gitnexus-pr-review": "actual GitNexus MCP tools",
                "gitnexus-refactoring": "actual GitNexus MCP tools",
                "allsup-leads-ssdi": "current collection",
                "allsup-leads-veterans": "current collection",
                "mine": "current collection",
                "refine": "current collection",
                "signal-mine": "current collection",
                "whitelabel-radar": "current collection",
                "tiger-leader-hunt": "current collection",
            }
            for skill_name, marker in group_markers.items():
                self.assertIn(marker, generated[skill_name], skill_name)

            prohibited_patterns = {
                "AskUserQuestion": re.compile(r"AskUserQuestion"),
                "Agent call": re.compile(r"Agent\("),
                "Task call": re.compile(r"Task\("),
                "Claude skill path": re.compile(r"~/.claude/skills/"),
                "Claude HOME skill path": re.compile(r"\$HOME/\.claude/skills/"),
                "Claude plugin/cache": re.compile(
                    r"(?:\$HOME|~)/\.claude/plugins/(?:cache|marketplaces)/"
                ),
                "Claude plugin manifest": re.compile(r"\.claude-plugin/plugin\.json"),
                "Claude ToolSearch": re.compile(r"ToolSearch"),
                "web pseudo-call": re.compile(
                    r"(?:WebSearch|WebFetch|Codex web (?:search|fetch)"
                    r"(?: capability)?)\("
                ),
                "Claude Desktop config": re.compile(r"claude_desktop_config"),
            }
            hits = []
            for path in output.rglob("*.md"):
                text = path.read_text(encoding="utf-8")
                for label, pattern in prohibited_patterns.items():
                    if pattern.search(text):
                        hits.append(f"{path.relative_to(output)}: {label}")
                for line in text.splitlines():
                    if ".claude/" in line and not (
                        "historical" in line and "read-only evidence" in line
                    ):
                        hits.append(
                            f"{path.relative_to(output)}: non-historical Claude path"
                        )
            self.assertEqual([], hits)

            named_resources = {
                ("skill-miner", "REFERENCE.md"),
                ("the-rebuild", "REFERENCE.md"),
            }
            for skill_name, relative_path in named_resources:
                source = REPOSITORY_ROOT / skill_name / relative_path
                copied = output / skill_name / relative_path
                self.assertNotEqual(source.read_bytes(), copied.read_bytes())
                self.assertEqual(
                    stat.S_IMODE(source.stat().st_mode),
                    stat.S_IMODE(copied.stat().st_mode),
                )

            for entry in manifest.sources:
                source_dir = REPOSITORY_ROOT / entry.source
                destination_dir = output / entry.output
                for source in source_dir.rglob("*"):
                    if not source.is_file() or source.is_symlink():
                        continue
                    relative = source.relative_to(source_dir)
                    copied = destination_dir / relative
                    if not copied.exists() or relative == Path("SKILL.md"):
                        continue
                    if (entry.source, relative.as_posix()) in named_resources:
                        continue
                    if relative == Path("agents/openai.yaml"):
                        continue
                    self.assertEqual(source.read_bytes(), copied.read_bytes(), source)
                    self.assertEqual(
                        stat.S_IMODE(source.stat().st_mode),
                        stat.S_IMODE(copied.stat().st_mode),
                        source,
                    )

        self.assertEqual(before, hash_protected_sources(REPOSITORY_ROOT))


if __name__ == "__main__":
    unittest.main()
