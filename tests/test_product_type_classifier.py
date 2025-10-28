import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents.context import AdContext, BrandMatch  # noqa: E402
from agents.product_type_classifier import ProductTypeClassifier  # noqa: E402


def make_context(raw_text: str, brand_match: BrandMatch | None = None) -> AdContext:
    context = AdContext(unique_id="test", advertiser_id=None, raw_text=raw_text)
    if brand_match:
        context.brand_matches.append(brand_match)
        context.brand = brand_match.name
        context.brand_confidence = brand_match.confidence
    return context


def test_electronics_brand_fast_path():
    classifier = ProductTypeClassifier()
    context = make_context(
        "New Samsung Galaxy S24 Ultra with 5G, 200MP camera, and 45W fast charging.",
        BrandMatch(
            name="Samsung",
            confidence=0.9,
            alias="Samsung",
            source="catalog",
            entity_type="electronics",
        ),
    )

    decision = classifier.classify(context)

    assert decision.product_type == "physical_product"
    assert decision.confidence >= 0.85


def test_fashion_keywords_detect_physical_product():
    classifier = ProductTypeClassifier()
    context = make_context("Flash sale: New summer dresses, abayas, and sneakers under QAR 149!")

    decision = classifier.classify(context)

    assert decision.product_type == "physical_product"


def test_pharmacy_brand_fast_path():
    classifier = ProductTypeClassifier()
    context = make_context(
        "فيتامينات للأطفال من صيدلية الدوحة مع خصم 15 ريال وتوصيل مجاني",
        BrandMatch(
            name="Doha Pharmacy",
            confidence=0.9,
            alias="Doha Pharmacy",
            source="catalog",
            entity_type="pharmacy",
        ),
    )

    decision = classifier.classify(context)

    assert decision.product_type == "physical_product"
