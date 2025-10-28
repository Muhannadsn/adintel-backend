from __future__ import annotations

import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Callable, Dict, Iterable, List, Optional, Sequence, Tuple

from .context import AdContext, BrandMatch


@dataclass(frozen=True)
class BrandRecord:
    """Metadata for a known merchant or product brand."""

    canonical_name: str
    aliases: Sequence[str]
    entity_type: str = "restaurant"  # restaurant | product | platform | marketplace | grocery | electronics | fashion | sports | home_appliances | pharmacy
    priority: int = 0  # Larger numbers win ties


BrandResolverFn = Callable[[AdContext], List[BrandMatch]]


DEFAULT_BRAND_CATALOG: Dict[str, BrandRecord] = {
    "McDonald's": BrandRecord(
        canonical_name="McDonald's",
        aliases=("mcdonald", "mcdonalds", "mc donald's", "ماكدونالدز"),
        entity_type="restaurant",
        priority=5,
    ),
    "Burger King": BrandRecord(
        canonical_name="Burger King",
        aliases=("burger king", "برغر كينغ", "برجر كينج"),
        entity_type="restaurant",
        priority=4,
    ),
    "KFC": BrandRecord(
        canonical_name="KFC",
        aliases=("kfc", "kentucky", "كنتاكي"),
        entity_type="restaurant",
        priority=5,
    ),
    "Smash Me": BrandRecord(
        canonical_name="Smash Me",
        aliases=("smash me", "smashme", "سماش مي"),
        entity_type="restaurant",
        priority=4,
    ),
    "P.F. Chang's": BrandRecord(
        canonical_name="P.F. Chang's",
        aliases=("pf changs", "p.f. chang's", "pf chang", "ب ف شانجز", "بي اف شانغز"),
        entity_type="restaurant",
        priority=4,
    ),
    "Pizza Hut": BrandRecord(
        canonical_name="Pizza Hut",
        aliases=("pizza hut", "بيتزا هت"),
        entity_type="restaurant",
        priority=4,
    ),
    "Subway": BrandRecord(
        canonical_name="Subway",
        aliases=("subway", "صب واي", "سب واي"),
        entity_type="restaurant",
        priority=4,
    ),
    "TGI Friday's": BrandRecord(
        canonical_name="TGI Friday's",
        aliases=("tgi friday", "tgi fridays", "tgi friday's", "fridays", "تي جي آي فرايدي", "تي جي آي فرايديز"),
        entity_type="restaurant",
        priority=4,
    ),
    "Applebee's": BrandRecord(
        canonical_name="Applebee's",
        aliases=("applebees", "applebee's", "applebee", "آبليبيز"),
        entity_type="restaurant",
        priority=4,
    ),
    "Chili's": BrandRecord(
        canonical_name="Chili's",
        aliases=("chilis", "chili's", "chili", "تشيليز"),
        entity_type="restaurant",
        priority=4,
    ),
    "Texas Roadhouse": BrandRecord(
        canonical_name="Texas Roadhouse",
        aliases=("texas roadhouse", "texasroadhouse", "تكساس رودهاوس"),
        entity_type="restaurant",
        priority=4,
    ),
    "Hardee's": BrandRecord(
        canonical_name="Hardee's",
        aliases=("hardees", "hardee's", "hardee", "هارديز"),
        entity_type="restaurant",
        priority=4,
    ),
    "Wendy's": BrandRecord(
        canonical_name="Wendy's",
        aliases=("wendys", "wendy's", "wendy", "ويندي", "ويندي ز"),
        entity_type="restaurant",
        priority=4,
    ),
    "Domino's Pizza": BrandRecord(
        canonical_name="Domino's Pizza",
        aliases=("dominos", "domino's", "domino pizza", "دومينوز"),
        entity_type="restaurant",
        priority=4,
    ),
    "Papa John's": BrandRecord(
        canonical_name="Papa John's",
        aliases=("papa johns", "papa john's", "papajohns", "بابا جونز"),
        entity_type="restaurant",
        priority=4,
    ),
    "Starbucks": BrandRecord(
        canonical_name="Starbucks",
        aliases=("starbucks", "ستاربكس"),
        entity_type="restaurant",
        priority=5,
    ),
    "Costa Coffee": BrandRecord(
        canonical_name="Costa Coffee",
        aliases=("costa", "costa coffee", "كوستا"),
        entity_type="restaurant",
        priority=4,
    ),
    "Dunkin'": BrandRecord(
        canonical_name="Dunkin'",
        aliases=("dunkin", "dunkin donuts", "dunkin'", "دانكن", "دنكن"),
        entity_type="restaurant",
        priority=4,
    ),
    "Baskin Robbins": BrandRecord(
        canonical_name="Baskin Robbins",
        aliases=("baskin robbins", "baskin-robbins", "baskinrobbins", "باسكن روبنز"),
        entity_type="restaurant",
        priority=4,
    ),
    "Cold Stone": BrandRecord(
        canonical_name="Cold Stone",
        aliases=("cold stone", "coldstone", "cold stone creamery", "كولد ستون"),
        entity_type="restaurant",
        priority=3,
    ),
    "Shake Shack": BrandRecord(
        canonical_name="Shake Shack",
        aliases=("shake shack", "shakeshack", "شيك شاك"),
        entity_type="restaurant",
        priority=4,
    ),
    "Five Guys": BrandRecord(
        canonical_name="Five Guys",
        aliases=("five guys", "fiveguys", "فايف جايز"),
        entity_type="restaurant",
        priority=3,
    ),
    "Popeyes": BrandRecord(
        canonical_name="Popeyes",
        aliases=("popeyes", "popeye's", "بوبايز"),
        entity_type="restaurant",
        priority=4,
    ),
    "Nando's": BrandRecord(
        canonical_name="Nando's",
        aliases=("nandos", "nando's", "nando", "ناندوز"),
        entity_type="restaurant",
        priority=4,
    ),
    "Buffalo Wild Wings": BrandRecord(
        canonical_name="Buffalo Wild Wings",
        aliases=("buffalo wild wings", "buffalo wings", "bww", "بافلو وايلد وينجز"),
        entity_type="restaurant",
        priority=3,
    ),
    "The Cheesecake Factory": BrandRecord(
        canonical_name="The Cheesecake Factory",
        aliases=("cheesecake factory", "the cheesecake factory", "تشيز كيك فاكتوري"),
        entity_type="restaurant",
        priority=4,
    ),
    "Olive Garden": BrandRecord(
        canonical_name="Olive Garden",
        aliases=("olive garden", "olivegarden", "أوليف جاردن"),
        entity_type="restaurant",
        priority=4,
    ),
    "Red Lobster": BrandRecord(
        canonical_name="Red Lobster",
        aliases=("red lobster", "redlobster", "ريد لوبستر"),
        entity_type="restaurant",
        priority=4,
    ),
    "Al Wakrah Sweets": BrandRecord(
        canonical_name="Al Wakrah Sweets",
        aliases=("al wakrah sweets", "wakrah sweets", "الوكرة حلويات", "حلويات الوكرة"),
        entity_type="restaurant",
        priority=3,
    ),
    "O2 Cafe": BrandRecord(
        canonical_name="O2 Cafe",
        aliases=("o2 cafe", "o2cafe", "o2", "او2 كافيه"),
        entity_type="restaurant",
        priority=3,
    ),
    "NutriBullet": BrandRecord(
        canonical_name="NutriBullet",
        aliases=("nutribullet", "nutri bullet"),
        entity_type="product",
        priority=3,
    ),
    "Talabat": BrandRecord(
        canonical_name="Talabat",
    aliases=("talabat", "طلبات"),
    entity_type="platform",
    priority=0,
),
"Snoonu": BrandRecord(
    canonical_name="Snoonu",
        aliases=("snoonu", "snoonu.com", "سنوونو"),
        entity_type="platform",
        priority=0,
    ),
    "Rafeeq": BrandRecord(
        canonical_name="Rafeeq",
        aliases=("rafeeq", "rafiq", "رفيق"),
        entity_type="platform",
        priority=0,
    ),
    "Keeta": BrandRecord(
        canonical_name="Keeta",
        aliases=("keeta", "كيتا"),
        entity_type="platform",
        priority=0,
    ),
    "Lulu Hypermarket": BrandRecord(
        canonical_name="Lulu Hypermarket",
        aliases=("lulu", "lulu hypermarket", "lulu qatar", "لولو", "لولو هايبر ماركت"),
        entity_type="grocery",
        priority=4,
    ),
    "Al Meera": BrandRecord(
        canonical_name="Al Meera",
        aliases=("al meera", "al-meera", "الميرة"),
        entity_type="grocery",
        priority=4,
    ),
    "Monoprix": BrandRecord(
        canonical_name="Monoprix",
        aliases=("monoprix", "monoprix qatar", "مونوبري"),
        entity_type="grocery",  # Supermarket/grocery store, NOT restaurant
        priority=4,  # Increased priority
    ),
    "Snoomart": BrandRecord(
        canonical_name="Snoomart",
        aliases=("snoomart", "snoo mart", "سنومارت"),
        entity_type="grocery",
        priority=2,
    ),
    "TalabatMart": BrandRecord(
        canonical_name="TalabatMart",
        aliases=("talabatmart", "talabat mart", "طلبات مارت"),
        entity_type="grocery",
        priority=2,
    ),
    "Samsung": BrandRecord(
        canonical_name="Samsung",
        aliases=("samsung", "سامسونج"),
        entity_type="electronics",
        priority=4,
    ),
    "Apple": BrandRecord(
        canonical_name="Apple",
        aliases=("apple", "آبل", "iphone", "آيفون"),
        entity_type="electronics",
        priority=5,
    ),
    "Xiaomi": BrandRecord(
        canonical_name="Xiaomi",
        aliases=("xiaomi", "شاومي"),
        entity_type="electronics",
        priority=3,
    ),
    "Huawei": BrandRecord(
        canonical_name="Huawei",
        aliases=("huawei", "هواوي"),
        entity_type="electronics",
        priority=3,
    ),
    "Sony": BrandRecord(
        canonical_name="Sony",
        aliases=("sony", "سوني"),
        entity_type="electronics",
        priority=3,
    ),
    "Philips": BrandRecord(
        canonical_name="Philips",
        aliases=("philips", "فيليبس"),
        entity_type="home_appliances",
        priority=3,
    ),
    "Bosch": BrandRecord(
        canonical_name="Bosch",
        aliases=("bosch", "بوش"),
        entity_type="home_appliances",
        priority=3,
    ),
    "H&M": BrandRecord(
        canonical_name="H&M",
        aliases=("h&m", "hm", "اتش اند ام"),
        entity_type="fashion",
        priority=3,
    ),
    "Zara": BrandRecord(
        canonical_name="Zara",
        aliases=("zara", "زارا"),
        entity_type="fashion",
        priority=3,
    ),
    "Shein": BrandRecord(
        canonical_name="Shein",
        aliases=("shein", "شي ان", "شيإن"),
        entity_type="fashion",
        priority=2,
    ),
    "Nike": BrandRecord(
        canonical_name="Nike",
        aliases=("nike", "نايك"),
        entity_type="sports",
        priority=4,
    ),
    "Adidas": BrandRecord(
        canonical_name="Adidas",
        aliases=("adidas", "أديداس"),
        entity_type="sports",
        priority=4,
    ),
    "Decathlon": BrandRecord(
        canonical_name="Decathlon",
        aliases=("decathlon", "ديكاتلون"),
        entity_type="sports",
        priority=3,
    ),
    "Modest Fashion Boutique": BrandRecord(
        canonical_name="Modest Fashion Boutique",
        aliases=("modest fashion boutique", "modest boutique", "عبايات مودست"),
        entity_type="fashion",
        priority=2,
    ),
    "Abaya House": BrandRecord(
        canonical_name="Abaya House",
        aliases=("abaya house", "بيت العباية", "عباية هاوس"),
        entity_type="fashion",
        priority=2,
    ),
    "Doha Pharmacy": BrandRecord(
        canonical_name="Doha Pharmacy",
        aliases=("doha pharmacy", "صيدلية الدوحة"),
        entity_type="pharmacy",
        priority=2,
    ),
    "Al Aziziya Pharmacy": BrandRecord(
        canonical_name="Al Aziziya Pharmacy",
        aliases=("al aziziya pharmacy", "aziziya pharmacy", "صيدلية العزيزية", "العزيزية"),
        entity_type="pharmacy",
        priority=3,
    ),
    "Kulud Pharmacy": BrandRecord(
        canonical_name="Kulud Pharmacy",
        aliases=("kulud pharmacy", "كلود", "صيدلية كلود"),
        entity_type="pharmacy",
        priority=2,
    ),
    "Rafeeq Care": BrandRecord(
        canonical_name="Rafeeq Care",
        aliases=("rafeeq care", "rafiq care", "رفيق كير"),
        entity_type="pharmacy",
        priority=2,
    ),
    "Boots": BrandRecord(
        canonical_name="Boots",
        aliases=("boots", "boots pharmacy"),
        entity_type="pharmacy",
        priority=3,
    ),
    "MAC Cosmetics": BrandRecord(
        canonical_name="MAC Cosmetics",
        aliases=("mac cosmetics", "mac", "ماك"),
        entity_type="beauty",
        priority=4,
    ),
    "Sephora": BrandRecord(
        canonical_name="Sephora",
        aliases=("sephora", "سيفورا"),
        entity_type="beauty",
        priority=4,
    ),
    "L'Oréal": BrandRecord(
        canonical_name="L'Oréal",
        aliases=("loreal", "l'oreal", "لوريال"),
        entity_type="beauty",
        priority=3,
    ),
    "Maybelline": BrandRecord(
        canonical_name="Maybelline",
        aliases=("maybelline", "مايبيلين"),
        entity_type="beauty",
        priority=3,
    ),
    "Olaplex": BrandRecord(
        canonical_name="Olaplex",
        aliases=("olaplex", "أولابليكس"),
        entity_type="beauty",
        priority=2,
    ),
    "Biobalance": BrandRecord(
        canonical_name="Biobalance",
        aliases=("biobalance", "bio balance", "بايو بالانس"),
        entity_type="beauty",
        priority=2,
    ),
    "Anua": BrandRecord(
        canonical_name="Anua",
        aliases=("anua", "أنوا"),
        entity_type="beauty",
        priority=2,
    ),
    "Fino": BrandRecord(
        canonical_name="Fino",
        aliases=("fino", "فينو"),
        entity_type="beauty",
        priority=1,
    ),
    "Ferns and Petals": BrandRecord(
        canonical_name="Ferns and Petals",
        aliases=("ferns and petals", "ferns & petals", "fnp"),
        entity_type="flowers",
        priority=4,
    ),
    "Floward": BrandRecord(
        canonical_name="Floward",
        aliases=("floward", "فلاورد"),
        entity_type="flowers",
        priority=3,
    ),
    "Lattafa": BrandRecord(
        canonical_name="Lattafa",
        aliases=("lattafa", "لطافة"),
        entity_type="beauty",  # Perfume brand
        priority=3,
    ),
    "Rainbow Milk": BrandRecord(
        canonical_name="Rainbow",
        aliases=("rainbow", "rainbow milk", "rainbow evaporated milk"),
        entity_type="grocery",
        priority=2,
    ),
    "PlayStation": BrandRecord(
        canonical_name="PlayStation",
        aliases=("playstation", "ps5", "ps4", "بلايستيشن"),
        entity_type="electronics",
        priority=5,
    ),
}


class BrandExtractor:
    """
    Agent 4: identifies brands or restaurants mentioned in the creative text.

    The extractor prioritizes deterministic matches against the merchant catalog,
    applies fuzzy/position-aware boosts, and optionally consults an LLM resolver
    when no confident hit is found. When the catalog cannot resolve a brand, the
    extractor surfaces high-potential unknown candidates so downstream agents or
    humans can review them.
    """

    def __init__(
        self,
        catalog: Optional[Dict[str, BrandRecord]] = None,
        stop_entity_types: Optional[Iterable[str]] = None,
        llm_resolver: Optional[BrandResolverFn] = None,
        fuzzy_threshold: float = 0.86,
        advertiser_brand_map: Optional[Dict[str, Sequence[str]]] = None,
    ) -> None:
        self.catalog = catalog or DEFAULT_BRAND_CATALOG
        self.stop_entity_types = set(stop_entity_types or {"platform"})
        self.llm_resolver = llm_resolver
        self.fuzzy_threshold = fuzzy_threshold
        self.advertiser_brand_map = advertiser_brand_map or {}
        self._alias_index: List[Tuple[re.Pattern, BrandRecord, str]] = []
        self._alias_lookup: Dict[str, BrandRecord] = {}
        self._word_boundary_chars = "A-Za-z0-9\u0600-\u06FF"
        self._english_stop_words = {
            "order",
            "delivery",
            "delivered",
            "sponsored",
            "talabat",
            "get",
            "your",
            "online",
            "today",
            "visit",
            "advertiser",
            "food",
            "delicious",
            "enjoy",
            "service",
            "official",
            "drink",
            "cuisine",
            "desi",
            "fast",
            "easy",
            "meal",
            "meals",
            "deal",
            "deals",
            "combo",
            "combos",
        }
        self._arabic_stop_words = {
            "إعلان",
            "اطلب",
            "طلبات",
            "اطلب على طلبات",
            "العاصمة",
            "على",
            "اليوم",
            "أونلاين",
            "طلب",
            "كل",
            "شيء",
            "توصل",
            "لك",
        }
        self._platform_terms = {
            record.canonical_name.lower()
            for record in self.catalog.values()
            if record.entity_type == "platform"
        }
        self._generic_marketing_terms = {
            "meal",
            "meals",
            "deal",
            "deals",
            "combo",
            "combos",
            "offer",
            "offers",
            "special",
            "promo",
            "promotion",
            "promotions",
            "limited",
            "seasonal",
            "bundle",
            "bundles",
        }
        self._generic_marketing_phrases = {
            "meal deals",
            "meal deal",
            "combo deals",
            "combo deal",
            "meal combos",
            "special offers",
            "limited offers",
            "limited time",
            "special deal",
            "special deals",
        }
        # Generic category/location terms that should NEVER be extracted as brands
        self._generic_category_terms = {
            # Countries & Cities
            "qatar", "doha", "bahrain", "kuwait", "saudi", "arabia", "uae", "dubai",
            # Generic Categories
            "restaurants", "restaurant", "groceries", "grocery", "electronics", "fashion",
            "clothing", "shoes", "accessories", "beauty", "cosmetics", "pharmacy",
            "food", "beverages", "drinks", "snacks", "sweets", "desserts",
            "pet", "pets", "supplies", "pet supplies", "pet food",  # Pet category terms
            # Product Types
            "pizza", "burger", "sandwich", "coffee", "tea", "juice", "water",
            "phone", "laptop", "tablet", "watch", "headphones", "camera",
            "dress", "shirt", "pants", "jacket", "bag", "perfume",
            # Generic Merchant Types
            "shop", "store", "market", "supermarket", "hypermarket", "mall",
            "cafe", "bakery", "butcher", "pharmacy",
            # Marketing Terms
            "sale", "offer", "discount", "free", "new", "best", "top", "hot",
            "exclusive", "premium", "luxury", "quality", "fresh", "organic",
            # Product Descriptions
            "coffee machine", "pizza menu", "burger menu", "product", "service",
            "item", "items", "products", "services", "brand", "brands",
            # Time/Days
            "today", "tomorrow", "weekend", "monday", "tuesday", "wednesday",
            "thursday", "friday", "saturday", "sunday", "weekday",
            # Misc
            "adventure awaits", "welcome", "hello", "thank you", "shop now",
            "order now", "download", "install", "subscribe", "follow",
        }
        # Brand suffix stopwords - words that commonly FOLLOW brand names in marketing text
        # Used to trim trailing CTA/marketing fluff after brand extraction
        self._brand_suffix_stop_en = {
            "online", "with", "delivery", "delivered", "in", "qatar", "fast", "minute", "minutes",
            "hour", "hours", "today", "now", "order", "buy", "shop", "offer", "offers", "deal",
            "deals", "free", "get", "your", "to", "the", "and", "skip", "doorstep", "have", "it",
            "on", "from", "at", "by", "via", "through", "using", "download", "app", "website"
        }
        self._brand_suffix_stop_ar = {
            "عروض", "توصيل", "سريع", "مجاني", "اليوم", "الآن", "اطلب", "تسوق", "اشتري",
            "مع", "الى", "إلى", "و", "في", "قطر"
        }
        self._build_alias_index()

    def _build_alias_index(self) -> None:
        flags = re.IGNORECASE
        pattern_template = r"\b{}\b"

        for record in self.catalog.values():
            for alias in record.aliases:
                escaped = re.escape(alias)
                pattern = pattern_template.format(escaped)
                regex = re.compile(pattern, flags)
                self._alias_index.append((regex, record, alias))
                self._alias_lookup[alias.lower()] = record
            self._alias_lookup[record.canonical_name.lower()] = record

    def extract(self, context: AdContext) -> List[BrandMatch]:
        text, used_sections = self._compose_text_sources(context)
        matches = self._scan_catalog(text)

        if not matches and self.llm_resolver:
            llm_matches = self.llm_resolver(context)
            matches = [m for m in llm_matches if self._allow_entity(m.entity_type)]

        matches = self._augment_with_unknown_brands(text, matches)
        matches = self._apply_advertiser_context(context, matches)
        matches = self._dedupe_and_sort(matches)

        context.brand_matches = matches
        if matches:
            primary = matches[0]
            context.brand = primary.name
            context.brand_confidence = primary.confidence
            context.brand_source = primary.source
            context.add_evidence(
                agent="BrandExtractor",
                observation=f"Primary brand: {primary.name} ({primary.source})",
                confidence=primary.confidence,
            )
            if len(matches) > 1:
                context.set_flag("multiple_brands_detected", True)
        else:
            context.brand = None
            context.brand_confidence = None
            context.brand_source = None
            context.set_flag("brand_not_found", True)

        if used_sections:
            context.set_flag("brand_vision_sections_used", True)

        return matches

    def _compose_text_sources(self, context: AdContext) -> Tuple[str, bool]:
        """
        Combine raw OCR text with structured vision sections (brand/product) so
        marketplace creatives can still surface merchant names when OCR fails.
        """
        parts: List[str] = []
        seen: set[str] = set()

        def add_part(value: Optional[str]) -> None:
            if not value:
                return
            normalized = value.strip()
            if not normalized:
                return
            key = normalized.lower()
            if key in seen:
                return
            parts.append(normalized)
            seen.add(key)

        add_part(context.raw_text)
        used_sections = False

        vision = context.vision_extraction
        if vision and getattr(vision, "sections", None):
            for key in ("brand", "product_service", "offers"):
                section_text = vision.sections.get(key)
                if section_text:
                    add_part(section_text)
                    used_sections = True

        combined_text = "\n".join(parts)
        return combined_text, used_sections

    def _scan_catalog(self, text: str) -> List[BrandMatch]:
        results: List[BrandMatch] = []
        lowered = text.lower()
        text_length = max(len(text), 1)

        for regex, record, alias in self._alias_index:
            if not self._allow_entity(record.entity_type):
                continue

            match_iter = list(regex.finditer(text))
            if match_iter:
                occurrences = len(match_iter)
                start = match_iter[0].start()
                base_conf = 0.92 if alias.lower() == record.canonical_name.lower() else 0.87
                confidence = self._boost_confidence(base_conf, start, text_length, occurrences)
                results.append(
                    BrandMatch(
                        name=record.canonical_name,
                        confidence=confidence,
                        alias=alias,
                        source="catalog",
                        entity_type=record.entity_type,
                    )
                )
                continue

            safe_hits = self._safe_substring_matches(lowered, alias.lower())
            if safe_hits:
                start = safe_hits[0]
                occurrences = len(safe_hits)
                confidence = self._boost_confidence(0.85, start, text_length, occurrences)
                results.append(
                    BrandMatch(
                        name=record.canonical_name,
                        confidence=confidence,
                        alias=alias,
                        source="catalog_substring",
                        entity_type=record.entity_type,
                    )
                )
                continue

            fuzzy_hit = self._fuzzy_match(lowered, alias.lower())
            if fuzzy_hit:
                start, score, candidate = fuzzy_hit
                base_conf = 0.75 + max(0.0, score - self.fuzzy_threshold) * 0.25
                confidence = self._boost_confidence(base_conf, start, text_length, 1)
                results.append(
                    BrandMatch(
                        name=record.canonical_name,
                        confidence=confidence,
                        alias=candidate,
                        source="catalog_fuzzy",
                        entity_type=record.entity_type,
                    )
                )

        return results

    def _dedupe_and_sort(self, matches: List[BrandMatch]) -> List[BrandMatch]:
        unique: Dict[str, BrandMatch] = {}
        for match in matches:
            existing = unique.get(match.name)
            if not existing or match.confidence > existing.confidence:
                unique[match.name] = match

        def sort_key(m: BrandMatch) -> Tuple[int, int, float, int]:
            advertiser_score = 1 if m.is_advertiser_match else 0
            record = self.catalog.get(m.name)
            if record:
                priority = record.priority
            else:
                priority = 1 if m.entity_type != "unknown" else -1
            return (advertiser_score, priority, m.confidence, len(m.name))

        sorted_matches = sorted(unique.values(), key=sort_key, reverse=True)
        return sorted_matches

    def _allow_entity(self, entity_type: str) -> bool:
        return entity_type not in self.stop_entity_types

    def _boost_confidence(self, base: float, start: int, text_length: int, occurrences: int) -> float:
        boost = 0.0
        if text_length > 0:
            position_ratio = start / text_length
            if position_ratio <= 0.2:
                boost += 0.05
            elif position_ratio <= 0.4:
                boost += 0.03

        if occurrences > 1:
            boost += min(0.05, 0.02 * (occurrences - 1))

        boosted = min(0.99, base + boost)
        return round(boosted, 3)

    def _safe_substring_matches(self, text_lower: str, alias_lower: str) -> List[int]:
        if len(alias_lower) < 3:
            return []
        boundary = self._word_boundary_chars
        pattern = re.compile(
            rf"(?<![{boundary}]){re.escape(alias_lower)}(?![{boundary}])"
        )
        return [m.start() for m in pattern.finditer(text_lower)]

    def _fuzzy_match(self, text_lower: str, alias_lower: str) -> Optional[Tuple[int, float, str]]:
        alias_words = alias_lower.split()
        if not alias_words:
            return None

        tokens = re.findall(r"\w+", text_lower)
        window = len(alias_words)
        if window == 0 or not tokens or len(tokens) < window:
            return None

        for i in range(len(tokens) - window + 1):
            candidate_words = tokens[i : i + window]
            candidate = " ".join(candidate_words)
            score = SequenceMatcher(None, alias_lower, candidate).ratio()
            if score >= self.fuzzy_threshold:
                candidate_norm = " ".join(candidate_words)
                pattern = re.compile(r"\b" + re.escape(candidate_norm) + r"\b")
                match = pattern.search(text_lower)
                start = match.start() if match else text_lower.find(candidate_words[0])
                return start, score, candidate_norm

        return None

    def _apply_advertiser_context(self, context: AdContext, matches: List[BrandMatch]) -> List[BrandMatch]:
        expected = self._resolve_expected_brands(context)
        if not expected:
            return matches

        expected_lower = {name.lower() for name in expected}
        matched = False
        high_conflicting: List[BrandMatch] = []

        for match in matches:
            canonical_name, record = self._canonicalize_name(match.name)
            match.name = canonical_name
            if record and match.entity_type == "unknown":
                match.entity_type = record.entity_type

            if canonical_name.lower() in expected_lower:
                match.is_advertiser_match = True
                match.confidence = min(0.99, match.confidence + 0.12)
                matched = True
            elif match.confidence >= 0.8:
                high_conflicting.append(match)

        if not matched:
            fallback_name = expected[0]
            fallback_name, record = self._canonicalize_name(fallback_name)
            entity_type = record.entity_type if record else "unknown"
            fallback_confidence = 0.82 if record else 0.75
            if high_conflicting:
                context.set_flag("brand_conflict_with_advertiser", True)
                context.add_evidence(
                    agent="BrandExtractor",
                    observation=(
                        "Advertiser brand missing from text; detected other brands: "
                        + ", ".join(sorted({m.name for m in high_conflicting}))
                    ),
                    confidence=max(m.confidence for m in high_conflicting),
                )
            matches.append(
                BrandMatch(
                    name=fallback_name,
                    confidence=fallback_confidence,
                    alias=fallback_name,
                    source="advertiser_hint",
                    entity_type=entity_type,
                    is_advertiser_match=True,
                )
            )
            context.set_flag("brand_inferred_from_advertiser", True)
            context.advertiser_brand_hint = fallback_name
            context.add_evidence(
                agent="BrandExtractor",
                observation=f"Inferred brand from advertiser metadata: {fallback_name}",
                confidence=fallback_confidence,
            )
        else:
            if high_conflicting:
                context.set_flag("brand_conflict_with_advertiser", True)
                context.add_evidence(
                    agent="BrandExtractor",
                    observation=(
                        "Detected additional brands not matching advertiser identity: "
                        + ", ".join(sorted({m.name for m in high_conflicting}))
                    ),
                    confidence=max(m.confidence for m in high_conflicting),
                )

        return matches

    def _resolve_expected_brands(self, context: AdContext) -> List[str]:
        expected: List[str] = []
        if context.advertiser_id:
            mapping = self.advertiser_brand_map.get(context.advertiser_id)
            if mapping:
                if isinstance(mapping, str):
                    expected.append(mapping)
                else:
                    expected.extend(mapping)
        if context.advertiser_brand_hint:
            expected.append(context.advertiser_brand_hint)
        # Deduplicate while preserving order
        seen = set()
        normalized: List[str] = []
        for name in expected:
            if not name:
                continue
            canonical, _ = self._canonicalize_name(name)
            if canonical.lower() in seen:
                continue
            seen.add(canonical.lower())
            normalized.append(canonical)
        return normalized

    def _canonicalize_name(self, name: str) -> Tuple[str, Optional[BrandRecord]]:
        if not name:
            return "", None
        record = self.catalog.get(name)
        if record:
            return record.canonical_name, record
        lookup = self._alias_lookup.get(name.lower())
        if lookup:
            return lookup.canonical_name, lookup
        return name, None

    def _trim_brand_suffix(self, s: str, max_tokens: int = 5) -> str:
        """
        Trim captured merchant candidates at stopwords and cap tokens.
        Preserves apostrophes/hyphens; returns TitleCase.

        Example: "DE'LONGHI ONLINE WITH ONE HOUR DELIVERY" -> "De'Longhi"
        """
        # Normalize whitespace and strip trailing delimiters
        s = re.sub(r"\s+", " ", s.strip(" -–|"))

        # Choose stopword set based on script presence
        has_ar = bool(re.search(r"[\u0600-\u06FF]", s))
        stop = self._brand_suffix_stop_ar if has_ar else self._brand_suffix_stop_en

        toks = s.split()
        out = []
        for tok in toks:
            # Normalize for stopword comparison
            norm_en = re.sub(r"[^\w'-]+", "", tok).lower()
            norm_ar = norm_en

            # Stop at suffix stopword
            if norm_en in stop or norm_ar in stop:
                break

            # Also stop at generic category/marketing terms
            if (
                norm_en in self._generic_category_terms
                or norm_en in self._generic_marketing_terms
                or norm_en in self._english_stop_words
            ):
                break

            out.append(tok)
            if len(out) >= max_tokens:
                break

        if not out:
            return ""

        # Smart TitleCase preserving apostrophes/hyphens
        def smart_cap(w: str) -> str:
            if len(w) <= 2:
                return w.upper() if w.isupper() else w
            parts = w.split("'")
            parts = [p.capitalize() if p else p for p in parts]
            w = "'".join(parts)
            if '-' in w:
                w = "-".join(p.capitalize() if p else p for p in w.split("-"))
            return w

        return " ".join(smart_cap(w) for w in out).strip()

    def _augment_with_unknown_brands(self, text: str, matches: List[BrandMatch]) -> List[BrandMatch]:
        if not text:
            return matches

        augmented = list(matches)
        known_lower = {m.name.lower() for m in matches}
        text_length = max(len(text), 1)

        # Heuristic 0: Semantic merchant extraction (HIGH CONFIDENCE)
        # Look for linguistic patterns like "Shop from [MERCHANT]", "Order from [MERCHANT]"
        # These patterns strongly indicate the actual merchant vs platform
        merchant_patterns = [
            r"(?:shop|order|buy|available|delivered|fast delivery|delivery)\s+(?:online\s+)?from\s+([A-Z][A-Za-z\s&'.-]+?)(?:\s*[-|]|\s*on\s|\s*in\s|$)",
            r"at\s+([A-Z][A-Za-z\s&'.-]+?)(?:\s*[-|]|\s*on\s|\s*in\s|$)",
            r"by\s+([A-Z][A-Za-z\s&'.-]+?)(?:\s*[-|]|\s*on\s|\s*in\s|$)",
        ]

        for pattern in merchant_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                merchant_name_raw = match.group(1).strip()

                # Clean up trailing punctuation
                merchant_name_raw = merchant_name_raw.rstrip('.,;!?-')

                # CRITICAL FIX 3: Trim trailing marketing/CTA text (e.g., "DE'LONGHI ONLINE WITH..." -> "De'Longhi")
                merchant_name = self._trim_brand_suffix(merchant_name_raw)

                # Skip if empty or too short
                if not merchant_name or len(merchant_name) <= 2:
                    continue

                # CRITICAL FIX 1: Skip overly long brand names (likely marketing text)
                if len(merchant_name) > 50:
                    continue

                merchant_lower = merchant_name.lower()

                # CRITICAL FIX 2: Skip single-word unknowns (likely OCR errors or articles)
                words = merchant_name.split()
                if len(words) == 1 and merchant_lower not in self.catalog:
                    continue

                # Skip if it's a platform term (Snoonu, Talabat, Rafeeq, Keeta)
                if merchant_lower in self._platform_terms:
                    continue

                # Skip if already extracted
                if merchant_lower in known_lower:
                    continue

                # Check if it's in catalog
                mapped_record = self._alias_lookup.get(merchant_lower)
                if mapped_record:
                    canonical_name = mapped_record.canonical_name
                    if canonical_name.lower() in known_lower:
                        continue
                    entity_type = mapped_record.entity_type
                else:
                    canonical_name = merchant_name
                    entity_type = "unknown"

                # High confidence - semantic patterns are very reliable
                confidence = self._boost_confidence(0.90, match.start(), text_length, 1)

                augmented.append(
                    BrandMatch(
                        name=canonical_name,
                        confidence=confidence,
                        alias=merchant_name,
                        source="semantic_merchant",
                        entity_type=entity_type,
                    )
                )
                known_lower.add(canonical_name.lower())

        # Heuristic 1: URLs like talabat.com/region/merchant-slug
        for match in re.finditer(r"talabat\.com/[A-Za-z\-]+/([a-z0-9\-]+)", text.lower()):
            slug = match.group(1)
            candidate = self._normalize_slug(slug)
            if not candidate:
                continue
            candidate_lower = candidate.lower()
            mapped_record = self._alias_lookup.get(candidate_lower)
            if mapped_record:
                canonical_name = mapped_record.canonical_name
                if canonical_name.lower() in known_lower:
                    continue
                entity_type = mapped_record.entity_type
            else:
                canonical_name = candidate
                entity_type = "unknown"
            if (
                canonical_name.lower() in known_lower
                or candidate_lower in self._platform_terms
                or candidate_lower in self._english_stop_words
            ):
                continue
            confidence = self._boost_confidence(0.72, match.start(), text_length, 1)
            augmented.append(
                BrandMatch(
                    name=canonical_name,
                    confidence=confidence,
                    alias=candidate,
                    source="heuristic_url",
                    entity_type=entity_type,
                )
            )
            known_lower.add(canonical_name.lower())

        # Heuristic 2: Title-case English phrases not already matched (max 3 words to avoid capturing menu items)
        for match in re.finditer(r"\b([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+){0,2})\b", text):
            candidate = match.group(1).strip()
            candidate_lower = candidate.lower()
            words = candidate.split()
            mapped_record = self._alias_lookup.get(candidate_lower)
            if mapped_record:
                canonical_name = mapped_record.canonical_name
                if canonical_name.lower() in known_lower:
                    continue
                entity_type = mapped_record.entity_type
            else:
                canonical_name = candidate
                entity_type = "unknown"

            # Skip generic category terms (Qatar, Restaurants, Electronics, etc.)
            if candidate_lower in self._generic_category_terms:
                continue

            # Skip if any word is a generic category term
            if any(word.lower() in self._generic_category_terms for word in words):
                continue

            # CRITICAL FIX 1: Skip overly long brand names (likely marketing text)
            if len(candidate) > 50:
                continue

            # CRITICAL FIX 2: Skip single-word unknowns (likely OCR errors or articles)
            if len(words) == 1 and candidate_lower not in {k.lower() for k in self.catalog.keys()}:
                continue

            if (
                canonical_name.lower() in known_lower
                or any(word.lower() in self._platform_terms for word in words)
                or all(word.lower() in self._english_stop_words for word in words)
                or len(candidate) <= 2
            ):
                continue
            marketing_hits = sum(1 for word in words if word.lower() in self._generic_marketing_terms)
            candidate_lower_phrase = " ".join(word.lower() for word in words)
            if candidate_lower_phrase in self._generic_marketing_phrases:
                continue
            if marketing_hits:
                total_words = len(words)
                # Skip highly generic phrases dominated by marketing vocabulary
                if marketing_hits == total_words or (total_words <= 3 and marketing_hits >= total_words - 1):
                    continue
            confidence = self._boost_confidence(0.68, match.start(), text_length, text.count(candidate))
            augmented.append(
                BrandMatch(
                    name=canonical_name,
                    confidence=confidence,
                    alias=candidate,
                    source="heuristic_titlecase",
                    entity_type=entity_type,
                )
            )
            known_lower.add(canonical_name.lower())

        # Heuristic 3: Arabic phrases (3+ letters) not equal to stop words/platforms.
        for match in re.finditer(r"([\u0600-\u06FF]{3,}(?:\s+[\u0600-\u06FF]{3,})*)", text):
            candidate = match.group(1).strip()
            candidate_lower = candidate.lower()
            if (
                candidate_lower in known_lower
                or candidate in self._arabic_stop_words
                or any(term in candidate_lower for term in self._platform_terms)
            ):
                continue
            confidence = self._boost_confidence(0.7, match.start(), text_length, 1)
            augmented.append(
                BrandMatch(
                    name=candidate,
                    confidence=confidence,
                    alias=candidate,
                    source="heuristic_arabic",
                    entity_type="unknown",
                )
            )
            known_lower.add(candidate_lower)

        return augmented

    @staticmethod
    def _normalize_slug(slug: str) -> Optional[str]:
        if not slug or slug.isdigit():
            return None
        words = [w for w in slug.replace("-", " ").split() if w]
        if not words:
            return None
        normalized_words = []
        for word in words:
            if word.isdigit():
                normalized_words.append(word)
            elif len(word) == 1:
                normalized_words.append(word.upper())
            else:
                normalized_words.append(word[0].upper() + word[1:])
        candidate = " ".join(normalized_words)
        return candidate if len(candidate) > 2 else None
