#!/usr/bin/env python3
"""
Orchestrated Ad Intelligence - Wraps the 11-agent orchestrator
for backwards compatibility with existing AdIntelligence API

This adapter converts between:
- INPUT: Database ad format (ad_text, image_url, advertiser_id, etc.)
- ORCHESTRATOR: AdContext enrichment
- OUTPUT: Database-compatible enrichment dict
"""

from typing import List, Dict
from datetime import datetime

# Import the orchestrator
from orchestrator import AdIntelligenceOrchestrator
from agents.context import AdContext


class OrchestratedAnalyzer:
    """
    Drop-in replacement for AdIntelligence that uses the 11-agent orchestrator

    Maintains API compatibility while upgrading to:
    - Agent 11: Region Validator (data quality gatekeeper)
    - Agent 3: Subscription Detector
    - Agent 4: Brand Extractor
    - Agent 5: Product Type Classifier
    - Agent 7: Food Category Classifier (conditional)
    - Agent 8: Offer Extractor
    - Agent 9: Audience Detector (multi-category)
    - Agent 10: Theme Analyzer (no LLM, keyword-based)
    """

    def __init__(self,
                 model: str = "llama3.1:8b",
                 vision_model: str = "llava:latest",  # Not used yet in orchestrator
                 ollama_host: str = "http://localhost:11434",
                 expected_region: str = "QA"):
        """
        Initialize orchestrated analyzer

        Args:
            model: LLM model for agents (llama3.1:8b, deepseek-r1, etc.)
            vision_model: Vision model (future use)
            ollama_host: Ollama API endpoint
            expected_region: Expected ad region (QA, AE, SA, etc.)
        """
        self.model = model
        self.vision_model = vision_model
        self.ollama_host = ollama_host
        self.expected_region = expected_region

        # Initialize the orchestrator
        self.orchestrator = AdIntelligenceOrchestrator(
            expected_region=expected_region,
            ollama_host=ollama_host,
            model=model
        )

        # Product categories (for API compatibility)
        self.product_categories = [
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

        # Audience segments (for API compatibility)
        self.audience_segments = [
            "Young Professionals (25-34)",
            "Families with Kids",
            "Students (18-24)",
            "Late-night Users",
            "Health-Conscious Consumers",
            "Budget-Conscious Diners",
            "Premium Seekers",
            "New Customers",
            "Tech Enthusiasts",
            "Gamers",
            "General Audience"
        ]

        print(f"✅ Orchestrated Analyzer initialized - Using 11-agent pipeline")
        print(f"   Expected Region: {expected_region}")
        print(f"   Model: {model}")

    def categorize_ad(self, ad: Dict) -> Dict:
        """
        Analyze single ad using the orchestrator

        Args:
            ad: Dict with keys: ad_text, image_url, advertiser_id, regions, id

        Returns:
            Original ad dict + orchestrator enrichment mapped to database fields
        """
        try:
            # Extract ad data
            ad_text = ad.get('ad_text', '') or ad.get('extracted_text', '')
            ad_id = ad.get('id') or ad.get('ad_id', 'unknown')
            advertiser_id = ad.get('advertiser_id', '')
            region = ad.get('regions', self.expected_region)

            # Create AdContext for orchestrator
            context = AdContext(
                unique_id=str(ad_id),
                advertiser_id=advertiser_id,
                region_hint=region,
                raw_text=ad_text,
                raw_image_url=ad.get('image_url')
            )

            # Run orchestrator enrichment
            enriched_context = self.orchestrator.enrich(context)

            # Map orchestrator output to database format
            enrichment = self._map_context_to_db(enriched_context)

            # Merge with original ad
            enriched_ad = {
                **ad,
                **enrichment,
                'analyzed_at': datetime.now().isoformat(),
                'analysis_model': self.model,
                'enrichment_method': 'orchestrator_11_agents'
            }

            return enriched_ad

        except Exception as e:
            print(f"⚠️  Error analyzing ad {ad.get('id')}: {e}")
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

        print(f"🤖 Starting orchestrator analysis of {total} ads...")
        print(f"   Using 11-agent pipeline with region validation")

        rejected_count = 0

        for i, ad in enumerate(ads, 1):
            try:
                enriched = self.categorize_ad(ad)
                enriched_ads.append(enriched)

                # Track rejections
                if enriched.get('rejected_wrong_region'):
                    rejected_count += 1

                # Show progress every batch_size ads
                if i % batch_size == 0 or i == total:
                    progress = (i / total) * 100
                    print(f"   Progress: {i}/{total} ads analyzed ({progress:.1f}%) | Rejected: {rejected_count}")

            except Exception as e:
                print(f"⚠️  Failed to analyze ad {i}: {e}")
                enriched_ads.append(self._create_fallback_enrichment(ad, str(e)))

        print(f"✅ Analysis complete! {len(enriched_ads)} ads processed.")
        print(f"   ✅ Valid: {total - rejected_count}")
        print(f"   ❌ Rejected (wrong region): {rejected_count}")

        return enriched_ads

    def _map_context_to_db(self, context: AdContext) -> Dict:
        """
        Map enriched AdContext to database-compatible dict

        Args:
            context: Enriched AdContext from orchestrator

        Returns:
            Dict with database field names
        """
        # Map product_type to product_category
        product_category = self._map_product_type_to_category(context.product_type)

        # Get food category from flags (if restaurant)
        food_category = context.flags.get('food_category') if context.product_type == 'restaurant' else None

        # Build messaging themes dict
        messaging_themes = {}
        if context.themes:
            messaging_themes = context.themes.messaging_themes

        # Get primary theme
        primary_theme = context.themes.primary_theme if context.themes else 'convenience'

        # Get offer data
        offer_type = context.offer.offer_type if context.offer else 'none'
        offer_details = context.offer.offer_details if context.offer else ''

        # Get audience
        audience_segment = context.audience.target_audience if context.audience else 'General Audience'

        # Build product_name
        product_name = self._build_product_name(context, product_category, food_category)

        # Calculate confidence score (average of available confidences)
        confidence_scores = []
        if context.brand_confidence:
            confidence_scores.append(context.brand_confidence)
        if context.product_type_confidence:
            confidence_scores.append(context.product_type_confidence)
        if context.offer and context.offer.confidence:
            confidence_scores.append(context.offer.confidence)
        if context.audience and context.audience.confidence:
            confidence_scores.append(context.audience.confidence)

        confidence_score = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.7

        # Region validation flags
        is_valid_region = context.region_validation.is_valid if context.region_validation else True
        rejected_wrong_region = not is_valid_region
        detected_region = context.region_validation.detected_region if context.region_validation else self.expected_region

        return {
            # Core categorization
            'product_category': product_category,
            'product_name': product_name,
            'food_category': food_category,

            # Brand
            'brand': context.brand,
            'brand_confidence': context.brand_confidence,

            # Messaging
            'messaging_themes': messaging_themes,
            'primary_theme': primary_theme,

            # Offer
            'offer_type': offer_type,
            'offer_details': offer_details,

            # Audience
            'audience_segment': audience_segment,

            # Confidence
            'confidence_score': round(confidence_score, 2),

            # Region validation
            'is_qatar_only': is_valid_region,  # Backwards compatible field name
            'detected_region': detected_region,
            'rejected_wrong_region': rejected_wrong_region,

            # Subscription flag
            'is_subscription': context.subscription.is_subscription if context.subscription else False,
            'subscription_name': context.subscription.subscription_name if context.subscription else None,

            # Metadata
            'enrichment_pipeline': '11_agents_orchestrated',
            'agents_used': self._get_agents_used(context)
        }

    def _map_product_type_to_category(self, product_type: str) -> str:
        """
        Map Agent 5's product_type to database product_category

        Args:
            product_type: Output from Agent 5 (restaurant, unknown_category, service, etc.)

        Returns:
            Database-compatible category
        """
        if not product_type:
            return "Meal Deals & Combos"  # Default

        # Map product types to categories
        type_to_category = {
            'restaurant': 'Specific Restaurant/Brand Promo',  # Will be refined by Agent 7
            'unknown_category': 'Consumer Electronics',  # Generic, will be refined by category inference
            'service': 'Platform Subscription Service',
            'grocery': 'Grocery Delivery',
            'pharmacy': 'Pharmacy & Health'
        }

        return type_to_category.get(product_type, "Meal Deals & Combos")

    def _build_product_name(self, context: AdContext, category: str, food_category: str) -> str:
        """
        Build product_name from context data

        Args:
            context: Enriched AdContext
            category: Product category
            food_category: Food category (if restaurant)

        Returns:
            Formatted product name
        """
        # If we have a brand, use it
        if context.brand:
            if food_category:
                return f"{context.brand} - {food_category}"
            else:
                return f"{context.brand} - {category}"

        # If subscription, use subscription name
        if context.subscription and context.subscription.subscription_name:
            return context.subscription.subscription_name

        # If food category, use it as product name
        if food_category:
            return food_category

        # Default: use category
        return category or "Unknown"

    def _get_agents_used(self, context: AdContext) -> List[str]:
        """
        Get list of agents that were executed for this ad

        Args:
            context: Enriched AdContext

        Returns:
            List of agent names
        """
        agents_used = []

        # Always used
        agents_used.append("RegionValidator")
        agents_used.append("SubscriptionDetector")
        agents_used.append("BrandExtractor")
        agents_used.append("ProductTypeClassifier")

        # Conditional: Food Category (only for restaurants)
        if context.product_type == "restaurant":
            agents_used.append("FoodCategoryClassifier")

        # Always used
        agents_used.append("OfferExtractor")
        agents_used.append("AudienceDetector")
        agents_used.append("ThemeAnalyzer")

        return agents_used

    def _create_fallback_enrichment(self, ad: Dict, error: str) -> Dict:
        """
        Create basic enrichment when orchestrator fails

        Args:
            ad: Original ad dict
            error: Error message

        Returns:
            Ad with basic enrichment
        """
        return {
            **ad,
            'product_category': "Meal Deals & Combos",
            'product_name': 'Unknown',
            'messaging_themes': {'price': 0.0, 'speed': 0.0, 'quality': 0.0, 'convenience': 0.0},
            'primary_theme': 'convenience',
            'audience_segment': 'General Audience',
            'offer_type': 'none',
            'offer_details': '',
            'confidence_score': 0.3,
            'enrichment_error': error,
            'enrichment_method': 'fallback',
            'analyzed_at': datetime.now().isoformat()
        }


# Backwards compatibility alias
AdIntelligence = OrchestratedAnalyzer
