#!/usr/bin/env python3
"""Offline install, execution evidence, and implementation-Q&A consistency checks."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
from datetime import datetime, timezone
from urllib.parse import quote


TOPICS = {
    "problem": "문제와 우선순위",
    "architecture": "구조와 데이터 흐름",
    "correctness": "업무 규칙과 정확성",
    "verification": "검증과 오류 복구",
    "tradeoffs": "대안·한계·변경 대응",
    "ai-control": "AI 지시와 본인의 판단",
}
CORE_SKILLS = {
    "grill-with-docs", "grilling", "domain-modeling", "implement", "tdd",
    "codebase-design", "code-review", "diagnosing-bugs", "handoff", "to-questionnaire",
}
IGNORED_DIRS = {
    ".git", "node_modules", ".venv", "venv", "__pycache__", ".pytest_cache",
    ".mypy_cache", ".ruff_cache", ".cache", ".next", "dist", "build", "coverage",
}
BEGIN = "<!-- cofa-hackathon-kit:begin -->"
END = "<!-- cofa-hackathon-kit:end -->"
AGENT_BLOCK = f"""{BEGIN}
## Cofa hackathon workflow

Read `.hackathon/OPERATING_RULES.md` before task work. The official task README and current exam instructions take priority. Preserve the provided task files.

Use `.hackathon/REQUIREMENTS.md`, `DECISIONS.md`, and `VERIFICATION.md` for evidence-based requirements, important choices, and actual checks. Use the local Markdown tracker in `docs/agents/issue-tracker.md`.

Use only the provided Codex and allowed models. Do not update Codex, connect external AI/personal keys, use Computer Use/browser automation, push Git, send task data outside, or alter platform/proctor settings. Browser interaction is performed manually by the participant.

Completion includes `$implementation-brief`: before submission is fixed, create evidence-based `.hackathon/study/IMPLEMENTATION_QA.md` and `LAST_REVIEW.md`, run `python3 .hackathon/tools/kit.py verify-qa --workspace .`, and leave time for the participant to review. Do not fabricate answers, tests, or decision history. Recheck Q&A if source or evidence changes. Stop AI use after submission is fixed; never answer live follow-up exam questions.
{END}
"""


class KitError(Exception):
    pass


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def digest_bytes(data):
    return hashlib.sha256(data).hexdigest()


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def load_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise KitError(f"JSON을 읽을 수 없음: {path}: {exc}") from exc


def inside(root, relative):
    if not isinstance(relative, str) or not relative:
        raise KitError("비어 있거나 잘못된 상대 경로")
    rel = Path(relative)
    if rel.is_absolute() or ".." in rel.parts:
        raise KitError(f"작업 공간 밖의 경로: {relative}")
    current = root
    for part in rel.parts:
        current = current / part
        if current.is_symlink():
            raise KitError(f"심볼릭 링크는 읽거나 덮어쓰지 않음: {relative}")
    if not current.resolve().is_relative_to(root):
        raise KitError(f"작업 공간 밖의 경로: {relative}")
    return current


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_bytes(json_bytes(value))
    temporary.replace(path)


def repository_root():
    return Path(__file__).resolve().parents[1]


def verify_vendor(root):
    lock = load_json(root / "vendor" / "snapshot.json")
    base = root / "vendor" / "matt-pocock-skills"
    actual_paths = {
        p.relative_to(base).as_posix() for p in base.rglob("*") if p.is_file()
    }
    if actual_paths != set(lock["files"]):
        raise KitError("Matt 원본 파일 목록이 고정본과 다름")
    for relative, expected in lock["files"].items():
        target = inside(base.resolve(), relative)
        if digest_bytes(target.read_bytes()) != expected:
            raise KitError(f"Matt 원본 해시 불일치: {relative}")
    return lock


def git_base(root):
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            text=True, capture_output=True, timeout=10, check=False,
        )
        return result.stdout.strip() if result.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired):
        return None


def install(root, mode):
    source = repository_root()
    if root == source:
        raise KitError("준비 레포 안이 아니라 제공된 작업 공간 루트를 --workspace로 지정할 것")
    lock = verify_vendor(source)
    plans = {}
    preserved = []

    def plan(relative, content, preserve=False):
        target = inside(root, relative)
        if target.exists():
            if not target.is_file():
                raise KitError(f"파일 경로에 디렉터리가 있음: {relative}")
            if preserve:
                preserved.append(relative)
                return
            if target.read_bytes() != content:
                raise KitError(f"기존 파일과 충돌. 아무 파일도 쓰지 않음: {relative}")
        plans[target] = content

    for name in [
        "OPERATING_RULES.md", "START_PROMPT.md", "FINISH_PROMPT.md", "QA_CONTRACT.md",
        "TIMEBOX.md", "SKILLS.md", "INPUT_EXAMPLES.md",
    ]:
        plan(f".hackathon/{name}", (source / "docs" / name).read_bytes())
    for name in ["REQUIREMENTS.md", "DECISIONS.md", "VERIFICATION.md"]:
        plan(f".hackathon/{name}", (source / "templates" / name).read_bytes(), preserve=True)
    for name in ["issue-tracker.md", "domain.md", "triage-labels.md"]:
        plan(f"docs/agents/{name}", (source / "templates" / name).read_bytes())
    plan(".hackathon/tools/kit.py", Path(__file__).read_bytes())

    skill_sources = [source / ".agents" / "skills" / "implementation-brief"]
    if mode != "none":
        vendor = source / "vendor" / "matt-pocock-skills" / "skills"
        for category in ["engineering", "productivity"]:
            for skill in sorted((vendor / category).iterdir()):
                if (skill / "SKILL.md").is_file() and (mode == "all" or skill.name in CORE_SKILLS):
                    skill_sources.append(skill)
    for skill in skill_sources:
        for entry in sorted(skill.rglob("*")):
            if entry.is_symlink():
                raise KitError(f"스킬 원본의 심볼릭 링크: {entry}")
            if entry.is_file():
                relative = entry.relative_to(skill).as_posix()
                plan(f".agents/skills/{skill.name}/{relative}", entry.read_bytes())
    plan(".agents/skills/MATT_LICENSE.txt", (source / "vendor/matt-pocock-skills/LICENSE").read_bytes())

    agent_path = inside(root, "AGENTS.md")
    existing = agent_path.read_text(encoding="utf-8") if agent_path.exists() else ""
    if BEGIN in existing or END in existing:
        if existing.count(BEGIN) != 1 or existing.count(END) != 1 or AGENT_BLOCK.strip() not in existing:
            raise KitError("기존 kit 지시 블록이 다름. 내용을 보존하고 중단함")
        agent_content = existing
    else:
        agent_content = existing + ("\n\n" if existing else "") + AGENT_BLOCK
    plans[agent_path] = agent_content.encode("utf-8")

    installed_path = inside(root, ".hackathon/install.json")
    previous = load_json(installed_path) if installed_path.exists() else None
    kit_directory = source.relative_to(root).as_posix() if source.is_relative_to(root) else None
    manifest = {
        "schema_version": 1, "matt_commit": lock["commit"], "matt_mode": mode,
        "kit_directory": kit_directory,
        "base_commit": previous.get("base_commit") if previous else git_base(root),
        "skills": sorted(p.name for p in skill_sources),
    }
    plan(".hackathon/install.json", json_bytes(manifest))

    # All content collisions and symlink checks complete before the first write.
    for target, content in plans.items():
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists() or target.read_bytes() != content:
            target.write_bytes(content)
    return {"installed_skills": len(skill_sources), "preserved_ledgers": preserved,
            "next": "Read .hackathon/START_PROMPT.md in the provided Codex."}


def fingerprint(root):
    excluded_kit = None
    marker = root / ".hackathon/install.json"
    if marker.is_file():
        raw = load_json(marker).get("kit_directory")
        if raw:
            excluded_kit = inside(root, raw)
            if excluded_kit == root:
                raise KitError("준비 레포 제외 경로가 전체 작업 공간을 가리킴")
    files = {}
    for directory, dirnames, filenames in os.walk(root, followlinks=False):
        current = Path(directory)
        relative_dir = current.relative_to(root).as_posix()
        if relative_dir in {".hackathon/study", ".hackathon/tools"} or current == excluded_kit:
            dirnames[:] = []
            continue
        dirnames[:] = sorted(
            name for name in dirnames
            if name not in IGNORED_DIRS and not (current / name).is_symlink()
        )
        for name in sorted(filenames):
            path = current / name
            if name == ".DS_Store" or name.endswith((".pyc", ".pyo")):
                continue
            relative = path.relative_to(root).as_posix()
            if path.is_symlink():
                files[relative] = "symlink:" + digest_bytes(os.readlink(path).encode())
            elif path.is_file():
                hasher = hashlib.sha256()
                with path.open("rb") as stream:
                    for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                        hasher.update(chunk)
                files[relative] = hasher.hexdigest()
    canonical = json.dumps(files, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return {"digest": digest_bytes(canonical.encode("utf-8")), "file_count": len(files)}


def record_check(root, check_id, command, timeout):
    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,63}", check_id):
        raise KitError("체크 ID에는 소문자·숫자·밑줄·하이픈만 사용")
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        raise KitError("실행할 명령이 없음")
    output = inside(root, f".hackathon/checks/{check_id}.json")
    if output.exists():
        raise KitError("이미 있는 실행 기록은 보존함. tests-02처럼 새 ID 사용")
    started = utc_now()
    timed_out = False
    try:
        process = subprocess.Popen(command, cwd=root, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   text=True, encoding="utf-8", errors="replace", start_new_session=True)
        try:
            stdout, stderr = process.communicate(timeout=timeout)
            exit_code = process.returncode
        except subprocess.TimeoutExpired:
            timed_out = True
            os.killpg(process.pid, signal.SIGKILL)
            stdout, stderr = process.communicate()
            exit_code = 124
    except OSError as exc:
        stdout, stderr, exit_code = "", str(exc), 127
    record = {
        "id": check_id, "command": command, "cwd": ".", "started_at": started,
        "finished_at": utc_now(), "exit_code": exit_code, "timed_out": timed_out,
        "stdout": stdout[-32000:], "stderr": stderr[-32000:],
        "output_truncated": len(stdout) > 32000 or len(stderr) > 32000,
    }
    # A test command can create files, so check the output route again afterwards.
    output = inside(root, f".hackathon/checks/{check_id}.json")
    write_json(output, record)
    return record


def qa_path(root):
    return inside(root, ".hackathon/study/qa.json")


def prepare_qa(root):
    target = qa_path(root)
    if target.exists():
        raise KitError("기존 문답을 보존함. 실제 내용 재검토 후 직접 갱신할 것")
    questions = []
    for number, (topic, label) in enumerate(TOPICS.items(), start=1):
        questions.append({
            "id": f"Q{number:02d}", "topic": topic, "priority": "core",
            "question": f"{label}: 실제 구현에 맞는 질문으로 작성",
            "short_answer": "", "answer": "", "evidence": [], "check_ids": [], "limitations": [],
        })
    value = {"schema_version": 1, "source_fingerprint": fingerprint(root)["digest"],
             "reviewed_at": "", "questions": questions}
    write_json(target, value)
    return {"draft": str(target.relative_to(root)), "status": "needs_actual_answers"}


def nonempty(value, name):
    if not isinstance(value, str) or not value.strip():
        raise KitError(f"비어 있는 답변 필드: {name}")


def validate_qa(root):
    data = load_json(qa_path(root))
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        raise KitError("지원하지 않는 문답 스키마")
    if data.get("source_fingerprint") != fingerprint(root)["digest"]:
        raise KitError("소스·근거가 바뀜. 문답 내용 재검토 후 지문 갱신·재렌더 필요")
    try:
        timestamp = datetime.fromisoformat(data.get("reviewed_at", ""))
        if timestamp.tzinfo is None:
            raise ValueError("timezone required")
    except (ValueError, TypeError) as exc:
        raise KitError("실제로 검토한 reviewed_at ISO 시각과 시간대 필요") from exc
    questions = data.get("questions")
    if not isinstance(questions, list) or not 6 <= len(questions) <= 12:
        raise KitError("문답은 핵심 6개와 추가 최대 6개")
    ids, core_topics = set(), []
    for question in questions:
        if not isinstance(question, dict):
            raise KitError("질문은 객체여야 함")
        identifier = question.get("id")
        if not isinstance(identifier, str) or not re.fullmatch(r"Q\d{2}", identifier) or identifier in ids:
            raise KitError("질문 ID는 중복 없는 Q01 형식")
        ids.add(identifier)
        if question.get("topic") not in TOPICS or question.get("priority") not in {"core", "extra"}:
            raise KitError(f"{identifier}: 잘못된 topic/priority")
        if question["priority"] == "core":
            core_topics.append(question["topic"])
        for field in ["question", "short_answer", "answer"]:
            nonempty(question.get(field), f"{identifier}.{field}")
        if len(question["short_answer"]) > 350:
            raise KitError(f"{identifier}: 짧은 답변 350자 초과")
        refs = question.get("evidence")
        if not isinstance(refs, list) or not refs:
            raise KitError(f"{identifier}: 실제 파일 근거 필요")
        for ref in refs:
            if not isinstance(ref, dict):
                raise KitError(f"{identifier}: 잘못된 근거 형식")
            relative = ref.get("path")
            target = inside(root, relative)
            if Path(relative).parts[:2] == (".hackathon", "study"):
                raise KitError(f"{identifier}: 문답 자체를 근거로 삼을 수 없음")
            try:
                lines = target.read_text(encoding="utf-8").splitlines()
            except (OSError, UnicodeError) as exc:
                raise KitError(f"{identifier}: 읽을 수 없는 근거: {relative}") from exc
            line = ref.get("line")
            if type(line) is not int or not 1 <= line <= len(lines):
                raise KitError(f"{identifier}: 근거 행이 실제 범위 밖: {relative}")
            excerpt = ref.get("quote")
            nonempty(excerpt, f"{identifier}.quote")
            if len(excerpt) > 160 or excerpt not in lines[line - 1]:
                raise KitError(f"{identifier}: 인용이 지정 행과 다름: {relative}:{line}")
        checks = question.get("check_ids", [])
        if not isinstance(checks, list):
            raise KitError(f"{identifier}: check_ids는 목록")
        for check_id in checks:
            if not isinstance(check_id, str) or not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,63}", check_id):
                raise KitError(f"{identifier}: 잘못된 체크 ID")
            record = load_json(inside(root, f".hackathon/checks/{check_id}.json"))
            if record.get("id") != check_id or type(record.get("exit_code")) is not int:
                raise KitError(f"{identifier}: 잘못된 실행 기록")
        limits = question.get("limitations")
        if not isinstance(limits, list) or not limits:
            raise KitError(f"{identifier}: 한계 또는 미검증 범위를 명시할 것")
        for limit in limits:
            nonempty(limit, f"{identifier}.limitations")
    if sorted(core_topics) != sorted(TOPICS):
        raise KitError("핵심 6개 주제를 각 한 번씩 포함할 것")
    return data


def render_content(root, data):
    warning = "과제 제출물 확정 전 복습용. 실제 출제 문항이 아니며, 확정 후에는 AI 사용을 중단하고 직접 답변한다.\n"
    full = ["# 구현 기반 예상 문답\n", warning,
            f"검토 시각: {data['reviewed_at']}\n소스 지문: `{data['source_fingerprint']}`\n"]
    short = ["# 제출 전 마지막 복습\n", warning,
             "핵심 6개를 본인 말로 설명한다. 질문의 전제가 구현과 다르면 실제 구현부터 바로잡는다.\n"]
    ordered = sorted(data["questions"], key=lambda item: item["priority"] != "core")
    for question in ordered:
        heading = f"## {question['id']} · {question['question']}\n"
        full.extend([heading, question["short_answer"] + "\n", question["answer"] + "\n", "근거:\n"])
        for ref in question["evidence"]:
            label = f"{ref['path']}:{ref['line']}"
            link = "../../" + quote(ref["path"], safe="/")
            full.append(f"- [{label}]({link}): {ref['quote']}\n")
        for check_id in question.get("check_ids", []):
            record = load_json(root / f".hackathon/checks/{check_id}.json")
            full.append(f"- 실행 `{check_id}`: exit={record['exit_code']}, {record['finished_at']}\n")
        full.append("\n한계: " + " / ".join(question["limitations"]) + "\n")
        if question["priority"] == "core":
            short.extend([heading, question["short_answer"] + "\n"])
    return {"IMPLEMENTATION_QA.md": "\n".join(full), "LAST_REVIEW.md": "\n".join(short)}


def render_qa(root, verify_only=False):
    data = validate_qa(root)
    documents = render_content(root, data)
    for name, content in documents.items():
        target = inside(root, f".hackathon/study/{name}")
        if verify_only:
            if not target.exists() or target.read_text(encoding="utf-8") != content:
                raise KitError(f"렌더 결과가 없거나 JSON과 다름: {name}. render-qa 필요")
        else:
            target.write_text(content, encoding="utf-8")
    return {"status": "verified" if verify_only else "rendered", "questions": len(data["questions"]),
            "scope": "file fingerprint, references, check records, and rendered document consistency only"}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="action", required=True)
    for action in ["install", "fingerprint", "check", "prepare-qa", "render-qa", "verify-qa"]:
        sub = commands.add_parser(action)
        sub.add_argument("--workspace", default=".")
        if action == "install":
            sub.add_argument("--matt", choices=["all", "core", "none"], default="all")
        if action == "check":
            sub.add_argument("--id", required=True)
            sub.add_argument("--timeout", type=int, default=300)
            sub.add_argument("command", nargs=argparse.REMAINDER)
    commands.add_parser("verify-vendor")
    args = parser.parse_args(argv)
    try:
        if args.action == "verify-vendor":
            value = verify_vendor(repository_root())
            result = {"status": "verified", "commit": value["commit"], "files": len(value["files"])}
        else:
            root = Path(args.workspace).resolve()
            if not root.is_dir():
                raise KitError("작업 공간이 존재하지 않음")
            if args.action == "install":
                result = install(root, args.matt)
            elif args.action == "fingerprint":
                result = fingerprint(root)
            elif args.action == "check":
                if args.timeout <= 0:
                    raise KitError("timeout은 양수")
                result = record_check(root, args.id, args.command, args.timeout)
                print(json.dumps(result, ensure_ascii=False, indent=2))
                return result["exit_code"] if result["exit_code"] >= 0 else 128 - result["exit_code"]
            elif args.action == "prepare-qa":
                result = prepare_qa(root)
            else:
                result = render_qa(root, verify_only=args.action == "verify-qa")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (KitError, OSError, UnicodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
