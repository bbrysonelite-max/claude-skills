import re
import unittest
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import Mock, patch


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS_ROOT = REPOSITORY_ROOT / ".github" / "workflows"
WORKFLOW_PATH = WORKFLOWS_ROOT / "ci.yml"

CHECKOUT_ACTION = (
    "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1"
)
SETUP_PYTHON_ACTION = (
    "actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97"
)
REQUIRED_COMMANDS = [
    "python -m unittest discover -s tests -v",
    "python scripts/build.py --check",
    "python scripts/validate.py --check",
]


@dataclass(frozen=True)
class _YamlLine:
    indent: int
    content: str


def _yaml_lines(text):
    lines = []
    for raw_line in text.splitlines():
        # This workflow has no values for which a literal ``#`` is meaningful.
        # Ignoring comments keeps assertions independent of explanatory notes.
        uncommented = raw_line.split("#", 1)[0].rstrip()
        if not uncommented.strip():
            continue
        indentation = len(uncommented) - len(uncommented.lstrip(" "))
        lines.append(_YamlLine(indentation, uncommented.strip()))
    return lines


def _key_value(content):
    if content.startswith("- "):
        content = content[2:].lstrip()
    match = re.fullmatch(
        r"(?P<key>[A-Za-z0-9_-]+|'[^']+'|\"[^\"]+\"):\s*(?P<value>.*)",
        content,
    )
    if not match:
        return None
    return match.group("key").strip("'\""), match.group("value").strip()


def _children(lines, entry_index):
    parent_indent = lines[entry_index].indent
    end = entry_index + 1
    while end < len(lines) and lines[end].indent > parent_indent:
        end += 1
    return lines[entry_index + 1 : end]


def _direct_mapping(lines, parent_indent):
    candidates = [line.indent for line in lines if line.indent > parent_indent]
    if not candidates:
        return {}
    child_indent = min(candidates)
    result = {}
    for index, line in enumerate(lines):
        if line.indent != child_indent or line.content.startswith("- "):
            continue
        parsed = _key_value(line.content)
        if parsed:
            key, value = parsed
            result.setdefault(key, []).append((index, value))
    return result


def _one_entry(mapping, key):
    entries = mapping.get(key, [])
    if len(entries) != 1:
        raise ValueError(f"expected exactly one {key!r} entry, found {len(entries)}")
    return entries[0]


def _scalar(value):
    return value.strip().strip("'\"")


def _string_list(value, children):
    if value:
        if not (value.startswith("[") and value.endswith("]")):
            return [_scalar(value)]
        body = value[1:-1].strip()
        if not body:
            return []
        return [_scalar(item.strip()) for item in body.split(",")]

    list_indents = [
        line.indent for line in children if line.content.startswith("- ")
    ]
    if not list_indents:
        return []
    item_indent = min(list_indents)
    return [
        _scalar(line.content[2:].strip())
        for line in children
        if line.indent == item_indent and line.content.startswith("- ")
    ]


def _step_records(step_lines):
    item_indents = [
        line.indent for line in step_lines if line.content.startswith("- ")
    ]
    if not item_indents:
        return []
    item_indent = min(item_indents)
    starts = [
        index
        for index, line in enumerate(step_lines)
        if line.indent == item_indent and line.content.startswith("- ")
    ]
    records = []
    for position, start in enumerate(starts):
        end = starts[position + 1] if position + 1 < len(starts) else len(step_lines)
        records.append(step_lines[start:end])
    return records


def _step_mapping(step):
    first = step[0]
    field_indent = first.indent + 2
    normalized = [
        _YamlLine(field_indent, first.content[2:].lstrip()),
        *step[1:],
    ]
    return _direct_mapping(normalized, first.indent), normalized


class CiWorkflowContractTests(unittest.TestCase):
    def test_rejects_in_memory_permission_env_and_token_mutations(self):
        safe = WORKFLOW_PATH.read_text(encoding="utf-8")

        def replace_once(source, needle, replacement):
            self.assertEqual(
                source.count(needle),
                1,
                f"mutation anchor must occur exactly once: {needle!r}",
            )
            return source.replace(needle, replacement, 1)

        job_permissions = replace_once(
            safe,
            "  test:\n",
            "  test:\n    permissions:\n      contents: write\n",
        )
        top_level_env = replace_once(
            safe,
            "\npermissions:\n",
            "\nenv:\n  PYTHONDONTWRITEBYTECODE: 1\n\npermissions:\n",
        )
        step_env = replace_once(
            safe,
            f"      - uses: {CHECKOUT_ACTION}\n",
            f"      - uses: {CHECKOUT_ACTION}\n"
            "        env:\n"
            "          PYTHONDONTWRITEBYTECODE: 1\n",
        )
        unexpected_job_env = replace_once(
            safe,
            "      PYTHONDONTWRITEBYTECODE: 1\n",
            "      PYTHONDONTWRITEBYTECODE: 1\n"
            "      UNEXPECTED_ENV: 1\n",
        )
        wrong_job_env_value = replace_once(
            safe,
            "      PYTHONDONTWRITEBYTECODE: 1\n",
            "      PYTHONDONTWRITEBYTECODE: 0\n",
        )
        group = (
            "  group: ${{ github.workflow }}-"
            "${{ github.event.pull_request.number || github.ref }}\n"
        )
        github_token = replace_once(
            safe,
            group,
            group.rstrip("\n") + "-${{ github.token }}\n",
        )
        gh_token = replace_once(
            safe,
            group,
            group.rstrip("\n") + "-${{ env.GH_TOKEN }}\n",
        )
        github_token_env = replace_once(
            safe,
            group,
            group.rstrip("\n") + "-${{ env.GITHUB_TOKEN }}\n",
        )
        combined = replace_once(
            job_permissions,
            "      PYTHONDONTWRITEBYTECODE: 1\n",
            "      PYTHONDONTWRITEBYTECODE: 1\n"
            "      GH_TOKEN: ${{ github.token }}\n",
        )

        mutations = (
            ("job permissions", job_permissions, "job-level permissions"),
            ("top-level env", top_level_env, "top-level env"),
            ("step env", step_env, "step-level env"),
            ("unexpected job env", unexpected_job_env, "job env"),
            ("wrong job env value", wrong_job_env_value, "job env"),
            ("github.token", github_token, "token references"),
            ("GH_TOKEN", gh_token, "token references"),
            ("GITHUB_TOKEN", github_token_env, "token references"),
            ("combined reviewer mutation", combined, "job-level permissions"),
        )

        for name, unsafe, expected_failure in mutations:
            with self.subTest(name=name):
                mutated_path = Mock()
                mutated_path.is_file.return_value = True
                mutated_path.read_text.return_value = unsafe
                with (
                    patch.dict(globals(), {"WORKFLOW_PATH": mutated_path}),
                    self.assertRaisesRegex(AssertionError, expected_failure),
                ):
                    self.test_ci_workflow_is_least_privilege_and_runs_all_deterministic_gates()

    def test_ci_workflow_is_least_privilege_and_runs_all_deterministic_gates(self):
        self.assertTrue(
            WORKFLOW_PATH.is_file(),
            "required CI workflow is missing at .github/workflows/ci.yml",
        )
        workflow_files = sorted(
            path.relative_to(REPOSITORY_ROOT).as_posix()
            for path in WORKFLOWS_ROOT.glob("*.y*ml")
        )
        self.assertEqual(workflow_files, [".github/workflows/ci.yml"])

        text = WORKFLOW_PATH.read_text(encoding="utf-8")
        lines = _yaml_lines(text)

        try:
            root = _direct_mapping(lines, -1)
            _, name = _one_entry(root, "name")
            on_index, on_value = _one_entry(root, "on")
            permissions_index, permissions_value = _one_entry(root, "permissions")
            concurrency_index, concurrency_value = _one_entry(root, "concurrency")
            jobs_index, jobs_value = _one_entry(root, "jobs")
        except ValueError as error:
            self.fail(f"workflow top-level structure is invalid: {error}")

        self.assertEqual(_scalar(name), "CI")
        self.assertEqual(on_value, "")
        self.assertEqual(permissions_value, "")
        self.assertEqual(concurrency_value, "")
        self.assertEqual(jobs_value, "")
        self.assertNotIn("env", root, "top-level env blocks are forbidden")
        on_lines = _children(lines, on_index)
        on_mapping = _direct_mapping(on_lines, lines[on_index].indent)
        self.assertEqual(set(on_mapping), {"pull_request", "push"})
        for trigger in ("pull_request", "push"):
            trigger_index, trigger_value = _one_entry(on_mapping, trigger)
            self.assertEqual(trigger_value, "")
            trigger_lines = _children(on_lines, trigger_index)
            trigger_mapping = _direct_mapping(
                trigger_lines, on_lines[trigger_index].indent
            )
            branches_index, branches_value = _one_entry(
                trigger_mapping, "branches"
            )
            branch_lines = _children(trigger_lines, branches_index)
            self.assertEqual(_string_list(branches_value, branch_lines), ["main"])

        uncommented = "\n".join(line.content for line in lines)
        self.assertNotRegex(uncommented, r"(?m)^pull_request_target\s*:")
        self.assertNotRegex(uncommented, r"(?m)^workflow_run\s*:")

        permission_lines = _children(lines, permissions_index)
        permission_mapping = _direct_mapping(
            permission_lines, lines[permissions_index].indent
        )
        self.assertEqual(set(permission_mapping), {"contents"})
        _, contents_permission = _one_entry(permission_mapping, "contents")
        self.assertEqual(_scalar(contents_permission), "read")

        concurrency_lines = _children(lines, concurrency_index)
        concurrency_mapping = _direct_mapping(
            concurrency_lines, lines[concurrency_index].indent
        )
        _, group = _one_entry(concurrency_mapping, "group")
        _, cancel = _one_entry(concurrency_mapping, "cancel-in-progress")
        self.assertIn("github.workflow", group)
        self.assertIn("github.event.pull_request.number", group)
        self.assertIn("github.ref", group)
        self.assertEqual(_scalar(cancel).lower(), "true")

        job_lines = _children(lines, jobs_index)
        jobs = _direct_mapping(job_lines, lines[jobs_index].indent)
        self.assertEqual(len(jobs), 1, "CI must use one matrix job")
        job_name = next(iter(jobs))
        job_index, job_value = _one_entry(jobs, job_name)
        self.assertEqual(job_value, "")
        job_body = _children(job_lines, job_index)
        job_mapping = _direct_mapping(job_body, job_lines[job_index].indent)
        self.assertNotIn(
            "permissions",
            job_mapping,
            "job-level permissions overrides are forbidden",
        )

        _, runner = _one_entry(job_mapping, "runs-on")
        _, timeout = _one_entry(job_mapping, "timeout-minutes")
        self.assertEqual(_scalar(runner), "ubuntu-24.04")
        self.assertEqual(_scalar(timeout), "15")

        strategy_index, strategy_value = _one_entry(job_mapping, "strategy")
        self.assertEqual(strategy_value, "")
        strategy_lines = _children(job_body, strategy_index)
        strategy_mapping = _direct_mapping(
            strategy_lines, job_body[strategy_index].indent
        )
        _, fail_fast = _one_entry(strategy_mapping, "fail-fast")
        matrix_index, matrix_value = _one_entry(strategy_mapping, "matrix")
        self.assertEqual(_scalar(fail_fast).lower(), "false")
        self.assertEqual(matrix_value, "")
        matrix_lines = _children(strategy_lines, matrix_index)
        matrix_mapping = _direct_mapping(
            matrix_lines, strategy_lines[matrix_index].indent
        )
        python_index, python_versions = _one_entry(
            matrix_mapping, "python-version"
        )
        version_lines = _children(matrix_lines, python_index)
        self.assertEqual(
            _string_list(python_versions, version_lines), ["3.11.15", "3.14.5"]
        )

        env_index, env_value = _one_entry(job_mapping, "env")
        self.assertEqual(env_value, "")
        env_lines = _children(job_body, env_index)
        env_mapping = _direct_mapping(env_lines, job_body[env_index].indent)
        self.assertEqual(
            set(env_mapping),
            {"PYTHONDONTWRITEBYTECODE"},
            "job env must contain only PYTHONDONTWRITEBYTECODE",
        )
        _, dont_write_bytecode = _one_entry(
            env_mapping, "PYTHONDONTWRITEBYTECODE"
        )
        self.assertEqual(
            _scalar(dont_write_bytecode),
            "1",
            "job env PYTHONDONTWRITEBYTECODE must equal 1",
        )

        def effective_nested_value(first_key, second_key):
            for scope, parent_indent in (
                (job_body, job_lines[job_index].indent),
                (lines, -1),
            ):
                mapping = _direct_mapping(scope, parent_indent)
                if first_key not in mapping:
                    continue
                first_index, first_value = _one_entry(mapping, first_key)
                self.assertEqual(first_value, "")
                nested_lines = _children(scope, first_index)
                nested_mapping = _direct_mapping(
                    nested_lines, scope[first_index].indent
                )
                if second_key in nested_mapping:
                    _, value = _one_entry(nested_mapping, second_key)
                    return _scalar(value)
            self.fail(f"missing effective {first_key}.{second_key}")

        self.assertEqual(
            effective_nested_value("env", "PYTHONDONTWRITEBYTECODE"), "1"
        )

        working_directory = None
        for scope, parent_indent in (
            (job_body, job_lines[job_index].indent),
            (lines, -1),
        ):
            mapping = _direct_mapping(scope, parent_indent)
            if "defaults" not in mapping:
                continue
            defaults_index, defaults_value = _one_entry(mapping, "defaults")
            self.assertEqual(defaults_value, "")
            defaults_lines = _children(scope, defaults_index)
            defaults_mapping = _direct_mapping(
                defaults_lines, scope[defaults_index].indent
            )
            run_index, run_value = _one_entry(defaults_mapping, "run")
            self.assertEqual(run_value, "")
            run_lines = _children(defaults_lines, run_index)
            run_mapping = _direct_mapping(
                run_lines, defaults_lines[run_index].indent
            )
            _, working_directory = _one_entry(
                run_mapping, "working-directory"
            )
            working_directory = _scalar(working_directory)
            break
        self.assertEqual(working_directory, "codex-skills")

        steps_index, steps_value = _one_entry(job_mapping, "steps")
        self.assertEqual(steps_value, "")
        steps = _step_records(_children(job_body, steps_index))
        self.assertEqual(len(steps), 5, "expected two actions and three run gates")

        action_steps = []
        run_commands = []
        for step in steps:
            step_mapping, normalized_step = _step_mapping(step)
            self.assertNotIn(
                "env", step_mapping, "step-level env blocks are forbidden"
            )
            if "uses" in step_mapping:
                _, action = _one_entry(step_mapping, "uses")
                action_steps.append((_scalar(action), step_mapping, normalized_step))
            if "run" in step_mapping:
                _, command = _one_entry(step_mapping, "run")
                run_commands.append(_scalar(command))

        self.assertEqual(
            [action for action, _, _ in action_steps],
            [CHECKOUT_ACTION, SETUP_PYTHON_ACTION],
        )
        self.assertEqual(run_commands, REQUIRED_COMMANDS)
        for action, _, _ in action_steps:
            self.assertRegex(action.rsplit("@", 1)[1], r"^[0-9a-f]{40}$")

        checkout_mapping, checkout_step = action_steps[0][1:]
        checkout_with_index, checkout_with_value = _one_entry(
            checkout_mapping, "with"
        )
        self.assertEqual(checkout_with_value, "")
        checkout_with_lines = _children(checkout_step, checkout_with_index)
        checkout_with = _direct_mapping(
            checkout_with_lines, checkout_step[checkout_with_index].indent
        )
        _, persist_credentials = _one_entry(
            checkout_with, "persist-credentials"
        )
        self.assertEqual(_scalar(persist_credentials).lower(), "false")

        setup_mapping, setup_step = action_steps[1][1:]
        setup_with_index, setup_with_value = _one_entry(setup_mapping, "with")
        self.assertEqual(setup_with_value, "")
        setup_with_lines = _children(setup_step, setup_with_index)
        setup_with = _direct_mapping(
            setup_with_lines, setup_step[setup_with_index].indent
        )
        _, selected_python = _one_entry(setup_with, "python-version")
        self.assertEqual(_scalar(selected_python), "${{ matrix.python-version }}")

        lower = uncommented.lower()
        self.assertNotRegex(lower, r"\bsecrets?\b")
        self.assertNotRegex(lower, r"\bcache\b")
        self.assertNotRegex(lower, r"\bpip(?:3|x)?\b")
        self.assertNotRegex(lower, r"\buv\b")
        self.assertNotRegex(lower, r"\b(curl|wget|npm|npx|brew|gh|aws|gcloud)\b")
        self.assertNotRegex(
            lower,
            r"\b(?:gh_token|github_token)\b|github\s*\.\s*token\b",
            "GitHub token references or github.token exposure are forbidden",
        )
        credential_lines = [
            line.content
            for line in lines
            if re.search(r"\bcredentials?\b", line.content, re.IGNORECASE)
        ]
        self.assertEqual(credential_lines, ["persist-credentials: false"])


if __name__ == "__main__":
    unittest.main()
