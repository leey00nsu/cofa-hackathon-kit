#!/usr/bin/env python3
"""Offline install, execution evidence, and implementation-Q&A consistency checks."""

from __future__ import annotations

import argparse
import hashlib
import http.client
import ipaddress
import json
import os
from pathlib import Path
import platform
import re
import shutil
import signal
import subprocess
import sys
from datetime import datetime, timezone
from urllib.parse import quote, urlsplit, unquote


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
PRIVATE_PATHS = (".hackathon/private", ".hackathon/checks", ".hackathon/study", "private", "docs/DEFENSE.md")
PRIVATE_IGNORES = (
    "/.hackathon/private/", "/.hackathon/checks/", "/.hackathon/study/",
    "/private/", "/PRIVATE*", "/docs/DEFENSE.md",
)


class KitError(Exception):
    pass


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def digest_bytes(data):
    return hashlib.sha256(data).hexdigest()


def digest_file(path):
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


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
        p.relative_to(base).as_posix() for p in base.rglob("*")
        if p.is_file() and p.name != ".DS_Store"
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


def requirements_file(root, explicit=None):
    if explicit:
        return inside(root, explicit)
    marker = inside(root, ".hackathon/install.json")
    if marker.is_file():
        chosen = load_json(marker).get("requirements_path")
        if chosen:
            return inside(root, chosen)
    candidates = [inside(root, name) for name in (
        ".hackathon/REQUIREMENTS.md", "docs/REQUIREMENTS.md", "REQUIREMENTS.md",
        "docs/requirements.md", "requirements.md",
    )]
    existing = []
    for path in candidates:
        if path.is_file() and not any(path.samefile(p) for p in existing):
            existing.append(path)
    if len(existing) > 1:
        raise KitError("요구사항 문서가 여러 개임. --requirements로 기존 정본을 지정할 것")
    return existing[0] if existing else candidates[0]


def install(root, mode, requirements=None):
    source = repository_root()
    if root == source:
        raise KitError("준비 레포 안이 아니라 제공된 작업 공간 루트를 --workspace로 지정할 것")
    lock = verify_vendor(source)
    plans = {}
    preserved = []
    requirement_path = requirements_file(root, requirements)
    requirement_relative = requirement_path.relative_to(root).as_posix()

    # Ignore cannot protect an already tracked private file. Never silently untrack it.
    if (root / ".git").exists():
        result = subprocess.run(["git", "-C", str(root), "ls-files", "-z"],
                                capture_output=True, text=True, timeout=10, check=False)
        if result.returncode != 0:
            raise KitError("Git 추적 파일 확인 실패. 아무 파일도 쓰지 않음")
        tracked_private = [name for name in result.stdout.split("\0") if name and (
            any(name == p or name.startswith(p + "/") for p in PRIVATE_PATHS)
            or name.startswith("PRIVATE"))]
        if tracked_private:
            raise KitError("이미 추적 중인 비공개 경로. ignore로 보호되지 않음. 내용을 보존하고 중단함: "
                           + ", ".join(tracked_private))

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

    for name in ["START_PROMPT.md", "INTERVIEW_PROTOCOL.md", "AUTOMATED_TESTING.md"]:
        plan(f".hackathon/{name}", (source / "docs" / name).read_bytes())
    plan(".hackathon/references/validation-tools.md",
         (source / "docs/references/validation-tools.md").read_bytes())
    plan(requirement_relative, (source / "templates/REQUIREMENTS.md").read_bytes(), preserve=True)
    for name in ["DECISIONS.md", "VERIFICATION.md"]:
        plan(f".hackathon/{name}", (source / "templates" / name).read_bytes(), preserve=True)
    plan("docs/DEFENSE.md", (source / "docs/DEFENSE.md").read_bytes(), preserve=True)
    plan(".hackathon/private/INTERVIEWS.md", (
        "# 전달받은 고객 질문·답변 — 로컬 비공개\n\n"
        "아직 대화 기록 없음. 실제 전달받은 질문·답변만 Q번호로 남긴다. "
        "질문 원문이 없으면 미보존이라고 표시한다. "
        "비공개 페르소나·평가표·인증정보를 가져오지 않는다.\n"
    ).encode("utf-8"), preserve=True)
    for name in ["issue-tracker.md", "domain.md", "triage-labels.md"]:
        plan(f"docs/agents/{name}", (source / "templates" / name).read_bytes())
    for stack, files in {
        "python": ["http_fixture.py.example", "test_feature.py.example"],
        "node": ["http_fixture.mjs.example", "feature.test.mjs.example"],
    }.items():
        for name in files:
            plan(f".hackathon/testing/{stack}/{name}", (source / "templates/testing" / stack / name).read_bytes())
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
            if entry.is_file() and entry.name != ".DS_Store":
                relative = entry.relative_to(skill).as_posix()
                plan(f".agents/skills/{skill.name}/{relative}", entry.read_bytes())
    plan(".agents/skills/MATT_LICENSE.txt", (source / "vendor/matt-pocock-skills/LICENSE").read_bytes())

    agent_path = inside(root, "AGENTS.md")
    existing = agent_path.read_text(encoding="utf-8") if agent_path.exists() else ""
    instructions = (source / "templates/AGENTS.md").read_text(encoding="utf-8")
    block = BEGIN + "\n" + instructions.strip() + "\n" + END + "\n"
    block = block.replace(".hackathon/REQUIREMENTS.md", requirement_relative)
    if requirement_relative != ".hackathon/REQUIREMENTS.md":
        block = block.replace("## Cofa hackathon workflow", "## Cofa hackathon workflow\n\nThe requirements source of truth is `" + requirement_relative + "`; use it wherever kit guides mention `.hackathon/REQUIREMENTS.md`.")
    if BEGIN in existing or END in existing:
        if existing.count(BEGIN) != 1 or existing.count(END) != 1 or block.strip() not in existing:
            raise KitError("기존 kit 지시 블록이 다름. 내용을 보존하고 중단함")
        agent_content = existing
    else:
        agent_content = existing + ("\n\n" if existing else "") + block
    plans[agent_path] = agent_content.encode("utf-8")

    ignore_path = inside(root, ".gitignore")
    ignore_text = ignore_path.read_text(encoding="utf-8") if ignore_path.exists() else ""
    # Append after existing negations so the local-private rules take precedence.
    ignore_block = "# Cofa local private records\n" + "\n".join(PRIVATE_IGNORES) + "\n"
    if not ignore_text.endswith(ignore_block):
        ignore_text += ("\n" if ignore_text and not ignore_text.endswith("\n") else "") + ignore_block
    plans[ignore_path] = ignore_text.encode("utf-8")

    installed_path = inside(root, ".hackathon/install.json")
    previous = load_json(installed_path) if installed_path.exists() else None
    kit_directory = source.relative_to(root).as_posix() if source.is_relative_to(root) else None
    manifest = {
        "schema_version": 1, "matt_commit": lock["commit"], "matt_mode": mode,
        "requirements_path": requirement_relative,
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
            "requirements_path": requirement_relative,
            "next": "Read .hackathon/START_PROMPT.md in the provided Codex."}


def fingerprint(root, for_checks=False, requirements=None):
    excluded_kit = None
    installed_skills = set()
    marker = root / ".hackathon/install.json"
    if marker.is_file():
        manifest = load_json(marker)
        raw = manifest.get("kit_directory")
        if for_checks:
            installed_skills = {".agents/skills/" + name for name in manifest.get("skills", [])}
        if raw:
            excluded_kit = inside(root, raw)
            if excluded_kit == root:
                raise KitError("준비 레포 제외 경로가 전체 작업 공간을 가리킴")
    requirement_path = requirements_file(root, requirements) if for_checks else None
    files = {}
    for directory, dirnames, filenames in os.walk(root, followlinks=False):
        current = Path(directory)
        relative_dir = current.relative_to(root).as_posix()
        excluded = ({".hackathon", "docs/agents"} | installed_skills) if for_checks else {".hackathon/study", ".hackathon/tools"}
        if relative_dir in excluded or current == excluded_kit:
            dirnames[:] = []
            continue
        dirnames[:] = sorted(
            name for name in dirnames
            if name not in IGNORED_DIRS and not (current / name).is_symlink()
        )
        for name in sorted(filenames):
            path = current / name
            if path == requirement_path:
                continue
            if name == ".DS_Store" or name.endswith((".pyc", ".pyo")):
                continue
            relative = path.relative_to(root).as_posix()
            # Updating a study index after a check must not invalidate that run.
            # Full Q&A fingerprints still include DEFENSE, even though Git ignores it.
            if for_checks and relative == "docs/DEFENSE.md":
                continue
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


REQUIREMENT_FIELDS = {
    "id": ("id", "requirementid"),
    "description": ("요구사항", "description", "requirement"),
    "status": ("상태", "status"),
    "source": ("고객근거q/공식과제위치", "customerevidence", "source"),
    "acceptance": ("관찰가능한수락조건", "acceptancecriteria", "acceptance"),
    "files": ("실제구현파일", "implementationfiles", "implementation"),
    "procedure": ("검증절차v/명령·테스트", "verificationprocedure", "test"),
    "actual": ("실제결과·실행기록", "actualverificationresult", "evidence"),
    "remaining": ("남은질문·문제", "remainingissues"),
}
EMPTY = {"", "—", "-", "없음", "미확인", "미실행", "해당없음", "todo", "n/a"}


def field_text(value):
    return value.strip().strip("`*").strip()


def requirement_rows(root, explicit=None):
    path = requirements_file(root, explicit)
    if not path.is_file():
        raise KitError("요구사항 문서 없음: " + path.relative_to(root).as_posix())
    rows, errors, columns = [], [], None
    fenced = False
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if line.lstrip().startswith(("```", "~~~")):
            fenced = not fenced
            columns = None
            continue
        if fenced or not line.strip().startswith("|"):
            columns = None
            continue
        cells = [field_text(x.replace(r"\|", "|")) for x in re.split(r"(?<!\\)\|", line.strip().strip("|"))]
        if all(re.fullmatch(r":?-+:?", c.replace(" ", "")) for c in cells):
            continue
        normalized = [re.sub(r"\s+", "", c).lower() for c in cells]
        if normalized[0] in REQUIREMENT_FIELDS["id"]:
            columns = {key: normalized.index(alias) for key, aliases in REQUIREMENT_FIELDS.items()
                       for alias in aliases if alias in normalized}
            width = len(cells)
            required = set(REQUIREMENT_FIELDS) - {"remaining"}
            if not required <= columns.keys():
                errors.append(f"행 {number}: 지원 표의 필수 열 누락: {', '.join(sorted(required - columns.keys()))}")
                columns = None
            continue
        if columns is not None:
            if len(cells) != width:
                errors.append(f"행 {number}: 표 열 수 불일치. 셀 안의 |는 \\|로 작성")
                continue
            rows.append({**{key: cells[index] for key, index in columns.items()}, "line": number})
    return path, rows, errors


def q_ids(text):
    result = {str(int(n)) for n in re.findall(r"(?<![\w])Q(\d+)\b", text, re.I)}
    for left, right in re.findall(r"\bQ(\d+)\s*[~–-]\s*Q?(\d+)\b", text, re.I):
        a, b = int(left), int(right)
        if b < a or b - a > 1000:
            raise KitError("Q번호 범위가 잘못되거나 너무 큼")
        result.update(str(n) for n in range(a, b + 1))
    return result


def customer_answers(root):
    path = inside(root, ".hackathon/private/INTERVIEWS.md")
    if not path.is_file():
        return {}
    visible, fenced = [], False
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.lstrip().startswith(("```", "~~~")):
            fenced = not fenced
        elif not fenced:
            visible.append(line)
    sections = re.split(r"(?m)^(?=#{1,6}\s)", "\n".join(visible))
    answers = {}
    for section in sections:
        title, _, body = section.partition("\n")
        found = re.match(r"^#{1,6}\s+Q(\d+)\b", title, re.I)
        if not found or re.search(r"대기|미수신|pending", title, re.I):
            continue
        labeled = re.search(r"(?im)^\s*(?:답변|answer)\s*:\s*(.+)", body)
        received = (re.search(r"답변|응답|answer", title, re.I) and body.strip()) or (
            labeled and field_text(labeled[1]).lower() not in EMPTY
            and not re.search(r"^(?:답변\s*)?대기|^pending|^미수신", labeled[1], re.I))
        if received:
            key = str(int(found[1]))
            if key in answers:
                raise KitError("고객 원문에 중복 Q번호: Q" + key)
            answers[key] = section.strip()
    return answers


def binding_digest(row, answers):
    content = {k: row[k] for k in ("id", "description", "source", "acceptance")}
    content["customer_answers"] = {q: digest_bytes(answers[q].encode()) if q in answers else None
                                   for q in sorted(q_ids(row["source"]))}
    return digest_bytes(json_bytes(content))


def requirement_bindings(root, ids, explicit=None):
    if not ids:
        return {}
    _, rows, errors = requirement_rows(root, explicit)
    if errors:
        raise KitError("; ".join(errors))
    answers = customer_answers(root)
    bindings = {}
    for identifier in ids:
        matched = [r for r in rows if r["id"] == identifier]
        if len(matched) != 1:
            raise KitError("고유한 요구사항을 찾을 수 없음: " + identifier)
        bindings[identifier] = binding_digest(matched[0], answers)
    return bindings


def file_references(value):
    # Human-readable file/function references, not commands or arbitrary URLs.
    found = re.findall(r"\[[^\]]*\]\(<?([^)>]+)>?\)", value)
    value = re.sub(r"https?://\S+", "", value)
    found += re.findall(r"`([^`]+)`", value)
    found += re.findall(r"(?<![\w/.-])(?:\.?[\w.-]+/)*[\w.-]+\.[A-Za-z][A-Za-z0-9]{0,10}", value)
    result = set()
    for name in found:
        name = unquote(name).split("#", 1)[0].split(":", 1)[0].strip()
        if name and not name.startswith(("http", "check", "manual")):
            result.add(name)
    return result


def execution_log_integrity(root, record):
    """Check preservation, not authenticity, of one command's original full log."""
    schema = record.get("schema_version")
    modern = type(schema) is int and schema >= 3
    relative = record.get("log")
    if not relative:
        return {"status": "FAIL" if modern else "UNVERIFIED", "reason": "원본 로그 경로 미기록"}
    if relative != f".hackathon/checks/{record.get('id')}.log":
        return {"status": "FAIL", "reason": "실행 ID의 원본 로그 경로와 다름"}
    try:
        path = inside(root, relative)
        if not path.is_file():
            return {"status": "FAIL", "reason": "원본 로그 파일 없음"}
        expected = record.get("log_sha256")
        if expected is None and not modern:
            return {"status": "UNVERIFIED", "reason": "이전 기록: 원본 로그 내용 지문 미적용"}
        if not isinstance(expected, str) or not re.fullmatch(r"[0-9a-f]{64}", expected):
            return {"status": "FAIL", "reason": "원본 로그 내용 지문이 없거나 잘못됨"}
        if digest_file(path) != expected:
            return {"status": "FAIL", "reason": "원본 로그 내용이 기록 당시와 다름"}
    except (KitError, OSError) as exc:
        return {"status": "FAIL", "reason": "원본 로그 확인 실패: " + str(exc)}
    return {"status": "PASS", "reason": "원본 로그 존재·내용 지문 일치"}


def audit_requirements(root, explicit=None):
    path, rows, errors = requirement_rows(root, explicit)
    warnings, seen, unverified_logs = [], set(), set()
    answers = customer_answers(root)
    current = fingerprint(root, for_checks=True, requirements=explicit)["digest"]
    for row in rows:
        rid = row["id"]
        def issue(message):
            errors.append(rid + ": " + message)
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]*\d+", rid) or rid.lower() in seen:
            issue("ID 형식이 잘못되거나 중복됨")
        seen.add(rid.lower())
        status = row["status"].lower()
        if status not in {"proposed", "confirmed", "implemented", "verified", "blocked"}:
            issue("지원하지 않는 상태")
        for key in ("description", "acceptance"):
            if row[key].lower() in EMPTY:
                (warnings if status == "proposed" else errors).append(rid + ": 빈 " + key)
        if status != "proposed":
            refs = q_ids(row["source"])
            for q in refs:
                if q not in answers:
                    issue("실제 답변 절이 없는 고객 근거: Q" + q)
            sources = file_references(row["source"])
            if not refs and not sources:
                issue("고객 Q 또는 공식 과제 파일 근거 필요")
            for source in sources:
                if not inside(root, source).is_file():
                    issue("근거 파일 없음: " + source)
        if status in {"implemented", "verified"}:
            files = file_references(row["files"])
            if not files:
                issue("실제 구현 파일 경로 필요")
            for name in files:
                if not inside(root, name).is_file():
                    issue("구현 파일 없음: " + name)
        if status == "verified":
            if row["procedure"].lower() in EMPTY:
                issue("검증 절차 필요")
            if re.search(r"미실행|미검증|대기|NOT_RUN|NOT_TESTED", row["actual"] + " " + row.get("remaining", ""), re.I):
                issue("미실행·미검증·대기 기록과 Verified가 불일치")
            ids = re.findall(r"\b(check|manual):([a-z0-9][a-z0-9_-]{0,63})\b", row["actual"])
            if not ids:
                issue("실제 결과 셀에 check:<실행ID> 또는 manual:<관찰ID> 필요")
            for kind, check_id in ids:
                try:
                    record = load_json(inside(root, f".hackathon/checks/{check_id}.json"))
                except KitError:
                    issue("실행/관찰 기록을 읽을 수 없음: " + check_id)
                    continue
                if not isinstance(record, dict):
                    issue("실행 기록 객체 형식이 잘못됨: " + check_id)
                    continue
                if record.get("id") != check_id or record.get("result") != "PASS":
                    issue("통과한 실행/관찰이 아님: " + check_id)
                if kind == "manual" and record.get("kind") != "participant-attestation":
                    issue("수동 관찰 기록이 아님: " + check_id)
                if kind == "check" and (record.get("kind") != "executed-command" or record.get("exit_code") != 0):
                    issue("명령 실행 근거가 아님: " + check_id)
                if record.get("kind") == "executed-command":
                    integrity = execution_log_integrity(root, record)
                    if integrity["status"] == "FAIL":
                        issue(integrity["reason"] + ": " + check_id)
                    elif integrity["status"] == "UNVERIFIED":
                        unverified_logs.add(check_id)
                        warnings.append(rid + ": " + integrity["reason"] + ": " + check_id)
                if not record.get("stable_source") or record.get("source_after") != current:
                    issue("실행 당시 소스와 다름. 재검증 필요: " + check_id)
                bindings = record.get("requirements", {})
                if not isinstance(bindings, dict) or bindings.get(rid) != binding_digest(row, answers):
                    issue("해당 요구·수락 조건·고객 근거와 연결되지 않음: " + check_id)
    return {"status": "FAIL" if errors else "NOT_RUN" if not rows else "UNVERIFIED" if unverified_logs else "PASS",
            "requirements_path": path.relative_to(root).as_posix(), "requirements": len(rows),
            "not_marked_verified": [r["id"] for r in rows if r["status"].lower() != "verified"],
            "errors": errors, "warnings": warnings, "unverified_log_ids": sorted(unverified_logs),
            "scope": "Reference structure and recorded freshness only; no semantic coverage, customer authenticity or understanding guarantee."}


def test_summary(command, output, runner):
    if runner == "auto":
        names = [Path(x).name for x in command]
        modules = {right for left, right in zip(names, names[1:]) if left == "-m"}
        runner = "pytest" if names[0].startswith("pytest") or "pytest" in modules else (
            "unittest" if "unittest" in modules else
            "node" if names[0] in {"node", "nodejs", "node.exe"} and "--test" in names else "none")
    text = re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", output)
    total = skipped = None
    todo = cancelled = failed = 0
    ambiguous = False
    if runner == "unittest":
        ran = re.findall(r"(?m)^Ran (\d+) tests?\b", text)
        if ran:
            total = int(ran[-1])
            skipped_rows = re.findall(r"(?m)^(?:OK|FAILED)\s*\([^\n]*\bskipped=(\d+)", text)
            skipped = int(skipped_rows[-1]) if skipped_rows else 0
            problems = re.findall(r"(?m)^FAILED\s*\(([^\n]*)\)", text)
            if problems:
                failed = sum(int(n) for n in re.findall(r"(?:failures|errors)=(\d+)", problems[-1]))
    elif runner == "pytest":
        groups = []
        for line in text.splitlines():
            if re.search(r"\b\d+ (?:passed|failed|skipped|errors?|xfailed|xpassed)\b.*\bin \d", line):
                groups.append({key: int(n) for n, key in re.findall(
                    r"\b(\d+) (passed|failed|skipped|errors?|xfailed|xpassed)\b", line)})
            elif re.search(r"\bno tests ran\b", line):
                groups.append({})
        # A wrapper may print several runs or repeat a summary. Keep every failure,
        # but do not invent a combined test count or choose the last successful run.
        failed = sum(g.get("failed", 0) + g.get("error", 0) + g.get("errors", 0) for g in groups)
        ambiguous = len(groups) > 1
        if len(groups) == 1:
            total, skipped = sum(groups[0].values()), groups[0].get("skipped", 0)
    elif runner == "node":
        groups, counts = [], {}
        for key, n in re.findall(r"(?m)^#\s+(tests|pass|fail|cancelled|skipped|todo)\s+(\d+)\s*$", text):
            if key == "tests" and counts:
                groups.append(counts)
                counts = {}
            counts[key] = int(n)
        if counts:
            groups.append(counts)
        failed = sum(c.get("fail", 0) for c in groups)
        cancelled = sum(c.get("cancelled", 0) for c in groups)
        required = {"tests", "pass", "fail", "skipped", "todo"}
        if groups and all(required <= c.keys() and c["tests"] == sum(c.get(k, 0) for k in
                ("pass", "fail", "cancelled", "skipped", "todo")) for c in groups):
            total = sum(c["tests"] for c in groups)
            skipped = sum(c["skipped"] for c in groups)
            todo = sum(c["todo"] for c in groups)
    effective = total - skipped - todo - cancelled if total is not None else None
    state = "NOT_APPLICABLE" if runner == "none" else "UNKNOWN" if total is None else (
        "NOT_RUN" if effective <= 0 else "RAN")
    return {"runner": runner, "state": state, "total": total, "skipped": skipped,
            "todo": todo, "cancelled": cancelled, "failed": failed, "effective": effective,
            "ambiguous": ambiguous}


def record_check(root, check_id, command, timeout, runner="auto", requirement_ids=(), requirements=None):
    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,63}", check_id):
        raise KitError("체크 ID에는 소문자·숫자·밑줄·하이픈만 사용")
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        raise KitError("실행할 명령이 없음")
    if timeout <= 0:
        raise KitError("timeout은 양수")
    output = inside(root, f".hackathon/checks/{check_id}.json")
    log_path = inside(root, f".hackathon/checks/{check_id}.log")
    if output.exists() or log_path.exists():
        raise KitError("이미 있는 실행 기록은 보존함. tests-02처럼 새 ID 사용")
    bindings = requirement_bindings(root, requirement_ids, requirements)
    before = fingerprint(root, for_checks=True, requirements=requirements)["digest"]
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
    after = fingerprint(root, for_checks=True, requirements=requirements)["digest"]
    summary = test_summary(command, stdout + "\n" + stderr, runner)
    result = "FAIL" if summary["failed"] or summary["cancelled"] or exit_code and not (exit_code == 5 and summary["runner"] in {"pytest", "unittest"} and summary["state"] == "NOT_RUN") else (
        "NOT_RUN" if summary["state"] == "NOT_RUN" else
        "UNVERIFIED" if before != after or summary["state"] == "UNKNOWN" else "PASS")
    record = {
        "schema_version": 3, "kind": "executed-command", "result": result,
        "id": check_id, "command": command, "cwd": ".", "started_at": started,
        "finished_at": utc_now(), "exit_code": exit_code, "timed_out": timed_out,
        "stdout": stdout[-32000:], "stderr": stderr[-32000:],
        "output_truncated": len(stdout) > 32000 or len(stderr) > 32000,
        "log": log_path.relative_to(root).as_posix(), "tests": summary,
        "source_before": before, "source_after": after, "stable_source": before == after,
        "requirements": bindings,
    }
    # A test command can create files, so check the output route again afterwards.
    output = inside(root, f".hackathon/checks/{check_id}.json")
    log_path = inside(root, f".hackathon/checks/{check_id}.log")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("x", encoding="utf-8") as log:
        log.write("STDOUT\n" + stdout + "\nSTDERR\n" + stderr)
    record["log_sha256"] = digest_file(log_path)
    write_json(output, record)
    return record


def record_manual(root, check_id, result, note, requirement_ids=(), requirements=None):
    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,63}", check_id) or not note.strip():
        raise KitError("관찰 ID와 참가자가 보고한 구체적인 관찰 내용 필요")
    if result not in {"PASS", "FAIL", "NOT_RUN"}:
        raise KitError("수동 결과는 PASS/FAIL/NOT_RUN")
    target = inside(root, f".hackathon/checks/{check_id}.json")
    if target.exists() or inside(root, f".hackathon/checks/{check_id}.log").exists():
        raise KitError("이미 있는 실행/관찰 ID는 보존함")
    stamp = fingerprint(root, for_checks=True, requirements=requirements)["digest"]
    record = {"schema_version": 2, "kind": "participant-attestation", "id": check_id,
              "result": result, "observer": "participant", "recorded_at": utc_now(),
              "note": note, "source_before": stamp, "source_after": stamp, "stable_source": True,
              "requirements": requirement_bindings(root, requirement_ids, requirements),
              "scope": "Participant reports this observation for the current source. No automated observation or browser action."}
    write_json(target, record)
    return record


def review_scope(root, base=None):
    def git(*args):
        return subprocess.run(["git", "-C", str(root), *args], capture_output=True,
                              text=True, timeout=10, check=False)
    try:
        top = git("rev-parse", "--show-toplevel")
        if top.returncode:
            return {"status": "UNAVAILABLE", "reason": "Git 작업 공간 아님. 실제 파일을 직접 검토할 것"}
        if Path(top.stdout.strip()).resolve() != root:
            return {"status": "UNAVAILABLE", "reason": "--workspace가 Git 루트와 다름. 과제의 실제 Git 루트를 지정하거나 파일을 직접 검토할 것"}
    except FileNotFoundError:
        return {"status": "UNAVAILABLE", "reason": "Git 없음. 실제 파일을 직접 검토할 것"}
    marker = inside(root, ".hackathon/install.json")
    if not base and marker.is_file():
        base = load_json(marker).get("base_commit")
    base = base or git_base(root)
    if base:
        resolved = git("rev-parse", "--verify", "--end-of-options", base + "^{commit}")
        if resolved.returncode or not re.fullmatch(r"[0-9a-f]{40,64}\s*", resolved.stdout):
            raise KitError("리뷰 기준 커밋을 찾을 수 없음")
        base = resolved.stdout.strip()
    files = set()
    for args in (["diff", "--name-only", "-z", base, "--"] if base else ["diff", "--name-only", "-z", "--"],
                 ["diff", "--cached", "--name-only", "-z", "--"],
                 ["ls-files", "--others", "--exclude-standard", "-z"]):
        value = git(*args)
        if value.returncode:
            raise KitError("리뷰 대상 열거 실패: " + value.stderr.strip())
        files.update(name for name in value.stdout.split("\0") if name)
    return {"status": "ENUMERATED", "base_commit": base, "files": sorted(files),
            "scope": "Committed + staged + unstaged + untracked paths only. Not a code review verdict."}


def preflight(root, url=None):
    path = requirements_file(root)
    report = {"status": "OBSERVED", "python": platform.python_version(),
              "tools": {name: shutil.which(name) is not None for name in ("git", "node", "npm")},
              "requirements_path": path.relative_to(root).as_posix(), "requirements_exists": path.is_file(),
              "http": {"result": "NOT_RUN"}, "scope": "Read-only environment observation; not UI usability or submission readiness."}
    if url:
        try:
            target = urlsplit(url)
            host, port = target.hostname or "", target.port
        except ValueError as exc:
            raise KitError("잘못된 로컬 URL") from exc
        try:
            local = host == "localhost" or ipaddress.ip_address(host).is_loopback
        except ValueError:
            local = False
        if target.scheme not in {"http", "https"} or not local or target.username or target.password:
            raise KitError("preflight URL은 인증정보 없는 로컬 loopback HTTP(S)만 허용")
        connection = (http.client.HTTPSConnection if target.scheme == "https" else http.client.HTTPConnection)(
            host, port, timeout=3)
        try:
            connection.request("GET", (target.path or "/") + ("?" + target.query if target.query else ""))
            response = connection.getresponse()
            report["http"] = {"result": "PASS" if 200 <= response.status < 300 else "FAIL",
                              "status_code": response.status, "url": url,
                              "notice": "No redirects followed; response body not recorded."}
        except (OSError, http.client.HTTPException) as exc:
            report["http"] = {"result": "FAIL", "error": type(exc).__name__}
        finally:
            connection.close()
    return report


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
            if not isinstance(record, dict) or record.get("id") != check_id:
                raise KitError(f"{identifier}: 잘못된 실행 기록")
            if record.get("kind") == "participant-attestation":
                if record.get("observer") != "participant" or record.get("result") not in {"PASS", "FAIL", "NOT_RUN"}:
                    raise KitError(f"{identifier}: 잘못된 참가자 관찰 기록")
                nonempty(record.get("note"), f"{identifier}.manual.note")
                nonempty(record.get("recorded_at"), f"{identifier}.manual.recorded_at")
            elif type(record.get("exit_code")) is not int or not record.get("finished_at"):
                raise KitError(f"{identifier}: 잘못된 명령 실행 기록")
            else:
                integrity = execution_log_integrity(root, record)
                if integrity["status"] == "FAIL":
                    raise KitError(f"{identifier}: {integrity['reason']}: {check_id}")
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
            if record.get("kind") == "participant-attestation":
                full.append(f"- 참가자 수동 진술 `{check_id}`: {record['result']}, {record['recorded_at']} · {record['note']}\n")
            else:
                full.append(f"- 실행 `{check_id}`: {record.get('result', 'legacy/unassessed')}, exit={record['exit_code']}, {record['finished_at']}\n")
                integrity = execution_log_integrity(root, record)
                full.append(f"- 로그 보관 확인 `{check_id}`: {integrity['status']} · {integrity['reason']}\n")
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
    unverified = set()
    for question in data["questions"]:
        for check_id in question.get("check_ids", []):
            record = load_json(inside(root, f".hackathon/checks/{check_id}.json"))
            if record.get("kind") != "participant-attestation" and execution_log_integrity(root, record)["status"] == "UNVERIFIED":
                unverified.add(check_id)
    return {"status": "verified" if verify_only else "rendered", "questions": len(data["questions"]),
            "unverified_log_ids": sorted(unverified),
            "scope": "file fingerprint, references, log preservation, check records, and rendered document consistency only"}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="action", required=True)
    for action in ["install", "fingerprint", "check", "manual-check", "audit-requirements", "preflight", "review-scope", "prepare-qa", "render-qa", "verify-qa"]:
        sub = commands.add_parser(action)
        sub.add_argument("--workspace", default=".")
        if action == "install":
            sub.add_argument("--matt", choices=["all", "core", "none"], default="core")
        if action in {"install", "check", "manual-check", "audit-requirements"}:
            sub.add_argument("--requirements", help="기존 요구사항 Markdown 정본 경로")
        if action in {"check", "manual-check"}:
            sub.add_argument("--requirement", action="append", default=[], help="연결할 R ID (반복 가능)")
        if action == "manual-check":
            sub.add_argument("--id", required=True)
            sub.add_argument("--result", choices=["PASS", "FAIL", "NOT_RUN"], required=True)
            sub.add_argument("--note", required=True)
        if action == "preflight":
            sub.add_argument("--url", help="선택: 이미 실행 중인 로컬 서버 주소")
        if action == "review-scope":
            sub.add_argument("--base", help="설치 시 기준 대신 사용할 Git commit/ref")
        if action == "check":
            sub.add_argument("--id", required=True)
            sub.add_argument("--timeout", type=int, default=300)
            sub.add_argument("--test-runner", choices=["auto", "none", "unittest", "pytest", "node"], default="auto")
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
                result = install(root, args.matt, args.requirements)
            elif args.action == "fingerprint":
                result = fingerprint(root)
            elif args.action == "check":
                if args.timeout <= 0:
                    raise KitError("timeout은 양수")
                result = record_check(root, args.id, args.command, args.timeout,
                                      args.test_runner, args.requirement, args.requirements)
                print(json.dumps(result, ensure_ascii=False, indent=2))
                if result["exit_code"] == 0 and result["result"] != "PASS":
                    return 2
                return result["exit_code"] if result["exit_code"] >= 0 else 128 - result["exit_code"]
            elif args.action == "manual-check":
                result = record_manual(root, args.id, args.result, args.note, args.requirement, args.requirements)
                print(json.dumps(result, ensure_ascii=False, indent=2))
                return {"PASS": 0, "FAIL": 1, "NOT_RUN": 2}[result["result"]]
            elif args.action == "audit-requirements":
                result = audit_requirements(root, args.requirements)
                print(json.dumps(result, ensure_ascii=False, indent=2))
                return {"PASS": 0, "FAIL": 1, "NOT_RUN": 2, "UNVERIFIED": 2}[result["status"]]
            elif args.action == "review-scope":
                result = review_scope(root, args.base)
            elif args.action == "preflight":
                result = preflight(root, args.url)
                print(json.dumps(result, ensure_ascii=False, indent=2))
                return 1 if result["http"]["result"] == "FAIL" else 0
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
