# Ad Intelligence Enrichment Pipeline - Agent Blueprint

**Version:** 1.0
**Date:** 2025-01-22
**Status:** Design Phase

---

## Overview

Multi-agent pipeline for extracting strategic intelligence from food delivery advertisements. Each agent has ONE focused task with clear inputs/outputs.

**Core Principle:** Sequential specialized agents > One mega-prompt

---

## Agent Pipeline Flow

```
Raw Ad Image + advertiser_id
    ↓
[Agent 1: Text Extractor] → raw_text
    ↓
[Agent 2: Product Knowledge Lookup] → cached_product_info (if exists)
    ↓
[Agent 3: Subscription Service Detector] → is_subscription + subscription_name
    ↓
[Agent 4: Brand/Restaurant Extractor] → brand_name + confidence
    ↓
[Agent 5: Product Type Classifier] → product_type (restaurant/physical_product/subscription/category)
    ↓
[Agent 6: Web Search Validator] → validated_product_info (only if confidence < 0.7)
    ↓
[Agent 7: Food Category Classifier] → food_category (if restaurant)
    ↓
[Agent 8: Offer Extractor] → offer_type + offer_details
    ↓
[Agent 9: Audience Detector] → target_audience
    ↓
[Agent 10: Theme Analyzer] → messaging_themes (price/speed/quality/convenience)
    ↓
Enriched Ad Data
```

---

## Agent Specifications

### Agent 1: Text Extractor (Vision Model)

**Purpose:** Extract ALL visible text from ad image
**Model:** Llava (local vision model via Ollama)
**Trigger:** Always runs for every ad with an image

**Input:**
```json
{
  "image_url": "https://...",
  "advertiser_id": "AR123..."
}
```

**Output:**
```json
{
  "raw_text": "Nutribullet 9 in 1 Smart Pot 2\nProduct Overview: The Nutribullet Smart Pot 2 is versatile...",
  "extraction_confidence": 0.95,
  "language_detected": "en"
}
```

**Implementation Notes:**
- No interpretation, just raw text extraction
- Include Arabic text if present
- Return empty string if no text found

---

### Agent 2: Product Knowledge Lookup (Database Query)

**Purpose:** Check if product is already known in local cache
**Model:** SQLite query (no AI)
**Trigger:** Always runs after text extraction

**Input:**
```json
{
  "raw_text": "...",
  "extracted_brands": ["Nutribullet", "McDonald's"]  // from quick regex scan
}
```

**Output:**
```json
{
  "cache_hit": true,
  "cached_product": {
    "product_name": "Nutribullet",
    "product_type": "physical_product",
    "is_restaurant": false,
    "is_physical_product": true,
    "category": "Kitchen Appliances",
    "confidence": 0.95,
    "verified_date": "2025-01-20"
  }
}
```

**Implementation Notes:**
- Exact match first, then fuzzy match (LIKE)
- If cache hit, skip Agents 4-6 for this product
- Multiple brands = check each one

---

### Agent 3: Subscription Service Detector (Rule-Based + AI)

**Purpose:** Detect platform subscription ads (Talabat Pro, S Plus, etc.)
**Model:** Rule-based + LLM validation
**Trigger:** Always runs

**Input:**
```json
{
  "raw_text": "...",
  "advertiser_id": "AR14306592000630063105"
}
```

**Output:**
```json
{
  "is_subscription": true,
  "subscription_name": "Talabat Pro",
  "confidence": 0.98,
  "detected_keywords": ["pro", "برو", "subscription"]
}
```

**Subscription Service Map:**
```python
SUBSCRIPTION_SERVICES = {
    "AR14306592000630063105": {
        "platform": "Talabat",
        "subscription_name": "Talabat Pro",
        "keywords": ["talabat pro", "برو", "pro", "talabat برو"]
    },
    "AR12079153035289296897": {
        "platform": "Snoonu",
        "subscription_name": "S Plus",
        "keywords": ["s plus", "snoonu plus", "s+", "snoonu +"]
    },
    "AR08778154730519003137": {
        "platform": "Rafeeq",
        "subscription_name": "Rafeeq Pro",
        "keywords": ["rafeeq pro", "رفيق برو", "rafeeq برو", "pro"]
    }
    # NOTE: Keeta (AR02245493152427278337) has NO subscription service
    # NOTE: Deliveroo dropped from competitive tracking
}
```

**Implementation Notes:**
- Check advertiser_id + keywords in text
- Must see BOTH platform name AND subscription keyword
- If detected → product_type = "Platform Subscription Service"
- Implementation reference: `agents/subscription_detector.py` (Codex, 2025-01-22)

---

### Agent 4: Brand/Restaurant Extractor (NER + LLM)

**Purpose:** Extract brand/restaurant names from text
**Model:** Llama 3.1 8B (local)
**Trigger:** Always runs (unless cache hit from Agent 2)

**Input:**
```json
{
  "raw_text": "McDonald's 50% off Big Mac...",
  "is_subscription": false
}
```

**Output:**
```json
{
  "brands_found": [
    {
      "name": "McDonald's",
      "confidence": 0.95,
      "position": "primary"  // or "secondary", "logo_only"
    }
  ],
  "overall_confidence": 0.95
}
```

**Extraction Rules:**
- Ignore platform names (Talabat, Deliveroo, etc.) UNLESS subscription detected
- Look for: Restaurant chains, local restaurants, product brands
- Check against known restaurant list (expandable)

**Implementation Notes:**
- Return multiple brands if present (e.g., "McDonald's + Coca-Cola")
- Confidence based on: name clarity, position in text, repetition
- Implementation reference: `agents/brand_extractor.py` (Codex, 2025-01-22)
- Supports fuzzy typo recovery and grocery catalog (Lulu, Al Meera, Monoprix, Snoomart, TalabatMart)
- Heuristic backstops detect new merchants via Talabat URL slugs, title-case nouns, and Arabic phrases; outputs flagged as `entity_type="unknown"` for downstream validation
- Advertiser-aware prioritisation: supply `advertiser_brand_map` to boost expected brands, flag conflicts, and infer missing brands from advertiser metadata (`brand_inferred_from_advertiser`, `brand_conflict_with_advertiser`)
- Advertiser → brand hints are loaded from `config/advertiser_brand_map.yaml`; update this file as new electronics/fashion/sports advertisers are added to the KB.

---

### Agent 5: Product Type Classifier (LLM)

**Purpose:** Classify what is being advertised
**Model:** Llama 3.1 8B
**Trigger:** Always runs

**Input:**
```json
{
  "raw_text": "...",
  "brands_found": [...],
  "is_subscription": false
}
```

**Output:**
```json
{
  "product_type": "physical_product",  // or "restaurant", "subscription", "category_promotion"
  "confidence": 0.85,
  "reasoning": "Text describes kitchen appliance features and specifications"
}
```

**Product Types:**
- `restaurant` - Specific restaurant promotion
- `physical_product` - Physical goods (groceries, appliances, etc.)
- `subscription` - Platform subscription service
- `category_promotion` - Multi-restaurant or food category promo

---

### Agent 6: Web Search Validator (Search + LLM)

**Purpose:** Validate unknown products via web search
**Model:** DuckDuckGo + Llama 3.1 8B
**Trigger:** Only when confidence < 0.7 OR unknown brand

**Input:**
```json
{
  "brand_name": "Nutribullet",
  "raw_text": "...",
  "current_confidence": 0.6
}
```

**Process:**
1. Search: "What is [brand_name]"
2. Get top 3 results (titles + snippets)
3. Feed to LLM: "Based on these search results, is this a restaurant or product?"

**Output:**
```json
{
  "validated_type": "physical_product",
  "validated_category": "Kitchen Appliances",
  "is_restaurant": false,
  "is_physical_product": true,
  "confidence": 0.95,
  "search_source": "duckduckgo",
  "cache_this": true  // Save to product_knowledge table
}
```

**Implementation Notes:**
- Cache all validated results to avoid repeat searches
- Timeout: 10 seconds max
- Fallback: If search fails, use Agent 5 classification

---

### Agent 7: Food Category Classifier (LLM)

**Purpose:** Classify food type if restaurant detected
**Model:** Llama 3.1 8B
**Trigger:** Only if product_type == "restaurant"

**Input:**
```json
{
  "restaurant_name": "McDonald's",
  "raw_text": "50% off Big Mac..."
}
```

**Output:**
```json
{
  "food_category": "Burgers & Fast Food",
  "confidence": 0.95
}
```

**Food Categories:**
```python
FOOD_CATEGORIES = [
    "Platform Subscription Service",
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
]
```

---

### Agent 8: Offer Extractor (Regex + LLM)

**Purpose:** Extract promotional offers and deals
**Model:** Regex patterns + Llama 3.1 8B for complex offers
**Trigger:** Always runs

**Input:**
```json
{
  "raw_text": "50% off your first order..."
}
```

**Output:**
```json
{
  "offer_type": "percentage_discount",
  "offer_details": "50% off first order",
  "offer_conditions": "new customers only",
  "confidence": 0.9
}
```

**Offer Types:**
- `percentage_discount` - "50% off", "30% discount"
- `fixed_discount` - "QAR 20 off", "$10 discount"
- `free_delivery` - "Free delivery"
- `bogo` - "Buy 1 Get 1 Free"
- `limited_time` - "Today only", "Limited time"
- `new_product` - "New item launch"
- `none` - No offer detected

---

### Agent 9: Audience Detector (LLM)

**Purpose:** Identify target audience segment
**Model:** Llama 3.1 8B
**Trigger:** Always runs

**Input:**
```json
{
  "raw_text": "...",
  "offer_details": "50% off first order",
  "product_category": "Burgers & Fast Food"
}
```

**Output:**
```json
{
  "target_audience": "New Customers",
  "confidence": 0.85,
  "signals": ["first order", "new customer"]
}
```

**Audience Segments:**
```python
AUDIENCE_SEGMENTS = [
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
```

---

### Agent 10: Theme Analyzer (LLM)

**Purpose:** Analyze messaging themes and priorities
**Model:** Llama 3.1 8B
**Trigger:** Always runs (final agent)

**Input:**
```json
{
  "raw_text": "...",
  "offer_details": "50% off"
}
```

**Output:**
```json
{
  "messaging_themes": {
    "price": 0.9,      // Strong emphasis on discounts
    "speed": 0.3,      // Mentions "fast delivery"
    "quality": 0.1,    // No quality mentions
    "convenience": 0.4 // Mentions "easy ordering"
  },
  "primary_theme": "price",
  "confidence": 0.85
}
```

**Theme Definitions:**
- `price` - Discounts, savings, value, deals
- `speed` - Fast delivery, quick service, express
- `quality` - Premium, fresh, high-quality, best
- `convenience` - Easy, simple, 24/7, accessible

---

## Final Enriched Output Schema

```json
{
  // Original data
  "advertiser_id": "AR14306592000630063105",
  "advertiser_name": "Talabat",
  "image_url": "https://...",
  "ad_text": "Original scraped text",

  // Agent 1 output
  "extracted_text": "Full text extracted from image",

  // Agent 2 output
  "cached_from_kb": true,

  // Agent 3 output
  "is_subscription": false,

  // Agent 4 output
  "extracted_brands": ["Nutribullet"],

  // Agent 5 + 6 outputs
  "product_type": "physical_product",
  "product_category": "Grocery Delivery",
  "product_name": "Nutribullet 9-in-1 Smart Pot 2",

  // Agent 7 output (if restaurant)
  "food_category": null,

  // Agent 8 output
  "offer_type": "none",
  "offer_details": "",

  // Agent 9 output
  "target_audience": "General Audience",

  // Agent 10 output
  "messaging_themes": {
    "price": 0.2,
    "speed": 0.3,
    "quality": 0.8,
    "convenience": 0.6
  },
  "primary_theme": "quality",

  // Metadata
  "confidence_score": 0.92,
  "analyzed_at": "2025-01-22T10:30:00Z",
  "analysis_model": "llama3.1:8b",
  "agents_used": [1, 2, 4, 5, 6, 8, 9, 10],
  "validation_source": "web_search"
}
```

---

## Implementation Priority

### Phase 1: Core Pipeline (Agents 1-6)
1. ✅ Agent 1: Text Extractor (already exists - Llava)
2. ✅ Agent 2: Product Knowledge Lookup (database methods added)
3. ⏳ Agent 3: Subscription Detector
4. ⏳ Agent 4: Brand Extractor
5. ⏳ Agent 5: Product Type Classifier
6. ⏳ Agent 6: Web Search Validator

### Phase 2: Enrichment Agents (Agents 7-10)
7. Agent 7: Food Category Classifier
8. Agent 8: Offer Extractor
9. Agent 9: Audience Detector
10. Agent 10: Theme Analyzer

---

## Testing Strategy

**Test Ad Examples:**

1. **Nutribullet Ad** (Physical Product)
   - Should detect: physical_product, not restaurant
   - Should search web and cache result

2. **Talabat Pro Ad** (Subscription)
   - Should detect: subscription service
   - Should NOT confuse with restaurant

3. **McDonald's 50% Off** (Restaurant Promo)
   - Should detect: restaurant, Burgers & Fast Food
   - Should extract: 50% discount offer

4. **Multi-Restaurant Banner** (Category Promo)
   - Should detect: category_promotion
   - Should list multiple brands

---

## Performance Targets

- **Speed:** < 30 seconds per ad (including web search)
- **Accuracy:** > 90% on known products
- **Cache Hit Rate:** > 70% after first week
- **Web Search Rate:** < 20% of ads

---

## Next Steps

1. Build Agent 3 (Subscription Detector)
2. Build Agent 4 (Brand Extractor)
3. Build Agent 6 (Web Validator with DuckDuckGo)
4. Test on 10 sample ads
5. Iterate based on results

---

**Blueprint Status:** APPROVED - Ready for Implementation
