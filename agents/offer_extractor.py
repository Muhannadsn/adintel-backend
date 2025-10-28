#!/usr/bin/env python3
"""
Agent 8: Offer Extractor
Regex-based extraction with LLM fallback for complex offers.
Supports English + Arabic.
"""

from __future__ import annotations

import re
import requests
import json
from typing import Optional, List, Dict
from .context import AdContext, OfferDecision


class OfferExtractor:
    """
    Agent 8: Offer Extractor

    Strategy:
    1. Fast path: Regex patterns for common offer formats (English + Arabic)
    2. Fallback: LLM for complex/ambiguous offers
    3. Returns structured offer data with confidence
    """

    def __init__(
        self,
        ollama_host: str = "http://localhost:11434",
        model: str = "llama3.1:8b"
    ):
        self.ollama_host = ollama_host
        self.model = model
        self.api_url = f"{ollama_host}/api/generate"

        # Regex patterns for common offer types (English + Arabic)
        self.patterns = {
            "percentage_discount": [
                # English: "50% off", "30% discount", "Get 20% OFF"
                r"(\d+)%\s*(?:off|discount|خصم)",
                # Arabic: "خصم 50%", "تخفيض 30%"
                r"(?:خصم|تخفيض)\s*(\d+)%",
                r"save\s*(\d+)%",
            ],
            "fixed_discount": [
                # "QAR 20 off", "$10 discount", "SAR 15 off"
                r"(?:QAR|SAR|\$|AED|ريال)\s*(\d+)\s*(?:off|discount|خصم)",
                # Arabic: "خصم 20 ريال"
                r"(?:خصم|تخفيض)\s*(\d+)\s*(?:ريال|QAR|SAR)",
            ],
            "free_delivery": [
                # "Free delivery", "توصيل مجاني"
                r"free\s*delivery",
                r"توصيل\s*مجاني",
                r"no\s*delivery\s*fee",
                r"بدون\s*رسوم\s*توصيل",
            ],
            "bogo": [
                # "Buy 1 Get 1 Free", "اشتر واحد واحصل على الثاني مجاناً"
                r"buy\s*\d+\s*get\s*\d+\s*free",
                r"bogo",
                r"b\d+g\d+",
                r"اشتر.+مجان",
            ],
            "limited_time": [
                # "Today only", "Limited time", "لفترة محدودة"
                r"today\s*only",
                r"limited\s*time",
                r"لفترة\s*محدودة",
                r"عرض\s*محدود",
                r"for\s*\d+\s*days?\s*only",
            ],
            "first_order": [
                # "50% off first order", "خصم على الطلب الأول"
                r"(?:first|1st)\s*order",
                r"new\s*customer",
                r"الطلب\s*الأول",
                r"عملاء\s*جدد",
            ],
            "minimum_order": [
                # "Min order QAR 50", "orders above QAR 50", "حد أدنى 50 ريال"
                r"min(?:imum)?\s*order\s*(?:QAR|SAR|\$)?\s*(\d+)",
                r"orders?\s*above\s*(?:QAR|SAR|\$)?\s*(\d+)",
                r"حد\s*أدنى.+(\d+)",
            ]
        }

    def extract(self, context: AdContext) -> OfferDecision:
        """Extract ALL offers from ad text (supports multiple offers)"""

        text = context.raw_text or ""
        text_lower = text.lower()

        # STEP 1: Extract ALL regex-based offers
        all_offers = self._extract_all_with_regex(text, text_lower)

        # STEP 2: Check for generic promotional language (if no specific offers found)
        if not all_offers:
            generic_result = self._check_generic_promo(text_lower)
            if generic_result:
                print(f"   🎁 Generic promo: {generic_result.offer_type}")
                return generic_result

        # STEP 3: LLM fallback for complex/unclear offers (if no regex matches)
        if not all_offers and len(text) > 20:
            llm_result = self._extract_with_llm(text)
            if llm_result.offer_type != "none":
                print(f"   🤖 LLM extracted: {llm_result.offer_type} - {llm_result.offer_details}")
                return llm_result

        # STEP 4: Return primary + additional offers
        if all_offers:
            primary = all_offers[0]
            additional = [
                {
                    "offer_type": offer["offer_type"],
                    "offer_details": offer["offer_details"],
                    "confidence": offer["confidence"]
                }
                for offer in all_offers[1:]
            ]

            print(f"   🎯 Found {len(all_offers)} offer(s): {primary['offer_type']} (+ {len(additional)} more)")
            return OfferDecision(
                offer_type=primary["offer_type"],
                offer_details=primary["offer_details"],
                offer_conditions=primary.get("offer_conditions"),
                confidence=primary["confidence"],
                signals=primary["signals"],
                additional_offers=additional
            )

        # STEP 5: No offer detected
        print(f"   📭 No offer detected")
        return OfferDecision(
            offer_type="none",
            offer_details="",
            confidence=0.95,
            signals=["no_offer_patterns"]
        )

    def _extract_all_with_regex(self, text: str, text_lower: str) -> List[Dict]:
        """Extract ALL offers using regex patterns (supports multiple offers)"""

        all_offers = []
        conditions = self._extract_conditions(text_lower)

        # Check percentage discounts
        for pattern in self.patterns["percentage_discount"]:
            for match in re.finditer(pattern, text_lower):
                percentage = match.group(1)
                all_offers.append({
                    "offer_type": "percentage_discount",
                    "offer_details": f"{percentage}% off",
                    "offer_conditions": conditions,
                    "confidence": 0.92,
                    "signals": [f"regex:percentage_{percentage}", f"match:{match.group(0)}"]
                })

        # Check fixed discounts
        for pattern in self.patterns["fixed_discount"]:
            for match in re.finditer(pattern, text_lower):
                amount = match.group(1)
                all_offers.append({
                    "offer_type": "fixed_discount",
                    "offer_details": f"QAR {amount} off",
                    "offer_conditions": conditions,
                    "confidence": 0.90,
                    "signals": [f"regex:fixed_{amount}", f"match:{match.group(0)}"]
                })

        # Check free delivery
        for pattern in self.patterns["free_delivery"]:
            if re.search(pattern, text_lower):
                all_offers.append({
                    "offer_type": "free_delivery",
                    "offer_details": "Free delivery",
                    "offer_conditions": conditions,
                    "confidence": 0.95,
                    "signals": ["regex:free_delivery"]
                })
                break  # Only add once

        # Check BOGO
        for pattern in self.patterns["bogo"]:
            if re.search(pattern, text_lower):
                all_offers.append({
                    "offer_type": "bogo",
                    "offer_details": "Buy one, get one offer",
                    "offer_conditions": conditions,
                    "confidence": 0.88,
                    "signals": ["regex:bogo"]
                })
                break

        # Check first order
        for pattern in self.patterns["first_order"]:
            if re.search(pattern, text_lower):
                all_offers.append({
                    "offer_type": "first_order",
                    "offer_details": "First order discount",
                    "offer_conditions": conditions,
                    "confidence": 0.85,
                    "signals": ["regex:first_order"]
                })
                break

        return all_offers

    def _extract_with_regex(self, text: str, text_lower: str) -> Optional[OfferDecision]:
        """Fast path: Regex pattern matching (DEPRECATED - use _extract_all_with_regex)"""

        signals = []

        # Check percentage discounts
        for pattern in self.patterns["percentage_discount"]:
            match = re.search(pattern, text_lower)
            if match:
                percentage = match.group(1)
                signals.append(f"regex:percentage_{percentage}")

                # Check for conditions
                conditions = self._extract_conditions(text_lower)

                return OfferDecision(
                    offer_type="percentage_discount",
                    offer_details=f"{percentage}% off",
                    offer_conditions=conditions,
                    confidence=0.92,
                    signals=signals + [f"match:{match.group(0)}"]
                )

        # Check fixed discounts
        for pattern in self.patterns["fixed_discount"]:
            match = re.search(pattern, text_lower)
            if match:
                amount = match.group(1)
                signals.append(f"regex:fixed_{amount}")
                conditions = self._extract_conditions(text_lower)

                return OfferDecision(
                    offer_type="fixed_discount",
                    offer_details=f"QAR {amount} off",
                    offer_conditions=conditions,
                    confidence=0.90,
                    signals=signals + [f"match:{match.group(0)}"]
                )

        # Check free delivery
        for pattern in self.patterns["free_delivery"]:
            if re.search(pattern, text_lower):
                signals.append("regex:free_delivery")
                conditions = self._extract_conditions(text_lower)

                return OfferDecision(
                    offer_type="free_delivery",
                    offer_details="Free delivery",
                    offer_conditions=conditions,
                    confidence=0.95,
                    signals=signals
                )

        # Check BOGO
        for pattern in self.patterns["bogo"]:
            match = re.search(pattern, text_lower)
            if match:
                signals.append("regex:bogo")

                return OfferDecision(
                    offer_type="bogo",
                    offer_details=match.group(0),
                    confidence=0.93,
                    signals=signals
                )

        return None

    def _extract_conditions(self, text_lower: str) -> Optional[str]:
        """Extract offer conditions (first order, minimum, etc.)"""

        conditions = []

        # Check for first order requirement
        for pattern in self.patterns["first_order"]:
            if re.search(pattern, text_lower):
                conditions.append("first order only")

        # Check for minimum order
        for pattern in self.patterns["minimum_order"]:
            match = re.search(pattern, text_lower)
            if match:
                amount = match.group(1)
                conditions.append(f"min order QAR {amount}")

        # Check for limited time
        for pattern in self.patterns["limited_time"]:
            match = re.search(pattern, text_lower)
            if match:
                conditions.append("limited time")

        return "; ".join(conditions) if conditions else None

    def _check_generic_promo(self, text_lower: str) -> Optional[OfferDecision]:
        """Check for generic promotional language without specific offer"""

        # New product launch
        if any(kw in text_lower for kw in ["new", "جديد", "launch", "إطلاق", "تقديم"]):
            if any(kw in text_lower for kw in ["product", "item", "menu", "منتج", "قائمة"]):
                return OfferDecision(
                    offer_type="new_product",
                    offer_details="New product/menu item",
                    confidence=0.75,
                    signals=["generic:new_product"]
                )

        # Special offer (vague)
        if any(kw in text_lower for kw in ["special offer", "عرض خاص", "عرض", "deal"]):
            return OfferDecision(
                offer_type="special_offer",
                offer_details="Special offer (details unclear)",
                confidence=0.60,
                signals=["generic:special_offer"]
            )

        return None

    def _extract_with_llm(self, text: str) -> OfferDecision:
        """Fallback: LLM extraction for complex offers"""

        prompt = f"""You are analyzing a food delivery advertisement (English or Arabic) to extract promotional offers.

Advertisement Text:
{text[:800]}

Extract the offer information and return VALID JSON (no other text):
{{
    "offer_type": "percentage_discount | fixed_discount | free_delivery | bogo | limited_time | new_product | special_offer | none",
    "offer_details": "Brief description of the offer (e.g., '50% off first order')",
    "offer_conditions": "Any conditions (e.g., 'new customers only', 'min order QAR 50') or null",
    "confidence": 0.0-1.0
}}

Offer Types:
- percentage_discount: "50% off", "30% discount"
- fixed_discount: "QAR 20 off", "$10 discount"
- free_delivery: "Free delivery", "توصيل مجاني"
- bogo: "Buy 1 Get 1 Free"
- limited_time: "Today only", "Limited time"
- new_product: "New item launch"
- special_offer: Generic promotional language
- none: No clear offer

Rules:
- If NO clear offer is mentioned, return offer_type="none"
- Be precise with offer_details (extract exact discount amount)
- Extract conditions if mentioned (first order, minimum, time limit)
"""

        try:
            response = requests.post(
                self.api_url,
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.1, "num_predict": 256}
                },
                timeout=90
            )

            if response.status_code != 200:
                raise Exception(f"LLM API error: {response.status_code}")

            result = response.json()
            response_text = result.get('response', '').strip()

            # Extract JSON
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            if start_idx == -1 or end_idx == 0:
                raise ValueError("No JSON in LLM response")

            offer_data = json.loads(response_text[start_idx:end_idx])

            return OfferDecision(
                offer_type=offer_data.get('offer_type', 'none'),
                offer_details=offer_data.get('offer_details', ''),
                offer_conditions=offer_data.get('offer_conditions'),
                confidence=offer_data.get('confidence', 0.5),
                signals=["llm_extraction"]
            )

        except Exception as e:
            print(f"   ⚠️  LLM extraction failed: {e}")
            return OfferDecision(
                offer_type="none",
                offer_details="",
                confidence=0.3,
                signals=["llm_failure"]
            )
