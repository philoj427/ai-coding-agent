import tempfile
from pathlib import Path
import unittest
from unittest import mock

from ai_coding_agent.context_builder import build_context_pack
from ai_coding_agent.builder import build_prompt
from ai_coding_agent.builder import _strip_code_fences
from ai_coding_agent.gatekeeper import GatekeeperError, inspect_patch
from ai_coding_agent.git_guard import GitGuardError, ensure_clean_worktree, validate_allowed_changes
from ai_coding_agent.patch_applier import PatchParseError
from ai_coding_agent.patch_applier import apply_search_replace_patch
from ai_coding_agent.patch_parser import parse_search_replace_patch
from ai_coding_agent.task import TaskSpec
from ai_coding_agent.workflow import run_workflow


class TestCore(unittest.TestCase):
    def test_build_prompt_is_strict_and_compact(self):
        prompt = build_prompt("context")
        self.assertIn("Output only one SEARCH/REPLACE patch.", prompt)
        self.assertIn("Preserve exact indentation and whitespace.", prompt)
        self.assertIn("Patch must change the target file contents.", prompt)
        self.assertIn("Do not change indentation on a line unless the line content also changes.", prompt)
        self.assertTrue(prompt.endswith("\n"))

    def test_strip_code_fences(self):
        patch = "```text\nSEARCH\nold\nEND_SEARCH\nREPLACE\nnew\nEND_REPLACE\n```\n"
        self.assertEqual(
            _strip_code_fences(patch),
            "SEARCH\nold\nEND_SEARCH\nREPLACE\nnew\nEND_REPLACE",
        )

    def test_task_parse(self):
        task = TaskSpec.from_text("app.py | pytest | tests/test_app.py | Implement divide")
        self.assertEqual(task.target_file, Path("app.py"))
        self.assertEqual(task.test_type, "pytest")
        self.assertEqual(task.test_file, Path("tests/test_app.py"))

    def test_patch_parse(self):
        patch = "SEARCH\nold\nEND_SEARCH\nREPLACE\nnew\nEND_REPLACE\n"
        self.assertEqual(parse_search_replace_patch(patch), [("old", "new")])

    def test_patch_apply(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            target = root / "app.py"
            target.write_text("value = 1\n", encoding="utf-8")
            patch = "SEARCH\nvalue = 1\nEND_SEARCH\nREPLACE\nvalue = 2\nEND_REPLACE\n"
            result = apply_search_replace_patch(target, patch)
            self.assertTrue(result.applied)
            self.assertEqual(target.read_text(encoding="utf-8"), "value = 2\n")

    def test_patch_apply_preserves_indentation_in_search_block(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            target = root / "app.py"
            target.write_text(
                "def outer():\n"
                "    def inner():\n"
                "        return 1\n"
                "    return inner()\n",
                encoding="utf-8",
            )
            patch = (
                "SEARCH\n"
                "    def inner():\n"
                "        return 1\n"
                "END_SEARCH\n"
                "REPLACE\n"
                "    def inner():\n"
                "        return 2\n"
                "END_REPLACE\n"
            )
            apply_search_replace_patch(target, patch)
            self.assertIn("        return 2\n", target.read_text(encoding="utf-8"))

    def test_patch_apply_raises_when_search_matches_multiple_locations(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            target = root / "app.py"
            target.write_text(
                "def add(a, b):\n"
                "    return a + b\n\n"
                "def add_twice(a, b):\n"
                "    return a + b\n",
                encoding="utf-8",
            )
            patch = (
                "SEARCH\n"
                "    return a + b\n"
                "END_SEARCH\n"
                "REPLACE\n"
                "    return a - b\n"
                "END_REPLACE\n"
            )
            with self.assertRaises(PatchParseError):
                apply_search_replace_patch(target, patch)

    def test_patch_apply_raises_when_search_not_found(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            target = root / "app.py"
            target.write_text("value = 1\n", encoding="utf-8")
            patch = (
                "SEARCH\n"
                "missing_value = 1\n"
                "END_SEARCH\n"
                "REPLACE\n"
                "value = 2\n"
                "END_REPLACE\n"
            )
            with self.assertRaises(PatchParseError):
                apply_search_replace_patch(target, patch)

    def test_patch_apply_rejects_indentation_only_changes(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            target = root / "app.py"
            target.write_text("def add(a, b):\n    return a + b\n", encoding="utf-8")
            patch = (
                "SEARCH\n"
                "    return a + b\n"
                "END_SEARCH\n"
                "REPLACE\n"
                "        return a + b\n"
                "END_REPLACE\n"
            )
            with self.assertRaises(PatchParseError):
                apply_search_replace_patch(target, patch)

    def test_patch_apply_rejects_line_level_indentation_only_changes(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            target = root / "app.py"
            target.write_text(
                "def add(a, b):\n"
                "    return a + b\n",
                encoding="utf-8",
            )
            patch = (
                "SEARCH\n"
                "def add(a, b):\n"
                "    return a + b\n"
                "END_SEARCH\n"
                "REPLACE\n"
                "def add(a, b):\n"
                "        return a + b\n"
                "END_REPLACE\n"
            )
            with self.assertRaises(PatchParseError):
                apply_search_replace_patch(target, patch)

    def test_patch_apply_rejects_no_op_patch(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            target = root / "app.py"
            target.write_text("value = 1\n", encoding="utf-8")
            patch = (
                "SEARCH\n"
                "value = 1\n"
                "END_SEARCH\n"
                "REPLACE\n"
                "value = 1\n"
                "END_REPLACE\n"
            )
            with self.assertRaises(PatchParseError):
                apply_search_replace_patch(target, patch)

    def test_gatekeeper_rejects_no_op_patch(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            target = root / "app.py"
            target.write_text("value = 1\n", encoding="utf-8")
            patch = (
                "SEARCH\n"
                "value = 1\n"
                "END_SEARCH\n"
                "REPLACE\n"
                "value = 1\n"
                "END_REPLACE\n"
            )
            with self.assertRaises(GatekeeperError):
                inspect_patch(target, patch)

    def test_gatekeeper_rejects_duplicate_top_level_function_names(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            target = root / "app.py"
            target.write_text(
                "def add(a, b):\n"
                "    return a + b\n",
                encoding="utf-8",
            )
            patch = (
                "SEARCH\n"
                "def add(a, b):\n"
                "    return a + b\n"
                "END_SEARCH\n"
                "REPLACE\n"
                "def add(a, b):\n"
                "    return a + b\n\n"
                "def add(a, b):\n"
                "    return a + b\n"
                "END_REPLACE\n"
            )
            with self.assertRaises(GatekeeperError):
                inspect_patch(target, patch)

    def test_gatekeeper_rejects_docstring_glued_to_def(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            target = root / "app.py"
            target.write_text(
                '"""Module docs."""\n\n'
                "def add(a, b):\n"
                "    return a + b\n",
                encoding="utf-8",
            )
            patch = (
                "SEARCH\n"
                '"""Module docs."""\n\n'
                "def add(a, b):\n"
                "    return a + b\n"
                "END_SEARCH\n"
                "REPLACE\n"
                '"""Module docs."""\n'
                "def add(a, b):\n"
                "    return a + b\n"
                "END_REPLACE\n"
            )
            with self.assertRaises(GatekeeperError):
                inspect_patch(target, patch)

    def test_context_builder(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "app.py").write_text("x = 1\n", encoding="utf-8")
            (root / "tests").mkdir()
            (root / "tests" / "test_app.py").write_text("assert True\n", encoding="utf-8")
            task = TaskSpec.from_text("app.py | pytest | tests/test_app.py | Update x")
            context_path = build_context_pack(root, task, root / "workspace")
            self.assertTrue(context_path.exists())

    def test_validate_allowed_changes_blocks_unauthorized_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            self._init_git_repo(root)

            allowed = root / "allowed.py"
            other = root / "other.py"
            allowed.write_text("print('a')\n", encoding="utf-8")
            other.write_text("print('b')\n", encoding="utf-8")
            self._git(root, "add", ".")
            self._git(root, "commit", "-m", "baseline")

            allowed.write_text("print('a2')\n", encoding="utf-8")
            other.write_text("print('b2')\n", encoding="utf-8")

            with self.assertRaises(GitGuardError):
                validate_allowed_changes(root, {allowed})

    def test_validate_allowed_changes_blocks_staged_unauthorized_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            self._init_git_repo(root)

            allowed = root / "allowed.py"
            other = root / "other.py"
            allowed.write_text("print('a')\n", encoding="utf-8")
            other.write_text("print('b')\n", encoding="utf-8")
            self._git(root, "add", ".")
            self._git(root, "commit", "-m", "baseline")

            other.write_text("print('b2')\n", encoding="utf-8")
            self._git(root, "add", "other.py")

            with self.assertRaises(GitGuardError):
                validate_allowed_changes(root, {allowed})

    def test_validate_allowed_changes_blocks_untracked_unauthorized_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            self._init_git_repo(root)

            allowed = root / "allowed.py"
            allowed.write_text("print('a')\n", encoding="utf-8")
            self._git(root, "add", ".")
            self._git(root, "commit", "-m", "baseline")

            rogue = root / "rogue.py"
            rogue.write_text("print('rogue')\n", encoding="utf-8")

            with self.assertRaises(GitGuardError):
                validate_allowed_changes(root, {allowed})

    def test_ensure_clean_worktree_accepts_clean_repo(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            self._init_git_repo(root)

            sample = root / "sample.py"
            sample.write_text("print('x')\n", encoding="utf-8")
            self._git(root, "add", ".")
            self._git(root, "commit", "-m", "baseline")

            ensure_clean_worktree(root)

    def test_run_workflow_rolls_back_target_file_on_test_failure(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            self._init_git_repo(root)
            (root / ".gitignore").write_text("workspace/\n", encoding="utf-8")

            target = root / "demo.py"
            target.write_text(
                "def greet(name):\n"
                "    return f'Hello {name}'\n",
                encoding="utf-8",
            )
            task_file = root / "task.txt"
            task_file.write_text(
                "demo.py | pytest | tests/test_demo.py | Make greet add punctuation.\n",
                encoding="utf-8",
            )
            (root / "tests").mkdir()
            (root / "tests" / "test_demo.py").write_text("import unittest\n", encoding="utf-8")
            self._git(root, "add", ".")
            self._git(root, "commit", "-m", "baseline")

            patch = (
                "SEARCH\n"
                "    return f'Hello {name}'\n"
                "END_SEARCH\n"
                "REPLACE\n"
                "    return f'Hello {name}!'\n"
                "END_REPLACE\n"
            )

            class FakeResult:
                passed = False
                exit_code = 1

            with mock.patch("ai_coding_agent.workflow.generate_patch", return_value=patch), \
                 mock.patch("ai_coding_agent.workflow.run_tests", return_value=FakeResult()):
                exit_code = run_workflow(
                    root=root,
                    task_path=task_file,
                    workspace_dir=root / "workspace",
                    model="qwen2.5-coder:7b",
                    ollama_host="http://localhost:11434",
                    dry_run=False,
                )

            self.assertEqual(exit_code, 1)
            self.assertEqual(
                target.read_text(encoding="utf-8"),
                "def greet(name):\n    return f'Hello {name}'\n",
            )
            self.assertEqual(
                (root / "workspace" / "git_diff.txt").read_text(encoding="utf-8"),
                "",
            )

    def test_run_workflow_rejects_no_op_patch(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            self._init_git_repo(root)
            (root / ".gitignore").write_text("workspace/\n", encoding="utf-8")

            target = root / "demo.py"
            target.write_text(
                "def greet(name):\n"
                "    return f'Hello {name}'\n",
                encoding="utf-8",
            )
            task_file = root / "task.txt"
            task_file.write_text(
                "demo.py | pytest | tests/test_demo.py | Keep greet unchanged.\n",
                encoding="utf-8",
            )
            (root / "tests").mkdir()
            (root / "tests" / "test_demo.py").write_text("import unittest\n", encoding="utf-8")
            self._git(root, "add", ".")
            self._git(root, "commit", "-m", "baseline")

            patch = (
                "SEARCH\n"
                "    return f'Hello {name}'\n"
                "END_SEARCH\n"
                "REPLACE\n"
                "    return f'Hello {name}'\n"
                "END_REPLACE\n"
            )

            class FakeResult:
                passed = True
                exit_code = 0

            with mock.patch("ai_coding_agent.workflow.generate_patch", return_value=patch), \
                 mock.patch("ai_coding_agent.workflow.run_tests", return_value=FakeResult()) as run_tests:
                exit_code = run_workflow(
                    root=root,
                    task_path=task_file,
                    workspace_dir=root / "workspace",
                    model="qwen2.5-coder:7b",
                    ollama_host="http://localhost:11434",
                    dry_run=False,
                )

            self.assertEqual(exit_code, 1)
            run_tests.assert_not_called()
            self.assertEqual(
                target.read_text(encoding="utf-8"),
                "def greet(name):\n    return f'Hello {name}'\n",
            )
            report = (root / "workspace" / "test_result.txt").read_text(encoding="utf-8")
            self.assertIn("Stage: gatekeeper", report)
            self.assertIn(
                "SEARCH/REPLACE patch must change target file",
                report,
            )

    def test_gatekeeper_failure_report_contains_stage(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            self._init_git_repo(root)
            (root / ".gitignore").write_text("workspace/\n", encoding="utf-8")

            target = root / "demo.py"
            target.write_text(
                "def greet(name):\n"
                "    return f'Hello {name}'\n",
                encoding="utf-8",
            )
            task_file = root / "task.txt"
            task_file.write_text(
                "demo.py | pytest | tests/test_demo.py | Make greet add punctuation.\n",
                encoding="utf-8",
            )
            (root / "tests").mkdir()
            (root / "tests" / "test_demo.py").write_text("import unittest\n", encoding="utf-8")
            self._git(root, "add", ".")
            self._git(root, "commit", "-m", "baseline")

            bad_patch = (
                "SEARCH\n"
                "    return f'Hello {name}'\n"
                "END_SEARCH\n"
                "REPLACE\n"
                "    return f'Hello {name}'\n"
                "END_REPLACE\n"
            )

            class FakeResult:
                passed = True
                exit_code = 0

            with mock.patch("ai_coding_agent.workflow.generate_patch", return_value=bad_patch), \
                 mock.patch("ai_coding_agent.workflow.run_tests", return_value=FakeResult()) as run_tests:
                exit_code = run_workflow(
                    root=root,
                    task_path=task_file,
                    workspace_dir=root / "workspace",
                    model="qwen2.5-coder:7b",
                    ollama_host="http://localhost:11434",
                    dry_run=False,
                )

            self.assertEqual(exit_code, 1)
            run_tests.assert_not_called()
            report = (root / "workspace" / "test_result.txt").read_text(encoding="utf-8")
            self.assertIn("Stage: gatekeeper", report)
            self.assertIn("SEARCH/REPLACE patch must change target file", report)

    def test_run_workflow_cleans_untracked_file_on_test_failure(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            self._init_git_repo(root)
            (root / ".gitignore").write_text("workspace/\n", encoding="utf-8")

            target = root / "demo.py"
            target.write_text(
                "def greet(name):\n"
                "    return f'Hello {name}'\n",
                encoding="utf-8",
            )
            task_file = root / "task.txt"
            task_file.write_text(
                "demo.py | pytest | tests/test_demo.py | Make greet add punctuation.\n",
                encoding="utf-8",
            )
            (root / "tests").mkdir()
            (root / "tests" / "test_demo.py").write_text("import unittest\n", encoding="utf-8")
            self._git(root, "add", ".")
            self._git(root, "commit", "-m", "baseline")

            patch = (
                "SEARCH\n"
                "    return f'Hello {name}'\n"
                "END_SEARCH\n"
                "REPLACE\n"
                "    return f'Hello {name}!'\n"
                "END_REPLACE\n"
            )

            class FakeResult:
                passed = False
                exit_code = 1
                output = "temp artifact\n"

            rogue = root / "rogue.log"

            def fake_run_tests(*args, **kwargs):
                workspace_dir = args[3]
                (workspace_dir / "test_result.txt").write_text("temp artifact\n", encoding="utf-8")
                rogue.write_text("temp artifact\n", encoding="utf-8")
                return FakeResult()

            with mock.patch("ai_coding_agent.workflow.generate_patch", return_value=patch), \
                 mock.patch("ai_coding_agent.workflow.run_tests", side_effect=fake_run_tests):
                exit_code = run_workflow(
                    root=root,
                    task_path=task_file,
                    workspace_dir=root / "workspace",
                    model="qwen2.5-coder:7b",
                    ollama_host="http://localhost:11434",
                    dry_run=False,
                )

            self.assertEqual(exit_code, 1)
            self.assertFalse(rogue.exists())
            self.assertEqual(
                target.read_text(encoding="utf-8"),
                "def greet(name):\n    return f'Hello {name}'\n",
            )
            self.assertEqual(
                (root / "workspace" / "git_diff.txt").read_text(encoding="utf-8"),
                "",
            )
            report = (root / "workspace" / "test_result.txt").read_text(encoding="utf-8")
            self.assertIn("Stage: tests", report)
            self.assertIn("temp artifact", report)

    def test_run_workflow_retries_once_on_patch_parse_failure(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            self._init_git_repo(root)
            (root / ".gitignore").write_text("workspace/\n", encoding="utf-8")

            target = root / "demo.py"
            target.write_text(
                "def greet(name):\n"
                "    return f'Hello {name}'\n",
                encoding="utf-8",
            )
            task_file = root / "task.txt"
            task_file.write_text(
                "demo.py | pytest | tests/test_demo.py | Make greet add punctuation.\n",
                encoding="utf-8",
            )
            (root / "tests").mkdir()
            (root / "tests" / "test_demo.py").write_text("import unittest\n", encoding="utf-8")
            self._git(root, "add", ".")
            self._git(root, "commit", "-m", "baseline")

            bad_patch = "SEARCH\nmissing\nEND_SEARCH\nREPLACE\nx\nEND_REPLACE\n"
            good_patch = (
                "SEARCH\n"
                "    return f'Hello {name}'\n"
                "END_SEARCH\n"
                "REPLACE\n"
                "    return f'Hello {name}!'\n"
                "END_REPLACE\n"
            )

            class FakeResult:
                passed = True
                exit_code = 0

            with mock.patch("ai_coding_agent.workflow.generate_patch", side_effect=[bad_patch, good_patch]) as mock_generate, \
                 mock.patch("ai_coding_agent.workflow.run_tests", return_value=FakeResult()):
                exit_code = run_workflow(
                    root=root,
                    task_path=task_file,
                    workspace_dir=root / "workspace",
                    model="qwen2.5-coder:7b",
                    ollama_host="http://localhost:11434",
                    dry_run=False,
                )

            self.assertEqual(exit_code, 0)
            self.assertEqual(mock_generate.call_count, 2)
            self.assertIn("!", target.read_text(encoding="utf-8"))
            self.assertFalse(any(root.rglob("__pycache__")))

    def test_run_workflow_retries_once_on_gatekeeper_failure(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            self._init_git_repo(root)
            (root / ".gitignore").write_text("workspace/\n", encoding="utf-8")

            target = root / "demo.py"
            target.write_text(
                "def greet(name):\n"
                "    return f'Hello {name}'\n",
                encoding="utf-8",
            )
            task_file = root / "task.txt"
            task_file.write_text(
                "demo.py | pytest | tests/test_demo.py | Make greet add punctuation.\n",
                encoding="utf-8",
            )
            (root / "tests").mkdir()
            (root / "tests" / "test_demo.py").write_text("import unittest\n", encoding="utf-8")
            self._git(root, "add", ".")
            self._git(root, "commit", "-m", "baseline")

            bad_patch = (
                "SEARCH\n"
                "    return f'Hello {name}'\n"
                "END_SEARCH\n"
                "REPLACE\n"
                "    return f'Hello {name}'\n"
                "END_REPLACE\n"
            )
            good_patch = (
                "SEARCH\n"
                "    return f'Hello {name}'\n"
                "END_SEARCH\n"
                "REPLACE\n"
                "    return f'Hello {name}!'\n"
                "END_REPLACE\n"
            )

            class FakeResult:
                passed = True
                exit_code = 0

            with mock.patch("ai_coding_agent.workflow.generate_patch", side_effect=[bad_patch, good_patch]) as mock_generate, \
                 mock.patch("ai_coding_agent.workflow.run_tests", return_value=FakeResult()):
                exit_code = run_workflow(
                    root=root,
                    task_path=task_file,
                    workspace_dir=root / "workspace",
                    model="qwen2.5-coder:7b",
                    ollama_host="http://localhost:11434",
                    dry_run=False,
                )

            self.assertEqual(exit_code, 0)
            self.assertEqual(mock_generate.call_count, 2)
            self.assertIn("!", target.read_text(encoding="utf-8"))
            self.assertFalse(any(root.rglob("__pycache__")))

    def test_run_workflow_rolls_back_on_python_syntax_failure(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            self._init_git_repo(root)
            (root / ".gitignore").write_text("workspace/\n", encoding="utf-8")

            target = root / "demo.py"
            target.write_text(
                "def greet(name):\n"
                "    return f'Hello {name}'\n",
                encoding="utf-8",
            )
            task_file = root / "task.txt"
            task_file.write_text(
                "demo.py | pytest | tests/test_demo.py | Make greet add punctuation.\n",
                encoding="utf-8",
            )
            (root / "tests").mkdir()
            (root / "tests" / "test_demo.py").write_text("import unittest\n", encoding="utf-8")
            self._git(root, "add", ".")
            self._git(root, "commit", "-m", "baseline")

            bad_patch = (
                "SEARCH\n"
                "    return f'Hello {name}'\n"
                "END_SEARCH\n"
                "REPLACE\n"
                "    return f'Hello {name}'\n"
                "    )\n"
                "END_REPLACE\n"
            )

            class FakeResult:
                passed = True
                exit_code = 0

            with mock.patch("ai_coding_agent.workflow.generate_patch", return_value=bad_patch), \
                 mock.patch("ai_coding_agent.workflow.run_tests", return_value=FakeResult()):
                exit_code = run_workflow(
                    root=root,
                    task_path=task_file,
                    workspace_dir=root / "workspace",
                    model="qwen2.5-coder:7b",
                    ollama_host="http://localhost:11434",
                    dry_run=False,
                )

            self.assertEqual(exit_code, 1)
            self.assertEqual(
                target.read_text(encoding="utf-8"),
                "def greet(name):\n    return f'Hello {name}'\n",
            )
            self.assertEqual(
                (root / "workspace" / "git_diff.txt").read_text(encoding="utf-8"),
                "",
            )
            self.assertFalse(any(root.rglob("__pycache__")))

    def _init_git_repo(self, root: Path) -> None:
        self._git(root, "init")
        self._git(root, "config", "user.name", "Jamison")
        self._git(root, "config", "user.email", "jamison@example.com")

    def _git(self, root: Path, *args: str) -> None:
        import subprocess

        subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True, text=True)
