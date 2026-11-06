#!/usr/bin/env python3
"""Read-only, bounded mechanical preflight; never a semantic/publication gate.

Usage: python -B scripts/preflight_review.py WORKSPACE [WORKSPACE ...]
Use --through edited to require all pre-review artifacts even in an early workspace.
Ordinary-reader workflows 1.9/1.10 require a current policy lock from source onward.
Opt in to --final-pass-set only after the final full reading passes; legacy books are not migrated.
Exit 0 means no errors in checks that ran; inspect not_yet before proceeding.
Exit 1 means mechanical errors; exit 2 means invalid command-line arguments.
No lock, approval, review answer, state change, hash refresh or report file is written.
"""
from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys

# Also suppress caches when imported by another Python program.
sys.dont_write_bytecode = True

from validate_workspace import ORDER, STAGE_FILES, read_json, read_jsonl

WORKFLOW = [
    "intake", "diagnosis", "source", "source_adjudicated", "normalized",
    "book_understood", "reader_designed", "reader_units_built", "sample_accepted",
    "modernized", "edited", "reader_revised", "final_adjudicated", "publication", "complete",
]
EXTRA_ARTIFACTS = {
    "40-modernized/book-understanding.md": "book_understood",
    "50-edited/editorial-plan.md": "reader_designed",
    "50-edited/illustration-plan.md": "reader_designed",
    "50-edited/reader-units.json": "reader_units_built",
    "50-edited/production-plan.json": "sample_accepted",
    "50-edited/modern-reading.md": "edited",
    "50-edited/source-reader-map.jsonl": "edited",
    "50-edited/reader-unit-rendering.json": "edited",
}
CHECKS = [*ORDER, "acceptance_policy_lock", "reader_units", "production_plan", "source_reader_map", "reader_unit_rendering", "source_anchors", "final_pass_set"]
BOUNDARY = (
    "仅检查现有记录的机械完整性与绑定；ready 不代表语义通过、独立审读完成或出版通过。"
    "是否值得开始语义审读仍由人或 agent 判断。正式阶段、政策锁、疑点、忠实度、读者与 PDF 验收保持原要求。"
)


def readonly_guard() -> None:
    """Prevent accidental writes or subprocesses inside each validator worker."""
    mutations = {
        "os.remove", "os.rmdir", "os.mkdir", "os.rename", "os.link", "os.symlink",
        "os.truncate", "os.chmod", "os.chown", "os.utime", "os.system",
        "os.posix_spawn", "subprocess.Popen",
    }

    def audit(event, args):
        if event == "open":
            mode, flags = args[1], args[2]
            if (isinstance(mode, str) and any(c in mode for c in "wax+")) or (
                isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND)
            ):
                raise PermissionError("preflight read-only worker blocked a file write")
        elif event in mutations:
            raise PermissionError(f"preflight read-only worker blocked {event}")

    sys.addaudithook(audit)


def check_source_anchors(root: Path) -> list[str]:
    """Early subset of validate_delivery's compact-final source anchor contract.

Do not manufacture or require a fidelity-review verdict to inspect its future inputs.
The formal delivery validator remains authoritative and must still run later.
"""
    source = read_jsonl(root / STAGE_FILES["source"])
    manuscript = (root / "50-edited/modern-reading.md").read_text(encoding="utf-8")
    return [
        f"missing final-reader source anchor: <!-- source:{row['block_id']} -->"
        for row in source
        if row.get("disposition") not in {"noncontent", "excluded_with_reason", "unreadable"}
        and f"<!-- source:{row['block_id']} -->" not in manuscript
    ]


def check_final_pass_set(root: Path) -> list[str]:
    """Opt-in declaration/binding/line-coverage check, not proof of actual reading.

Reuse the frozen stability gate, then reject local regressions or unverifiable
chapter-name-only coverage. Never generate reader answers or alter old records.
"""
    from validate_integrity import workspace_review_protocol, validate_review_stability
    book = read_json(root / "book.json")
    policy_path = root / "50-edited/review-policy.json"
    policy = read_json(policy_path) if policy_path.is_file() else {}
    errors: list[str] = []
    workspace_review_protocol(root, book, policy, errors)
    if errors:
        return errors
    if book.get("delivery_mode") != "ordinary_reader" or book.get("workflow_schema_version") not in {"1.9", "1.10"}:
        return []
    manuscript_path = root / "50-edited/modern-reading.md"
    validate_review_stability(root, manuscript_path, errors)
    # focused-v1 invokes the same check inside the formal stability gate.
    if book.get("review_protocol") != "focused-v1":
        from validate_full_read import validate_full_read_coverage
        validate_full_read_coverage(root, manuscript_path, errors)
    return errors


def worker(root: Path, check: str) -> dict:
    readonly_guard()
    try:
        if check in ORDER:
            import validate_workspace
            sys.argv = [str(Path(validate_workspace.__file__)), str(root), "--stage", check]
            captured = io.StringIO()
            with contextlib.redirect_stdout(captured):
                validate_workspace.main()
            result = json.loads(captured.getvalue())
            return {"errors": result["errors"], "counts": result.get("counts", {})}
        if check == "acceptance_policy_lock":
            from validate_integrity import validate_policy_lock
            errors: list[str] = []
            validate_policy_lock(root, errors)
        elif check == "source_reader_map":
            from validate_integrity import validate_scope
            errors = []
            validate_scope(root, read_jsonl(root / STAGE_FILES["source"]),
                           (root / "50-edited/modern-reading.md").read_text(encoding="utf-8"), errors)
        elif check in {"reader_units", "reader_unit_rendering"}:
            from validate_reader_units import validate
            errors = validate(root, publication=check == "reader_unit_rendering")
        elif check == "production_plan":
            from validate_production_plan import validate
            errors = validate(root)
        elif check == "final_pass_set":
            errors = check_final_pass_set(root)
        else:
            errors = check_source_anchors(root)
        return {"errors": errors}
    except Exception as exc:
        # A malformed record must not hide errors in other stages/checks/books.
        return {"errors": [f"{check} could not complete: {type(exc).__name__}: {exc}"]}


def run_check(root: Path, check: str, timeout: float) -> dict:
    try:
        process = subprocess.run(
            [sys.executable, "-B", str(Path(__file__).resolve()), str(root), "--_check", check],
            capture_output=True, text=True, timeout=timeout,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        )
        result = json.loads(process.stdout)
        if not isinstance(result, dict) or not isinstance(result.get("errors"), list):
            raise ValueError("validator did not return an errors array")
        if process.returncode not in {0, 1}:
            raise ValueError(f"validator exited {process.returncode}: {process.stderr[-800:]}")
        return result
    except subprocess.TimeoutExpired:
        return {"errors": [f"{check} exceeded {timeout:g}s; rerun this validator separately before review"]}
    except (OSError, ValueError) as exc:
        return {"errors": [f"{check} did not produce a usable result: {exc}"]}


def inspect_workspace(root: Path, through: str = "auto", timeout: float = 30, final_pass_set: bool = False) -> dict:
    root = root.expanduser().resolve()
    metadata_errors: list[str] = []
    metadata: dict[str, dict] = {}
    for name in ("book.json", "run-state.json"):
        try:
            metadata[name] = read_json(root / name)
        except (OSError, ValueError) as exc:
            metadata_errors.append(f"{name}: {exc}")
            metadata[name] = {}
    book, state = metadata["book.json"], metadata["run-state.json"]
    from validate_integrity import workspace_review_protocol
    policy_path = root / "50-edited/review-policy.json"
    try:
        policy = read_json(policy_path) if policy_path.is_file() else {}
        workspace_review_protocol(root, book, policy, metadata_errors)
    except (OSError, ValueError) as exc:
        metadata_errors.append(f"review-policy.json: {exc}")
    if not isinstance(book.get("delivery_mode"), str) or book["delivery_mode"] not in {"ordinary_reader", "source_comparison", "evidence_archive"}:
        metadata_errors.append("book.json requires explicit delivery_mode")
    if not isinstance(book.get("book_id"), str) or not book["book_id"].strip() or state.get("book_id") != book.get("book_id"):
        metadata_errors.append("book.json and run-state.json require the same nonempty book_id")
    stages = state.get("stages", {})
    if not isinstance(stages, dict):
        metadata_errors.append("run-state.json stages must be an object")
        stages = {}

    reached = {"intake"}
    current = state.get("current_stage")
    if isinstance(current, str) and current in WORKFLOW:
        reached.add(current)
    for name, record in stages.items():
        if not isinstance(record, dict):
            metadata_errors.append(f"run-state.json stage {name} must be an object")
        elif record.get("status") is not None and not isinstance(record["status"], str):
            metadata_errors.append(f"run-state.json stage {name} status must be a string")
        elif name in WORKFLOW and record.get("status") not in {None, "pending", "not_started", "not_applicable", "skipped"}:
            reached.add(name)
    for relative, stage in {**{v: k for k, v in STAGE_FILES.items()}, **EXTRA_ARTIFACTS}.items():
        if (root / relative).exists():
            reached.add(stage)
    if through != "auto":
        reached.add(through)
    frontier = max(reached, key=WORKFLOW.index)

    checks: dict[str, dict] = {}
    issues: list[dict] = []
    issue_ids: dict[str, str] = {}

    def record(name: str, result: dict, action: str) -> None:
        refs = []
        for message in result.get("errors", []):
            if message not in issue_ids:
                issue_id = f"E{len(issues) + 1:03d}"
                issue_ids[message] = issue_id
                issues.append({"id": issue_id, "message": message, "checks": [], "action": action})
            issue_id = issue_ids[message]
            issue = issues[int(issue_id[1:]) - 1]
            if name not in issue["checks"]:
                issue["checks"].append(name)
            if issue_id not in refs:
                refs.append(issue_id)
        checks[name] = {"readiness": "error" if refs else "ready", "issues": refs}
        if result.get("counts"):
            checks[name]["counts"] = result["counts"]

    record("metadata", {"errors": metadata_errors}, "修正元数据结构与标识；不要修改验收结论来消除错误。")
    ordinary = book.get("delivery_mode") == "ordinary_reader"
    version = str(book.get("workflow_schema_version") or "")
    specs = [(name, name, True) for name in ORDER] + [
        ("acceptance_policy_lock", "source", ordinary and version in {"1.9", "1.10"}),
        ("reader_units", "reader_units_built", ordinary and version == "1.10"),
        ("production_plan", "sample_accepted", ordinary),
        ("source_reader_map", "edited", ordinary and version in {"1.9", "1.10"}),
        ("reader_unit_rendering", "edited", ordinary and version == "1.10"),
        ("source_anchors", "edited", ordinary and version in {"1.8", "1.9", "1.10"}),
    ]
    if final_pass_set:
        # An explicit request must report missing final material, not defer it.
        specs.append(("final_pass_set", "intake", ordinary and version in {"1.9", "1.10"}))
    for name, due, applicable in specs:
        if not applicable:
            checks[name] = {"readiness": "not_applicable", "reason": "当前交付模式或版本不要求此项；不自动迁移旧版。"}
        elif WORKFLOW.index(frontier) < WORKFLOW.index(due):
            checks[name] = {"readiness": "not_yet", "due_at": due}
        else:
            action = (
                f"修正对应文件后重跑 validate_workspace.py WORKSPACE --stage {name}。"
                if name in ORDER else
                "首次语义审读前运行 lock_acceptance_policy.py；旧锁失效时先确认策略/范围变更，重锁并重审受影响内容。"
                if name == "acceptance_policy_lock" else
                "保存真实全文审读的当前稿绑定、逐段起止行与证据；局部回归不得改标签充当全文轮次。"
                if name == "final_pass_set" else
                "按报错修正实际文件、引用与证据；变更后重审受影响内容，不只刷新哈希或补通过状态。"
            )
            record(name, run_check(root, name, timeout), action)
    return {
        "workspace": str(root), "observed_through": frontier, "requested_through": through,
        "mechanical_status": "errors_found" if issues else "no_errors_in_executed_checks",
        "checks": checks, "issues": issues,
        "semantic_review": "not_assessed", "publication_approval": "not_assessed",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workspace", nargs="+", type=Path, help="explicit workspaces; no recursive discovery")
    parser.add_argument("--through", choices=["auto", *ORDER], default="auto",
                        help="require at least this stage; auto uses existing artifacts and run-state")
    parser.add_argument("--timeout", type=float, default=30, help="seconds per isolated check (0 < timeout <= 60)")
    parser.add_argument("--final-pass-set", action="store_true",
                        help="opt-in final full-read declaration, stability, binding and whole-manuscript line coverage check")
    parser.add_argument("--_check", choices=CHECKS, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if not 0 < args.timeout <= 60:
        parser.error("--timeout must be greater than 0 and at most 60 seconds")
    if args._check:
        if len(args.workspace) != 1:
            parser.error("worker expects exactly one workspace")
        result = worker(args.workspace[0].resolve(), args._check)
        print(json.dumps(result, ensure_ascii=False))
        return int(bool(result["errors"]))
    reports = [inspect_workspace(root, args.through, args.timeout, args.final_pass_set) for root in args.workspace]
    result = {"schema_version": "1.0", "scope": "mechanical_preflight_only", "read_only": True,
              "boundary": BOUNDARY, "workspaces": reports}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return int(any(report["issues"] for report in reports))


if __name__ == "__main__":
    raise SystemExit(main())
