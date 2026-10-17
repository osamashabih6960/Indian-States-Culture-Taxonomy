"""
Stage A: File Integrity Validator.
Checks decodability, magic bytes, dimensions (>=512x512), and non-blank content.
"""

from pathlib import Path
from typing import Dict, Any, Tuple
import numpy as np
from PIL import Image

from src.config import (
    MIN_IMAGE_WIDTH,
    MIN_IMAGE_HEIGHT,
    ALLOWED_FORMATS,
    MAX_BLANK_PERCENTAGE
)

# Known magic bytes signatures
MAGIC_SIGNATURES = {
    b"\xFF\xD8\xFF": "JPEG",
    b"\x89PNG\r\n\x1a\n": "PNG",
    b"RIFF": "WEBP"  # Subtype checked below
}


def detect_magic_format(file_path: Path) -> str:
    """Detect image file format from raw header bytes."""
    try:
        with open(file_path, "rb") as f:
            header = f.read(16)
            if header.startswith(b"\xFF\xD8\xFF"):
                return "JPEG"
            if header.startswith(b"\x89PNG\r\n\x1a\n"):
                return "PNG"
            if header.startswith(b"RIFF") and header[8:12] == b"WEBP":
                return "WEBP"
    except Exception:
        return "UNKNOWN"
    return "UNKNOWN"


def validate_file_integrity(
    file_path: Path,
    min_width: int = MIN_IMAGE_WIDTH,
    min_height: int = MIN_IMAGE_HEIGHT
) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Execute Stage A validation:
    - File exists and has size > 0
    - Magic bytes match allowed formats
    - PIL can decode and load image data without corruption
    - Resolution meets or exceeds minimum thresholds
    - Image is not solid blank/uniform color
    """
    metadata: Dict[str, Any] = {
        "file_readable": False,
        "magic_format": "UNKNOWN",
        "detected_format": "UNKNOWN",
        "width": 0,
        "height": 0,
        "channels": 0,
        "file_size_bytes": 0,
        "is_blank": False
    }

    if not file_path.exists() or not file_path.is_file():
        return False, "File does not exist or is not a regular file", metadata

    file_size = file_path.stat().st_size
    metadata["file_size_bytes"] = file_size
    if file_size == 0:
        return False, "File is completely empty (0 bytes)", metadata

    # 1. Magic bytes check
    magic_fmt = detect_magic_format(file_path)
    metadata["magic_format"] = magic_fmt
    if magic_fmt not in ALLOWED_FORMATS:
        return False, f"Invalid or unsupported magic format: {magic_fmt}", metadata

    # 2. PIL decoding and deep loading
    try:
        with Image.open(file_path) as img:
            metadata["detected_format"] = img.format
            metadata["width"] = img.width
            metadata["height"] = img.height
            metadata["mode"] = img.mode

            # Verify integrity
            img.verify()

        # Reopen to load pixel data fully (verify() closes/invalidates the handle in PIL)
        with Image.open(file_path) as img:
            img_converted = img.convert("RGB")
            arr = np.array(img_converted)
            metadata["file_readable"] = True
            metadata["channels"] = arr.shape[2] if arr.ndim == 3 else 1

            # 3. Check format consistency
            is_format_consistent = (magic_fmt == img.format) or (magic_fmt == "JPEG" and img.format in ["JPEG", "MPO"])
            if not is_format_consistent:
                # E.g. .jpg file that is actually a PNG or WebP
                return (
                    False,
                    f"Format mismatch: Magic bytes indicate {magic_fmt} but decoder found {img.format}",
                    metadata
                )

            # 4. Dimension check
            if img.width < min_width or img.height < min_height:
                return (
                    False,
                    f"Dimensions too small: {img.width}x{img.height} (Minimum required: {min_width}x{min_height})",
                    metadata
                )

            # 5. Blank image check (uniformity / extreme low variance)
            channel_stds = np.std(arr, axis=(0, 1))
            mean_std = float(np.mean(channel_stds))
            metadata["std_variance"] = mean_std

            if mean_std < 1.0:
                metadata["is_blank"] = True
                return False, f"Image is solid or blank (standard deviation: {mean_std:.2f})", metadata

            # Check most frequent color dominance
            flat_pixels = arr.reshape(-1, 3)
            # Sample 2000 pixels for fast uniformity check
            sample_indices = np.random.choice(flat_pixels.shape[0], size=min(2000, flat_pixels.shape[0]), replace=False)
            sampled = flat_pixels[sample_indices]
            unique_rows, counts = np.unique(sampled, axis=0, return_counts=True)
            max_fraction = counts.max() / len(sample_indices)
            if max_fraction >= MAX_BLANK_PERCENTAGE:
                metadata["is_blank"] = True
                return (
                    False,
                    f"Image is over {MAX_BLANK_PERCENTAGE*100:.0f}% uniform single color (detected {max_fraction*100:.1f}%)",
                    metadata
                )

    except Exception as e:
        return False, f"Corrupted image or decode failure: {str(e)}", metadata

    return True, "PASSED", metadata
