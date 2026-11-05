"""The starter must never overwrite an official project or leak local build files."""

import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


KIT_PATH = Path(__file__).resolve().parents[1] / "scripts/kit.py"
SPEC = importlib.util.spec_from_file_location("scaffold_kit", KIT_PATH)
kit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(kit)


class ScaffoldTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name).resolve()
        self.source = self.base / "kit"
        self.root = self.base / "task"
        self.root.mkdir()
        self.starter = self.source / "starters/nextjs"
        self.starter.mkdir(parents=True)
        self.files = ("package.json", "app/page.tsx", ".env.example")
        for name, value in zip(self.files, (b'{"name":"fictional-starter"}\n', b"// fixture\n", b"EXAMPLE_ONLY=1\n")):
            path = self.starter / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(value)
        self.patches = [patch.object(kit, "repository_root", return_value=self.source),
                        patch.object(kit, "NEXTJS_FILES", self.files, create=True)]
        for item in self.patches:
            item.start()

    def tearDown(self):
        for item in reversed(self.patches):
            item.stop()
        self.temp.cleanup()

    def test_scaffold_preserves_official_files_and_is_repeatable(self):
        (self.root / "README.md").write_text("Official task must stay.\n")
        (self.root / "AGENTS.md").write_text("Existing instructions.\n")
        original_ignore = "# Keep existing rules\ndata/\n!*.env\n"
        (self.root / ".gitignore").write_text(original_ignore)
        # Only the explicit package inventory is exportable, not local files.
        (self.starter / ".env.local").write_text("FICTIONAL_PRIVATE_VALUE=not-for-export\n")
        (self.starter / "node_modules").mkdir()
        (self.starter / "node_modules/local.txt").write_text("local dependency\n")
        first = kit.scaffold(self.root)
        before = {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        kit.scaffold(self.root)
        self.assertEqual(first["stack"], "nextjs-postgres")
        self.assertEqual(before, {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob("*") if p.is_file()})
        self.assertEqual((self.root / "README.md").read_text(), "Official task must stay.\n")
        self.assertEqual((self.root / "AGENTS.md").read_text(), "Existing instructions.\n")
        self.assertTrue((self.root / ".gitignore").read_text().startswith(original_ignore))
        self.assertFalse((self.root / ".env.local").exists())
        self.assertFalse((self.root / "node_modules").exists())
        self.assertFalse((self.root / ".git").exists())

    def test_existing_app_conflict_aborts_before_any_write(self):
        original = b'{"name":"official-project"}\n'
        (self.root / "package.json").write_bytes(original)
        with self.assertRaisesRegex(kit.KitError, "충돌"):
            kit.scaffold(self.root)
        self.assertEqual((self.root / "package.json").read_bytes(), original)
        self.assertFalse((self.root / "app").exists())
        self.assertFalse((self.root / ".gitignore").exists())

    def test_symlink_destination_cannot_write_outside_task(self):
        outside = self.base / "outside"
        outside.mkdir()
        (self.root / "app").symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(kit.KitError, "심볼릭"):
            kit.scaffold(self.root)
        self.assertFalse((outside / "page.tsx").exists())
        self.assertFalse((self.root / "package.json").exists())

    def test_parent_file_conflict_aborts_before_any_write(self):
        (self.root / "app").write_text("Official file, not a directory.\n")
        with self.assertRaisesRegex(kit.KitError, "충돌"):
            kit.scaffold(self.root)
        self.assertFalse((self.root / "package.json").exists())
        self.assertEqual((self.root / "app").read_text(), "Official file, not a directory.\n")

    def test_missing_or_linked_source_aborts_before_any_write(self):
        (self.starter / "app/page.tsx").unlink()
        with self.assertRaises(kit.KitError):
            kit.scaffold(self.root)
        self.assertFalse((self.root / "package.json").exists())
        (self.starter / "app/page.tsx").symlink_to(self.starter / "package.json")
        with self.assertRaisesRegex(kit.KitError, "심볼릭"):
            kit.scaffold(self.root)
        self.assertFalse((self.root / "package.json").exists())

    def test_scaffold_rejects_kit_source_and_its_children(self):
        for target in (self.source, self.starter):
            with self.subTest(target=target), self.assertRaises(kit.KitError):
                kit.scaffold(target)

    def test_private_environment_and_build_outputs_are_ignored(self):
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        kit.scaffold(self.root)
        result = subprocess.run(
            ["git", "-C", str(self.root), "check-ignore", "--stdin"],
            input=".env\n.env.local\n.next/cache/file\nnode_modules/file\ncoverage/file\n",
            capture_output=True, text=True, check=True,
        )
        self.assertEqual(len(result.stdout.splitlines()), 5)
        visible = subprocess.run(["git", "-C", str(self.root), "check-ignore", ".env.example"],
                                 capture_output=True, text=True)
        self.assertEqual(visible.returncode, 1)


if __name__ == "__main__":
    unittest.main()
