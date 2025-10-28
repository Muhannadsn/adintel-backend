from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any


@dataclass
class EvidenceEntry:
    """Traceable note from an agent about a specific observation."""

    agent: str
    observation: str
    confidence: float = 1.0
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class SubscriptionDecision:
    """Structured result from the subscription detector."""

    is_subscription: bool
    subscription_name: Optional[str] = None
    platform: Optional[str] = None
    confidence: float = 0.0
    reasons: List[str] = field(default_factory=list)
    detected_keywords: List[str] = field(default_factory=list)


@dataclass
class BrandMatch:
    """Single brand or merchant detection result."""

    name: str
    confidence: float
    alias: Optional[str] = None
    source: str = "rule"
    entity_type: str = "restaurant"  # restaurant | product | platform | marketplace
    is_advertiser_match: bool = False


@dataclass
class OfferDecision:
    """Structured result from the offer extractor."""

    offer_type: str
    offer_details: str
    offer_conditions: Optional[str] = None
    confidence: float = 0.0
    signals: List[str] = field(default_factory=list)
    additional_offers: List[Dict] = field(default_factory=list)  # Support for multiple offers


@dataclass
class AudienceDecision:
    """Structured result from the audience detector."""

    target_audience: str
    confidence: float
    signals: List[str] = field(default_factory=list)


@dataclass
class ThemeDecision:
    """Structured result from the theme analyzer."""

    messaging_themes: Dict[str, float]
    primary_theme: str
    confidence: float


@dataclass
class RegionDecision:
    """Structured result from the region validator."""

    detected_region: str
    confidence: float
    signals: List[str] = field(default_factory=list)
    mismatches: List[str] = field(default_factory=list)
    is_valid: bool = True


@dataclass
class VisionExtractionResult:
    """Structured result from vision extraction (Layer 0)."""

    extracted_text: str
    visual_description: str
    confidence: float
    deepseek_text: str
    llava_analysis: str
    method_used: str
    sections: Dict[str, str] = field(default_factory=dict)


@dataclass
class AdContext:
    """
    Shared context object passed between enrichment agents.

    Fields will grow as more agents are implemented, but keeping the canonical
    schema in one place ensures Codex/Claude stay aligned.
    """

    unique_id: Optional[str]
    advertiser_id: Optional[str]
    region_hint: Optional[str] = None
    raw_image_url: Optional[str] = None
    raw_text: str = ""
    ocr_confidence: Optional[float] = None
    brand: Optional[str] = None
    brand_confidence: Optional[float] = None
    brand_source: Optional[str] = None
    brand_matches: List[BrandMatch] = field(default_factory=list)
    advertiser_brand_hint: Optional[str] = None
    subscription: Optional[SubscriptionDecision] = None
    platform_branding: Optional[str] = None
    product_type: Optional[str] = None
    product_type_confidence: Optional[float] = None
    offer: Optional[OfferDecision] = None
    audience: Optional[AudienceDecision] = None
    themes: Optional[ThemeDecision] = None
    region_validation: Optional[RegionDecision] = None
    vision_extraction: Optional[VisionExtractionResult] = None
    flags: Dict[str, Any] = field(default_factory=dict)
    evidence: List[EvidenceEntry] = field(default_factory=list)

    def add_evidence(
        self,
        agent: str,
        observation: str,
        confidence: float = 1.0,
    ) -> None:
        """Append an evidence entry."""
        self.evidence.append(EvidenceEntry(agent=agent, observation=observation, confidence=confidence))

    def set_flag(self, name: str, value: Any) -> None:
        """Convenience helper for flag storage."""
        self.flags[name] = value
