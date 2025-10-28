import sys
import os
import base64
import json
from anthropic import Anthropic

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from analyzers.base import BaseAnalyzer
from models.ad_creative import Analysis, Screenshot


class ClaudeAnalyzer(BaseAnalyzer):
    """
    Uses Claude API (Anthropic) for vision-based ad analysis.
    Requires ANTHROPIC_API_KEY environment variable.
    """

    def __init__(self, api_key: str = None):
        self.client = Anthropic(api_key=api_key or os.environ.get("ANTHROPIC_API_KEY"))

    def analyze_screenshot(self, screenshot: Screenshot) -> Analysis:
        """
        Sends a screenshot to Claude API for analysis and returns an Analysis object.
        """
        print(f"Analyzing screenshot: {screenshot.image_path}")

        # Read and encode image
        with open(screenshot.image_path, "rb") as image_file:
            image_data = base64.standard_b64encode(image_file.read()).decode("utf-8")

        # Determine image type
        image_ext = screenshot.image_path.lower().split('.')[-1]
        media_type = f"image/{image_ext}" if image_ext in ['png', 'jpeg', 'jpg', 'webp', 'gif'] else "image/png"

        prompt = """
        Analyze this advertisement screenshot and extract ALL information. Return a JSON object with these fields:

        - "product_category": Main category (e.g., "Food Delivery", "Grocery", "Restaurant", "Fashion")
        - "offer_type": Promotion type (e.g., "Free Delivery", "Percentage Discount", "Buy One Get One", "No Offer")
        - "messaging": Brief summary of main message
        - "extracted_text": ALL visible text (exact words)
        - "headline": Main headline/title
        - "call_to_action": CTA text (e.g., "Order Now", "Shop Now")
        - "discount_percentage": Any discount (e.g., "50% off", "Buy 1 Get 1 Free")
        - "products_mentioned": Array of specific products (e.g., ["Cake", "Grocery"])
        - "keywords": Array of marketing keywords (e.g., ["delivery", "fast", "easy"])
        - "brand_name": Brand/company name
        - "price_mentioned": Any price shown

        Return ONLY valid JSON, no other text.
        """

        try:
            message = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1024,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": image_data,
                                },
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ],
                    }
                ],
            )

            # Extract response
            response_text = message.content[0].text

            print(f"Raw Claude response:\n{response_text[:500]}...")

            # Parse JSON from response
            import re
            json_match = re.search(r'```json\s*\n({.*?})\n```', response_text, re.DOTALL)
            if not json_match:
                json_match = re.search(r'({[\s\S]*})', response_text, re.DOTALL)

            if json_match:
                analysis_json_string = json_match.group(1).strip()
            else:
                analysis_json_string = response_text.strip()

            analysis_json = json.loads(analysis_json_string)

            return Analysis(
                screenshot_id=screenshot.creative_id,
                product_category=analysis_json.get('product_category', 'N/A'),
                offer_type=analysis_json.get('offer_type', 'N/A'),
                messaging=analysis_json.get('messaging', 'N/A'),
                raw_ai_response=json.dumps(dict(message)),
                extracted_text=analysis_json.get('extracted_text'),
                headline=analysis_json.get('headline'),
                call_to_action=analysis_json.get('call_to_action'),
                discount_percentage=analysis_json.get('discount_percentage'),
                products_mentioned=analysis_json.get('products_mentioned', []),
                keywords=analysis_json.get('keywords', []),
                brand_name=analysis_json.get('brand_name'),
                price_mentioned=analysis_json.get('price_mentioned')
            )

        except Exception as e:
            print(f"Error with Claude API: {e}")
            return Analysis(
                screenshot_id=screenshot.creative_id,
                product_category="Error",
                offer_type="Error",
                messaging=f"API error: {e}",
                raw_ai_response=""
            )


if __name__ == '__main__':
    # Test with existing screenshot
    sample_screenshot = Screenshot(
        creative_id=12345,
        image_path='/Users/muhannadsaad/Desktop/ad-intelligence/data/screenshots/creative_DELIVERY_HERO_TALABAT_DB_L.L.C_1760562261.png'
    )

    analyzer = ClaudeAnalyzer()
    analysis_result = analyzer.analyze_screenshot(sample_screenshot)
    print(f"\nAnalysis result:")
    print(f"Category: {analysis_result.product_category}")
    print(f"Offer: {analysis_result.offer_type}")
    print(f"Headline: {analysis_result.headline}")
    print(f"Products: {analysis_result.products_mentioned}")
    print(f"Keywords: {analysis_result.keywords}")
