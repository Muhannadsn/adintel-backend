#!/usr/bin/env python3
"""
Agent 11: Region Validator (DATA QUALITY GATEKEEPER!)

THE BOUNCER that filters out wrong-region ads:
- Chinese ads → REJECTED
- UAE ads in Qatar data → FLAG & REROUTE
- Saudi ads in Qatar data → FLAG & REROUTE
- Wrong phone formats → DETECTED
- Wrong currency → DETECTED

Multi-signal validation (ordered by priority):
1. Non-Arabic scripts (Chinese, Korean, etc.) → INSTANT REJECTION
2. Wrong-region cities (Dubai, Cairo, Riyadh, etc.) → INSTANT REJECTION
3. Domain/URL patterns (.qa, .ae, .com.sa, talabat.ae) → 8.0x weight
4. Phone number patterns (Qatar: +974, UAE: +971, Saudi: +966) → 5.0x weight
5. Currency mentions (QAR, AED, SAR, KWD, CNY, ¥) → 3.0x weight
6. Region-specific keywords (Doha, Dubai, Riyadh) → 2.0x weight

ENHANCED:
- Arabic OCR enabled for text extraction
- 100+ cities tracked (UAE, Saudi, Egypt, Bahrain) in Arabic & English
- Instant rejection on city detection
"""

from __future__ import annotations

import re
from typing import Optional, List, Tuple
from .context import AdContext, RegionDecision


# GCC Phone prefixes
PHONE_PATTERNS = {
    "QA": {
        "prefix": "+974",
        "pattern": r"(?:\+974|00974|974)\s*[3456789]\d{7}",
        "keywords": ["قطر", "qatar", "doha", "الدوحة"]
    },
    "AE": {
        "prefix": "+971",
        "pattern": r"(?:\+971|00971|971)\s*[2456789]\d{7,8}",
        "keywords": ["uae", "الإمارات", "dubai", "دبي", "abu dhabi", "أبوظبي"]
    },
    "SA": {
        "prefix": "+966",
        "pattern": r"(?:\+966|00966|966)\s*5\d{8}",
        "keywords": ["saudi", "السعودية", "riyadh", "الرياض", "jeddah", "جدة", "ksa"]
    },
    "KW": {
        "prefix": "+965",
        "pattern": r"(?:\+965|00965|965)\s*[2456]\d{7}",
        "keywords": ["kuwait", "الكويت"]
    },
    "BH": {
        "prefix": "+973",
        "pattern": r"(?:\+973|00973|973)\s*[3679]\d{7}",
        "keywords": ["bahrain", "البحرين", "manama", "المنامة"]
    },
    "OM": {
        "prefix": "+968",
        "pattern": r"(?:\+968|00968|968)\s*[79]\d{7}",
        "keywords": ["oman", "عمان", "muscat", "مسقط"]
    }
}

# Domain/URL patterns (Country Code TLDs and localized domains)
DOMAIN_PATTERNS = {
    "QA": [".qa", "qatar", "/qa/", "/qa-", "-qa"],
    "AE": [".ae", "/ae/", "/ae-", "-ae", "/uae/", "/emirates/"],
    "SA": [".sa", ".com.sa", "/sa/", "/sa-", "-sa", "/ksa/", "/saudi/"],
    "KW": [".kw", "/kw/", "/kw-", "-kw", "/kuwait/"],
    "BH": [".bh", "/bh/", "/bh-", "-bh", "/bahrain/"],
    "OM": [".om", "/om/", "/om-", "-om", "/oman/"],
    "EG": [".eg", ".com.eg", "/eg/", "-eg", "/egypt/", "/cairo/"],
}

# Currency patterns
CURRENCY_PATTERNS = {
    "QA": ["qar", "ق.ر", "ریال قطری", "riyal"],
    "AE": ["aed", "د.إ", "dirham", "درهم"],
    "SA": ["sar", "ر.س", "riyal", "ریال سعودی"],
    "KW": ["kwd", "د.ك", "dinar", "دينار"],
    "BH": ["bhd", "د.ب", "dinar"],
    "OM": ["omr", "ر.ع", "riyal"],
    "CN": ["cny", "¥", "yuan", "rmb", "人民币"],
    "IN": ["inr", "₹", "rupee"],
    "PK": ["pkr", "₨", "rupee"]
}

# Non-Arabic scripts (instant rejection for Gulf regions)
NON_ARABIC_SCRIPTS = {
    "chinese": r"[\u4e00-\u9fff]",  # Chinese characters
    "korean": r"[\uac00-\ud7af]",   # Korean Hangul
    "japanese": r"[\u3040-\u309f\u30a0-\u30ff]",  # Japanese Hiragana/Katakana
    "cyrillic": r"[\u0400-\u04ff]",  # Russian/Cyrillic
    "thai": r"[\u0e00-\u0e7f]",      # Thai
    "hindi": r"[\u0900-\u097f]"      # Devanagari (Hindi)
}

# Wrong-region cities (instant rejection if detected in Qatar ads)
REJECTION_CITIES = {
    "UAE": [
        # Major Emirates cities (English)
        "dubai", "abu dhabi", "sharjah", "ajman", "ras al khaimah", "fujairah",
        "umm al quwain", "al ain", "khor fakkan",
        # Arabic names
        "دبي", "أبوظبي", "أبو ظبي", "الشارقة", "عجمان", "رأس الخيمة",
        "الفجيرة", "أم القيوين", "العين", "خورفكان"
    ],
    "SA": [
        # Major Saudi cities (English)
        "riyadh", "jeddah", "mecca", "medina", "dammam", "khobar", "dhahran",
        "taif", "tabuk", "buraidah", "khamis mushait", "hail", "najran",
        "jazan", "yanbu", "al kharj", "abha", "unaizah", "qatif",
        # Arabic names
        "الرياض", "جدة", "جده", "مكة", "مكه", "المدينة", "المدينه المنورة",
        "الدمام", "الخبر", "الظهران", "الطائف", "تبوك", "بريدة", "بريده",
        "خميس مشيط", "حائل", "نجران", "جازان", "جيزان", "ينبع", "الخرج",
        "أبها", "عنيزة", "القطيف"
    ],
    "EG": [
        # Major Egyptian cities (English)
        "cairo", "alexandria", "giza", "shubra el kheima", "port said",
        "suez", "luxor", "aswan", "mansoura", "tanta", "asyut", "ismailia",
        "faiyum", "zagazig", "damietta", "assiut", "minya", "damanhur",
        "beni suef", "qena", "sohag", "hurghada", "6th of october",
        "shibin el kom", "banha", "kafr el sheikh", "arish", "mallawi",
        # Arabic names
        "القاهرة", "القاهره", "الإسكندرية", "الاسكندرية", "الجيزة", "الجيزه",
        "شبرا الخيمة", "بورسعيد", "السويس", "الأقصر", "الاقصر", "أسوان", "اسوان",
        "المنصورة", "المنصوره", "طنطا", "أسيوط", "اسيوط", "الإسماعيلية", "الاسماعيلية",
        "الفيوم", "الزقازيق", "دمياط", "المنيا", "دمنهور", "بني سويف",
        "قنا", "سوهاج", "الغردقة", "الغرقة", "6 أكتوبر", "شبين الكوم",
        "بنها", "كفر الشيخ", "العريش", "ملوي"
    ],
    "BH": [
        # Major Bahraini cities (English)
        "manama", "muharraq", "riffa", "hamad town", "isa town", "sitra",
        "budaiya", "jidhafs", "al hidd", "sanabis",
        # Arabic names
        "المنامة", "المنامه", "المحرق", "المحرّق", "الرفاع", "الرفاعة",
        "مدينة حمد", "مدينة عيسى", "سترة", "البدية", "جدحفص", "الحد", "سنابس"
    ]
}


class RegionValidator:
    """
    Agent 11: Region Validator - THE DATA QUALITY GATEKEEPER

    Validates ad region using:
    - Phone number analysis
    - Currency detection
    - Language/script detection
    - Region-specific keywords

    Flags mismatches and prevents wrong-region data contamination!
    """

    def __init__(self, expected_region: str = "QA"):
        self.expected_region = expected_region.upper()

    def validate(self, context: AdContext) -> RegionDecision:
        """
        Validate ad region and detect mismatches.

        Returns:
            RegionDecision with detected_region, confidence, and is_valid flag
        """

        text = context.raw_text or ""
        text_lower = text.lower()

        signals = []
        mismatches = []
        detected_regions = {}

        # STEP 1: Check for non-Arabic scripts (INSTANT REJECTION for Gulf)
        script_check = self._detect_non_arabic_scripts(text)
        if script_check:
            script, count = script_check
            print(f"   🚫 NON-ARABIC SCRIPT DETECTED: {script} ({count} chars)")
            return RegionDecision(
                detected_region="INVALID",
                confidence=0.98,
                signals=[f"{script}_script_detected"],
                mismatches=[f"Non-GCC language: {script}"],
                is_valid=False
            )

        # STEP 1B: Check for wrong-region cities (INSTANT REJECTION)
        city_check = self._detect_wrong_region_cities(text_lower)
        if city_check:
            region, city = city_check
            print(f"   🚫 WRONG-REGION CITY DETECTED: {city} ({region})")
            return RegionDecision(
                detected_region=region,
                confidence=0.95,
                signals=[f"city_{region}_{city}"],
                mismatches=[f"Expected {self.expected_region}, found {region} city: {city}"],
                is_valid=False
            )

        # STEP 2: Domain/URL analysis (HIGHEST PRIORITY - most reliable signal)
        domain_matches = self._detect_domains(text_lower)
        for region, count in domain_matches.items():
            detected_regions[region] = detected_regions.get(region, 0) + (count * 8.0)  # Highest weight
            signals.append(f"domain_{region}_x{count}")

        # STEP 3: Phone number analysis
        phone_matches = self._detect_phone_numbers(text)
        for region, count in phone_matches.items():
            detected_regions[region] = detected_regions.get(region, 0) + (count * 5.0)  # High weight
            signals.append(f"phone_{region}_x{count}")

        # STEP 4: Currency detection
        currency_matches = self._detect_currencies(text_lower)
        for region, count in currency_matches.items():
            detected_regions[region] = detected_regions.get(region, 0) + (count * 3.0)  # Medium weight
            signals.append(f"currency_{region}_x{count}")

        # STEP 5: Region-specific keywords
        keyword_matches = self._detect_region_keywords(text_lower)
        for region, count in keyword_matches.items():
            detected_regions[region] = detected_regions.get(region, 0) + (count * 2.0)  # Lower weight
            signals.append(f"keyword_{region}_x{count}")

        # STEP 6: Determine final region
        if not detected_regions:
            # No region signals - assume expected region with low confidence
            print(f"   ✅ No region signals - assuming {self.expected_region} (low confidence)")
            return RegionDecision(
                detected_region=self.expected_region,
                confidence=0.40,
                signals=["no_region_signals"],
                mismatches=[],
                is_valid=True
            )

        # Get top detected region
        detected_region = max(detected_regions, key=detected_regions.get)
        score = detected_regions[detected_region]

        # Calculate confidence
        confidence = min(0.98, 0.60 + (score / 20.0))

        # Check for mismatch
        is_valid = (detected_region == self.expected_region)

        if not is_valid:
            mismatches.append(f"Expected {self.expected_region}, detected {detected_region}")
            print(f"   ⚠️  REGION MISMATCH: Expected {self.expected_region}, detected {detected_region} (score: {score:.1f})")
        else:
            print(f"   ✅ Region validated: {detected_region} (score: {score:.1f})")

        return RegionDecision(
            detected_region=detected_region,
            confidence=confidence,
            signals=signals,
            mismatches=mismatches,
            is_valid=is_valid
        )

    def _detect_non_arabic_scripts(self, text: str) -> Optional[Tuple[str, int]]:
        """
        Detect non-Arabic/English scripts (Chinese, Korean, etc.)

        Returns:
            (script_name, char_count) if found, else None
        """

        for script, pattern in NON_ARABIC_SCRIPTS.items():
            matches = re.findall(pattern, text)
            if matches and len(matches) >= 3:  # Threshold: 3+ characters
                return (script, len(matches))

        return None

    def _detect_phone_numbers(self, text: str) -> dict:
        """
        Detect phone numbers and map to regions.

        Returns:
            {region: count} dict
        """

        matches = {}

        for region, data in PHONE_PATTERNS.items():
            pattern = data["pattern"]
            found = re.findall(pattern, text)
            if found:
                matches[region] = len(found)

        return matches

    def _detect_currencies(self, text: str) -> dict:
        """
        Detect currency mentions and map to regions.

        Returns:
            {region: count} dict
        """

        matches = {}

        for region, currencies in CURRENCY_PATTERNS.items():
            count = sum(1 for curr in currencies if curr in text)
            if count > 0:
                matches[region] = count

        return matches

    def _detect_region_keywords(self, text: str) -> dict:
        """
        Detect region-specific keywords (city names, country names).

        Returns:
            {region: count} dict
        """

        matches = {}

        for region, data in PHONE_PATTERNS.items():
            keywords = data.get("keywords", [])
            count = sum(1 for kw in keywords if kw in text)
            if count > 0:
                matches[region] = count

        return matches

    def _detect_domains(self, text: str) -> dict:
        """
        Detect domain/URL patterns indicating specific regions.

        Examples:
        - talabat.qa → Qatar
        - talabat.ae → UAE
        - noon.com/sa/ → Saudi Arabia

        Returns:
            {region: count} dict
        """

        matches = {}

        for region, patterns in DOMAIN_PATTERNS.items():
            count = sum(1 for pattern in patterns if pattern in text)
            if count > 0:
                matches[region] = count

        return matches

    def _detect_wrong_region_cities(self, text: str) -> Optional[Tuple[str, str]]:
        """
        Detect cities from wrong regions (instant rejection).

        Examples:
        - "توصيل في دبي" (delivery in Dubai) → Reject (UAE)
        - "Free delivery in Cairo" → Reject (Egypt)
        - "متوفر في الرياض" (available in Riyadh) → Reject (Saudi)

        Returns:
            (region, city_name) if wrong-region city found, else None
        """

        for region, cities in REJECTION_CITIES.items():
            # Skip if this is actually the expected region
            if region == self.expected_region:
                continue

            for city in cities:
                # Check if city name appears in text
                # Use word boundaries for English cities to avoid partial matches
                if city in text:
                    # For Arabic cities, direct match is fine
                    # For English cities, ensure it's not part of another word
                    if any('\u0600' <= c <= '\u06FF' for c in city):
                        # Arabic city - direct match is reliable
                        return (region, city)
                    else:
                        # English city - check word boundaries
                        # Simple check: city should be surrounded by spaces or punctuation
                        import re
                        pattern = r'\b' + re.escape(city) + r'\b'
                        if re.search(pattern, text, re.IGNORECASE):
                            return (region, city)

        return None
