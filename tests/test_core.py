import tempfile
from pathlib import Path
import unittest

from ai_coding_agent.context_builder import build_context_pack
from ai_coding_agent.git_guard import GitGuardError, ensure_clean_worktree, validate_allowed_changes
from ai_coding_agent.patch_applier import apply_search_replace_patch
from ai_coding_agent.patch_parser import parse_search_replace_patch
from ai_coding_agent.task import TaskSpec


class TestCore(unittest.TestCase):
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

    def test_ensure_clean_worktree_accepts_clean_repo(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            self._init_git_repo(root)

            sample = root / "sample.py"
            sample.write_text("print('x')\n", encoding="utf-8")
            self._git(root, "add", ".")
            self._git(root, "commit", "-m", "baseline")

            ensure_clean_worktree(root)

    def _init_git_repo(self, root: Path) -> None:
        self._git(root, "init")
        self._git(root, "config", "user.name", "Jamison")
        self._git(root, "config", "user.email", "jamison@example.com")

    def _git(self, root: Path, *args: str) -> None:
        import subprocess

        subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True, text=True)
