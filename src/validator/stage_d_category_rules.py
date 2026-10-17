"""
Stage D: Category-Specific Visual Rules.
Enforces strict research rules for each of the 7 Indian cultural categories:
C1 Festivals, C2 Monuments, C3 Attire, C4 Cuisine, C5 Art & Crafts, C6 Cultural Symbols, C7 Communities.
"""

from typing import Dict, Any, Tuple, Optional
from src.config import (
    STATUS_APPROVED,
    STATUS_REJECTED,
    STATUS_QUARANTINE,
    STATUS_UNVERIFIED
)


def evaluate_c1_festivals(
    visible_subject: str,
    concept: Optional[str],
    source_desc: Optional[str]
) -> Tuple[str, str]:
    """C1: Festivals validation."""
    desc = (source_desc or "").lower()
    subj = visible_subject.lower()
    con = (concept or "").lower()

    # Reject generic office/party gatherings
    disallowed_keywords = ["club", "disco", "cocktail party", "office meeting", "conference", "traffic jam"]
    if any(k in desc or k in subj for k in disallowed_keywords):
        return STATUS_REJECTED, "C1 Violation: Depicts generic social gathering or modern meeting, not a traditional cultural festival."

    # Festival verification signals
    festival_signals = ["festival", "utsav", "fair", "puja", "parade", "celebration", "ritual", "decorat", "carnival", "procession", "onam", "bihu", "pushkar", "teej", "chath", "bathukamma", "losar"]
    if any(k in desc or k in con for k in festival_signals):
        return STATUS_APPROVED, "C1 Passed: Documented festival event and festive celebration visual."

    return STATUS_QUARANTINE, "C1 Review: Cultural festival context requires further documentation or source verification."


def evaluate_c2_monuments(
    visible_subject: str,
    concept: Optional[str],
    source_desc: Optional[str]
) -> Tuple[str, str]:
    """C2: Monuments validation."""
    desc = (source_desc or "").lower()
    subj = visible_subject.lower()
    con = (concept or "").lower()

    # Reject modern office towers, skylines, generic highway
    modern_keywords = ["skyscraper", "glass building", "shopping mall", "highway", "modern villa", "airport terminal"]
    if any(k in desc or k in subj for k in modern_keywords):
        return STATUS_REJECTED, "C2 Violation: Depicts modern architecture/skyline rather than an eligible historic monument or heritage structure."

    heritage_signals = ["fort", "palace", "temple", "monastery", "church", "archaeological", "ruins", "tomb", "stupa", "caves", "pillar", "heritage", "monument", "minaret", "stepwell"]
    if any(k in desc or k in con or k in subj for k in heritage_signals):
        return STATUS_APPROVED, "C2 Passed: Confirmed historic monument, fort, or architectural heritage site."

    return STATUS_QUARANTINE, "C2 Review: Historic monument status and location must be verified against heritage registers."


def evaluate_c3_attire(
    visible_subject: str,
    concept: Optional[str],
    source_desc: Optional[str]
) -> Tuple[str, str]:
    """C3: Attire validation."""
    desc = (source_desc or "").lower()
    subj = visible_subject.lower()
    con = (concept or "").lower()

    # Reject modern western casual clothes or commercial fashion ads
    casual_keywords = ["t-shirt", "jeans", "hoodie", "sneakers", "swimsuit", "business suit", "fashion runway"]
    if any(k in desc or k in subj for k in casual_keywords):
        return STATUS_REJECTED, "C3 Violation: Depicts contemporary modern casual wear or commercial fashion advertisement."

    attire_signals = [
        "sari", "saree", "mundu", "kasavu", "angrakha", "pagri", "turban", "mekhela chador",
        "dupatta", "ghagra", "choli", "bakhu", "kho", "honju", "pangden", "thokro", "dumvum",
        "gyadoom", "dhaka topi", "traditional dress", "costume", "garment", "handwoven attire",
        "attire", "muga silk", "eri silk", "pat silk", "riha", "seleng", "dokhana", "pano bhaju",
        "kashti", "kunbi", "bhagalpuri silk", "tussar silk", "pochampally", "gadwal", "narayanpet",
        "pancha", "dastaar", "bandhani", "leheriya", "dhabla", "safah"
    ]
    if any(k in desc or k in con for k in attire_signals):
        return STATUS_APPROVED, "C3 Passed: Traditional regional attire clearly visible and documented."

    return STATUS_QUARANTINE, "C3 Review: Requires verification that traditional attire is sufficiently visible and distinct from generic attire."


def evaluate_c4_cuisine(
    visible_subject: str,
    concept: Optional[str],
    source_desc: Optional[str]
) -> Tuple[str, str]:
    """C4: Cuisine validation."""
    desc = (source_desc or "").lower()
    subj = visible_subject.lower()
    con = (concept or "").lower()

    # Reject non-food restaurant interiors or fast-food
    fastfood_keywords = ["burger", "pizza", "hotdog", "sandwich", "french fries", "coca cola", "pepsi"]
    if any(k in desc or k in subj for k in fastfood_keywords):
        return STATUS_REJECTED, "C4 Violation: Depicts global fast food or commercial items unrelated to regional Indian cuisine."

    cuisine_signals = [
        "cuisine", "dish", "curry", "sweet", "bread", "platter", "thali", "sadhya",
        "dal baati", "khar", "fish curry", "litti chokha", "biryani", "momos", "beverage",
        "payasam", "roti", "food", "recipe", "appam", "puttu", "avial", "karimeen",
        "idiyappam", "pazham pori", "ela ada", "neyyappam", "unniyappam", "gatte ki sabzi",
        "laal maas", "ker sangri", "ghevar", "pyaaz kachori", "masor tenga", "aloo pitika",
        "pitha", "kaji nemu", "vindaloo", "xacuti", "bebinca", "sorpotel", "feni",
        "sattu", "thekua", "dal pitha", "tilkut", "sarva pindi", "sakinalu", "haleem",
        "thukpa", "gundruk", "phagshapa", "kinema", "sel roti", "chhurpi"
    ]
    if any(k in desc or k in con or k in subj for k in cuisine_signals):
        return STATUS_APPROVED, "C4 Passed: Traditional regional cuisine or documented dish clearly depicted."

    return STATUS_QUARANTINE, "C4 Review: Dish requires culinary documentation to confirm specific regional dish identity."


def evaluate_c5_art_crafts(
    visible_subject: str,
    concept: Optional[str],
    source_desc: Optional[str]
) -> Tuple[str, str]:
    """
    C5: Art & Crafts validation.
    Fully incorporates:
    C5.1 Painting and Visual Arts
    C5.2 Handicrafts and Material Arts
    C5.3 Dance Traditions (Kathakali, Mohiniyattam, Ghoomar, Kalbelia, Bihu, Fugdi, Perini, etc.)
    C5.4 Music and Musical Instruments (Chenda, Pepa, Gogona, Ghumat, Kamaicha, etc.)
    C5.5 Theatre and Storytelling (Kathputli, Koodiyattam, Bhaona, Tiatr, Theyyam, etc.)
    """
    desc = (source_desc or "").lower()
    subj = visible_subject.lower()
    con = (concept or "").lower()

    # Reject non-cultural modern commercial entertainment
    disallowed = ["nightclub", "pop concert", "dj party", "cinema hall", "multiplex", "disco"]
    if any(k in desc or k in subj for k in disallowed):
        return STATUS_REJECTED, "C5 Violation: Depicts modern commercial entertainment rather than authentic traditional arts or crafts."

    craft_and_performance_signals = [
        # C5.1 Painting and Visual Arts
        "painting", "mural", "fresco", "madhubani", "mithila art", "thangka", "phad", "cheriyal",
        "nirmal", "scroll painting", "manjusha", "miniature painting", "pichwai", "tanjore",
        # C5.2 Handicrafts and Material Arts
        "handicraft", "craft", "pottery", "sculpture", "wood carving", "metalwork", "brass",
        "textile weaving", "embroidery", "dokra", "terracotta", "weaving", "aranmula kannadi",
        "coir craft", "blue pottery", "block printing", "sanganeri", "bagru", "meenakari",
        "thewa", "bamboo craft", "cane handicraft", "majuli mask", "bell metal", "shital pati",
        "goan azulejos", "seashell craft", "tikuli craft", "sikki grass", "sujani", "bidriware",
        "pembarthi", "silver filigree", "choktse", "carpet weaving", "stone craft", "clay pottery",
        # C5.3 Dance Traditions
        "dance", "classical dance", "folk dance", "kathakali", "mohiniyattam", "ghoomar",
        "kalbelia", "bihu dance", "fugdi", "dekhnni", "jhumur", "singhi chham", "perini",
        "chhau", "theyyam", "dandiya", "garba", "dhalo", "corridinho", "sattriya", "mask dance",
        # C5.4 Music and Musical Instruments
        "music", "musical instrument", "pepa", "gogona", "samai", "ghumat", "mridangam",
        "chenda", "kamaicha", "ravanahatha", "tokari", "dhol", "sitar", "veena", "shehnai",
        "sarangi", "damphu", "khol", "thavil", "nadaswaram", "surando",
        # C5.5 Theatre and Storytelling
        "theatre", "theater", "storytelling", "kathputli", "puppet", "puppetry", "koodiyattam",
        "bhaona", "tiatr", "bhavai", "yakshagana", "harikatha", "burrakatha", "folk theatre"
    ]
    if any(k in desc or k in con or k in subj for k in craft_and_performance_signals):
        return STATUS_APPROVED, "C5 Passed: Validated under C5 Art & Crafts (Painting, Handicrafts, Dance, Music/Instruments, or Theatre)."

    return STATUS_QUARANTINE, "C5 Review: Artwork, craft technique, or traditional performing art requires verification."


def evaluate_c6_cultural_symbols(
    visible_subject: str,
    concept: Optional[str],
    source_desc: Optional[str]
) -> Tuple[str, str]:
    """
    C6: Cultural Symbols validation.
    C6.1 Official State Symbols
    C6.2 Religious and Sacred Symbols
    C6.3 Regional Motifs
    C6.4 Cultural Objects and Artifacts
    C6.5 Heritage Icons
    """
    desc = (source_desc or "").lower()
    con = (concept or "").lower()

    symbol_signals = [
        "symbol", "motif", "emblem", "nilavilakku", "aranmula kannadi", "jaapi", "gamusa",
        "gamosa", "dharma wheel", "dharma chakra", "ashtamangala", "ashoka", "kolam", "rangoli",
        "conch", "sacred", "traditional emblem", "prayer wheel", "snow lion", "endless knot",
        "dorje", "vajra", "mani stone", "kakatiya thoranam", "palapitta", "samai", "ghumat",
        "tulsi vrindavan", "bodhi tree", "ashokan pillar", "soop", "elephant caparison",
        "nettipattom", "kettuvalam", "jharokha", "mandana", "sarai", "xorai", "pepa", "rhino",
        "hornbill", "red panda", "state bird", "state animal", "state flower", "heritage icon"
    ]
    if any(k in desc or k in con for k in symbol_signals):
        return STATUS_APPROVED, "C6 Passed: Established cultural emblem, motif, or sacred regional symbol."

    return STATUS_QUARANTINE, "C6 Review: Cultural symbolism must be substantiated by cultural references."


def evaluate_c7_communities(
    visible_subject: str,
    concept: Optional[str],
    source_desc: Optional[str]
) -> Tuple[str, str]:
    """
    C7: Communities validation.
    C7.1 Indigenous and Tribal Communities
    C7.2 Artisan and Occupational Communities
    C7.3 Rural and Agrarian Lifestyles
    C7.4 Pastoral and Nomadic Lifestyles
    C7.5 Coastal, Riverine and Mountain Communities
    """
    desc = (source_desc or "").lower()
    con = (concept or "").lower()

    if not desc and not con:
        return (
            STATUS_UNVERIFIED,
            "C7 Violation: Photograph of unidentified persons cannot be approved as community representation without explicit source documentation."
        )

    # Documented community and lifestyle signals
    community_signals = [
        "community", "tribe", "people", "folk", "villagers", "traditional group",
        "indigenous", "tribal", "artisan", "occupational", "weaver", "potter", "blacksmith",
        "agrarian", "rural", "farmer", "peasant", "pastoral", "nomadic", "lifestyle",
        "coastal", "fisherman", "riverine", "mountain community", "inhabitants",
        # Specific regional communities
        "ezhava", "nair", "mappila", "syrian christian", "kadar", "kurichiya", "pulayar", "paniyan",
        "rajput", "marwari", "bishnoi", "kalbelia", "bhil", "meena", "gujjar", "gadolia lohar", "rebari", "raika",
        "ahom", "bodo", "mishing", "karbi", "tiwa", "dimasa", "rabha", "koch rajbongshi", "tea tribe",
        "kunbi", "gauda", "velip", "goan catholic", "saraswat", "kharvi", "dhangar",
        "maithil", "bhojpuri", "magahi", "santhal", "oraon", "tharu", "munda",
        "lambada", "chenchu", "gond", "koya", "padmashali", "kolam",
        "lepcha", "bhutia", "limbu", "sherpa", "nepali sikkimese", "newar", "rai"
    ]
    if any(k in desc or k in con for k in community_signals):
        return STATUS_APPROVED, "C7 Passed: Verified contextual documentation linking image to specific cultural community or lifestyle."

    return (
        STATUS_UNVERIFIED,
        "C7 Unverified: Insufficient contextual documentation. Visual appearance alone cannot establish community membership."
    )


def validate_category_specific_rules(
    category: str,
    visible_subject: str,
    concept: Optional[str] = None,
    source_desc: Optional[str] = None
) -> Tuple[str, str]:
    """Route image to appropriate category-specific evaluator."""
    evaluators = {
        "Festivals": evaluate_c1_festivals,
        "Monuments": evaluate_c2_monuments,
        "Attire": evaluate_c3_attire,
        "Cuisine": evaluate_c4_cuisine,
        "Art & Crafts": evaluate_c5_art_crafts,
        "Cultural Symbols": evaluate_c6_cultural_symbols,
        "Communities": evaluate_c7_communities
    }

    evaluator = evaluators.get(category)
    if not evaluator:
        return STATUS_REJECTED, f"Unknown category '{category}'"

    return evaluator(visible_subject, concept, source_desc)
