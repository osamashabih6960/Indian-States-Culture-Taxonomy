"""
IndiaCulFair CLI - Research Data Curator & Validation Pipeline.
Usage:
  python3 main.py audit --archive /path/to/archive.zip
  python3 main.py audit --dir /path/to/extracted_folder
  python3 main.py test
  python3 main.py collect --state Kerala --category Cuisine --target 200
"""

import argparse
import sys
import zipfile
from pathlib import Path

from src.config import (
    STAGING_DIR,
    REPORTS_DIR,
    TARGET_STATES,
    TARGET_CATEGORIES,
    ACCEPTED_DIR
)
from src.validator.pipeline import ImageValidationPipeline
from src.audit.auditor import DatasetAuditor
from src.gallery.review_gallery import generate_html_review_gallery
from src.collector.downloader import VerifiedCollector


def run_archive_audit(archive_path: Path):
    """Safely extracts ZIP into staging and runs baseline recursive audit."""
    print(f"=== INGESTING ARCHIVE: {archive_path} ===")
    if not archive_path.exists():
        print(f"Error: Archive {archive_path} does not exist.")
        sys.exit(1)

    extract_dest = STAGING_DIR / f"extracted_{archive_path.stem}"
    extract_dest.mkdir(parents=True, exist_ok=True)

    print(f"Extracting safely into staging area: {extract_dest}")
    with zipfile.ZipFile(archive_path, "r") as zip_ref:
        zip_ref.extractall(extract_dest)

    run_directory_audit(extract_dest)


def run_directory_audit(dir_path: Path):
    """Audits directory of images, produces all 10 reports and visual gallery."""
    print(f"=== COMMENCING DATASET AUDIT ON: {dir_path} ===")
    auditor = DatasetAuditor()
    records = auditor.audit_directory(dir_path, route_files=True)
    report_paths = auditor.generate_all_reports()

    # Generate HTML gallery
    gallery_path = generate_html_review_gallery(records)

    print("\n=== AUDIT SUMMARY ===")
    total = len(records)
    approved = sum(1 for r in records if r["final_decision"] == "APPROVED")
    quarantine = sum(1 for r in records if r["final_decision"] in ["QUARANTINE", "UNVERIFIED"])
    rejected = sum(1 for r in records if r["final_decision"] == "REJECTED")

    print(f"Total Processed: {total}")
    print(f"Approved (Unique): {approved}")
    print(f"Quarantined:       {quarantine}")
    print(f"Rejected:          {rejected}")
    print(f"\nAll 10 reports and matrices written to: {REPORTS_DIR}")
    print(f"Interactive Review Gallery: {gallery_path}")


def main():
    parser = argparse.ArgumentParser(description="IndiaCulFair Strict Validation & Data Curation Pipeline")
    subparsers = parser.add_subparsers(dest="command")

    audit_parser = subparsers.add_parser("audit", help="Audit an archive or folder")
    audit_parser.add_argument("--archive", type=Path, help="Path to ZIP archive")
    audit_parser.add_argument("--dir", type=Path, help="Path to directory")

    test_parser = subparsers.add_parser("test", help="Execute self-test suite")

    collect_parser = subparsers.add_parser("collect", help="Collect replacement candidates")
    collect_parser.add_argument("--state", type=str, required=True, choices=TARGET_STATES)
    collect_parser.add_argument("--category", type=str, required=True, choices=list(TARGET_CATEGORIES.values()))
    collect_parser.add_argument("--concept", type=str, help="Specific cultural concept to query")
    collect_parser.add_argument("--target", type=int, default=200)

    collect_all_parser = subparsers.add_parser("collect-all", help="Collect verified images across all 7 states")
    collect_all_parser.add_argument("--target", type=int, default=200, help="Target images per cell (default 200)")
    collect_all_parser.add_argument("--per-state", type=int, default=None, help="Target images per state category")

    reaudit_parser = subparsers.add_parser("re-audit", help="Re-audit accepted directory and regenerate all 10 reports and matrices")

    args = parser.parse_args()

    if args.command == "audit":
        if args.archive:
            run_archive_audit(args.archive)
        elif args.dir:
            run_directory_audit(args.dir)
        else:
            print("Specify --archive or --dir for audit.")
    elif args.command == "re-audit":
        print("Re-auditing accepted images and regenerating all reports...")
        run_directory_audit(ACCEPTED_DIR)
    elif args.command == "test":
        print("Running pipeline self-test...")
        import subprocess
        res = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests"], capture_output=False)
        sys.exit(res.returncode)
    elif args.command == "collect":
        collector = VerifiedCollector()
        target = args.target

        # If concept specified, use it; otherwise use curated queries for the state & category
        if args.concept:
            queries = [f"{args.state} {args.concept}"]
        else:
            queries = collector.get_curated_search_queries(args.state, args.category)

        print(f"=== COLLECTING VERIFIED IMAGES FOR {args.state} — {args.category} (Target: {target}) ===")
        cell_dir = ACCEPTED_DIR / args.state / args.category
        approved_count = len(list(cell_dir.glob("*.*"))) if cell_dir.exists() else 0

        for q in queries:
            if approved_count >= target:
                break
            for offset in [0, 30]:
                if approved_count >= target:
                    break
                print(f"\nSearching curated query: '{q}' (offset {offset})...")
                candidates = collector.search_wikimedia_commons(q, limit=30, offset=offset)
                print(f"Found {len(candidates)} candidates.")

                for cand in candidates:
                    if approved_count >= target:
                        break
                    concept_name = args.concept or q.replace(args.state, "").strip()
                    approved, meta = collector.download_and_validate_candidate(
                        cand,
                        claimed_state=args.state,
                        claimed_category=args.category,
                        claimed_concept=concept_name
                    )
                    status = meta.get("final_decision", "REJECTED")
                    reason = meta.get("rejection_or_warning_reason", "Unknown reason")

                    if approved:
                        approved_count += 1
                        print(f"  [APPROVED {approved_count}/{target}] {cand['filename']}")
                    else:
                        print(f"  [{status}] {cand['filename']}: {reason}")

        print(f"\nCollection session finished. Approved unique images: {approved_count}/{target}")
        run_directory_audit(ACCEPTED_DIR)
    elif args.command == "collect-all":
        collector = VerifiedCollector()
        target_per_cell = args.per_state if args.per_state is not None else args.target
        print(f"=== COMMENCING BATCH VERIFIED COLLECTION ACROSS ALL 7 STATES (Quota: {target_per_cell}/cell, Total: {target_per_cell * 49}) ===")

        # Strictly include all 7 fixed top-level categories
        all_categories = ["Monuments", "Festivals", "Art & Crafts", "Cuisine", "Attire", "Cultural Symbols", "Communities"]

        for state in TARGET_STATES:
            print(f"\n==========================================")
            print(f"PROCESSING STATE: {state.upper()}")
            print(f"==========================================")

            for cat in all_categories:
                cell_dir = ACCEPTED_DIR / state / cat
                existing_files = list(cell_dir.glob("*.*")) if cell_dir.exists() else []
                approved_for_cell = len(existing_files)

                print(f"\nTargeting {state} — {cat}: Current approved = {approved_for_cell}/{target_per_cell}")
                if approved_for_cell >= target_per_cell:
                    print(f"  Cell quota already fulfilled ({approved_for_cell}/{target_per_cell}). Moving to next cell.")
                    continue

                queries = collector.get_curated_search_queries(state, cat)

                for q in queries:
                    if approved_for_cell >= target_per_cell:
                        break
                    for offset in [0, 30]:
                        if approved_for_cell >= target_per_cell:
                            break
                        candidates = collector.search_wikimedia_commons(q, limit=30, offset=offset)
                        if not candidates:
                            break

                        for cand in candidates:
                            if approved_for_cell >= target_per_cell:
                                break
                            try:
                                concept_name = q.replace(state, "").strip()
                                approved, meta = collector.download_and_validate_candidate(
                                    cand,
                                    claimed_state=state,
                                    claimed_category=cat,
                                    claimed_concept=concept_name
                                )
                                if approved:
                                    approved_for_cell += 1
                                    print(f"  [APPROVED {approved_for_cell}/{target_per_cell}] {cand['filename']}")
                                else:
                                    status = meta.get("final_decision", "REJECTED")
                                    reason = meta.get("rejection_or_warning_reason", "Review needed")
                                    print(f"  [{status}] {cand['filename']}: {reason}")
                            except Exception as item_err:
                                print(f"  [SKIPPED] Error processing candidate '{cand.get('filename')}': {item_err}")
                                continue

        print("\n=== BATCH COLLECTION COMPLETE: RE-SYNCHRONIZING AUDIT REPORTS & MATRICES ===")
        run_directory_audit(ACCEPTED_DIR)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
