"""Isolated fictional fixtures: never run against a rehearsal or customer project."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import unittest


SOURCE = Path(__file__).resolve().parents[1] / "scripts/kit.py"
SPEC = importlib.util.spec_from_file_location("evidence_kit", SOURCE)
kit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(kit)


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()

    def tearDown(self):
        self.temp.cleanup()

    def fixture(self):
        (self.root / "src").mkdir()
        (self.root / "src/total.py").write_text("def total(a, b):\n    return a + b\n")
        (self.root / "test_total.py").write_text(
            "import unittest\nfrom src.total import total\n"
            "class TotalTests(unittest.TestCase):\n"
            "    def test_example(self):\n        self.assertEqual(total(2, 3), 5)\n")
        raw = self.root / ".hackathon/private/INTERVIEWS.md"
        raw.parent.mkdir(parents=True, exist_ok=True)
        raw.write_text("# Fictional test fixture, not a customer interview\n\n## Q1\n질문: 예시 결과는?\n답변: 두 수의 합.\n")
        self.write_requirement()

    def write_requirement(self, status="Implemented", source="Q1", acceptance="2와 3은 5", actual="미실행", remaining="—"):
        template = (SOURCE.parents[1] / "templates/REQUIREMENTS.md").read_text()
        divider = "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"
        row = f"| R-001 | 가상 합계 예시 | {status} | 미확인 | {source} | {acceptance} | 해당 없음 | src/total.py | python3 -m unittest -v test_total | {actual} | {remaining} |"
        path = self.root / ".hackathon/REQUIREMENTS.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(template.replace(divider, divider + "\n" + row))

    def run_example(self, check_id="sum-01"):
        return kit.record_check(self.root, check_id,
                                [sys.executable, "-m", "unittest", "-v", "test_total"],
                                10, requirement_ids=["R-001"])

    def test_actual_customer_to_requirement_to_execution_and_read_only_audit(self):
        self.fixture()
        record = self.run_example()
        self.assertEqual(record["result"], "PASS")
        self.assertEqual(record["tests"]["effective"], 1)
        self.write_requirement("Verified", actual="check:sum-01; 1개 통과")
        before = (self.root / ".hackathon/REQUIREMENTS.md").read_bytes()
        result = kit.audit_requirements(self.root)
        self.assertEqual(result["status"], "PASS", result)
        self.assertEqual(result["not_marked_verified"], [])
        self.assertEqual((self.root / ".hackathon/REQUIREMENTS.md").read_bytes(), before)
        self.assertTrue((self.root / record["log"]).is_file())

    def test_source_change_invalidates_verified_record(self):
        self.fixture()
        self.run_example()
        self.write_requirement("Verified", actual="check:sum-01")
        (self.root / "src/total.py").write_text("def total(a, b):\n    return a - b\n")
        result = kit.audit_requirements(self.root)
        self.assertEqual(result["status"], "FAIL")
        self.assertTrue(any("소스" in s for s in result["errors"]))

    def test_acceptance_or_customer_correction_invalidates_binding(self):
        self.fixture()
        self.run_example()
        self.write_requirement("Verified", acceptance="새 수락 조건", actual="check:sum-01")
        self.assertEqual(kit.audit_requirements(self.root)["status"], "FAIL")
        self.write_requirement("Verified", actual="check:sum-01")
        raw = self.root / ".hackathon/private/INTERVIEWS.md"
        raw.write_text(raw.read_text().replace("두 수의 합", "세 수의 합"))
        result = kit.audit_requirements(self.root)
        self.assertTrue(any("고객 근거" in s for s in result["errors"]))

    def test_new_unrelated_customer_answer_does_not_invalidate_existing_binding(self):
        self.fixture()
        self.run_example()
        self.write_requirement("Verified", actual="check:sum-01")
        raw = self.root / ".hackathon/private/INTERVIEWS.md"
        raw.write_text(raw.read_text() + "\n## Q2\n질문: 범위 밖 예시?\n답변: 추가 답변 fixture.\n")
        self.assertEqual(kit.audit_requirements(self.root)["status"], "PASS")

    def test_duplicate_id_and_pending_customer_answer_are_not_confirmed(self):
        self.fixture()
        self.write_requirement("Confirmed", source="Q2")
        raw = self.root / ".hackathon/private/INTERVIEWS.md"
        raw.write_text(raw.read_text() + "\n## Q2 — 답변 대기\n질문: 미수신 질문\n")
        path = self.root / ".hackathon/REQUIREMENTS.md"
        path.write_text(path.read_text() + "\n| ID | 요구사항 | 상태 | 고객 근거 Q/공식 과제 위치 | 관찰 가능한 수락 조건 | 실제 구현 파일 | 검증 절차 V/명령·테스트 | 실제 결과·실행 기록 |\n"
                        "| --- | --- | --- | --- | --- | --- | --- | --- |\n"
                        "| R-001 | 중복 fixture | Confirmed | Q1 | 합계 | src/total.py | 확인 | 미실행 |\n")
        result = kit.audit_requirements(self.root)
        self.assertTrue(any("중복" in s for s in result["errors"]))
        self.assertTrue(any("Q2" in s for s in result["errors"]))

    def test_empty_ledger_is_not_run_and_missing_files_are_reported(self):
        kit.install(self.root, "none")
        self.assertEqual(kit.audit_requirements(self.root)["status"], "NOT_RUN")
        self.fixture()
        (self.root / "src/total.py").unlink()
        self.assertTrue(any("구현 파일 없음" in s for s in kit.audit_requirements(self.root)["errors"]))

    def test_failure_and_unbound_check_cannot_verify_requirement(self):
        self.fixture()
        kit.record_check(self.root, "unbound", [sys.executable, "-c", "pass"], 10)
        self.write_requirement("Verified", actual="check:unbound")
        self.assertEqual(kit.audit_requirements(self.root)["status"], "FAIL")
        kit.record_check(self.root, "failed", [sys.executable, "-c", "raise SystemExit(3)"], 10,
                         requirement_ids=["R-001"])
        self.write_requirement("Verified", actual="check:failed")
        self.assertEqual(kit.audit_requirements(self.root)["status"], "FAIL")

    def test_manual_observation_is_participant_attestation_and_can_remain_pending(self):
        self.fixture()
        pending = kit.record_manual(self.root, "ui-pending", "NOT_RUN", "관찰 전 fixture", ["R-001"])
        self.assertEqual(pending["kind"], "participant-attestation")
        self.write_requirement("Verified", actual="manual:ui-pending")
        self.assertEqual(kit.audit_requirements(self.root)["status"], "FAIL")
        kit.record_manual(self.root, "ui-observed", "PASS", "가상 테스트의 참가자 관찰 입력", ["R-001"])
        self.write_requirement("Verified", actual="manual:ui-observed")
        self.assertEqual(kit.audit_requirements(self.root)["status"], "PASS")
        with self.assertRaises(kit.KitError):
            kit.record_manual(self.root, "ui-observed", "PASS", "overwrite")

    def test_fenced_example_and_pending_answer_are_not_customer_evidence(self):
        self.fixture()
        raw = self.root / ".hackathon/private/INTERVIEWS.md"
        raw.write_text("# Fictional log\n```text\n## Q1\n답변: example only\n```\n\n## Q2\n질문: pending\n답변: 대기\n")
        self.assertEqual(kit.customer_answers(self.root), {})
        self.assertEqual(kit.audit_requirements(self.root)["status"], "FAIL")

    def test_workspace_escape_in_file_reference_is_rejected(self):
        self.fixture()
        path = self.root / ".hackathon/REQUIREMENTS.md"
        path.write_text(path.read_text().replace("| src/total.py |", "| `../outside.py` |"))
        with self.assertRaises(kit.KitError):
            kit.audit_requirements(self.root)

    def test_change_during_command_is_unverified(self):
        (self.root / "source.txt").write_text("before")
        record = kit.record_check(self.root, "mutation", [sys.executable, "-c",
            "from pathlib import Path; Path('source.txt').write_text('after')"], 10)
        self.assertEqual(record["exit_code"], 0)
        self.assertEqual(record["result"], "UNVERIFIED")

    def test_bundled_skills_are_excluded_but_new_product_skills_are_fingerprinted(self):
        kit.install(self.root, "none")
        before = kit.fingerprint(self.root, for_checks=True)
        bundled = self.root / ".agents/skills/implementation-brief/SKILL.md"
        bundled.write_text(bundled.read_text() + "\nfixture documentation\n")
        self.assertEqual(kit.fingerprint(self.root, for_checks=True), before)
        product = self.root / ".agents/skills/product/SKILL.md"
        product.parent.mkdir()
        product.write_text("Product source fixture\n")
        self.assertNotEqual(kit.fingerprint(self.root, for_checks=True), before)

    def test_qa_renders_manual_evidence_as_participant_report(self):
        self.fixture()
        kit.record_manual(self.root, "observation", "PASS", "Fictional observation fixture", ["R-001"])
        kit.prepare_qa(self.root)
        path = self.root / ".hackathon/study/qa.json"
        data = json.loads(path.read_text())
        data["reviewed_at"] = kit.utc_now()
        for question in data["questions"]:
            question.update(question="가상 구조 검사", short_answer="합계 예시", answer="가상 예시의 구조만 확인",
                            evidence=[{"path": "src/total.py", "line": 2, "quote": "return a + b"}],
                            check_ids=["observation"], limitations=["실제 고객/화면 관찰 아님"])
        path.write_bytes(kit.json_bytes(data))
        kit.render_qa(self.root)
        rendered = (self.root / ".hackathon/study/IMPLEMENTATION_QA.md").read_text()
        self.assertIn("참가자 수동 진술 `observation`: PASS", rendered)
        self.assertNotIn("실행 `observation`", rendered)

    def test_real_zero_and_all_skipped_unittest_runs_are_not_success(self):
        for name, body in [("empty", ""), ("skipped", "import unittest\n@unittest.skip('fixture')\nclass T(unittest.TestCase):\n def test_skipped(self): pass\n")]:
            target = self.root / name
            target.mkdir()
            (target / "test_example.py").write_text(body)
            record = kit.record_check(target, name, [sys.executable, "-m", "unittest", "discover", "-v"], 10)
            self.assertIn(record["exit_code"], (0, 5))
            self.assertEqual(record["result"], "NOT_RUN")
            self.assertEqual(record["tests"]["effective"], 0)
        result = subprocess.run([sys.executable, str(SOURCE), "check", "--workspace", str(self.root / "empty"),
                                 "--id", "cli-empty", "--", sys.executable, "-m", "unittest", "discover"],
                                text=True, capture_output=True)
        self.assertIn(result.returncode, (2, 5))
        self.assertEqual(json.loads(result.stdout)["result"], "NOT_RUN")

    def test_pytest_native_summary_parser_with_ansi_and_deselection(self):
        summary = kit.test_summary(["pytest"], "\x1b[32m=== 2 passed, 1 skipped, 9 deselected in 0.12s ===\x1b[0m", "auto")
        self.assertEqual((summary["total"], summary["effective"]), (3, 2))
        self.assertEqual(kit.test_summary(["pytest"], "1 skipped in 0.01s", "auto")["state"], "NOT_RUN")
        self.assertEqual(kit.test_summary(["pytest"], "silenced summary", "auto")["state"], "UNKNOWN")

    def test_large_output_keeps_full_log_and_original_failure(self):
        record = kit.record_check(self.root, "large", [sys.executable, "-c", "print('begin-' + 'x'*40000); raise SystemExit(7)"], 10)
        self.assertEqual(record["exit_code"], 7)
        self.assertTrue(record["output_truncated"])
        self.assertIn("begin-", (self.root / record["log"]).read_text())

    def test_installer_reuses_existing_requirements_and_cli_defaults_to_core(self):
        (self.root / "docs").mkdir()
        existing = self.root / "docs/REQUIREMENTS.md"
        existing.write_text("Existing official project requirements\n")
        result = subprocess.run([sys.executable, str(SOURCE), "install", "--workspace", str(self.root)],
                                text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["installed_skills"], 11)
        self.assertEqual(existing.read_text(), "Existing official project requirements\n")
        self.assertFalse((self.root / ".hackathon/REQUIREMENTS.md").exists())
        self.assertIn("docs/REQUIREMENTS.md", (self.root / "AGENTS.md").read_text())
        kit.install(self.root, "core")

    def test_ambiguous_requirements_require_explicit_selection_without_writes(self):
        (self.root / "docs").mkdir()
        (self.root / "docs/REQUIREMENTS.md").write_text("one\n")
        (self.root / "REQUIREMENTS.md").write_text("two\n")
        with self.assertRaises(kit.KitError):
            kit.install(self.root, "none")
        self.assertFalse((self.root / "AGENTS.md").exists())
        kit.install(self.root, "none", "docs/REQUIREMENTS.md")

    def test_review_scope_includes_committed_staged_unstaged_and_untracked(self):
        def git(*args):
            return subprocess.run(["git", "-C", str(self.root), *args], check=True, capture_output=True, text=True)
        git("init", "-q")
        for name in ["committed.py", "staged.py", "working.py"]:
            (self.root / name).write_text("old\n")
        git("add", ".")
        git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.test", "commit", "-qm", "baseline")
        base = git("rev-parse", "HEAD").stdout.strip()
        (self.root / "committed.py").write_text("new\n")
        git("add", "committed.py")
        git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.test", "commit", "-qm", "change")
        (self.root / "staged.py").write_text("new\n"); git("add", "staged.py")
        (self.root / "working.py").write_text("new\n")
        (self.root / "new.py").write_text("new\n")
        result = kit.review_scope(self.root, base)
        self.assertEqual(set(result["files"]), {"committed.py", "staged.py", "working.py", "new.py"})

    def test_preflight_is_read_only_and_does_not_follow_http_redirects(self):
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(302); self.send_header("Location", "https://example.invalid/"); self.end_headers()
            def log_message(self, *args):
                pass
        server = HTTPServer(("127.0.0.1", 0), Handler)
        worker = threading.Thread(target=server.serve_forever, daemon=True); worker.start()
        try:
            result = kit.preflight(self.root, f"http://127.0.0.1:{server.server_port}/")
            self.assertEqual(result["http"]["status_code"], 302)
            self.assertEqual(result["http"]["result"], "FAIL")
            self.assertEqual(list(self.root.iterdir()), [])
            with self.assertRaises(kit.KitError):
                kit.preflight(self.root, "https://example.invalid/")
        finally:
            server.shutdown(); server.server_close(); worker.join()


if __name__ == "__main__":
    unittest.main()
