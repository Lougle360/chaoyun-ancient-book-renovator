"""Synthetic prerequisite regressions; never evidence of real book acceptance."""
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from pypdf import PdfWriter

import test_layout_proof as proof_fixtures
from test_reader_production import fixture_plan, write
from validate_layout_proof import validate as validate_proof
from validate_production_plan import ILLUSTRATION_BINDINGS, sha, validate as validate_plan


class FocusedProductionPrerequisites(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='chaoyun-focused-plan-test-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.book = {'delivery_mode': 'ordinary_reader', 'workflow_schema_version': '1.10',
                     'review_protocol': 'focused-v1'}
        write(self.root / 'book.json', self.book)
        block = {'block_id': 'P000001-B001', 'block_type': 'body', 'source_text': '天地玄黄',
                 'source_page': 1, 'reading_order': 1, 'component_id': 'C1'}
        for name in ('20-source/blocks.jsonl', '30-normalized/blocks.jsonl'):
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(block) + '\n', encoding='utf-8')
        self.plan = fixture_plan(self.root)
        self.plan['schema_version'] = '1.1'
        for name in ILLUSTRATION_BINDINGS:
            path = self.root / name
            path.write_text('SYNTHETIC ONLY: text-only fixture; no illustration proposed.\n', encoding='utf-8')
            self.plan['bindings'][name] = sha(path)
        write(self.root / '10-diagnosis/edition-scope.json', {
            'status': 'locked', 'source_components': [
                {'component_id': 'C1', 'planned_destination': 'final_reader'}]})
        review = '90-audit/synthetic-unit-review.json'
        write(self.root / review, {'synthetic': 'contract test only, not semantic acceptance'})
        evidence = {'file': review, 'sha256': sha(self.root / review), 'reason': 'Synthetic unit fixture only'}
        units = '50-edited/reader-units.json'
        write(self.root / units, {
            'schema_version': '1.0', 'status': 'reviewed',
            'source_sha256': sha(self.root / '20-source/blocks.jsonl'), 'review_evidence': evidence,
            'units': [{'unit_id': 'U1', 'kind': 'main_text', 'source_blocks': [block['block_id']],
                       'source_pages': [1], 'destination': 'final_reader', 'decision_evidence': evidence}],
            'continuations': [],
        })
        self.plan['bindings'][units] = sha(self.root / units)
        self.save()

    def save(self):
        write(self.root / '50-edited/production-plan.json', self.plan)

    def test_focused_11_accepts_complete_bound_fixture(self):
        self.assertEqual(validate_plan(self.root), [])

    def test_focused_rejects_missing_and_wrong_schema(self):
        for schema in (None, '1.0', '1.2', 1.1):
            with self.subTest(schema=schema):
                if schema is None:
                    self.plan.pop('schema_version', None)
                else:
                    self.plan['schema_version'] = schema
                self.save()
                self.assertIn('focused-v1 requires production-plan schema 1.1', str(validate_plan(self.root)))

    def test_focused_legacy_schema_cannot_omit_illustration_contract(self):
        self.plan['schema_version'] = '1.0'
        for name in ILLUSTRATION_BINDINGS:
            self.plan['bindings'].pop(name)
            (self.root / name).unlink()
        self.save()
        self.assertIn('focused-v1 requires production-plan schema 1.1', str(validate_plan(self.root)))

    def test_focused_11_still_requires_plan_and_actual_sample_review(self):
        original = copy.deepcopy(self.plan)
        for missing in (*ILLUSTRATION_BINDINGS, 'sample_review'):
            with self.subTest(missing=missing):
                self.plan = copy.deepcopy(original)
                if missing == 'sample_review':
                    self.plan.pop(missing)
                else:
                    self.plan['bindings'].pop(missing)
                self.save()
                errors = validate_plan(self.root)
                expected = 'actual reading session' if missing == 'sample_review' else 'representative-figure review'
                self.assertIn(expected, str(errors))

    def test_unmarked_110_retains_legacy_plan_without_migration(self):
        self.book.pop('review_protocol')
        write(self.root / 'book.json', self.book)
        self.plan['schema_version'] = '1.0'
        for name in ILLUSTRATION_BINDINGS:
            self.plan['bindings'].pop(name)
            (self.root / name).unlink()
        self.save()
        before = {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        self.assertEqual(validate_plan(self.root), [])
        after = {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        self.assertEqual(before, after)


class FocusedProofApplicability(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='chaoyun-focused-proof-test-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.book = {'book_id': 'synthetic', 'workflow_schema_version': '1.10',
                     'delivery_mode': 'ordinary_reader', 'review_protocol': 'focused-v1'}

    def save(self):
        write(self.root / 'book.json', self.book)

    def test_focused_requires_explicit_applicability(self):
        self.save()
        self.assertIn('requires explicit layout_proof_applicability', str(validate_proof(self.root)))

    def test_focused_rejects_malformed_applicability(self):
        values = (None, [], {}, {'required': 1, 'reason': 'synthetic'},
                  {'required': 'false', 'reason': 'synthetic'}, {'required': False},
                  {'required': False, 'reason': '  '}, {'required': False, 'reason': 3})
        for value in values:
            with self.subTest(value=value):
                self.book['layout_proof_applicability'] = value
                self.save()
                self.assertTrue(validate_proof(self.root))

    def test_required_proof_cannot_be_missing_even_for_candidate_check(self):
        self.book['layout_proof_applicability'] = {'required': True, 'reason': 'Synthetic complex-column diagnosis'}
        self.save()
        for require_acceptance in (False, True):
            with self.subTest(require_acceptance=require_acceptance):
                self.assertIn('required=true requires layout_proof_review',
                              str(validate_proof(self.root, require_acceptance=require_acceptance)))

    def test_required_proof_cannot_be_disabled_in_its_registration(self):
        self.book['layout_proof_applicability'] = {'required': True, 'reason': 'Synthetic complex-column diagnosis'}
        for config in ({}, {'required': False, 'record': 'proof.json'}, []):
            with self.subTest(config=config):
                self.book['layout_proof_review'] = config
                self.save()
                self.assertIn('must remain required once registered', str(validate_proof(self.root)))

    def test_explicit_not_applicable_does_not_create_a_proof(self):
        self.book['layout_proof_applicability'] = {'required': False, 'reason': 'Synthetic text-only diagnosis'}
        self.save()
        before = (self.root / 'book.json').read_bytes()
        self.assertEqual(validate_proof(self.root), [])
        self.assertEqual((self.root / 'book.json').read_bytes(), before)
        self.assertEqual(list(self.root.iterdir()), [self.root / 'book.json'])

    def test_not_applicable_conflicts_with_registered_required_proof(self):
        self.book['layout_proof_applicability'] = {'required': False, 'reason': 'Synthetic text-only diagnosis'}
        self.book['layout_proof_review'] = {'required': True, 'record': 'proof.json'}
        self.save()
        self.assertIn('conflicts with registered layout_proof_review', str(validate_proof(self.root)))

    def test_required_sample_proof_is_sufficient_without_whole_book_rebuild(self):
        # Reuse the existing explicitly synthetic accepted sample, including all
        # PDF and semantic bindings; this exercises the full original validator.
        fixture = proof_fixtures.LayoutProofTests('test_valid_record')
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        # The accepted proof covers page 1 of a two-page synthetic source.
        # Declared sample scope must not be expanded to a complete-book proof.
        source = fixture.root / '00-intake/source.pdf'
        writer = PdfWriter()
        for _ in range(2):
            writer.add_blank_page(width=200, height=300)
        writer.write(str(source))
        fixture.record['source_pdf'] = fixture.ref('00-intake/source.pdf')
        write(fixture.root / '00-intake/source-manifest.json', {
            'staged_source': str(source), 'source_sha256': sha(source)})
        fixture.save_semantic()
        fixture.save()
        fixture.book.update(review_protocol='focused-v1', workflow_schema_version='1.10',
                            source_pdf_pages=2,
                            layout_proof_applicability={'required': True, 'reason': 'Synthetic representative-page diagnosis'})
        write(fixture.root / 'book.json', fixture.book)
        self.assertEqual(fixture.record['scope']['kind'], 'sample')
        self.assertEqual(validate_proof(fixture.root), [])
        fixture.record.update(status='pending', review=None)
        fixture.save()
        self.assertIn('requires actual review: pending', str(validate_proof(fixture.root)))

    def test_unmarked_110_keeps_legacy_opt_in_without_writes(self):
        self.book.pop('review_protocol')
        self.save()
        before = (self.root / 'book.json').read_bytes()
        self.assertEqual(validate_proof(self.root), [])
        self.assertEqual((self.root / 'book.json').read_bytes(), before)
        self.assertEqual(list(self.root.iterdir()), [self.root / 'book.json'])


class FocusedPublisherCli(unittest.TestCase):
    def test_changed_delivery_mode_cannot_skip_focused_profile_validation(self):
        publisher = Path(__file__).resolve().parents[2] / 'chaoyun-quality-publisher/scripts/audit_publication.py'
        with tempfile.TemporaryDirectory(prefix='chaoyun-focused-publisher-test-') as directory:
            root = Path(directory)
            write(root / '50-edited/review-policy.json', {'protocol': 'focused-v1'})
            for mode in ('source_comparison', 'evidence_archive'):
                with self.subTest(mode=mode):
                    write(root / 'book.json', {
                        'workflow_schema_version': '1.10', 'review_protocol': 'focused-v1',
                        'delivery_mode': mode,
                        'layout_proof_applicability': {'required': False, 'reason': 'Synthetic CLI fixture only'},
                    })
                    result = subprocess.run([sys.executable, str(publisher), str(root)],
                                            capture_output=True, text=True)
                    self.assertEqual(result.returncode, 1, result.stderr)
                    report = json.loads(result.stdout)
                    # Missing publication files alone would also fail. Require
                    # the profile error to prove this independent entry runs it.
                    self.assertIn('focused-v1 requires workflow 1.10 ordinary_reader', report['errors'])


if __name__ == '__main__':
    unittest.main()
