#!/usr/bin/env python3
"""
Simple LLM-based extractor - no regex, no catalogs, just ask the LLM.
A direct comparison to the complex rule-based approach.
"""
import json
import requests
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class SimpleLLMResult:
    """Clean extraction result from LLM"""
    brand_name: str
    product_category: str
    offer_type: str
    offer_details: str
    confidence: float
    raw_response: str


class SimpleLLMExtractor:
    """
    Dead simple approach: Just ask the LLM to extract everything.
    No regex, no catalogs, no heuristics, no bullshit.
    """

    def __init__(
        self,
        ollama_host: str = "http://localhost:11434",
        model: str = "llama3.1:8b",
        formatter_model: str = "deepseek-r1:1.5b"
    ):
        self.ollama_host = ollama_host
        self.model = model
        self.formatter_model = formatter_model
        self.api_url = f"{ollama_host}/api/generate"

    def extract(self, text: str) -> SimpleLLMResult:
        """
        Extract brand, category, and offers from ad text using pure LLM.
        """

        prompt = f"""You are analyzing a food delivery or retail advertisement. Extract the key information.

Advertisement Text:
{text[:1000]}

IMPORTANT: Return ONLY valid JSON with double quotes ("), no other text or explanation.

Extract and return this exact JSON structure:
{{
    "brand_name": "The restaurant or brand name",
    "product_category": "restaurant | electronics | grocery | fashion | beauty | pharmacy | sports | home_appliances | toys | entertainment | flowers | beverages | sweets_desserts",
    "offer_type": "percentage_discount | fixed_discount | free_delivery | bogo | new_product | none",
    "offer_details": "Brief description",
    "confidence": 0.9
}}

Rules:
- brand_name: Extract the MAIN brand/restaurant name only (not menu items)
  Examples: "TGI Friday's" NOT "TGI Friday's Mozzarella Sticks"
            "McDonald's" NOT "McDonald's Big Mac"
- product_category: Choose ONE category only
- offer_type: Choose ONE offer type only
- offer_details: Maximum 10 words, extract ONLY the core offer
  Examples: "Free delivery on all orders"
            "70% off mid-month deals"
            "Buy 1 Get 1 Free"
  BAD: Long descriptions or full ad copy
- confidence: 0.0 to 1.0

Return ONLY the JSON, nothing else.
"""

        try:
            response = requests.post(
                self.api_url,
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,
                        "num_predict": 256
                    }
                },
                timeout=90
            )

            if response.status_code != 200:
                raise Exception(f"LLM API error: {response.status_code}")

            result = response.json()
            response_text = result.get('response', '').strip()

            # Extract JSON from response
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1

            if start_idx == -1 or end_idx == 0:
                raise ValueError("No JSON in LLM response")

            json_str = response_text[start_idx:end_idx]

            # Try to parse JSON, with fallback to DeepSeek formatter
            try:
                extracted = json.loads(json_str)
            except json.JSONDecodeError as e:
                # Llama generated invalid JSON - use DeepSeek to fix it
                print(f"      ⚠️  JSON parsing failed, using DeepSeek formatter...")
                fixed_json = self._format_with_deepseek(response_text)
                if fixed_json:
                    extracted = fixed_json
                    print(f"      ✅ DeepSeek fixed the JSON")
                else:
                    print(f"      ❌ DeepSeek could not fix JSON")
                    raise ValueError(f"Invalid JSON from LLM: {e}")

            return SimpleLLMResult(
                brand_name=extracted.get('brand_name', 'Unknown'),
                product_category=extracted.get('product_category', 'unknown'),
                offer_type=extracted.get('offer_type', 'none'),
                offer_details=extracted.get('offer_details', ''),
                confidence=float(extracted.get('confidence', 0.5)),
                raw_response=response_text
            )

        except Exception as e:
            print(f"   ⚠️  Simple LLM extraction failed: {e}")
            return SimpleLLMResult(
                brand_name="Unknown",
                product_category="unknown",
                offer_type="none",
                offer_details="",
                confidence=0.0,
                raw_response=str(e)
            )

    def _format_with_deepseek(self, malformed_response: str) -> Optional[Dict]:
        """
        Use DeepSeek-R1 to fix malformed JSON from Llama
        """

        formatter_prompt = f"""Fix this malformed JSON to be valid JSON with proper double quotes.

Malformed JSON:
{malformed_response[:500]}

Return ONLY valid JSON (no explanation):
{{
    "brand_name": "...",
    "product_category": "...",
    "offer_type": "...",
    "offer_details": "...",
    "confidence": 0.9
}}"""

        try:
            response = requests.post(
                self.api_url,
                json={
                    "model": self.formatter_model,
                    "prompt": formatter_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.0,
                        "num_predict": 128
                    }
                },
                timeout=30
            )

            if response.status_code != 200:
                return None

            result = response.json()
            response_text = result.get('response', '').strip()

            # Extract JSON
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1

            if start_idx == -1 or end_idx == 0:
                return None

            fixed_json = json.loads(response_text[start_idx:end_idx])
            return fixed_json

        except Exception:
            return None


def test_simple_extractor():
    """Quick test of the simple extractor"""
    extractor = SimpleLLMExtractor()

    test_cases = [
        "Tgi Fridays Mozzarella Sticks 50% off your first order",
        "McDonald's Big Mac meal deal - Buy 1 Get 1 Free",
        "Apple iPhone 15 Pro - 20% discount on Rafeeq Pro",
        "Al Wakrah Sweets - Fresh desserts delivered free"
    ]

    print("=" * 70)
    print("SIMPLE LLM EXTRACTOR TEST")
    print("=" * 70)

    for text in test_cases:
        print(f"\n📝 Text: {text}")
        result = extractor.extract(text)
        print(f"   Brand: {result.brand_name}")
        print(f"   Category: {result.product_category}")
        print(f"   Offer: {result.offer_type} - {result.offer_details}")
        print(f"   Confidence: {result.confidence:.2f}")


if __name__ == "__main__":
    test_simple_extractor()
