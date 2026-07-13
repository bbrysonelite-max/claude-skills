import json
import tempfile
import unittest
from dataclasses import FrozenInstanceError
from pathlib import Path

from scripts.common import (
    Manifest,
    SkillEntry,
    discover_source_skills,
    load_manifest,
)


CODEX_SKILLS_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = CODEX_SKILLS_ROOT.parent
MANIFEST_PATH = CODEX_SKILLS_ROOT / "manifest.yaml"
ALLOWED_CONVERSIONS = {"native", "adapted", "dependency-required"}


def source_entry(name="sample", output=None, **overrides):
    entry = {
        "source": name,
        "promoted_from": None,
        "output": output or name,
        "conversion": "native",
        "dependencies": [],
        "notes": "Works directly in Codex.",
    }
    entry.update(overrides)
    return entry


def promoted_entry(name="promoted", provenance=".agents-backup/source.md", **overrides):
    entry = {
        "source": None,
        "promoted_from": provenance,
        "output": name,
        "conversion": "adapted",
        "dependencies": [],
        "notes": "Removes archived orchestration coupling.",
    }
    entry.update(overrides)
    return entry


class ManifestTests(unittest.TestCase):
    def load_data(self, data, repo_root=None):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.yaml"
            path.write_text(json.dumps(data), encoding="utf-8")
            return load_manifest(path, repo_root=repo_root)

    def assert_invalid(self, data, pattern, repo_root=None):
        with self.assertRaisesRegex(ValueError, pattern):
            self.load_data(data, repo_root=repo_root)

    def test_manifest_has_51_sources_and_7_promoted_skills(self):
        manifest = load_manifest(MANIFEST_PATH, repo_root=REPOSITORY_ROOT)

        self.assertEqual(51, len(manifest.sources))
        self.assertEqual(7, len(manifest.promoted))
        self.assertEqual(58, len({entry.output for entry in manifest.entries}))

    def test_all_source_folders_are_accounted_for_without_renaming(self):
        manifest = load_manifest(MANIFEST_PATH, repo_root=REPOSITORY_ROOT)
        discovered = {path.name for path in discover_source_skills(REPOSITORY_ROOT)}

        self.assertEqual(discovered, {entry.source for entry in manifest.sources})
        self.assertTrue(all(entry.source == entry.output for entry in manifest.sources))

    def test_promoted_outputs_record_expected_provenance(self):
        manifest = load_manifest(MANIFEST_PATH, repo_root=REPOSITORY_ROOT)
        expected = {
            "assumptions-audit": ".agents-backup/gsd-assumptions-analyzer.md",
            "codebase-pattern-mapping": ".agents-backup/gsd-pattern-mapper.md",
            "documentation-claim-verification": ".agents-backup/gsd-doc-verifier.md",
            "integration-flow-audit": ".agents-backup/gsd-integration-checker.md",
            "requirements-coverage-audit": ".agents-backup/gsd-nyquist-auditor.md",
            "threat-mitigation-audit": ".agents-backup/gsd-security-auditor.md",
            "ai-evaluation-audit": ".agents-backup/gsd-eval-auditor.md",
        }

        self.assertEqual(expected, {entry.output: entry.promoted_from for entry in manifest.promoted})

    def test_classes_dependency_tuples_and_notes_are_valid(self):
        manifest = load_manifest(MANIFEST_PATH, repo_root=REPOSITORY_ROOT)

        for entry in manifest.entries:
            self.assertIn(entry.conversion, ALLOWED_CONVERSIONS)
            self.assertIsInstance(entry.dependencies, tuple)
            self.assertTrue(entry.notes.strip())

    def test_manifest_records_all_three_conversion_classes(self):
        manifest = load_manifest(MANIFEST_PATH, repo_root=REPOSITORY_ROOT)

        self.assertEqual(ALLOWED_CONVERSIONS, {entry.conversion for entry in manifest.entries})

    def test_reviewed_entries_record_exact_runtime_requirements(self):
        manifest = load_manifest(MANIFEST_PATH, repo_root=REPOSITORY_ROOT)
        entries = {entry.output: entry for entry in manifest.entries}

        self.assertEqual("adapted", entries["the-rebuild"].conversion)
        self.assertIn("reference tool/path adaptation", entries["the-rebuild"].notes)
        self.assertEqual(
            ("bash", "curl", "file", "bundled or system jq", "here.now network access"),
            entries["here-now"].dependencies,
        )
        self.assertEqual(
            ("gcloud CLI", "Google Cloud user and ADC access", "cloud-sql-proxy"),
            entries["cloud-run-reauth"].dependencies,
        )
        self.assertEqual(
            ("Node.js", "Google Chrome"),
            entries["tiger-whitepaper"].dependencies,
        )

    def test_manifest_models_are_frozen(self):
        entry = SkillEntry(None, None, "sample", "native", (), "note")
        manifest = Manifest((entry,), ())

        with self.assertRaises(FrozenInstanceError):
            entry.output = "changed"
        with self.assertRaises(FrozenInstanceError):
            manifest.sources = ()
        self.assertEqual((entry,), manifest.entries)

    def test_rejects_unknown_top_level_keys(self):
        self.assert_invalid(
            {"sources": [], "promoted": [], "extra": []},
            "unknown top-level keys",
        )

    def test_rejects_unknown_entry_keys(self):
        entry = source_entry(extra="unexpected")
        self.assert_invalid(
            {"sources": [entry], "promoted": []},
            "unknown entry keys",
        )

    def test_rejects_missing_top_level_fields(self):
        self.assert_invalid({"sources": []}, "missing top-level keys")

    def test_rejects_missing_entry_fields(self):
        entry = source_entry()
        del entry["notes"]
        self.assert_invalid(
            {"sources": [entry], "promoted": []},
            "missing entry keys",
        )

    def test_rejects_invalid_conversion_classes(self):
        entry = source_entry(conversion="automatic")
        self.assert_invalid(
            {"sources": [entry], "promoted": []},
            "invalid conversion",
        )

    def test_rejects_unsafe_source_names(self):
        entry = source_entry(name="../sample", output="sample")
        self.assert_invalid(
            {"sources": [entry], "promoted": []},
            "unsafe source name",
        )

    def test_rejects_unsafe_output_names(self):
        entry = source_entry(output="Sample Skill")
        self.assert_invalid(
            {"sources": [entry], "promoted": []},
            "unsafe output name",
        )

    def test_rejects_unsafe_promoted_provenance_paths(self):
        entry = promoted_entry(provenance="../outside.md")
        self.assert_invalid(
            {"sources": [], "promoted": [entry]},
            "unsafe promoted provenance",
        )

    def test_rejects_duplicate_sources(self):
        self.assert_invalid(
            {"sources": [source_entry(), source_entry(output="other")], "promoted": []},
            "duplicate source",
        )

    def test_rejects_duplicate_outputs_across_sections(self):
        self.assert_invalid(
            {
                "sources": [source_entry(output="duplicate")],
                "promoted": [promoted_entry(name="duplicate")],
            },
            "duplicate output",
        )

    def test_rejects_nonexistent_source_path_when_repo_root_is_supplied(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assert_invalid(
                {"sources": [source_entry(name="missing")], "promoted": []},
                "source path does not exist",
                repo_root=Path(directory),
            )

    def test_rejects_nonexistent_promoted_provenance_when_repo_root_is_supplied(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assert_invalid(
                {"sources": [], "promoted": [promoted_entry()]},
                "promoted provenance does not exist",
                repo_root=Path(directory),
            )

    def test_dependencies_are_loaded_as_a_tuple(self):
        manifest = self.load_data(
            {
                "sources": [source_entry(dependencies=["example-cli", "service credentials"])],
                "promoted": [],
            }
        )

        self.assertEqual(("example-cli", "service credentials"), manifest.sources[0].dependencies)

    def test_rejects_wrong_entry_provenance_for_each_section(self):
        self.assert_invalid(
            {"sources": [source_entry(source=None)], "promoted": []},
            "source entry must set source",
        )
        self.assert_invalid(
            {"sources": [], "promoted": [promoted_entry(source="sample")]},
            "promoted entry must not set source",
        )

    def test_rejects_invalid_field_types(self):
        self.assert_invalid(
            {"sources": [source_entry(dependencies="cli")], "promoted": []},
            "dependencies must be a list",
        )
        self.assert_invalid(
            {"sources": [source_entry(notes="")], "promoted": []},
            "notes must be a non-empty string",
        )
        self.assert_invalid(
            {"sources": [source_entry(conversion=["native"])], "promoted": []},
            "invalid conversion",
        )


if __name__ == "__main__":
    unittest.main()
