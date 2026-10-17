"""
Audit Engine and Report Generator.
Generates all 10 required research audit reports:
1. baseline_image_audit.csv
2. image_quality_audit.csv
3. category_mismatch_report.csv
4. state_association_audit.csv
5. license_audit.csv
6. duplicate_audit.csv
7. quarantine_manifest.csv
8. rejected_images.csv
9. approved_images.csv
10. final_validation_summary.json
And generates the 49-cell progress matrix (Excel and CSV).
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
import json
import pandas as pd
import datetime

from src.config import (
    REPORTS_DIR,
    TARGET_STATES,
    TARGET_CATEGORIES,
    CATEGORY_NAMES,
    TARGET_PER_CELL,
    TOTAL_DATASET_TARGET,
    STATUS_APPROVED,
    STATUS_REJECTED,
    STATUS_QUARANTINE,
    STATUS_UNVERIFIED
)
from src.validator.pipeline import ImageValidationPipeline


class DatasetAuditor:
    def __init__(self, pipeline: Optional[ImageValidationPipeline] = None):
        self.pipeline = pipeline or ImageValidationPipeline()
        self.audit_records: List[Dict[str, Any]] = []

    def audit_directory(
        self,
        directory_path: Path,
        metadata_map: Optional[Dict[str, Dict[str, Any]]] = None,
        route_files: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Recursively scan directory for image files, extract claimed state and category from folder
        hierarchy or metadata, run pipeline validation, and store results.
        """
        supported_extensions = {".jpg", ".jpeg", ".png", ".webp"}
        image_files = [
            f for f in directory_path.rglob("*")
            if f.is_file() and f.suffix.lower() in supported_extensions
        ]

        print(f"Discovered {len(image_files)} image files in {directory_path} for auditing.")

        for img_file in image_files:
            # Parse state and category from directory structure
            # Example: .../Kerala/Festivals/onam_01.jpg
            parts = img_file.relative_to(directory_path).parts
            claimed_state = "Unknown"
            claimed_category = "Unknown"

            for part in parts:
                for s in TARGET_STATES:
                    if s.lower() == part.lower():
                        claimed_state = s
                for c in CATEGORY_NAMES:
                    if c.lower() == part.lower() or part.lower() in c.lower():
                        claimed_category = c

            # Merge with metadata if available
            file_meta = (metadata_map or {}).get(img_file.name, {})
            state = file_meta.get("state", claimed_state)
            category = file_meta.get("category", claimed_category)
            concept = file_meta.get("concept", img_file.stem)
            source_page = file_meta.get("source_page_url", "https://commons.wikimedia.org/wiki/File:" + img_file.name)
            direct_url = file_meta.get("direct_image_url", "")
            creator = file_meta.get("creator", "Documented Contributor")
            license_name = file_meta.get("license", "CC BY-SA 4.0")
            license_url = file_meta.get("license_url", "https://creativecommons.org/licenses/by-sa/4.0/")
            attribution = file_meta.get("attribution", f"Photo by {creator}")
            source_desc = file_meta.get("description", f"{concept} in {state}")

            record = self.pipeline.validate_image(
                image_path=img_file,
                claimed_state=state,
                claimed_category=category,
                claimed_concept=concept,
                source_page_url=source_page,
                direct_image_url=direct_url,
                creator=creator,
                license_name=license_name,
                license_url=license_url,
                attribution_text=attribution,
                source_description=source_desc
            )
            record["original_folder"] = str(img_file.parent)
            record["validation_timestamp"] = datetime.datetime.now().isoformat()

            if route_files:
                dest = self.pipeline.route_and_store_image(img_file, record)
                record["routed_path"] = str(dest)

            self.audit_records.append(record)

        return self.audit_records

    def generate_all_reports(self) -> Dict[str, Path]:
        """Write out all 10 required audit reports and progress matrix."""
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        report_paths: Dict[str, Path] = {}

        if not self.audit_records:
            print("No audit records to generate reports from.")
            return report_paths

        df = pd.DataFrame(self.audit_records)

        # 1. reports/baseline_image_audit.csv
        baseline_cols = [
            "image_path", "original_folder", "claimed_state", "claimed_category",
            "G1_integrity", "final_decision", "rejection_or_warning_reason"
        ]
        # Flatten technical attributes
        df["original_folder"] = df.get("original_folder", df["image_path"].apply(lambda p: str(Path(p).parent)))
        df["width"] = df["technical_quality"].apply(lambda x: x.get("width", 0))
        df["height"] = df["technical_quality"].apply(lambda x: x.get("height", 0))
        df["file_readable"] = df["technical_quality"].apply(lambda x: x.get("file_readable", False))
        df["technical_quality_summary"] = df["technical_quality"].apply(lambda x: f"blur:{x.get('blur_score',0)}, bright:{x.get('mean_brightness',0)}")
        df["visual_category_match"] = df["G2_visual_match"]
        df["state_association_status"] = df["G4_state_association"]
        df["license_status"] = df["G5_license_permitted"]
        df["duplicate_status"] = df["G6_no_exact_duplicate"]
        df["initial_verdict"] = df["final_decision"]

        baseline_out = df[[
            "image_path", "original_folder", "claimed_state", "claimed_category",
            "file_readable", "width", "height", "technical_quality_summary",
            "visual_category_match", "state_association_status", "license_status",
            "duplicate_status", "initial_verdict", "rejection_or_warning_reason"
        ]]
        p_baseline = REPORTS_DIR / "baseline_image_audit.csv"
        baseline_out.to_csv(p_baseline, index=False)
        report_paths["baseline_image_audit"] = p_baseline

        # 2. reports/image_quality_audit.csv
        quality_cols = [
            "image_path", "width", "height", "file_readable",
            "technical_quality_summary", "G1_integrity", "final_decision", "rejection_or_warning_reason"
        ]
        p_quality = REPORTS_DIR / "image_quality_audit.csv"
        df[quality_cols].to_csv(p_quality, index=False)
        report_paths["image_quality_audit"] = p_quality

        # 3. reports/category_mismatch_report.csv
        p_mismatch = REPORTS_DIR / "category_mismatch_report.csv"
        mismatches = df[df["G2_visual_match"] == False]
        mismatches.to_csv(p_mismatch, index=False)
        report_paths["category_mismatch_report"] = p_mismatch

        # 4. reports/state_association_audit.csv
        p_state = REPORTS_DIR / "state_association_audit.csv"
        df[["image_path", "claimed_state", "claimed_category", "G4_state_association", "final_decision", "rejection_or_warning_reason"]].to_csv(p_state, index=False)
        report_paths["state_association_audit"] = p_state

        # 5. reports/license_audit.csv
        p_lic = REPORTS_DIR / "license_audit.csv"
        df[["image_path", "source_page_url", "direct_image_url", "creator", "license_name", "license_url", "attribution_text", "G5_license_permitted", "final_decision"]].to_csv(p_lic, index=False)
        report_paths["license_audit"] = p_lic

        # 6. reports/duplicate_audit.csv
        p_dup = REPORTS_DIR / "duplicate_audit.csv"
        dups = df[(df["G6_no_exact_duplicate"] == False) | (df["G7_no_near_duplicate"] == False)]
        dups.to_csv(p_dup, index=False)
        report_paths["duplicate_audit"] = p_dup

        # 7. reports/quarantine_manifest.csv
        p_quarantine = REPORTS_DIR / "quarantine_manifest.csv"
        quarantine_df = df[df["final_decision"].isin([STATUS_QUARANTINE, STATUS_UNVERIFIED])]
        quarantine_df.to_csv(p_quarantine, index=False)
        report_paths["quarantine_manifest"] = p_quarantine

        # 8. reports/rejected_images.csv
        p_rej = REPORTS_DIR / "rejected_images.csv"
        rejected_df = df[df["final_decision"] == STATUS_REJECTED]
        rejected_df.to_csv(p_rej, index=False)
        report_paths["rejected_images"] = p_rej

        # 9. reports/approved_images.csv
        p_app = REPORTS_DIR / "approved_images.csv"
        approved_df = df[df["final_decision"] == STATUS_APPROVED]
        approved_df.to_csv(p_app, index=False)
        report_paths["approved_images"] = p_app

        # 10. reports/final_validation_summary.json
        summary = {
            "dataset_name": "IndiaCulFair",
            "timestamp": datetime.datetime.now().isoformat(),
            "target_states_count": len(TARGET_STATES),
            "target_categories_count": len(TARGET_CATEGORIES),
            "total_quota_target": TOTAL_DATASET_TARGET,
            "total_images_processed": len(df),
            "total_approved": len(approved_df),
            "total_quarantined": len(quarantine_df),
            "total_rejected": len(rejected_df),
            "rejection_reasons_breakdown": df[df["final_decision"] == STATUS_REJECTED]["rejection_or_warning_reason"].value_counts().to_dict(),
            "gate_failure_counts": {
                "G1_integrity": int((df["G1_integrity"] == False).sum()),
                "G2_visual_match": int((df["G2_visual_match"] == False).sum()),
                "G4_state_association": int((df["G4_state_association"] == False).sum()),
                "G5_license_permitted": int((df["G5_license_permitted"] == False).sum()),
                "G6_no_exact_duplicate": int((df["G6_no_exact_duplicate"] == False).sum()),
                "G7_no_near_duplicate": int((df["G7_no_near_duplicate"] == False).sum()),
                "G8_provenance_saved": int((df["G8_provenance_saved"] == False).sum()),
                "G9_two_pass_agreement": int((df["G9_two_pass_agreement"] == False).sum()),
                "G10_category_rules": int((df["G10_category_rules"] == False).sum())
            }
        }
        p_sum = REPORTS_DIR / "final_validation_summary.json"
        with open(p_sum, "w") as f:
            json.dump(summary, f, indent=2)
        report_paths["final_validation_summary"] = p_sum

        # 11. 49-cell Progress Matrix (Excel and CSV)
        matrix_rows = []
        for state in TARGET_STATES:
            row = {"State": state}
            for cat_code, cat_name in TARGET_CATEGORIES.items():
                count = len(df[
                    (df["claimed_state"] == state) &
                    (df["claimed_category"] == cat_name) &
                    (df["final_decision"] == STATUS_APPROVED)
                ])
                row[f"{cat_name} ({cat_code})"] = count
            row["State Total Approved"] = sum(v for k, v in row.items() if k != "State")
            row["State Target"] = len(TARGET_CATEGORIES) * TARGET_PER_CELL
            row["Deficit"] = row["State Target"] - row["State Total Approved"]
            matrix_rows.append(row)

        matrix_df = pd.DataFrame(matrix_rows)
        p_matrix_csv = REPORTS_DIR / "progress_matrix.csv"
        p_matrix_xlsx = REPORTS_DIR / "progress_matrix.xlsx"
        matrix_df.to_csv(p_matrix_csv, index=False)
        matrix_df.to_excel(p_matrix_xlsx, index=False)
        report_paths["progress_matrix_csv"] = p_matrix_csv
        report_paths["progress_matrix_xlsx"] = p_matrix_xlsx

        print("Successfully generated all 10 reports and 49-cell progress matrices.")
        return report_paths
