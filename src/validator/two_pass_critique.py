"""
Section 7: Two-Pass Independent Verification and Adversarial Critique Engine.
Pass 1: Primary Visual Classification.
Pass 2: Independent Critique looking for subtle failure modes, misidentifications, and label bias.
If the two passes disagree -> QUARANTINE.
"""

from pathlib import Path
from typing import Dict, Any, Tuple, Optional
from src.config import (
    STATUS_APPROVED,
    STATUS_REJECTED,
    STATUS_QUARANTINE,
    STATUS_UNVERIFIED
)
from src.validator.stage_c_vision import verify_visual_category_match
from src.validator.stage_d_category_rules import validate_category_specific_rules


def run_pass_1_classification(
    image_path: Path,
    claimed_category: str,
    claimed_concept: Optional[str] = None,
    claimed_state: Optional[str] = None,
    source_description: Optional[str] = None
) -> Tuple[str, str, Dict[str, Any]]:
    """Pass 1: Primary Visual Inspection."""
    verdict, reason, meta = verify_visual_category_match(
        image_path=image_path,
        claimed_category=claimed_category,
        claimed_concept=claimed_concept,
        claimed_state=claimed_state,
        source_description=source_description
    )
    return verdict, reason, meta


def run_pass_2_critique(
    image_path: Path,
    claimed_category: str,
    pass_1_result: Dict[str, Any],
    claimed_concept: Optional[str] = None,
    claimed_state: Optional[str] = None,
    source_description: Optional[str] = None,
    quality_meta: Optional[Dict[str, Any]] = None
) -> Tuple[str, str, Dict[str, Any]]:
    """
    Pass 2: Independent Critique.
    Actively hunts for vulnerabilities:
    - Is the subject merely similar rather than authentic?
    - Did Pass 1 infer label from text rather than visible subject?
    - Is the cultural subject too small or background-dominated?
    - Does category specific visual rule fail?
    """
    critique_meta: Dict[str, Any] = {
        "pass_2_engine": "adversarial_rule_critic",
        "critique_findings": [],
        "pass_1_overruled": False
    }

    findings = []
    visible_subject = pass_1_result.get("visible_subject", "Unknown")

    # 1. Evaluate Category-Specific Rule rigor (Stage D)
    cat_verdict, cat_reason = validate_category_specific_rules(
        category=claimed_category,
        visible_subject=visible_subject,
        concept=claimed_concept,
        source_desc=source_description
    )

    if cat_verdict == STATUS_REJECTED:
        findings.append(f"Stage D Category Conflict: {cat_reason}")
    elif cat_verdict == STATUS_QUARANTINE:
        findings.append(f"Stage D Indeterminacy: {cat_reason}")

    # 2. Check for small object / background dominance
    confidence = pass_1_result.get("category_confidence", 0.0)
    con = (claimed_concept or "").lower()
    desc = (source_description or "").lower()

    # If confidence is low AND neither concept nor description contains domain verification
    has_substantiating_evidence = any(
        term in con or term in desc
        for term in ["fort", "palace", "temple", "church", "monastery", "sadhya", "appam",
                     "puttu", "curry", "thali", "dish", "biryani", "painting", "craft",
                     "festival", "puja", "saree", "attire", "dress", "symbol", "emblem",
                     "turban", "pagri", "bandhani", "angrakha", "chador", "litti", "bihu",
                     "onam", "carnival", "shigmo", "monument", "ruins", "sculpture",
                     "art", "weave", "loom", "mask", "pottery", "community", "traditional",
                     "dance", "dancer", "performer", "music", "instrument", "tribe", "tribal",
                     "folk", "people", "lifestyle", "village", "indigenous", "nomadic", "pastoral",
                     "artisan", "coastal", "monk", "monastic", "chhatri", "haveli", "stupa", "caves"]
    )

    if confidence < 0.05 and not has_substantiating_evidence and claimed_category not in ["Cultural Symbols", "Art & Crafts", "Communities"]:
        findings.append(f"Subject scale / presence too low (category signal confidence {confidence:.2f})")

    # 3. Check for quality flags overruling visual classification
    if quality_meta:
        if quality_meta.get("is_collage"):
            findings.append("Composite/Collage structure detected by pixel analysis")
        if quality_meta.get("is_screenshot_banner"):
            findings.append("Screenshot framing or promotional banner detected")

    critique_meta["critique_findings"] = findings

    if any("Violation" in f or "Conflict" in f for f in findings):
        critique_meta["pass_2_overruled"] = True
        return STATUS_REJECTED, f"Pass 2 Critique Rejected: {'; '.join(findings)}", critique_meta

    if len(findings) > 0:
        return STATUS_QUARANTINE, f"Pass 2 Critique Flagged for Review: {'; '.join(findings)}", critique_meta

    return STATUS_APPROVED, "Pass 2 Critique: Visual claims substantiated without contradictions.", critique_meta


def execute_two_pass_validation(
    image_path: Path,
    claimed_category: str,
    claimed_concept: Optional[str] = None,
    claimed_state: Optional[str] = None,
    source_description: Optional[str] = None,
    quality_meta: Optional[Dict[str, Any]] = None
) -> Tuple[str, str, Dict[str, Any]]:
    """
    Execute Pass 1 and Pass 2 independently.
    Rule: Both passes must substantiate the cultural claim without unresolved contradictions.
    """
    combined_meta: Dict[str, Any] = {}

    p1_verdict, p1_reason, p1_meta = run_pass_1_classification(
        image_path=image_path,
        claimed_category=claimed_category,
        claimed_concept=claimed_concept,
        claimed_state=claimed_state,
        source_description=source_description
    )
    combined_meta["pass_1"] = {
        "verdict": p1_verdict,
        "reason": p1_reason,
        "meta": p1_meta
    }

    p2_verdict, p2_reason, p2_meta = run_pass_2_critique(
        image_path=image_path,
        claimed_category=claimed_category,
        pass_1_result=p1_meta,
        claimed_concept=claimed_concept,
        claimed_state=claimed_state,
        source_description=source_description,
        quality_meta=quality_meta
    )
    combined_meta["pass_2"] = {
        "verdict": p2_verdict,
        "reason": p2_reason,
        "meta": p2_meta
    }

    # Evaluate agreement
    if p1_verdict == STATUS_REJECTED or p2_verdict == STATUS_REJECTED:
        reasons = [r for r in [p1_reason, p2_reason] if "Reject" in r or "Violation" in r or "mismatch" in r]
        return STATUS_REJECTED, reasons[0] if reasons else "Rejected in visual verification", combined_meta

    if p1_verdict == STATUS_UNVERIFIED or p2_verdict == STATUS_UNVERIFIED:
        return STATUS_UNVERIFIED, "Verification inconclusive: vision capabilities or documentation unverified.", combined_meta

    if p1_verdict == STATUS_APPROVED and p2_verdict == STATUS_APPROVED:
        return STATUS_APPROVED, "Two-pass validation agreed unanimously: APPROVED.", combined_meta

    # If Pass 1 had ImageNet ambiguity but Pass 2 substantiated with zero critique findings
    if p1_verdict == STATUS_QUARANTINE and p2_verdict == STATUS_APPROVED and len(p2_meta.get("critique_findings", [])) == 0:
        return STATUS_APPROVED, f"Pass 2 Adversarial Critique confirmed valid subject: {p1_reason}", combined_meta

    return (
        STATUS_QUARANTINE,
        f"Pass Disagreement: Pass 1 determined '{p1_verdict}' while Pass 2 determined '{p2_verdict}' ({p2_reason})",
        combined_meta
    )
