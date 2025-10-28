#!/usr/bin/env python3
"""
ORCHESTRATOR: The Brain of the Million Dollar Ad Intelligence System

Smart agent layering for MAXIMUM EFFICIENCY:

LAYER 0 (VISION EXTRACTION - THE FOUNDATION):
└─ Agent 0: LLaVA → Vision analysis (OCR + visual understanding)
   ↓ (90% confidence, extracts all text from ad images)
   → Populates context.raw_text for all downstream agents

LAYER 1 (GATEKEEPERS - FAST, NO LLM):
├─ Agent 11: Region Validator → REJECT wrong-region ads immediately
└─ Agent 2: Product Knowledge Lookup → Use cache, skip expensive agents

LAYER 2 (CORE CLASSIFICATION - CONDITIONAL LLM):
├─ Agent 3: Subscription Detector (rule-based + LLM validation)
├─ Agent 4: Brand Extractor (NER + LLM)
└─ Agent 5: Product Type Classifier (fast path → LLM fallback)

LAYER 3 (VALIDATION - CONDITIONAL, ONLY IF NEEDED):
└─ Agent 6: Web Search Validator → ONLY if confidence < 0.7

LAYER 4 (ENRICHMENT - CONDITIONAL, PRODUCT-SPECIFIC):
├─ Agent 7: Food Category Classifier → ONLY if product_type == "restaurant"
├─ Agent 8: Offer Extractor (regex → LLM fallback)
├─ Agent 9: Audience Detector (signals → LLM fallback)
└─ Agent 10: Theme Analyzer (keyword scoring, NO LLM)

Performance optimizations:
- Vision-first: Extract text from images BEFORE all other processing
- Early rejection (Region Validator first)
- Cache hits skip expensive agents
- Fast paths bypass LLM calls
- Conditional execution based on product type
- Parallel-safe design (can run Layer 4 agents concurrently)
"""

from __future__ import annotations

from typing import Optional
from datetime import datetime
from pathlib import Path
import yaml
import concurrent.futures

from agents.context import AdContext
from agents.vision_extractor import VisionExtractor
from agents.subscription_detector import SubscriptionDetector
from agents.brand_extractor import BrandExtractor
from agents.product_type_classifier import ProductTypeClassifier
from agents.food_category_classifier_v2 import FoodCategoryClassifier
from agents.offer_extractor import OfferExtractor
from agents.audience_detector import AudienceDetector
from agents.theme_analyzer import ThemeAnalyzer
from agents.region_validator import RegionValidator
from agents.web_search_validator import WebSearchValidator
from agents.simple_llm_extractor import SimpleLLMExtractor


class AdIntelligenceOrchestrator:
    """
    The Brain: Orchestrates all 11 agents with smart layering.

    Agent execution order optimized for:
    1. Speed (early rejection, cache hits)
    2. Efficiency (conditional execution)
    3. Cost (minimize LLM calls)
    """

    def __init__(
        self,
        expected_region: str = "QA",
        ollama_host: str = "http://localhost:11434",
        model: str = "llama3.1:8b"
    ):
        # LAYER 0: Vision Extraction (THE FOUNDATION)
        self.vision_extractor = VisionExtractor(ollama_host=ollama_host)

        # LAYER 1: Gatekeepers (fast, no LLM)
        self.region_validator = RegionValidator(expected_region=expected_region)
        # Agent 2 (Product Knowledge Lookup) will be DB-based when implemented

        # LAYER 2: Core Classification (SIMPLE LLM APPROACH)
        self.simple_extractor = SimpleLLMExtractor(ollama_host=ollama_host, model=model, formatter_model="deepseek-r1:1.5b")

        # Keep old agents for fallback/comparison if needed
        self.subscription_detector = SubscriptionDetector()
        advertiser_brand_map = self._load_advertiser_brand_map()
        self.brand_extractor = BrandExtractor(advertiser_brand_map=advertiser_brand_map)
        self.product_classifier = ProductTypeClassifier(ollama_host=ollama_host, model=model)

        # LAYER 3: Validation (conditional - only if confidence < 0.7)
        self.web_search_validator = WebSearchValidator(ollama_host=ollama_host, model="deepseek-r1:latest")

        # LAYER 4: Enrichment (conditional, product-specific)
        # PARALLEL LLM EXECUTION: Each agent gets its own model for true parallelism!
        self.food_classifier = FoodCategoryClassifier(ollama_host=ollama_host, model=model)
        self.offer_extractor = OfferExtractor(ollama_host=ollama_host, model="llama3:latest")  # Different model!
        self.audience_detector = AudienceDetector(ollama_host=ollama_host, model="deepseek-r1:latest")  # Better reasoning!
        self.theme_analyzer = ThemeAnalyzer()

        self.stats = {
            "total_processed": 0,
            "region_rejected": 0,
            "cache_hits": 0,
            "llm_calls": 0,
            "fast_path_wins": 0
        }

    def enrich(self, context: AdContext) -> AdContext:
        """
        Main enrichment pipeline - executes all agents in optimal order.

        Returns:
            Enriched AdContext with all intelligence extracted
        """

        self.stats["total_processed"] += 1

        print("\n" + "=" * 80)
        print(f"🚀 ORCHESTRATOR: Processing ad {context.unique_id}")
        print("=" * 80)

        # ========================================================================
        # LAYER 0: VISION EXTRACTION (THE FOUNDATION - EXTRACT TEXT FROM IMAGES)
        # ========================================================================

        print("\n👁️  LAYER 0: VISION EXTRACTION")

        # If we have an image (URL or screenshot path), extract text from it
        if context.raw_image_url or context.flags.get('screenshot_path'):
            print("   [Agent 0] Vision Extractor (LLaVA)...")
            context.vision_extraction = self.vision_extractor.extract(
                image_url=context.raw_image_url or "",
                local_path=context.flags.get('screenshot_path')
            )

            # CRITICAL: Use extracted text as raw_text for downstream agents
            if context.vision_extraction and context.vision_extraction.extracted_text:
                context.raw_text = context.vision_extraction.extracted_text
                print(f"   ✅ Extracted {len(context.raw_text)} chars for downstream analysis")
                print(f"   📊 Vision Confidence: {context.vision_extraction.confidence:.2f}")
            else:
                print("   ⚠️  Vision extraction failed - no text extracted")
        else:
            print("   ⚠️  No image provided - using raw_text directly")

        # ========================================================================
        # LAYER 1: GATEKEEPERS (FAST REJECTION & CACHE)
        # ========================================================================

        print("\n🛡️  LAYER 1: GATEKEEPERS")

        # Agent 11: Region Validator (FIRST - reject wrong regions immediately)
        print("   [Agent 11] Region Validator...")
        context.region_validation = self.region_validator.validate(context)

        if not context.region_validation.is_valid:
            print(f"   ❌ REJECTED: {context.region_validation.mismatches}")
            self.stats["region_rejected"] += 1
            context.set_flag("rejected_wrong_region", True)
            return context  # EARLY EXIT - don't waste compute on wrong-region ads

        # Agent 2: Product Knowledge Lookup (check cache)
        # TODO: Implement when DB cache is ready
        # if cache_hit:
        #     self.stats["cache_hits"] += 1
        #     return context  # EARLY EXIT - use cached data

        # ========================================================================
        # LAYER 2: SIMPLE LLM EXTRACTION (Brand + Category + Offer in ONE call)
        # ========================================================================

        print("\n🧠 LAYER 2: SIMPLE LLM EXTRACTION")
        print("   [Simple LLM] Extracting brand, category, and offer...")

        simple_result = self.simple_extractor.extract(context.raw_text)

        # Populate context with simple LLM results
        context.brand = simple_result.brand_name
        context.brand_confidence = simple_result.confidence
        context.product_type = simple_result.product_category
        context.product_type_confidence = simple_result.confidence

        print(f"   ✅ Brand: {simple_result.brand_name}")
        print(f"   ✅ Category: {simple_result.product_category}")
        print(f"   ✅ Offer: {simple_result.offer_type} - {simple_result.offer_details}")
        print(f"   ✅ Confidence: {simple_result.confidence:.2f}")

        # ========================================================================
        # LAYER 3: WEB VALIDATION (ALWAYS RUN FOR BRAND/PRODUCT VERIFICATION)
        # ========================================================================

        # Agent 6: Web Search Validator - ONLY validate when LLM has low confidence
        print(f"\n🔍 LAYER 3: WEB VALIDATION (DuckDuckGo)")
        print("   [Agent 6] Web Search Validator...")

        # ONLY run web validation when:
        # 1. LLM classification has LOW confidence (< 0.75), OR
        # 2. No brand detected (merchant unknown)
        #
        # HIGH CONFIDENCE LLM RESULTS ARE TRUSTED!
        # Web validator was overriding correct classifications (e.g., PlayStation → electronics)

        llm_confidence = context.product_type_confidence or 0
        should_validate = llm_confidence < 0.75

        if not should_validate:
            print(f"   ⏭️  SKIPPING: LLM classification has HIGH confidence ({llm_confidence:.2f}), trusting LLM result")
            context.set_flag('classification_source', 'llm_high_confidence')
            context.set_flag('web_validated', False)
        else:
            # Build search term from available data
            search_term = None

            # Strategy 1: Use BRAND NAME FIRST (the merchant being advertised)
            if context.brand and context.brand.lower() not in ['n/a', 'unknown', 'the']:
                search_term = context.brand
                print(f"   🔍 Search strategy: Using brand name (merchant) '{search_term}'")

            # CRITICAL: SKIP web validation if no brand/merchant extracted
            # Web validation is for validating SPECIFIC brands, not generic categories!
            if not search_term:
                print(f"   ⏭️  SKIPPING: No brand/merchant to validate (product_type='{context.product_type}' is not searchable)")
                context.set_flag('classification_source', 'llm')
                context.set_flag('web_validated', False)
            else:
                # RUN WEB SEARCH (DuckDuckGo validates specific brands/merchants)
                try:
                    validation_result = self.web_search_validator.validate_product(search_term)

                    # Store validation data
                    context.set_flag('web_validated', True)
                    context.set_flag('web_validation_data', validation_result)

                    # WEB VALIDATION = SOURCE OF TRUTH (only for low confidence cases)
                    # Use web validation to correct low-confidence LLM results
                    web_confidence = validation_result.get('confidence', 0)
                    web_product_type = validation_result.get('product_type')

                    if web_product_type and web_confidence > 0.5:
                        # DuckDuckGo returned a classification - USE IT
                        llm_product_type = context.product_type
                        llm_confidence = context.product_type_confidence or 0

                        if web_product_type != llm_product_type:
                            print(f"   🔄 OVERRIDE: LLM said '{llm_product_type}' ({llm_confidence:.2f}), DuckDuckGo says '{web_product_type}' ({web_confidence:.2f})")
                            print(f"   ✅ Using DuckDuckGo result (SOURCE OF TRUTH)")
                        else:
                            print(f"   ✅ Web validation confirms LLM: {web_product_type} ({web_confidence:.2f})")

                        # ALWAYS use web validation result
                        context.product_type = web_product_type
                        context.product_type_confidence = web_confidence
                        context.set_flag('classification_source', 'duckduckgo')
                    else:
                        print(f"   ⚠️  Web validation returned low confidence ({web_confidence:.2f}), keeping LLM result")
                        context.set_flag('classification_source', 'llm')
                except Exception as e:
                    print(f"   ❌ Web validation failed: {e}")
                    context.set_flag('classification_source', 'llm')

        # ========================================================================
        # LAYER 4: ENRICHMENT (PARALLEL EXECUTION - 3x SPEEDUP!)
        # ========================================================================

        print("\n✨ LAYER 4: ENRICHMENT (PARALLEL LLM EXECUTION)")

        # Agent 7: Food Category Classifier (ONLY for restaurants - sequential)
        if context.product_type == "restaurant":
            print("   [Agent 7] Food Category Classifier...")
            food_decision = self.food_classifier.classify(context)
            if food_decision:
                context.set_flag("food_category", food_decision.food_category)
                context.set_flag("food_category_confidence", food_decision.confidence)

        # Store offer from simple LLM extraction
        from agents.context import OfferDecision
        context.offer = OfferDecision(
            offer_type=simple_result.offer_type,
            offer_details=simple_result.offer_details,
            confidence=simple_result.confidence,
            signals=["simple_llm"]
        )

        # PARALLEL EXECUTION: Run 2 remaining agents concurrently
        # - Audience Detector → deepseek-r1:latest
        # - Theme Analyzer → rule-based (no LLM)

        print("   🚀 Running 2 agents in parallel...")

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            # Submit both tasks at once
            future_audience = executor.submit(self._run_audience_detector, context)
            future_themes = executor.submit(self._run_theme_analyzer, context)

            # Wait for both to complete
            try:
                context.audience = future_audience.result(timeout=60)
                print("   ✅ [Agent 9] Audience Detector complete")
            except Exception as e:
                print(f"   ❌ [Agent 9] Audience Detector failed: {e}")

            try:
                context.themes = future_themes.result(timeout=60)
                print("   ✅ [Agent 10] Theme Analyzer complete")
            except Exception as e:
                print(f"   ❌ [Agent 10] Theme Analyzer failed: {e}")

        # ========================================================================
        # FINALIZATION
        # ========================================================================

        print("\n" + "=" * 80)
        print("✅ ENRICHMENT COMPLETE")
        print("=" * 80)
        self._print_summary(context)

        return context

    def _run_offer_extractor(self, context: AdContext):
        """Thread-safe wrapper for offer extraction"""
        return self.offer_extractor.extract(context)

    def _run_audience_detector(self, context: AdContext):
        """Thread-safe wrapper for audience detection"""
        return self.audience_detector.detect(context)

    def _run_theme_analyzer(self, context: AdContext):
        """Thread-safe wrapper for theme analysis"""
        return self.theme_analyzer.analyze(context)

    def _load_advertiser_brand_map(self) -> dict:
        """Load advertiser → brand hints from config/advertiser_brand_map.yaml."""
        config_path = Path(__file__).parent / "config" / "advertiser_brand_map.yaml"
        if not config_path.exists():
            print("   ⚠️  advertiser_brand_map.yaml not found; proceeding without advertiser overrides")
            return {}

        try:
            with config_path.open("r", encoding="utf-8") as handle:
                raw = yaml.safe_load(handle) or {}
        except Exception as exc:
            print(f"   ⚠️  Failed to read advertiser_brand_map.yaml: {exc}")
            return {}

        mapping = raw.get("advertiser_brand_map", {})
        normalized: dict[str, list[str]] = {}
        for adv_id, brands in mapping.items():
            if not brands:
                continue
            if isinstance(brands, str):
                normalized[adv_id] = [brands]
            else:
                normalized[adv_id] = [brand for brand in brands if brand]
        return normalized

    def _print_summary(self, context: AdContext):
        """Print enrichment summary"""

        print(f"\n📊 RESULTS:")
        print(f"   Region: {context.region_validation.detected_region if context.region_validation else 'N/A'} "
              f"({context.region_validation.confidence:.2f} confidence)" if context.region_validation else "N/A")
        print(f"   Brand: {context.brand or 'N/A'}")
        print(f"   Product Type: {context.product_type or 'N/A'}")

        if context.product_type == "restaurant":
            food_cat = context.flags.get("food_category", "N/A")
            print(f"   Food Category: {food_cat}")

        if context.offer:
            print(f"   Offer: {context.offer.offer_type} - {context.offer.offer_details}")

        if context.audience:
            print(f"   Audience: {context.audience.target_audience}")

        if context.themes:
            print(f"   Primary Theme: {context.themes.primary_theme} ({context.themes.messaging_themes.get(context.themes.primary_theme, 0):.2f})")

        print(f"\n📈 PIPELINE STATS:")
        print(f"   Total Processed: {self.stats['total_processed']}")
        print(f"   Region Rejected: {self.stats['region_rejected']}")
        print(f"   Cache Hits: {self.stats['cache_hits']}")

    def get_stats(self) -> dict:
        """Get pipeline statistics"""
        return self.stats.copy()


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def enrich_ad(
    raw_text: str,
    unique_id: str,
    advertiser_id: Optional[str] = None,
    region: str = "QA",
    ollama_host: str = "http://localhost:11434",
    model: str = "llama3.1:8b"
) -> AdContext:
    """
    Convenience function to enrich a single ad.

    Example:
        >>> enriched = enrich_ad(
        ...     raw_text="50% off your first order at McDonald's! Call +974 1234 5678",
        ...     unique_id="ad_001",
        ...     advertiser_id="AR123",
        ...     region="QA"
        ... )
        >>> print(enriched.brand)  # "McDonald's"
        >>> print(enriched.offer.offer_type)  # "percentage_discount"
    """

    context = AdContext(
        unique_id=unique_id,
        advertiser_id=advertiser_id,
        region_hint=region,
        raw_text=raw_text
    )

    orchestrator = AdIntelligenceOrchestrator(
        expected_region=region,
        ollama_host=ollama_host,
        model=model
    )

    return orchestrator.enrich(context)


def batch_enrich(
    ads: list,
    region: str = "QA",
    ollama_host: str = "http://localhost:11434",
    model: str = "llama3.1:8b"
) -> list:
    """
    Batch enrich multiple ads (reuses orchestrator instance for efficiency).

    Example:
        >>> ads = [
        ...     {"unique_id": "ad_001", "raw_text": "...", "advertiser_id": "AR123"},
        ...     {"unique_id": "ad_002", "raw_text": "...", "advertiser_id": "AR124"},
        ... ]
        >>> enriched_ads = batch_enrich(ads, region="QA")
    """

    orchestrator = AdIntelligenceOrchestrator(
        expected_region=region,
        ollama_host=ollama_host,
        model=model
    )

    enriched = []
    for ad_data in ads:
        context = AdContext(
            unique_id=ad_data.get("unique_id"),
            advertiser_id=ad_data.get("advertiser_id"),
            region_hint=region,
            raw_text=ad_data.get("raw_text", "")
        )

        enriched_context = orchestrator.enrich(context)
        enriched.append(enriched_context)

    print(f"\n🎯 BATCH COMPLETE: {len(enriched)} ads enriched")
    print(f"📊 Stats: {orchestrator.get_stats()}")

    return enriched
