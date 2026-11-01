"""Check evidence for G3.5 text review, not the truth of an OCR/semantic judgment."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

from validate_layout_proof import binding, local, need, obj, sha

CHECKS = ("glyph_fidelity", "source_reading_separation", "contextual_terms",
          "reading_order", "meaning_in_context", "final_artifact")
LEDGERS = ("uncertainty-candidates.jsonl", "uncertainty-adjudication.jsonl", "uncertain-items.jsonl")


def proof_digest(proof):
    # Exclude status/review/text_semantics_review to avoid circular hashes.
    keys = ("book_id", "version", "validator_sha256", "text_semantics_policy_sha256",
            "scope", "source_pdf", "pdf", "inputs", "coverage", "figures", "pages")
    data = {key: proof.get(key) for key in keys}
    return hashlib.sha256(json.dumps(data, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def validate(root, proof, blocks, selected):
    """Raise on invalid evidence; pending candidates may omit unfinished review."""
    need(proof.get("text_semantics_policy_sha256") == sha(Path(__file__)),
         "text/semantics policy changed; fresh review required")
    ref = proof.get("text_semantics_review")
    if ref is None:
        need(proof.get("status") != "accepted", "accepted proof lacks text/semantics review")
        return
    report = obj(binding(root, ref))
    need(report.get("schema_version") == "1.0", "unsupported text/semantics review schema")
    need(report.get("proof_sha256") == proof_digest(proof), "text/semantics review belongs to another proof or inputs")
    need(report.get("status") in {"passed", "changes_requested"}, "invalid text/semantics status")
    for key in ("producer", "producer_run_id", "reviewer", "reviewer_run_id", "reviewed_at"):
        need(isinstance(report.get(key), str) and report[key].strip(), "missing text/semantics review actor/time")
    need(report["producer"] != report["reviewer"] and report["producer_run_id"] != report["reviewer_run_id"],
         "text/semantics review requires a separate execution")
    binding(root, report.get("evidence"))

    # Reuse the existing adjudication contract; do not create a parallel doubt ledger.
    adjudicator = Path(__file__).resolve().parents[2] / "chaoyun-uncertainty-adjudicator/scripts"
    sys.path.insert(0, str(adjudicator))
    try:
        import project_open_items as ledger
        from closure_evidence import located
    finally:
        sys.path.pop(0)
    data = []
    for name in LEDGERS:
        relative = "90-audit/" + name
        item = report.get("ledger_bindings", {}).get(name, {})
        # Zero candidates is legitimate; an empty JSONL must still be hash-bound.
        path = local(root, item.get("path"))
        need(path == root / relative and path.is_file() and sha(path) == item.get("sha256"),
             "missing/stale canonical text review ledger: " + name)
        data.append(ledger.read_jsonl(path))
    candidates, decisions, projection = data
    errors = ledger.validate(root, candidates, decisions)
    need(not errors, "text review uncertainty ledger invalid: " + "; ".join(errors))
    active = ledger.active_decisions(decisions)
    open_ids = {d["adjudication_id"] for d in active if d["status"] == "open_material"}
    need(len(projection) == len(open_ids)
         and {r.get("adjudication_id") for r in projection} == open_ids
         and all(r.get("status") == "open" for r in projection), "text review open projection differs")

    expected = {b["block_id"] for b in blocks if b["source_page"] in selected}
    coverage = report.get("coverage")
    need(isinstance(coverage, list) and len(coverage) == len(selected), "text review page coverage differs")
    need({r.get("source_page") for r in coverage} == selected, "text review source pages differ")
    for row in coverage:
        ids = {b["block_id"] for b in blocks if b["source_page"] == row["source_page"]}
        reviewed = row.get("block_ids", [])
        need(isinstance(reviewed, list) and len(reviewed) == len(ids) and set(reviewed) == ids,
             "text review must inspect all source blocks, not only flagged OCR")
        need(isinstance(row.get("findings"), str) and row["findings"].strip(), "missing page-specific text review findings")
    for key in CHECKS:
        check = report.get("checks", {}).get(key, {})
        need(check.get("status") in {"passed", "passed_with_ledger", "changes_requested"}, "missing text review check: " + key)
        need(isinstance(check.get("findings"), str) and check["findings"].strip(), "missing text review findings: " + key)
        if report["status"] == "passed":
            need(check["status"] != "changes_requested", "unresolved text review check: " + key)

    selected_candidates = {c["candidate_id"] for c in candidates if c.get("block_id") in expected}
    results = report.get("candidate_results")
    need(isinstance(results, list) and len(results) == len(selected_candidates)
         and {r.get("candidate_id") for r in results} == selected_candidates, "text review candidate coverage differs")
    by_candidate = {cid: d for d in active for cid in d["candidate_ids"]}
    for result in results:
        decision = by_candidate[result["candidate_id"]]
        is_open = decision["status"] == "open_material"
        need(result.get("result") == ("disclosed_unresolved" if is_open else "verified"),
             "text review cannot treat an open meaning as resolved")
        need(isinstance(result.get("finding"), str) and result["finding"].strip(), "missing candidate-specific review finding")
        refs = result.get("evidence")
        need(isinstance(refs, list) and refs, "missing located candidate evidence")
        for item in refs:
            located(root, item)
        if is_open:
            disclosure = result.get("reader_disclosure")
            path = located(root, disclosure)
            need(path.relative_to(root).parts[0] in {"30-normalized", "40-modernized", "50-edited", "60-publication"},
                 "unresolved reading needs a reader-visible disclosure, not only an internal audit")
            if report["status"] == "passed":
                need(decision["reader_impact"] != "high", "high-impact meaning uncertainty blocks text review acceptance")
    if proof["status"] == "accepted":
        need(report["status"] == "passed", "text/semantics review returned changes_requested")
