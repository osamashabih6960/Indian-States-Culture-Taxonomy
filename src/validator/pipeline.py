"""
Master Image Validation Pipeline and Mandatory Gates Engine.
Evaluates every candidate image across all 10 Mandatory Gates (G1 to G10).
Routes images safely into:
- images_accepted/
- images_quarantine/
- images_rejected/
"""

from pathlib import Path
from typing import Dict, Any, Tuple, Optional
import shutil

from src.config import (
    STATUS_APPROVED,
    STATUS_REJECTED,
    STATUS_QUARANTINE,
    STATUS_UNVERIFIED,
    ACCEPTED_DIR,
    QUARANTINE_DIR,
    REJECTED_DIR,
    GATE_DEFINITIONS
)

from src.validator.stage_a_integrity import validate_file_integrity
from src.validator.stage_b_quality import validate_image_quality
from src.validator.two_pass_critique import execute_two_pass_validation
from src.validator.state_association import verify_state_association
from src.validator.license_filter import verify_license
from src.validator.deduplication import GlobalDeduplicator


class ImageValidationPipeline:
    def __init__(self, deduplicator: Optional[GlobalDeduplicator] = None):
        self.deduplicator = deduplicator or GlobalDeduplicator()

    def validate_image(
        self,
        image_path: Path,
        claimed_state: str,
        claimed_category: str,
        claimed_concept: Optional[str] = None,
        source_page_url: Optional[str] = None,
        direct_image_url: Optional[str] = None,
        creator: Optional[str] = None,
        license_name: Optional[str] = None,
        license_url: Optional[str] = None,
        attribution_text: Optional[str] = None,
        source_description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Evaluate image across all 10 Mandatory Gates (G1 to G10).
        Returns a complete audit dictionary with verdicts for all gates.
        """
        audit_record: Dict[str, Any] = {
            "image_path": str(image_path),
            "filename": image_path.name,
            "original_folder": str(image_path.parent),
            "claimed_state": claimed_state,
            "claimed_category": claimed_category,
            "claimed_concept": claimed_concept or "",
            "source_page_url": source_page_url or "",
            "direct_image_url": direct_image_url or "",
            "creator": creator or "Unknown",
            "license_name": license_name or "Unknown",
            "license_url": license_url or "",
            "attribution_text": attribution_text or "",
            # Gate verdicts
            "G1_integrity": False,
            "G2_visual_match": False,
            "G3_concept_support": False,
            "G4_state_association": False,
            "G5_license_permitted": False,
            "G6_no_exact_duplicate": False,
            "G7_no_near_duplicate": False,
            "G8_provenance_saved": False,
            "G9_two_pass_agreement": False,
            "G10_category_rules": False,
            # Master outcome
            "final_decision": STATUS_UNVERIFIED,
            "rejection_or_warning_reason": "",
            "failed_gates": [],
            "technical_quality": {},
            "visual_details": {},
            "state_details": {},
            "license_details": {},
            "duplicate_details": {}
        }

        # ----------------------------------------------------
        # GATE 8: Provenance metadata presence check
        # ----------------------------------------------------
        if source_page_url and len(source_page_url.strip()) > 5:
            audit_record["G8_provenance_saved"] = True
        else:
            audit_record["failed_gates"].append("G8")
            audit_record["rejection_or_warning_reason"] = "Missing essential source page provenance URL."
            audit_record["final_decision"] = STATUS_REJECTED
            return audit_record

        # ----------------------------------------------------
        # GATE 1: Stage A File Integrity & Stage B Quality
        # ----------------------------------------------------
        a_pass, a_reason, a_meta = validate_file_integrity(image_path)
        audit_record["technical_quality"].update(a_meta)
        if not a_pass:
            audit_record["failed_gates"].append("G1")
            audit_record["rejection_or_warning_reason"] = f"G1 Integrity Failed: {a_reason}"
            audit_record["final_decision"] = STATUS_REJECTED
            return audit_record

        b_pass, b_reason, b_meta = validate_image_quality(image_path)
        audit_record["technical_quality"].update(b_meta)
        if not b_pass:
            audit_record["failed_gates"].append("G1")
            audit_record["rejection_or_warning_reason"] = f"G1 Quality Failed: {b_reason}"
            audit_record["final_decision"] = STATUS_REJECTED
            return audit_record

        audit_record["G1_integrity"] = True

        # ----------------------------------------------------
        # GATE 6 & 7: Global Deduplication
        # ----------------------------------------------------
        is_dup, dup_reason, dup_meta = self.deduplicator.check_duplicate(image_path)
        audit_record["duplicate_details"] = dup_meta
        if is_dup:
            if dup_meta["duplicate_type"] == "EXACT_SHA256":
                audit_record["failed_gates"].append("G6")
                audit_record["rejection_or_warning_reason"] = f"G6 Duplicate Failed: {dup_reason}"
            else:
                audit_record["failed_gates"].append("G7")
                audit_record["rejection_or_warning_reason"] = f"G7 Near-Duplicate Failed: {dup_reason}"
            audit_record["final_decision"] = STATUS_REJECTED
            return audit_record

        audit_record["G6_no_exact_duplicate"] = True
        audit_record["G7_no_near_duplicate"] = True

        # ----------------------------------------------------
        # GATE 5: License Filter
        # ----------------------------------------------------
        lic_verdict, lic_reason, lic_meta = verify_license(
            license_name=license_name,
            source_page_url=source_page_url,
            direct_image_url=direct_image_url,
            creator=creator,
            license_url=license_url,
            attribution_text=attribution_text
        )
        audit_record["license_details"] = lic_meta
        if lic_verdict == STATUS_REJECTED:
            audit_record["failed_gates"].append("G5")
            audit_record["rejection_or_warning_reason"] = f"G5 Licence Rejected: {lic_reason}"
            audit_record["final_decision"] = STATUS_REJECTED
            return audit_record
        elif lic_verdict == STATUS_QUARANTINE:
            audit_record["failed_gates"].append("G5")
            audit_record["rejection_or_warning_reason"] = f"G5 Licence Quarantined: {lic_reason}"
            audit_record["final_decision"] = STATUS_QUARANTINE
            # Continue checking other gates for comprehensive audit report
        else:
            audit_record["G5_license_permitted"] = True

        # ----------------------------------------------------
        # GATE 4: State Association Verification
        # ----------------------------------------------------
        state_verdict, state_reason, state_meta = verify_state_association(
            claimed_state=claimed_state,
            category=claimed_category,
            concept=claimed_concept,
            source_url=source_page_url,
            source_description=source_description
        )
        audit_record["state_details"] = state_meta
        if state_verdict == STATUS_REJECTED:
            audit_record["failed_gates"].append("G4")
            audit_record["rejection_or_warning_reason"] = f"G4 State Mismatch: {state_reason}"
            audit_record["final_decision"] = STATUS_REJECTED
            return audit_record
        elif state_verdict == STATUS_QUARANTINE:
            audit_record["failed_gates"].append("G4")
            if not audit_record["rejection_or_warning_reason"]:
                audit_record["rejection_or_warning_reason"] = f"G4 State Unconfirmed: {state_reason}"
            audit_record["final_decision"] = STATUS_QUARANTINE
        else:
            audit_record["G4_state_association"] = True

        # ----------------------------------------------------
        # GATE 2, 3, 9, 10: Two-Pass Visual Inspection & Critique
        # ----------------------------------------------------
        vis_verdict, vis_reason, vis_meta = execute_two_pass_validation(
            image_path=image_path,
            claimed_category=claimed_category,
            claimed_concept=claimed_concept,
            claimed_state=claimed_state,
            source_description=source_description,
            quality_meta=b_meta
        )
        audit_record["visual_details"] = vis_meta

        if vis_verdict == STATUS_REJECTED:
            audit_record["failed_gates"].extend(["G2", "G9"])
            audit_record["rejection_or_warning_reason"] = f"Visual Verification Rejected: {vis_reason}"
            audit_record["final_decision"] = STATUS_REJECTED
            return audit_record
        elif vis_verdict in [STATUS_QUARANTINE, STATUS_UNVERIFIED]:
            audit_record["failed_gates"].append("G9")
            if not audit_record["rejection_or_warning_reason"]:
                audit_record["rejection_or_warning_reason"] = f"Visual Verification Flagged: {vis_reason}"
            audit_record["final_decision"] = vis_verdict
        else:
            audit_record["G2_visual_match"] = True
            audit_record["G3_concept_support"] = True
            audit_record["G9_two_pass_agreement"] = True
            audit_record["G10_category_rules"] = True

        # Final determination if all 10 gates passed
        if len(audit_record["failed_gates"]) == 0:
            audit_record["final_decision"] = STATUS_APPROVED
            audit_record["rejection_or_warning_reason"] = "All 10 mandatory validation gates passed."
            # Register in deduplicator
            self.deduplicator.register_image(image_path)

        return audit_record

    def route_and_store_image(
        self,
        image_path: Path,
        audit_record: Dict[str, Any],
        target_filename: Optional[str] = None
    ) -> Path:
        """
        Safely copies image into the proper destination folder without deleting the original:
        - images_accepted/<State>/<Category>/<filename>
        - images_quarantine/<State>/<Category>/<filename>
        - images_rejected/<State>/<Category>/<filename>
        """
        decision = audit_record["final_decision"]
        state = audit_record["claimed_state"]
        category = audit_record["claimed_category"]

        if decision == STATUS_APPROVED:
            target_dir = ACCEPTED_DIR / state / category
        elif decision in [STATUS_QUARANTINE, STATUS_UNVERIFIED]:
            target_dir = QUARANTINE_DIR / state / category
        else:
            target_dir = REJECTED_DIR / state / category

        target_dir.mkdir(parents=True, exist_ok=True)
        filename_to_use = target_filename or image_path.name
        dest_path = target_dir / filename_to_use

        # Copy without destroying original (skip if already in destination)
        if dest_path.resolve() != image_path.resolve():
            shutil.copy2(image_path, dest_path)
        return dest_path
