import tempfile
from pathlib import Path
import unittest

from ai_coding_agent.context_builder import build_context_pack
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

    def test_context_builder(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "app.py").write_text("x = 1\n", encoding="utf-8")
            (root / "tests").mkdir()
            (root / "tests" / "test_app.py").write_text("assert True\n", encoding="utf-8")
            task = TaskSpec.from_text("app.py | pytest | tests/test_app.py | Update x")
            context_path = build_context_pack(root, task, root / "workspace")
            self.assertTrue(context_path.exists())

