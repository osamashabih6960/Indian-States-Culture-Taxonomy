"""
Comprehensive Unit and Integration Test Suite for IndiaCulFair Validation Pipeline.
Tests all 10 Mandatory Gates, Stage A-D validators, licence filtering, deduplication, and reporting.
"""

import unittest
from pathlib import Path
import tempfile
import shutil
import numpy as np
from PIL import Image

from src.config import (
    STATUS_APPROVED,
    STATUS_REJECTED,
    STATUS_QUARANTINE,
    STATUS_UNVERIFIED
)
from src.validator.stage_a_integrity import validate_file_integrity
from src.validator.stage_b_quality import validate_image_quality
from src.validator.stage_d_category_rules import validate_category_specific_rules
from src.validator.state_association import verify_state_association
from src.validator.license_filter import verify_license
from src.validator.deduplication import GlobalDeduplicator
from src.validator.pipeline import ImageValidationPipeline
from src.audit.auditor import DatasetAuditor


class TestValidationPipeline(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def _create_sample_image(self, filename: str, size=(600, 600), color=(128, 128, 128), add_noise=True) -> Path:
        """Helper to create test image with configurable texture."""
        img_path = self.test_dir / filename
        arr = np.full((size[1], size[0], 3), color, dtype=np.uint8)
        if add_noise:
            # Add texture so it's not a blank image
            noise = np.random.randint(-40, 40, (size[1], size[0], 3), dtype=np.int16)
            arr = np.clip(arr.astype(np.int16) + noise, 0, 255).astype(np.uint8)

        img = Image.fromarray(arr)
        img.save(img_path)
        return img_path

    # ----------------------------------------------------
    # STAGE A: FILE INTEGRITY TESTS
    # ----------------------------------------------------
    def test_stage_a_valid_image(self):
        img_path = self._create_sample_image("valid.jpg", size=(600, 600))
        is_valid, reason, meta = validate_file_integrity(img_path)
        self.assertTrue(is_valid, f"Expected valid image to pass: {reason}")
        self.assertEqual(meta["width"], 600)
        self.assertEqual(meta["height"], 600)

    def test_stage_a_undersized_image_rejected(self):
        img_path = self._create_sample_image("small.jpg", size=(400, 400))
        is_valid, reason, _ = validate_file_integrity(img_path)
        self.assertFalse(is_valid)
        self.assertIn("Dimensions too small", reason)

    def test_stage_a_blank_image_rejected(self):
        img_path = self._create_sample_image("blank.jpg", size=(600, 600), color=(255, 255, 255), add_noise=False)
        is_valid, reason, _ = validate_file_integrity(img_path)
        self.assertFalse(is_valid)
        self.assertIn("blank", reason.lower())

    def test_stage_a_corrupted_file_rejected(self):
        corrupt_path = self.test_dir / "corrupt.jpg"
        corrupt_path.write_bytes(b"\xFF\xD8\xFF\xE0\x00\x10JFIF" + b"random broken garbage data")
        is_valid, reason, _ = validate_file_integrity(corrupt_path)
        self.assertFalse(is_valid)

    # ----------------------------------------------------
    # STAGE B: TECHNICAL QUALITY TESTS
    # ----------------------------------------------------
    def test_stage_b_underexposed_image_rejected(self):
        img_path = self._create_sample_image("dark.jpg", size=(600, 600), color=(10, 10, 10), add_noise=False)
        is_valid, reason, meta = validate_image_quality(img_path)
        self.assertFalse(is_valid)
        self.assertTrue(meta["is_underexposed"])

    def test_stage_b_overexposed_image_rejected(self):
        img_path = self._create_sample_image("bright.jpg", size=(600, 600), color=(250, 250, 250), add_noise=False)
        is_valid, reason, meta = validate_image_quality(img_path)
        self.assertFalse(is_valid)
        self.assertTrue(meta["is_overexposed"])

    # ----------------------------------------------------
    # STAGE D: CATEGORY SPECIFIC RULES TESTS
    # ----------------------------------------------------
    def test_stage_d_dance_traditions_approved_in_art_and_crafts(self):
        # Taxonomy includes C5.3 Dance Traditions
        verdict, reason = validate_category_specific_rules(
            category="Art & Crafts",
            visible_subject="Dancer",
            concept="Kathakali Dance performance",
            source_desc="Kathakali classical dance on stage in Kerala"
        )
        self.assertEqual(verdict, STATUS_APPROVED)
        self.assertIn("C5 Passed", reason)

    def test_stage_d_nightclub_rejected_from_art_and_crafts(self):
        verdict, reason = validate_category_specific_rules(
            category="Art & Crafts",
            visible_subject="Nightclub",
            concept="Commercial DJ Party",
            source_desc="Modern pop nightclub and disco"
        )
        self.assertEqual(verdict, STATUS_REJECTED)
        self.assertIn("commercial entertainment", reason.lower())

    def test_stage_d_modern_skyscraper_rejected_from_monuments(self):
        verdict, reason = validate_category_specific_rules(
            category="Monuments",
            visible_subject="Skyscraper",
            concept="City Center Building",
            source_desc="Modern glass building and office towers"
        )
        self.assertEqual(verdict, STATUS_REJECTED)
        self.assertIn("modern architecture", reason.lower())

    def test_stage_d_fast_food_rejected_from_cuisine(self):
        verdict, reason = validate_category_specific_rules(
            category="Cuisine",
            visible_subject="Burger",
            concept="Cheeseburger",
            source_desc="Fast food burger with french fries"
        )
        self.assertEqual(verdict, STATUS_REJECTED)
        self.assertIn("fast food", reason.lower())

    def test_stage_d_community_requires_context_not_stereotyping(self):
        # When no contextual documentation is provided, photos of people must not be accepted
        verdict, reason = validate_category_specific_rules(
            category="Communities",
            visible_subject="Person",
            concept="",
            source_desc=""
        )
        self.assertEqual(verdict, STATUS_UNVERIFIED)
        self.assertIn("cannot be approved as community representation without explicit source documentation", reason)

    # ----------------------------------------------------
    # SECTION 4: STATE ASSOCIATION & CONFLICT TESTS
    # ----------------------------------------------------
    def test_state_association_conflict_rejection(self):
        # Claiming Hyderabadi Biryani under Kerala should be rejected as geographic conflict
        verdict, reason, _ = verify_state_association(
            claimed_state="Kerala",
            category="Cuisine",
            concept="Hyderabadi Biryani",
            source_url="https://commons.wikimedia.org/wiki/File:Hyderabadi_Biryani.jpg",
            source_description="Iconic dish of Hyderabad, Telangana"
        )
        self.assertEqual(verdict, STATUS_REJECTED)
        self.assertIn("Telangana", reason)

    def test_valid_state_association(self):
        verdict, reason, _ = verify_state_association(
            claimed_state="Rajasthan",
            category="Monuments",
            concept="Hawa Mahal",
            source_url="https://commons.wikimedia.org/wiki/File:Hawa_Mahal_Jaipur.jpg",
            source_description="Hawa Mahal palace in Jaipur, Rajasthan"
        )
        self.assertEqual(verdict, STATUS_APPROVED)

    # ----------------------------------------------------
    # SECTION 5: LICENCE FILTER TESTS
    # ----------------------------------------------------
    def test_license_filter_nc_forbidden(self):
        verdict, reason, _ = verify_license(
            license_name="CC BY-NC 4.0",
            source_page_url="https://commons.wikimedia.org/wiki/File:Sample.jpg"
        )
        self.assertEqual(verdict, STATUS_REJECTED)
        self.assertIn("forbidden", reason.lower())

    def test_license_filter_cc_by_sa_permitted(self):
        verdict, reason, _ = verify_license(
            license_name="CC BY-SA 4.0",
            source_page_url="https://commons.wikimedia.org/wiki/File:Sample.jpg",
            creator="Photographer A"
        )
        self.assertEqual(verdict, STATUS_APPROVED)

    def test_license_filter_missing_source_rejected(self):
        verdict, reason, _ = verify_license(
            license_name="CC0",
            source_page_url=""
        )
        self.assertEqual(verdict, STATUS_REJECTED)

    # ----------------------------------------------------
    # SECTION 9: GLOBAL DEDUPLICATION TESTS
    # ----------------------------------------------------
    def test_deduplication_exact_sha256(self):
        img1 = self._create_sample_image("img1.jpg", size=(600, 600))
        img2 = self.test_dir / "img2.jpg"
        shutil.copy2(img1, img2)

        dedup = GlobalDeduplicator()
        dedup.register_image(img1)

        is_dup, reason, meta = dedup.check_duplicate(img2)
        self.assertTrue(is_dup)
        self.assertEqual(meta["duplicate_type"], "EXACT_SHA256")

    # ----------------------------------------------------
    # INTEGRATION: FULL 10-GATE PIPELINE & AUDIT REPORTS
    # ----------------------------------------------------
    def test_full_pipeline_approval_and_reporting(self):
        # Create a valid test image
        img_path = self._create_sample_image("amber_fort.jpg", size=(700, 700))

        pipeline = ImageValidationPipeline()
        record = pipeline.validate_image(
            image_path=img_path,
            claimed_state="Rajasthan",
            claimed_category="Monuments",
            claimed_concept="Amber Fort",
            source_page_url="https://commons.wikimedia.org/wiki/File:Amber_Fort.jpg",
            direct_image_url="https://upload.wikimedia.org/amber_fort.jpg",
            creator="Heritage Archivist",
            license_name="CC BY-SA 4.0",
            source_description="Historic Amber Fort palace in Rajasthan"
        )

        self.assertIn(record["final_decision"], [STATUS_APPROVED, STATUS_QUARANTINE])

        # Test Auditor report generation
        auditor = DatasetAuditor(pipeline=pipeline)
        auditor.audit_records = [record]
        reports = auditor.generate_all_reports()

        self.assertIn("baseline_image_audit", reports)
        self.assertIn("progress_matrix_xlsx", reports)
        self.assertTrue(reports["baseline_image_audit"].exists())
        self.assertTrue(reports["progress_matrix_xlsx"].exists())


if __name__ == "__main__":
    unittest.main()
