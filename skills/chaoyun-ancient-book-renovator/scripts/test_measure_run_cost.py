"""Metadata-only fixtures shaped like local Codex token_usage_record logs."""
import contextlib
import copy
from datetime import datetime, timezone
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from measure_run_cost import main, record_type


PARENT = "01a1a0b2-4b68-7ce0-a076-c0c826d5a6f4"
CHILD = "01a1ac33-91df-7762-a770-603a899dc3f6"
START = "2026-11-05T14:00:00Z"
END = "2026-11-05T15:00:00Z"


def record(owner=CHILD, response="resp_one", at=START):
    return {"timestamp": at, "type": "token_usage_record", "payload": {
        "thread_id": owner, "turn_id": CHILD, "session_id": PARENT, "root_turn_id": PARENT,
        "response_id": response, "usage": {"input_tokens": 100, "cached_input_tokens": 80,
            "output_tokens": 20, "reasoning_output_tokens": 10, "total_tokens": 120},
        "turn_token_usage": {"total_tokens": 999999}, "thread_token_usage": {"total_tokens": 9999999}}}


def metadata(owner, agent):
    return {"timestamp": START, "type": "session_meta", "payload": {
        "id": owner, "source": {"subagent": {"thread_spawn": {
            "parent_thread_id": PARENT, "depth": 1, "agent_path": agent}}}}}


class MeasureRunCost(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.path = self.root / "child.jsonl"

    def write(self, rows, path=None):
        path = path or self.path
        path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
        return path

    def run_cli(self, *extra, sessions=None):
        argv = ["--start", START, "--end", END]
        for owner, path in sessions or [(CHILD, self.path)]:
            argv.extend(["--session", f"{owner}={path}"])
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = main(argv + list(extra))
        return code, json.loads(output.getvalue())

    def unknown(self, result):
        code, report = result
        self.assertEqual(code, 1)
        self.assertEqual(report["status"], "unknown")
        self.assertIsNone(report["totals"])
        self.assertEqual(report["budget"]["status"], "unknown")

    def test_inherited_filter_dedup_and_cache_arithmetic(self):
        inherited = record(PARENT, "parent_response")
        inherited["payload"].pop("usage")  # Inherited usage is never counted or validated.
        self.write([metadata(PARENT, "/root"), inherited, metadata(CHILD, "/root/audit"),
                    record(), record(), {"type": "event_msg", "payload": {"type": "token_count"}}])
        code, report = self.run_cli()
        self.assertEqual(code, 0)
        self.assertEqual(report["totals"], {"input_tokens": 100, "cached_input_tokens": 80,
            "output_tokens": 20, "reasoning_output_tokens": 10, "total_tokens": 120,
            "uncached_input_tokens": 20, "uncached_plus_output_tokens": 40, "response_count": 1})
        self.assertEqual(report["duplicates_removed"], 1)
        self.assertEqual(report["by_thread"][0]["agent_path"], "/root/audit")
        self.assertEqual(report["by_agent"][0]["total_tokens"], 120)

    def test_global_dedup_across_explicit_files(self):
        self.write([record()])
        other = self.write([record()], self.root / "copy.jsonl")
        code, report = self.run_cli(sessions=[(CHILD, self.path), (CHILD, other)])
        self.assertEqual(code, 0)
        self.assertEqual(report["totals"]["response_count"], 1)
        self.assertEqual(report["duplicates_removed"], 1)

    def test_multiple_threads_and_agent_summaries(self):
        self.write([metadata(CHILD, "/root/audit"), record()])
        parent = self.write([metadata(PARENT, "/root"), record(PARENT, "resp_parent")], self.root / "parent.jsonl")
        code, report = self.run_cli(sessions=[(CHILD, self.path), (PARENT, parent)])
        self.assertEqual(code, 0)
        self.assertEqual(len(report["by_thread"]), 2)
        self.assertEqual(len(report["by_agent"]), 2)
        self.assertEqual(report["totals"]["uncached_plus_output_tokens"], 80)

    def test_start_inclusive_end_exclusive_and_timezone(self):
        self.write([record(response="before", at="2026-11-05T13:59:59.999999Z"), record(),
                    record(response="last", at="2026-11-05T14:59:59.999999Z"),
                    record(response="end", at=END)])
        code, report = self.run_cli("--start", "2026-11-05T22:00:00+08:00", "--end", "2026-11-05 15:00:00 UTC")
        self.assertEqual(code, 0)
        self.assertEqual(report["totals"]["response_count"], 2)
        self.assertEqual(report["window"]["elapsed_seconds"], 3600)
        self.assertEqual(report["sample"]["first_record_at"], START)

    def test_message_payloads_are_not_decoded(self):
        # Reading the envelope stops before this private and even invalid body.
        self.assertEqual(record_type('{"timestamp":"' + START + '","type":"response_item",'
                                     '"payload": PRIVATE_REASONING_NOT_DECODED'), "response_item")
        self.write([record()])
        with self.path.open("a") as stream:
            stream.write('{"type":"response_item","payload": PRIVATE_BODY_NOT_DECODED\n')
        code, report = self.run_cli()
        self.assertEqual(code, 0)
        self.assertNotIn("PRIVATE_BODY", json.dumps(report))

    def test_default_end_uses_invocation_time(self):
        self.write([record()])
        output = io.StringIO()
        with contextlib.redirect_stdout(output), patch("measure_run_cost.datetime", wraps=datetime) as clock:
            clock.now.return_value = datetime(2026, 11, 5, 15, tzinfo=timezone.utc)
            code = main(["--session", f"{CHILD}={self.path}", "--start", START])
        report = json.loads(output.getvalue())
        self.assertEqual(code, 0)
        self.assertEqual(report["window"]["end"], END)

    def test_budget_reached_at_equality(self):
        self.write([record()])
        for limit, expected, state in [(41, 0, "below"), (40, 2, "reached"), (39, 2, "reached")]:
            with self.subTest(limit=limit):
                code, report = self.run_cli("--budget-tokens", str(limit))
                self.assertEqual(code, expected)
                self.assertEqual(report["budget"]["status"], state)

    def test_missing_empty_wrong_thread_and_outside_window_are_unknown(self):
        self.unknown(self.run_cli())
        for rows in ([], [record(PARENT)], [record(at=END)], [{"type": "event_msg"}]):
            with self.subTest(rows=rows):
                self.write(rows)
                self.unknown(self.run_cli("--budget-tokens", "1000"))

    def test_missing_usage_fields_and_bad_arithmetic_are_unknown(self):
        mutations = [("input_tokens", None), ("cached_input_tokens", 101), ("output_tokens", -1),
                     ("reasoning_output_tokens", 21), ("total_tokens", 121),
                     ("input_tokens", True), ("cached_input_tokens", 80.0)]
        for key, value in mutations:
            with self.subTest(key=key, value=value):
                row = record()
                if value is None:
                    del row["payload"]["usage"][key]
                else:
                    row["payload"]["usage"][key] = value
                self.write([row])
                self.unknown(self.run_cli())

    def test_invalid_id_response_time_and_json_are_unknown_without_echo(self):
        for field in ("thread_id", "response_id", "usage"):
            row = record()
            del row["payload"][field]
            self.write([row])
            self.unknown(self.run_cli())
        for time in ("not-a-time", "2026-11-05T14:00:00", None):
            self.write([record(at=time)])
            self.unknown(self.run_cli())
        self.path.write_text('{PRIVATE_MESSAGE\n', encoding="utf-8")
        result = self.run_cli()
        self.unknown(result)
        self.assertNotIn("PRIVATE_MESSAGE", json.dumps(result))

    def test_conflicting_duplicate_is_unknown(self):
        changed = copy.deepcopy(record())
        changed["payload"]["usage"]["cached_input_tokens"] = 79
        self.write([record(), changed])
        self.unknown(self.run_cli())
        self.write([record()])
        other = self.write([record(PARENT)], self.root / "parent.jsonl")
        self.unknown(self.run_cli(sessions=[(CHILD, self.path), (PARENT, other)]))

    def test_invalid_cli_and_times_and_budget_are_unknown(self):
        self.write([record()])
        for args in [("--start", "yesterday"), ("--end", START), ("--end", "2026-11-04T00:00:00Z"),
                     ("--budget-tokens", "0"), ("--budget-tokens", "-1"),
                     ("--budget-tokens", "1.5"), ("--unexpected", "PRIVATE")]:
            with self.subTest(args=args):
                self.unknown(self.run_cli(*args))
        self.unknown(self.run_cli(sessions=[("bad-id", self.path)]))

    def test_output_is_explicit_and_cannot_overwrite_input(self):
        self.write([record()])
        output = self.root / "measurement.json"
        code, report = self.run_cli("--output", str(output))
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(output.read_text()), report)
        before = self.path.read_bytes()
        self.unknown(self.run_cli("--output", str(self.path)))
        self.assertEqual(before, self.path.read_bytes())
        self.unknown(self.run_cli("--output", str(self.root / "missing" / "out.json")))

    def test_output_aliases_cannot_overwrite_input(self):
        self.write([record()])
        before = self.path.read_bytes()
        symlink = self.root / "symlink.json"
        symlink.symlink_to(self.path)
        hardlink = self.root / "hardlink.json"
        hardlink.hardlink_to(self.path)
        for alias in (symlink, hardlink):
            with self.subTest(alias=alias.name):
                self.unknown(self.run_cli("--output", str(alias)))
                self.assertEqual(before, self.path.read_bytes())


if __name__ == "__main__":
    unittest.main()
