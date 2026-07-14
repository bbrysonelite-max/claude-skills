import io
import inspect
import json
import os
import shutil
import sys
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


def write_child_file(directory_fd: int, name: str, data: bytes) -> None:
    descriptor = os.open(
        name,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL,
        0o600,
        dir_fd=directory_fd,
    )
    try:
        os.write(descriptor, data)
    finally:
        os.close(descriptor)


class InstallTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.destination = self.root / "home" / "skills"

    def tearDown(self):
        self.temporary.cleanup()

    def test_install_accepts_explicit_exclusions(self):
        self.assertIn("exclude", inspect.signature(install).parameters)

    def test_result_preserves_legacy_positional_argument_mapping(self):
        result = InstallResult(
            ("created",),
            ("updated",),
            ("planned-created",),
            ("planned-updated",),
            ("unchanged",),
            ("skipped",),
            ("collision",),
            ("error",),
            ("warning",),
        )

        self.assertEqual(("collision",), result.collisions)
        self.assertEqual(("error",), result.errors)
        self.assertEqual(("warning",), result.warnings)
        self.assertEqual((), result.excluded)

    def test_result_is_structured_immutable_and_serializable(self):
        result = InstallResult(
            created=("sample",),
            planned_created=("sample", "other"),
            errors=("error",),
        )

        with self.assertRaises(FrozenInstanceError):
            result.created = ()
        self.assertEqual(
            {
                "ok": False,
                "created": ["sample"],
                "updated": [],
                "planned_created": ["sample", "other"],
                "planned_updated": [],
                "unchanged": [],
                "skipped": [],
                "excluded": [],
                "collisions": [],
                "errors": ["error"],
                "warnings": [],
            },
            result.to_dict(),
        )
        json.dumps(result.to_dict())

    def test_installs_all_skills_into_an_empty_destination(self):
        result = install(COLLECTION, self.destination)

        self.assertEqual(59, len(result.created))
        self.assertEqual((), result.errors)
        self.assertEqual(59, len(tuple(self.destination.iterdir())))
        for name in result.created:
            path = self.destination / name
            self.assertTrue(path.is_symlink())
            self.assertTrue(Path(path.readlink()).is_absolute())

    def test_second_install_is_idempotent(self):
        first = install(COLLECTION, self.destination)
        first_links = {path.name: os.readlink(path) for path in self.destination.iterdir()}

        second = install(COLLECTION, self.destination)

        self.assertEqual(59, len(first.created))
        self.assertEqual(59, len(second.unchanged))
        self.assertEqual((), second.created)
        self.assertEqual(
            first_links,
            {path.name: os.readlink(path) for path in self.destination.iterdir()},
        )

    def test_idempotent_plan_rejects_destination_swap_before_open(self):
        from scripts import install as install_module

        install(COLLECTION, self.destination)
        moved = self.root / "planned-destination"
        real_open = install_module._DestinationHandle.open

        def swap_before_open(handle):
            self.destination.rename(moved)
            self.destination.mkdir()
            (self.destination / "personal.txt").write_bytes(b"replacement root\n")
            return real_open(handle)

        with patch.object(
            install_module._DestinationHandle,
            "open",
            autospec=True,
            side_effect=swap_before_open,
        ):
            result = install(COLLECTION, self.destination)

        self.assertTrue(result.errors)
        self.assertEqual((), result.unchanged)
        self.assertEqual(
            ["personal.txt"],
            [path.name for path in self.destination.iterdir()],
        )
        self.assertEqual(59, len(tuple(moved.iterdir())))
        self.assertEqual([], list(moved.glob(".*.codex-install-*")))

    def test_skip_plan_rejects_destination_swap_before_open(self):
        from scripts import install as install_module

        existing = make_external_skill(self.destination, "last30days")
        expected_document = (existing / "SKILL.md").read_bytes()
        first = install(
            COLLECTION,
            self.destination,
            skip_existing=("last30days",),
        )
        self.assertEqual(58, len(first.created))
        moved = self.root / "planned-skip-destination"
        real_open = install_module._DestinationHandle.open

        def swap_before_open(handle):
            self.destination.rename(moved)
            self.destination.mkdir()
            (self.destination / "personal.txt").write_bytes(b"replacement skip root\n")
            return real_open(handle)

        with patch.object(
            install_module._DestinationHandle,
            "open",
            autospec=True,
            side_effect=swap_before_open,
        ):
            result = install(
                COLLECTION,
                self.destination,
                skip_existing=("last30days",),
            )

        self.assertTrue(result.errors)
        self.assertEqual((), result.unchanged)
        self.assertEqual((), result.skipped)
        self.assertEqual(
            ["personal.txt"],
            [path.name for path in self.destination.iterdir()],
        )
        self.assertEqual(
            expected_document,
            (moved / "last30days" / "SKILL.md").read_bytes(),
        )
        self.assertEqual(59, len(tuple(moved.iterdir())))
        self.assertEqual([], list(moved.glob(".*.codex-install-*")))

    def test_unchanged_link_replacement_after_open_invalidates_plan(self):
        from scripts import install as install_module

        install(COLLECTION, self.destination)
        path = self.destination / "agent-reach"
        displaced = self.destination / "preserved-agent-reach"
        expected_target = os.readlink(path)
        real_open = install_module._DestinationHandle.open

        def replace_after_open(handle):
            real_open(handle)
            path.rename(displaced)
            path.write_bytes(b"replacement entry\n")

        with patch.object(
            install_module._DestinationHandle,
            "open",
            autospec=True,
            side_effect=replace_after_open,
        ):
            result = install(COLLECTION, self.destination)

        self.assertTrue(result.errors)
        self.assertEqual((), result.unchanged)
        self.assertEqual(b"replacement entry\n", path.read_bytes())
        self.assertTrue(displaced.is_symlink())
        self.assertEqual(expected_target, os.readlink(displaced))
        self.assertEqual([], list(self.destination.glob(".*.codex-install-*")))

    def test_approved_skill_mutation_after_open_invalidates_plan_before_creation(self):
        from scripts import install as install_module

        existing = make_external_skill(self.destination, "last30days")
        skill = existing / "SKILL.md"
        replacement = skill.read_bytes().replace(
            b"an installer test needs an existing skill",
            b"the approved skill changed after planning",
        )
        real_open = install_module._DestinationHandle.open

        def mutate_after_open(handle):
            real_open(handle)
            skill.write_bytes(replacement)

        with patch.object(
            install_module._DestinationHandle,
            "open",
            autospec=True,
            side_effect=mutate_after_open,
        ):
            result = install(
                COLLECTION,
                self.destination,
                skip_existing=("last30days",),
            )

        self.assertTrue(result.errors)
        self.assertEqual((), result.created)
        self.assertEqual((), result.unchanged)
        self.assertEqual((), result.skipped)
        self.assertEqual(58, len(result.planned_created))
        self.assertEqual(replacement, skill.read_bytes())
        self.assertEqual(
            ["last30days"],
            [path.name for path in self.destination.iterdir()],
        )
        self.assertEqual([], list(self.destination.glob(".*.codex-install-*")))

    def test_approved_skill_mutation_during_install_rolls_back_before_commit(self):
        from scripts import install as install_module

        existing = make_external_skill(self.destination, "last30days")
        skill = existing / "SKILL.md"
        replacement = skill.read_bytes().replace(
            b"an installer test needs an existing skill",
            b"the approved skill changed during installation",
        )
        real_publish = install_module._publish_without_overwrite
        changed = False

        def publish_then_mutate(*args, **kwargs):
            nonlocal changed
            result = real_publish(*args, **kwargs)
            if not changed:
                changed = True
                skill.write_bytes(replacement)
            return result

        with patch(
            "scripts.install._publish_without_overwrite",
            side_effect=publish_then_mutate,
        ):
            result = install(
                COLLECTION,
                self.destination,
                skip_existing=("last30days",),
            )

        self.assertTrue(changed)
        self.assertTrue(result.errors)
        self.assertEqual((), result.created)
        self.assertEqual((), result.skipped)
        self.assertEqual(58, len(result.planned_created))
        self.assertEqual(replacement, skill.read_bytes())
        self.assertEqual(
            ["last30days"],
            [path.name for path in self.destination.iterdir()],
        )
        self.assertEqual([], list(self.destination.glob(".*.codex-install-*")))

    def test_approved_tree_mutations_invalidate_real_and_symlink_plans(self):
        from scripts import install as install_module

        scenarios = (
            ("escaping-link", "after-open"),
            ("escaping-link", "during-publish"),
            ("broken-link", "after-open"),
            ("broken-link", "during-publish"),
            ("replace-file", "after-open"),
            ("replace-directory", "after-open"),
            ("delete-file", "after-open"),
            ("delete-directory", "after-open"),
            ("mutate-content", "during-publish"),
        )
        for form in ("directory", "symlink"):
            for mutation, timing in scenarios:
                with self.subTest(form=form, mutation=mutation, timing=timing):
                    case_root = self.root / f"tree-{form}-{mutation}-{timing}"
                    destination = case_root / "skills"
                    if form == "directory":
                        approved = make_external_skill(destination, "last30days")
                    else:
                        approved = make_external_skill(
                            case_root / "external",
                            "last30days",
                        )
                        destination.mkdir(parents=True)
                        (destination / "last30days").symlink_to(
                            approved,
                            target_is_directory=True,
                        )
                    notes = approved / "notes.txt"
                    notes.write_bytes(b"approved notes\n")
                    resources = approved / "resources"
                    resources.mkdir()
                    (resources / "keep.txt").write_bytes(b"keep resource\n")
                    outside = case_root / "outside.txt"
                    outside.write_bytes(b"outside\n")
                    mutation_path: Path
                    expected_bytes: bytes | None = None
                    expected_link: str | None = None

                    def mutate_tree():
                        nonlocal mutation_path, expected_bytes, expected_link
                        if mutation == "escaping-link":
                            mutation_path = approved / "escape.txt"
                            mutation_path.symlink_to(outside)
                            expected_link = os.readlink(mutation_path)
                        elif mutation == "broken-link":
                            mutation_path = approved / "broken.txt"
                            mutation_path.symlink_to(approved / "missing.txt")
                            expected_link = os.readlink(mutation_path)
                        elif mutation == "replace-file":
                            mutation_path = notes
                            mutation_path.unlink()
                            expected_bytes = b"replacement notes\n"
                            mutation_path.write_bytes(expected_bytes)
                        elif mutation == "replace-directory":
                            shutil.rmtree(resources)
                            resources.mkdir()
                            mutation_path = resources / "replacement.txt"
                            expected_bytes = b"replacement resource\n"
                            mutation_path.write_bytes(expected_bytes)
                        elif mutation == "delete-file":
                            mutation_path = notes
                            mutation_path.unlink()
                        elif mutation == "delete-directory":
                            mutation_path = resources
                            shutil.rmtree(mutation_path)
                        else:
                            mutation_path = notes
                            expected_bytes = b"mutated approved notes\n"
                            mutation_path.write_bytes(expected_bytes)

                    changed = False
                    real_open = install_module._DestinationHandle.open
                    real_publish = install_module._publish_without_overwrite

                    def open_then_mutate(handle):
                        nonlocal changed
                        real_open(handle)
                        mutate_tree()
                        changed = True

                    def publish_then_mutate(*args, **kwargs):
                        nonlocal changed
                        result = real_publish(*args, **kwargs)
                        if not changed:
                            mutate_tree()
                            changed = True
                        return result

                    if timing == "after-open":
                        with patch.object(
                            install_module._DestinationHandle,
                            "open",
                            autospec=True,
                            side_effect=open_then_mutate,
                        ):
                            result = install(
                                COLLECTION,
                                destination,
                                skip_existing=("last30days",),
                            )
                    else:
                        with patch(
                            "scripts.install._publish_without_overwrite",
                            side_effect=publish_then_mutate,
                        ):
                            result = install(
                                COLLECTION,
                                destination,
                                skip_existing=("last30days",),
                            )

                    self.assertTrue(changed)
                    self.assertTrue(result.errors)
                    self.assertEqual((), result.created)
                    self.assertEqual((), result.updated)
                    self.assertEqual((), result.unchanged)
                    self.assertEqual((), result.skipped)
                    self.assertEqual(58, len(result.planned_created))
                    self.assertEqual(
                        ["last30days"],
                        [path.name for path in destination.iterdir()],
                    )
                    self.assertEqual(
                        [], list(destination.glob(".*.codex-install-*"))
                    )
                    if mutation in ("delete-file", "delete-directory"):
                        self.assertFalse(mutation_path.exists())
                    elif expected_link is not None:
                        self.assertTrue(mutation_path.is_symlink())
                        self.assertEqual(expected_link, os.readlink(mutation_path))
                    else:
                        self.assertEqual(expected_bytes, mutation_path.read_bytes())

                    if mutation in ("escaping-link", "broken-link"):
                        report = validate_collection(
                            REPOSITORY_ROOT,
                            installed=destination,
                            approved_existing=("last30days",),
                            collect_evidence=False,
                            structural_only=True,
                        )
                        self.assertFalse(report.ok)

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
        self.assertEqual((), result.created)
        self.assertEqual((), result.updated)
        self.assertEqual(58, len(result.planned_created))
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

    def test_excluded_skill_is_not_inspected_touched_or_managed(self):
        self.destination.mkdir(parents=True)
        existing = self.destination / "last30days"
        existing.write_bytes(b"invalid but explicitly excluded\n")
        before = existing.lstat()

        dry = install(
            COLLECTION,
            self.destination,
            exclude=("last30days",),
            dry_run=True,
        )

        self.assertTrue(dry.ok, dry.errors)
        self.assertEqual(("last30days",), dry.excluded)
        self.assertEqual(58, len(dry.planned_created))
        self.assertEqual((), dry.created)
        self.assertEqual(before.st_ino, existing.lstat().st_ino)
        self.assertEqual(b"invalid but explicitly excluded\n", existing.read_bytes())

        first = install(COLLECTION, self.destination, exclude=("last30days",))
        second = install(COLLECTION, self.destination, exclude=("last30days",))

        self.assertEqual(58, len(first.created))
        self.assertEqual(("last30days",), first.excluded)
        self.assertEqual(58, len(second.unchanged))
        self.assertEqual(("last30days",), second.excluded)
        self.assertEqual(before.st_ino, existing.lstat().st_ino)
        self.assertEqual(b"invalid but explicitly excluded\n", existing.read_bytes())

    def test_unknown_unsafe_or_conflicting_exclusion_is_rejected_without_mutation(self):
        for name in ("unknown-skill", "../unsafe"):
            with self.subTest(name=name):
                destination = self.root / f"exclude-{Path(name).name}"
                result = install(COLLECTION, destination, exclude=(name,))
                self.assertTrue(result.errors)
                self.assertFalse(destination.exists())

        existing = make_external_skill(self.destination, "last30days")
        before = (existing / "SKILL.md").read_bytes()
        result = install(
            COLLECTION,
            self.destination,
            skip_existing=("last30days",),
            exclude=("last30days",),
        )
        self.assertTrue(result.errors)
        self.assertFalse(any(path.is_symlink() for path in self.destination.iterdir()))
        self.assertEqual(before, (existing / "SKILL.md").read_bytes())

    def test_valid_real_existing_skill_can_be_explicitly_skipped(self):
        existing = make_external_skill(self.destination, "last30days")
        before = existing.lstat().st_ino

        result = install(
            COLLECTION, self.destination, skip_existing=("last30days",)
        )

        self.assertEqual(("last30days",), result.skipped)
        self.assertEqual(before, existing.lstat().st_ino)
        self.assertEqual(58, len(result.created))

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
        self.assertEqual(58, report.installed_count)
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

        self.assertEqual((), dry.created)
        self.assertEqual(59, len(dry.planned_created))
        self.assertFalse(self.destination.exists())

        actual = install(COLLECTION, self.destination)
        self.assertEqual(59, len(actual.created))
        self.assertEqual(dry.planned_created, actual.planned_created)

    def test_default_destination_uses_codex_home(self):
        codex_home = self.root / "codex-home"
        with patch.dict(os.environ, {"CODEX_HOME": str(codex_home)}):
            result = install()

        self.assertTrue(result.ok)
        self.assertEqual(59, len(tuple((codex_home / "skills").iterdir())))

    def test_empty_codex_home_uses_home_fallback(self):
        home = self.root / "user-home"
        with patch.dict(os.environ, {"CODEX_HOME": "", "HOME": str(home)}):
            result = install()

        self.assertTrue(result.ok, result.errors)
        self.assertEqual(59, len(tuple((home / ".codex" / "skills").iterdir())))

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

    def test_symlinked_ancestor_is_rejected_regardless_of_owner(self):
        real = self.root / "root-owned-real"
        real.mkdir()
        linked = self.root / "root-owned-link"
        linked.symlink_to(real, target_is_directory=True)

        with patch("scripts.install.os.getuid", return_value=-1):
            result = install(COLLECTION, linked / "skills")

        self.assertTrue(
            any("symlinked ancestor" in error for error in result.errors), result.errors
        )
        self.assertFalse((real / "skills").exists())

    @unittest.skipUnless(sys.platform == "darwin", "Darwin system alias regression")
    def test_tmp_alias_does_not_hide_nested_symlink(self):
        real = self.root / "tmp-alias-real"
        real.mkdir()
        linked = Path("/tmp") / f"codex-installer-link-{os.getpid()}-{id(self)}"
        self.assertFalse(os.path.lexists(linked))
        linked.symlink_to(real, target_is_directory=True)
        try:
            result = install(COLLECTION, linked / "skills")
        finally:
            if os.path.lexists(linked):
                linked.unlink()

        self.assertTrue(
            any("symlinked ancestor" in error for error in result.errors), result.errors
        )
        self.assertFalse((real / "skills").exists())

    def test_source_itself_cannot_be_a_symlink(self):
        source = self.root / "source"
        source.symlink_to(COLLECTION, target_is_directory=True)

        result = install(source, self.destination)

        self.assertTrue(result.errors)
        self.assertFalse(self.destination.exists())

    def make_stale_managed_links(
        self, destination: Path, names: tuple[str, ...]
    ) -> dict[str, str]:
        destination.mkdir(parents=True)
        collection = COLLECTION.resolve()
        targets = tuple(reversed(names))
        raw_targets: dict[str, str] = {}
        for name, wrong_name in zip(names, targets, strict=True):
            if wrong_name == name:
                wrong_name = "agent-reach" if name != "agent-reach" else "ground-truth"
            raw_target = str(collection / wrong_name)
            (destination / name).symlink_to(raw_target, target_is_directory=True)
            raw_targets[name] = raw_target
        return raw_targets

    def assert_only_original_links(
        self, destination: Path, raw_targets: dict[str, str]
    ) -> None:
        self.assertEqual(sorted(raw_targets), sorted(path.name for path in destination.iterdir()))
        for name, raw_target in raw_targets.items():
            self.assertTrue((destination / name).is_symlink())
            self.assertEqual(raw_target, os.readlink(destination / name))

    def test_backup_cleanup_failure_rolls_back_everything(self):
        names = ("agent-reach", "ai-evaluation-audit", "allsup-leads-ssdi")
        for error_type in (OSError, RuntimeError):
            for failure_position in (1, 2, 3):
                with self.subTest(
                    error_type=error_type.__name__, position=failure_position
                ):
                    destination = self.root / f"cleanup-{error_type.__name__}-{failure_position}"
                    raw_targets = self.make_stale_managed_links(destination, names)
                    real_unlink = os.unlink
                    attempts = 0
                    failed = False

                    def fail_backup_once(path, *args, **kwargs):
                        nonlocal attempts, failed
                        if ".backup.codex-install-" in Path(path).name:
                            attempts += 1
                            if not failed and attempts == failure_position:
                                failed = True
                                raise error_type("injected backup cleanup failure")
                        return real_unlink(path, *args, **kwargs)

                    with patch("scripts.install.os.unlink", side_effect=fail_backup_once):
                        result = install(COLLECTION, destination)

                    self.assertTrue(
                        any("backup cleanup failure" in error for error in result.errors),
                        result.errors,
                    )
                    self.assertEqual((), result.created)
                    self.assertEqual((), result.updated)
                    self.assert_only_original_links(destination, raw_targets)
                    self.assertEqual([], list(destination.glob(".*.codex-install-*")))

    def test_staging_and_backup_name_collisions_are_never_clobbered(self):
        real_symlink = os.symlink
        real_link = os.link
        for location in ("stage", "ready", "backup"):
            for artifact_kind in ("file", "directory", "symlink"):
                with self.subTest(location=location, artifact=artifact_kind):
                    destination = self.root / f"exclusive-{location}-{artifact_kind}"
                    if location == "backup":
                        self.make_stale_managed_links(destination, ("agent-reach",))
                    artifact_path: Path | None = None
                    artifact_inode: int | None = None
                    artifact_link_text: str | None = None

                    def create_artifact(name: str, directory_fd: int) -> None:
                        nonlocal artifact_path, artifact_inode, artifact_link_text
                        path = destination / Path(name).name
                        artifact_path = path
                        if artifact_kind == "file":
                            write_child_file(
                                directory_fd,
                                Path(name).name,
                                b"preserve collision bytes\n",
                            )
                        elif artifact_kind == "directory":
                            os.mkdir(Path(name).name, dir_fd=directory_fd)
                            (path / "payload.txt").write_text(
                                "preserve directory\n", encoding="utf-8"
                            )
                        else:
                            artifact_link_text = str(self.root / "unrelated-target")
                            real_symlink(
                                artifact_link_text,
                                Path(name).name,
                                dir_fd=directory_fd,
                            )
                        artifact_inode = path.lstat().st_ino

                    def collide_symlink(source, target, *args, **kwargs):
                        target_path = Path(target)
                        if (
                            artifact_path is None
                            and location == "stage"
                            and ".stage.codex-install-" in target_path.name
                        ):
                            create_artifact(target, kwargs["dir_fd"])
                        return real_symlink(source, target, *args, **kwargs)

                    def collide_link(source, target, *args, **kwargs):
                        target_path = Path(target)
                        if artifact_path is None and (
                            (location == "ready" and ".ready.codex-install-" in target_path.name)
                            or (
                                location == "backup"
                                and ".backup.codex-install-" in target_path.name
                            )
                        ):
                            create_artifact(target, kwargs["dst_dir_fd"])
                        return real_link(source, target, *args, **kwargs)

                    with (
                        patch("scripts.install.os.symlink", side_effect=collide_symlink),
                        patch("scripts.install.os.link", side_effect=collide_link),
                    ):
                        result = install(COLLECTION, destination)

                    self.assertTrue(result.ok, result.errors)
                    self.assertIsNotNone(artifact_path)
                    assert artifact_path is not None and artifact_inode is not None
                    self.assertEqual(artifact_inode, artifact_path.lstat().st_ino)
                    if artifact_kind == "file":
                        self.assertEqual(
                            b"preserve collision bytes\n", artifact_path.read_bytes()
                        )
                    elif artifact_kind == "directory":
                        self.assertEqual(
                            "preserve directory\n",
                            (artifact_path / "payload.txt").read_text(encoding="utf-8"),
                        )
                    else:
                        self.assertEqual(artifact_link_text, os.readlink(artifact_path))

    def test_substituted_stage_is_preserved_and_never_published(self):
        real_symlink = os.symlink
        attacker_path: Path | None = None
        attacker_inode: int | None = None

        def substitute_stage(source, target, *args, **kwargs):
            nonlocal attacker_path, attacker_inode
            real_symlink(source, target, *args, **kwargs)
            candidate = self.destination / Path(target).name
            if attacker_path is None and ".stage.codex-install-" in candidate.name:
                os.unlink(Path(target).name, dir_fd=kwargs["dir_fd"])
                write_child_file(
                    kwargs["dir_fd"], Path(target).name, b"attacker stage bytes\n"
                )
                attacker_path = candidate
                attacker_inode = candidate.lstat().st_ino

        with patch("scripts.install.os.symlink", side_effect=substitute_stage):
            result = install(COLLECTION, self.destination)

        self.assertTrue(result.errors)
        self.assertEqual((), result.created)
        self.assertIsNotNone(attacker_path)
        assert attacker_path is not None and attacker_inode is not None
        self.assertEqual(attacker_inode, attacker_path.lstat().st_ino)
        self.assertEqual(b"attacker stage bytes\n", attacker_path.read_bytes())
        installed = self.destination / "agent-reach"
        self.assertFalse(installed.exists())
        self.assertFalse(installed.is_symlink())

    def test_substituted_ready_is_preserved_and_never_published(self):
        real_link = os.link
        attacker_path: Path | None = None
        attacker_inode: int | None = None

        def substitute_ready(source, target, *args, **kwargs):
            nonlocal attacker_path, attacker_inode
            result = real_link(source, target, *args, **kwargs)
            candidate = self.destination / Path(target).name
            if attacker_path is None and ".ready.codex-install-" in candidate.name:
                os.unlink(Path(target).name, dir_fd=kwargs["dst_dir_fd"])
                write_child_file(
                    kwargs["dst_dir_fd"],
                    Path(target).name,
                    b"attacker ready bytes\n",
                )
                attacker_path = candidate
                attacker_inode = candidate.lstat().st_ino
            return result

        with patch("scripts.install.os.link", side_effect=substitute_ready):
            result = install(COLLECTION, self.destination)

        self.assertTrue(result.errors)
        self.assertEqual((), result.created)
        self.assertIsNotNone(attacker_path)
        assert attacker_path is not None and attacker_inode is not None
        self.assertEqual(attacker_inode, attacker_path.lstat().st_ino)
        self.assertEqual(b"attacker ready bytes\n", attacker_path.read_bytes())
        installed = self.destination / "agent-reach"
        self.assertFalse(installed.exists())
        self.assertFalse(installed.is_symlink())

    def test_attacker_stage_hardlink_is_removed_only_at_ready_name(self):
        real_link = os.link
        attacker_stage: Path | None = None
        attacker_inode: int | None = None

        def substitute_source_before_link(source, target, *args, **kwargs):
            nonlocal attacker_stage, attacker_inode
            source_path = self.destination / Path(source).name
            target_path = Path(target)
            if (
                attacker_stage is None
                and ".ready.codex-install-" in target_path.name
            ):
                os.unlink(Path(source).name, dir_fd=kwargs["src_dir_fd"])
                write_child_file(
                    kwargs["src_dir_fd"],
                    Path(source).name,
                    b"attacker source-stage bytes\n",
                )
                attacker_stage = source_path
                attacker_inode = source_path.lstat().st_ino
            return real_link(source, target, *args, **kwargs)

        with patch("scripts.install.os.link", side_effect=substitute_source_before_link):
            result = install(COLLECTION, self.destination)

        self.assertTrue(result.errors)
        self.assertIsNotNone(attacker_stage)
        assert attacker_stage is not None and attacker_inode is not None
        self.assertEqual(attacker_inode, attacker_stage.lstat().st_ino)
        self.assertEqual(b"attacker source-stage bytes\n", attacker_stage.read_bytes())
        ready_links = [
            path
            for path in self.destination.glob(".*.ready.codex-install-*")
            if path.lstat().st_ino == attacker_inode
        ]
        self.assertEqual([], ready_links)
        self.assertFalse((self.destination / "agent-reach").exists())

    def test_managed_update_keeps_installed_name_present_through_exchange(self):
        raw_targets = self.make_stale_managed_links(
            self.destination, ("agent-reach",)
        )
        existing = self.destination / "agent-reach"
        from scripts import install as install_module

        real_exchange = install_module._atomic_exchange
        checkpoints: list[bool] = []

        def observe_exchange(handle, first, second):
            checkpoints.append(os.path.lexists(existing))
            real_exchange(handle, first, second)
            checkpoints.append(os.path.lexists(existing))

        with patch("scripts.install._atomic_exchange", side_effect=observe_exchange):
            result = install(COLLECTION, self.destination)

        self.assertTrue(result.ok, result.errors)
        self.assertTrue(checkpoints)
        self.assertTrue(all(checkpoints))
        self.assertNotEqual(raw_targets["agent-reach"], os.readlink(existing))
        self.assertEqual(str((COLLECTION / "agent-reach").resolve()), os.readlink(existing))

    def test_concurrent_real_replacement_during_exchange_is_preserved(self):
        raw_targets = self.make_stale_managed_links(
            self.destination, ("agent-reach",)
        )
        existing = self.destination / "agent-reach"
        from scripts import install as install_module

        real_exchange = install_module._atomic_exchange
        injected = False

        def replace_before_exchange(handle, first, second):
            nonlocal injected
            if not injected:
                injected = True
                handle.child_unlink(existing)
                assert handle.fd is not None
                write_child_file(
                    handle.fd, existing.name, b"concurrent personal file\n"
                )
            real_exchange(handle, first, second)

        with patch(
            "scripts.install._atomic_exchange", side_effect=replace_before_exchange
        ):
            result = install(COLLECTION, self.destination)

        self.assertTrue(result.errors)
        self.assertFalse(existing.is_symlink())
        self.assertEqual(b"concurrent personal file\n", existing.read_bytes())
        self.assertNotEqual(raw_targets["agent-reach"], str(existing))
        self.assertEqual([], list(self.destination.glob(".*.codex-install-*")))

    def test_unsupported_atomic_exchange_fails_before_destination_mutation(self):
        raw_targets = self.make_stale_managed_links(
            self.destination, ("agent-reach",)
        )

        with patch(
            "scripts.install._atomic_exchange_capability_error",
            return_value="atomic exchange unsupported in test",
        ):
            result = install(COLLECTION, self.destination)

        self.assertTrue(any("unsupported" in error for error in result.errors))
        self.assert_only_original_links(self.destination, raw_targets)
        self.assertEqual([], list(self.destination.glob(".*.codex-install-*")))

    def test_exception_after_created_publication_rolls_back_created_link(self):
        from scripts import install as install_module

        real_publish = install_module._publish_without_overwrite
        raised = False

        def publish_then_raise(handle, first, second):
            nonlocal raised
            real_publish(handle, first, second)
            if not raised:
                raised = True
                raise RuntimeError("injected exception after publication")

        with patch(
            "scripts.install._publish_without_overwrite", side_effect=publish_then_raise
        ):
            result = install(COLLECTION, self.destination)

        self.assertTrue(any("after publication" in error for error in result.errors))
        self.assertEqual((), result.created)
        self.assertFalse(self.destination.exists())

    def test_exception_after_atomic_swap_restores_original_link(self):
        raw_targets = self.make_stale_managed_links(
            self.destination, ("agent-reach",)
        )
        from scripts import install as install_module

        real_exchange = install_module._atomic_exchange
        raised = False

        def exchange_then_raise(handle, first, second):
            nonlocal raised
            real_exchange(handle, first, second)
            if not raised:
                raised = True
                raise RuntimeError("injected exception after atomic swap")

        with patch("scripts.install._atomic_exchange", side_effect=exchange_then_raise):
            result = install(COLLECTION, self.destination)

        self.assertTrue(any("after atomic swap" in error for error in result.errors))
        self.assert_only_original_links(self.destination, raw_targets)
        self.assertEqual([], list(self.destination.glob(".*.codex-install-*")))

    def test_recovery_cleanup_failure_rolls_back_everything(self):
        names = ("agent-reach", "ai-evaluation-audit", "allsup-leads-ssdi")
        for error_type in (OSError, RuntimeError):
            for failure_position in (1, 2, 3):
                with self.subTest(
                    error_type=error_type.__name__, position=failure_position
                ):
                    destination = (
                        self.root
                        / f"recovery-{error_type.__name__}-{failure_position}"
                    )
                    raw_targets = self.make_stale_managed_links(destination, names)
                    real_unlink = os.unlink
                    attempts = 0
                    failed = False

                    def fail_recovery_once(path, *args, **kwargs):
                        nonlocal attempts, failed
                        if ".recovery.codex-install-" in Path(path).name:
                            attempts += 1
                            if not failed and attempts == failure_position:
                                failed = True
                                raise error_type("injected recovery cleanup failure")
                        return real_unlink(path, *args, **kwargs)

                    with patch(
                        "scripts.install.os.unlink", side_effect=fail_recovery_once
                    ):
                        result = install(COLLECTION, destination)

                    self.assertTrue(
                        any(
                            "recovery cleanup failure" in error
                            for error in result.errors
                        ),
                        result.errors,
                    )
                    self.assertFalse(result.ok)
                    self.assertEqual((), result.created)
                    self.assertEqual((), result.updated)
                    self.assertEqual((), result.warnings)
                    self.assert_only_original_links(destination, raw_targets)
                    self.assertEqual(
                        [], list(destination.glob(".*.codex-install-*"))
                    )

    def test_persistent_exchange_failure_preserves_manual_recovery_material(self):
        self.make_stale_managed_links(self.destination, ("agent-reach",))
        existing = self.destination / "agent-reach"
        from scripts import install as install_module

        real_exchange = install_module._atomic_exchange
        calls = 0
        concurrent_inode: int | None = None

        def fail_exchange_back_and_retries(handle, first, second):
            nonlocal calls, concurrent_inode
            calls += 1
            if calls == 1:
                handle.child_unlink(existing)
                assert handle.fd is not None
                write_child_file(
                    handle.fd, existing.name, b"concurrent fallback file\n"
                )
                concurrent_inode = existing.lstat().st_ino
                return real_exchange(handle, first, second)
            raise OSError("injected unavailable exchange-back")

        with (
            patch(
                "scripts.install._atomic_exchange",
                side_effect=fail_exchange_back_and_retries,
            ),
            patch(
                "scripts.install.os.replace",
                side_effect=AssertionError("rollback must never overwrite"),
            ),
        ):
            result = install(COLLECTION, self.destination)

        self.assertTrue(
            any("unavailable exchange-back" in error for error in result.errors),
            result.errors,
        )
        self.assertEqual(4, calls)
        self.assertIsNotNone(concurrent_inode)
        self.assertTrue(existing.is_symlink())
        recovery = [
            path
            for path in self.destination.iterdir()
            if path.lstat().st_ino == concurrent_inode
        ]
        self.assertEqual(1, len(recovery), result.errors)
        self.assertEqual(b"concurrent fallback file\n", recovery[0].read_bytes())
        self.assertTrue(
            any("manual recovery" in error for error in result.errors), result.errors
        )

    def test_destination_replacement_during_rollback_is_never_overwritten(self):
        raw_targets = self.make_stale_managed_links(
            self.destination, ("agent-reach",)
        )
        existing = self.destination / "agent-reach"
        from scripts import install as install_module

        real_exchange = install_module._atomic_exchange
        real_prepare = install_module._prepare_ready_link
        prepare_calls = 0
        exchange_calls = 0
        personal_inode: int | None = None

        def fail_second_prepare(*args, **kwargs):
            nonlocal prepare_calls
            prepare_calls += 1
            if prepare_calls == 2:
                raise OSError("force rollback after managed update")
            return real_prepare(*args, **kwargs)

        def replace_before_rollback_exchange(handle, first, second):
            nonlocal exchange_calls, personal_inode
            exchange_calls += 1
            if exchange_calls == 2:
                handle.child_unlink(existing)
                assert handle.fd is not None
                write_child_file(
                    handle.fd,
                    existing.name,
                    b"personal replacement during rollback\n",
                )
                personal_inode = existing.lstat().st_ino
                raise OSError("destination replaced before rollback exchange")
            return real_exchange(handle, first, second)

        with (
            patch(
                "scripts.install._prepare_ready_link",
                side_effect=fail_second_prepare,
            ),
            patch(
                "scripts.install._atomic_exchange",
                side_effect=replace_before_rollback_exchange,
            ),
            patch(
                "scripts.install.os.replace",
                side_effect=AssertionError("rollback must never overwrite"),
            ),
        ):
            result = install(COLLECTION, self.destination)

        self.assertTrue(result.errors)
        self.assertIsNotNone(personal_inode)
        self.assertFalse(existing.is_symlink())
        self.assertEqual(personal_inode, existing.lstat().st_ino)
        self.assertEqual(
            b"personal replacement during rollback\n", existing.read_bytes()
        )
        recovery = [
            path
            for path in self.destination.glob(".*.codex-install-*")
            if path.is_symlink()
            and os.readlink(path) == raw_targets["agent-reach"]
        ]
        self.assertEqual(1, len(recovery), result.errors)
        self.assertTrue(
            any("manual recovery" in error for error in result.errors), result.errors
        )

    def test_exchange_back_failure_restores_concurrent_real_path(self):
        from scripts import install as install_module

        real_exchange = install_module._atomic_exchange
        for error_type in (OSError, RuntimeError):
            for failure_phase in ("before", "after"):
                with self.subTest(
                    error_type=error_type.__name__, phase=failure_phase
                ):
                    destination = (
                        self.root
                        / f"exchange-{error_type.__name__}-{failure_phase}"
                    )
                    self.make_stale_managed_links(destination, ("agent-reach",))
                    existing = destination / "agent-reach"
                    calls = 0
                    concurrent_inode: int | None = None

                    def fail_second_exchange(handle, first, second):
                        nonlocal calls, concurrent_inode
                        calls += 1
                        if calls == 1:
                            handle.child_unlink(existing)
                            assert handle.fd is not None
                            write_child_file(
                                handle.fd,
                                existing.name,
                                b"concurrent personal file\n",
                            )
                            concurrent_inode = existing.lstat().st_ino
                            return real_exchange(handle, first, second)
                        if calls == 2:
                            if failure_phase == "after":
                                real_exchange(handle, first, second)
                            raise error_type(
                                f"injected {failure_phase} exchange-back failure"
                            )
                        return real_exchange(handle, first, second)

                    with patch(
                        "scripts.install._atomic_exchange",
                        side_effect=fail_second_exchange,
                    ):
                        result = install(COLLECTION, destination)

                    self.assertTrue(
                        any("exchange-back failure" in error for error in result.errors),
                        result.errors,
                    )
                    self.assertFalse(result.ok)
                    self.assertEqual((), result.created)
                    self.assertEqual((), result.updated)
                    self.assertIsNotNone(concurrent_inode)
                    self.assertFalse(existing.is_symlink())
                    self.assertEqual(concurrent_inode, existing.lstat().st_ino)
                    self.assertEqual(
                        b"concurrent personal file\n", existing.read_bytes()
                    )
                    self.assertEqual(
                        ["agent-reach"],
                        [path.name for path in destination.iterdir()],
                    )
                    self.assertEqual(
                        [], list(destination.glob(".*.codex-install-*"))
                    )

    def test_atomic_failure_rolls_back_links_and_removes_temp_debris(self):
        self.destination.mkdir(parents=True)
        existing = self.destination / "agent-reach"
        original_target = str(COLLECTION.resolve() / "ai-evaluation-audit")
        existing.symlink_to(original_target, target_is_directory=True)
        from scripts import install as install_module

        real_publish = install_module._publish_without_overwrite
        calls = 0

        def fail_once(handle, source, destination):
            nonlocal calls
            calls += 1
            if calls == 3:
                raise OSError("injected atomic failure")
            return real_publish(handle, source, destination)

        with patch(
            "scripts.install._publish_without_overwrite", side_effect=fail_once
        ):
            result = install(COLLECTION, self.destination)

        self.assertTrue(any("injected atomic failure" in error for error in result.errors))
        self.assertEqual((), result.created)
        self.assertEqual((), result.updated)
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
            if not injected and ".agent-reach.stage.codex-install-" in target.name:
                injected = True
                write_child_file(
                    kwargs["dir_fd"],
                    "agent-reach",
                    b"appeared concurrently\n",
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

        real_stage = install_module._prepare_ready_link
        calls = 0

        def fail_second(*args, **kwargs):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise RuntimeError("injected strict resolution failure")
            return real_stage(*args, **kwargs)

        with patch("scripts.install._prepare_ready_link", side_effect=fail_second):
            result = install(COLLECTION, self.destination)

        self.assertTrue(
            any("strict resolution failure" in error for error in result.errors)
        )
        self.assertEqual((), result.created)
        self.assertFalse(self.destination.exists())

    def test_ordinary_base_exceptions_return_structured_errors_after_rollback(self):
        from scripts import install as install_module

        real_prepare = install_module._prepare_ready_link
        for error_type in (ValueError, AssertionError):
            with self.subTest(error_type=error_type.__name__):
                destination = self.root / f"ordinary-{error_type.__name__}"
                calls = 0

                def fail_second(*args, **kwargs):
                    nonlocal calls
                    calls += 1
                    if calls == 2:
                        raise error_type("injected ordinary mutation failure")
                    return real_prepare(*args, **kwargs)

                with patch(
                    "scripts.install._prepare_ready_link", side_effect=fail_second
                ):
                    result = install(COLLECTION, destination)

                self.assertTrue(
                    any("ordinary mutation failure" in error for error in result.errors),
                    result.errors,
                )
                self.assertEqual((), result.created)
                self.assertFalse(destination.exists())

    def test_interrupts_are_reraised_only_after_publication_rollback(self):
        from scripts import install as install_module

        real_publish = install_module._publish_without_overwrite
        for error_type in (KeyboardInterrupt, SystemExit):
            with self.subTest(error_type=error_type.__name__):
                destination = self.root / f"interrupt-{error_type.__name__}"
                calls = 0

                def interrupt_second(handle, first, second):
                    nonlocal calls
                    calls += 1
                    if calls == 2:
                        raise error_type("injected publication interrupt")
                    return real_publish(handle, first, second)

                with (
                    patch(
                        "scripts.install._publish_without_overwrite",
                        side_effect=interrupt_second,
                    ),
                    self.assertRaises(error_type),
                ):
                    install(COLLECTION, destination)

                self.assertFalse(destination.exists())

    def test_cleanup_interrupt_is_reraised_after_retry_removes_debris(self):
        real_unlink = os.unlink
        interrupted = False

        def interrupt_ready_cleanup(path, *args, **kwargs):
            nonlocal interrupted
            if (
                not interrupted
                and ".ready.codex-install-" in Path(path).name
            ):
                interrupted = True
                raise KeyboardInterrupt("injected cleanup interrupt")
            return real_unlink(path, *args, **kwargs)

        with (
            patch("scripts.install.os.unlink", side_effect=interrupt_ready_cleanup),
            self.assertRaises(KeyboardInterrupt),
        ):
            install(COLLECTION, self.destination)

        self.assertFalse(self.destination.exists())

    def test_syscall_succeeded_then_exception_is_enrolled_for_cleanup(self):
        real_symlink = os.symlink
        real_link = os.link
        real_mkdir = os.mkdir
        scenarios = ("mkdir", "stage", "ready", "backup", "recovery")
        for scenario in scenarios:
            for error_type in (KeyboardInterrupt, SystemExit, ValueError):
                with self.subTest(scenario=scenario, error_type=error_type.__name__):
                    destination = self.root / f"post-{scenario}-{error_type.__name__}"
                    raw_targets: dict[str, str] = {}
                    if scenario in ("backup", "recovery"):
                        raw_targets = self.make_stale_managed_links(
                            destination, ("agent-reach",)
                        )
                    raised = False

                    def mkdir_then_raise(path, *args, **kwargs):
                        nonlocal raised
                        result = real_mkdir(path, *args, **kwargs)
                        if (
                            not raised
                            and scenario == "mkdir"
                            and Path(path).name == destination.name
                        ):
                            raised = True
                            raise error_type("injected exception after mkdir")
                        return result

                    def symlink_then_raise(source, target, *args, **kwargs):
                        nonlocal raised
                        result = real_symlink(source, target, *args, **kwargs)
                        if (
                            not raised
                            and scenario == "stage"
                            and ".stage.codex-install-" in Path(target).name
                        ):
                            raised = True
                            raise error_type("injected exception after stage symlink")
                        return result

                    def hardlink_then_raise(source, target, *args, **kwargs):
                        nonlocal raised
                        result = real_link(source, target, *args, **kwargs)
                        if (
                            not raised
                            and f".{scenario}.codex-install-" in Path(target).name
                        ):
                            raised = True
                            raise error_type(
                                f"injected exception after {scenario} hardlink"
                            )
                        return result

                    context = (
                        self.assertRaises(error_type)
                        if not issubclass(error_type, Exception)
                        else redirect_stdout(io.StringIO())
                    )
                    with (
                        patch("scripts.install.os.mkdir", side_effect=mkdir_then_raise),
                        patch("scripts.install.os.symlink", side_effect=symlink_then_raise),
                        patch("scripts.install.os.link", side_effect=hardlink_then_raise),
                        context,
                    ):
                        result = install(COLLECTION, destination)

                    self.assertTrue(raised)
                    if issubclass(error_type, Exception):
                        self.assertTrue(result.errors)
                    if raw_targets:
                        self.assert_only_original_links(destination, raw_targets)
                    else:
                        self.assertFalse(destination.exists())
                    if destination.exists():
                        self.assertEqual(
                            [], list(destination.glob(".*.codex-install-*"))
                        )

    def test_destination_swap_during_publish_does_not_write_or_hide_debris(self):
        from scripts import install as install_module

        real_publish = install_module._publish_without_overwrite
        moved = self.root / "moved-destination"
        swapped = False

        def swap_then_publish(*args, **kwargs):
            nonlocal swapped
            if not swapped:
                swapped = True
                self.destination.rename(moved)
                self.destination.mkdir()
                (self.destination / "personal.txt").write_bytes(b"personal\n")
            return real_publish(*args, **kwargs)

        with patch(
            "scripts.install._publish_without_overwrite", side_effect=swap_then_publish
        ):
            result = install(COLLECTION, self.destination)

        self.assertTrue(result.errors)
        self.assertEqual(b"personal\n", (self.destination / "personal.txt").read_bytes())
        self.assertEqual([], list(moved.glob(".*.codex-install-*")))
        self.assertEqual(
            [],
            [path for path in moved.iterdir() if path.name in result.planned_created],
        )

    def test_destination_swap_during_cleanup_uses_opened_directory(self):
        real_unlink = os.unlink
        moved = self.root / "cleanup-moved-destination"
        swapped = False

        def swap_then_unlink(path, *args, **kwargs):
            nonlocal swapped
            if not swapped and ".ready.codex-install-" in Path(path).name:
                swapped = True
                self.destination.rename(moved)
                self.destination.mkdir()
                (self.destination / "personal.txt").write_bytes(b"personal cleanup\n")
            return real_unlink(path, *args, **kwargs)

        with patch("scripts.install.os.unlink", side_effect=swap_then_unlink):
            result = install(COLLECTION, self.destination)

        self.assertTrue(result.errors)
        self.assertEqual(
            b"personal cleanup\n", (self.destination / "personal.txt").read_bytes()
        )
        self.assertEqual([], list(moved.glob(".*.codex-install-*")))
        self.assertEqual(
            [],
            [path for path in moved.iterdir() if path.name in result.planned_created],
        )

    def test_ancestor_replacement_during_traversal_never_redirects_creation(self):
        anchor = self.root / "walk-anchor"
        original_parent = anchor / "parent"
        original_parent.mkdir(parents=True)
        moved_anchor = self.root / "walk-anchor-moved"
        real_open = os.open
        swapped = False

        def swap_ancestor_before_open(path, flags, *args, **kwargs):
            nonlocal swapped
            if not swapped and Path(path).name == "parent" and kwargs.get("dir_fd"):
                swapped = True
                anchor.rename(moved_anchor)
                replacement_parent = anchor / "parent"
                replacement_parent.mkdir(parents=True)
                (replacement_parent / "personal.txt").write_bytes(b"replacement\n")
            return real_open(path, flags, *args, **kwargs)

        with patch("scripts.install.os.open", side_effect=swap_ancestor_before_open):
            result = install(COLLECTION, anchor / "parent" / "skills")

        self.assertTrue(result.errors)
        replacement = anchor / "parent"
        self.assertEqual(b"replacement\n", (replacement / "personal.txt").read_bytes())
        self.assertFalse((replacement / "skills").exists())
        self.assertFalse((moved_anchor / "parent" / "skills").exists())

    def test_installed_validator_observes_all_managed_links(self):
        install(COLLECTION, self.destination)

        report = validate_collection(
            REPOSITORY_ROOT,
            installed=self.destination,
            collect_evidence=False,
            structural_only=True,
        )

        self.assertTrue(report.ok, report.errors)
        self.assertEqual(59, report.installed_count)
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
        self.assertEqual(58, report.installed_count)
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
            self.assertEqual([], payload["created"])
            self.assertEqual(59, len(payload["planned_created"]))
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
            self.assertEqual([], payload["created"])
            self.assertEqual(58, len(payload["planned_created"]))

    def test_text_collision_summary_does_not_claim_planned_links_were_created(self):
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "skills"
            destination.mkdir()
            (destination / "agent-reach").write_text(
                "collision\n", encoding="utf-8"
            )
            stdout = io.StringIO()
            with redirect_stdout(stdout), redirect_stderr(io.StringIO()):
                exit_code = main(
                    ["--source", str(COLLECTION), "--dest", str(destination)]
                )

            self.assertEqual(1, exit_code)
            self.assertIn("Applied: created 0", stdout.getvalue())
            self.assertIn("Planned: create 58", stdout.getvalue())

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

    def test_cli_supports_repeatable_exclusions(self):
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "skills"
            stdout = io.StringIO()
            stderr = io.StringIO()
            with redirect_stdout(stdout), redirect_stderr(stderr):
                try:
                    exit_code = main(
                        [
                            "--source",
                            str(COLLECTION),
                            "--dest",
                            str(destination),
                            "--exclude",
                            "last30days",
                            "--exclude",
                            "agent-reach",
                            "--dry-run",
                            "--json",
                        ]
                    )
                except SystemExit as error:
                    exit_code = error.code

            self.assertEqual(0, exit_code, stderr.getvalue())
            payload = json.loads(stdout.getvalue())
            self.assertEqual(["agent-reach", "last30days"], payload["excluded"])
            self.assertEqual(57, len(payload["planned_created"]))
            self.assertFalse(destination.exists())

    def test_text_output_names_excluded_skills(self):
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "skills"
            stdout = io.StringIO()
            with redirect_stdout(stdout), redirect_stderr(io.StringIO()):
                exit_code = main(
                    [
                        "--source",
                        str(COLLECTION),
                        "--dest",
                        str(destination),
                        "--exclude",
                        "last30days",
                        "--dry-run",
                    ]
                )

            self.assertEqual(0, exit_code)
            self.assertIn("Excluded: last30days", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
