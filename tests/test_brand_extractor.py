import sys
from pathlib import Path
from typing import List, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents.context import AdContext, BrandMatch, VisionExtractionResult  # noqa: E402
from agents.brand_extractor import BrandExtractor, BrandRecord  # noqa: E402


def make_context(raw_text: str, advertiser_id: Optional[str] = None) -> AdContext:
    return AdContext(unique_id="test", advertiser_id=advertiser_id, raw_text=raw_text)


def test_catalog_match_basic():
    extractor = BrandExtractor()
    context = make_context("Limited time: 50% off at McDonald's with Talabat delivery.")

    matches = extractor.extract(context)

    assert matches
    assert matches[0].name == "McDonald's"
    assert context.brand == "McDonald's"
    assert context.brand_confidence >= 0.85
    # Ensure Talabat platform mention was ignored
    assert all(match.name != "Talabat" for match in matches)


def test_alias_detection_handles_spacing():
    extractor = BrandExtractor()
    context = make_context("Grab the Nutri Bullet Smart Pot 2 on sale now!")

    matches = extractor.extract(context)

    assert matches
    names = [m.name for m in matches]
    assert "NutriBullet" in names


def test_multiple_brands_flag():
    custom_catalog = {
        "McDonald's": BrandRecord("McDonald's", ("mcdonald's", "mcdonalds")),
        "Coca-Cola": BrandRecord("Coca-Cola", ("coca cola", "coke"), entity_type="product"),
    }
    extractor = BrandExtractor(catalog=custom_catalog, stop_entity_types=("platform",))
    context = make_context("McDonald's teams up with Coca Cola for a combo offer.")

    matches = extractor.extract(context)

    names = {m.name for m in matches}
    assert "McDonald's" in names
    assert "Coca-Cola" in names
    assert context.flags.get("multiple_brands_detected") is True


def test_llm_resolver_fallback():
    def fake_resolver(ctx: AdContext) -> List[BrandMatch]:
        return [
            BrandMatch(name="Haldiram's", confidence=0.7, alias=None, source="llm", entity_type="restaurant")
        ]

    extractor = BrandExtractor(catalog={}, llm_resolver=fake_resolver)
    context = make_context("Enjoy authentic Indian sweets from Haldiram's.")

    matches = extractor.extract(context)

    assert matches
    haldiram_match = next(match for match in matches if match.name == "Haldiram's")
    assert context.brand == "Haldiram's"
    assert context.brand_source == "llm"
    assert context.brand_confidence == haldiram_match.confidence


def test_fuzzy_matching_catches_typos():
    extractor = BrandExtractor()
    context = make_context("Exclusive combo at MacDonalds this weekend!")

    matches = extractor.extract(context)

    assert matches
    assert matches[0].name == "McDonald's"
    assert matches[0].source in {"catalog", "catalog_fuzzy", "catalog_substring"}
    assert context.brand_confidence >= 0.75


def test_grocery_brands_in_catalog():
    extractor = BrandExtractor()
    context = make_context("Shop weekly essentials from Lulu Hypermarket and TalabatMart.")

    matches = extractor.extract(context)

    names = [m.name for m in matches]
    assert "Lulu Hypermarket" in names
    assert "TalabatMart" in names
    assert context.flags.get("multiple_brands_detected") is True


def test_substring_false_positive_prevented():
    extractor = BrandExtractor()
    context = make_context("This dessert is absolutely delicious and lovely.")

    matches = extractor.extract(context)

    assert all(match.name != "Lulu Hypermarket" for match in matches)


def test_url_slug_heuristic_detects_unknown_brand():
    extractor = BrandExtractor()
    context = make_context("Order now at www.talabat.com/bahrain/chicket for quick delivery.")

    matches = extractor.extract(context)

    assert any(match.name == "Chicket" and match.source == "heuristic_url" for match in matches)


def test_titlecase_heuristic_detects_unknown_brand():
    extractor = BrandExtractor()
    context = make_context("Get your meal delivered from Shalteneh in Cairo via Talabat.")

    matches = extractor.extract(context)

    assert any(match.name == "Shalteneh" and match.source == "heuristic_titlecase" for match in matches)


def test_arabic_heuristic_detects_unknown_brand():
    extractor = BrandExtractor()
    context = make_context("اطلب اليوم من شلنته في القاهرة واستمتع بوجبتك مع طلبات.")

    matches = extractor.extract(context)

    assert any("شلنته" in match.name for match in matches)


def test_electronics_brand_recognised():
    extractor = BrandExtractor()
    context = make_context("Upgrade to the latest Samsung Galaxy smartphone with 5G performance.")

    matches = extractor.extract(context)

    samsung = next(match for match in matches if match.name == "Samsung")
    assert samsung.entity_type == "electronics"
    assert context.brand == "Samsung"


def test_advertiser_brand_overrides_priority():
    advertiser_map = {"ADV-PEPSI": ["Pepsi"]}
    extractor = BrandExtractor(advertiser_brand_map=advertiser_map)
    context = make_context(
        "Pepsi is the perfect drink for your Pizza Hut meal tonight.",
        advertiser_id="ADV-PEPSI",
    )

    matches = extractor.extract(context)

    assert matches
    assert context.brand == "Pepsi"
    assert matches[0].name == "Pepsi"
    assert matches[0].is_advertiser_match is True
    assert context.flags.get("brand_conflict_with_advertiser") is True  # Pizza Hut still present


def test_advertiser_hint_used_when_text_missing_brand():
    advertiser_map = {"ADV-KFC": ["KFC"]}
    extractor = BrandExtractor(advertiser_brand_map=advertiser_map)
    context = make_context("Try the new Twister with extra sauce.", advertiser_id="ADV-KFC")

    matches = extractor.extract(context)

    assert context.brand == "KFC"
    assert any(match.source == "advertiser_hint" for match in matches)
    assert context.flags.get("brand_inferred_from_advertiser") is True


def test_advertiser_conflict_flagged_on_mismatch():
    advertiser_map = {"ADV-KFC": ["KFC"]}
    extractor = BrandExtractor(advertiser_brand_map=advertiser_map)
    context = make_context("Grab a Burger King meal with crispy fries.", advertiser_id="ADV-KFC")

    matches = extractor.extract(context)

    assert any(match.name == "KFC" for match in matches)  # advertiser hint added
    assert any(match.name == "Burger King" for match in matches)
    assert context.flags.get("brand_conflict_with_advertiser") is True


def test_brand_section_recovers_marketplace_merchant():
    extractor = BrandExtractor()
    context = make_context("Limited-time delivery offer.")
    context.vision_extraction = VisionExtractionResult(
        extracted_text="Limited-time delivery offer.",
        visual_description="Ad with Snoonu colors promoting groceries.",
        confidence=0.9,
        deepseek_text="",
        llava_analysis="1. Visible text:\nLimited-time delivery offer.\n2. Product or service being advertised:\nGrocery delivery for Monoprix via Snoonu.\n3. Brand name:\nMonoprix\n",
        method_used="llava_only",
        sections={
            "visible_text": "Limited-time delivery offer.",
            "product_service": "Grocery delivery for Monoprix via Snoonu.",
            "brand": "Monoprix",
        },
    )

    matches = extractor.extract(context)

    assert any(match.name == "Monoprix" for match in matches)
    assert context.brand == "Monoprix"
    assert context.flags.get("brand_vision_sections_used") is True
