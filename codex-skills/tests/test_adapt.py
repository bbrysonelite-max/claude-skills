import tempfile
import unittest
from pathlib import Path

from scripts.adapt import ADAPTER_REGISTRY, adapt_description, adapt_text
from scripts.build import build_collection
from scripts.common import Manifest, hash_protected_sources, load_manifest


CODEX_SKILLS_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = CODEX_SKILLS_ROOT.parent
MANIFEST_PATH = CODEX_SKILLS_ROOT / "manifest.yaml"


def source_text(name: str, relative_path: str = "SKILL.md") -> str:
    with (REPOSITORY_ROOT / name / relative_path).open(
        "r", encoding="utf-8", newline=""
    ) as source_file:
        return source_file.read()


class AdapterContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = load_manifest(MANIFEST_PATH, repo_root=REPOSITORY_ROOT)
        cls.entries = {entry.source: entry for entry in cls.manifest.sources}

    def adapt_source(self, name: str, relative_path: str = "SKILL.md") -> str:
        return adapt_text(
            name,
            source_text(name, relative_path),
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
        source = source_text("page-rethink").replace(
            "Use the gstack browse binary:", "Use an unspecified browser:"
        )

        with self.assertRaisesRegex(ValueError, "page-rethink.*expected.*1"):
            adapt_text(
                "page-rethink",
                source,
                entry=self.entries["page-rethink"],
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


if __name__ == "__main__":
    unittest.main()
