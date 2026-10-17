"""
IndiaCulFair Dataset Configuration and Taxonomies.
Target: 7 states x 7 categories x 200 approved unique images = 9,800 approved unique images.
"""

from pathlib import Path

# Base Paths
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = WORKSPACE_ROOT / "data"
STAGING_DIR = WORKSPACE_ROOT / "staging"
ACCEPTED_DIR = WORKSPACE_ROOT / "images_accepted"
QUARANTINE_DIR = WORKSPACE_ROOT / "images_quarantine"
REJECTED_DIR = WORKSPACE_ROOT / "images_rejected"
REPORTS_DIR = WORKSPACE_ROOT / "reports"

# Ensure foundational directories exist
for directory in [DATA_DIR, STAGING_DIR, ACCEPTED_DIR, QUARANTINE_DIR, REJECTED_DIR, REPORTS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# 1. FIXED RESEARCH REQUIREMENTS
# Exactly 7 Indian States (Strictly NO Union Territories)
TARGET_STATES = [
    "Kerala",
    "Rajasthan",
    "Assam",
    "Goa",
    "Bihar",
    "Telangana",
    "Sikkim"
]

# Exactly 7 Top-Level Categories (Dance is strictly excluded from taxonomy)
TARGET_CATEGORIES = {
    "C1": "Festivals",
    "C2": "Monuments",
    "C3": "Attire",
    "C4": "Cuisine",
    "C5": "Art & Crafts",
    "C6": "Cultural Symbols",
    "C7": "Communities"
}

CATEGORY_NAMES = list(TARGET_CATEGORIES.values())
CATEGORY_CODE_MAP = {v: k for k, v in TARGET_CATEGORIES.items()}

# Quota settings
TARGET_PER_CELL = 200
TOTAL_CELLS = len(TARGET_STATES) * len(TARGET_CATEGORIES)  # 49
TOTAL_DATASET_TARGET = TOTAL_CELLS * TARGET_PER_CELL       # 9,800

# 2. VALIDATION GATES (G1 to G10)
GATE_DEFINITIONS = {
    "G1": "File integrity and technical usability (decodable, dimensions, non-blank)",
    "G2": "Visual content matches assigned top-level category",
    "G3": "Claimed cultural concept matches visual evidence",
    "G4": "State association supported by reliable regional evidence",
    "G5": "Individual image licence is verified and permitted",
    "G6": "No exact SHA-256 duplicate exists in the dataset",
    "G7": "No unacceptable near-duplicate (perceptual hash)",
    "G8": "Source URL and essential provenance metadata preserved",
    "G9": "Two-pass verification critique does not disagree",
    "G10": "Category-specific evidence requirements satisfied"
}

# 3. TECHNICAL IMAGE THRESHOLDS (Stage A & B)
MIN_IMAGE_WIDTH = 512
MIN_IMAGE_HEIGHT = 512
MIN_LAPLACIAN_VARIANCE = 40.0       # Minimum sharpness / blur threshold (40.0 allows authentic portraits/bokeh while rejecting blurry shots)
MIN_BRIGHTNESS = 25.0               # Reject overly dark / underexposed images (0-255 scale)
MAX_BRIGHTNESS = 235.0              # Reject severely overexposed / washed out images
MIN_CONTRAST_STD = 15.0             # Reject low contrast / washed out images
MAX_BLANK_PERCENTAGE = 0.85         # Reject if >85% of pixels are uniform color
ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}
MAX_PERCEPTUAL_HASH_DIFF = 5        # Hamming distance <= 5 flagged as near duplicate

# 4. LICENCE PERMISSIONS (Stage E)
PERMITTED_LICENSES = {
    "CC0",
    "CC0 1.0",
    "Public Domain",
    "CC-PD-Mark",
    "CC BY",
    "CC BY 2.0",
    "CC BY 2.5",
    "CC BY 3.0",
    "CC BY 4.0",
    "CC BY-SA",
    "CC BY-SA 2.0",
    "CC BY-SA 2.5",
    "CC BY-SA 3.0",
    "CC BY-SA 4.0",
    "Free Art License",
    "FAL",
    "FAL 1.3",
    "GODL-India",
    "GODL"
}

FORBIDDEN_LICENSES = {
    "CC BY-NC",
    "CC BY-NC 2.0",
    "CC BY-NC 3.0",
    "CC BY-NC 4.0",
    "CC BY-NC-SA",
    "CC BY-NC-SA 2.0",
    "CC BY-NC-SA 3.0",
    "CC BY-NC-SA 4.0",
    "CC BY-ND",
    "CC BY-ND 2.0",
    "CC BY-ND 3.0",
    "CC BY-ND 4.0",
    "CC BY-NC-ND",
    "All Rights Reserved",
    "Copyrighted",
    "Unknown",
    "Commercial Only"
}

# 5. TRUSTED SOURCE DOMAINS (For Regional Provenance Verification)
TRUSTED_SOURCE_DOMAINS = [
    "commons.wikimedia.org",
    "wikipedia.org",
    "asi.nic.in",
    "ignca.gov.in",
    "indiaculture.gov.in",
    "sahapedia.org",
    "keralatourism.org",
    "tourism.rajasthan.gov.in",
    "assamtourism.gov.in",
    "goatourism.gov.in",
    "bihartourism.gov.in",
    "telanganatourism.gov.in",
    "sikkimtourism.gov.in",
    "unesco.org",
    "smithsonianmag.com",
    "museums.gov.in",
    "archive.org",
    "flickr.com"  # With verified CC licence filter
]

# Explicit Status Values
STATUS_APPROVED = "APPROVED"
STATUS_QUARANTINE = "QUARANTINE"
STATUS_REJECTED = "REJECTED"
STATUS_UNVERIFIED = "UNVERIFIED"
