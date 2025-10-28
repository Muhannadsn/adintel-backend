#!/usr/bin/env python3
"""
Agent 7: Food Category Classifier
Classifies food type for restaurant ads (only runs if product_type == "restaurant")
"""

from __future__ import annotations

import requests
import json
import re
from dataclasses import dataclass
from typing import Dict, Optional, List

from .context import AdContext


@dataclass
class FoodCategoryDecision:
    """Result from food category classification"""
    food_category: str
    confidence: float
    reasoning: str
    signals: List[str]


# Known restaurant → category mapping (fast path)
RESTAURANT_CATEGORY_MAP: Dict[str, str] = {
    # Burgers & Fast Food
    "McDonald's": "Burgers & Fast Food",
    "Burger King": "Burgers & Fast Food",
    "Five Guys": "Burgers & Fast Food",
    "Shake Shack": "Burgers & Fast Food",
    "Smash Me": "Burgers & Fast Food",
    "Wendy's": "Burgers & Fast Food",
    "Carl's Jr.": "Burgers & Fast Food",
    "Hardee's": "Burgers & Fast Food",
    "Johnny Rockets": "Burgers & Fast Food",
    "In-N-Out": "Burgers & Fast Food",

    # Pizza & Italian
    "Pizza Hut": "Pizza & Italian",
    "Domino's": "Pizza & Italian",
    "Papa John's": "Pizza & Italian",
    "Little Caesars": "Pizza & Italian",
    "Papa Murphy's": "Pizza & Italian",
    "Sbarro": "Pizza & Italian",
    "California Pizza Kitchen": "Pizza & Italian",

    # Fried Chicken
    "KFC": "Fried Chicken & Fast Food",
    "Popeyes": "Fried Chicken & Fast Food",
    "Texas Chicken": "Fried Chicken & Fast Food",
    "Church's Chicken": "Fried Chicken & Fast Food",
    "Bojangles": "Fried Chicken & Fast Food",
    "Raising Cane's": "Fried Chicken & Fast Food",
    "Jollibee": "Fried Chicken & Fast Food",

    # Asian Food (Chinese/Thai/Japanese/Korean)
    "P.F. Chang's": "Asian Food (Chinese/Thai/Japanese)",
    "Panda Express": "Asian Food (Chinese/Thai/Japanese)",
    "Wagamama": "Asian Food (Chinese/Thai/Japanese)",
    "Pei Wei": "Asian Food (Chinese/Thai/Japanese)",
    "Benihana": "Asian Food (Chinese/Thai/Japanese)",
    "Yoshinoya": "Asian Food (Chinese/Thai/Japanese)",
    "Teriyaki Madness": "Asian Food (Chinese/Thai/Japanese)",
    "Noodles & Company": "Asian Food (Chinese/Thai/Japanese)",
    "Chipotle": "Mexican & Tex-Mex",  # Not Asian, special case

    # Mexican & Tex-Mex
    "Chipotle": "Mexican & Tex-Mex",
    "Taco Bell": "Mexican & Tex-Mex",
    "Qdoba": "Mexican & Tex-Mex",
    "Moe's Southwest Grill": "Mexican & Tex-Mex",
    "Del Taco": "Mexican & Tex-Mex",
    "Tijuana Flats": "Mexican & Tex-Mex",

    # Sandwiches & Subs
    "Subway": "Sandwiches & Subs",
    "Jimmy John's": "Sandwiches & Subs",
    "Jersey Mike's": "Sandwiches & Subs",
    "Firehouse Subs": "Sandwiches & Subs",
    "Quiznos": "Sandwiches & Subs",
    "Panera Bread": "Sandwiches & Subs",
    "Potbelly": "Sandwiches & Subs",

    # Coffee & Beverages
    "Starbucks": "Coffee & Beverages",
    "Costa Coffee": "Coffee & Beverages",
    "Dunkin'": "Coffee & Beverages",
    "Dunkin' Donuts": "Coffee & Beverages",
    "Tim Hortons": "Coffee & Beverages",
    "Caribou Coffee": "Coffee & Beverages",
    "Peet's Coffee": "Coffee & Beverages",
    "The Coffee Bean": "Coffee & Beverages",

    # Desserts & Sweets
    "Baskin Robbins": "Desserts & Sweets",
    "Cold Stone": "Desserts & Sweets",
    "Dairy Queen": "Desserts & Sweets",
    "Ben & Jerry's": "Desserts & Sweets",
    "Häagen-Dazs": "Desserts & Sweets",
    "Cinnabon": "Desserts & Sweets",
    "Krispy Kreme": "Desserts & Sweets",
    "Auntie Anne's": "Desserts & Sweets",
    "Yogurtland": "Desserts & Sweets",
    "Jamba Juice": "Healthy/Organic Food",  # Smoothies = healthy

    # Healthy/Organic Food (Acai, Smoothies, Salads)
    "Sweetgreen": "Healthy/Organic Food",
    "Cava": "Healthy/Organic Food",
    "Freshii": "Healthy/Organic Food",
    "Saladworks": "Healthy/Organic Food",
    "Tender Greens": "Healthy/Organic Food",
    "Juice It Up": "Healthy/Organic Food",
    "Nekter Juice Bar": "Healthy/Organic Food",
    "Playa Bowls": "Healthy/Organic Food",  # Acai bowls
    "Vitality Bowls": "Healthy/Organic Food",  # Acai/superfood bowls
    "Jamba Juice": "Healthy/Organic Food",
    "Smoothie King": "Healthy/Organic Food",

    # Arabic & Middle Eastern
    "Shawarma House": "Arabic & Middle Eastern",
    "Al Baik": "Arabic & Middle Eastern",
    "Zaatar w Zeit": "Arabic & Middle Eastern",
    "Just Falafel": "Arabic & Middle Eastern",
    "Operation Falafel": "Arabic & Middle Eastern",

    # Premium/Fine Dining
    "The Cheesecake Factory": "Premium/Fine Dining",
    "Ruth's Chris": "Premium/Fine Dining",
    "Morton's": "Premium/Fine Dining",
    "Capital Grille": "Premium/Fine Dining",

    # Breakfast & Brunch
    "IHOP": "Breakfast & Brunch",
    "Denny's": "Breakfast & Brunch",
    "Waffle House": "Breakfast & Brunch",
    "First Watch": "Breakfast & Brunch",
    "Cracker Barrel": "Breakfast & Brunch",
}


class FoodCategoryClassifier:
    """
    Agent 7: Classifies food category for restaurant ads

    Categories:
    - Burgers & Fast Food
    - Pizza & Italian
    - Mexican & Tex-Mex
    - Asian Food (Chinese/Thai/Japanese)
    - Arabic & Middle Eastern
    - Fried Chicken & Fast Food
    - Sandwiches & Subs
    - Breakfast & Brunch
    - Desserts & Sweets
    - Coffee & Beverages
    - Healthy/Organic Food (Acai bowls, smoothies, salads, vegan)
    - Premium/Fine Dining
    """

    def __init__(
        self,
        ollama_host: str = "http://localhost:11434",
        model: str = "llama3.1:8b"
    ):
        self.ollama_host = ollama_host
        self.model = model
        self.api_url = f"{ollama_host}/api/generate"

    def classify(self, context: AdContext) -> Optional[FoodCategoryDecision]:
        """
        Classify food category for restaurant ads

        Args:
            context: AdContext with product_type and brand populated

        Returns:
            FoodCategoryDecision or None if not a restaurant
        """
        # Only run for restaurants
        if context.product_type != "restaurant":
            return None

        # FAST PATH 1: Use known restaurant → category mapping
        if context.brand and context.brand in RESTAURANT_CATEGORY_MAP:
            category = RESTAURANT_CATEGORY_MAP[context.brand]
            decision = FoodCategoryDecision(
                food_category=category,
                confidence=0.95,
                reasoning=f"Known restaurant '{context.brand}' mapped to category",
                signals=["known_restaurant_mapping"]
            )
            context.add_evidence(
                agent="FoodCategoryClassifier",
                observation=f"Fast path: {context.brand} → {category}",
                confidence=0.95
            )
            print(f"   ⚡ Fast path: {context.brand} → {category}")
            return decision

        # FAST PATH 2: Check for strong keyword signals (English + Arabic)
        text_lower = (context.raw_text or "").lower()
        keyword_category = self._detect_category_by_keywords(text_lower)

        if keyword_category:
            decision = FoodCategoryDecision(
                food_category=keyword_category["category"],
                confidence=keyword_category["confidence"],
                reasoning=f"Strong keywords detected: {', '.join(keyword_category['signals'])}",
                signals=keyword_category["signals"]
            )
            context.add_evidence(
                agent="FoodCategoryClassifier",
                observation=f"Keyword match: {keyword_category['category']}",
                confidence=keyword_category["confidence"]
            )
            print(f"   ⚡ Keyword match: {keyword_category['category']} (confidence: {keyword_category['confidence']:.2f})")
            return decision

        # Fallback to LLM classification
        try:
            decision = self._classify_with_llm(context)
            context.add_evidence(
                agent="FoodCategoryClassifier",
                observation=f"LLM classification: {decision.food_category}",
                confidence=decision.confidence
            )
            return decision
        except Exception as e:
            print(f"   ⚠️  LLM classification failed: {e}")
            # Default fallback
            decision = FoodCategoryDecision(
                food_category="Specific Restaurant/Brand Promo",
                confidence=0.3,
                reasoning="Classification failed, using default category",
                signals=["fallback"]
            )
            return decision

    def _detect_category_by_keywords(self, text: str) -> Optional[Dict]:
        """Detect food category by strong keywords (English + Arabic)"""

        # Category keyword patterns (English + Arabic) - ordered by specificity
        # IMPORTANT: More specific categories FIRST to avoid false matches
        category_patterns = {
            "Healthy/Organic Food": {
                "keywords": [
                    # Acai & Superfoods (HIGH PRIORITY)
                    "acai", "أساي", "açaí", "superfood", "سوبرفود", "acai bowl", "smoothie bowl",
                    # Salads & Greens
                    "healthy", "صحي", "organic", "عضوي", "salad", "سلطة", "vegan", "نباتي", "vegetarian",
                    # Fresh & Clean
                    "kale", "كيل", "quinoa", "كينوا", "avocado", "أفوكادو",
                    # Juices & Smoothies
                    "juice", "عصير", "smoothie", "سموذي", "cold pressed", "detox", "ديتوكس", "green juice",
                    # Bowls (but we'll need "acai" or "superfood" nearby)
                    "protein bowl", "buddha bowl", "grain bowl"
                ],
                "confidence": 0.82
            },
            "Mexican & Tex-Mex": {
                "keywords": ["taco", "tacos", "تاكو", "burrito", "بوريتو", "quesadilla", "كيساديا", "nachos", "ناتشوز", "guacamole", "mexican", "مكسيكي", "chipotle", "salsa"],
                "confidence": 0.88
            },
            "Pizza & Italian": {
                "keywords": ["pizza", "pizzas", "بيتزا", "italian", "pasta", "باستا", "margherita", "pepperoni", "calzone", "lasagna"],
                "confidence": 0.88
            },
            "Burgers & Fast Food": {
                "keywords": ["burger", "burgers", "برجر", "برغر", "big mac", "whopper", "fries", "بطاطس مقلية", "cheeseburger"],
                "confidence": 0.88
            },
            "Fried Chicken & Fast Food": {
                "keywords": ["chicken", "دجاج", "fried chicken", "دجاج مقلي", "wings", "أجنحة", "crispy", "كرسبي", "tenders", "bucket"],
                "confidence": 0.85
            },
            "Asian Food (Chinese/Thai/Japanese)": {
                "keywords": ["sushi", "سوشي", "chinese", "صيني", "thai", "تايلندي", "ramen", "راميـن", "noodles", "نودلز", "wok", "dim sum", "pad thai", "teriyaki", "تيرياكي", "hibachi", "poke bowl"],
                "confidence": 0.87
            },
            "Arabic & Middle Eastern": {
                "keywords": ["shawarma", "شاورما", "kabab", "كباب", "kebab", "falafel", "فلافل", "hummus", "حمص", "arabic", "عربي", "tabbouleh", "تبولة", "fattoush", "فتوش", "manakish", "مناقيش"],
                "confidence": 0.87
            },
            "Coffee & Beverages": {
                "keywords": ["coffee", "قهوة", "latte", "لاتيه", "cappuccino", "كابتشينو", "espresso", "اسبريسو", "frappuccino", "فرابتشينو", "mocha", "موكا", "americano"],
                "confidence": 0.90
            },
            "Desserts & Sweets": {
                "keywords": ["ice cream", "آيس كريم", "dessert", "حلويات", "cake", "كيك", "brownie", "براوني", "sweet", "حلو", "donut", "دونات", "gelato", "جيلاتو", "frozen yogurt"],
                "confidence": 0.88
            },
            "Breakfast & Brunch": {
                "keywords": ["breakfast", "فطور", "brunch", "eggs", "بيض", "pancakes", "بان كيك", "waffle", "وافل", "french toast", "omelette", "أومليت"],
                "confidence": 0.85
            },
            "Sandwiches & Subs": {
                "keywords": ["sandwich", "ساندويتش", "sub", "سب", "wrap", "لفافة", "panini", "باني��ي", "hoagie", "club sandwich"],
                "confidence": 0.85
            },
            "Healthy/Organic Food": {
                "keywords": [
                    # Acai & Superfoods
                    "acai", "أساي", "açaí", "superfood", "سوبرفود", "acai bowl", "smoothie bowl",
                    # Salads & Greens
                    "healthy", "صحي", "organic", "عضوي", "salad", "سلطة", "vegan", "نباتي", "vegetarian", "نباتي",
                    # Fresh & Clean
                    "fresh", "طازج", "kale", "كيل", "quinoa", "كينوا", "avocado", "أفوكادو",
                    # Juices & Smoothies
                    "juice", "عصير", "smoothie", "سموذي", "cold pressed", "detox", "ديتوكس", "green juice",
                    # Bowls
                    "poke bowl", "buddha bowl", "grain bowl", "protein bowl"
                ],
                "confidence": 0.82
            }
        }

        # Check each category
        for category, data in category_patterns.items():
            matched_keywords = []
            for keyword in data["keywords"]:
                if keyword in text:
                    matched_keywords.append(keyword)

            # If we have 2+ keyword matches, high confidence
            if len(matched_keywords) >= 2:
                return {
                    "category": category,
                    "confidence": min(0.92, data["confidence"] + 0.05),
                    "signals": matched_keywords[:3]  # Top 3 signals
                }
            # 1 match = medium confidence
            elif len(matched_keywords) == 1:
                return {
                    "category": category,
                    "confidence": data["confidence"],
                    "signals": matched_keywords
                }

        return None

    def _classify_with_llm(self, context: AdContext) -> FoodCategoryDecision:
        """Use LLM to classify food category"""

        text = context.raw_text or ""
        brand_hint = f"Restaurant: {context.brand}" if context.brand else ""

        prompt = f"""You are analyzing a restaurant advertisement (English or Arabic) to classify the food category.

Advertisement Text:
{text[:800]}

{brand_hint}

Classify this restaurant into ONE of these food categories (text may be in English or Arabic):

1. **Burgers & Fast Food** - Burger joints, fast food chains
   Examples: McDonald's, Burger King, Five Guys

2. **Pizza & Italian** - Pizza restaurants, Italian cuisine
   Examples: Pizza Hut, Domino's, Italian restaurants

3. **Mexican & Tex-Mex** - Mexican food, tacos, burritos
   Examples: Chipotle, Taco Bell, Mexican restaurants

4. **Asian Food (Chinese/Thai/Japanese)** - Asian cuisine
   Examples: Chinese takeout, sushi, Thai food, ramen, poke bowls

5. **Arabic & Middle Eastern** - Arabic/Middle Eastern cuisine
   Examples: Shawarma, kabab, falafel, hummus, Arabic restaurants

6. **Fried Chicken & Fast Food** - Fried chicken restaurants
   Examples: KFC, Popeyes, Texas Chicken

7. **Sandwiches & Subs** - Sandwich shops
   Examples: Subway, sandwich cafes

8. **Breakfast & Brunch** - Breakfast-focused restaurants
   Examples: Pancakes, eggs, breakfast combos

9. **Desserts & Sweets** - Dessert shops, ice cream
   Examples: Ice cream, cakes, desserts

10. **Coffee & Beverages** - Coffee shops, beverage cafes
    Examples: Starbucks, Costa, coffee shops

11. **Healthy/Organic Food** - Health-focused restaurants, acai bowls, smoothies
    Examples: Salad bars, vegan restaurants, organic food, acai bowls, juice bars, poke bowls

12. **Premium/Fine Dining** - Upscale restaurants
    Examples: Fine dining, premium steakhouses

13. **Specific Restaurant/Brand Promo** - General restaurant (can't determine specific category)

Return your analysis in VALID JSON format (no other text):

{{
    "food_category": "category name from above",
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation",
    "key_signals": ["signal1", "signal2"]
}}

IMPORTANT:
- Look for food item mentions (pizza, burger, shawarma, etc.)
- Check restaurant type/cuisine mentions
- Return ONLY valid JSON, no other text.
"""

        print(f"   🤖 Classifying food category with {self.model}...")

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

        food_category = classification.get('food_category', 'Specific Restaurant/Brand Promo')
        confidence = classification.get('confidence', 0.5)
        reasoning = classification.get('reasoning', '')
        key_signals = classification.get('key_signals', [])

        print(f"   ✅ Classified as: {food_category} (confidence: {confidence:.2f})")

        return FoodCategoryDecision(
            food_category=food_category,
            confidence=confidence,
            reasoning=reasoning,
            signals=key_signals
        )


# ============================================================================
# Test Function
# ============================================================================

def test_food_category_classifier():
    """Test the food category classifier"""
    print("=" * 70)
    print("TESTING FOOD CATEGORY CLASSIFIER")
    print("=" * 70)

    classifier = FoodCategoryClassifier()

    # Test 1: Known restaurant (McDonald's)
    context1 = AdContext(
        unique_id="test1",
        advertiser_id="AR123",
        raw_text="McDonald's Big Mac Meal 50% off!",
        brand="McDonald's",
        product_type="restaurant"
    )

    print("\n--- Test 1: Known Restaurant (McDonald's) ---")
    decision1 = classifier.classify(context1)
    print(f"Category: {decision1.food_category}")
    print(f"Confidence: {decision1.confidence}")
    print(f"Reasoning: {decision1.reasoning}")

    # Test 2: Keyword detection (Arabic shawarma)
    context2 = AdContext(
        unique_id="test2",
        advertiser_id="AR123",
        raw_text="شاورما دجاج طازج مع خبز عربي! اطلب الآن",
        product_type="restaurant"
    )

    print("\n--- Test 2: Arabic Keywords (Shawarma) ---")
    decision2 = classifier.classify(context2)
    print(f"Category: {decision2.food_category}")
    print(f"Confidence: {decision2.confidence}")
    print(f"Signals: {decision2.signals}")

    # Test 3: Pizza keywords
    context3 = AdContext(
        unique_id="test3",
        advertiser_id="AR123",
        raw_text="Large pizza with 3 toppings for only QAR 39!",
        product_type="restaurant"
    )

    print("\n--- Test 3: Pizza Keywords ---")
    decision3 = classifier.classify(context3)
    print(f"Category: {decision3.food_category}")
    print(f"Confidence: {decision3.confidence}")
    print(f"Signals: {decision3.signals}")

    # Test 4: Coffee (Arabic)
    context4 = AdContext(
        unique_id="test4",
        advertiser_id="AR123",
        raw_text="قهوة لاتيه طازجة مع كابتشينو اليوم!",
        product_type="restaurant"
    )

    print("\n--- Test 4: Coffee (Arabic) ---")
    decision4 = classifier.classify(context4)
    print(f"Category: {decision4.food_category}")
    print(f"Confidence: {decision4.confidence}")
    print(f"Signals: {decision4.signals}")


if __name__ == "__main__":
    test_food_category_classifier()
