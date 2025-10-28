#!/usr/bin/env python3
"""
Agent 5: Product Type Classifier
Classifies what type of product/service is being advertised using LLM analysis
"""

from __future__ import annotations

import requests
import json
import re
from dataclasses import dataclass
from typing import Dict, Optional, List

from .context import AdContext


@dataclass
class ProductTypeDecision:
    """Result from product type classification"""
    product_type: str  # restaurant | electronics | home_appliances | fashion | beauty | sports | pharmacy | toys | pet_supplies | grocery | flowers | entertainment | sweets_desserts | beverages | subscription | category_promotion
    confidence: float
    reasoning: str
    signals: List[str]


class ProductTypeClassifier:
    """
    Agent 5: Classifies the type of product/service being advertised

    Product Types:
    - restaurant: Specific restaurant or food establishment
    - unknown_category: Physical goods (groceries, appliances, etc.)
    - subscription: Platform subscription service
    - category_promotion: Multi-restaurant or food category promo
    """

    def __init__(
        self,
        ollama_host: str = "http://localhost:11434",
        model: str = "llama3.1:8b"
    ):
        self.ollama_host = ollama_host
        self.model = model
        self.api_url = f"{ollama_host}/api/generate"
        self._device_override_keywords = {
            "smartphone",
            "smart phone",
            "iphone",
            "android",
            "samsung",
            "galaxy",
            "xiaomi",
            "huawei",
            "pixel",
            "oneplus",
            "oppo",
            "vivo",
            "realme",
            "tablet",
            "ipad",
            "laptop",
            "macbook",
            "notebook",
            "ultrabook",
            "console",
            "playstation",
            "ps5",
            "xbox",
            "nintendo",
            "switch",
            "camera",
            "dslr",
            "mirrorless",
            "lens",
            "headphone",
            "headphones",
            "earbud",
            "earbuds",
            "airpods",
            "smartwatch",
            "smart watch",
            "apple watch",
            "fitbit",
            "garmin",
            "soundbar",
            "projector",
        }
        self._food_anchor_keywords = {
            "meal",
            "meals",
            "combo",
            "combos",
            "burger",
            "pizza",
            "shawarma",
            "restaurant",
            "dining",
            "menu",
            "order now",
            "offers",
            "deal",
            "deals",
            "food",
            "kitchen",
            "chef",
            "breakfast",
            "lunch",
            "dinner",
        }
        self._pet_keywords = {
            "pet", "pets", "dog", "cat", "puppy", "kitten",
            "pet food", "dog food", "cat food",
            "pet supplies", "pet accessories",
            "pet care", "pet toys",
        }
        self._pharmacy_keywords = {
            "pharmacy", "pharmacies", "صيدلية", "صيدليات",
            "medicine", "medicines", "دواء", "أدوية",
            "vitamin", "vitamins", "فيتامين", "فيتامينات",
            "supplement", "supplements", "مكمل", "مكملات",
            "medication", "medications", "علاج", "علاجات",
            "prescription", "وصفة طبية",
            "healthcare", "health products", "منتجات صحية",
            "medical supplies", "مستلزمات طبية",
            "wellness", "عافية", "صحة",
        }
        self._beauty_keywords = {
            "beauty", "جمال", "تجميل",
            "cosmetics", "مستحضرات تجميل", "ميكب",
            "makeup", "مكياج",
            "skincare", "عناية بالبشرة",
            "perfume", "عطر", "عطور",
            "fragrance", "رائحة",
            "lipstick", "أحمر شفاه",
            "mascara", "ماسكارا",
            "foundation", "فاونديشن",
            "serum", "سيروم",
            "cream", "كريم",
            "lotion", "لوشن",
            "hair care", "عناية بالشعر",
            "shampoo", "شامبو",
            "conditioner", "بلسم",
        }
        self._flowers_keywords = {
            "flowers", "flower", "زهور", "زهرة", "ورود", "ورد",
            "bouquet", "bouquets", "باقة", "باقات",
            "petals", "بتلات",
            "roses", "rose", "وردة",
            "arrangement", "تنسيق",
            "florist", "محل ورد",
            "ferns and petals", "ferns & petals",
        }
        self._entertainment_keywords = {
            "theme park", "water park", "waterpark", "مدينة ملاهي", "حديقة مائية",
            "amusement park", "منتزه",
            "tickets", "تذاكر", "admission", "دخول",
            "rides", "ألعاب", "attractions", "معالم",
            "entertainment", "ترفيه",
            "aquarium", "حوض أسماك", "museum", "متحف",
            "cinema", "movie", "سينما", "فيلم",
            "concert", "حفل", "show", "عرض",
            "meryal", "aqua park",
        }
        self._sweets_keywords = {
            "sweets", "حلويات", "حلوى",
            "desserts", "dessert", "حلى", "تحلية",
            "chocolate", "شوكولاتة",
            "candy", "حلوى", "سكاكر",
            "cake", "كيك", "كعكة",
            "pastry", "pastries", "معجنات حلوة",
            "bakery", "مخبز", "حلويات",
            "cookies", "بسكويت",
            "ice cream", "آيس كريم", "بوظة",
        }
        self._beverage_keywords = {
            "drinks", "drink", "مشروبات", "مشروب",
            "beverage", "beverages",
            "juice", "عصير",
            "coffee", "قهوة",
            "tea", "شاي",
            "milk", "حليب", "لبن",
            "water", "ماء", "مياه",
            "soda", "soft drink", "مشروب غازي",
            "energy drink", "مشروب طاقة",
        }
        self._toy_keywords = {
            "toy", "toys", "لعبة", "ألعاب",
            "kids", "children", "أطفال",
            "educational", "تعليمي",
            "learning", "تعلم",
            "game", "games", "ألعاب",
            "puzzle", "أحجية",
            "playstation", "xbox", "console",
            "action figure", "دمية",
            "lego", "building blocks",
        }

    def classify(self, context: AdContext) -> ProductTypeDecision:
        """
        Classify product type based on extracted text and brand information

        Args:
            context: AdContext with raw_text and brand_matches populated

        Returns:
            ProductTypeDecision with classification result
        """
        # Quick checks before LLM
        # Note: We no longer early-return on subscription detection
        # because ads can mention "Rafeeq Pro" while advertising products/electronics
        # We'll use subscription as a signal, not a definitive classification

        # 2. FAST PATH: Use Agent 4's entity_type if available (high confidence brands)
        if context.brand_matches:
            primary_brand = context.brand_matches[0]

            # Direct classification for known product brands
            if primary_brand.entity_type in {"product", "electronics", "fashion", "sports", "home_appliances", "pharmacy", "beauty", "flowers", "entertainment", "sweets_desserts", "beverages", "toys"} and primary_brand.confidence >= 0.82:
                # USE SPECIFIC CATEGORY FROM ENTITY_TYPE, NOT GENERIC "unknown_category"
                specific_category = primary_brand.entity_type
                decision = ProductTypeDecision(
                    product_type=specific_category,  # electronics, home_appliances, fashion, etc.
                    confidence=min(0.95, primary_brand.confidence + 0.05),
                    reasoning=f"Brand '{primary_brand.name}' is a known {specific_category.replace('_', ' ')} brand",
                    signals=["known_product_brand", f"entity_type={specific_category}"]
                )
                context.product_type = decision.product_type
                context.product_type_confidence = decision.confidence
                print(f"   ⚡ Fast path: {primary_brand.name} → {specific_category} (confidence: {decision.confidence:.2f})")
                return decision

            # Direct classification for known restaurant brands
            if primary_brand.entity_type == "restaurant" and primary_brand.confidence >= 0.85:
                decision = ProductTypeDecision(
                    product_type="restaurant",
                    confidence=min(0.95, primary_brand.confidence + 0.05),
                    reasoning=f"Brand '{primary_brand.name}' is a known restaurant",
                    signals=["known_restaurant_brand", f"entity_type={primary_brand.entity_type}"]
                )
                context.product_type = decision.product_type
                context.product_type_confidence = decision.confidence
                print(f"   ⚡ Fast path: {primary_brand.name} → restaurant (confidence: {decision.confidence:.2f})")
                return decision

            # Marketplace/Grocery: Favor category_promotion or unknown_category
            if primary_brand.entity_type in ["marketplace", "grocery"] and primary_brand.confidence >= 0.80:
                # Check if multiple products or category language
                text_lower = (context.raw_text or "").lower()
                category_signals = self._detect_category_signals(text_lower)

                if category_signals or "offers" in text_lower or "deals" in text_lower or "عروض" in text_lower:
                    decision = ProductTypeDecision(
                        product_type="category_promotion",
                        confidence=0.88,
                        reasoning=f"Marketplace '{primary_brand.name}' with category/offers language",
                        signals=["marketplace_brand", "category_signals"] + category_signals
                    )
                else:
                    decision = ProductTypeDecision(
                        product_type="unknown_category",
                        confidence=0.85,
                        reasoning=f"Marketplace '{primary_brand.name}' promoting specific products",
                        signals=["marketplace_brand", "unknown_category_context"]
                    )

                context.product_type = decision.product_type
                context.product_type_confidence = decision.confidence
                print(f"   ⚡ Fast path: {primary_brand.name} (marketplace) → {decision.product_type} (confidence: {decision.confidence:.2f})")
                return decision

        # 3. Check for pharmacy-related content (FAST PATH)
        text_lower = (context.raw_text or "").lower()
        pharmacy_signals = [kw for kw in self._pharmacy_keywords if kw in text_lower]
        if len(pharmacy_signals) >= 2:  # At least 2 pharmacy keywords
            decision = ProductTypeDecision(
                product_type="pharmacy",
                confidence=0.92,
                reasoning=f"Strong pharmacy-related signals: {', '.join(pharmacy_signals[:3])}",
                signals=["pharmacy_keywords"] + pharmacy_signals
            )
            context.product_type = decision.product_type
            context.product_type_confidence = decision.confidence
            print(f"   ⚡ Fast path: Pharmacy keywords detected → pharmacy (confidence: {decision.confidence:.2f})")
            return decision

        # 4. Check for beauty-related content (FAST PATH)
        beauty_signals = [kw for kw in self._beauty_keywords if kw in text_lower]
        if len(beauty_signals) >= 2:  # At least 2 beauty keywords
            decision = ProductTypeDecision(
                product_type="beauty",
                confidence=0.90,
                reasoning=f"Strong beauty-related signals: {', '.join(beauty_signals[:3])}",
                signals=["beauty_keywords"] + beauty_signals
            )
            context.product_type = decision.product_type
            context.product_type_confidence = decision.confidence
            print(f"   ⚡ Fast path: Beauty keywords detected → beauty (confidence: {decision.confidence:.2f})")
            return decision

        # 5. Check for flower-related content (FAST PATH)
        flower_signals = [kw for kw in self._flowers_keywords if kw in text_lower]
        if len(flower_signals) >= 2:  # At least 2 flower keywords
            decision = ProductTypeDecision(
                product_type="flowers",
                confidence=0.92,
                reasoning=f"Strong flower-related signals: {', '.join(flower_signals[:3])}",
                signals=["flower_keywords"] + flower_signals
            )
            context.product_type = decision.product_type
            context.product_type_confidence = decision.confidence
            print(f"   ⚡ Fast path: Flower keywords detected → flowers (confidence: {decision.confidence:.2f})")
            return decision

        # 6. Check for entertainment-related content (FAST PATH)
        entertainment_signals = [kw for kw in self._entertainment_keywords if kw in text_lower]
        if len(entertainment_signals) >= 2:
            decision = ProductTypeDecision(
                product_type="entertainment",
                confidence=0.92,
                reasoning=f"Strong entertainment signals: {', '.join(entertainment_signals[:3])}",
                signals=["entertainment_keywords"] + entertainment_signals
            )
            context.product_type = decision.product_type
            context.product_type_confidence = decision.confidence
            print(f"   ⚡ Fast path: Entertainment keywords detected → entertainment (confidence: {decision.confidence:.2f})")
            return decision

        # 7. Check for sweets/desserts-related content (FAST PATH)
        sweets_signals = [kw for kw in self._sweets_keywords if kw in text_lower]
        if len(sweets_signals) >= 2:
            decision = ProductTypeDecision(
                product_type="sweets_desserts",
                confidence=0.88,
                reasoning=f"Strong sweets signals: {', '.join(sweets_signals[:3])}",
                signals=["sweets_keywords"] + sweets_signals
            )
            context.product_type = decision.product_type
            context.product_type_confidence = decision.confidence
            print(f"   ⚡ Fast path: Sweets keywords detected → sweets_desserts (confidence: {decision.confidence:.2f})")
            return decision

        # 8. Check for beverage-related content (FAST PATH)
        beverage_signals = [kw for kw in self._beverage_keywords if kw in text_lower]
        if len(beverage_signals) >= 2:
            decision = ProductTypeDecision(
                product_type="beverages",
                confidence=0.88,
                reasoning=f"Strong beverage signals: {', '.join(beverage_signals[:3])}",
                signals=["beverage_keywords"] + beverage_signals
            )
            context.product_type = decision.product_type
            context.product_type_confidence = decision.confidence
            print(f"   ⚡ Fast path: Beverage keywords detected → beverages (confidence: {decision.confidence:.2f})")
            return decision

        # 9. Check for toy-related content (FAST PATH)
        toy_signals = [kw for kw in self._toy_keywords if kw in text_lower]
        if len(toy_signals) >= 2:
            decision = ProductTypeDecision(
                product_type="toys",
                confidence=0.90,
                reasoning=f"Strong toy signals: {', '.join(toy_signals[:3])}",
                signals=["toy_keywords"] + toy_signals
            )
            context.product_type = decision.product_type
            context.product_type_confidence = decision.confidence
            print(f"   ⚡ Fast path: Toy keywords detected → toys (confidence: {decision.confidence:.2f})")
            return decision

        # 10. Check for pet-related content (FAST PATH)
        pet_signals = [kw for kw in self._pet_keywords if kw in text_lower]
        if len(pet_signals) >= 2:  # At least 2 pet keywords
            decision = ProductTypeDecision(
                product_type="pet_supplies",
                confidence=0.90,
                reasoning=f"Strong pet-related signals: {', '.join(pet_signals[:3])}",
                signals=["pet_keywords"] + pet_signals
            )
            context.product_type = decision.product_type
            context.product_type_confidence = decision.confidence
            print(f"   ⚡ Fast path: Pet keywords detected → pet_supplies (confidence: {decision.confidence:.2f})")
            return decision

        # 7. Check for physical product keywords (high signal words)
        physical_signals = self._detect_unknown_category_signals(text_lower)

        # 8. Check for category/multi-restaurant signals
        category_signals = self._detect_category_signals(text_lower)

        # 9. Check if this is a PURE subscription ad (no products mentioned)
        # Only classify as subscription if:
        # - Subscription is detected AND
        # - No strong physical product signals AND
        # - No brand matches (except platform brands)
        is_pure_subscription = False
        if context.subscription and context.subscription.is_subscription:
            has_product_brands = any(
                brand.entity_type not in {"platform", "marketplace", "grocery"}
                for brand in (context.brand_matches or [])
            )
            if not has_product_brands and len(physical_signals) == 0:
                # This is purely advertising the subscription service
                is_pure_subscription = True
                decision = ProductTypeDecision(
                    product_type="subscription",
                    confidence=context.subscription.confidence,
                    reasoning=f"Pure subscription ad: {context.subscription.subscription_name} (no products mentioned)",
                    signals=["subscription_detected", "no_product_signals"]
                )
                context.product_type = decision.product_type
                context.product_type_confidence = decision.confidence
                print(f"   ⚡ Fast path: Pure subscription ad → subscription (confidence: {decision.confidence:.2f})")
                return decision

        # 5. CONFLICT RESOLUTION: Platform advertising products
        platform_product_conflict = False
        if context.platform_branding and context.brand_matches:
            primary_brand = context.brand_matches[0]
            if primary_brand.entity_type in ["product", "grocery", "marketplace"]:
                platform_product_conflict = True
                print(f"   ⚠️  Conflict detected: Platform '{context.platform_branding}' advertising '{primary_brand.name}' ({primary_brand.entity_type})")

        # 6. Use brand entity types if available
        brand_hints = []
        if context.brand_matches:
            for brand in context.brand_matches:
                brand_hints.append(f"{brand.name} ({brand.entity_type})")

        # Build prompt for LLM classification
        prompt = self._build_classification_prompt(
            text_lower,
            physical_signals,
            category_signals,
            brand_hints,
            platform_product_conflict,
            context.platform_branding
        )

        # Call LLM
        try:
            decision = self._classify_with_llm(prompt, physical_signals, category_signals)
        except Exception as e:
            print(f"   ⚠️  LLM classification failed: {e}")
            # Fallback to heuristic classification
            decision = self._heuristic_classification(physical_signals, category_signals)

        decision = self._postprocess_decision(
            context=context,
            decision=decision,
            text_lower=text_lower,
            physical_signals=physical_signals,
            category_signals=category_signals,
        )

        # Update context
        context.product_type = decision.product_type
        context.product_type_confidence = decision.confidence

        return decision

    def _detect_unknown_category_signals(self, text: str) -> List[str]:
        """Detect strong signals for physical products (English & Arabic)"""
        signals = []

        # Product attribute keywords (English + Arabic)
        product_keywords = [
            "specifications", "features", "model", "version", "capacity",
            "dimensions", "weight", "material", "color", "size",
            "warranty", "guarantee", "brand new", "original",
            "kitchen appliance", "blender", "pot", "pan", "cooker",
            "electronics", "gadget", "device", "tool",
            "grocery", "groceries", "fresh", "organic", "produce",
            "smartphone", "phone", "tablet", "laptop", "notebook", "console", "playstation", "xbox", "headphones",
            "camera", "dslr", "lens", "smartwatch", "earbuds", "gaming pc",
            "fridge", "refrigerator", "washing machine", "dryer", "microwave", "air conditioner", "vacuum", "dishwasher",
            "clothes", "fashion", "dress", "shirt", "abaya", "abayas", "shoe", "sneaker", "bag", "accessories",
            "sportswear", "fitness", "equipment", "dumbbell", "treadmill", "yoga mat", "cycling",
            # Arabic keywords
            "مواصفات", "ميزات", "موديل", "سعة", "وزن", "مادة",
            "ضمان", "جديد", "أصلي", "جهاز", "أداة", "بقالة", "طازج",
            "هاتف", "جوال", "كمبيوتر", "تابلت", "سماعة", "سماعات",
            "كاميرا", "عدسة", "ساعة ذكية", "معالج", "أجهزة منزلية", "ثلاجة", "غسالة", "مكيف",
            "ملابس", "أزياء", "فساتين", "عباية", "عبايات", "أحذية", "حقيبة", "اكسسوارات",
            "رياضة", "معدات", "لياقة"
        ]

        for keyword in product_keywords:
            if keyword in text:
                signals.append(keyword)

        # Numeric patterns (prices, capacities, etc.)
        if re.search(r'\d+\s*(l|ml|kg|g|inch|cm|mm|watt|w)', text, re.IGNORECASE):
            signals.append("technical_specs")

        return signals

    def _detect_category_signals(self, text: str) -> List[str]:
        """Detect signals for category promotions"""
        signals = []

        category_keywords = [
            "all restaurants", "multiple restaurants", "various restaurants",
            "pizza category", "burger category", "asian food category",
            "restaurants near you", "explore restaurants",
            "choose from", "hundreds of", "thousands of",
            "any restaurant", "all cuisines",
            "all electronics", "multiple electronics", "various electronics",
            "shop all gadgets", "all smartphones", "electronics deals",
            "fashion brands", "all fashion", "clothing brands",
            "sports brands", "outdoor brands", "home appliance deals"
        ]

        for keyword in category_keywords:
            if keyword in text:
                signals.append(keyword)

        return signals

    def _build_classification_prompt(
        self,
        text: str,
        physical_signals: List[str],
        category_signals: List[str],
        brand_hints: List[str],
        platform_product_conflict: bool = False,
        platform_name: Optional[str] = None
    ) -> str:
        """Build LLM prompt for classification"""

        signals_section = ""
        if physical_signals:
            signals_section += f"\n- Physical product signals detected: {', '.join(physical_signals)}"
        if category_signals:
            signals_section += f"\n- Category promotion signals detected: {', '.join(category_signals)}"
        if brand_hints:
            signals_section += f"\n- Detected brands: {', '.join(brand_hints)}"

        # Add conflict resolution context
        conflict_context = ""
        if platform_product_conflict and platform_name:
            conflict_context = f"""

⚠️ CONFLICT RESOLUTION CONTEXT:
The advertiser is '{platform_name}', a food delivery platform, but the ad mentions products/groceries/marketplaces.
This is NORMAL - platforms often advertise products they sell through their grocery/mart sections.
Classify the PRODUCT BEING ADVERTISED, not the platform itself.
Example: If Talabat advertises Nutribullet, classify as "unknown_category", not "restaurant" or "subscription".
"""

        prompt = f"""You are analyzing advertisement text (English or Arabic) to classify what type of product/service is being advertised.

Advertisement Text:
{text[:1000]}

{signals_section}
{conflict_context}

Classify this advertisement into ONE of these categories (text may be in English or Arabic):

1. **restaurant** - A specific restaurant or food establishment
   Examples: "McDonald's 50% off", "Pizza Hut family deal", "Subway sandwich"

2. **electronics** - Electronic devices and gadgets
   Examples: "iPhone 15 Pro", "Samsung Galaxy", "Laptop deals", "Headphones"

3. **home_appliances** - Kitchen and home appliances
   Examples: "Washing machine", "Refrigerator", "Microwave", "Air conditioner"

4. **fashion** - Clothing, shoes, bags, accessories
   Examples: "Abaya collection", "Summer dresses", "Nike shoes", "Handbags"

5. **beauty** - Cosmetics, skincare, fragrances
   Examples: "MAC cosmetics", "Perfume sale", "Skincare products"

6. **sports** - Sports equipment and fitness gear
   Examples: "Gym equipment", "Running shoes", "Yoga mats", "Cycling gear"

7. **pharmacy** - Medicine, health products, supplements
   Examples: "Vitamins", "First aid", "Medical supplies", "Pharmacy deals"

8. **toys** - Children's toys and games
   Examples: "LEGO sets", "Board games", "Action figures"

9. **pet_supplies** - Pet food, accessories, supplies
   Examples: "Dog food", "Cat litter", "Pet toys", "Pet accessories"

10. **grocery** - Food items, fresh produce, household essentials
    Examples: "Fresh vegetables", "Organic food", "Grocery delivery", "Milk", "Eggs"

11. **flowers** - Flowers, bouquets, floral arrangements
    Examples: "Roses", "Flower bouquets", "Ferns and Petals", "Flower delivery"

12. **entertainment** - Theme parks, waterparks, cinemas, museums, concerts
    Examples: "Meryal Waterpark", "Theme park tickets", "Cinema tickets", "Aquarium"

13. **sweets_desserts** - Sweets, desserts, bakery items, ice cream
    Examples: "Al Wakrah Sweets", "Chocolate", "Cake shop", "Ice cream", "Bakery"

14. **beverages** - Drinks, juices, coffee, tea, milk products
    Examples: "Coffee shop", "Juice bar", "Energy drinks", "Soft drinks"

15. **subscription** - Platform subscription service
    Examples: "Talabat Pro membership", "Deliveroo Plus unlimited delivery"

16. **category_promotion** - Multi-restaurant or multi-product category promotion
    Examples: "All pizza restaurants 30% off", "Shop all electronics"

Return your analysis in VALID JSON format (no other text):

{{
    "product_type": "restaurant" | "electronics" | "home_appliances" | "fashion" | "beauty" | "sports" | "pharmacy" | "toys" | "pet_supplies" | "grocery" | "flowers" | "entertainment" | "sweets_desserts" | "beverages" | "subscription" | "category_promotion",
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation",
    "key_signals": ["signal1", "signal2"]
}}

IMPORTANT:
- Choose the MOST SPECIFIC category that matches the ad
- If multiple products/restaurants → category_promotion
- Return ONLY valid JSON, no other text.
"""
        return prompt

    def _classify_with_llm(
        self,
        prompt: str,
        physical_signals: List[str],
        category_signals: List[str]
    ) -> ProductTypeDecision:
        """Use LLM to classify product type"""

        print(f"   🤖 Classifying product type with {self.model}...")

        response = requests.post(
            self.api_url,
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "num_predict": 256
                }
            },
            timeout=90
        )

        if response.status_code != 200:
            raise Exception(f"LLM API error: {response.status_code}")

        result = response.json()
        response_text = result.get('response', '').strip()

        # Extract JSON from response
        if response_text.startswith('```'):
            lines = response_text.split('\n')
            response_text = '\n'.join(lines[1:-1])

        start_idx = response_text.find('{')
        end_idx = response_text.rfind('}') + 1

        if start_idx == -1 or end_idx == 0:
            raise ValueError("No JSON found in LLM response")

        json_str = response_text[start_idx:end_idx]
        classification = json.loads(json_str)

        product_type = classification.get('product_type', 'unknown')
        confidence = classification.get('confidence', 0.5)
        reasoning = classification.get('reasoning', '')
        key_signals = classification.get('key_signals', [])

        # Boost confidence if we have strong signals
        if product_type == 'unknown_category' and len(physical_signals) >= 3:
            confidence = min(0.95, confidence + 0.1)

        print(f"   ✅ Classified as: {product_type} (confidence: {confidence:.2f})")

        return ProductTypeDecision(
            product_type=product_type,
            confidence=confidence,
            reasoning=reasoning,
            signals=key_signals
        )

    def _postprocess_decision(
        self,
        context: AdContext,
        decision: ProductTypeDecision,
        text_lower: str,
        physical_signals: List[str],
        category_signals: List[str],
    ) -> ProductTypeDecision:
        """Apply deterministic overrides after LLM classification."""

        if decision.product_type == "unknown_category":
            return decision

        # Removed subscription early return - we want to allow overrides even for subscription ads
        # because they might be advertising products while mentioning the subscription

        strong_physical = len(set(physical_signals)) >= 3
        has_device_terms = any(keyword in text_lower for keyword in self._device_override_keywords)
        if decision.product_type in {"restaurant", "category_promotion"}:
            if (strong_physical or has_device_terms) and not category_signals:
                if not self._contains_food_language(text_lower):
                    print("   🔄 Override: strong physical product cues detected, forcing unknown_category")
                    merged_signals = sorted(set(decision.signals + physical_signals))
                    return ProductTypeDecision(
                        product_type="unknown_category",
                        confidence=max(decision.confidence, 0.83),
                        reasoning="Overrode LLM: detected strong physical product indicators (e.g., smartphone/device terms)",
                        signals=merged_signals,
                    )

        return decision

    def _contains_food_language(self, text_lower: str) -> bool:
        """Detect whether obvious food terminology is present."""

        return any(token in text_lower for token in self._food_anchor_keywords)

    def _heuristic_classification(
        self,
        physical_signals: List[str],
        category_signals: List[str]
    ) -> ProductTypeDecision:
        """Fallback heuristic classification if LLM fails"""

        print("   ⚠️  Using heuristic classification (LLM failed)")

        # Strong physical product signals
        if len(physical_signals) >= 2:
            return ProductTypeDecision(
                product_type="unknown_category",
                confidence=0.7,
                reasoning="Multiple physical product signals detected",
                signals=physical_signals
            )

        # Category promotion signals
        if len(category_signals) >= 1:
            return ProductTypeDecision(
                product_type="category_promotion",
                confidence=0.6,
                reasoning="Category promotion signals detected",
                signals=category_signals
            )

        # Default to restaurant with low confidence
        return ProductTypeDecision(
            product_type="restaurant",
            confidence=0.4,
            reasoning="No strong signals detected, defaulting to restaurant",
            signals=[]
        )


# ============================================================================
# Test Function
# ============================================================================

def test_product_type_classifier():
    """Test the product type classifier"""
    print("=" * 70)
    print("TESTING PRODUCT TYPE CLASSIFIER")
    print("=" * 70)

    classifier = ProductTypeClassifier()

    # Test case 1: Physical product
    context1 = AdContext(
        unique_id="test1",
        advertiser_id="AR14306592000630063105",
        raw_text="Nutribullet 9-in-1 Smart Pot 2. Specifications: 6L capacity, 1000W power, multi-function cooker"
    )

    print("\n--- Test 1: Physical Product ---")
    decision1 = classifier.classify(context1)
    print(f"Type: {decision1.product_type}")
    print(f"Confidence: {decision1.confidence}")
    print(f"Reasoning: {decision1.reasoning}")

    # Test case 2: Restaurant
    context2 = AdContext(
        unique_id="test2",
        advertiser_id="AR14306592000630063105",
        raw_text="McDonald's Big Mac Meal 50% off! Get your favorite burger today."
    )

    print("\n--- Test 2: Restaurant ---")
    decision2 = classifier.classify(context2)
    print(f"Type: {decision2.product_type}")
    print(f"Confidence: {decision2.confidence}")
    print(f"Reasoning: {decision2.reasoning}")

    # Test case 3: Category promotion
    context3 = AdContext(
        unique_id="test3",
        advertiser_id="AR14306592000630063105",
        raw_text="Free delivery on all pizza restaurants! Choose from hundreds of options."
    )

    print("\n--- Test 3: Category Promotion ---")
    decision3 = classifier.classify(context3)
    print(f"Type: {decision3.product_type}")
    print(f"Confidence: {decision3.confidence}")
    print(f"Reasoning: {decision3.reasoning}")


if __name__ == "__main__":
    test_product_type_classifier()
