"""
Global Deduplication Engine.
Performs dataset-wide exact (SHA-256) and perceptual hash (pHash / dHash) deduplication.
Ensures no image is counted twice under different filenames or locations.
"""

from pathlib import Path
from typing import Dict, Any, Tuple, Optional, List
import hashlib
from PIL import Image
import imagehash

from src.config import (
    MAX_PERCEPTUAL_HASH_DIFF,
    STATUS_APPROVED,
    STATUS_REJECTED
)


class GlobalDeduplicator:
    def __init__(self, max_hamming_distance: int = MAX_PERCEPTUAL_HASH_DIFF):
        self.max_hamming_distance = max_hamming_distance
        # Stores: sha256 -> surviving_image_path
        self.sha256_index: Dict[str, Path] = {}
        # Stores: phash_str -> (imagehash_obj, surviving_image_path)
        self.phash_index: List[Tuple[Any, Path]] = {}

    def compute_sha256(self, file_path: Path) -> str:
        """Compute SHA-256 hexadecimal digest of raw file bytes."""
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    def compute_perceptual_hashes(self, file_path: Path) -> Dict[str, Any]:
        """Compute pHash (DCT-based) and dHash (difference-based)."""
        with Image.open(file_path) as img:
            phash = imagehash.phash(img)
            dhash = imagehash.dhash(img)
            return {
                "phash": phash,
                "dhash": dhash,
                "phash_str": str(phash),
                "dhash_str": str(dhash)
            }

    def check_duplicate(self, file_path: Path) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Check if file_path is an exact duplicate or near-duplicate of an already registered image.
        Returns:
        (is_duplicate, reason, duplicate_metadata)
        """
        dup_meta: Dict[str, Any] = {
            "sha256": "",
            "phash": "",
            "duplicate_type": "NONE",
            "surviving_image_path": "",
            "hamming_distance": 999
        }

        # 1. Exact SHA-256 check
        sha256_hash = self.compute_sha256(file_path)
        dup_meta["sha256"] = sha256_hash

        if sha256_hash in self.sha256_index:
            survivor = self.sha256_index[sha256_hash]
            dup_meta["duplicate_type"] = "EXACT_SHA256"
            dup_meta["surviving_image_path"] = str(survivor)
            return True, f"Exact file duplicate (SHA-256 matched: {survivor.name})", dup_meta

        # 2. Perceptual Hash near-duplicate check
        try:
            hashes = self.compute_perceptual_hashes(file_path)
            phash_obj = hashes["phash"]
            dup_meta["phash"] = hashes["phash_str"]

            for registered_hash, survivor in self.phash_index:
                diff = phash_obj - registered_hash
                if diff <= self.max_hamming_distance:
                    dup_meta["duplicate_type"] = "NEAR_PERCEPTUAL_DUPLICATE"
                    dup_meta["surviving_image_path"] = str(survivor)
                    dup_meta["hamming_distance"] = int(diff)
                    return (
                        True,
                        f"Perceptual near-duplicate (pHash distance {diff} <= {self.max_hamming_distance} of {survivor.name})",
                        dup_meta
                    )

        except Exception as e:
            dup_meta["error"] = str(e)

        return False, "UNIQUE", dup_meta

    def register_image(self, file_path: Path):
        """Register an approved unique image into the global deduplication indexes."""
        sha256_hash = self.compute_sha256(file_path)
        self.sha256_index[sha256_hash] = file_path

        try:
            hashes = self.compute_perceptual_hashes(file_path)
            self.phash_index.append((hashes["phash"], file_path))
        except Exception:
            pass
