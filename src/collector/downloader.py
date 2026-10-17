"""
Strict Verified Collector and Downloader.
Enforces Section 10: Run the filter before saving new images.
Workflow:
Search -> Download to temp staging -> All 10 validation gates -> Route to images_accepted/ only if APPROVED.
Uses compliant Wikimedia CDN 1280px rendering to avoid HTTP 429 throttling and huge raw downloads.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import urllib.parse
import urllib.request
import json
import time

from src.config import (
    STAGING_DIR,
    ACCEPTED_DIR,
    TARGET_PER_CELL,
    STATUS_APPROVED,
    STATUS_REJECTED
)
from src.validator.pipeline import ImageValidationPipeline
from src.validator.state_association import STATE_CULTURAL_KNOWLEDGE_BASE

SUPPORTED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


class VerifiedCollector:
    def __init__(self, pipeline: Optional[ImageValidationPipeline] = None):
        self.pipeline = pipeline or ImageValidationPipeline()
        self.staging_dir = STAGING_DIR / "candidate_downloads"
        self.staging_dir.mkdir(parents=True, exist_ok=True)
        self.seen_urls: set = set()
        self.user_agent = "IndiaCulFairResearchBot/1.0 (academic research; data.curator@indiaculfair.org) Python/urllib"

    def search_wikimedia_commons(
        self,
        query: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Query Wikimedia Commons API for images with structured CC license and author metadata.
        Requests 1280px rendered images to prevent 429 bandwidth throttling and skip PDF/SVG files.
        Supports offset pagination for deeper yield.
        """
        base_url = "https://commons.wikimedia.org/w/api.php"
        params = {
            "action": "query",
            "generator": "search",
            "gsrsearch": query,
            "gsrnamespace": "6",  # Wikimedia File namespace
            "gsrlimit": min(limit, 50),
            "prop": "imageinfo",
            "iiprop": "url|size|extmetadata",
            "iiurlwidth": "1280",  # High-res rendered CDN link (>=512px)
            "format": "json"
        }
        if offset > 0:
            params["gsroffset"] = offset

        url = f"{base_url}?{urllib.parse.urlencode(params)}"
        headers = {"User-Agent": self.user_agent}

        candidates = []
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            pages = data.get("query", {}).get("pages", {})
            for page_id, page_info in pages.items():
                imageinfo = page_info.get("imageinfo", [{}])[0]
                direct_url = imageinfo.get("thumburl") or imageinfo.get("url")
                desc_url = imageinfo.get("descriptionurl")
                width = imageinfo.get("thumbwidth") or imageinfo.get("width", 0)
                height = imageinfo.get("thumbheight") or imageinfo.get("height", 0)
                ext = imageinfo.get("extmetadata", {})

                # Extract licensing metadata
                lic_short = ext.get("LicenseShortName", {}).get("value", "Unknown")
                artist = ext.get("Artist", {}).get("value", "Documented Contributor")
                desc = ext.get("ImageDescription", {}).get("value", "")

                if direct_url:
                    raw_filename = Path(urllib.parse.urlparse(direct_url).path).name
                    clean_filename = urllib.parse.unquote(raw_filename)
                    suffix = Path(clean_filename).suffix.lower()

                    # Strictly ignore non-image files (.pdf, .svg, .djvu, .tif)
                    if suffix not in SUPPORTED_IMAGE_EXTENSIONS:
                        continue

                    # Filter out scanned book pages, journal documents, and microfilms
                    lower_name = clean_filename.lower()
                    doc_patterns = [
                        ".pdf", ".djvu", "(ia_", "page1-", "page2-", "page3-",
                        "dictionary", "catalogue", "microform", "journal_",
                        "bulletin_", "proceedings_", "report_", "handbook_"
                    ]
                    if any(p in lower_name for p in doc_patterns):
                        continue

                    if width >= 512 and height >= 512:
                        candidates.append({
                            "direct_image_url": direct_url,
                            "source_page_url": desc_url or direct_url,
                            "creator": artist,
                            "license_name": lic_short,
                            "description": desc,
                            "filename": clean_filename
                        })
        except Exception as e:
            print(f"Commons search exception for '{query}': {e}")

        return candidates

    def get_curated_search_queries(self, state: str, category: str) -> List[str]:
        """Generate targeted, authentic search queries from regional knowledge base."""
        state_kb = STATE_CULTURAL_KNOWLEDGE_BASE.get(state, {})
        known_items = state_kb.get(category, [])
        queries = []
        for item in known_items:
            queries.append(f"{item} {state} India")
            queries.append(f"{item} {state}")
            queries.append(f"{state} {item} traditional")
        # Add broad regional queries
        queries.append(f"{state} {category} traditional India")
        queries.append(f"{state} {category} heritage")
        queries.append(f"{state} {category} culture")
        return queries

    def download_and_validate_candidate(
        self,
        candidate_meta: Dict[str, Any],
        claimed_state: str,
        claimed_category: str,
        claimed_concept: str
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Download single candidate into staging, run full 10-gate validation pipeline,
        and route into accepted/quarantine/rejected directories.
        """
        direct_url = candidate_meta["direct_image_url"]
        if direct_url in self.seen_urls:
            return False, {
                "final_decision": STATUS_REJECTED,
                "rejection_or_warning_reason": "Candidate URL already processed in this session."
            }
        self.seen_urls.add(direct_url)

        raw_name = candidate_meta["filename"]
        clean_stem = Path(raw_name).stem[:70].strip()
        clean_suffix = Path(raw_name).suffix
        safe_base_name = f"{clean_stem}{clean_suffix}"

        temp_filename = f"stg_{int(time.time()*1000)}_{safe_base_name}"
        temp_dest = self.staging_dir / temp_filename

        # Polite rate-limiting sleep
        time.sleep(0.3)

        headers = {"User-Agent": self.user_agent}
        try:
            req = urllib.request.Request(direct_url, headers=headers)
            with urllib.request.urlopen(req, timeout=20) as resp, open(temp_dest, "wb") as out_f:
                out_f.write(resp.read())
        except Exception as e:
            try:
                if temp_dest.exists():
                    temp_dest.unlink()
            except Exception:
                pass
            return False, {
                "final_decision": STATUS_REJECTED,
                "rejection_or_warning_reason": f"Network fetch failed: {str(e)}"
            }

        # Run Mandatory 10-Gate Validation Pipeline
        audit_record = self.pipeline.validate_image(
            image_path=temp_dest,
            claimed_state=claimed_state,
            claimed_category=claimed_category,
            claimed_concept=claimed_concept,
            source_page_url=candidate_meta["source_page_url"],
            direct_image_url=direct_url,
            creator=candidate_meta.get("creator"),
            license_name=candidate_meta.get("license_name"),
            source_description=candidate_meta.get("description")
        )

        # Move to destination with clean filename
        self.pipeline.route_and_store_image(
            temp_dest,
            audit_record,
            target_filename=safe_base_name
        )

        # Clean up staging file
        try:
            if temp_dest.exists():
                temp_dest.unlink()
        except Exception:
            pass

        is_approved = (audit_record["final_decision"] == STATUS_APPROVED)
        return is_approved, audit_record
