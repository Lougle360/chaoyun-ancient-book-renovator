#!/usr/bin/env python3
"""Validate workflow 1.9 scope, traceability, review stability and policy freeze."""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections import Counter
from pathlib import Path


REQUIRED_SOURCE_FIELDS = {"component_id", "structural_role", "bbox", "reading_order"}
ALLOWED_COMPONENT_KINDS = {"main_text", "commentary", "preface", "figure", "table", "paratext"}
ALLOWED_DESTINATIONS = {"final_reader", "supplement", "evidence_only"}
FOCUSED_PROTOCOL = "focused-v1"
REQUIRED_REVIEW_METHODS = {"manuscript_reader", "source_fidelity", "final_pdf_reader"}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected object: {path}")
    return value


def read_jsonl(path: Path) -> list[dict]:
    values = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"expected object at {path}:{number}")
        value["_line"] = number
        values.append(value)
    return values


def review_protocol(book: dict, policy: dict, errors: list[str], lock: dict | None = None) -> str | None:
    """Only two absent markers mean legacy; unknown/mismatched markers fail closed."""
    if lock is not None and any(key in lock for key in ("review_protocol", "review_policy_sha256", "layout_proof_applicability")):
        if lock.get("review_protocol") != FOCUSED_PROTOCOL or book.get("review_protocol") != FOCUSED_PROTOCOL or policy.get("protocol") != FOCUSED_PROTOCOL:
            errors.append("acceptance policy lock review protocol cannot be removed or changed")
            return None
    if "review_protocol" not in book and "protocol" not in policy:
        return None
    if book.get("review_protocol") != FOCUSED_PROTOCOL or policy.get("protocol") != FOCUSED_PROTOCOL:
        errors.append("unknown or mismatched book/review-policy protocol")
        return None
    if book.get("workflow_schema_version") != "1.10" or book.get("delivery_mode") != "ordinary_reader":
        errors.append("focused-v1 requires workflow 1.10 ordinary_reader")
    return FOCUSED_PROTOCOL


def workspace_review_protocol(root: Path, book: dict, policy: dict, errors: list[str]) -> str | None:
    """Check existing lock markers before any legacy version or delivery-mode skip."""
    path = root / "90-audit/acceptance-policy-lock.json"
    try:
        lock = read_json(path) if path.is_file() else None
    except (OSError, ValueError) as exc:
        errors.append(f"invalid acceptance-policy-lock.json: {exc}")
        return None
    return review_protocol(book, policy, errors, lock)


def focused_execution_context(root: Path, manuscript_path: Path, errors: list[str]) -> tuple[dict, list[Path]]:
    """Bind identities to existing execution evidence, without certifying its truth."""
    protected = [manuscript_path.resolve()]
    context: dict = {}

    def local(relative: object) -> Path:
        if not isinstance(relative, str) or not relative.strip() or Path(relative).is_absolute():
            raise ValueError("execution evidence path must be workspace-relative")
        path = (root / relative).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            raise ValueError(f"missing or escaping execution evidence: {relative}")
        return path

    try:
        acceptance_path = root / "50-edited/reader-acceptance-report.json"
        acceptance = read_json(acceptance_path)
        protected.append(acceptance_path)
        session = acceptance.get("reading_session")
        if not isinstance(session, dict):
            raise ValueError("actual reading_session is required")
        expected_hash = sha256(manuscript_path)
        if acceptance.get("output_sha256") != expected_hash:
            raise ValueError("reader acceptance is not bound to the current manuscript")
        for role in ("producer", "reviewer"):
            path = local(acceptance.get(role + "_record"))
            protected.append(path)
            record = read_json(path)
            run_id, actor = record.get("run_id"), record.get("actor")
            if acceptance.get(role + "_record_sha256") != sha256(path):
                raise ValueError(f"{role} execution record hash mismatch")
            if not isinstance(run_id, str) or not run_id.strip() or run_id != session.get(role + "_execution_id"):
                raise ValueError(f"{role} execution differs from actual reading session")
            if not isinstance(actor, str) or not actor.strip() or actor != acceptance.get(role) or record.get("output_sha256") != expected_hash:
                raise ValueError(f"{role} execution is not bound to the actual actor and current manuscript")
            context[role + "_run_id"] = run_id
        if context["producer_run_id"].strip() == context["reviewer_run_id"].strip():
            raise ValueError("producer and reviewer must use separate actual execution runs")
        provenance = local(session.get("provenance_file"))
        if session.get("provenance_sha256") != sha256(provenance):
            raise ValueError("actual reading-session provenance binding is invalid")
        context["provenance_sha256"] = sha256(provenance)
        for key in ("manuscript_file", "tasks_file"):
            if session.get(key):
                protected.append(local(session[key]))
        review_path = root / "50-edited/reader-review.json"
        if review_path.is_file():
            review = read_json(review_path)
            if review.get("input_snapshot"):
                protected.append(local(review["input_snapshot"]))
    except (OSError, ValueError) as exc:
        errors.append(f"focused-v1 actual execution binding: {exc}")
    # Source/input files and copies cannot masquerade as a reader transcript.
    for folder in ("00-intake", "20-source", "30-normalized", "40-modernized"):
        protected.extend(path for path in (root / folder).rglob("*") if path.is_file())
    return context, protected


def layout_proof_applicability(book: dict, errors: list[str]) -> dict | None:
    value = book.get("layout_proof_applicability")
    if not isinstance(value, dict) or type(value.get("required")) is not bool or not isinstance(value.get("reason"), str) or not value["reason"].strip():
        errors.append("focused-v1 requires explicit layout_proof_applicability required:boolean and nonempty reason before policy lock")
        return None
    return value


def section(text: str, heading: str) -> str:
    matches = list(re.finditer(r"^(#{1,6})\s+(.+?)\s*$", text, re.M))
    for index, match in enumerate(matches):
        if match.group(2) != heading:
            continue
        end = next(
            (later.start() for later in matches[index + 1 :] if len(later.group(1)) <= len(match.group(1))),
            len(text),
        )
        return text[match.end() : end]
    return ""


def validate_scope(root: Path, source: list[dict], manuscript: str, errors: list[str]) -> None:
    path = root / "10-diagnosis/edition-scope.json"
    if not path.is_file():
        errors.append("workflow 1.9 requires a frozen 10-diagnosis/edition-scope.json")
        return
    try:
        scope = read_json(path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        errors.append(f"invalid edition-scope.json: {exc}")
        return

    if scope.get("status") != "locked" or not str(scope.get("locked_at") or "").strip():
        errors.append("edition scope must be locked before production")
    if scope.get("delivery_mode") != "ordinary_reader" or scope.get("completeness_claim") != "full_source_content":
        errors.append("ordinary-reader white-language delivery requires full_source_content scope")
    if not str(scope.get("user_requirement") or "").strip():
        errors.append("edition scope must preserve the user's actual delivery requirement")

    components = scope.get("source_components")
    if not isinstance(components, list) or not components:
        errors.append("edition scope requires a nonempty source_components inventory")
        return
    component_by_id: dict[str, dict] = {}
    for item in components:
        if not isinstance(item, dict) or not str(item.get("component_id") or "").strip():
            errors.append("edition scope contains a component without component_id")
            continue
        component_id = item["component_id"]
        if component_id in component_by_id:
            errors.append(f"duplicate edition component: {component_id}")
        component_by_id[component_id] = item
        if item.get("kind") not in ALLOWED_COMPONENT_KINDS:
            errors.append(f"edition component {component_id} has invalid kind")
        if item.get("planned_destination") not in ALLOWED_DESTINATIONS:
            errors.append(f"edition component {component_id} has invalid planned_destination")
        if item.get("kind") in {"main_text", "commentary", "preface"} and item.get("required_in_release") is not True:
            authorization = item.get("exclusion_authorization")
            if not isinstance(authorization, dict) or not authorization.get("user_quote") or not authorization.get("recorded_at"):
                errors.append(f"source-bearing component {component_id} may not be excluded without explicit user authorization")

    source_component_ids = {row.get("component_id") for row in source if row.get("component_id")}
    unknown = source_component_ids - set(component_by_id)
    if unknown:
        errors.append(f"source blocks reference unknown edition components: {sorted(unknown)[:10]}")
    unused = set(component_by_id) - source_component_ids
    if unused:
        errors.append(f"edition components have no source blocks: {sorted(unused)[:10]}")

    map_path = root / "50-edited/source-reader-map.jsonl"
    if not map_path.is_file():
        errors.append("workflow 1.9 requires 50-edited/source-reader-map.jsonl")
        return
    try:
        mappings = read_jsonl(map_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        errors.append(f"invalid source-reader-map.jsonl: {exc}")
        return
    by_block = Counter(row.get("block_id") for row in mappings)
    duplicates = sorted(key for key, count in by_block.items() if key and count != 1)
    if duplicates:
        errors.append(f"source-reader map must contain each block exactly once: {duplicates[:10]}")

    source_by_id = {row.get("block_id"): row for row in source}
    for block_id, block in source_by_id.items():
        component = component_by_id.get(block.get("component_id"), {})
        source_bearing = block.get("disposition") not in {"noncontent", "unreadable", "excluded_with_reason"}
        required = component.get("required_in_release") is True and component.get("planned_destination") == "final_reader"
        rows = [row for row in mappings if row.get("block_id") == block_id]
        if source_bearing and required and len(rows) != 1:
            errors.append(f"source block {block_id} lacks exactly one reader mapping")
            continue
        if not rows:
            continue
        row = rows[0]
        if row.get("component_id") != block.get("component_id"):
            errors.append(f"source-reader map component mismatch for {block_id}")
        if required:
            heading = row.get("reader_heading")
            quote = row.get("reader_quote")
            if not isinstance(heading, str) or not isinstance(quote, str) or not quote.strip():
                errors.append(f"reader mapping for {block_id} requires heading and exact quote")
            elif quote not in section(manuscript, heading):
                errors.append(f"reader mapping for {block_id} is not located in its declared section")
            if row.get("status") != "reviewed" or not str(row.get("review_evidence") or "").strip():
                errors.append(f"reader mapping for {block_id} lacks reviewed evidence")
        else:
            if row.get("destination") not in {"supplement", "evidence_only", "noncontent", "unreadable"}:
                errors.append(f"non-reading block {block_id} lacks a valid preserved destination")

    for number, line in enumerate(manuscript.splitlines(), 1):
        if line.count("<!-- source:") > 1:
            errors.append(f"aggregated source anchors are not valid mapping evidence: line {number}")


def validate_source_structure(source: list[dict], errors: list[str]) -> None:
    roles = Counter()
    pages = Counter()
    for row in source:
        missing = REQUIRED_SOURCE_FIELDS - row.keys()
        if missing:
            errors.append(f"source block {row.get('block_id')} lacks structural fields: {sorted(missing)}")
            continue
        bbox = row.get("bbox")
        if not isinstance(bbox, list) or len(bbox) != 4 or not all(isinstance(value, (int, float)) for value in bbox):
            errors.append(f"source block {row.get('block_id')} has invalid bbox")
        if not isinstance(row.get("reading_order"), int) or row["reading_order"] < 1:
            errors.append(f"source block {row.get('block_id')} has invalid reading_order")
        roles[str(row.get("structural_role"))] += 1
        pages[row.get("source_page")] += 1
    if source and set(roles) == {"body"} and all(count == 1 for count in pages.values()):
        errors.append("source reconstruction collapsed every page into one body block; printed structure was not reconstructed")


def validate_review_stability(root: Path, manuscript_path: Path, errors: list[str]) -> None:
    root = Path(root).resolve()
    policy_path = root / "50-edited/review-policy.json"
    if not policy_path.is_file():
        errors.append("workflow 1.9 requires 50-edited/review-policy.json")
        return
    try:
        policy = read_json(policy_path)
        book = read_json(root / "book.json")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        errors.append(f"invalid review-policy.json: {exc}")
        return
    protocol_errors: list[str] = []
    protocol = workspace_review_protocol(root, book, policy, protocol_errors)
    if protocol_errors:
        errors.extend(protocol_errors)
        return
    if protocol == FOCUSED_PROTOCOL:
        # A marker alone never reduces the old 3/2 gate: verify its frozen contract.
        validate_policy_lock(root, protocol_errors)
        if protocol_errors:
            errors.extend(protocol_errors)
            return
        methods = policy.get("required_methods")
        if not isinstance(methods, list) or any(not isinstance(method, str) for method in methods) or not REQUIRED_REVIEW_METHODS.issubset(methods):
            errors.append("focused-v1 requires manuscript_reader, source_fidelity and final_pdf_reader methods")
    minimum = policy.get("minimum_full_passes")
    stable = policy.get("required_stable_passes")
    minimum_floor, stable_floor = (1, 1) if protocol == FOCUSED_PROTOCOL else (3, 2)
    if type(minimum) is not int or minimum < minimum_floor:
        errors.append("focused-v1 requires at least one complete pass" if protocol == FOCUSED_PROTOCOL else "ordinary-reader review policy requires at least three complete passes")
        return
    if type(stable) is not int or stable < stable_floor or stable > minimum:
        errors.append("focused-v1 requires at least one stable final pass and stable <= minimum" if protocol == FOCUSED_PROTOCOL else "review policy requires at least two stable final passes")
        return

    pass_dir = root / "50-edited/review-history/full-passes"
    paths = sorted(pass_dir.glob("*.json")) if pass_dir.is_dir() else []
    if len(paths) < minimum:
        errors.append(f"complete reader passes are insufficient: {len(paths)}/{minimum}")
        return
    expected_hash = sha256(manuscript_path)
    context, protected = focused_execution_context(root, manuscript_path, errors) if protocol == FOCUSED_PROTOCOL else ({}, [])
    policy_lock_hash = sha256(root / "90-audit/acceptance-policy-lock.json") if protocol == FOCUSED_PROTOCOL else None
    records = []
    run_ids = set()
    for path in paths:
        try:
            record = read_json(path)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            errors.append(f"invalid complete reader pass {path.name}: {exc}")
            continue
        records.append(record)
        if record.get("manuscript_sha256") != expected_hash:
            errors.append(f"complete reader pass {path.name} is stale")
        run_id = record.get("reviewer_run_id")
        run_key = run_id.strip() if isinstance(run_id, str) else None
        if not run_key or run_key in run_ids:
            errors.append(f"complete reader pass {path.name} requires a distinct real reviewer_run_id")
        if isinstance(run_id, str):
            run_ids.add(run_key)
        if protocol == FOCUSED_PROTOCOL:
            producer_id = record.get("producer_run_id")
            if not isinstance(producer_id, str) or not producer_id.strip() or producer_id.strip() == str(run_id).strip():
                errors.append(f"complete reader pass {path.name} requires a nonempty producer_run_id distinct from reviewer_run_id")
            if producer_id != context.get("producer_run_id") or run_key == str(context.get("producer_run_id")).strip():
                errors.append(f"complete reader pass {path.name} is not independent of the bound actual producer run")
            if record.get("acceptance_policy_lock_sha256") != policy_lock_hash:
                errors.append(f"complete reader pass {path.name} acceptance policy lock binding is stale or missing; a new lock requires fresh review")
        if record.get("status") not in ("passed", "failed"):
            errors.append(f"complete reader pass {path.name} has invalid status")
        findings = record.get("findings")
        if not isinstance(findings, list):
            errors.append(f"complete reader pass {path.name} requires findings list")
        if not isinstance(record.get("sections_covered"), list) or not record.get("sections_covered"):
            errors.append(f"complete reader pass {path.name} lacks section coverage")
        transcript = record.get("transcript")
        if not isinstance(transcript, str):
            errors.append(f"complete reader pass {path.name} requires transcript path")
        else:
            transcript_path = (root / transcript).resolve()
            if not transcript_path.is_relative_to(root) or not transcript_path.is_file() or record.get("transcript_sha256") != sha256(transcript_path):
                errors.append(f"complete reader pass {path.name} transcript binding is invalid")
            elif protocol == FOCUSED_PROTOCOL:
                try:
                    transcript_text = transcript_path.read_text(encoding="utf-8")
                    if not transcript_text.strip():
                        errors.append(f"complete reader pass {path.name} requires a nonempty actual transcript")
                    if Path(transcript).is_absolute() or any(
                        target.resolve() == transcript_path or (
                            target.stat().st_size == transcript_path.stat().st_size and sha256(target) == record.get("transcript_sha256")
                        ) for target in protected
                    ):
                        errors.append(f"complete reader pass {path.name} transcript reuses manuscript, source/input or execution content")
                    if not run_key or run_id not in transcript_text:
                        errors.append(f"complete reader pass {path.name} transcript lacks its actual reviewer_run_id")
                    sections = record.get("sections_covered")
                    if isinstance(sections, list):
                        for item in sections:
                            if isinstance(item, dict) and isinstance(item.get("evidence"), str) and item["evidence"].strip() and item["evidence"] not in transcript_text:
                                errors.append(f"complete reader pass {path.name} section evidence is absent from its actual transcript")
                except (OSError, ValueError) as exc:
                    errors.append(f"complete reader pass {path.name} transcript cannot be checked: {exc}")
    if len(records) >= stable:
        for record in records[-stable:]:
            if record.get("status") != "passed" or record.get("new_blocking_issues") != [] or record.get("open_blocking_issues") != []:
                errors.append("the final stable reader passes must have no new or open blocking issues")
    if protocol == FOCUSED_PROTOCOL:
        if records and (records[-1].get("reviewer_run_id") != context.get("reviewer_run_id") or records[-1].get("transcript_sha256") != context.get("provenance_sha256")):
            errors.append("final complete reader pass must match the actual acceptance reviewer run and reading-session provenance")
        from validate_full_read import validate_full_read_coverage
        validate_full_read_coverage(root, manuscript_path, errors)

    acceptance_path = root / "50-edited/reader-acceptance-report.json"
    if acceptance_path.is_file():
        try:
            acceptance = read_json(acceptance_path)
            evidence = [
                str(item.get("evidence") or "").strip()
                for item in (acceptance.get("dimension_checks") or {}).values()
                if isinstance(item, dict)
            ]
            if evidence:
                repeated = Counter(evidence).most_common(1)[0][1]
                if repeated > max(2, math.ceil(len(evidence) / 3)):
                    errors.append("reader acceptance reuses generic evidence across too many dimensions")
        except (OSError, ValueError, json.JSONDecodeError):
            pass

    process = root / "50-edited/review-history/RC0001/process-edition.md"
    ledger = root / "50-edited/reader-revision-ledger.jsonl"
    if process.is_file() and ledger.is_file():
        try:
            before = len(re.sub(r"\s+", "", process.read_text(encoding="utf-8")))
            after = len(re.sub(r"\s+", "", manuscript_path.read_text(encoding="utf-8")))
            changes = read_jsonl(ledger)
            if before and abs(after - before) / before > 0.15 and len(changes) < 3:
                errors.append("a large final-reader cut cannot be represented by one catch-all revision record")
        except (OSError, ValueError, json.JSONDecodeError):
            pass


def validator_paths(protocol: str | None = None) -> dict[str, Path]:
    if protocol not in {None, FOCUSED_PROTOCOL}:
        raise ValueError(f"unknown review protocol: {protocol}")
    controller = Path(__file__).resolve().parent
    skills = controller.parents[1]
    paths = {
        "controller/validate_workspace.py": controller / "validate_workspace.py",
        "controller/validate_layout_proof.py": controller / "validate_layout_proof.py",
        "controller/validate_text_semantics.py": controller / "validate_text_semantics.py",
        "controller/validate_integrity.py": controller / "validate_integrity.py",
        "controller/validate_reader_units.py": controller / "validate_reader_units.py",
        "controller/validate_production_plan.py": controller / "validate_production_plan.py",
        "controller/validate_delivery.py": controller / "validate_delivery.py",
        "reading-editor/validate_reader_value.py": skills / "chaoyun-reading-editor/scripts/validate_reader_value.py",
        "reader-reviser/validate_reader_revision.py": skills / "chaoyun-reader-experience-reviser/scripts/validate_reader_revision.py",
        "publisher/audit_publication.py": skills / "chaoyun-quality-publisher/scripts/audit_publication.py",
        "publisher/validate_release_binding.py": skills / "chaoyun-quality-publisher/scripts/validate_release_binding.py",
        "publisher/validate_pdf_readability.py": skills / "chaoyun-quality-publisher/scripts/validate_pdf_readability.py",
    }
    if protocol == FOCUSED_PROTOCOL:
        for name in ("validate_full_read.py", "init_workspace.py", "lock_acceptance_policy.py", "preflight_review.py"):
            paths[f"controller/{name}"] = controller / name
    return paths


def validate_policy_lock(root: Path, errors: list[str]) -> None:
    root = Path(root).resolve()
    path = root / "90-audit/acceptance-policy-lock.json"
    if not path.is_file():
        errors.append("workflow 1.9 requires a frozen acceptance-policy-lock.json")
        return
    try:
        lock = read_json(path)
        book = read_json(root / "book.json")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        errors.append(f"invalid acceptance-policy-lock.json: {exc}")
        return
    policy_path = root / "50-edited/review-policy.json"
    try:
        policy = read_json(policy_path) if policy_path.is_file() else {}
    except (OSError, ValueError) as exc:
        errors.append(f"invalid review-policy.json: {exc}")
        return
    protocol_errors: list[str] = []
    protocol = review_protocol(book, policy, protocol_errors, lock)
    errors.extend(protocol_errors)
    if protocol == FOCUSED_PROTOCOL:
        if lock.get("review_protocol") != protocol:
            errors.append("acceptance policy lock does not match the frozen review protocol")
        if not policy_path.is_file() or lock.get("review_policy_sha256") != sha256(policy_path):
            errors.append("acceptance policy lock does not match the frozen review-policy.json")
        applicability = layout_proof_applicability(book, errors)
        locked_applicability = lock.get("layout_proof_applicability")
        if applicability is None or json.dumps(locked_applicability, sort_keys=True) != json.dumps(applicability, sort_keys=True):
            errors.append("acceptance policy lock does not match the frozen layout_proof_applicability")
    elif "review_protocol" in lock or "review_policy_sha256" in lock:
        errors.append("acceptance policy lock review protocol cannot be removed or changed")
    if lock.get("policy_version") != book.get("workflow_schema_version"):
        errors.append("acceptance policy lock must match the book workflow version")
    contract = root / "10-diagnosis/edition-scope.json"
    if not contract.is_file() or lock.get("edition_scope_sha256") != sha256(contract):
        errors.append("acceptance policy lock does not match the frozen edition scope")
    locked = lock.get("validators") if isinstance(lock.get("validators"), dict) else {}
    for name, path_value in validator_paths(protocol).items():
        if not path_value.is_file() or locked.get(name) != sha256(path_value):
            errors.append(f"acceptance policy changed after review began: {name}")


def validate_source(root: Path) -> list[str]:
    """Run the workflow-1.9 structure/scope gate as soon as source reconstruction ends."""
    root = Path(root).resolve()
    errors: list[str] = []
    try:
        book = read_json(root / "book.json")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return [f"cannot validate workflow 1.9 source integrity: {exc}"]
    policy_path = root / "50-edited/review-policy.json"
    try:
        policy = read_json(policy_path) if policy_path.is_file() else {}
    except (OSError, ValueError) as exc:
        return [f"invalid review-policy.json: {exc}"]
    workspace_review_protocol(root, book, policy, errors)
    if errors:
        return errors
    if book.get("delivery_mode") != "ordinary_reader" or str(book.get("workflow_schema_version") or "") not in {"1.9", "1.10"}:
        return errors
    try:
        source = read_jsonl(root / "20-source/blocks.jsonl")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return [f"cannot validate workflow 1.9 source blocks: {exc}"]
    validate_source_structure(source, errors)
    scope_path = root / "10-diagnosis/edition-scope.json"
    if not scope_path.is_file():
        errors.append("workflow 1.9 source gate requires a frozen 10-diagnosis/edition-scope.json")
        return errors
    try:
        scope = read_json(scope_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        errors.append(f"invalid edition-scope.json: {exc}")
        return errors
    if scope.get("status") != "locked":
        errors.append("edition scope must be locked before source reconstruction can pass")
    components = scope.get("source_components") if isinstance(scope.get("source_components"), list) else []
    component_ids = {item.get("component_id") for item in components if isinstance(item, dict)}
    invalid_components = [row.get("block_id") for row in source if row.get("component_id") not in component_ids]
    if invalid_components:
        errors.append(
            "source blocks lack a component declared by edition scope: "
            f"count={len(invalid_components)}, examples={invalid_components[:10]}"
        )
    return errors


def validate(root: Path) -> list[str]:
    root = Path(root).resolve()
    errors: list[str] = []
    try:
        book = read_json(root / "book.json")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return [f"cannot validate workflow 1.9 integrity: {exc}"]
    # Marked records must be checked even when malformed metadata would skip legacy gates.
    policy_path = root / "50-edited/review-policy.json"
    try:
        policy = read_json(policy_path) if policy_path.is_file() else {}
    except (OSError, ValueError) as exc:
        return [f"invalid review-policy.json: {exc}"]
    workspace_review_protocol(root, book, policy, errors)
    if errors:
        return errors
    if book.get("delivery_mode") != "ordinary_reader" or str(book.get("workflow_schema_version") or "") not in {"1.9", "1.10"}:
        return errors
    try:
        source = read_jsonl(root / "20-source/blocks.jsonl")
        manuscript_path = root / "50-edited/modern-reading.md"
        manuscript = manuscript_path.read_text(encoding="utf-8")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return [f"cannot validate workflow 1.9 artifacts: {exc}"]
    validate_source_structure(source, errors)
    validate_scope(root, source, manuscript, errors)
    validate_review_stability(root, manuscript_path, errors)
    if book.get("review_protocol") != FOCUSED_PROTOCOL:
        validate_policy_lock(root, errors)
    from validate_reader_units import validate as validate_units
    errors.extend(validate_units(root, publication=True))
    if book.get("workflow_schema_version") == "1.10":
        try:
            state = read_json(root / "run-state.json")
        except (OSError, ValueError) as exc:
            errors.append(f"invalid reader-unit stage state: {exc}")
            state = {}
        if state.get("stages", {}).get("reader_units_built", {}).get("status") != "passed":
            errors.append("reader_units_built stage must pass before publication")
    return errors
