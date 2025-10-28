from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional

from .context import AdContext, SubscriptionDecision


@dataclass(frozen=True)
class SubscriptionMetadata:
    """Configuration for a platform subscription program."""

    platform: str
    subscription_name: str
    keywords: List[str]
    platform_terms: List[str]
    enabled: bool = True


DEFAULT_SUBSCRIPTIONS: Dict[str, SubscriptionMetadata] = {
    # Talabat Pro
    "AR14306592000630063105": SubscriptionMetadata(
        platform="Talabat",
        subscription_name="Talabat Pro",
        keywords=["talabat pro", "برو", "talabat برو", "pro membership", "subscription", "اشتراك", "عضوية"],
        platform_terms=["talabat", "طلبات"],
    ),
    # Keeta (no subscription offering; kept disabled to prevent false positives)
    "AR02245493152427278337": SubscriptionMetadata(
        platform="Keeta",
        subscription_name="Keeta Pro",
        keywords=["keeta pro", "keeta برو", "keeta plus"],
        platform_terms=["keeta"],
        enabled=False,
    ),
    # Deliveroo Plus
    "AR13676304484790173697": SubscriptionMetadata(
        platform="Deliveroo",
        subscription_name="Deliveroo Plus",
        keywords=["deliveroo plus", "plus membership", "plus plan"],
        platform_terms=["deliveroo"],
    ),
    # Rafeeq Pro
    "AR08778154730519003137": SubscriptionMetadata(
        platform="Rafeeq",
        subscription_name="Rafeeq Pro",
        keywords=["rafeeq pro", "رفيق برو", "rafeeq plus", "rafeeq برو", "pro", "برو"],
        platform_terms=["rafeeq", "rafiq", "رفيق"],
    ),
    # Snoonu S Plus
    "AR12079153035289296897": SubscriptionMetadata(
        platform="Snoonu",
        subscription_name="S Plus",
        keywords=["s plus", "snoonu plus", "s+", "س بلص", "سنوونو بلس"],
        platform_terms=["snoonu", "سنوونو"],
    ),
}


class SubscriptionDetector:
    """
    Agent 3: determines whether an ad promotes a platform subscription service.

    The detector combines advertiser metadata with text heuristics so we only
    flag subscriptions when both the platform and membership cues appear.
    """

    def __init__(
        self,
        catalog: Optional[Dict[str, SubscriptionMetadata]] = None,
        generic_keywords: Optional[Iterable[str]] = None,
    ) -> None:
        self.catalog = catalog or DEFAULT_SUBSCRIPTIONS
        self.generic_keywords = set(k.lower() for k in (generic_keywords or ["subscription", "member price"]))

    def analyze(self, context: AdContext) -> SubscriptionDecision:
        text = (context.raw_text or "").lower()
        advertiser_id = context.advertiser_id or ""
        decision = SubscriptionDecision(is_subscription=False, confidence=0.0)

        # Fast exits: nothing to analyze
        if not advertiser_id and not text:
            context.subscription = decision
            return decision

        metadata = self.catalog.get(advertiser_id)

        if metadata and not metadata.enabled:
            # Explicitly disabled: ensure we record platform branding but do not mark subscription
            context.platform_branding = metadata.platform
            decision.reasons.append(f"{metadata.platform} subscription disabled for advertiser")
            context.subscription = decision
            return decision

        if metadata:
            platform_hit = self._contains_any(text, metadata.platform_terms)
            keyword_hit = self._contains_any(text, metadata.keywords)

            # Honor upstream hints like SUBSCRIPTION_SERVICE: Talabat Pro
            if not keyword_hit:
                keyword_hit = "subscription_service:" in text and metadata.subscription_name.lower() in text

            if platform_hit and keyword_hit:
                decision = SubscriptionDecision(
                    is_subscription=True,
                    subscription_name=metadata.subscription_name,
                    platform=metadata.platform,
                    confidence=0.95,
                    reasons=[
                        f"Advertiser maps to {metadata.platform}",
                        f"Detected keywords: {self._matched_terms(text, metadata.keywords)}",
                    ],
                    detected_keywords=self._matched_terms(text, metadata.keywords + metadata.platform_terms),
                )
            elif platform_hit and not keyword_hit:
                decision.reasons.append("Platform detected without subscription keyword")
                decision.detected_keywords = self._matched_terms(text, metadata.platform_terms)
                decision.confidence = 0.2
            elif keyword_hit:
                decision.reasons.append("Subscription keyword found but platform term missing")
                decision.detected_keywords = self._matched_terms(text, metadata.keywords)
                decision.confidence = 0.3
            else:
                decision.reasons.append("No subscription signals detected for mapped advertiser")
                decision.confidence = 0.05

            if decision.is_subscription:
                context.platform_branding = metadata.platform
            else:
                # Still record the platform for downstream sanity checks
                context.platform_branding = metadata.platform

            context.subscription = decision
            return decision

        # No explicit catalog entry: fall back to generic guard to avoid false positives.
        generic_hit = any(term in text for term in self.generic_keywords)
        if generic_hit:
            # If we find subscription language but no known platform, set low confidence flag.
            decision.reasons.append("Generic subscription language detected without platform mapping")
            decision.detected_keywords = [term for term in self.generic_keywords if term in text]
            decision.confidence = 0.15

        context.subscription = decision
        return decision

    @staticmethod
    def _contains_any(text: str, needles: Iterable[str]) -> bool:
        return any(n.lower() in text for n in needles if n)

    @staticmethod
    def _matched_terms(text: str, needles: Iterable[str]) -> List[str]:
        found: List[str] = []
        for needle in needles:
            if not needle:
                continue
            if needle.lower() in text:
                found.append(needle)
            else:
                # Quick regex to catch variants with punctuation (e.g., "S+")
                pattern = re.escape(needle.lower()).replace("\\+", "\\s*\\+")
                if re.search(pattern, text):
                    found.append(needle)
        return list(dict.fromkeys(found))
