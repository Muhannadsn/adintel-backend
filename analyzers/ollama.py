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

class OllamaAnalyzer(BaseAnalyzer):
    def __init__(self, api_endpoint="http://localhost:11434/api/chat"):
        self.api_endpoint = api_endpoint

    def analyze_screenshot(self, screenshot: Screenshot) -> Analysis:
        """
        Sends a screenshot to the Ollama API for analysis and returns an Analysis object.
        """
        print(f"Analyzing screenshot: {screenshot.image_path}")

        with open(screenshot.image_path, "rb") as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode('utf-8')

        prompt = """
        Read all text from this advertisement image and extract information.

        Extract ONLY what you see - don't make things up.

        Respond with JSON in this format (replace values with actual content from the ad):

        product_category: What is being advertised? (Food Delivery, Grocery, Restaurant, Electronics, Fashion, etc)
        offer_type: What deal is offered? (Free Delivery, 50% Discount, Buy One Get One, or No Offer if none visible)
        extracted_text: Write out ALL text you see in the ad, exactly as written
        headline: What is the main large text?
        brand_name: What company/brand name do you see?
        products_mentioned: List any specific products or items mentioned
        keywords: List important marketing words you see
        discount_percentage: Any discount shown? (like "50% off" or "Free delivery")
        call_to_action: Any action text? (Order Now, Shop Now, etc)

        Return valid JSON only.
        """

        payload = {
            "model": "llava",  # Vision-capable model
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                },
                {
                    "role": "user",
                    "content": "", # Empty content
                    "images": [encoded_image]
                }
            ],
            "stream": False
        }

        try:
            # Add timeout to prevent hanging
            response = requests.post(self.api_endpoint, json=payload, timeout=120)  # 2 min timeout
            response.raise_for_status()

            response_data = response.json()
            analysis_json_string = response_data.get('message', {}).get('content', '{}')

            print(f"Raw LLM response:\n{analysis_json_string[:500]}...")  # Debug output

            # Use regex to find the JSON block (multiple patterns)
            import re

            # Try different JSON extraction patterns
            json_match = re.search(r'```json\s*\n({.*?})\n```', analysis_json_string, re.DOTALL)
            if not json_match:
                json_match = re.search(r'```\s*\n({.*?})\n```', analysis_json_string, re.DOTALL)
            if not json_match:
                json_match = re.search(r'({[\s\S]*})', analysis_json_string, re.DOTALL)

            if json_match:
                analysis_json_string = json_match.group(1).strip()
            else:
                # If no JSON found, try the whole response
                analysis_json_string = analysis_json_string.strip()

            analysis_json = json.loads(analysis_json_string)

            return Analysis(
                screenshot_id=screenshot.creative_id,
                product_category=analysis_json.get('product_category', 'N/A'),
                offer_type=analysis_json.get('offer_type', 'N/A'),
                messaging=analysis_json.get('messaging', 'N/A'),
                raw_ai_response=json.dumps(response_data),
                extracted_text=analysis_json.get('extracted_text'),
                headline=analysis_json.get('headline'),
                call_to_action=analysis_json.get('call_to_action'),
                discount_percentage=analysis_json.get('discount_percentage'),
                products_mentioned=analysis_json.get('products_mentioned', []),
                keywords=analysis_json.get('keywords', []),
                brand_name=analysis_json.get('brand_name'),
                price_mentioned=analysis_json.get('price_mentioned')
            )
        except requests.exceptions.RequestException as e:
            print(f"Error connecting to Ollama API: {e}")
            return Analysis(
                screenshot_id=screenshot.creative_id,
                product_category="Error",
                offer_type="Error",
                messaging=f"API connection error: {e}",
                raw_ai_response=""
            )
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON from Ollama response: {e}")
            return Analysis(
                screenshot_id=screenshot.creative_id,
                product_category="Error",
                offer_type="Error",
                messaging=f"JSON decode error: {e}",
                raw_ai_response=response.text if 'response' in locals() else ""
            )


if __name__ == '__main__':
    # This assumes you have run the gatc.py script and have a screenshot available
    # You might need to update the path to a real screenshot
    sample_screenshot = Screenshot(
        creative_id=12345,
        image_path='/Users/muhannadsaad/Desktop/ad-intelligence/data/screenshots/creative_Test Advertiser_1760559294.png'
    )

    analyzer = OllamaAnalyzer()
    analysis_result = analyzer.analyze_screenshot(sample_screenshot)
    print(f"Analysis result: {analysis_result}")
