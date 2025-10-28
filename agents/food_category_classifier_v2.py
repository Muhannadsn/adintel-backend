#!/usr/bin/env python3
"""
Agent 7: Food Category Classifier V2
Enhanced version with:
- Scoring-based conflict resolution (not first-match-wins)
- Granular Arabic categories (Shawarma, Khaliji, Pastries)
- Multi-category support (Family Diner = Mixed Cuisine)
- Evidence-weighted classification
"""

from __future__ import annotations

import requests
import json
from dataclasses import dataclass
from typing import Dict, Optional, List, Tuple
from collections import defaultdict

from .context import AdContext


@dataclass
class FoodCategoryDecision:
    """Result from food category classification"""
    food_category: str
    confidence: float
    reasoning: str
    signals: List[str]
    category_scores: Optional[Dict[str, float]] = None  # All category scores for transparency


# Granular category definitions with weighted keywords
CATEGORY_KEYWORDS = {
    # Burgers & Fast Food
    "Burgers & Fast Food": {
        "keywords": {
            "burger": 3.0, "burgers": 3.0, "برجر": 3.0, "برغر": 3.0,
            "big mac": 4.0, "whopper": 4.0, "cheeseburger": 3.5,
            "fries": 2.0, "بطاطس مقلية": 2.0
        },
        "brands": ["McDonald's", "Burger King", "Five Guys", "Shake Shack", "Smash Me", "Wendy's"]
    },

    # Pizza & Italian
    "Pizza & Italian": {
        "keywords": {
            "pizza": 4.0, "pizzas": 4.0, "بيتزا": 4.0,
            "italian": 3.0, "pasta": 3.0, "باستا": 3.0,
            "margherita": 3.5, "pepperoni": 3.5
        },
        "brands": ["Pizza Hut", "Domino's", "Papa John's"]
    },

    # Mexican & Tex-Mex
    "Mexican & Tex-Mex": {
        "keywords": {
            "taco": 4.0, "tacos": 4.0, "تاكو": 4.0,
            "burrito": 4.0, "بوريتو": 4.0,
            "quesadilla": 4.0, "كيساديا": 4.0,
            "nachos": 3.5, "guacamole": 3.5, "mexican": 3.0, "مكسيكي": 3.0
        },
        "brands": ["Chipotle", "Taco Bell", "Qdoba"]
    },

    # Asian Food
    "Asian Food (Chinese/Thai/Japanese)": {
        "keywords": {
            "sushi": 4.0, "سوشي": 4.0,
            "chinese": 3.0, "صيني": 3.0,
            "thai": 3.5, "تايلندي": 3.5,
            "ramen": 4.0, "راميـن": 4.0,
            "noodles": 2.5, "نودلز": 2.5,
            "wok": 3.0, "teriyaki": 3.5, "تيرياكي": 3.5,
            "pad thai": 4.0, "poke bowl": 3.5
        },
        "brands": ["P.F. Chang's", "Panda Express", "Wagamama"]
    },

    # Shawarma (Specific Middle Eastern subcategory)
    "Shawarma & Street Food": {
        "keywords": {
            "shawarma": 5.0, "شاورما": 5.0,
            "falafel": 3.5, "فلافل": 3.5,
            "street food": 3.0, "طعام شارع": 3.0
        },
        "brands": []
    },

    # Khaliji (Mandi, Madbi, Majboos)
    "Khaliji Cuisine (Mandi/Madbi/Majboos)": {
        "keywords": {
            "mandi": 5.0, "مندي": 5.0,
            "madbi": 5.0, "مضبي": 5.0,
            "majboos": 5.0, "مجبوس": 5.0,
            "kabsa": 4.5, "كبسة": 4.5,
            "khaliji": 4.0, "خليجي": 4.0,
            "rice": 1.5, "رز": 1.5  # Lower weight - too generic
        },
        "brands": []
    },

    # Arabic Pastries
    "Arabic Pastries & Sweets": {
        "keywords": {
            "kunafa": 5.0, "كنافة": 5.0,
            "baklava": 5.0, "بقلاوة": 5.0,
            "qatayef": 4.5, "قطايف": 4.5,
            "arabic sweets": 4.0, "حلويات عربية": 4.0,
            "pastries": 2.0, "معجنات": 2.0  # Lower weight - generic
        },
        "brands": []
    },

    # General Arabic (catch-all for non-specific)
    "Arabic & Middle Eastern": {
        "keywords": {
            "kabab": 3.0, "كباب": 3.0, "kebab": 3.0,
            "hummus": 3.0, "حمص": 3.0,
            "arabic": 2.0, "عربي": 2.0,
            "tabbouleh": 3.0, "تبولة": 3.0,
            "fattoush": 3.0, "فتوش": 3.0,
            "manakish": 3.5, "مناقيش": 3.5
        },
        "brands": ["Zaatar w Zeit"]
    },

    # Fried Chicken
    "Fried Chicken & Fast Food": {
        "keywords": {
            "fried chicken": 4.0, "دجاج مقلي": 4.0,
            "wings": 3.0, "أجنحة": 3.0,
            "crispy": 2.0, "كرسبي": 2.0,
            "tenders": 3.0, "bucket": 3.5
        },
        "brands": ["KFC", "Popeyes", "Texas Chicken", "Jollibee"]
    },

    # Coffee & Beverages
    "Coffee & Beverages": {
        "keywords": {
            "coffee": 3.5, "قهوة": 3.5,
            "latte": 3.0, "لاتيه": 3.0,
            "cappuccino": 3.0, "كابتشينو": 3.0,
            "espresso": 3.0, "اسبريسو": 3.0,
            "frappuccino": 3.5, "mocha": 2.5
        },
        "brands": ["Starbucks", "Costa Coffee", "Dunkin'"]
    },

    # Healthy/Organic (Acai, Smoothies, Salads)
    "Healthy/Organic Food": {
        "keywords": {
            "acai": 5.0, "أساي": 5.0, "açaí": 5.0,
            "superfood": 4.5, "سوبرفود": 4.5,
            "acai bowl": 5.0, "smoothie bowl": 4.5,
            "salad": 3.0, "سلطة": 3.0,
            "vegan": 4.0, "نباتي": 4.0,
            "organic": 3.5, "عضوي": 3.5,
            "kale": 4.0, "quinoa": 4.0, "كينوا": 4.0,
            "detox": 4.0, "ديتوكس": 4.0,
            "cold pressed": 4.5, "green juice": 4.0
        },
        "brands": ["Sweetgreen", "Cava", "Freshii", "Jamba Juice", "Playa Bowls"]
    },

    # Desserts & Sweets
    "Desserts & Sweets": {
        "keywords": {
            "ice cream": 4.0, "آيس كريم": 4.0,
            "dessert": 3.0, "حلويات": 3.0,
            "cake": 3.0, "كيك": 3.0,
            "brownie": 3.5, "براوني": 3.5,
            "donut": 3.5, "دونات": 3.5,
            "gelato": 4.0, "جيلاتو": 4.0
        },
        "brands": ["Baskin Robbins", "Cold Stone", "Dairy Queen", "Krispy Kreme"]
    },

    # Breakfast & Brunch
    "Breakfast & Brunch": {
        "keywords": {
            "breakfast": 4.0, "فطور": 4.0,
            "brunch": 4.0,
            "eggs": 2.5, "بيض": 2.5,
            "pancakes": 3.5, "بان كيك": 3.5,
            "waffle": 3.5, "وافل": 3.5,
            "omelette": 3.0, "أومليت": 3.0
        },
        "brands": ["IHOP", "Denny's", "Waffle House"]
    },

    # Sandwiches & Subs
    "Sandwiches & Subs": {
        "keywords": {
            "sandwich": 3.5, "ساندويتش": 3.5,
            "sub": 3.5, "سب": 3.5,
            "wrap": 3.0, "لفافة": 3.0,
            "panini": 3.5, "بانيني": 3.5
        },
        "brands": ["Subway", "Jimmy John's", "Jersey Mike's"]
    },

    # Mixed Cuisine (Family Diners, Diverse Menus)
    "Mixed Cuisine / Family Dining": {
        "keywords": {
            "family": 2.5, "عائلة": 2.5,
            "diner": 3.0,
            "variety": 2.0, "تنوع": 2.0,
            "menu": 1.0  # Very generic
        },
        "brands": ["The Cheesecake Factory", "Applebee's", "Chili's"]
    }
}


class FoodCategoryClassifier:
    """
    Agent 7 V2: Food Category Classifier with Scoring System

    Key Improvements:
    - Scores ALL categories based on keyword matches
    - Resolves conflicts via evidence weighting
    - Granular Arabic categories (Shawarma, Khaliji, Pastries vs generic Arabic)
    - Supports mixed cuisine detection
    """

    def __init__(
        self,
        ollama_host: str = "http://localhost:11434",
        model: str = "llama3.1:8b",
        score_threshold: float = 3.0,  # Minimum score to consider a category
        mixed_cuisine_threshold: float = 0.7  # If top 2 scores are within this ratio, it's mixed
    ):
        self.ollama_host = ollama_host
        self.model = model
        self.api_url = f"{ollama_host}/api/generate"
        self.score_threshold = score_threshold
        self.mixed_cuisine_threshold = mixed_cuisine_threshold

    def classify(self, context: AdContext) -> Optional[FoodCategoryDecision]:
        """Classify food category using evidence-based scoring"""

        # Only run for restaurants
        if context.product_type != "restaurant":
            return None

        text_lower = (context.raw_text or "").lower()

        # STEP 1: Score all categories
        category_scores = self._score_all_categories(text_lower, context.brand)

        if not category_scores:
            # No keyword matches - fallback to LLM
            return self._classify_with_llm(context)

        # STEP 2: Get top categories
        sorted_categories = sorted(category_scores.items(), key=lambda x: x[1]['score'], reverse=True)
        top_category, top_data = sorted_categories[0]

        # STEP 3: Check for mixed cuisine (multiple high-scoring categories)
        if len(sorted_categories) >= 2:
            second_category, second_data = sorted_categories[1]
            score_ratio = second_data['score'] / top_data['score'] if top_data['score'] > 0 else 0

            if score_ratio >= self.mixed_cuisine_threshold:
                # Mixed cuisine detected
                decision = FoodCategoryDecision(
                    food_category="Mixed Cuisine / Family Dining",
                    confidence=0.80,
                    reasoning=f"Multiple cuisines detected: {top_category} + {second_category}",
                    signals=top_data['keywords'] + second_data['keywords'][:2],
                    category_scores={cat: data['score'] for cat, data in sorted_categories[:3]}
                )
                print(f"   🍽️  Mixed Cuisine: {top_category} ({top_data['score']:.1f}) + {second_category} ({second_data['score']:.1f})")
                return decision

        # STEP 4: Single clear winner
        confidence = min(0.95, 0.70 + (top_data['score'] / 20.0))  # Scale score to confidence

        decision = FoodCategoryDecision(
            food_category=top_category,
            confidence=confidence,
            reasoning=f"Keyword score: {top_data['score']:.1f} from {len(top_data['keywords'])} signals",
            signals=top_data['keywords'][:5],  # Top 5 signals
            category_scores={cat: data['score'] for cat, data in sorted_categories[:3]}
        )

        context.add_evidence(
            agent="FoodCategoryClassifier",
            observation=f"Category: {top_category} (score: {top_data['score']:.1f})",
            confidence=confidence
        )

        print(f"   ⚡ Scored: {top_category} ({top_data['score']:.1f} pts) - {decision.signals[:3]}")

        return decision

    def _score_all_categories(
        self,
        text: str,
        brand: Optional[str]
    ) -> Dict[str, Dict]:
        """Score all categories based on keyword matches and brand"""

        scores = defaultdict(lambda: {'score': 0.0, 'keywords': []})

        for category, data in CATEGORY_KEYWORDS.items():
            # Score based on keywords
            for keyword, weight in data['keywords'].items():
                if keyword in text:
                    scores[category]['score'] += weight
                    scores[category]['keywords'].append(keyword)

            # Bonus for brand match
            if brand and brand in data['brands']:
                scores[category]['score'] += 10.0  # Strong brand signal
                scores[category]['keywords'].insert(0, f"brand:{brand}")

        # Filter out low-scoring categories
        return {
            cat: data for cat, data in scores.items()
            if data['score'] >= self.score_threshold
        }

    def _classify_with_llm(self, context: AdContext) -> FoodCategoryDecision:
        """Fallback to LLM when keywords don't match"""

        text = context.raw_text or ""
        brand_hint = f"Restaurant: {context.brand}" if context.brand else ""

        # Build category list from CATEGORY_KEYWORDS (clean format, no markdown)
        category_list = "\\n".join([f"{i+1}. {cat}" for i, cat in enumerate(CATEGORY_KEYWORDS.keys())])

        prompt = f"""You are analyzing a restaurant advertisement (English or Arabic) to classify the food category.

Advertisement Text:
{text[:800]}

{brand_hint}

Classify into ONE of these categories:
{category_list}

Return VALID JSON (no other text):
{{
    "food_category": "category name",
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation",
    "key_signals": ["signal1", "signal2"]
}}
"""

        print(f"   🤖 LLM fallback classification...")

        try:
            response = requests.post(
                self.api_url,
                json={"model": self.model, "prompt": prompt, "stream": False,
                      "options": {"temperature": 0.1, "num_predict": 256}},
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

            classification = json.loads(response_text[start_idx:end_idx])

            return FoodCategoryDecision(
                food_category=classification.get('food_category', 'Mixed Cuisine / Family Dining'),
                confidence=classification.get('confidence', 0.5),
                reasoning=classification.get('reasoning', ''),
                signals=classification.get('key_signals', [])
            )

        except Exception as e:
            print(f"   ⚠️  LLM failed: {e}")
            return FoodCategoryDecision(
                food_category="Mixed Cuisine / Family Dining",
                confidence=0.3,
                reasoning="Unable to classify - fallback category",
                signals=["llm_failure"]
            )
