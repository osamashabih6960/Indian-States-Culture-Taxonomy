"""
License Filter and Rights Auditor.
Enforces Section 5: Strict Licence Filter with zero tolerance for unknown, commercial, or non-commercial (NC/ND) rights.
Permits exclusively: CC0, Public Domain, CC BY (all versions), CC BY-SA (all versions).
"""

from typing import Dict, Any, Tuple, Optional
from src.config import (
    PERMITTED_LICENSES,
    FORBIDDEN_LICENSES,
    STATUS_APPROVED,
    STATUS_REJECTED,
    STATUS_QUARANTINE
)


def normalize_license_string(raw_license: Optional[str]) -> str:
    """Normalize license representation for strict matching."""
    if not raw_license:
        return "Unknown"
    norm = raw_license.strip()
    norm_upper = norm.upper()

    if "CC0" in norm_upper or "ZERO" in norm_upper:
        return "CC0 1.0"
    if "PUBLIC DOMAIN" in norm_upper or "PDM" in norm_upper:
        return "Public Domain"
    if "GODL" in norm_upper or "GOVERNMENT OPEN DATA" in norm_upper:
        return "GODL-India"
    if "FAL" in norm_upper or "FREE ART" in norm_upper or "ART LIBRE" in norm_upper:
        return "Free Art License"
    if "CC BY-SA" in norm_upper:
        for ver in ["4.0", "3.0", "2.5", "2.0"]:
            if ver in norm_upper:
                return f"CC BY-SA {ver}"
        return "CC BY-SA"
    if "CC BY-NC-SA" in norm_upper:
        return "CC BY-NC-SA"
    if "CC BY-NC-ND" in norm_upper:
        return "CC BY-NC-ND"
    if "CC BY-NC" in norm_upper:
        return "CC BY-NC"
    if "CC BY-ND" in norm_upper:
        return "CC BY-ND"
    if "CC BY" in norm_upper:
        for ver in ["4.0", "3.0", "2.5", "2.0"]:
            if ver in norm_upper:
                return f"CC BY {ver}"
        return "CC BY"

    return norm


def verify_license(
    license_name: Optional[str],
    source_page_url: Optional[str] = None,
    direct_image_url: Optional[str] = None,
    creator: Optional[str] = None,
    license_url: Optional[str] = None,
    attribution_text: Optional[str] = None
) -> Tuple[str, str, Dict[str, Any]]:
    """
    Section 5: Strict Licence Filter.
    Returns:
    (verdict, reason, license_record)
    """
    normalized_lic = normalize_license_string(license_name)

    record: Dict[str, Any] = {
        "source_page_url": source_page_url or "",
        "direct_image_url": direct_image_url or "",
        "creator": creator or "Unknown",
        "license_name": normalized_lic,
        "license_version": "",
        "license_url": license_url or "",
        "attribution_text": attribution_text or "",
        "license_verification_status": "PENDING"
    }

    # Extract version if present
    parts = normalized_lic.split()
    if len(parts) > 1 and parts[-1][0].isdigit():
        record["license_version"] = parts[-1]

    # Gate 1: Source page must be documented
    if not source_page_url or not source_page_url.startswith("http"):
        record["license_verification_status"] = STATUS_REJECTED
        return (
            STATUS_REJECTED,
            "Licence Check Failed: Missing original source page URL. Cannot establish rights provenance.",
            record
        )

    # Gate 2: Generic 'free' or commercial statements are invalid
    raw_lower = (license_name or "").lower()
    if "free download" in raw_lower or "royalty free" in raw_lower:
        record["license_verification_status"] = STATUS_REJECTED
        return (
            STATUS_REJECTED,
            "Licence Check Failed: 'Free download' or 'Royalty free' is a distribution claim, not an academic open license.",
            record
        )

    # Gate 3: Forbidden Licenses (NC / ND / Copyright / Unknown)
    for forbidden in FORBIDDEN_LICENSES:
        if forbidden.upper() in normalized_lic.upper():
            record["license_verification_status"] = STATUS_REJECTED
            return (
                STATUS_REJECTED,
                f"Licence Incompatible: '{normalized_lic}' contains restrictive terms ({forbidden}) forbidden for core distributable dataset.",
                record
            )

    # Gate 4: Permitted Licenses Check
    is_permitted = any(p.upper() == normalized_lic.upper() or normalized_lic.upper().startswith(p.upper()) for p in PERMITTED_LICENSES)
    if not is_permitted:
        record["license_verification_status"] = STATUS_QUARANTINE
        return (
            STATUS_QUARANTINE,
            f"Unverified Licence: '{normalized_lic}' requires individual manual rights audit before inclusion.",
            record
        )

    # Gate 5: CC BY and CC BY-SA require creator or attribution text
    if "CC BY" in normalized_lic.upper() and normalized_lic.upper() != "CC0 1.0":
        if (not creator or creator.lower() in ["unknown", "none", ""]) and (not attribution_text):
            record["license_verification_status"] = STATUS_QUARANTINE
            return (
                STATUS_QUARANTINE,
                f"Missing Attribution: '{normalized_lic}' requires creator attribution, but creator and attribution text are absent.",
                record
            )

    record["license_verification_status"] = STATUS_APPROVED
    return (
        STATUS_APPROVED,
        f"Verified Academic Open Licence: {normalized_lic}",
        record
    )
