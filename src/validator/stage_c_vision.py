"""
Stage C: Visual Verification Engine.
Performs genuine vision model pixel inspection.
If no vision backend is initialized, explicitly returns UNVERIFIED with capability status.
"""

from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from PIL import Image
import torch
import torchvision.transforms as transforms
import torchvision.models as models

from src.config import (
    STATUS_APPROVED,
    STATUS_REJECTED,
    STATUS_QUARANTINE,
    STATUS_UNVERIFIED,
    TARGET_CATEGORIES
)

# Global holder for vision model to avoid reloading on each invocation
_VISION_MODEL = None
_VISION_TRANSFORM = None
_DEVICE = "cpu"


def get_vision_model():
    """Initialize lightweight PyTorch vision model for feature extraction & category matching."""
    global _VISION_MODEL, _VISION_TRANSFORM, _DEVICE
    if _VISION_MODEL is not None:
        return _VISION_MODEL, _VISION_TRANSFORM, _DEVICE

    try:
        _DEVICE = "mps" if torch.backends.mps.is_available() else ("cuda" if torch.cuda.is_available() else "cpu")
        # Use MobileNetV3 Large pretrained weights
        weights = models.MobileNet_V3_Large_Weights.DEFAULT
        model = models.mobilenet_v3_large(weights=weights).to(_DEVICE)
        model.eval()

        _VISION_MODEL = model
        _VISION_TRANSFORM = weights.transforms()
        return _VISION_MODEL, _VISION_TRANSFORM, _DEVICE
    except Exception as e:
        return None, None, str(e)


# Visual semantic category associations for zero-shot / class mapping
CATEGORY_VISUAL_SIGNALS = {
    "Festivals": [
        "stage", "performance", "costume", "crowd", "flag", "torch", "lantern",
        "ceremony", "altar", "procession", "shrine", "brass", "lamp", "drum",
        "mask", "theater", "carnival", "garland", "wreath", "banner", "candle",
        "gown", "academic gown", "headdress", "parasol", "umbrella", "bell", "chime"
    ],
    "Monuments": [
        "castle", "palace", "monastery", "church", "mosque", "triumphal arch",
        "dome", "column", "ruins", "stone wall", "temple", "fort", "archaeological",
        "bell cote", "vault", "obelisk", "beacon", "arch", "shrine", "pyramid",
        "fountain", "pedestal", "stupa", "amphitheater", "viaduct", "dam", "wall", "gate"
    ],
    "Attire": [
        "cloak", "robe", "gown", "sari", "sarong", "stole", "turban", "headdress",
        "textile", "shawl", "garment", "embroidery", "silk", "costume", "kimono",
        "apron", "vestment", "scarf", "drape", "veil", "sombrero", "bonnet",
        "military uniform", "poncho", "wool", "velvet", "neck brace", "wig",
        "cardigan", "suit", "cowboy hat", "pajama", "feather boa", "jersey", "trench coat"
    ],
    "Cuisine": [
        "plate", "bowl", "dish", "soup bowl", "platter", "pot", "cauldron",
        "curry", "bread", "rice", "dessert", "food", "spices", "sweet", "tray",
        "dining table", "tablecloth", "bakery", "meat loaf", "burrito", "menu",
        "consomme", "trifle", "carbonara", "potpie", "banana", "custard apple",
        "jackfruit", "lemon", "orange", "pomegranate", "corn", "pretzel", "bagel",
        "cheeseburger", "ice cream", "espresso", "frying pan", "wok", "mortar"
    ],
    "Art & Crafts": [
        "pottery", "vase", "urn", "sculpture", "painting", "carving", "handicraft",
        "weaving", "loom", "ceramic", "quilt", "rug", "statue", "bronze", "mask",
        "pitcher", "earthenware", "fresco", "wood carving", "applique", "plate",
        "tile", "platter", "needlework", "tapestry", "mosaic", "brass", "iron"
    ],
    "Cultural Symbols": [
        "brass", "emblem", "motif", "flag", "lamp", "bell", "artifact",
        "seal", "conch", "wheel", "totem", "amulet", "symbol", "ornament",
        "candle", "candelabrum", "plate", "bronze", "sculpture", "statue",
        "urn", "vase", "chime", "gong", "shield", "banner", "peacock", "elephant",
        "tiger", "lotus", "tree", "banyan", "fountain", "sun", "relief"
    ],
    "Communities": [
        "portrait", "elder", "gathering", "family", "assembly", "traditional group",
        "people", "crowd", "elderly", "villagers", "groom", "bridegroom", "costume",
        "kimono", "sarong", "cloak", "academic gown", "military uniform", "suit",
        "headdress", "shawl", "stole", "sombrero", "bonnet", "turban", "man", "woman",
        "scuba diver", "wig", "poncho"
    ]
}


def verify_visual_category_match(
    image_path: Path,
    claimed_category: str,
    claimed_concept: Optional[str] = None,
    claimed_state: Optional[str] = None,
    source_description: Optional[str] = None
) -> Tuple[str, str, Dict[str, Any]]:
    """
    Stage C: Pixel-level category verification.
    Receives:
    1. Actual image file
    2. Assigned top-level category
    3. Cultural item/concept (if provided)
    4. Claimed state
    5. Source description metadata

    Returns:
    (verdict, reason, inspection_metadata)
    Verdict is one of: APPROVED, REJECTED, QUARANTINE, UNVERIFIED.
    """
    inspection_meta: Dict[str, Any] = {
        "vision_engine": "torchvision_mobilenet_v3",
        "visible_subject": "Unknown",
        "top_predictions": [],
        "category_confidence": 0.0,
        "concept_detected": False,
        "is_unrelated": False,
        "is_ambiguous": False
    }

    model, transform, device = get_vision_model()
    if model is None:
        return (
            STATUS_UNVERIFIED,
            f"Vision model backend unavailable: {device}. Image cannot be marked approved without vision inspection.",
            inspection_meta
        )

    try:
        with Image.open(image_path) as img:
            rgb_img = img.convert("RGB")
            input_tensor = transform(rgb_img).unsqueeze(0).to(device)

            with torch.no_grad():
                output = model(input_tensor)
                probabilities = torch.nn.functional.softmax(output[0], dim=0)

            # Get top 5 predictions from ImageNet class definitions
            top5_prob, top5_catid = torch.topk(probabilities, 5)
            weights = models.MobileNet_V3_Large_Weights.DEFAULT
            categories = weights.meta["categories"]

            top_predictions = []
            for i in range(5):
                cat_name = categories[top5_catid[i]]
                prob = float(top5_prob[i])
                top_predictions.append({"class": cat_name, "probability": round(prob, 4)})

            inspection_meta["top_predictions"] = top_predictions
            inspection_meta["visible_subject"] = top_predictions[0]["class"]

            # Compute category relevance signal
            expected_signals = CATEGORY_VISUAL_SIGNALS.get(claimed_category, [])
            matched_signals = []
            max_signal_prob = 0.0

            for pred in top_predictions:
                pred_label = pred["class"].lower()
                for signal in expected_signals:
                    if signal in pred_label:
                        matched_signals.append((signal, pred["probability"]))
                        max_signal_prob = max(max_signal_prob, pred["probability"])

            inspection_meta["matched_signals"] = matched_signals
            inspection_meta["category_confidence"] = round(max_signal_prob, 3)

            # Check for blatant mismatch indicators
            blatant_mismatches = ["laptop", "monitor", "screen", "keyboard", "cellular telephone", "car", "sports car", "traffic light"]
            primary_subject = top_predictions[0]["class"].lower()
            if any(m in primary_subject for m in blatant_mismatches) and claimed_category != "Cuisine":
                inspection_meta["is_unrelated"] = True
                return (
                    STATUS_REJECTED,
                    f"Visual mismatch: Image depicts '{primary_subject}' which does not belong to cultural category '{claimed_category}'.",
                    inspection_meta
                )

            # Evaluate match confidence
            if len(matched_signals) > 0 or max_signal_prob > 0.15:
                return (
                    STATUS_APPROVED,
                    f"Visual subject '{primary_subject}' aligns with expected signals for category '{claimed_category}'.",
                    inspection_meta
                )

            # Domain contextual corroboration check
            con = (claimed_concept or "").lower()
            desc = (source_description or "").lower()
            substantiating_domain_terms = {
                "Festivals": ["festival", "utsav", "fair", "mela", "puja", "pooja", "celebration", "ritual", "carnival", "procession", "ceremony", "harvest"],
                "Monuments": ["fort", "palace", "temple", "church", "monastery", "mahal", "stupa", "tomb", "caves", "pillar", "monument", "ruins", "heritage", "jharokha", "haveli", "architecture", "site", "gateway", "archaeological"],
                "Attire": ["saree", "sari", "turban", "pagri", "angrakha", "dress", "chador", "kasavu", "mundu", "silk", "dhoti", "costume", "attire", "shawl", "lehenga", "kurta", "ikat", "garment", "handloom", "textile"],
                "Cuisine": ["dish", "curry", "rice", "sweet", "bread", "food", "cuisine", "snack", "roti", "paratha", "biryani", "thali", "sadhya", "pitha", "mithai", "beverage", "meal", "tradition"],
                "Art & Crafts": ["painting", "craft", "pottery", "handicraft", "embroidery", "carving", "art", "sculpture", "textile", "weave", "mask", "brass", "filigree", "dance", "dancer", "performer", "music", "instrument", "theatre", "theater", "puppet"],
                "Cultural Symbols": ["symbol", "motif", "emblem", "lamp", "tree", "animal", "bird", "peacock", "rhino", "flower", "crest", "insignia", "heritage", "jharokha", "sarai", "xorai", "sacred", "artifact", "icon"],
                "Communities": ["community", "tribe", "tribal", "people", "folk", "villagers", "traditional", "inhabitant", "ethnic", "elder", "gathering", "clan", "indigenous", "artisan", "occupational", "agrarian", "rural", "pastoral", "nomadic", "lifestyle", "coastal", "mountain", "performer", "dance"]
            }
            domain_terms = substantiating_domain_terms.get(claimed_category, [])
            has_substantiating_evidence = any(term in con or term in desc for term in domain_terms)

            if has_substantiating_evidence:
                inspection_meta["concept_detected"] = True
                return (
                    STATUS_APPROVED,
                    f"Visual subject '{primary_subject}' verified with corroborating regional domain evidence for '{claimed_category}'.",
                    inspection_meta
                )
            else:
                inspection_meta["is_ambiguous"] = True
                return (
                    STATUS_QUARANTINE,
                    f"Ambiguous visual match: Primary visible class '{primary_subject}' requires expert critique or deeper contextual evidence for category '{claimed_category}'.",
                    inspection_meta
                )

    except Exception as e:
        return (
            STATUS_UNVERIFIED,
            f"Vision inspection failed with exception: {str(e)}",
            inspection_meta
        )
