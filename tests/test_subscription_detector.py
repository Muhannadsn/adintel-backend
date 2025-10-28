import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents.context import AdContext  # noqa: E402
from agents.subscription_detector import SubscriptionDetector, DEFAULT_SUBSCRIPTIONS  # noqa: E402


def make_context(advertiser_id: str, raw_text: str) -> AdContext:
    return AdContext(
        unique_id="test",
        advertiser_id=advertiser_id,
        raw_text=raw_text,
    )


def test_talabat_pro_detected():
    detector = SubscriptionDetector()
    context = make_context(
        "AR14306592000630063105",
        "Join Talabat Pro today and unlock free delivery on every order!",
    )

    decision = detector.analyze(context)

    assert decision.is_subscription
    assert decision.subscription_name == "Talabat Pro"
    assert decision.platform == "Talabat"
    assert context.platform_branding == "Talabat"
    assert decision.confidence > 0.9


def test_platform_without_keyword_not_flagged():
    detector = SubscriptionDetector()
    context = make_context(
        "AR14306592000630063105",
        "Talabat delivers thousands of restaurants to you.",
    )

    decision = detector.analyze(context)

    assert not decision.is_subscription
    assert decision.confidence < 0.5
    assert context.platform_branding == "Talabat"


def test_snoonu_s_plus_detected():
    detector = SubscriptionDetector()
    context = make_context(
        "AR12079153035289296897",
        "Upgrade to Snoonu S Plus for unlimited free deliveries.",
    )

    decision = detector.analyze(context)

    assert decision.is_subscription
    assert decision.subscription_name == "S Plus"
    assert decision.platform == "Snoonu"


def test_disabled_subscription_entry():
    detector = SubscriptionDetector()
    metadata = DEFAULT_SUBSCRIPTIONS["AR02245493152427278337"]
    assert not metadata.enabled

    context = make_context(
        "AR02245493152427278337",
        "Keeta Pro gives you amazing perks.",
    )

    decision = detector.analyze(context)

    assert not decision.is_subscription
    assert decision.subscription_name is None
    assert context.platform_branding == "Keeta"


def test_generic_subscription_language_low_confidence():
    detector = SubscriptionDetector()
    context = make_context(
        "UNKNOWN",
        "Premium subscription members save more.",
    )

    decision = detector.analyze(context)

    assert not decision.is_subscription
    assert decision.confidence <= 0.2
    assert "subscription" in decision.detected_keywords
