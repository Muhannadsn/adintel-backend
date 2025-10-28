from dataclasses import dataclass, field
from typing import Optional, List

@dataclass
class Creative:
    advertiser: str
    creative: str
    format: str
    region_filter: str
    campaign_duration: str
    first_seen: str
    last_seen: str
    gatc_link: str

@dataclass
class Screenshot:
    creative_id: int  # To link back to the creative
    image_path: str
    video_path: Optional[str] = None

@dataclass
class Analysis:
    screenshot_id: int  # To link back to the screenshot
    product_category: str
    offer_type: str
    messaging: str
    raw_ai_response: str
    # Enhanced fields for detailed analysis
    extracted_text: Optional[str] = None  # Full text extracted from ad
    headline: Optional[str] = None  # Main headline/title
    call_to_action: Optional[str] = None  # CTA text (e.g., "Order Now")
    discount_percentage: Optional[str] = None  # e.g., "50%", "Buy 1 Get 1"
    products_mentioned: List[str] = field(default_factory=list)  # Specific products mentioned
    keywords: List[str] = field(default_factory=list)  # Key marketing terms
    brand_name: Optional[str] = None  # Brand mentioned in ad
    price_mentioned: Optional[str] = None  # Any price shown