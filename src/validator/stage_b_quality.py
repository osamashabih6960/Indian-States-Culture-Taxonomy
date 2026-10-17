"""
Stage B: Technical Image Quality Inspector.
Performs quantitative pixel analysis for:
- Blur detection via Laplacian variance
- Exposure/lighting checks (underexposed vs overexposed)
- Contrast and dynamic range
- Watermark / promotional banner detection
- Collage / multi-panel layout detection
- Screenshot / infographic / UI artifact detection
"""

from pathlib import Path
from typing import Dict, Any, Tuple
import numpy as np
from PIL import Image
from scipy.signal import convolve2d

from src.config import (
    MIN_LAPLACIAN_VARIANCE,
    MIN_BRIGHTNESS,
    MAX_BRIGHTNESS,
    MIN_CONTRAST_STD
)


def compute_laplacian_variance(gray_array: np.ndarray) -> float:
    """Compute blur metric using variance of 2D discrete Laplacian filter."""
    laplacian_kernel = np.array([
        [0,  1, 0],
        [1, -4, 1],
        [0,  1, 0]
    ], dtype=np.float32)

    # Downsample if image is very large for efficiency
    h, w = gray_array.shape
    if max(h, w) > 1024:
        scale = 1024.0 / max(h, w)
        new_w, new_h = int(w * scale), int(h * scale)
        img_pil = Image.fromarray(gray_array.astype(np.uint8)).resize((new_w, new_h), Image.Resampling.BILINEAR)
        gray_array = np.array(img_pil, dtype=np.float32)

    laplacian = convolve2d(gray_array, laplacian_kernel, mode="valid")
    return float(np.var(laplacian))


def detect_collage_patterns(gray_array: np.ndarray) -> Tuple[bool, str]:
    """
    Detect multi-panel collages by analyzing strong horizontal/vertical dividing lines
    AND verifying color/intensity distribution discontinuity across the partition.
    Prevents false positives on natural architecture like pillars, arches, and window frames.
    """
    h, w = gray_array.shape
    if h < 200 or w < 200:
        return False, "Image too small for collage analysis"

    dx = np.abs(np.diff(gray_array, axis=1))
    dy = np.abs(np.diff(gray_array, axis=0))

    col_edge_sums = np.mean(dx, axis=0)
    row_edge_sums = np.mean(dy, axis=1)

    # Check common collage grid dividing positions
    for fraction in [0.5, 0.333, 0.667, 0.25, 0.75]:
        target_col = int(w * fraction)
        window_col = col_edge_sums[max(0, target_col - 5):min(w - 1, target_col + 5)]
        if len(window_col) > 0 and np.max(window_col) > 4.5 * np.median(col_edge_sums):
            # Check if left and right panels have distinct mean brightness/variance (true collage)
            left_side = gray_array[:, :target_col]
            right_side = gray_array[:, target_col:]
            if left_side.size > 0 and right_side.size > 0:
                mean_diff = abs(float(np.mean(left_side)) - float(np.mean(right_side)))
                var_diff = abs(float(np.var(left_side)) - float(np.var(right_side)))
                # If both sides are structurally disconnected
                if mean_diff > 35.0 or var_diff > 1200.0:
                    return True, f"Vertical collage partition detected near {int(fraction*100)}% width (mean diff: {mean_diff:.1f})"

        target_row = int(h * fraction)
        window_row = row_edge_sums[max(0, target_row - 5):min(h - 1, target_row + 5)]
        if len(window_row) > 0 and np.max(window_row) > 4.5 * np.median(row_edge_sums):
            top_side = gray_array[:target_row, :]
            bot_side = gray_array[target_row:, :]
            if top_side.size > 0 and bot_side.size > 0:
                mean_diff = abs(float(np.mean(top_side)) - float(np.mean(bot_side)))
                var_diff = abs(float(np.var(top_side)) - float(np.var(bot_side)))
                if mean_diff > 35.0 or var_diff > 1200.0:
                    return True, f"Horizontal collage partition detected near {int(fraction*100)}% height (mean diff: {mean_diff:.1f})"

    return False, "No collage dividers detected"


def detect_screenshot_or_banner(img_arr: np.ndarray) -> Tuple[bool, str]:
    """
    Detect browser bars, letterboxing, heavy text banners, or screenshot UI elements.
    """
    h, w, c = img_arr.shape

    top_strip = img_arr[:int(h * 0.06), :, :]
    bot_strip = img_arr[int(h * 0.94):, :, :]

    for name, strip in [("Top", top_strip), ("Bottom", bot_strip)]:
        if strip.size > 0:
            std = np.std(strip)
            mean_val = np.mean(strip)
            if std < 2.0 and (mean_val < 15 or mean_val > 240):
                return True, f"{name} letterbox / solid banner detected"

    aspect_ratio = w / float(h)
    if aspect_ratio > 3.2 or aspect_ratio < 0.32:
        return True, f"Abnormal aspect ratio ({aspect_ratio:.2f}) indicative of banner/screenshot"

    return False, "Clean framing"


def validate_image_quality(file_path: Path) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Execute Stage B Quality Validation.
    Computes all metrics into metadata first, then verifies thresholds.
    """
    quality_meta: Dict[str, Any] = {
        "blur_score": 0.0,
        "mean_brightness": 0.0,
        "contrast_std": 0.0,
        "is_blurry": False,
        "is_underexposed": False,
        "is_overexposed": False,
        "is_low_contrast": False,
        "is_collage": False,
        "is_screenshot_banner": False
    }

    try:
        with Image.open(file_path) as img:
            rgb_img = img.convert("RGB")
            arr = np.array(rgb_img, dtype=np.float32)

            # Grayscale conversion
            gray = 0.2989 * arr[:, :, 0] + 0.5870 * arr[:, :, 1] + 0.1140 * arr[:, :, 2]

            # 1. Compute all metrics
            blur_score = compute_laplacian_variance(gray)
            mean_brightness = float(np.mean(gray))
            contrast_std = float(np.std(gray))

            quality_meta["blur_score"] = round(blur_score, 2)
            quality_meta["mean_brightness"] = round(mean_brightness, 2)
            quality_meta["contrast_std"] = round(contrast_std, 2)

            # Check individual quality conditions
            if blur_score < MIN_LAPLACIAN_VARIANCE:
                quality_meta["is_blurry"] = True
            if mean_brightness < MIN_BRIGHTNESS:
                quality_meta["is_underexposed"] = True
            if mean_brightness > MAX_BRIGHTNESS:
                quality_meta["is_overexposed"] = True
            if contrast_std < MIN_CONTRAST_STD:
                quality_meta["is_low_contrast"] = True

            is_collage, collage_reason = detect_collage_patterns(gray)
            if is_collage:
                quality_meta["is_collage"] = True
                quality_meta["collage_reason"] = collage_reason

            is_banner, banner_reason = detect_screenshot_or_banner(arr)
            if is_banner:
                quality_meta["is_screenshot_banner"] = True
                quality_meta["banner_reason"] = banner_reason

            # Evaluate pass/fail hierarchy
            if quality_meta["is_underexposed"]:
                return (
                    False,
                    f"Image is underexposed / too dark (mean luminance: {mean_brightness:.1f} < {MIN_BRIGHTNESS})",
                    quality_meta
                )
            if quality_meta["is_overexposed"]:
                return (
                    False,
                    f"Image is severely overexposed / washed out (mean luminance: {mean_brightness:.1f} > {MAX_BRIGHTNESS})",
                    quality_meta
                )
            if quality_meta["is_low_contrast"]:
                return (
                    False,
                    f"Image has insufficient contrast (std dev: {contrast_std:.1f} < {MIN_CONTRAST_STD})",
                    quality_meta
                )
            if quality_meta["is_blurry"]:
                return (
                    False,
                    f"Image is severely blurry (Sharpness score: {blur_score:.1f} < threshold {MIN_LAPLACIAN_VARIANCE})",
                    quality_meta
                )
            if quality_meta["is_collage"]:
                return False, f"Collage detected: {collage_reason}", quality_meta
            if quality_meta["is_screenshot_banner"]:
                return False, f"Screenshot or banner detected: {banner_reason}", quality_meta

    except Exception as e:
        return False, f"Failed image quality inspection: {str(e)}", quality_meta

    return True, "PASSED", quality_meta
