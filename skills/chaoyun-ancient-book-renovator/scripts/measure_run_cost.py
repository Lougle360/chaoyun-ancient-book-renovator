#!/usr/bin/env python3
"""Measure explicit local Codex logs; never discover logs or estimate money.

Window: [start, end), with end defaulting to invocation time (UTC).
Exit codes: 0 = measured/below budget, 2 = budget reached, 1 = unknown.
Only per-response ``usage`` is counted; reasoning is a subset of output.
"""
import argparse
from collections import defaultdict
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from uuid import UUID


FIELDS = ("input_tokens", "cached_input_tokens", "output_tokens",
          "reasoning_output_tokens", "total_tokens")
METRICS = FIELDS + ("uncached_input_tokens", "uncached_plus_output_tokens")


class Unknown(ValueError):
    """No trustworthy measurement can be reported."""


class Parser(argparse.ArgumentParser):
    def error(self, message):
        # Do not echo invalid arguments: they could contain private text.
        raise Unknown("invalid CLI arguments; use --help for the required syntax")


def timestamp(value):
    if not isinstance(value, str):
        raise Unknown("timestamp must be an ISO date-time with a timezone")
    try:
        value = value.removesuffix(" UTC") + ("+00:00" if value.endswith(" UTC") else "")
        value = value.removesuffix("Z") + ("+00:00" if value.endswith("Z") else "")
        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise ValueError
        return parsed.astimezone(timezone.utc)
    except (ValueError, OverflowError):
        raise Unknown("invalid timestamp or missing timezone") from None


def thread_id(value):
    try:
        if not isinstance(value, str) or str(UUID(value)) != value.lower():
            raise ValueError
        return value.lower()
    except (ValueError, AttributeError):
        raise Unknown("thread_id must be a canonical UUID") from None


def iso(value):
    return value.isoformat().replace("+00:00", "Z")


def same_file(left, right):
    try:
        return (left.resolve() == right.resolve()
                or (left.exists() and right.exists() and left.samefile(right)))
    except (OSError, ValueError):
        raise Unknown("cannot verify input/output path separation") from None


def usage_values(usage):
    if not isinstance(usage, dict):
        raise Unknown("missing per-response usage object")
    if any(type(usage.get(key)) is not int or usage[key] < 0 for key in FIELDS):
        raise Unknown("usage requires all five nonnegative integer token fields")
    values = {key: usage[key] for key in FIELDS}
    if values["cached_input_tokens"] > values["input_tokens"]:
        raise Unknown("cached input exceeds input")
    if values["reasoning_output_tokens"] > values["output_tokens"]:
        raise Unknown("reasoning output exceeds output (it is a subset)")
    if values["total_tokens"] != values["input_tokens"] + values["output_tokens"]:
        raise Unknown("total_tokens must equal input_tokens + output_tokens")
    values["uncached_input_tokens"] = values["input_tokens"] - values["cached_input_tokens"]
    values["uncached_plus_output_tokens"] = values["uncached_input_tokens"] + values["output_tokens"]
    return values


def total(rows):
    result = {key: 0 for key in METRICS}
    result["response_count"] = len(rows)
    for row in rows:
        for key in METRICS:
            result[key] += row["usage"][key]
    return result


def record_type(line):
    """Read the Codex envelope only, stopping before message payloads."""
    decoder = json.JSONDecoder()
    rest = line.lstrip()
    if not rest.startswith("{"):
        raise Unknown("invalid JSONL envelope")
    rest = rest[1:].lstrip()
    try:
        while rest:
            key, end = decoder.raw_decode(rest)
            rest = rest[end:].lstrip()
            if not isinstance(key, str) or not rest.startswith(":"):
                break
            if key == "payload":
                break  # Standard Codex records put type before payload.
            value, end = decoder.raw_decode(rest[1:].lstrip())
            if key == "type" and isinstance(value, str):
                return value
            rest = rest[1:].lstrip()[end:].lstrip()
            if not rest.startswith(","):
                break
            rest = rest[1:].lstrip()
    except (ValueError, RecursionError):
        pass
    raise Unknown("invalid Codex envelope: expected type before payload")


def measure(sessions, start, end, budget=None):
    """Read only explicitly supplied paths; return (JSON-safe report, exit code)."""
    if end <= start:
        raise Unknown("end must be later than start")
    if budget is not None and (type(budget) is not int or budget <= 0):
        raise Unknown("budget-tokens must be a positive integer")
    responses, agents, sources = {}, {}, []
    matched = duplicates = 0
    for index, (owner, path) in enumerate(sessions, 1):
        owner = thread_id(owner)
        path = Path(path)
        source_count = 0
        line_number = 0
        try:
            with path.open(encoding="utf-8") as stream:
                for line_number, line in enumerate(stream, 1):
                    kind = record_type(line)
                    if kind not in ("token_usage_record", "session_meta"):
                        continue  # Do not decode message or reasoning payloads.
                    try:
                        record = json.loads(line)
                    except (ValueError, RecursionError):
                        raise Unknown("invalid JSONL record") from None
                    if not isinstance(record, dict):
                        raise Unknown("JSONL record must be an object")
                    payload = record.get("payload")
                    if not isinstance(payload, dict):
                        raise Unknown("metadata/usage payload must be an object")
                    if kind == "session_meta":
                        # Forks may contain parent metadata: never attribute it
                        # to the explicitly requested thread.
                        if payload.get("id") != owner:
                            continue
                        agent = payload.get("agent_path")
                        if agent is None:
                            source = payload.get("source")
                            if isinstance(source, dict):
                                subagent = source.get("subagent", {})
                                if isinstance(subagent, dict):
                                    spawn = subagent.get("thread_spawn", {})
                                    if isinstance(spawn, dict):
                                        agent = spawn.get("agent_path")
                            elif isinstance(source, str):
                                agent = "/root"
                        if agent is not None:
                            if not isinstance(agent, str) or not agent.startswith("/"):
                                raise Unknown("invalid agent_path metadata")
                            if owner in agents and agents[owner] != agent:
                                raise Unknown("conflicting agent_path metadata")
                            agents[owner] = agent
                        continue
                    record_owner = thread_id(payload.get("thread_id"))
                    if record_owner != owner:
                        continue
                    when = timestamp(record.get("timestamp"))
                    if not start <= when < end:
                        continue
                    response = payload.get("response_id")
                    if not isinstance(response, str) or not response.strip():
                        raise Unknown("missing response_id")
                    values = usage_values(payload.get("usage"))
                    source_count += 1
                    matched += 1
                    if response in responses:
                        prior = responses[response]
                        if prior["thread_id"] != owner or prior["usage"] != values:
                            raise Unknown("conflicting duplicate response_id")
                        duplicates += 1
                    else:
                        responses[response] = {"thread_id": owner, "timestamp": when, "usage": values}
        except Unknown as exc:
            raise Unknown(f"session {index}, line {line_number}: {exc}") from None
        except (OSError, UnicodeError, ValueError):
            raise Unknown(f"session {index}: log missing, unreadable, or invalid path/encoding") from None
        if not source_count:
            raise Unknown(f"session {index}: no matching token_usage_record in the requested window")
        sources.append({"thread_id": owner, "path": str(path.resolve()), "matched_records": source_count})
    if not responses:
        raise Unknown("no matching token_usage_record in the requested window")
    rows = list(responses.values())
    by_thread = []
    groups = defaultdict(list)
    for owner in sorted({row["thread_id"] for row in rows}):
        owned = [row for row in rows if row["thread_id"] == owner]
        agent = agents.get(owner)
        by_thread.append({"thread_id": owner, "agent_path": agent, **total(owned)})
        # Unknown agent paths stay separate; thread identity remains verified.
        groups[(agent, owner if agent is None else None)].extend(owned)
    by_agent = [{"agent_path": key[0], "thread_ids": sorted({r["thread_id"] for r in grouped}),
                 **total(grouped)} for key, grouped in groups.items()]
    totals = total(rows)
    reached = budget is not None and totals["uncached_plus_output_tokens"] >= budget
    report = {
        "status": "measured", "scope": "explicit_local_logs_only_not_account_billing",
        "window": {"start": iso(start), "end": iso(end), "bounds": "[start,end)",
                   "elapsed_seconds": (end - start).total_seconds()},
        "sample": {"first_record_at": iso(min(r["timestamp"] for r in rows)),
                   "last_record_at": iso(max(r["timestamp"] for r in rows))},
        "reasoning_is_subset_of_output": True,
        "sources": sources, "matched_records": matched, "duplicates_removed": duplicates,
        "totals": totals, "by_thread": by_thread, "by_agent": by_agent,
        "budget": {"metric": "uncached_plus_output_tokens", "limit": budget,
                   "status": "reached" if reached else "below" if budget is not None else "not_set"},
    }
    return report, 2 if reached else 0


def main(argv=None):
    parser = Parser(description=__doc__)
    parser.add_argument("--session", action="append", required=True, metavar="THREAD_ID=JSONL_PATH")
    parser.add_argument("--start", required=True, help="timezone-aware ISO time, or YYYY-MM-DD HH:MM:SS UTC")
    parser.add_argument("--end", help="exclusive end; default: invocation time in UTC")
    parser.add_argument("--budget-tokens", type=int, help="positive limit on uncached input + output")
    parser.add_argument("--output", type=Path, help="explicit JSON output path; stdout is always emitted")
    args = None
    output_allowed = False
    try:
        invocation_time = datetime.now(timezone.utc)
        args = parser.parse_args(argv)
        sessions = []
        for item in args.session:
            owner, separator, path = item.partition("=")
            if not separator or not path:
                raise Unknown("--session requires THREAD_ID=JSONL_PATH")
            sessions.append((thread_id(owner), Path(path)))
        if args.output is not None and any(same_file(args.output, p) for _, p in sessions):
            raise Unknown("output must not overwrite an input log")
        output_allowed = args.output is not None
        report, code = measure(sessions, timestamp(args.start),
                               timestamp(args.end) if args.end else invocation_time, args.budget_tokens)
    except Unknown as exc:
        report, code = {"status": "unknown", "totals": None,
                        "budget": {"status": "unknown"}, "error": str(exc)}, 1
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if output_allowed:
        try:
            if any(same_file(args.output, p) for _, p in sessions):
                raise Unknown("output must not overwrite an input log")
            args.output.write_text(rendered, encoding="utf-8")
        except (OSError, ValueError):
            report, code = {"status": "unknown", "totals": None,
                            "budget": {"status": "unknown"}, "error": "cannot safely write explicit output path"}, 1
            rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    sys.stdout.write(rendered)
    return code


if __name__ == "__main__":
    sys.exit(main())
