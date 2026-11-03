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
                                [sys.executable, "-B", "-m", "unittest", "-v", "test_total"],
                                10, requirement_ids=["R-001"])

    def example_qa(self, check_id):
        kit.prepare_qa(self.root)
        path = self.root / ".hackathon/study/qa.json"
        data = json.loads(path.read_text())
        data["reviewed_at"] = kit.utc_now()
        for question in data["questions"]:
            question.update(question="가상 합계의 동작은?", short_answer="두 수의 합을 돌려줍니다.",
                            answer="가상 합계 함수와 실제 실행 기록을 참조합니다.",
                            evidence=[{"path": "src/total.py", "line": 2, "quote": "return a + b"}],
                            check_ids=[check_id], limitations=["형식 검사용 fixture이며 고객 과제가 아닙니다."])
        path.write_bytes(kit.json_bytes(data))
        return path

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

    def test_missing_full_log_prevents_verified_audit(self):
        self.fixture()
        record = self.run_example()
        self.write_requirement("Verified", actual="check:sum-01")
        self.assertEqual(kit.audit_requirements(self.root)["status"], "PASS")
        (self.root / record["log"]).unlink()
        result = kit.audit_requirements(self.root)
        self.assertEqual(result["status"], "FAIL")
        self.assertTrue(any("로그" in error for error in result["errors"]))

    def test_modified_log_is_rejected_without_rewriting_ledger_or_execution(self):
        self.fixture()
        record = self.run_example()
        self.write_requirement("Verified", actual="check:sum-01")
        ledger = self.root / ".hackathon/REQUIREMENTS.md"
        execution = self.root / ".hackathon/checks/sum-01.json"
        before = (ledger.read_bytes(), execution.read_bytes())
        log = self.root / record["log"]
        log.write_bytes(log.read_bytes() + b"\nAltered fixture log\n")
        result = kit.audit_requirements(self.root)
        self.assertEqual(result["status"], "FAIL")
        self.assertTrue(any("로그 내용" in error for error in result["errors"]))
        self.assertEqual((ledger.read_bytes(), execution.read_bytes()), before)

    def test_log_evidence_rejects_bad_digest_path_symlink_and_directory(self):
        self.fixture()
        for index, condition in enumerate(["digest", "path", "symlink", "directory"]):
            with self.subTest(condition=condition):
                identifier = f"bad-log-{index}"
                record = self.run_example(identifier)
                self.write_requirement("Verified", actual="check:" + identifier)
                target = self.root / record["log"]
                if condition == "digest":
                    record["log_sha256"] = None
                elif condition == "path":
                    record["log"] = "../outside.log"
                else:
                    saved = target.with_suffix(".saved")
                    target.rename(saved)
                    if condition == "symlink":
                        target.symlink_to(saved)
                    else:
                        target.mkdir()
                (self.root / f".hackathon/checks/{identifier}.json").write_bytes(kit.json_bytes(record))
                result = kit.audit_requirements(self.root)
                self.assertEqual(result["status"], "FAIL")
                self.assertTrue(any("로그" in error for error in result["errors"]))

    def test_legacy_log_is_unverified_and_cli_preserves_the_original_record(self):
        self.fixture()
        record = self.run_example()
        record["schema_version"] = 2
        record.pop("log_sha256")
        target = self.root / ".hackathon/checks/sum-01.json"
        target.write_bytes(kit.json_bytes(record))
        self.write_requirement("Verified", actual="check:sum-01")
        before = target.read_bytes()
        result = subprocess.run([sys.executable, str(SOURCE), "audit-requirements", "--workspace", str(self.root)],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 2, result.stderr)
        audit = json.loads(result.stdout)
        self.assertEqual(audit["status"], "UNVERIFIED")
        self.assertEqual(audit["unverified_log_ids"], ["sum-01"])
        self.assertEqual(audit["errors"], [])
        self.assertEqual(target.read_bytes(), before)

    def test_refreshing_qa_fingerprint_cannot_legitimize_a_missing_log(self):
        self.fixture()
        record = self.run_example()
        path = self.example_qa("sum-01")
        kit.render_qa(self.root)
        (self.root / record["log"]).unlink()
        # A caller has refreshed the metadata: the independent log guard must still reject it.
        data = kit.load_json(path)
        data["source_fingerprint"] = kit.fingerprint(self.root)["digest"]
        path.write_bytes(kit.json_bytes(data))
        with self.assertRaisesRegex(kit.KitError, "로그"):
            kit.render_qa(self.root)

    def test_refreshed_qa_keeps_old_success_as_history_not_current_evidence(self):
        self.fixture()
        self.run_example()
        path = self.example_qa("sum-01")
        kit.render_qa(self.root)
        saved = self.root / ".hackathon/checks/sum-01.json"
        before = saved.read_bytes()
        (self.root / "src/total.py").write_text("def total(a, b):\n    return a - b\n")
        self.assertEqual(self.run_example("sum-02")["result"], "FAIL")
        data = kit.load_json(path)
        data["source_fingerprint"] = kit.fingerprint(self.root)["digest"]
        data["reviewed_at"] = kit.utc_now()
        for question in data["questions"]:
            question["evidence"][0]["quote"] = "return a - b"
            question["answer"] = "가상 재현: sum-01은 변경 전 성공이며 현재 sum-02는 실패했습니다."
        path.write_bytes(kit.json_bytes(data))
        kit.render_qa(self.root)
        result = subprocess.run([sys.executable, str(SOURCE), "verify-qa", "--workspace", str(self.root)],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 2, result.stdout)
        status = json.loads(result.stdout)
        self.assertEqual(status["status"], "unverified")
        self.assertEqual(status["stale_check_ids"], ["sum-01"])
        for name in ["IMPLEMENTATION_QA.md", "LAST_REVIEW.md"]:
            self.assertIn("과거 기록", (self.root / ".hackathon/study" / name).read_text())
        self.assertEqual(saved.read_bytes(), before)

    def test_qa_marks_historical_logs_without_inventing_integrity_evidence(self):
        self.fixture()
        record = self.run_example()
        record["schema_version"] = 2
        record.pop("log_sha256")
        target = self.root / ".hackathon/checks/sum-01.json"
        target.write_bytes(kit.json_bytes(record))
        self.example_qa("sum-01")
        before = target.read_bytes()
        self.assertEqual(kit.render_qa(self.root)["unverified_log_ids"], ["sum-01"])
        self.assertEqual(kit.render_qa(self.root, verify_only=True)["unverified_log_ids"], ["sum-01"])
        self.assertEqual(kit.render_qa(self.root, verify_only=True)["status"], "unverified")
        rendered = (self.root / ".hackathon/study/IMPLEMENTATION_QA.md").read_text()
        self.assertIn("이전 기록: 원본 로그 내용 지문 미적용", rendered)
        self.assertEqual(target.read_bytes(), before)

    def test_qa_freshness_tracks_bound_criteria_and_answers_only(self):
        self.fixture()
        self.run_example()
        path = self.example_qa("sum-01")
        ledger = self.root / ".hackathon/REQUIREMENTS.md"
        raw = self.root / ".hackathon/private/INTERVIEWS.md"
        original_ledger, original_answers = ledger.read_text(), raw.read_text()
        for name in ["criteria", "answer", "unrelated-answer", "broken-ledger"]:
            with self.subTest(change=name):
                ledger.write_text(original_ledger)
                raw.write_text(original_answers)
                if name == "criteria":
                    ledger.write_text(original_ledger.replace("2와 3은 5", "2와 3은 다른 값"))
                elif name == "answer":
                    raw.write_text(original_answers.replace("두 수의 합", "세 수의 합"))
                elif name == "unrelated-answer":
                    raw.write_text(original_answers + "\n## Q2\n질문: 범위 밖?\n답변: 별도 가상 답변.\n")
                else:
                    ledger.write_text(original_ledger + "\n| R-002 | 끊긴 가상 행 |\n")
                data = kit.load_json(path)
                data["source_fingerprint"] = kit.fingerprint(self.root)["digest"]
                data["reviewed_at"] = kit.utc_now()
                path.write_bytes(kit.json_bytes(data))
                kit.render_qa(self.root)
                result = kit.render_qa(self.root, verify_only=True)
                if name == "unrelated-answer":
                    self.assertEqual(result["status"], "verified", result)
                elif name == "broken-ledger":
                    self.assertEqual(result["unverified_check_ids"], ["sum-01"])
                else:
                    self.assertEqual(result["stale_check_ids"], ["sum-01"])

    def test_last_review_reports_stale_evidence_used_only_by_an_extra_question(self):
        self.fixture()
        self.run_example()
        path = self.example_qa("sum-01")
        (self.root / "src/total.py").write_text("def total(a, b):\n    return a - b\n")
        data = kit.load_json(path)
        extra = {**data["questions"][0], "id": "Q07", "priority": "extra"}
        data["questions"].append(extra)
        for question in data["questions"]:
            question["evidence"][0]["quote"] = "return a - b"
            if question["priority"] == "core":
                question["check_ids"] = []
        data["source_fingerprint"] = kit.fingerprint(self.root)["digest"]
        path.write_bytes(kit.json_bytes(data))
        kit.render_qa(self.root)
        result = kit.render_qa(self.root, verify_only=True)
        self.assertEqual(result["stale_check_ids"], ["sum-01"])
        short = (self.root / ".hackathon/study/LAST_REVIEW.md").read_text()
        self.assertIn("sum-01", short)
        self.assertIn("과거 기록", short)

    def test_qa_freshness_respects_explicit_nonstandard_requirements_path(self):
        self.fixture()
        target = self.root / "custom/criteria.md"
        target.parent.mkdir()
        (self.root / ".hackathon/REQUIREMENTS.md").rename(target)
        record = kit.record_check(self.root, "custom-rules", [sys.executable, "-B", "-m", "unittest", "-v", "test_total"],
                                  10, requirement_ids=["R-001"], requirements="custom/criteria.md")
        self.assertEqual(record["result"], "PASS")
        self.example_qa("custom-rules")
        kit.render_qa(self.root)
        self.assertEqual(kit.render_qa(self.root, verify_only=True)["status"], "verified")

    def test_current_failure_is_available_for_study_without_claiming_success(self):
        self.fixture()
        (self.root / "src/total.py").write_text("def total(a, b):\n    return a - b\n")
        self.assertEqual(self.run_example()["result"], "FAIL")
        path = self.example_qa("sum-01")
        data = kit.load_json(path)
        for question in data["questions"]:
            question["evidence"][0]["quote"] = "return a - b"
            question["answer"] = "가상 합계 요구를 충족하지 못하며 실제 검사는 실패했습니다."
        path.write_bytes(kit.json_bytes(data))
        kit.render_qa(self.root)
        self.assertEqual(kit.render_qa(self.root, verify_only=True)["status"], "verified")
        rendered = (self.root / ".hackathon/study/IMPLEMENTATION_QA.md").read_text()
        self.assertIn("실행 `sum-01`: FAIL", rendered)
        self.assertIn("현재 적용 확인 `sum-01`: CURRENT", rendered)

    def test_verified_flow_stays_valid_after_defense_update_but_not_code_change(self):
        # A real command in a fictional workspace exercises the post-feature loop.
        kit.install(self.root, "none")
        self.fixture()
        record = self.run_example()
        self.assertEqual(record["result"], "PASS")
        self.write_requirement("Verified", actual="check:sum-01")
        before = kit.fingerprint(self.root, for_checks=True)
        defense = self.root / "docs/DEFENSE.md"
        defense.write_text(
            "# Fictional example only, not a customer implementation\n"
            "R-001 / Q1: a, b -> src/total.py:total -> a + b.\n"
            "check:sum-01; actual command: " + " ".join(record["command"]) + "\n"
            "Actual result: PASS, one executed test. No type-validation claim.\n")
        self.assertEqual(kit.fingerprint(self.root, for_checks=True), before)
        self.assertEqual(kit.audit_requirements(self.root)["status"], "PASS")
        # Exempt exactly the study index, not other docs or real product files.
        (self.root / "docs/business-rule.py").write_text("LIMIT = 1\n")
        self.assertNotEqual(kit.fingerprint(self.root, for_checks=True), before)
        self.assertEqual(kit.audit_requirements(self.root)["status"], "FAIL")

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

    def test_answer_heading_cannot_confirm_an_explicitly_pending_answer(self):
        self.fixture()
        raw = self.root / ".hackathon/private/INTERVIEWS.md"
        raw.write_text("# Fictional fixture\n\n### Q1 답변\n질문: 예시 결과는?\n답변: 대기\n")
        self.run_example()
        self.write_requirement("Verified", actual="check:sum-01")
        result = kit.audit_requirements(self.root)
        self.assertEqual(result["status"], "FAIL", result)
        self.assertTrue(any("Q1" in error for error in result["errors"]))

    def test_pending_and_received_answer_formats_remain_distinct(self):
        self.fixture()
        raw = self.root / ".hackathon/private/INTERVIEWS.md"
        for index, value in enumerate(["pending", "미수신", "—", ""]):
            with self.subTest(pending=value):
                raw.write_text(f"### Q1 Answer\n질문: 가상 질문\n답변: {value}\n")
                self.run_example(f"pending-{index}")
                self.write_requirement("Verified", actual=f"check:pending-{index}")
                self.assertEqual(kit.audit_requirements(self.root)["status"], "FAIL")
        for index, body in enumerate(["답변: 두 수의 합.", "답변:\n두 수의 합.", "두 수의 합."]):
            with self.subTest(received=body):
                raw.write_text(f"### Q1 답변\n{body}\n")
                self.run_example(f"received-{index}")
                self.write_requirement("Verified", actual=f"check:received-{index}")
                self.assertEqual(kit.audit_requirements(self.root)["status"], "PASS")

    def test_notes_after_an_empty_answer_do_not_confirm_customer_evidence(self):
        self.fixture()
        raw = self.root / ".hackathon/private/INTERVIEWS.md"
        for index, value in enumerate(["—", "미확인", ""]):
            with self.subTest(empty_value=value):
                raw.write_text(f"### Q1 답변\n질문: 가상 질문\n답변: {value}\n메모: 아직 답변은 없음.\n")
                self.run_example(f"note-pending-{index}")
                self.write_requirement("Verified", actual=f"check:note-pending-{index}")
                self.assertEqual(kit.audit_requirements(self.root)["status"], "FAIL")

    def test_broken_requirement_table_cannot_hide_an_unverified_row(self):
        self.fixture()
        self.run_example()
        self.write_requirement("Verified", actual="check:sum-01")
        path = self.root / ".hackathon/REQUIREMENTS.md"
        first = next(line for line in path.read_text().splitlines() if line.startswith("| R-001 |"))
        orphan = first.replace("R-001", "R-002").replace("check:sum-01", "미실행")
        path.write_text(path.read_text() + "\n" + orphan + "\n")
        before = path.read_bytes()
        result = subprocess.run([sys.executable, str(SOURCE), "audit-requirements", "--workspace", str(self.root)],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 1, result.stdout)
        audit = json.loads(result.stdout)
        self.assertEqual(audit["status"], "FAIL")
        self.assertTrue(any("R-002" in error and "행" in error for error in audit["errors"]))
        self.assertEqual(path.read_bytes(), before)

    def test_unrelated_tables_and_fenced_examples_are_not_orphan_requirements(self):
        self.fixture()
        path = self.root / ".hackathon/REQUIREMENTS.md"
        path.write_text(path.read_text() + "\n| 우선순위 | 설명 |\n| --- | --- |\n| P0 | 별도 가상 참고 |\n"
                        "\n```text\n| R-999 | 실행하지 않은 형식 예시 |\n```\n")
        self.run_example()
        original = path.read_text()
        path.write_text(original.replace("| Implemented |", "| Verified |").replace("| 미실행 |", "| check:sum-01 |"))
        result = kit.audit_requirements(self.root)
        self.assertEqual(result["status"], "PASS", result)
        self.assertEqual(result["requirements"], 1)

    def test_empty_pipe_or_nonheader_cannot_hide_a_requirement_row(self):
        self.fixture()
        path = self.root / ".hackathon/REQUIREMENTS.md"
        original = path.read_text()
        for prefix in ["|\n", "| | |\n", "| 참고 | 잘못된 머리글 |\n"]:
            with self.subTest(prefix=prefix):
                path.write_text(original + "\n" + prefix + "| R-002 | 끊긴 가상 요구사항 |\n")
                result = kit.audit_requirements(self.root)
                self.assertEqual(result["status"], "FAIL", result)
                self.assertTrue(any("R-002" in error for error in result["errors"]))

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

    def test_expected_failure_only_is_executed_but_not_verified(self):
        self.fixture()
        source = self.root / "src/total.py"
        source.write_text("def total(a, b):\n    return a - b\n")
        test = self.root / "test_total.py"
        test.write_text(test.read_text().replace(
            "    def test_example", "    @unittest.expectedFailure\n    def test_example"))
        record = self.run_example()
        self.assertEqual(record["exit_code"], 0)
        self.assertEqual(record["result"], "UNVERIFIED")
        self.assertEqual(record["tests"]["expected_failed"], 1)
        self.assertEqual(record["tests"]["effective"], 0)
        self.assertNotEqual(record["tests"]["state"], "NOT_RUN")
        self.write_requirement("Verified", actual="check:sum-01")
        self.assertEqual(kit.audit_requirements(self.root)["status"], "FAIL")

    def test_pytest_expected_outcome_summaries_are_not_ordinary_successes(self):
        # Synthetic runner output exercises classification; this does not run pytest.
        cases = [("1 xfailed in 0.01s", "UNVERIFIED", 0),
                 ("1 xpassed in 0.01s", "UNVERIFIED", 0),
                 ("1 passed, 1 skipped, 1 xfailed in 0.01s", "PASS", 1),
                 ("1 failed, 1 xfailed in 0.01s", "FAIL", 1)]
        for index, (summary, expected, effective) in enumerate(cases):
            with self.subTest(summary=summary):
                record = kit.record_check(self.root, f"expected-summary-{index}",
                    [sys.executable, "-c", f"print({summary!r})"], 10, runner="pytest")
                self.assertEqual(record["result"], expected)
                self.assertEqual(record["tests"]["effective"], effective)

    def test_mixed_unittest_expected_failure_keeps_the_real_success_count(self):
        self.fixture()
        test = self.root / "test_total.py"
        test.write_text(test.read_text() + "\n    @unittest.expectedFailure\n"
                        "    def test_known_failure(self):\n        self.assertEqual(total(2, 3), 99)\n")
        record = self.run_example()
        self.assertEqual(record["result"], "PASS")
        self.assertEqual(record["tests"]["total"], 2)
        self.assertEqual(record["tests"]["effective"], 1)
        self.assertEqual(record["tests"]["expected_failed"], 1)

    def test_pytest_native_summary_parser_with_ansi_and_deselection(self):
        summary = kit.test_summary(["pytest"], "\x1b[32m=== 2 passed, 1 skipped, 9 deselected in 0.12s ===\x1b[0m", "auto")
        self.assertEqual((summary["total"], summary["effective"]), (3, 2))
        self.assertEqual(kit.test_summary(["pytest"], "1 skipped in 0.01s", "auto")["state"], "NOT_RUN")
        self.assertEqual(kit.test_summary(["pytest"], "silenced summary", "auto")["state"], "UNKNOWN")

    def test_pytest_wrapper_keeps_failure_before_later_success(self):
        # Captured runner summaries reproduce a wrapper that loses its child exit code.
        record = kit.record_check(self.root, "pytest-wrapper", [sys.executable, "-c",
            "print('1 failed in 0.01s'); print('1 passed in 0.01s')"], 10, runner="pytest")
        self.assertEqual(record["exit_code"], 0)
        self.assertEqual(record["result"], "FAIL")

    def test_pytest_mixed_summaries_keep_failures_across_streams_and_order(self):
        programs = [
            "print('1 passed in 0.01s'); print('1 failed in 0.01s')",
            "import sys; print('1 failed in 0.01s'); print('1 passed in 0.01s', file=sys.stderr)",
            "import sys; print('1 passed in 0.01s'); print('1 error in 0.01s', file=sys.stderr)",
        ]
        for index, program in enumerate(programs):
            with self.subTest(index=index):
                record = kit.record_check(self.root, f"mixed-{index}",
                    [sys.executable, "-c", program], 10, runner="pytest")
                self.assertEqual(record["exit_code"], 0)
                self.assertEqual(record["result"], "FAIL")
                self.assertTrue(record["tests"]["ambiguous"])

    def test_pytest_multiple_runs_without_failure_are_not_a_verified_total(self):
        for index, first in enumerate(["1 passed in 0.01s", "no tests ran in 0.01s"]):
            with self.subTest(first=first):
                record = kit.record_check(self.root, f"ambiguous-{index}",
                    [sys.executable, "-c", f"print({first!r}); print('1 passed in 0.01s')"],
                    10, runner="pytest")
                self.assertEqual(record["result"], "UNVERIFIED")
                self.assertIsNone(record["tests"]["total"])

    def test_pytest_ambiguous_cli_returns_nonzero_and_keeps_original_exit(self):
        result = subprocess.run([sys.executable, str(SOURCE), "check", "--workspace", str(self.root),
            "--id", "ambiguous-cli", "--test-runner", "pytest", "--", sys.executable, "-c",
            "print('1 passed in 0.01s'); print('1 passed in 0.01s')"],
            capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        record = json.loads(result.stdout)
        self.assertEqual((record["exit_code"], record["result"]), (0, "UNVERIFIED"))

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
