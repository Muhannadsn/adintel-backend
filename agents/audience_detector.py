#!/usr/bin/env python3
"""
Agent 9: Audience Detector
Multi-category intelligence across restaurants, electronics, fashion, sports,
home appliances, pharmacy, and groceries.

Strategy:
1. Infer product category from context
2. Use category-specific audience segments
3. Signal-based detection (fast path)
4. Offer-aware intelligence
5. LLM fallback for complex cases
"""

from __future__ import annotations

import requests
import json
from typing import Optional, Dict, List
from .context import AdContext, AudienceDecision


# Category-specific audience intelligence
AUDIENCE_INTELLIGENCE = {
    "restaurant": {
        "segments": [
            "Families with Kids",
            "Young Professionals (25-34)",
            "Students (18-24)",
            "Late-night Users",
            "Health-Conscious Eaters",
            "Budget-Conscious Diners",
            "Premium Food Seekers",
            "New Customers",
            "Existing Customers",
            "General Audience"
        ],
        "signals": {
            "Families with Kids": ["family", "kids", "children", "عائلة", "أطفال", "meal deal", "combo", "عائلية"],
            "Young Professionals (25-34)": ["quick", "lunch", "office", "work", "مكتب", "عمل", "غداء"],
            "Students (18-24)": ["student", "طالب", "university", "جامعة", "budget", "cheap"],
            "Late-night Users": ["late night", "midnight", "24/7", "سهرة", "منتصف الليل", "night"],
            "Health-Conscious Eaters": ["healthy", "organic", "salad", "صحي", "عضوي", "detox", "vegan", "kale"],
            "Budget-Conscious Diners": ["cheap", "رخيص", "value", "save", "توفير", "discount"],
            "Premium Food Seekers": ["premium", "finest", "best", "أفضل", "فاخر", "gourmet"],
            "New Customers": ["first order", "new customer", "الطلب الأول", "عميل جديد", "welcome"],
            "Existing Customers": ["loyalty", "rewards", "return", "ولاء", "مكافآت", "again"]
        }
    },

    "electronics": {
        "segments": [
            "Tech Enthusiasts",
            "Gamers",
            "Professionals/Remote Workers",
            "Students",
            "Budget Shoppers",
            "Premium Tech Seekers",
            "Photography Enthusiasts",
            "Smart Home Adopters",
            "General Audience"
        ],
        "signals": {
            "Tech Enthusiasts": ["latest", "newest", "flagship", "specs", "أحدث", "مواصفات", "cutting-edge", "innovation"],
            "Gamers": ["gaming", "fps", "rgb", "rtx", "ألعاب", "قيمنق", "gamer", "playstation", "xbox"],
            "Professionals/Remote Workers": ["work from home", "productivity", "laptop", "عمل عن بعد", "إنتاجية", "professional"],
            "Students": ["student", "طالب", "university", "جامعة", "study", "دراسة"],
            "Budget Shoppers": ["affordable", "رخيص", "budget", "installment", "تقسيط", "save"],
            "Premium Tech Seekers": ["premium", "flagship", "pro", "max", "فاخر", "برو", "luxury"],
            "Photography Enthusiasts": ["camera", "كاميرا", "photo", "صورة", "megapixel", "lens"],
            "Smart Home Adopters": ["smart home", "alexa", "google home", "منزل ذكي", "iot", "automation"]
        }
    },

    "fashion": {
        "segments": [
            "Trend Followers",
            "Budget Shoppers",
            "Premium Fashion Seekers",
            "Young Adults (18-30)",
            "Professionals",
            "Modest Fashion Seekers",
            "Athleisure Enthusiasts",
            "General Audience"
        ],
        "signals": {
            "Trend Followers": ["trending", "latest fashion", "new collection", "موضة", "ترند", "أحدث", "style"],
            "Budget Shoppers": ["sale", "تخفيض", "clearance", "cheap", "رخيص", "affordable"],
            "Premium Fashion Seekers": ["luxury", "designer", "premium", "فاخر", "ديزاينر", "haute"],
            "Young Adults (18-30)": ["young", "youth", "شباب", "casual", "streetwear"],
            "Professionals": ["professional", "formal", "office", "مكتب", "business", "احترافي"],
            "Modest Fashion Seekers": ["modest", "hijab", "abaya", "عباية", "حجاب", "محتشم", "covered"],
            "Athleisure Enthusiasts": ["sportswear", "athleisure", "activewear", "رياضي", "comfortable"]
        }
    },

    "sports": {
        "segments": [
            "Fitness Enthusiasts",
            "Athletes/Serious Trainers",
            "Casual Exercisers",
            "Beginners",
            "Outdoor Adventure Seekers",
            "Budget Shoppers",
            "General Audience"
        ],
        "signals": {
            "Fitness Enthusiasts": ["fitness", "gym", "لياقة", "جيم", "workout", "تمرين", "training"],
            "Athletes/Serious Trainers": ["pro", "professional", "performance", "احترافي", "أداء", "athlete", "competition"],
            "Casual Exercisers": ["casual", "light", "beginners", "easy", "سهل", "home workout"],
            "Beginners": ["beginner", "starter", "first time", "مبتدئ", "start", "بداية"],
            "Outdoor Adventure Seekers": ["outdoor", "hiking", "camping", "adventure", "مغامرة", "nature"],
            "Budget Shoppers": ["affordable", "budget", "cheap", "رخيص", "value"]
        }
    },

    "home_appliances": {
        "segments": [
            "New Homeowners",
            "Young Couples",
            "Parents/Families",
            "Budget Shoppers",
            "Premium Home Seekers",
            "Energy-Conscious Consumers",
            "General Audience"
        ],
        "signals": {
            "New Homeowners": ["new home", "first home", "منزل جديد", "بيت جديد", "moving", "نقل"],
            "Young Couples": ["couple", "زوجين", "newlywed", "عروسين", "together"],
            "Parents/Families": ["family", "kids", "عائلة", "أطفال", "parents", "والدين"],
            "Budget Shoppers": ["affordable", "budget", "installment", "تقسيط", "save", "توفير"],
            "Premium Home Seekers": ["premium", "luxury", "high-end", "فاخر", "best quality"],
            "Energy-Conscious Consumers": ["energy saving", "توفير الطاقة", "eco", "efficient", "كفاءة"]
        }
    },

    "pharmacy": {
        "segments": [
            "Health-Conscious Consumers",
            "Parents/Caregivers",
            "Elderly/Senior Care",
            "Fitness/Wellness Seekers",
            "Budget-Conscious Shoppers",
            "Chronic Condition Patients",
            "General Audience"
        ],
        "signals": {
            "Health-Conscious Consumers": ["health", "صحة", "wellness", "عافية", "vitamins", "فيتامينات", "supplements"],
            "Parents/Caregivers": ["baby", "kids", "طفل", "أطفال", "family", "عائلة", "children"],
            "Elderly/Senior Care": ["elderly", "senior", "كبار السن", "aged", "arthritis", "pain relief"],
            "Fitness/Wellness Seekers": ["fitness", "protein", "بروتين", "sports nutrition", "muscle"],
            "Budget-Conscious Shoppers": ["affordable", "discount", "خصم", "save", "توفير"],
            "Chronic Condition Patients": ["diabetes", "سكري", "blood pressure", "ضغط الدم", "chronic"]
        }
    },

    "grocery": {
        "segments": [
            "Families",
            "Bulk Buyers",
            "Health-Conscious Shoppers",
            "Budget Shoppers",
            "Busy Professionals",
            "Organic/Premium Seekers",
            "General Audience"
        ],
        "signals": {
            "Families": ["family", "عائلة", "bulk", "بالجملة", "kids", "أطفال", "household"],
            "Bulk Buyers": ["bulk", "بالجملة", "wholesale", "stock up", "تخزين", "large pack"],
            "Health-Conscious Shoppers": ["organic", "عضوي", "healthy", "صحي", "fresh", "طازج", "natural"],
            "Budget Shoppers": ["discount", "خصم", "sale", "تخفيض", "save", "توفير", "cheap"],
            "Busy Professionals": ["quick", "سريع", "delivery", "توصيل", "convenient", "سهل"],
            "Organic/Premium Seekers": ["organic", "عضوي", "premium", "فاخر", "imported", "مستورد"]
        }
    }
}


class AudienceDetector:
    """
    Agent 9: Multi-Category Audience Detector

    Identifies target audience using:
    1. Category-specific segments
    2. Signal-based fast path
    3. Offer intelligence
    4. LLM fallback
    """

    def __init__(
        self,
        ollama_host: str = "http://localhost:11434",
        model: str = "llama3.1:8b"
    ):
        self.ollama_host = ollama_host
        self.model = model
        self.api_url = f"{ollama_host}/api/generate"

    def detect(self, context: AdContext) -> AudienceDecision:
        """Detect target audience from context"""

        # STEP 1: Infer product category
        category = self._infer_category(context)

        # STEP 2: Try signal-based detection (fast path)
        signal_result = self._detect_with_signals(context, category)
        if signal_result:
            print(f"   🎯 Signal match: {signal_result.target_audience}")
            return signal_result

        # STEP 3: Use offer intelligence
        offer_result = self._detect_from_offer(context, category)
        if offer_result:
            print(f"   💰 Offer-based: {offer_result.target_audience}")
            return offer_result

        # STEP 4: LLM fallback
        llm_result = self._detect_with_llm(context, category)
        print(f"   🤖 LLM detected: {llm_result.target_audience}")
        return llm_result

    def _infer_category(self, context: AdContext) -> str:
        """Infer product category from context"""

        text_lower = (context.raw_text or "").lower()

        # Restaurant detection
        if context.product_type == "restaurant":
            return "restaurant"

        # Physical products
        if context.product_type == "unknown_category":
            # Electronics
            if any(kw in text_lower for kw in ["phone", "هاتف", "laptop", "لابتوب", "tablet", "تابلت",
                                                 "tv", "تلفزيون", "headphones", "سماعات", "gaming", "قيمنق"]):
                return "electronics"

            # Fashion
            if any(kw in text_lower for kw in ["shirt", "قميص", "dress", "فستان", "shoes", "حذاء",
                                                 "abaya", "عباية", "fashion", "موضة", "clothing"]):
                return "fashion"

            # Sports
            if any(kw in text_lower for kw in ["gym", "جيم", "fitness", "لياقة", "dumbbell", "dumbbells",
                                                 "running", "جري", "yoga", "يوغا", "sports", "رياضة"]):
                return "sports"

            # Home Appliances
            if any(kw in text_lower for kw in ["fridge", "ثلاجة", "washing machine", "غسالة", "microwave",
                                                 "مايكرويف", "oven", "فرن", "air conditioner", "مكيف"]):
                return "home_appliances"

            # Pharmacy
            if any(kw in text_lower for kw in ["pharmacy", "صيدلية", "medicine", "دواء", "vitamin", "فيتامين",
                                                 "supplement", "مكمل", "health", "صحة", "drug"]):
                return "pharmacy"

        # Grocery/Category promotion
        if context.product_type == "category_promotion" or "grocery" in text_lower:
            return "grocery"

        # Default
        return "general"

    def _detect_with_signals(self, context: AdContext, category: str) -> Optional[AudienceDecision]:
        """Fast path: Signal-based detection"""

        text_lower = (context.raw_text or "").lower()

        # Get category-specific signals
        audience_data = AUDIENCE_INTELLIGENCE.get(category, {})
        signals_map = audience_data.get("signals", {})

        # Score each audience segment
        scores = {}
        matched_signals = {}

        for audience, keywords in signals_map.items():
            score = 0
            matches = []
            for kw in keywords:
                if kw in text_lower:
                    score += 3.0  # Each keyword match = 3 points
                    matches.append(kw)

            if score >= 3.0:  # Threshold: at least 1 keyword
                scores[audience] = score
                matched_signals[audience] = matches

        if not scores:
            return None

        # Get top audience
        top_audience = max(scores, key=scores.get)
        confidence = min(0.95, 0.70 + (scores[top_audience] / 30.0))  # Scale to confidence

        return AudienceDecision(
            target_audience=top_audience,
            confidence=confidence,
            signals=matched_signals[top_audience]
        )

    def _detect_from_offer(self, context: AdContext, category: str) -> Optional[AudienceDecision]:
        """Use offer intelligence to infer audience"""

        if not context.offer:
            return None

        offer = context.offer

        # "First order" → New Customers
        if (offer.offer_details and "first order" in offer.offer_details.lower()) or \
           (offer.offer_conditions and "first order" in offer.offer_conditions.lower()):
            return AudienceDecision(
                target_audience="New Customers",
                confidence=0.88,
                signals=["first_order_offer"]
            )

        # High discount (>40%) → Budget-Conscious
        if offer.offer_type == "percentage_discount" and offer.offer_details:
            try:
                percentage = int(offer.offer_details.split('%')[0])
                if percentage >= 40:
                    budget_audience = self._get_budget_audience(category)
                    return AudienceDecision(
                        target_audience=budget_audience,
                        confidence=0.75,
                        signals=[f"high_discount_{percentage}%"]
                    )
            except:
                pass

        return None

    def _get_budget_audience(self, category: str) -> str:
        """Get budget-conscious audience for category"""
        budget_map = {
            "restaurant": "Budget-Conscious Diners",
            "electronics": "Budget Shoppers",
            "fashion": "Budget Shoppers",
            "sports": "Budget Shoppers",
            "home_appliances": "Budget Shoppers",
            "pharmacy": "Budget-Conscious Shoppers",
            "grocery": "Budget Shoppers"
        }
        return budget_map.get(category, "Budget Shoppers")

    def _detect_with_llm(self, context: AdContext, category: str) -> AudienceDecision:
        """LLM fallback for complex detection"""

        text = context.raw_text or ""

        # Get category-specific segments
        audience_data = AUDIENCE_INTELLIGENCE.get(category, AUDIENCE_INTELLIGENCE["restaurant"])
        segments = audience_data.get("segments", [])

        segments_str = "\n".join([f"- {seg}" for seg in segments])

        prompt = f"""You are analyzing an advertisement (English or Arabic) to identify the target audience.

Product Category: {category}

Advertisement Text:
{text[:800]}

Available Audience Segments for {category}:
{segments_str}

Return VALID JSON (no other text):
{{
    "target_audience": "segment name from list above",
    "confidence": 0.0-1.0,
    "signals": ["signal1", "signal2"]
}}

Choose the BEST matching segment. If unclear, use "General Audience".
"""

        try:
            response = requests.post(
                self.api_url,
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.1, "num_predict": 256}
                },
                timeout=90
            )

            if response.status_code != 200:
                raise Exception(f"LLM API error: {response.status_code}")

            result = response.json()
            response_text = result.get('response', '').strip()

            # Extract JSON
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            if start_idx == -1 or end_idx == 0:
                raise ValueError("No JSON in LLM response")

            audience_data = json.loads(response_text[start_idx:end_idx])

            return AudienceDecision(
                target_audience=audience_data.get('target_audience', 'General Audience'),
                confidence=audience_data.get('confidence', 0.5),
                signals=audience_data.get('signals', [])
            )

        except Exception as e:
            print(f"   ⚠️  LLM failed: {e}")
            return AudienceDecision(
                target_audience="General Audience",
                confidence=0.3,
                signals=["llm_failure"]
            )
