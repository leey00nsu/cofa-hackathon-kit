"""Behavioral checks for preservation, real execution evidence, and stale Q&A."""

import importlib.util
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


KIT_PATH = Path(__file__).resolve().parents[1] / "scripts/kit.py"
SPEC = importlib.util.spec_from_file_location("kit", KIT_PATH)
kit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(kit)


class KitTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name).resolve()

    def tearDown(self):
        self.temporary.cleanup()

    def create_source(self):
        (self.root / "src").mkdir()
        (self.root / "src/rule.py").write_text("def total(values):\n    return sum(values)\n")

    def complete_qa(self):
        self.create_source()
        kit.prepare_qa(self.root)
        path = self.root / ".hackathon/study/qa.json"
        data = json.loads(path.read_text())
        data["reviewed_at"] = "2026-10-30T16:00:00+09:00"
        for question in data["questions"]:
            # Fixture content exercises structural validation, not semantic grading.
            question.update({
                "question": question["topic"] + ": 구조 검사용 질문",
                "short_answer": "이 테스트 파일의 함수는 전달한 값의 합을 반환합니다.",
                "answer": "src/rule.py의 total이 sum을 반환합니다. 입력 검증은 없습니다.",
                "evidence": [{"path": "src/rule.py", "line": 2, "quote": "return sum(values)"}],
                "limitations": ["이 fixture는 답변의 의미적 정확성을 검사하지 않습니다."],
            })
        path.write_bytes(kit.json_bytes(data))
        return path, data

    def test_install_preserves_official_files_and_is_repeatable(self):
        official = "# Official problem\nNever replace this file.\n"
        (self.root / "README.md").write_text(official)
        (self.root / "AGENTS.md").write_text("Existing instruction.\n")
        result = kit.install(self.root, "core")
        self.assertEqual(result["installed_skills"], 11)
        self.assertEqual((self.root / "README.md").read_text(), official)
        self.assertTrue((self.root / "AGENTS.md").read_text().startswith("Existing instruction."))
        ledger = self.root / ".hackathon/REQUIREMENTS.md"
        ledger.write_text("Customer evidence received during the task.\n")
        kit.install(self.root, "core")
        self.assertEqual(ledger.read_text(), "Customer evidence received during the task.\n")
        self.assertEqual((self.root / "AGENTS.md").read_text().count(kit.BEGIN), 1)

    def test_install_rejects_kit_checkout_as_the_task_root(self):
        with self.assertRaisesRegex(kit.KitError, "작업 공간 루트"):
            kit.install(KIT_PATH.parents[1], "none")

    def test_vendor_allows_finder_metadata_but_rejects_untracked_source(self):
        vendor = self.root / "vendor/matt-pocock-skills"
        (vendor / "skills").mkdir(parents=True)
        (vendor / "LICENSE").write_bytes(b"fixture license")
        lock = {"commit": "fixture", "files": {"LICENSE": hashlib.sha256(b"fixture license").hexdigest()}}
        (self.root / "vendor/snapshot.json").write_bytes(kit.json_bytes(lock))
        (vendor / ".DS_Store").write_bytes(b"finder metadata")
        (vendor / "skills/.DS_Store").write_bytes(b"finder metadata")
        self.assertEqual(kit.verify_vendor(self.root)["commit"], "fixture")
        (vendor / "unexpected.sh").write_text("echo unexpected")
        with self.assertRaisesRegex(kit.KitError, "파일 목록"):
            kit.verify_vendor(self.root)

    def test_conflict_is_detected_before_any_install_write(self):
        target = self.root / "docs/agents"
        target.mkdir(parents=True)
        (target / "domain.md").write_text("Existing project conventions")
        with self.assertRaises(kit.KitError):
            kit.install(self.root, "core")
        self.assertFalse((self.root / ".hackathon").exists())
        self.assertFalse((self.root / "AGENTS.md").exists())
        self.assertEqual((target / "domain.md").read_text(), "Existing project conventions")

    def test_install_rejects_symlink_destination(self):
        outside = self.root / "outside"
        outside.mkdir()
        (self.root / ".hackathon").symlink_to(outside, target_is_directory=True)
        with self.assertRaises(kit.KitError):
            kit.install(self.root, "none")
        self.assertEqual(list(outside.iterdir()), [])

    def test_installed_tool_runs_without_the_source_checkout(self):
        kit.install(self.root, "none")
        result = subprocess.run(
            [sys.executable, str(self.root / ".hackathon/tools/kit.py"), "fingerprint", "--workspace", str(self.root)],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertGreater(json.loads(result.stdout)["file_count"], 0)

    def test_check_captures_real_failure_and_preserves_it(self):
        record = kit.record_check(self.root, "tests-01", [sys.executable, "-c", "import sys; print('actual output'); sys.exit(7)"], 10)
        self.assertEqual(record["exit_code"], 7)
        self.assertIn("actual output", record["stdout"])
        with self.assertRaises(kit.KitError):
            kit.record_check(self.root, "tests-01", [sys.executable, "-c", "pass"], 10)
        saved = kit.load_json(self.root / ".hackathon/checks/tests-01.json")
        self.assertEqual(saved["exit_code"], 7)

    def test_check_reports_missing_command_as_failure(self):
        record = kit.record_check(self.root, "missing", [str(self.root / "does-not-exist")], 10)
        self.assertEqual(record["exit_code"], 127)

    def test_check_timeout_is_not_success(self):
        record = kit.record_check(self.root, "timeout", [sys.executable, "-c", "import time; time.sleep(5)"], 0.05)
        self.assertEqual(record["exit_code"], 124)
        self.assertTrue(record["timed_out"])

    def test_empty_draft_cannot_be_rendered(self):
        self.create_source()
        kit.prepare_qa(self.root)
        with self.assertRaises(kit.KitError):
            kit.render_qa(self.root)
        self.assertFalse((self.root / ".hackathon/study/LAST_REVIEW.md").exists())

    def test_valid_qa_renders_and_survives_readback(self):
        self.complete_qa()
        kit.render_qa(self.root)
        result = kit.render_qa(self.root, verify_only=True)
        self.assertEqual(result["status"], "verified")
        self.assertIn("src/rule.py:2", (self.root / ".hackathon/study/IMPLEMENTATION_QA.md").read_text())
        self.assertEqual((self.root / ".hackathon/study/LAST_REVIEW.md").read_text().count("## Q"), 6)

    def test_source_change_invalidates_previously_rendered_qa(self):
        self.complete_qa()
        kit.render_qa(self.root)
        (self.root / "src/rule.py").write_text("def total(values):\n    return 0\n")
        with self.assertRaisesRegex(kit.KitError, "소스"):
            kit.render_qa(self.root, verify_only=True)

    def test_check_record_change_invalidates_qa(self):
        self.complete_qa()
        kit.render_qa(self.root)
        kit.record_check(self.root, "late", [sys.executable, "-c", "pass"], 10)
        with self.assertRaises(kit.KitError):
            kit.render_qa(self.root, verify_only=True)

    def test_wrong_line_quote_rejected_even_with_current_fingerprint(self):
        path, data = self.complete_qa()
        data["questions"][0]["evidence"][0]["quote"] = "return len(values)"
        path.write_bytes(kit.json_bytes(data))
        with self.assertRaisesRegex(kit.KitError, "인용"):
            kit.render_qa(self.root)

    def test_evidence_cannot_escape_workspace(self):
        path, data = self.complete_qa()
        data["questions"][0]["evidence"][0]["path"] = "../external.py"
        path.write_bytes(kit.json_bytes(data))
        with self.assertRaisesRegex(kit.KitError, "작업 공간 밖"):
            kit.render_qa(self.root)

    def test_symlink_evidence_is_rejected(self):
        path, data = self.complete_qa()
        (self.root / "alias.py").symlink_to(self.root / "src/rule.py")
        data["source_fingerprint"] = kit.fingerprint(self.root)["digest"]
        data["questions"][0]["evidence"][0]["path"] = "alias.py"
        path.write_bytes(kit.json_bytes(data))
        with self.assertRaisesRegex(kit.KitError, "심볼릭"):
            kit.render_qa(self.root)

    def test_unknown_execution_record_rejected(self):
        path, data = self.complete_qa()
        data["questions"][0]["check_ids"] = ["imagined-test"]
        path.write_bytes(kit.json_bytes(data))
        with self.assertRaises(kit.KitError):
            kit.render_qa(self.root)

    def test_markdown_edit_requires_render_again(self):
        path, data = self.complete_qa()
        kit.render_qa(self.root)
        data["questions"][0]["short_answer"] = "검토 후 수정한 다른 답변."
        path.write_bytes(kit.json_bytes(data))
        with self.assertRaisesRegex(kit.KitError, "렌더"):
            kit.render_qa(self.root, verify_only=True)

    def test_each_core_topic_is_required(self):
        path, data = self.complete_qa()
        data["questions"][0]["topic"] = "architecture"
        path.write_bytes(kit.json_bytes(data))
        with self.assertRaisesRegex(kit.KitError, "각 한 번"):
            kit.render_qa(self.root)

    def test_dependency_noise_does_not_invalidate_source_fingerprint(self):
        self.create_source()
        before = kit.fingerprint(self.root)
        dependency = self.root / "node_modules/package"
        dependency.mkdir(parents=True)
        (dependency / "index.js").write_text("generated dependency")
        self.assertEqual(kit.fingerprint(self.root), before)
        (self.root / "src/new.py").write_text("new source")
        self.assertNotEqual(kit.fingerprint(self.root)["digest"], before["digest"])


if __name__ == "__main__":
    unittest.main()
