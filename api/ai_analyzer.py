#!/usr/bin/env python3
"""
AI Analyzer Service - Extracts strategic intelligence from raw ad data
Uses LOCAL Ollama models (DeepSeek, Llama, Llava) for analysis
"""

import os
import json
import requests
from typing import List, Dict, Optional
from datetime import datetime


class AdIntelligence:
    """
    Extracts strategic intelligence from raw ad data using local Ollama models

    Capabilities:
    - Product categorization (Meal Deals, Grocery, Restaurant, etc.)
    - Messaging theme analysis (Price, Speed, Quality, Convenience)
    - Audience segment detection (Young Professionals, Families, etc.)
    - Offer type identification (Discount%, Free Delivery, etc.)
    """

    def __init__(self,
                 model: str = "llama3.1:8b",
                 vision_model: str = "llava:latest",
                 ollama_host: str = "http://localhost:11434"):
        """
        Initialize with local Ollama models

        Args:
            model: Text analysis model (deepseek-r1, llama3.1, etc.)
            vision_model: Image analysis model (llava)
            ollama_host: Ollama API endpoint
        """
        self.model = model
        self.vision_model = vision_model
        self.ollama_host = ollama_host
        self.api_url = f"{ollama_host}/api/generate"

        # Product categories (food + multi-vertical retail)
        self.product_categories = [
            "Platform Subscription Service",  # For Talabat Pro, Deliveroo Plus, etc.
            "Pizza & Italian",
            "Burgers & Fast Food",
            "Asian Food (Chinese/Thai/Japanese)",
            "Arabic & Middle Eastern",
            "Meal Deals & Combos",
            "Breakfast & Brunch",
            "Desserts & Sweets",
            "Coffee & Beverages",
            "Grocery Delivery",
            "Pharmacy & Health",
            "Convenience Store",
            "Premium/Fine Dining",
            "Healthy/Organic Food",
            "Late Night Food",
            "Specific Restaurant/Brand Promo",
            "Consumer Electronics",
            "Smartphones & Tablets",
            "Home Appliances",
            "Fashion & Accessories",
            "Sports & Outdoors Equipment"
            # NOTE: "Other" and "General" removed - AI MUST pick a specific category
        ]

        # Audience segments
        self.audience_segments = [
            "Young Professionals (25-34)",
            "Families (35-50)",
            "Students (18-24)",
            "Late-night Users",
            "Health-Conscious",
            "Budget-Conscious",
            "Premium Seekers",
            "New Customers",
            "Existing Customers",
            "General Audience"
        ]

        # Test connection
        self._test_connection()

    def _test_connection(self):
        """Test if Ollama is running and models are available"""
        try:
            response = requests.get(f"{self.ollama_host}/api/tags", timeout=2)
            if response.status_code == 200:
                models = response.json().get('models', [])
                available_models = [m['name'] for m in models]

                if self.model not in available_models:
                    print(f"⚠️  Warning: Model '{self.model}' not found. Available: {available_models}")
                    print(f"   Using fallback mode or download with: ollama pull {self.model}")
                else:
                    print(f"✅ Connected to Ollama - Using model: {self.model}")
        except requests.exceptions.RequestException as e:
            print(f"⚠️  Warning: Cannot connect to Ollama at {self.ollama_host}")
            print(f"   Make sure Ollama is running: ollama serve")
            print(f"   Will use fallback keyword matching")

    def categorize_ad(self, ad: Dict) -> Dict:
        """
        Analyze single ad and extract intelligence

        Args:
            ad: Dict with keys: ad_text, image_url, advertiser_id, regions

        Returns:
            Original ad dict + enriched fields:
            - product_category: str
            - product_name: str
            - messaging_themes: dict with confidence scores
            - primary_theme: str
            - audience_segment: str
            - offer_type: str
            - offer_details: str
            - confidence_score: float
        """
        try:
            ad_text = ad.get('ad_text', '')
            image_url = ad.get('image_url', '')

            if not ad_text and not image_url:
                return self._create_fallback_enrichment(ad, "No ad text or image provided")

            # 🔍 VISION EXTRACTION: If we have an image but no/poor text, use vision model
            extracted_text = ""
            if image_url and (not ad_text or ad_text == "Unknown"):
                try:
                    extracted_text = self._extract_text_from_image(image_url)
                    if extracted_text:
                        # 🎯 POST-PROCESSING: Detect subscription service ads (PLATFORM-AWARE!)
                        advertiser_id = ad.get('advertiser_id', '')

                        # Map advertiser IDs to platform names
                        platform_map = {
                            'AR14306592000630063105': 'Talabat Pro',
                            'AR02245493152427278337': 'Keeta Pro',
                            'AR08778154730519003137': 'Rafiq Pro',
                            'AR12079153035289296897': 'Snoonu Pro'
                        }

                        platform_name = platform_map.get(advertiser_id, 'Unknown Platform Pro')

                        subscription_keywords = ['pro', 'برو', 'plus', 'subscription', 'اشتراك', 'premium']
                        extracted_lower = extracted_text.lower()

                        is_subscription_ad = any(keyword in extracted_lower for keyword in subscription_keywords)

                        if is_subscription_ad:
                            # Use CORRECT platform name based on advertiser ID
                            ad_text = f"SUBSCRIPTION_SERVICE: {platform_name}\n\n{extracted_text}"
                            print(f"   🔔 Detected subscription service ad ({platform_name})")
                        else:
                            ad_text = extracted_text

                        print(f"   📸 Extracted text from image: {extracted_text[:80]}...")
                except Exception as e:
                    print(f"   ⚠️  Vision extraction failed: {e}")

            # Build prompt for local model
            prompt = self._build_analysis_prompt(ad_text, image_url)

            # Call Ollama API
            response = self._call_ollama(prompt)

            # Parse response
            analysis = self._parse_response(response)

            # Add extracted text to the enriched ad
            if extracted_text:
                analysis['extracted_text'] = extracted_text

            # 📍 QATAR DETECTION: Check if ad is Qatar-specific
            text_to_analyze = extracted_text or ad_text or ''
            analysis['is_qatar_only'] = self._detect_qatar_region(text_to_analyze)

            # Merge with original ad
            enriched_ad = {
                **ad,
                **analysis,
                'analyzed_at': datetime.now().isoformat(),
                'analysis_model': self.model
            }

            return enriched_ad

        except Exception as e:
            print(f"⚠️  Error analyzing ad: {e}")
            return self._create_fallback_enrichment(ad, str(e))

    def batch_analyze(self, ads: List[Dict], batch_size: int = 10) -> List[Dict]:
        """
        Efficiently analyze multiple ads with progress tracking

        Args:
            ads: List of ad dicts
            batch_size: Show progress every N ads (default: 10)

        Returns:
            List of enriched ads
        """
        enriched_ads = []
        total = len(ads)

        print(f"🤖 Starting AI analysis of {total} ads with {self.model}...")

        for i, ad in enumerate(ads, 1):
            try:
                enriched = self.categorize_ad(ad)
                enriched_ads.append(enriched)

                # Show progress every batch_size ads
                if i % batch_size == 0 or i == total:
                    progress = (i / total) * 100
                    print(f"   Progress: {i}/{total} ads analyzed ({progress:.1f}%)")

            except Exception as e:
                print(f"⚠️  Failed to analyze ad {i}: {e}")
                # Add ad with error flag
                enriched_ads.append({
                    **ad,
                    'enrichment_error': str(e),
                    'analyzed_at': datetime.now().isoformat()
                })

        print(f"✅ Analysis complete! {len(enriched_ads)} ads processed.")
        return enriched_ads

    def _extract_text_from_image(self, image_url: str, timeout: int = 60) -> str:
        """
        Extract text from ad image using Llava vision model

        Args:
            image_url: URL to the ad image
            timeout: Request timeout (vision models are slower)

        Returns:
            Extracted text from the image
        """
        try:
            # Download image
            import base64
            from io import BytesIO

            img_response = requests.get(image_url, timeout=10)
            if img_response.status_code != 200:
                raise Exception(f"Failed to download image: {img_response.status_code}")

            # Convert to base64
            img_data = base64.b64encode(img_response.content).decode('utf-8')

            # Prompt for vision model
            vision_prompt = """You are analyzing a food delivery advertisement image (likely from Talabat, Deliveroo, Keeta, Snoonu, Rafiq, or similar platforms).

⚠️ CRITICAL - AVOID PLATFORM NAME CONTAMINATION:
- Platforms like "Talabat", "Deliveroo", "Keeta", "Snoonu", "Rafiq" are DELIVERY SERVICES, NOT restaurants
- DO NOT extract these platform names as restaurant/product names UNLESS it's explicitly a platform subscription ad
- Only extract as product if you see: "Talabat Pro", "برو" (Pro), "Deliveroo Plus", "Premium Subscription"

IMPORTANT - SUBSCRIPTION SERVICE DETECTION:
- If you see "Talabat Pro", "برو" (Pro in Arabic), "Deliveroo Plus", or similar subscription service names, this is a SUBSCRIPTION AD
- Return "SUBSCRIPTION_SERVICE" as the restaurant name
- EXCEPTION: Plain "Talabat", "Deliveroo", "Keeta" logos WITHOUT "Pro"/"Plus" are just platform branding, NOT the product

Extract the following information from the image:

1. RESTAURANT/BRAND NAME: The actual restaurant or food brand being advertised
   - ❌ NEVER extract: "Talabat", "Deliveroo", "Keeta", "Snoonu", "Rafiq" (these are platforms, not products)
   - ✅ ONLY extract subscription services: "Talabat Pro", "Deliveroo Plus" → Return "SUBSCRIPTION_SERVICE"
   - ✅ Extract actual restaurants: "McDonald's", "Pizza Hut", "Burger King", "Paul", "Haldiram's", etc.
   - If no specific restaurant found: Return "Unknown"

2. FOOD TYPE/CATEGORY: What kind of food is shown or mentioned?
   - Examples: Pizza, Burgers, Arabic Food, Asian Food, Breakfast, Desserts, etc.
   - For subscription ads: Note the food category shown in the image

3. PROMOTIONAL OFFER: Any discounts, deals, or special offers
   - Examples: "50% off", "Buy 1 Get 1", "Free Delivery", specific prices
   - Include time-based offers (e.g., "40% off from 12pm-3pm")

4. PRODUCT NAME: Specific items or meal names if visible
   - Examples: "Big Mac", "Pepperoni Pizza", "Family Meal Deal"
   - ❌ DO NOT include platform names here

5. OTHER TEXT: Any additional text visible in the image
   - Include Arabic text if present
   - Include platform branding mentions (for context only)
   - Include ALL promotional text, slogans, and descriptions

Format your response as:
RESTAURANT: [name or "Unknown" or "SUBSCRIPTION_SERVICE"]
FOOD TYPE: [category]
OFFER: [deal details or "None"]
PRODUCT: [specific item or "General"]
OTHER: [List ALL other visible text including platform mentions, Arabic text, slogans, etc.]"""

            # Call Ollama vision API
            payload = {
                "model": self.vision_model,
                "prompt": vision_prompt,
                "images": [img_data],
                "stream": False,
                "options": {
                    "temperature": 0.1,  # Very low for accurate text extraction
                    "num_predict": 512
                }
            }

            response = requests.post(
                self.api_url,
                json=payload,
                timeout=timeout
            )

            if response.status_code != 200:
                raise Exception(f"Vision API error: {response.status_code}")

            result = response.json()
            extracted_text = result.get('response', '').strip()

            return extracted_text

        except Exception as e:
            raise Exception(f"Image text extraction failed: {e}")

    def _call_ollama(self, prompt: str, timeout: int = 30) -> str:
        """
        Call Ollama API with the given prompt

        Args:
            prompt: The analysis prompt
            timeout: Request timeout in seconds

        Returns:
            Model response text
        """
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,  # Lower for more consistent categorization
                    "num_predict": 1024   # Max tokens
                }
            }

            response = requests.post(
                self.api_url,
                json=payload,
                timeout=timeout
            )

            if response.status_code != 200:
                raise Exception(f"Ollama API error: {response.status_code} - {response.text}")

            result = response.json()
            return result.get('response', '')

        except requests.exceptions.Timeout:
            raise Exception(f"Ollama request timed out after {timeout}s")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Ollama request failed: {e}")

    def _build_analysis_prompt(self, ad_text: str, image_url: str) -> str:
        """
        Construct structured prompt for local model

        Args:
            ad_text: The ad copy/text
            image_url: URL to ad image (if available)

        Returns:
            Formatted prompt string
        """
        prompt = f"""You are an expert in analyzing food delivery and e-commerce advertisements.

Analyze this advertisement and extract strategic intelligence in JSON format.

AD TEXT (extracted from image or ad copy):
{ad_text}

CRITICAL INSTRUCTIONS - READ CAREFULLY:

⚠️ RULE #0 - AVOID PLATFORM NAME CONTAMINATION (HIGHEST PRIORITY):
   - ❌ NEVER extract these platform names as products: "Talabat", "Deliveroo", "Keeta", "Snoonu", "Rafiq"
   - These are DELIVERY PLATFORMS, not restaurants or products
   - If you see "Talabat" logo → This means "delivered by Talabat", NOT "product is Talabat"
   - ✅ EXCEPTION: "Talabat Pro", "Deliveroo Plus" ARE products (subscription services)

1. RESTAURANT/BRAND NAME EXTRACTION:
   - Search AGGRESSIVELY for ANY brand, restaurant, or company name in the text
   - Common names to look for: McDonald's, Burger King, KFC, Pizza Hut, Subway, Starbucks, Domino's, Haldiram's, Paul, Swirky's, TBS, etc.
   - Check Arabic text for restaurant names written in Arabic
   - ❌ IGNORE: "Talabat", "Deliveroo", "Keeta", "Snoonu", "Rafiq" (these are platforms, NOT products)
   - If you find ANY brand name → Use "Specific Restaurant/Brand Promo" as category
   - product_name MUST be: "RestaurantName - FoodCategory" (e.g., "Haldiram's - Indian Food", "Paul - Bakery")

2. SUBSCRIPTION SERVICE DETECTION:
   - If you see "SUBSCRIPTION_SERVICE:" at the start, extract the EXACT platform name that follows
   - Examples: "Talabat Pro", "Keeta Pro", "Deliveroo Plus", "Rafiq Pro", "Snoonu Pro"
   - ⚠️ USE THE EXACT NAME PROVIDED - do NOT change "Keeta Pro" to "Talabat Pro"!
     → category: "Platform Subscription Service"
     → product_name: [EXACT platform name from SUBSCRIPTION_SERVICE line]
   - Note: Plain "Talabat" without "Pro" is just platform branding, NOT a subscription service

3. NO GENERIC NAMES ALLOWED:
   - NEVER use: "Unknown", "Food Delivery Deal", "First Order Discount", "Arabic Food Promotion"
   - ❌ NEVER use platform names as product names: "Talabat", "Deliveroo", "Keeta"
   - If no restaurant found → Look at food type and be SPECIFIC
   - Examples: "Premium Burger Deal", "Arabic Mezze Platter", "Pizza Margherita Offer"

4. FOOD TYPE CATEGORIZATION (if no restaurant):
   - Look at what food is shown/mentioned
   - Categories available: {', '.join(self.product_categories)}
   - Pick the MOST SPECIFIC category, never use generic fallbacks

5. NON-FOOD ADS (Electronics/Fashion/Sports):
   - Use the dedicated categories in the list above, e.g., "Consumer Electronics", "Smartphones & Tablets",
     "Home Appliances", "Fashion & Accessories", "Sports & Outdoors Equipment"
   - Always mention the specific product line (e.g., "Samsung Galaxy S24" → Smartphones & Tablets)

Extract the following information and return ONLY valid JSON (no explanation text):

1. product_category: MUST be one of: {', '.join(self.product_categories)}
   - Use "Specific Restaurant/Brand Promo" if ANY restaurant/brand name found
   - Otherwise pick the specific food type category

2. product_name: MUST BE SPECIFIC!
   - If restaurant/brand mentioned: "BrandName - FoodType" (e.g., "Haldiram's - Indian", "Paul - French Bakery")
   - If no brand: Specific food item (e.g., "Margherita Pizza Special", "Chicken Shawarma Combo", "Premium Burger Meal")

3. messaging_themes: Confidence scores 0.0-1.0 for:
   - price: Discounts, savings, value mentions
   - speed: Fast delivery, quick service mentions
   - quality: Premium, fresh, high-quality mentions
   - convenience: Easy, simple, accessible mentions

4. primary_theme: Most dominant theme (price/speed/quality/convenience)

5. audience_segment: Target audience. Options: {', '.join(self.audience_segments)}

6. offer_type: Promotion type - percentage_discount, fixed_discount, free_delivery, bogo, limited_time, new_product, or none

7. offer_details: Specific offer text (e.g., "50% off first order", "Buy 1 Get 1 Free")

8. confidence_score: Overall confidence 0.0-1.0

Return ONLY this JSON structure (no other text):
{{
    "product_category": "...",
    "product_name": "...",
    "messaging_themes": {{"price": 0.0, "speed": 0.0, "quality": 0.0, "convenience": 0.0}},
    "primary_theme": "...",
    "audience_segment": "...",
    "offer_type": "...",
    "offer_details": "...",
    "confidence_score": 0.0
}}
"""
        return prompt

    def _parse_response(self, response_text: str) -> Dict:
        """
        Parse model's JSON response into structured dict

        Args:
            response_text: Raw response from Ollama

        Returns:
            Parsed dict with enrichment fields
        """
        try:
            # Clean up response - remove markdown formatting if present
            cleaned = response_text.strip()

            # Remove markdown code blocks
            if cleaned.startswith('```'):
                lines = cleaned.split('\n')
                # Remove first line (```json or ```) and last line (```)
                cleaned = '\n'.join(lines[1:-1])

            # Try to extract JSON from response
            start_idx = cleaned.find('{')
            end_idx = cleaned.rfind('}') + 1

            if start_idx == -1 or end_idx == 0:
                raise ValueError("No JSON found in response")

            json_str = cleaned[start_idx:end_idx]
            analysis = json.loads(json_str)

            # Validate required fields
            required_fields = [
                'product_category',
                'messaging_themes',
                'primary_theme',
                'offer_type'
            ]

            for field in required_fields:
                if field not in analysis:
                    print(f"⚠️  Missing field '{field}', using default")
                    if field == 'messaging_themes':
                        analysis[field] = {"price": 0.0, "speed": 0.0, "quality": 0.0, "convenience": 0.0}
                    elif field == 'primary_theme':
                        analysis[field] = 'convenience'
                    else:
                        analysis[field] = 'Other' if field == 'product_category' else 'none'

            # Ensure optional fields have defaults
            analysis.setdefault('product_name', 'Unknown')
            analysis.setdefault('audience_segment', 'General Audience')
            analysis.setdefault('offer_details', '')
            analysis.setdefault('confidence_score', 0.7)

            return analysis

        except json.JSONDecodeError as e:
            print(f"⚠️  JSON parsing error: {e}")
            print(f"Response was: {response_text[:200]}...")
            raise
        except Exception as e:
            print(f"⚠️  Error parsing response: {e}")
            raise

    def _detect_qatar_region(self, text: str) -> bool:
        """
        Detect if ad is Qatar-specific or from other regions (UAE, etc.)

        Args:
            text: Ad text or extracted text from image

        Returns:
            True if Qatar-only, False if UAE/other regions detected
        """
        if not text:
            return True  # Default to Qatar if no text

        text_lower = text.lower()

        # UAE indicators (if found, NOT Qatar-only)
        uae_indicators = [
            'dubai', 'abu dhabi', 'sharjah', 'ajman', 'دبي', 'أبوظبي', 'الشارقة',
            'aed', 'dhs', 'dirham',  # UAE currency
            '+971',  # UAE phone code
            'uae', 'u.a.e', 'emirates',
            'in dub',  # "in Dubai" shorthand
            'jbr', 'downtown dubai', 'marina', 'jumeirah'  # Dubai locations
        ]

        # Qatar indicators (if found, likely Qatar-only)
        qatar_indicators = [
            'qatar', 'doha', 'الدوحة', 'قطر',
            'qar', 'riyal',  # Qatar currency
            '+974',  # Qatar phone code
            'west bay', 'the pearl', 'lusail', 'katara',  # Qatar locations
            'aspire', 'villagio', 'city center doha'  # Qatar malls
        ]

        # Check for UAE indicators first (disqualifies Qatar-only)
        for indicator in uae_indicators:
            if indicator in text_lower:
                print(f"   🌍 Non-Qatar region detected: '{indicator}'")
                return False  # NOT Qatar-only

        # Check for Qatar indicators (confirms Qatar)
        qatar_found = False
        for indicator in qatar_indicators:
            if indicator in text_lower:
                qatar_found = True
                break

        # Default: assume Qatar if no explicit region found
        # (Since we scraped with region=QA parameter)
        return True

    def _create_fallback_enrichment(self, ad: Dict, error: str) -> Dict:
        """
        Create basic enrichment when AI analysis fails
        Uses simple keyword matching as fallback

        Args:
            ad: Original ad dict
            error: Error message

        Returns:
            Ad with basic enrichment
        """
        ad_text = ad.get('ad_text', '').lower()

        # Simple keyword-based categorization (MUST be specific!)
        product_category = "Meal Deals & Combos"  # Default fallback (instead of "Other")
        if any(word in ad_text for word in ['pizza', 'italian']):
            product_category = "Pizza & Italian"
        elif any(word in ad_text for word in ['burger', 'fast food', 'fries']):
            product_category = "Burgers & Fast Food"
        elif any(word in ad_text for word in ['grocery', 'supermarket', 'essentials']):
            product_category = "Grocery Delivery"
        elif any(word in ad_text for word in ['pharmacy', 'medicine', 'health']):
            product_category = "Pharmacy & Health"
        elif any(word in ad_text for word in ['arabic', 'shawarma', 'kebab', 'mezze']):
            product_category = "Arabic & Middle Eastern"
        elif any(word in ad_text for word in ['meal', 'food', 'lunch', 'dinner', 'restaurant']):
            product_category = "Meal Deals & Combos"
        elif any(word in ad_text for word in ['smartphone', 'iphone', 'android', 'laptop', 'gaming pc', 'electronics', 'gadget', 'tablet', 'headphone']):
            product_category = "Smartphones & Tablets" if 'phone' in ad_text or 'tablet' in ad_text else "Consumer Electronics"
        elif any(word in ad_text for word in ['appliance', 'air conditioner', 'fridge', 'washing machine', 'microwave', 'vacuum', 'oven']):
            product_category = "Home Appliances"
        elif any(word in ad_text for word in ['fashion', 'dress', 'shirt', 'abaya', 'shoe', 'sneaker', 'bag', 'accessories', 'jewelry', 'hoodie']):
            product_category = "Fashion & Accessories"
        elif any(word in ad_text for word in ['sports', 'outdoor', 'gym', 'fitness', 'yoga', 'treadmill', 'bike', 'cycling']):
            product_category = "Sports & Outdoors Equipment"

        # Detect primary theme
        themes = {
            'price': 0.0,
            'speed': 0.0,
            'quality': 0.0,
            'convenience': 0.0
        }

        if any(word in ad_text for word in ['%', 'off', 'discount', 'save', 'deal', 'free']):
            themes['price'] = 0.7
        if any(word in ad_text for word in ['fast', 'quick', 'minutes', 'instant', 'now']):
            themes['speed'] = 0.6
        if any(word in ad_text for word in ['premium', 'quality', 'fresh', 'best']):
            themes['quality'] = 0.5
        if any(word in ad_text for word in ['easy', 'convenient', 'simple', '24/7']):
            themes['convenience'] = 0.5

        primary_theme = max(themes, key=themes.get) if max(themes.values()) > 0 else 'convenience'

        # Detect offer
        offer_type = "none"
        offer_details = ""
        if '%' in ad_text and 'off' in ad_text:
            offer_type = "percentage_discount"
            import re
            match = re.search(r'(\d+)%\s*off', ad_text)
            if match:
                offer_details = f"{match.group(1)}% off"
        elif 'free delivery' in ad_text:
            offer_type = "free_delivery"
            offer_details = "Free delivery"

        return {
            **ad,
            'product_category': product_category,
            'product_name': 'Unknown',
            'messaging_themes': themes,
            'primary_theme': primary_theme,
            'audience_segment': 'General Audience',
            'offer_type': offer_type,
            'offer_details': offer_details,
            'confidence_score': 0.3,  # Low confidence for fallback
            'enrichment_error': error,
            'enrichment_method': 'fallback',
            'analyzed_at': datetime.now().isoformat()
        }


# ============================================================================
# Utility Functions
# ============================================================================

def test_analyzer():
    """
    Test the AI analyzer with sample ad data
    """
    # Sample ads for testing
    sample_ads = [
        {
            'ad_text': 'Get 50% off your first order! Fast delivery in 15 minutes. Order now from Talabat.',
            'image_url': '',
            'advertiser_id': 'AR14306592000630063105',
            'regions': 'QA'
        },
        {
            'ad_text': 'Premium restaurant-quality meals delivered to your door. Fresh ingredients, chef-prepared.',
            'image_url': '',
            'advertiser_id': 'AR13676304484790173697',
            'regions': 'QA'
        },
        {
            'ad_text': 'Order groceries in 3 easy taps. Everyday essentials at your fingertips. 24/7 availability.',
            'image_url': '',
            'advertiser_id': 'AR08778154730519003137',
            'regions': 'QA'
        }
    ]

    print("=" * 70)
    print("Testing AI Analyzer with Ollama Local Models")
    print("=" * 70)

    analyzer = AdIntelligence()

    for i, sample_ad in enumerate(sample_ads, 1):
        print(f"\n{'='*70}")
        print(f"TEST AD {i}")
        print(f"{'='*70}")
        print(f"Text: {sample_ad['ad_text']}\n")

        enriched = analyzer.categorize_ad(sample_ad)

        print("Analysis Result:")
        print(f"  Product Category: {enriched.get('product_category')}")
        print(f"  Product Name: {enriched.get('product_name')}")
        print(f"  Primary Theme: {enriched.get('primary_theme')}")
        print(f"  Messaging Themes:")
        for theme, score in enriched.get('messaging_themes', {}).items():
            print(f"    - {theme}: {score:.2f}")
        print(f"  Audience: {enriched.get('audience_segment')}")
        print(f"  Offer Type: {enriched.get('offer_type')}")
        print(f"  Offer Details: {enriched.get('offer_details')}")
        print(f"  Confidence: {enriched.get('confidence_score', 0):.2f}")
        print(f"  Model: {enriched.get('analysis_model', 'fallback')}")

    print(f"\n{'='*70}")
    print("Test Complete!")
    print(f"{'='*70}")


if __name__ == "__main__":
    # Run test when executed directly
    test_analyzer()
