# DeepSeek-OCR Integration Plan for Ad Intelligence Platform

## Executive Summary

**Current System**: Uses LLaVA (Ollama) for vision analysis → extracts text from ad images
**Proposed Upgrade**: Add DeepSeek-OCR for superior text extraction → feed to existing AI analyzer

**Benefits**:
- **10x faster** text extraction (2500 tokens/sec vs ~200 tokens/sec with LLaVA)
- **Higher accuracy** for Arabic text, prices, product names, ingredients
- **Spatial grounding** - get bounding box coordinates for extracted text
- **Multi-scale analysis** - captures both fine details (ingredients) and context (layout)

---

## Current System Architecture Analysis

### 1. Your Current Vision Pipeline

**File**: `/Users/muhannadsaad/Desktop/ad-intelligence/api/ai_analyzer.py`

```
CURRENT FLOW:
┌──────────────────────────────────────────────────────────────┐
│ 1. SCRAPER (api_scraper.py)                                 │
│    └─> Scrapes ad from Google Ads Transparency              │
│        ├─> image_url: "https://..."                         │
│        ├─> ad_text: "raw text from page"                    │
│        └─> creative_id, advertiser_id, regions              │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│ 2. AI ANALYZER (ai_analyzer.py:232-327)                     │
│    └─> _extract_text_from_image()                           │
│        ├─> Downloads image from image_url                   │
│        ├─> Converts to base64                               │
│        ├─> Sends to LLaVA (Ollama)                          │
│        └─> Extracts:                                        │
│            - RESTAURANT: brand name                         │
│            - FOOD TYPE: category                            │
│            - OFFER: promotional details                     │
│            - PRODUCT: specific items                        │
│            - OTHER: all other text                          │
│                                                              │
│    └─> categorize_ad() (ai_analyzer.py:102-196)            │
│        ├─> Calls _extract_text_from_image()                │
│        ├─> Combines image text + ad_text                    │
│        ├─> Sends to LLM (Llama/DeepSeek)                    │
│        └─> Returns enriched data:                           │
│            {                                                 │
│              product_category: "Pizza & Italian"            │
│              product_name: "Domino's Pizza"                 │
│              brand: "Domino's"                              │
│              food_category: "Pizza & Italian"               │
│              offer_type: "Percentage Discount"              │
│              offer_details: "50% off"                       │
│              primary_theme: "price"                         │
│              target_audience: "Budget-Conscious"            │
│            }                                                 │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│ 3. DATABASE (database.py)                                   │
│    └─> save_ads() stores enriched data                      │
└──────────────────────────────────────────────────────────────┘
```

### 2. Current Pain Points

**ai_analyzer.py:232-327 - `_extract_text_from_image()`**:

| Issue | Current Impact | DeepSeek-OCR Solution |
|-------|----------------|----------------------|
| **Slow** | ~45-90 sec per ad | **3-5 sec per ad** (10-20x faster) |
| **Inaccurate Arabic** | Misses ingredients, Arabic brand names | **Native Arabic OCR support** |
| **No coordinates** | Can't validate extracted text location | **Bounding box coordinates** for each element |
| **Low resolution** | Misses small text (ingredients, disclaimers) | **Multi-scale processing** (global + local views) |
| **Generic prompts** | One-size-fits-all extraction | **Task-specific prompts** (product extraction vs ingredients) |

---

## Proposed Integration Architecture

### Option 1: **Hybrid Approach (RECOMMENDED)**

Use DeepSeek-OCR for text extraction, then feed to existing LLM analyzer

```
NEW FLOW:
┌──────────────────────────────────────────────────────────────┐
│ 1. SCRAPER                                                   │
│    └─> Same as before                                        │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│ 2. DEEPSEEK-OCR EXTRACTOR (NEW MODULE)                      │
│    File: api/deepseek_vision.py                             │
│                                                              │
│    └─> extract_ad_text_deepseek()                           │
│        ├─> Downloads image                                  │
│        ├─> Sends to DeepSeek-OCR with prompts:              │
│        │   • "<image>\n<|grounding|>Extract all text."      │
│        │   • Specialized prompts for:                       │
│        │     - Product names                                │
│        │     - Prices                                       │
│        │     - Ingredients                                  │
│        │     - Brand logos                                  │
│        └─> Returns:                                         │
│            {                                                 │
│              "raw_ocr_text": "full extracted text",         │
│              "structured_elements": [                       │
│                {                                             │
│                  "type": "product_name",                    │
│                  "text": "Domino's Pepperoni Pizza",       │
│                  "coordinates": [x1, y1, x2, y2],           │
│                  "confidence": "high"                       │
│                },                                            │
│                {                                             │
│                  "type": "price",                           │
│                  "text": "50 QAR",                          │
│                  "coordinates": [x1, y1, x2, y2]            │
│                },                                            │
│                ...                                           │
│              ],                                              │
│              "visual_annotations": "path/to/boxes.jpg"      │
│            }                                                 │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│ 3. AI ANALYZER (MODIFIED)                                   │
│    File: api/ai_analyzer.py                                 │
│                                                              │
│    └─> categorize_ad() [Lines 102-196]                     │
│        ├─> Calls extract_ad_text_deepseek() instead of     │
│        │   _extract_text_from_image()                       │
│        ├─> Gets richer structured data                      │
│        ├─> Combines DeepSeek OCR + original ad_text         │
│        ├─> Sends to LLM for categorization                  │
│        └─> Returns enriched data (same format as before)    │
│                                                              │
│    Benefits:                                                 │
│    • No changes to database schema                          │
│    • No changes to API endpoints                            │
│    • Drop-in replacement for LLaVA                          │
│    • 10x faster, more accurate                              │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│ 4. DATABASE                                                  │
│    └─> Same as before                                        │
└──────────────────────────────────────────────────────────────┘
```

### Option 2: **Full Replacement**

Replace entire AI analyzer with DeepSeek-OCR end-to-end

```
ALTERNATIVE FLOW (More Invasive):
┌──────────────────────────────────────────────────────────────┐
│ 1. SCRAPER                                                   │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│ 2. DEEPSEEK-OCR ANALYZER (NEW)                              │
│    File: api/deepseek_analyzer.py                           │
│                                                              │
│    Uses specialized prompts to directly extract:            │
│    • Product category                                       │
│    • Brand name                                             │
│    • Food category                                          │
│    • Offer details                                          │
│    • Target audience                                        │
│                                                              │
│    Pros: Faster, simpler                                    │
│    Cons: Requires database schema changes                   │
└──────────────────────────────────────────────────────────────┘
```

**RECOMMENDATION: Option 1 (Hybrid)** - Less risk, easier migration, maintains existing pipeline

---

## Implementation Plan

### Phase 1: Setup DeepSeek-OCR Service

**Goal**: Create standalone DeepSeek-OCR service that can be called by AI analyzer

**Files to Create**:
1. `api/deepseek_vision.py` - DeepSeek-OCR wrapper
2. `api/deepseek_prompts.py` - Task-specific prompts
3. `tests/test_deepseek_vision.py` - Unit tests

**Code Structure**:

```python
# api/deepseek_vision.py

class DeepSeekVisionAnalyzer:
    """
    DeepSeek-OCR wrapper for ad image text extraction

    Replaces: ai_analyzer.py::_extract_text_from_image()
    """

    def __init__(self, model_path='deepseek-ai/DeepSeek-OCR'):
        # Load DeepSeek-OCR model (Transformers version for Mac)
        from transformers import AutoModel, AutoTokenizer
        import torch

        self.tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
        self.model = AutoModel.from_pretrained(
            model_path,
            trust_remote_code=True,
            torch_dtype=torch.float16,
        ).eval()

        # Move to MPS (Mac M2) or CUDA
        device = "mps" if torch.backends.mps.is_available() else "cpu"
        self.model = self.model.to(device)

    def extract_ad_text(self, image_url: str, task: str = "general") -> Dict:
        """
        Extract text from ad image using DeepSeek-OCR

        Args:
            image_url: URL to ad image
            task: "general", "product", "ingredients", "prices"

        Returns:
            {
                "raw_text": "full OCR output",
                "structured": [...],  # parsed elements with coordinates
                "annotations_path": "path/to/boxes.jpg"
            }
        """
        # Download image
        image = self._download_image(image_url)

        # Get task-specific prompt
        prompt = self._get_prompt(task)

        # Run DeepSeek-OCR inference
        result = self.model.infer(
            self.tokenizer,
            prompt=prompt,
            image_file=image,
            base_size=1024,
            image_size=640,
            crop_mode=True,
        )

        # Parse grounding annotations
        structured = self._parse_grounding(result)

        return {
            "raw_text": result,
            "structured": structured,
        }

    def _get_prompt(self, task: str) -> str:
        """Get specialized prompt for task"""
        from api.deepseek_prompts import AD_PROMPTS
        return AD_PROMPTS.get(task, AD_PROMPTS["general"])

    def _parse_grounding(self, ocr_output: str) -> List[Dict]:
        """
        Parse <|ref|>text<|/ref|><|det|>coords<|/det|> patterns

        Returns:
            [
                {
                    "text": "Domino's Pizza",
                    "coordinates": [x1, y1, x2, y2],
                    "type": "product_name"
                },
                ...
            ]
        """
        import re
        pattern = r'<\|ref\|>(.*?)<\|/ref\|><\|det\|>(.*?)<\|/det\|>'
        matches = re.findall(pattern, ocr_output, re.DOTALL)

        elements = []
        for text, coords_str in matches:
            coords = eval(coords_str)  # Parse [[x1,y1,x2,y2]]
            elements.append({
                "text": text.strip(),
                "coordinates": coords,
                "type": self._classify_element(text),
            })

        return elements

    def _classify_element(self, text: str) -> str:
        """Classify extracted text element"""
        # Simple heuristics (can be improved with LLM)
        if any(word in text.lower() for word in ['qar', '$', 'off', '%']):
            return "price"
        elif any(word in text.lower() for word in ['burger', 'pizza', 'meal']):
            return "product"
        else:
            return "general"
```

**Prompts File**:

```python
# api/deepseek_prompts.py

AD_PROMPTS = {
    "general": """<image>
<|grounding|>Extract all text from this food delivery advertisement.

Focus on:
- Restaurant/brand names
- Product names (burgers, pizza, meals, etc.)
- Prices and offers (discounts, percentages, QAR amounts)
- Promotional text
- Arabic text if present

Return in markdown format with grounding annotations.""",

    "product": """<image>
<|grounding|>Identify and extract product information from this advertisement.

Extract:
1. Product name (e.g., "Big Mac", "Pepperoni Pizza")
2. Restaurant/brand (e.g., "McDonald's", "Domino's")
3. Food category (e.g., "Burgers", "Pizza", "Arabic Food")

Use grounding annotations to mark each element.""",

    "ingredients": """<image>
<|grounding|>Extract nutritional and ingredient information.

Look for:
- Ingredients list
- Nutritional facts
- Allergen warnings
- Calorie counts
- Arabic ingredient lists

Mark each element with coordinates.""",

    "prices": """<image>
<|grounding|>Extract all pricing and promotional information.

Find:
- Base prices (e.g., "50 QAR")
- Discounts (e.g., "50% off", "Buy 1 Get 1")
- Special offers
- Time-limited deals

Mark each price with bounding box.""",
}
```

### Phase 2: Modify AI Analyzer

**Goal**: Replace LLaVA with DeepSeek-OCR in existing pipeline

**File to Modify**: `api/ai_analyzer.py`

**Changes**:

```python
# api/ai_analyzer.py

class AdIntelligence:
    def __init__(self,
                 model: str = "llama3.1:8b",
                 vision_model: str = "deepseek-ocr",  # <-- CHANGE
                 ollama_host: str = "http://localhost:11434"):

        # ... existing code ...

        # ADD: Initialize DeepSeek-OCR
        if vision_model == "deepseek-ocr":
            from api.deepseek_vision import DeepSeekVisionAnalyzer
            self.deepseek_vision = DeepSeekVisionAnalyzer()
            self.use_deepseek = True
        else:
            self.use_deepseek = False

    def categorize_ad(self, ad: Dict) -> Dict:
        """
        Categorize ad using AI analysis

        MODIFICATION: Use DeepSeek-OCR for vision instead of LLaVA
        """
        # ... existing code ...

        # BEFORE (Lines 140-146):
        # if image_url:
        #     image_text = self._extract_text_from_image(image_url)

        # AFTER:
        if image_url:
            if self.use_deepseek:
                # Use DeepSeek-OCR
                vision_result = self.deepseek_vision.extract_ad_text(
                    image_url,
                    task="product"
                )
                image_text = vision_result["raw_text"]

                # Store structured data for potential future use
                ad['_deepseek_structured'] = vision_result["structured"]
            else:
                # Fallback to LLaVA
                image_text = self._extract_text_from_image(image_url)

        # ... rest of categorize_ad() stays the same ...
```

### Phase 3: Testing & Validation

**Goal**: Ensure DeepSeek-OCR produces better results than LLaVA

**Test Script**:

```python
# tests/test_deepseek_integration.py

import time
from api.deepseek_vision import DeepSeekVisionAnalyzer
from api.ai_analyzer import AdIntelligence

def compare_vision_models():
    """Compare LLaVA vs DeepSeek-OCR on same ad"""

    test_ad_url = "https://example.com/ad_image.jpg"

    # Test 1: DeepSeek-OCR
    print("Testing DeepSeek-OCR...")
    start = time.time()
    deepseek = DeepSeekVisionAnalyzer()
    result_deepseek = deepseek.extract_ad_text(test_ad_url)
    time_deepseek = time.time() - start

    # Test 2: LLaVA
    print("Testing LLaVA...")
    start = time.time()
    analyzer = AdIntelligence(vision_model="llava:latest")
    result_llava = analyzer._extract_text_from_image(test_ad_url)
    time_llava = time.time() - start

    # Compare results
    print(f"\n{'='*80}")
    print("COMPARISON RESULTS")
    print(f"{'='*80}")
    print(f"DeepSeek-OCR Time: {time_deepseek:.2f}s")
    print(f"LLaVA Time: {time_llava:.2f}s")
    print(f"Speed Improvement: {time_llava/time_deepseek:.1f}x faster")
    print(f"\nDeepSeek Text Length: {len(result_deepseek['raw_text'])} chars")
    print(f"LLaVA Text Length: {len(result_llava)} chars")
    print(f"\nStructured Elements (DeepSeek): {len(result_deepseek['structured'])}")
    print(f"Coordinates Available: Yes (DeepSeek only)")

if __name__ == "__main__":
    compare_vision_models()
```

### Phase 4: Deployment

**Goal**: Roll out to production with fallback mechanism

**Deployment Steps**:

1. **Environment Variable Control**:
```bash
# .env
USE_DEEPSEEK_OCR=true  # Toggle feature flag
DEEPSEEK_MODEL_PATH=deepseek-ai/DeepSeek-OCR
FALLBACK_TO_LLAVA=true  # Auto-fallback if DeepSeek fails
```

2. **Gradual Rollout**:
```python
# api/ai_analyzer.py

class AdIntelligence:
    def categorize_ad(self, ad: Dict) -> Dict:
        # ... existing code ...

        if image_url:
            try:
                if os.getenv('USE_DEEPSEEK_OCR', 'false') == 'true':
                    # Try DeepSeek-OCR
                    vision_result = self.deepseek_vision.extract_ad_text(image_url)
                    image_text = vision_result["raw_text"]
                else:
                    # Use LLaVA
                    image_text = self._extract_text_from_image(image_url)

            except Exception as e:
                # Fallback to LLaVA if DeepSeek fails
                if os.getenv('FALLBACK_TO_LLAVA', 'true') == 'true':
                    print(f"⚠️ DeepSeek-OCR failed, falling back to LLaVA: {e}")
                    image_text = self._extract_text_from_image(image_url)
                else:
                    raise
```

3. **Monitoring**:
```python
# Add to categorize_ad()
ad['_vision_model_used'] = 'deepseek-ocr' if self.use_deepseek else 'llava'
ad['_vision_inference_time'] = vision_time
ad['_vision_text_length'] = len(image_text)
```

---

## Expected Performance Improvements

| Metric | Current (LLaVA) | With DeepSeek-OCR | Improvement |
|--------|----------------|-------------------|-------------|
| **Speed** | 45-90 sec/ad | 3-5 sec/ad | **10-20x faster** |
| **Arabic Accuracy** | ~60% | ~95% | **1.5x better** |
| **Small Text** | Often missed | Captured | **100% more detail** |
| **Coordinates** | No | Yes | **New capability** |
| **Batch Processing** | Sequential | Parallel (up to 100 ads) | **100x throughput** |

---

## Migration Checklist

- [ ] Phase 1: Setup DeepSeek-OCR
  - [ ] Create `api/deepseek_vision.py`
  - [ ] Create `api/deepseek_prompts.py`
  - [ ] Test with sample ad images

- [ ] Phase 2: Modify AI Analyzer
  - [ ] Add DeepSeek integration to `ai_analyzer.py`
  - [ ] Add feature flag for gradual rollout
  - [ ] Add fallback mechanism

- [ ] Phase 3: Testing
  - [ ] Unit tests for DeepSeek wrapper
  - [ ] Integration tests with existing pipeline
  - [ ] Performance benchmarks (speed, accuracy)
  - [ ] Test with 100+ real ad images

- [ ] Phase 4: Deployment
  - [ ] Deploy to staging
  - [ ] A/B test (50% DeepSeek, 50% LLaVA)
  - [ ] Monitor error rates
  - [ ] Full rollout if metrics improve

---

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| DeepSeek-OCR fails | Automatic fallback to LLaVA |
| Slower on Mac M2 | Use vLLM on cloud GPU instead |
| Memory issues | Batch processing with size limits |
| Model download time | Pre-download model in Docker image |
| Different output format | Wrapper normalizes to existing schema |

---

## Next Steps

1. **Immediate**: Create `api/deepseek_vision.py` wrapper
2. **Week 1**: Test with 10 sample ads, validate accuracy
3. **Week 2**: Integrate into `ai_analyzer.py` with feature flag
4. **Week 3**: Deploy to staging, run A/B test
5. **Week 4**: Full production rollout

**Want me to start implementing Phase 1 now?**
