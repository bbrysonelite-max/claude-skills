import io
import json
import os
import shutil
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import FrozenInstanceError
from pathlib import Path
from unittest.mock import patch

from scripts.install import InstallResult, install, main
from scripts.validate import validate_collection


CODEX_SKILLS_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = CODEX_SKILLS_ROOT.parent
COLLECTION = CODEX_SKILLS_ROOT / "skills"


def make_external_skill(root: Path, name: str, *, document_name: str | None = None) -> Path:
    skill = root / name
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text(
        "---\n"
        f'name: "{document_name or name}"\n'
        'description: "Use when an installer test needs an existing skill."\n'
        "---\n\n"
        "# Existing skill\n",
        encoding="utf-8",
    )
    return skill


class InstallTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.destination = self.root / "home" / "skills"

    def tearDown(self):
        self.temporary.cleanup()

    def test_result_is_structured_immutable_and_serializable(self):
        result = InstallResult(created=("sample",), errors=("error",))

        with self.assertRaises(FrozenInstanceError):
            result.created = ()
        self.assertEqual(
            {
                "ok": False,
                "created": ["sample"],
                "updated": [],
                "unchanged": [],
                "skipped": [],
                "collisions": [],
                "errors": ["error"],
            },
            result.to_dict(),
        )
        json.dumps(result.to_dict())

    def test_installs_all_skills_into_an_empty_destination(self):
        result = install(COLLECTION, self.destination)

        self.assertEqual(58, len(result.created))
        self.assertEqual((), result.errors)
        self.assertEqual(58, len(tuple(self.destination.iterdir())))
        for name in result.created:
            path = self.destination / name
            self.assertTrue(path.is_symlink())
            self.assertTrue(Path(path.readlink()).is_absolute())

    def test_second_install_is_idempotent(self):
        first = install(COLLECTION, self.destination)
        first_links = {path.name: os.readlink(path) for path in self.destination.iterdir()}

        second = install(COLLECTION, self.destination)

        self.assertEqual(58, len(first.created))
        self.assertEqual(58, len(second.unchanged))
        self.assertEqual((), second.created)
        self.assertEqual(
            first_links,
            {path.name: os.readlink(path) for path in self.destination.iterdir()},
        )

    def test_updates_a_managed_link_pointing_to_wrong_direct_child(self):
        install(COLLECTION, self.destination)
        path = self.destination / "agent-reach"
        path.unlink()
        path.symlink_to(COLLECTION / "ai-evaluation-audit", target_is_directory=True)

        result = install(COLLECTION, self.destination)

        self.assertEqual(("agent-reach",), result.updated)
        self.assertEqual((COLLECTION / "agent-reach").resolve(), path.resolve())

    def test_updates_a_broken_managed_link_with_lexical_target_in_collection(self):
        self.destination.mkdir(parents=True)
        path = self.destination / "agent-reach"
        stale_target = COLLECTION.resolve() / "removed-agent-reach"
        path.symlink_to(stale_target, target_is_directory=True)

        result = install(COLLECTION, self.destination)

        self.assertEqual(("agent-reach",), result.updated)
        self.assertEqual((COLLECTION / "agent-reach").resolve(), path.resolve())

    def test_real_directory_file_and_unrelated_symlink_are_collisions(self):
        for kind in ("directory", "file", "symlink"):
            with self.subTest(kind=kind):
                destination = self.root / kind
                destination.mkdir()
                path = destination / "agent-reach"
                if kind == "directory":
                    path.mkdir()
                elif kind == "file":
                    path.write_text("preserve me\n", encoding="utf-8")
                else:
                    external = make_external_skill(
                        self.root / f"external-{kind}", "agent-reach"
                    )
                    path.symlink_to(external, target_is_directory=True)
                before = path.lstat()
                link_text = os.readlink(path) if path.is_symlink() else None

                result = install(COLLECTION, destination)

                self.assertIn("agent-reach", result.collisions)
                self.assertEqual(before.st_ino, path.lstat().st_ino)
                if link_text is not None:
                    self.assertEqual(link_text, os.readlink(path))
                self.assertEqual(["agent-reach"], [item.name for item in destination.iterdir()])

    def test_collision_aborts_every_planned_mutation(self):
        self.destination.mkdir(parents=True)
        collision = self.destination / "ground-truth"
        collision.write_text("do not replace\n", encoding="utf-8")

        result = install(COLLECTION, self.destination)

        self.assertEqual(("ground-truth",), result.collisions)
        self.assertEqual("do not replace\n", collision.read_text(encoding="utf-8"))
        self.assertEqual(["ground-truth"], [item.name for item in self.destination.iterdir()])

    def test_unrelated_destination_entries_are_preserved(self):
        self.destination.mkdir(parents=True)
        unrelated = self.destination / "personal-only"
        unrelated.write_text("preserve me\n", encoding="utf-8")

        result = install(COLLECTION, self.destination)

        self.assertTrue(result.ok)
        self.assertEqual("preserve me\n", unrelated.read_text(encoding="utf-8"))

    def test_unknown_or_missing_skip_is_an_error_without_destination_creation(self):
        for name in ("unknown-skill", "agent-reach"):
            with self.subTest(name=name):
                destination = self.root / f"skip-{name}"
                result = install(COLLECTION, destination, skip_existing=(name,))
                self.assertTrue(result.errors)
                self.assertFalse(destination.exists())

    def test_valid_real_existing_skill_can_be_explicitly_skipped(self):
        existing = make_external_skill(self.destination, "last30days")
        before = existing.lstat().st_ino

        result = install(
            COLLECTION, self.destination, skip_existing=("last30days",)
        )

        self.assertEqual(("last30days",), result.skipped)
        self.assertEqual(before, existing.lstat().st_ino)
        self.assertEqual(57, len(result.created))

    def test_valid_unrelated_symlink_can_be_explicitly_skipped(self):
        self.destination.mkdir(parents=True)
        external = make_external_skill(self.root / "external", "last30days")
        existing = self.destination / "last30days"
        existing.symlink_to(external, target_is_directory=True)
        link_text = os.readlink(existing)

        result = install(
            COLLECTION, self.destination, skip_existing=("last30days",)
        )

        self.assertEqual(("last30days",), result.skipped)
        self.assertEqual(link_text, os.readlink(existing))

        report = validate_collection(
            REPOSITORY_ROOT,
            installed=self.destination,
            approved_existing=("last30days",),
            collect_evidence=False,
            structural_only=True,
        )
        self.assertTrue(report.ok, report.errors)
        self.assertEqual(57, report.installed_count)
        self.assertEqual(1, report.approved_existing_count)

    def test_skip_rejects_name_mismatch_or_unsafe_nested_symlink(self):
        for kind in ("name", "escape", "frontmatter"):
            with self.subTest(kind=kind):
                destination = self.root / f"invalid-{kind}"
                existing = make_external_skill(
                    destination,
                    "last30days",
                    document_name="wrong-name" if kind == "name" else None,
                )
                if kind == "escape":
                    outside = self.root / "outside.txt"
                    outside.write_text("outside\n", encoding="utf-8")
                    (existing / "escape.txt").symlink_to(outside)
                elif kind == "frontmatter":
                    skill_path = existing / "SKILL.md"
                    skill_path.write_text(
                        skill_path.read_text(encoding="utf-8").replace(
                            "description:", "extra: forbidden\ndescription:", 1
                        ),
                        encoding="utf-8",
                    )

                result = install(
                    COLLECTION, destination, skip_existing=("last30days",)
                )

                self.assertTrue(result.errors)
                self.assertEqual(["last30days"], [item.name for item in destination.iterdir()])

    def test_dry_run_returns_the_same_plan_without_mutation(self):
        dry = install(COLLECTION, self.destination, dry_run=True)

        self.assertEqual(58, len(dry.created))
        self.assertFalse(self.destination.exists())

        actual = install(COLLECTION, self.destination)
        self.assertEqual(dry.to_dict(), actual.to_dict())

    def test_default_destination_uses_codex_home(self):
        codex_home = self.root / "codex-home"
        with patch.dict(os.environ, {"CODEX_HOME": str(codex_home)}):
            result = install()

        self.assertTrue(result.ok)
        self.assertEqual(58, len(tuple((codex_home / "skills").iterdir())))

    def test_empty_codex_home_uses_home_fallback(self):
        home = self.root / "user-home"
        with patch.dict(os.environ, {"CODEX_HOME": "", "HOME": str(home)}):
            result = install()

        self.assertTrue(result.ok, result.errors)
        self.assertEqual(58, len(tuple((home / ".codex" / "skills").iterdir())))

    def test_destination_symlink_file_and_overlap_are_rejected(self):
        real = self.root / "real"
        real.mkdir()
        symlink = self.root / "linked-skills"
        symlink.symlink_to(real, target_is_directory=True)
        regular = self.root / "regular"
        regular.write_text("regular\n", encoding="utf-8")
        overlap = COLLECTION / "installed"

        for destination in (symlink, regular, overlap, REPOSITORY_ROOT):
            with self.subTest(destination=destination):
                result = install(COLLECTION, destination)
                self.assertTrue(result.errors)
        self.assertFalse(overlap.exists())

    def test_destination_with_user_symlinked_ancestor_is_rejected(self):
        real = self.root / "real-parent"
        real.mkdir()
        linked = self.root / "linked-parent"
        linked.symlink_to(real, target_is_directory=True)

        result = install(COLLECTION, linked / "skills")

        self.assertTrue(result.errors)
        self.assertFalse((real / "skills").exists())

    def test_source_itself_cannot_be_a_symlink(self):
        source = self.root / "source"
        source.symlink_to(COLLECTION, target_is_directory=True)

        result = install(source, self.destination)

        self.assertTrue(result.errors)
        self.assertFalse(self.destination.exists())

    def test_atomic_failure_rolls_back_links_and_removes_temp_debris(self):
        self.destination.mkdir(parents=True)
        existing = self.destination / "agent-reach"
        original_target = str(COLLECTION.resolve() / "ai-evaluation-audit")
        existing.symlink_to(original_target, target_is_directory=True)
        real_replace = os.replace
        calls = 0
        replacement_names: list[str] = []

        def fail_once(source, destination):
            nonlocal calls
            calls += 1
            replacement_names.append(Path(destination).name)
            if calls == 3:
                raise OSError("injected atomic failure")
            return real_replace(source, destination)

        with patch("scripts.install.os.replace", side_effect=fail_once):
            result = install(COLLECTION, self.destination)

        self.assertTrue(any("injected atomic failure" in error for error in result.errors))
        self.assertEqual((), result.created)
        self.assertEqual((), result.updated)
        self.assertTrue(replacement_names[0].startswith(".agent-reach.backup"))
        self.assertTrue(replacement_names[1].startswith(".agent-reach.ready"))
        self.assertTrue(replacement_names[2].startswith(".ai-evaluation-audit.ready"))
        self.assertEqual(original_target, os.readlink(existing))
        self.assertEqual(["agent-reach"], [item.name for item in self.destination.iterdir()])
        self.assertEqual([], list(self.destination.glob(".*.codex-install-*")))

    def test_appearing_real_file_is_not_overwritten_during_atomic_install(self):
        real_symlink = os.symlink
        injected = False

        def inject_collision(source, destination, *args, **kwargs):
            nonlocal injected
            real_symlink(source, destination, *args, **kwargs)
            target = Path(destination)
            if not injected and ".agent-reach.codex-install-" in target.name:
                injected = True
                (target.parent / "agent-reach").write_text(
                    "appeared concurrently\n", encoding="utf-8"
                )

        with patch("scripts.install.os.symlink", side_effect=inject_collision):
            result = install(COLLECTION, self.destination)

        collision = self.destination / "agent-reach"
        self.assertTrue(result.errors)
        self.assertFalse(collision.is_symlink())
        self.assertEqual(
            "appeared concurrently\n", collision.read_text(encoding="utf-8")
        )
        self.assertEqual(["agent-reach"], [item.name for item in self.destination.iterdir()])

    def test_failure_after_publication_rolls_back_the_published_link(self):
        real_unlink = os.unlink
        failed = False

        def fail_once(path, *args, **kwargs):
            nonlocal failed
            if not failed and ".agent-reach.ready.codex-install-" in Path(path).name:
                failed = True
                raise OSError("injected ready cleanup failure")
            return real_unlink(path, *args, **kwargs)

        with patch("scripts.install.os.unlink", side_effect=fail_once):
            result = install(COLLECTION, self.destination)

        self.assertTrue(any("ready cleanup failure" in error for error in result.errors))
        self.assertEqual((), result.created)
        self.assertFalse(self.destination.exists())

    def test_runtime_failure_during_mutation_rolls_back_prior_links(self):
        from scripts import install as install_module

        real_stage = install_module._stage_link
        calls = 0

        def fail_second(*args, **kwargs):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise RuntimeError("injected strict resolution failure")
            return real_stage(*args, **kwargs)

        with patch("scripts.install._stage_link", side_effect=fail_second):
            result = install(COLLECTION, self.destination)

        self.assertTrue(
            any("strict resolution failure" in error for error in result.errors)
        )
        self.assertEqual((), result.created)
        self.assertFalse(self.destination.exists())

    def test_installed_validator_observes_all_managed_links(self):
        install(COLLECTION, self.destination)

        report = validate_collection(
            REPOSITORY_ROOT,
            installed=self.destination,
            collect_evidence=False,
            structural_only=True,
        )

        self.assertTrue(report.ok, report.errors)
        self.assertEqual(58, report.installed_count)
        self.assertEqual(0, report.approved_existing_count)

    def test_installed_validator_observes_one_approved_existing_skill(self):
        make_external_skill(self.destination, "last30days")
        install(COLLECTION, self.destination, skip_existing=("last30days",))

        report = validate_collection(
            REPOSITORY_ROOT,
            installed=self.destination,
            approved_existing=("last30days",),
            collect_evidence=False,
            structural_only=True,
        )

        self.assertTrue(report.ok, report.errors)
        self.assertEqual(57, report.installed_count)
        self.assertEqual(1, report.approved_existing_count)


class SourcePreflightTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)

    def tearDown(self):
        self.temporary.cleanup()

    def copy_repository(self) -> tuple[Path, Path]:
        repository = self.root / "repo"
        shutil.copytree(
            REPOSITORY_ROOT,
            repository,
            symlinks=True,
            ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache"),
        )
        return repository, repository / "codex-skills" / "skills"

    def test_rejects_missing_extra_or_invalid_generated_skill(self):
        for kind in ("missing", "extra", "invalid"):
            with self.subTest(kind=kind):
                case_root = self.root / kind
                case_root.mkdir()
                repository = case_root / "repo"
                shutil.copytree(
                    REPOSITORY_ROOT,
                    repository,
                    symlinks=True,
                    ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache"),
                )
                collection = repository / "codex-skills" / "skills"
                if kind == "missing":
                    shutil.rmtree(collection / "agent-reach")
                elif kind == "extra":
                    shutil.copytree(collection / "agent-reach", collection / "extra-skill")
                    skill = collection / "extra-skill" / "SKILL.md"
                    skill.write_text(
                        skill.read_text(encoding="utf-8").replace(
                            'name: "agent-reach"', 'name: "extra-skill"', 1
                        ),
                        encoding="utf-8",
                    )
                else:
                    skill = collection / "agent-reach" / "SKILL.md"
                    skill.write_text(
                        skill.read_text(encoding="utf-8").replace(
                            'name: "agent-reach"', 'name: "wrong-name"', 1
                        ),
                        encoding="utf-8",
                    )

                destination = case_root / "destination"
                result = install(collection, destination)

                self.assertTrue(result.errors)
                if kind == "invalid":
                    self.assertTrue(
                        any("frontmatter name" in error for error in result.errors),
                        result.errors,
                    )
                self.assertFalse(destination.exists())

    def test_rejects_stale_validation_report(self):
        repository, collection = self.copy_repository()
        (collection / "agent-reach" / "unreviewed.txt").write_text(
            "stale output\n", encoding="utf-8"
        )
        destination = self.root / "destination"

        result = install(collection, destination)

        self.assertTrue(any("stale" in error for error in result.errors))
        self.assertFalse(destination.exists())

    def test_rejects_escaping_or_broken_source_symlink(self):
        for kind in ("escaping", "broken"):
            with self.subTest(kind=kind):
                case_root = self.root / kind
                case_root.mkdir()
                repository = case_root / "repo"
                shutil.copytree(
                    REPOSITORY_ROOT,
                    repository,
                    symlinks=True,
                    ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache"),
                )
                collection = repository / "codex-skills" / "skills"
                target = (
                    case_root / "outside.txt"
                    if kind == "escaping"
                    else case_root / "missing.txt"
                )
                if kind == "escaping":
                    target.write_text("outside\n", encoding="utf-8")
                (collection / "agent-reach" / "unsafe.txt").symlink_to(target)
                destination = case_root / "destination"

                result = install(collection, destination)

                self.assertTrue(result.errors)
                self.assertFalse(destination.exists())


class CliTests(unittest.TestCase):
    def test_json_dry_run_reports_plan_without_creating_destination(self):
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "skills"
            stdout = io.StringIO()
            with redirect_stdout(stdout), redirect_stderr(io.StringIO()):
                exit_code = main(
                    ["--source", str(COLLECTION), "--dest", str(destination), "--dry-run", "--json"]
                )

            payload = json.loads(stdout.getvalue())
            self.assertEqual(0, exit_code)
            self.assertEqual(58, len(payload["created"]))
            self.assertFalse(destination.exists())

    def test_cli_returns_nonzero_and_json_for_collisions(self):
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "skills"
            destination.mkdir()
            (destination / "agent-reach").write_text("collision\n", encoding="utf-8")
            stdout = io.StringIO()
            with redirect_stdout(stdout), redirect_stderr(io.StringIO()):
                exit_code = main(
                    ["--source", str(COLLECTION), "--dest", str(destination), "--json"]
                )

            payload = json.loads(stdout.getvalue())
            self.assertEqual(1, exit_code)
            self.assertEqual(["agent-reach"], payload["collisions"])

    def test_cli_supports_repeatable_skip_existing(self):
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "skills"
            make_external_skill(destination, "last30days")
            stdout = io.StringIO()
            with redirect_stdout(stdout), redirect_stderr(io.StringIO()):
                exit_code = main(
                    [
                        "--source",
                        str(COLLECTION),
                        "--dest",
                        str(destination),
                        "--skip-existing",
                        "last30days",
                        "--json",
                    ]
                )

            payload = json.loads(stdout.getvalue())
            self.assertEqual(0, exit_code)
            self.assertEqual(["last30days"], payload["skipped"])


if __name__ == "__main__":
    unittest.main()
