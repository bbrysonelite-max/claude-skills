import io
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


class InstallTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.destination = self.root / "home" / "skills"

    def tearDown(self):
        self.temporary.cleanup()

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
                "collisions": [],
                "errors": ["error"],
                "warnings": [],
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
        self.assertEqual((), result.created)
        self.assertEqual((), result.updated)
        self.assertEqual(57, len(result.planned_created))
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

        self.assertEqual((), dry.created)
        self.assertEqual(58, len(dry.planned_created))
        self.assertFalse(self.destination.exists())

        actual = install(COLLECTION, self.destination)
        self.assertEqual(58, len(actual.created))
        self.assertEqual(dry.planned_created, actual.planned_created)

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

                    def create_artifact(path: Path) -> None:
                        nonlocal artifact_path, artifact_inode, artifact_link_text
                        artifact_path = path
                        if artifact_kind == "file":
                            path.write_bytes(b"preserve collision bytes\n")
                        elif artifact_kind == "directory":
                            path.mkdir()
                            (path / "payload.txt").write_text(
                                "preserve directory\n", encoding="utf-8"
                            )
                        else:
                            artifact_link_text = str(self.root / "unrelated-target")
                            real_symlink(artifact_link_text, path)
                        artifact_inode = path.lstat().st_ino

                    def collide_symlink(source, target, *args, **kwargs):
                        target_path = Path(target)
                        if (
                            artifact_path is None
                            and location == "stage"
                            and ".stage.codex-install-" in target_path.name
                        ):
                            create_artifact(target_path)
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
                            create_artifact(target_path)
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
            candidate = Path(target)
            if attacker_path is None and ".stage.codex-install-" in candidate.name:
                candidate.unlink()
                candidate.write_bytes(b"attacker stage bytes\n")
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
            candidate = Path(target)
            if attacker_path is None and ".ready.codex-install-" in candidate.name:
                candidate.unlink()
                candidate.write_bytes(b"attacker ready bytes\n")
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
            source_path = Path(source)
            target_path = Path(target)
            if (
                attacker_stage is None
                and ".ready.codex-install-" in target_path.name
            ):
                source_path.unlink()
                source_path.write_bytes(b"attacker source-stage bytes\n")
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

        def observe_exchange(first, second):
            checkpoints.append(os.path.lexists(existing))
            real_exchange(first, second)
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

        def replace_before_exchange(first, second):
            nonlocal injected
            if not injected:
                injected = True
                existing.unlink()
                existing.write_bytes(b"concurrent personal file\n")
            real_exchange(first, second)

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

        def publish_then_raise(first, second):
            nonlocal raised
            real_publish(first, second)
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

        def exchange_then_raise(first, second):
            nonlocal raised
            real_exchange(first, second)
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

        def fail_exchange_back_and_retries(first, second):
            nonlocal calls, concurrent_inode
            calls += 1
            if calls == 1:
                existing.unlink()
                existing.write_bytes(b"concurrent fallback file\n")
                concurrent_inode = existing.lstat().st_ino
                return real_exchange(first, second)
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

        def replace_before_rollback_exchange(first, second):
            nonlocal exchange_calls, personal_inode
            exchange_calls += 1
            if exchange_calls == 2:
                existing.unlink()
                existing.write_bytes(b"personal replacement during rollback\n")
                personal_inode = existing.lstat().st_ino
                raise OSError("destination replaced before rollback exchange")
            return real_exchange(first, second)

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

                    def fail_second_exchange(first, second):
                        nonlocal calls, concurrent_inode
                        calls += 1
                        if calls == 1:
                            existing.unlink()
                            existing.write_bytes(b"concurrent personal file\n")
                            concurrent_inode = existing.lstat().st_ino
                            return real_exchange(first, second)
                        if calls == 2:
                            if failure_phase == "after":
                                real_exchange(first, second)
                            raise error_type(
                                f"injected {failure_phase} exchange-back failure"
                            )
                        return real_exchange(first, second)

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

        def fail_once(source, destination):
            nonlocal calls
            calls += 1
            if calls == 3:
                raise OSError("injected atomic failure")
            return real_publish(source, destination)

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

                def interrupt_second(first, second):
                    nonlocal calls
                    calls += 1
                    if calls == 2:
                        raise error_type("injected publication interrupt")
                    return real_publish(first, second)

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
            self.assertEqual([], payload["created"])
            self.assertEqual(58, len(payload["planned_created"]))
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
            self.assertEqual(57, len(payload["planned_created"]))

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
            self.assertIn("Planned: create 57", stdout.getvalue())

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
