#!/usr/bin/env python3
"""
Agent 10: Theme Analyzer (FINAL AGENT!)
Multi-category messaging theme detection across all product types.

Analyzes messaging priorities:
- Restaurants: price, speed, quality, convenience
- Electronics: price, innovation, performance, convenience
- Fashion: price, style, quality, convenience
- Sports: price, performance, quality, convenience
- Home Appliances: price, efficiency, quality, convenience
- Pharmacy: price, health, quality, convenience
- Grocery: price, freshness, variety, convenience
"""

from __future__ import annotations

from typing import Dict
from .context import AdContext, ThemeDecision


# Category-specific theme keywords (weighted)
THEME_DEFINITIONS = {
    "restaurant": {
        "price": ["discount", "خصم", "save", "cheap", "رخيص", "offer", "عرض", "sale", "تخفيض",
                  "deal", "صفقة", "%", "free", "مجاني"],
        "speed": ["fast", "سريع", "quick", "express", "30 min", "دقيقة", "instant", "فوري",
                  "now", "الآن", "asap"],
        "quality": ["fresh", "طازج", "premium", "best", "أفضل", "quality", "جودة", "finest",
                    "gourmet", "delicious", "لذيذ"],
        "convenience": ["easy", "سهل", "24/7", "delivered", "توصيل", "app", "تطبيق",
                        "simple", "بسيط", "anywhere", "في أي مكان"]
    },

    "electronics": {
        "price": ["discount", "خصم", "sale", "تخفيض", "installment", "تقسيط", "save", "توفير",
                  "offer", "عرض", "deal", "%"],
        "innovation": ["latest", "أحدث", "new", "جديد", "5G", "AI", "smart", "ذكي",
                       "cutting-edge", "innovative", "مبتكر", "advanced", "متقدم"],
        "performance": ["fast", "سريع", "powerful", "قوي", "specs", "مواصفات", "speed",
                        "performance", "أداء", "processor", "معالج", "ram", "storage"],
        "convenience": ["delivery", "توصيل", "easy setup", "تركيب سهل", "warranty", "ضمان",
                        "support", "دعم", "free shipping", "شحن مجاني"]
    },

    "fashion": {
        "price": ["sale", "تخفيض", "discount", "خصم", "clearance", "تصفية", "offer", "عرض",
                  "%", "cheap", "رخيص"],
        "style": ["trendy", "موضة", "latest", "أحدث", "collection", "مجموعة", "new", "جديد",
                  "fashion", "أناقة", "elegant", "راقي"],
        "quality": ["premium", "فاخر", "luxury", "designer", "ديزاينر", "high-quality",
                    "جودة عالية", "finest"],
        "convenience": ["free delivery", "توصيل مجاني", "easy return", "إرجاع سهل",
                        "cash on delivery", "الدفع عند الاستلام", "fast shipping"]
    },

    "sports": {
        "price": ["discount", "خصم", "sale", "offer", "عرض", "cheap", "رخيص", "%"],
        "performance": ["pro", "احترافي", "professional", "performance", "أداء", "advanced",
                        "متقدم", "athlete", "رياضي"],
        "quality": ["premium", "فاخر", "durable", "متين", "high-quality", "جودة عالية",
                    "best", "أفضل"],
        "convenience": ["delivery", "توصيل", "easy", "سهل", "free shipping", "شحن مجاني"]
    },

    "home_appliances": {
        "price": ["discount", "خصم", "installment", "تقسيط", "offer", "عرض", "sale",
                  "تخفيض", "%"],
        "efficiency": ["energy saving", "توفير الطاقة", "eco", "efficient", "كفاءة",
                       "power saving", "green", "أخضر"],
        "quality": ["durable", "متين", "warranty", "ضمان", "premium", "فاخر",
                    "high-quality", "جودة عالية", "reliable"],
        "convenience": ["delivery", "توصيل", "installation", "تركيب", "setup", "إعداد",
                        "free install", "تركيب مجاني"]
    },

    "pharmacy": {
        "price": ["discount", "خصم", "save", "توفير", "offer", "عرض", "cheap", "رخيص", "%"],
        "health": ["health", "صحة", "wellness", "عافية", "care", "رعاية", "effective",
                   "فعال", "trusted", "موثوق"],
        "quality": ["premium", "فاخر", "certified", "معتمد", "authentic", "أصلي",
                    "approved", "مصرح"],
        "convenience": ["delivery", "توصيل", "24/7", "prescription", "وصفة طبية",
                        "fast delivery", "توصيل سريع"]
    },

    "grocery": {
        "price": ["discount", "خصم", "save", "توفير", "offer", "عرض", "bulk", "بالجملة",
                  "%", "cheap", "رخيص"],
        "freshness": ["fresh", "طازج", "daily", "يومي", "new", "جديد", "quality", "جودة",
                      "organic", "عضوي"],
        "variety": ["variety", "تنوع", "wide selection", "اختيار واسع", "all brands",
                    "جميع الماركات", "everything"],
        "convenience": ["delivery", "توصيل", "quick", "سريع", "same day", "نفس اليوم",
                        "easy", "سهل", "app", "تطبيق"]
    }
}


class ThemeAnalyzer:
    """
    Agent 10: Multi-Category Theme Analyzer (FINAL AGENT!)

    Scores messaging themes based on product category.
    Returns theme scores (0.0-1.0) for each theme.
    """

    def __init__(self):
        pass

    def analyze(self, context: AdContext) -> ThemeDecision:
        """Analyze messaging themes from context"""

        text_lower = (context.raw_text or "").lower()

        # STEP 1: Infer category (same logic as Agent 9)
        category = self._infer_category(context)

        # STEP 2: Get category-specific themes
        theme_keywords = THEME_DEFINITIONS.get(category, THEME_DEFINITIONS["restaurant"])

        # STEP 3: Score each theme
        scores = {}
        for theme, keywords in theme_keywords.items():
            # Count keyword matches
            matches = sum(1 for kw in keywords if kw in text_lower)

            # Normalize to 0.0-1.0 (3+ matches = 1.0)
            score = min(1.0, matches / 3.0)
            scores[theme] = round(score, 2)

        # STEP 4: Boost based on offer
        if context.offer:
            scores = self._apply_offer_boost(scores, context.offer.offer_type)

        # STEP 5: Determine primary theme
        primary_theme = max(scores, key=scores.get) if scores else "none"

        # STEP 6: Calculate confidence
        confidence = self._calculate_confidence(scores)

        print(f"   📊 Themes: {primary_theme} ({scores[primary_theme]:.2f}) | {dict(sorted(scores.items(), key=lambda x: x[1], reverse=True)[:3])}")

        return ThemeDecision(
            messaging_themes=scores,
            primary_theme=primary_theme,
            confidence=confidence
        )

    def _infer_category(self, context: AdContext) -> str:
        """Infer product category (same as Agent 9)"""

        text_lower = (context.raw_text or "").lower()

        if context.product_type == "restaurant":
            return "restaurant"

        if context.product_type == "unknown_category":
            # Electronics
            if any(kw in text_lower for kw in ["phone", "هاتف", "laptop", "لابتوب", "tablet",
                                                 "tv", "headphones", "gaming"]):
                return "electronics"

            # Fashion
            if any(kw in text_lower for kw in ["shirt", "dress", "shoes", "abaya", "عباية",
                                                 "fashion", "clothing"]):
                return "fashion"

            # Sports
            if any(kw in text_lower for kw in ["gym", "fitness", "dumbbell", "running",
                                                 "yoga", "sports"]):
                return "sports"

            # Home Appliances
            if any(kw in text_lower for kw in ["fridge", "washing machine", "microwave",
                                                 "oven", "air conditioner"]):
                return "home_appliances"

            # Pharmacy
            if any(kw in text_lower for kw in ["pharmacy", "medicine", "vitamin",
                                                 "supplement", "health", "drug"]):
                return "pharmacy"

        # Grocery
        if context.product_type == "category_promotion" or "grocery" in text_lower:
            return "grocery"

        return "restaurant"  # Default

    def _apply_offer_boost(self, scores: Dict[str, float], offer_type: str) -> Dict[str, float]:
        """Boost price theme if discount detected"""

        if offer_type in ["percentage_discount", "fixed_discount", "bogo"]:
            # Boost price theme
            if "price" in scores:
                scores["price"] = min(1.0, scores["price"] + 0.3)

        return scores

    def _calculate_confidence(self, scores: Dict[str, float]) -> float:
        """Calculate confidence based on score distribution"""

        if not scores:
            return 0.3

        # If highest score is clear winner (>0.5 gap), high confidence
        sorted_scores = sorted(scores.values(), reverse=True)
        if len(sorted_scores) >= 2:
            gap = sorted_scores[0] - sorted_scores[1]
            if gap >= 0.5:
                return 0.95
            elif gap >= 0.3:
                return 0.85
            else:
                return 0.70
        elif len(sorted_scores) == 1:
            if sorted_scores[0] >= 0.7:
                return 0.90
            else:
                return 0.75

        return 0.70
