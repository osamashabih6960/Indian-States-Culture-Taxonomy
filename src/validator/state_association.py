"""
State and Regional Association Validator.
Separately evaluates geographic provenance and cultural belonging for the 7 target states:
Kerala, Rajasthan, Assam, Goa, Bihar, Telangana, Sikkim.
"""

from typing import Dict, Any, Tuple, Optional, List
from urllib.parse import urlparse
from src.config import (
    TARGET_STATES,
    TRUSTED_SOURCE_DOMAINS,
    STATUS_APPROVED,
    STATUS_REJECTED,
    STATUS_QUARANTINE
)

# Canonical regional cultural database for verified state entities
# Canonical regional cultural database for verified state entities (C1.1 to C7.5)
STATE_CULTURAL_KNOWLEDGE_BASE: Dict[str, Dict[str, List[str]]] = {
    "Kerala": {
        "Festivals": [
            "onam", "vishu", "thrissur pooram", "theyyam", "boat race", "vallam kali",
            "attukal pongala", "makaravilakku", "arattu", "chembai sangeetholsavam",
            "paripally kodimoottil", "kottiyoor vyshaka", "machad mamangam", "uthralikkavu pooram",
            "champakulam boat race", "nehru trophy", "payippad boat race"
        ],
        "Monuments": [
            "bekal fort", "padmanabhaswamy temple", "mattancherry palace", "st. francis church",
            "palakkad fort", "vadakkunnathan temple", "edakkal caves", "thalassery fort",
            "kannur fort", "st angelo fort", "synagogue kochi", "krishnapuram palace",
            "napier museum", "padmanabhapuram", "vizhinjam cave", "nalukettu"
        ],
        "Attire": [
            "kasavu", "mundu", "neriyathu", "settu mundu", "kerala saree", "kara mundu",
            "traditional kerala dress", "pattupavada", "kavani", "onam kasavu",
            "balaramapuram handloom", "chendamangalam handloom", "kuthampully",
            "kathakali vesham", "theyyam costume"
        ],
        "Cuisine": [
            "sadhya", "appam", "puttu", "kadala curry", "kerala fish curry", "avial",
            "payasam", "karimeen pollichathu", "idiyappam", "pazham pori", "ela ada",
            "malabar biryani", "neyyappam", "unniyappam", "kerala parotta", "thoran",
            "ada pradhaman", "palada payasam", "sambharam", "banana chips"
        ],
        "Art & Crafts": [
            "aranmula kannadi", "coir craft", "wood carving", "kathakali masks", "mural painting",
            "bell metal", "screw pine craft", "nettur petti", "coconut shell craft",
            "kathakali dance", "mohiniyattam", "theyyam performance", "thiruvathirakali",
            "chenda drum", "idakka instrument", "koodiyattam theatre", "ottamthullal"
        ],
        "Cultural Symbols": [
            "nilavilakku", "elephant caparison", "nettipattom", "kettuvalam", "coconut tree motif",
            "valkannadi", "aalroopam", "kindi brass", "para vessel", "uruli brass",
            "great hornbill emblem", "kanikonna flower", "chinese fishing nets"
        ],
        "Communities": [
            "ezhava", "nair", "syrian christian", "mappila", "kurichiya", "kadar", "pulayar",
            "kani tribe", "mullu kurumba", "mudugar", "paniyan", "dheevara fishermen",
            "pokkali farmers"
        ]
    },
    "Rajasthan": {
        "Festivals": [
            "pushkar fair", "desert festival", "gangaur", "teej", "marwar festival",
            "bikaner camel festival", "mewar festival", "shekhawati festival", "braj mahotsav",
            "matsya festival", "kolyat fair", "nagaur fair", "shravan teej", "kolayat camel"
        ],
        "Monuments": [
            "hawa mahal", "amber fort", "mehrangarh fort", "jaisalmer fort", "city palace jaipur",
            "chittorgarh fort", "kumbhalgarh", "city palace udaipur", "umaid bhawan", "junagarh fort",
            "ranthambore fort", "nahargarh fort", "jal mahal jaipur", "chand baori", "taragarh fort",
            "dilwara temples", "patwon ki haveli", "jharokha", "chhatri memorial"
        ],
        "Attire": [
            "angrakha", "pagri", "bandhani", "lehenga choli", "odhani", "rajasthani turban",
            "safah rajasthan", "gota patti", "leheriya", "chaniya choli", "dhabla",
            "kota doria", "pattu weaving", "jodhpuri sherwani"
        ],
        "Cuisine": [
            "dal baati churma", "gatte ki sabzi", "laal maas", "ker sangri", "ghevar",
            "pyaaz kachori", "mawa kachori", "bajra roti", "papad ki sabzi", "mohan thaal",
            "kalakand alwar", "mirchi vada", "bikaneri bhujia", "masala chaas"
        ],
        "Art & Crafts": [
            "kathputli", "blue pottery", "miniature painting", "phad painting", "block printing",
            "sanganeri", "bagru print", "mojari footwear", "tarkashi craft", "meenakari",
            "thewa art", "terracotta molela", "pichwai painting", "ghoomar dance",
            "kalbelia dance", "chari dance", "bhavai folk dance", "kamaicha instrument",
            "ravanahatha", "kathputli puppetry"
        ],
        "Cultural Symbols": [
            "camel motif", "peacock motif", "jharokha", "rajasthani royal crest", "chhatri dome",
            "jaipur seal", "mandana folk art", "suraj motif", "godawan bird", "khejri tree",
            "kavad shrine"
        ],
        "Communities": [
            "rajput", "marwari", "bishnoi", "kalbelia", "bhil", "meena", "gujjar",
            "gadolia lohar", "rebari", "raika camel herders", "sahariya", "garasia",
            "thar desert villagers"
        ]
    },
    "Assam": {
        "Festivals": [
            "bohag bihu", "kati bihu", "magh bihu", "ambubachi mela", "ali aye ligang",
            "me-dam-me-phi", "jonbeel mela", "baishagu", "dehing patkai festival", "tea festival assam",
            "rongali bihu", "bhogali bihu"
        ],
        "Monuments": [
            "kamakhya temple", "rang ghar", "kareng ghar", "talatal ghar", "sivasagar",
            "agnigarh", "charaideo moidams", "hayagriva madhava temple", "sri surya pahar", "sukreswar temple",
            "naamghar prayer hall", "umananda temple"
        ],
        "Attire": [
            "mekhela chador", "muga silk", "eri silk", "pat silk", "dhoti kurta assam",
            "riha assam", "seleng chador", "gamusa attire", "dokhana boro",
            "junbiri jewelry", "gamkharu", "dholbiri"
        ],
        "Cuisine": [
            "khar", "masor tenga", "duck curry", "aloo pitika", "pitha", "kaji nemu dish",
            "ou tenga", "pani hamuk", "xaj beverage", "dhekia xaak", "til pitha", "ghila pitha",
            "narikol laru", "assam tea"
        ],
        "Art & Crafts": [
            "bamboo craft", "cane handicraft", "majuli mask", "bell metal sarthebari",
            "terracotta asharikandi", "brass craft haja", "water hyacinth craft", "shital pati",
            "wood carving assam", "traditional loom assam", "bihu dance", "sattriya classical dance",
            "bagurumba dance", "pepa instrument", "gogona", "tokari", "bhaona theatre"
        ],
        "Cultural Symbols": [
            "jaapi", "gamusa", "gamosa", "one horned rhino emblem", "sarai", "xorai",
            "pepa instrument", "dheki", "gogona", "tokari", "kopou phool orchid", "kaziranga rhino"
        ],
        "Communities": [
            "ahom", "bodo", "mishing", "karbi", "tiwa", "dimasa", "rabha", "sonowal kachari",
            "koch rajbongshi", "chutia", "tea tribe assam", "mising community",
            "majuli islanders", "sarthebari smiths"
        ]
    },
    "Goa": {
        "Festivals": [
            "goa carnival", "shigmo", "bonderam", "sao joao", "feast of st. francis xavier",
            "tripurari poornima goa", "chikal kalo", "touxeachem fest", "divanji festival",
            "konsachem festival"
        ],
        "Monuments": [
            "basilica of bom jesus", "se cathedral", "aguada fort", "chapoora fort",
            "cabo de rama fort", "reis magos fort", "church of our lady of immaculate conception",
            "corjuem fort", "safa masjid goa", "mahadev temple tambdi surla", "st augustine tower",
            "fontainhas heritage", "menezes braganza house"
        ],
        "Attire": [
            "pano bhaju", "kashti", "kunbi saree", "goan traditional wear", "dhablo", "fadki",
            "goan crochet lace", "kunbi handloom"
        ],
        "Cuisine": [
            "goan fish curry", "vindaloo", "xacuti", "bebinca", "sorpotel", "balchao",
            "feni", "cafreal", "fish recheado", "poi bread", "sanna goan", "dodol",
            "cashew feni", "sol kadhi"
        ],
        "Art & Crafts": [
            "goan azulejos", "brass lamp craft", "clay pottery", "seashell craft", "crochet lace",
            "bicholim brass", "coconut husk carving", "woodcraft goa", "fugdi dance",
            "dekhnni dance", "dhalo dance", "corridinho dance", "ghumat drum", "tiatr theatre"
        ],
        "Cultural Symbols": [
            "rooster motif", "tulsi vrindavan", "cross of st. francis", "mandovi river symbol",
            "goa ghumat drum", "samai brass lamp", "flame throated bulbul", "azulejo tile motif"
        ],
        "Communities": [
            "kunbi", "gauda", "velip", "goan catholic", "saraswat", "maratha goan",
            "kharvi fishermen", "dhangar goa", "ramponkar community"
        ]
    },
    "Bihar": {
        "Festivals": [
            "chhath puja", "sama chakeva", "bihula", "sonpur cattle fair", "rajgir mahotsav",
            "shravani mela bihar", "pitrapaksha mela gaya", "karma dharma bihar",
            "makar sankranti bihar", "buddha mahotsav"
        ],
        "Monuments": [
            "mahabodhi temple", "nalanda university ruins", "vikramshila", "barabar caves",
            "rohtasgarh fort", "golghar", "ashokan pillar vaishali", "sher shah suri tomb",
            "kesaria stupa", "vishnupad temple gaya", "kumhrar palace ruins", "maner sharif"
        ],
        "Attire": [
            "bhagalpuri silk", "tussar silk saree", "dhoti kurta bihar", "maithili saree",
            "mirzai bihar", "gamchha bihar", "baun buti saree", "maithil paag"
        ],
        "Cuisine": [
            "litti chokha", "sattu paratha", "khaja", "thekua", "dal pitha", "tilkut",
            "chana ghugni", "balushahi bihar", "anarsa", "parwal ki mithai", "makhana kheer",
            "sattu sharbat"
        ],
        "Art & Crafts": [
            "madhubani painting", "mithila art", "manjusha art", "tikuli craft", "sikki grass craft",
            "sujani embroidery", "stone craft patharkatti", "bawan buti saree", "terracotta bihar",
            "kasida embroidery bihar", "chhau dance bihar", "jhijhiya dance", "jat jatin theatre",
            "bidesia theatre"
        ],
        "Cultural Symbols": [
            "bodhi tree", "ashoka pillar emblem", "madhubani fish motif", "chhath soop",
            "lotus motif mithila", "sikki grass basket", "mithila sun motif", "dharmachakra",
            "house sparrow symbol", "daura basket"
        ],
        "Communities": [
            "maithil", "bhojpuri", "magahi", "oraon", "santhal bihar", "tharu",
            "munda bihar", "kushwaha bihar", "ho tribe bihar", "mallah fishermen",
            "bhagalpur weavers"
        ]
    },
    "Telangana": {
        "Festivals": [
            "bathukamma", "bonalu", "sammakka sarakka jatara", "nagoba jatara", "medaram jatara",
            "komuravelli mallanna", "edupayala jatara", "sadar festival", "ugadi telangana"
        ],
        "Monuments": [
            "charminar", "golconda fort", "warangal fort", "ramappa temple", "thousand pillar temple",
            "chowmahalla palace", "qutb shahi tombs", "falaknuma palace", "paigah tombs",
            "medak cathedral", "bhuvanagiri fort", "alampur temples", "kakatiya gateway"
        ],
        "Attire": [
            "pochampally ikat saree", "gadwal saree", "narayanpet saree", "pancha",
            "golconda dastaar", "telangana handloom dress", "siddipet gollabhama",
            "lambada dress"
        ],
        "Cuisine": [
            "hyderabadi biryani", "sarva pindi", "sakinalu", "haleem", "pachi pulusu",
            "qubani ka meetha", "double ka meetha", "mirchi ka salan", "polelu telangana",
            "bagara baingan", "irani chai", "osmania biscuit"
        ],
        "Art & Crafts": [
            "bidriware", "dokra craft", "cheriyal scroll painting", "nirmal paintings and toys",
            "pembarthi metal craft", "silver filigree karimnagar", "pochampally tie and dye",
            "gadwal weaving", "durries warangal", "perini sivatandavam dance", "lambada dance",
            "gusadi dance", "oggu katha theatre", "dappu instrument"
        ],
        "Cultural Symbols": [
            "kakatiya thoranam", "charminar emblem", "bathukamma flower stack", "deer motif",
            "palapitta indian roller", "jammi chettu", "tangredu flower", "pembarthi kalasam"
        ],
        "Communities": [
            "lambada", "chenchu", "gond telangana", "koya", "telangana reddy", "padmashali",
            "kolam tribe", "pradhan tribe", "naikpod", "banjara community",
            "godavari fishermen"
        ]
    },
    "Sikkim": {
        "Festivals": [
            "losar", "saga dawa", "pang lhabsol", "losoong", "namsoong", "dasain sikkim",
            "tihar sikkim", "maghe sankranti sikkim", "bhumchu festival", "tendong lho rum faat"
        ],
        "Monuments": [
            "rumtek monastery", "pemayangtse monastery", "tashiding monastery", "rabdentse ruins",
            "dubdi monastery", "enchey monastery", "phodong monastery", "ralang monastery",
            "sanga choeling", "coronation throne yuksom", "norbugang yuksom"
        ],
        "Attire": [
            "bakhu", "kho", "honju", "pangden", "thokro dum", "dumvum lepcha",
            "gyadoom", "sikkimese traditional gown", "dhaka topi sikkim", "gao amulet box"
        ],
        "Cuisine": [
            "momos sikkim", "thukpa", "gundruk", "phagshapa", "kinema", "sel roti sikkim",
            "chhurpi", "sha phaley", "sinki sikkim", "chaang beverage", "chhurpi soup",
            "suja butter tea"
        ],
        "Art & Crafts": [
            "thangka painting", "choktse wooden table", "carpet weaving sikkim", "lepcha weave",
            "mask making", "wood carving sikkim", "handmade paper sikkim", "cane bamboo sikkim",
            "singhi chham snow lion dance", "yak dance sikkim", "cham mask dance",
            "damphu drum", "dungchen horn"
        ],
        "Cultural Symbols": [
            "ashtamangala", "endless knot", "dharma chakra", "mount kanchenjunga symbol",
            "prayer wheel sikkim", "snow lion emblem", "dorje vajra", "mani stone",
            "red panda emblem", "prayer flags lungta"
        ],
        "Communities": [
            "lepcha", "bhutia", "limbu", "nepali sikkimese", "newar sikkim",
            "sherpa sikkim", "rai sikkim", "tamang sikkim", "dokpa yak herders",
            "himalayan mountain villagers"
        ]
    }
}


def verify_source_domain_authority(source_url: Optional[str]) -> Tuple[bool, str]:
    """Check if the source URL belongs to an authoritative cultural or heritage institution."""
    if not source_url:
        return False, "Missing source URL"

    try:
        domain = urlparse(source_url).netloc.lower()
        for trusted in TRUSTED_SOURCE_DOMAINS:
            if trusted in domain:
                return True, f"Authoritative domain: {trusted}"
        return False, f"Non-curated domain: {domain}"
    except Exception:
        return False, "Malformed source URL"


def verify_state_association(
    claimed_state: str,
    category: str,
    concept: Optional[str] = None,
    source_url: Optional[str] = None,
    source_description: Optional[str] = None
) -> Tuple[str, str, Dict[str, Any]]:
    """
    Section 4: Separate Geographic & State Association Verification.
    Returns:
    (verdict, reason, metadata)
    """
    state_meta: Dict[str, Any] = {
        "claimed_state": claimed_state,
        "is_valid_target_state": claimed_state in TARGET_STATES,
        "is_authoritative_domain": False,
        "matched_entities": [],
        "shared_regional_notes": None
    }

    if claimed_state not in TARGET_STATES:
        return (
            STATUS_REJECTED,
            f"State '{claimed_state}' is not among the 7 designated research states (Kerala, Rajasthan, Assam, Goa, Bihar, Telangana, Sikkim).",
            state_meta
        )

    is_authoritative, auth_reason = verify_source_domain_authority(source_url)
    state_meta["is_authoritative_domain"] = is_authoritative
    state_meta["authority_note"] = auth_reason

    # Query regional knowledge base
    desc = (source_description or "").lower()
    con = (concept or "").lower()
    combined_text = f"{desc} {con}"

    state_kb = STATE_CULTURAL_KNOWLEDGE_BASE.get(claimed_state, {})
    cat_entities = state_kb.get(category, [])

    matched = []
    for entity in cat_entities:
        if entity in combined_text:
            matched.append(entity)

    state_meta["matched_entities"] = matched

    # Cross-state conflict detection
    # Ensure entity does not belong exclusively to a different state
    for other_state, other_categories in STATE_CULTURAL_KNOWLEDGE_BASE.items():
        if other_state == claimed_state:
            continue
        other_entities = other_categories.get(category, [])
        for ent in other_entities:
            # If an entity exclusive to another state is prominently named
            if ent in con and ent not in cat_entities:
                return (
                    STATUS_REJECTED,
                    f"Geographic mismatch: Concept '{con}' is strongly attributed to {other_state}, not {claimed_state}.",
                    state_meta
                )

    if len(matched) > 0 or claimed_state.lower() in desc:
        return (
            STATUS_APPROVED,
            f"Verified state association: Documented connection to {claimed_state} (Matches: {matched or claimed_state}).",
            state_meta
        )

    # If domain is authoritative and state is in text
    if is_authoritative and claimed_state.lower() in combined_text:
        return (
            STATUS_APPROVED,
            f"Verified regional provenance from authoritative source ({auth_reason}).",
            state_meta
        )

    return (
        STATUS_QUARANTINE,
        f"Unsupported state association: Cultural evidence connecting item to {claimed_state} requires secondary provenance verification.",
        state_meta
    )
