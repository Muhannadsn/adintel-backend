import sys
import os
import requests
import base64
import json

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from analyzers.base import BaseAnalyzer
from models.ad_creative import Analysis, Screenshot


class HybridAnalyzer(BaseAnalyzer):
    """
    Two-stage hybrid analyzer for speed optimization:
    Stage 1: llava (vision) - Extract text only (~30 sec)
    Stage 2: deepseek-r1 (text) - Analyze extracted text (~10 sec)

    Total: ~40 sec vs 2+ minutes with llava alone
    """

    def __init__(self, api_endpoint="http://localhost:11434/api/chat"):
        self.api_endpoint = api_endpoint

    def analyze_screenshot(self, screenshot: Screenshot) -> Analysis:
        """
        Two-stage analysis:
        1. Vision model extracts text
        2. Fast text model analyzes the extracted text
        """
        print(f"Analyzing screenshot: {screenshot.image_path}")

        # STAGE 1: Extract text with llava (vision model)
        print("  Stage 1: Extracting text with llava...")
        extracted_text = self._extract_text_with_vision(screenshot)

        if not extracted_text or extracted_text == "Error":
            print("  Failed to extract text, returning error")
            return Analysis(
                screenshot_id=screenshot.creative_id,
                product_category="Error",
                offer_type="Error",
                messaging="Failed to extract text from image",
                raw_ai_response=""
            )

        # STAGE 2: Analyze text with deepseek-r1 (fast text model)
        print(f"  Stage 2: Analyzing text with deepseek-r1...")
        print(f"  Extracted text: {extracted_text[:100]}...")

        return self._analyze_text_with_deepseek(screenshot, extracted_text)

    def _extract_text_with_vision(self, screenshot: Screenshot) -> str:
        """Stage 1: Use llava to extract ALL visible text from image"""

        with open(screenshot.image_path, "rb") as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode('utf-8')

        prompt = """
        Extract ALL text you see in this advertisement image.
        Write out every word, exactly as shown.

        Just return the text, nothing else.
        """

        payload = {
            "model": "llava",
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                },
                {
                    "role": "user",
                    "content": "",
                    "images": [encoded_image]
                }
            ],
            "stream": False
        }

        try:
            response = requests.post(self.api_endpoint, json=payload, timeout=60)
            response.raise_for_status()

            response_data = response.json()
            extracted_text = response_data.get('message', {}).get('content', '')

            return extracted_text.strip()

        except Exception as e:
            print(f"  Error extracting text: {e}")
            return "Error"

    def _analyze_text_with_deepseek(self, screenshot: Screenshot, extracted_text: str) -> Analysis:
        """Stage 2: Use deepseek-r1 to analyze the extracted text"""

        prompt = f"""
        You are analyzing advertisement text. Extract structured information from this ad text:

        AD TEXT:
        {extracted_text}

        Return ONLY a JSON object with these fields:
        {{
          "product_category": "Food Delivery/Grocery/Restaurant/Fashion/Electronics/etc",
          "offer_type": "Free Delivery/X% Discount/Buy One Get One/No Offer",
          "messaging": "One sentence summary of ad message",
          "headline": "Main headline from the text",
          "call_to_action": "Any CTA text like Order Now/Shop Now/null",
          "discount_percentage": "Any discount like 50% off/Free/null",
          "products_mentioned": ["list", "of", "products"],
          "keywords": ["key", "marketing", "words"],
          "brand_name": "Brand name mentioned",
          "price_mentioned": "Any price mentioned"
        }}

        Return ONLY valid JSON, no explanation.
        """

        payload = {
            "model": "deepseek-r1:latest",
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "stream": False
        }

        try:
            response = requests.post(self.api_endpoint, json=payload, timeout=90)  # 90 sec for deepseek
            response.raise_for_status()

            response_data = response.json()
            analysis_json_string = response_data.get('message', {}).get('content', '{}')

            # Parse JSON from response
            import re
            json_match = re.search(r'```json\s*\n({.*?})\n```', analysis_json_string, re.DOTALL)
            if not json_match:
                json_match = re.search(r'({[\s\S]*})', analysis_json_string, re.DOTALL)

            if json_match:
                analysis_json_string = json_match.group(1).strip()
            else:
                analysis_json_string = analysis_json_string.strip()

            analysis_json = json.loads(analysis_json_string)

            return Analysis(
                screenshot_id=screenshot.creative_id,
                product_category=analysis_json.get('product_category', 'N/A'),
                offer_type=analysis_json.get('offer_type', 'N/A'),
                messaging=analysis_json.get('messaging', 'N/A'),
                raw_ai_response=json.dumps(response_data),
                extracted_text=extracted_text,
                headline=analysis_json.get('headline'),
                call_to_action=analysis_json.get('call_to_action'),
                discount_percentage=analysis_json.get('discount_percentage'),
                products_mentioned=analysis_json.get('products_mentioned', []),
                keywords=analysis_json.get('keywords', []),
                brand_name=analysis_json.get('brand_name'),
                price_mentioned=analysis_json.get('price_mentioned')
            )

        except requests.exceptions.RequestException as e:
            print(f"  Error with deepseek API: {e}")
            return Analysis(
                screenshot_id=screenshot.creative_id,
                product_category="Error",
                offer_type="Error",
                messaging=f"API error: {e}",
                raw_ai_response="",
                extracted_text=extracted_text
            )
        except json.JSONDecodeError as e:
            print(f"  Error decoding JSON: {e}")
            return Analysis(
                screenshot_id=screenshot.creative_id,
                product_category="Error",
                offer_type="Error",
                messaging=f"JSON decode error: {e}",
                raw_ai_response=response.text if 'response' in locals() else "",
                extracted_text=extracted_text
            )


if __name__ == '__main__':
    # Test with existing screenshot
    sample_screenshot = Screenshot(
        creative_id=12345,
        image_path='/Users/muhannadsaad/Desktop/ad-intelligence/data/screenshots/creative_DELIVERY_HERO_TALABAT_DB_L.L.C_1760562261.png'
    )

    analyzer = HybridAnalyzer()
    analysis_result = analyzer.analyze_screenshot(sample_screenshot)
    print(f"\nAnalysis result:")
    print(f"Category: {analysis_result.product_category}")
    print(f"Offer: {analysis_result.offer_type}")
    print(f"Headline: {analysis_result.headline}")
    print(f"Products: {analysis_result.products_mentioned}")
    print(f"Keywords: {analysis_result.keywords}")
