## Cofa hackathon workflow

The official task README and current exam instructions take priority. Preserve provided files and existing instructions. At startup read `.hackathon/INTERVIEW_PROTOCOL.md`. Before implementation read `.hackathon/AUTOMATED_TESTING.md`; consult its command reference only when needed. Do not load every skill or reference at startup.

### Environment and timing

- Use the provided Codex and permitted models; participant guidance names 6.1 Sol, 5.6 Terra and 6.0 Luna. Check actual platform labels rather than inventing model IDs. Do not update Codex, connect external AI/personal keys/subscriptions, or change platform/proctor settings. Use tokens and resources for the task.
- Public instructions, skills, templates and partial code may be imported within the exam rules. Do not import private repositories, personal PC files or a complete external solution. Used repositories must remain public until second-round results. The participant uses platform AI for external information rather than browsing outside directly.
- Do not push Git, create external issues/PRs, deploy outside, or transmit task files, answers or logs. Public material imports do not authorize outgoing transfers. Do not bypass restrictions; report platform failures through Cofa Helper or the provided issue channel.
- Computer Use/browser automation is prohibited, including Playwright/Puppeteer/Selenium UI tests. Use CLI, unit tests and permitted local HTTP requests; the participant operates Browser manually. Bind the app to `0.0.0.0`, report its actual port/path, and keep its server running. Do not assume port 3000 or require a tunnel.
- Participant guidance: 2026-10-31 10:00–14:00 KST, at most 180 minutes for implementation, then six five-minute questions; generation waits also consume the absolute deadline. Use the actual timer and ask the participant for remaining time when necessary. For personal rehearsals use their stated timing and monitoring conditions.
- Reserve time for final regression, participant UI checks, implementation Q&A, review and direct submission; reduce scope when late. Check required files/save state and leave submission time. Finish AI-assisted study before submission is fixed, then stop AI use. Do not answer live follow-up questions or assume notes/code remain accessible; follow-up answers are typed by the participant without AI or copy/paste.

### Customer discovery and Matt skills

The participant relays questions and real customer answers. Business facts come from those answers or the official task; technical facts come from local inspection. Prioritize uncertainties that change behavior, acceptance criteria or scope. Follow the interview protocol's six discovery areas and implementation entry criteria; never finish discovery after one example. Reuse existing answers and propose customer workflow feedback after the first working slice and before scope freeze. Proposed questions are not confirmation.

| Need | Skill and project adjustment |
| --- | --- |
| Customer questions | Explicit `$grill-with-docs`; use open questions, not recommended business answers for the relay participant to approve. Do not force resolution of every design branch. |
| Terms and decisions | `domain-modeling`; record confirmed terms in GLOSSARY and important choices with R/D IDs, reasons and alternatives. |
| Confirmed implementation | Explicit `$implement`, with `tdd` and `codebase-design` as needed. Reuse agreed public test boundaries; do not request approval for every test. |
| Reproducible defects | `diagnosing-bugs`; retain the failure and rerun its procedure after fixing. |
| Review | `code-review`; compare official conditions and the requirements ledger to committed, staged, unstaged, untracked and deleted files. `review-scope` enumerates these but is not the review itself. |
| Before submission | `$implementation-brief` for actual implementation Q&A and participant review. |
| Session change | `$handoff` with actual files, unresolved questions and verification state. |

Use only needed skills and keep Matt's original SKILL.md unchanged. If invocation is unavailable, read the bundled skill and apply its procedure with available tools; do not update Codex or add plugins/MCP/accounts. Local Markdown tracking in `docs/agents/issue-tracker.md` is already configured; upstream setup is unnecessary. Local commits are optional when unavailable and never authorize push. If permitted independent reviewers are unavailable, accurately label a same-session review rather than claiming independent review.

### Requirements and evidence

Reuse `.hackathon/REQUIREMENTS.md`, `.hackathon/DECISIONS.md` and `.hackathon/VERIFICATION.md`; do not add a parallel PRD/ticket/evidence system. The installed manifest's `requirements_path` identifies the existing requirements source of truth. Preserve IDs and update only changed entries, briefly.

- After each relayed answer, separate facts from hypotheses, assign confirmed requirements R IDs, link actual Q/answer or official task locations, and define observable acceptance criteria. Propose important unanswered questions; proceed with independent confirmed work. Do not turn a convenience request into customer-confirmed P0.
- Before implementation identify the related R IDs. Record important decisions with their reasons, alternatives and actual files. Do not portray retrospective reasoning as historical intent or planned files as existing implementation.
- Status meanings: Proposed = unconfirmed; Confirmed = customer/official evidence; Implemented = confirmed behavior implemented with verification outstanding; Verified = actual evidence for every acceptance criterion; Blocked = a recorded dependency prevents progress. Partial implementation stays Confirmed with the remainder noted. Preserve prior state/evidence when blocked and continue independent work.
- Link each R to real procedures, commands, inputs, expected/observed results, pass/fail and execution IDs. Actual result cells use `check:<id>` or `manual:<id>`. Never claim an unrun test passed, fabricate missing questions/results, or promote partial coverage to Verified. Reassess after relevant code, criteria, answer or environment changes; retain past results as history.
- Keep raw relayed Q&A in Git-ignored `.hackathon/private/INTERVIEWS.md`; use `## Q1` with `질문:` and `답변:` for actual conversations. Keep only minimal summaries and Q references in the ledger. If the original question was not preserved, say so. Never import hidden personas/evaluation files or credentials.
- Logs and study outputs stay in ignored `.hackathon/checks/` and `.hackathon/study/`. Ignore rules do not protect already tracked files or erase Git history. Check tracked files/history separately; summaries, code and synthetic data also require publication review. Never publish without the user's separate approval; exam transfer restrictions still apply.

Markdown records, skill invocation and structural audit PASS do not guarantee official scores, evaluator access, semantic correctness or participant understanding.

### Implementation, verification and completion

Own intermediate verification using the automated testing guide: task-specific tests at real production boundaries, isolated data/test-owned servers, execution, failure analysis, fix and rerun of the original procedure under a new ID. Do not substitute a duplicated app/calculation or weaken customer criteria to pass tests. Preserve participant data and the running app.

Do not request a click test for every feature. Keep business-rule and textual workflow questions active. Automatic PASS with final UI pending remains Implemented where UI is an acceptance criterion and does not block independent work. After automatic regression, collect a final UI checklist in VERIFICATION with actual R IDs, URLs, inputs/actions and expected observations. Record only relayed real observations; after a UI fix rerun affected automatic checks and relevant UI steps.

Use `check --requirement <R-ID>` for real execution records. Zero tests/all skipped or todo are NOT_RUN; unrecognized summaries or changing sources are not verified. Before completion use `audit-requirements` and read actual files for review; consult `.hackathon/references/validation-tools.md` for command syntax and limitations.

Before submission is fixed, invoke `$implementation-brief` to produce `.hackathon/study/IMPLEMENTATION_QA.md` and `LAST_REVIEW.md`, run `python3 .hackathon/tools/kit.py verify-qa --workspace .`, and leave participant review time. Recheck Q&A after source/evidence changes. Invite the participant to explain key choices when available; unanswered invitations do not prove understanding or stop independent work. The participant confirms submission manually.

Report four things briefly: implemented requirements; actually verified requirements; unconfirmed/unimplemented items; known failure conditions.
