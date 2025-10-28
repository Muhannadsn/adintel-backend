#!/usr/bin/env python3
"""
DeepSeek-OCR Client
Wrapper to call the DeepSeek-OCR microservice
"""

import requests
from typing import Dict, Optional
import time


class DeepSeekOCRClient:
    """
    Client for DeepSeek-OCR microservice

    Usage:
        client = DeepSeekOCRClient()
        result = client.extract_text(image_url="https://...")
    """

    def __init__(self, service_url: str = "http://localhost:8001"):
        """
        Initialize client

        Args:
            service_url: URL of DeepSeek-OCR service
        """
        self.service_url = service_url
        self.ocr_endpoint = f"{service_url}/ocr"
        self.health_endpoint = f"{service_url}/health"

    def health_check(self) -> bool:
        """
        Check if DeepSeek-OCR service is running

        Returns:
            True if healthy, False otherwise
        """
        try:
            response = requests.get(self.health_endpoint, timeout=2)
            return response.status_code == 200
        except:
            return False

    def extract_text(self,
                     image_url: Optional[str] = None,
                     image_base64: Optional[str] = None,
                     prompt: str = "<image>\n<|grounding|>Extract all text from this advertisement.",
                     timeout: int = 60) -> Dict:
        """
        Extract text from image using DeepSeek-OCR

        Args:
            image_url: URL to image
            image_base64: Base64-encoded image (alternative to URL)
            prompt: OCR prompt (task-specific)
            timeout: Request timeout in seconds

        Returns:
            {
                "raw_text": "full extracted text",
                "structured": [
                    {
                        "text": "extracted element",
                        "coordinates": [[x1,y1,x2,y2]],
                        "type": "price|product|brand|general"
                    },
                    ...
                ],
                "processing_time": 3.5,
                "model": "deepseek-ocr"
            }

        Raises:
            Exception if service is down or OCR fails
        """
        if not image_url and not image_base64:
            raise ValueError("Provide either image_url or image_base64")

        payload = {
            "prompt": prompt,
            "base_size": 1024,
            "image_size": 640,
            "crop_mode": True
        }

        if image_url:
            payload["image_url"] = image_url
        else:
            payload["image_base64"] = image_base64

        try:
            response = requests.post(
                self.ocr_endpoint,
                json=payload,
                timeout=timeout
            )

            if response.status_code != 200:
                error_detail = response.json().get('detail', 'Unknown error')
                raise Exception(f"DeepSeek-OCR failed: {error_detail}")

            return response.json()

        except requests.exceptions.Timeout:
            raise Exception("DeepSeek-OCR service timeout")
        except requests.exceptions.ConnectionError:
            raise Exception("Cannot connect to DeepSeek-OCR service. Is it running?")
        except Exception as e:
            raise Exception(f"DeepSeek-OCR error: {str(e)}")


# Task-specific prompt templates
DEEPSEEK_PROMPTS = {
    "general": "<image>\n<|grounding|>Extract all text from this advertisement.",

    "product": """<image>
<|grounding|>Identify and extract product information from this advertisement.

Extract:
1. Product name (e.g., "Big Mac", "Pepperoni Pizza")
2. Restaurant/brand (e.g., "McDonald's", "Domino's")
3. Food category (e.g., "Burgers", "Pizza", "Arabic Food")

Use grounding annotations to mark each element.""",

    "prices": """<image>
<|grounding|>Extract all pricing and promotional information.

Find:
- Base prices (e.g., "50 QAR")
- Discounts (e.g., "50% off", "Buy 1 Get 1")
- Special offers
- Time-limited deals

Mark each price with bounding box.""",

    "ingredients": """<image>
<|grounding|>Extract nutritional and ingredient information.

Look for:
- Ingredients list
- Nutritional facts
- Allergen warnings
- Calorie counts
- Arabic ingredient lists

Mark each element with coordinates.""",
}


# Example usage
if __name__ == "__main__":
    # Test client
    client = DeepSeekOCRClient()

    # Check health
    print("Checking DeepSeek-OCR service...")
    if client.health_check():
        print("✅ Service is healthy")
    else:
        print("❌ Service is not running")
        print("   Start it with: cd ~/Desktop/DeepSeek-OCR && source venv/bin/activate && python deepseek_service.py")
        exit(1)

    # Test OCR (you need to provide a real image URL)
    print("\nTest OCR extraction:")
    test_url = input("Enter image URL to test (or press Enter to skip): ").strip()

    if test_url:
        try:
            result = client.extract_text(
                image_url=test_url,
                prompt=DEEPSEEK_PROMPTS["general"]
            )

            print(f"\n✅ OCR completed in {result['processing_time']:.2f}s")
            print(f"Raw text length: {len(result['raw_text'])} chars")
            print(f"Structured elements: {len(result['structured'])}")
            print(f"\nPreview:")
            print(result['raw_text'][:500])

        except Exception as e:
            print(f"❌ OCR failed: {e}")
