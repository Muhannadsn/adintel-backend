#!/usr/bin/env python3
"""
Web Search Module - Product validation via DuckDuckGo + DeepSeek
Uses DuckDuckGo HTML scraping for free web search (no API key needed)
Uses DeepSeek for intelligent result parsing
"""

import requests
import json
from typing import Dict, List, Optional
from datetime import datetime
from bs4 import BeautifulSoup
import urllib.parse


class WebSearchValidator:
    """
    Validates unknown products using web search

    Flow:
    1. Search product name via SearXNG
    2. Get top results (titles + snippets)
    3. Feed to DeepSeek for classification
    4. Return validated product info
    """

    def __init__(self,
                 ollama_host: str = "http://localhost:11434",
                 model: str = "deepseek-r1:latest"):
        """
        Initialize web search validator

        Args:
            ollama_host: Ollama API endpoint
            model: DeepSeek model name
        """
        self.ollama_host = ollama_host
        self.model = model
        self.api_url = f"{ollama_host}/api/generate"

        print(f"✅ Web Search Validator initialized with {model} + DuckDuckGo")

    def search_product(self, product_name: str, max_results: int = 3) -> List[Dict]:
        """
        Search for product information using DuckDuckGo HTML scraping

        Args:
            product_name: Product/brand name to search
            max_results: Number of results to return

        Returns:
            List of search results with title, url, content
        """
        query = f"What is {product_name}"
        print(f"   🔍 Searching: {query} via DuckDuckGo")

        try:
            # DuckDuckGo HTML search
            encoded_query = urllib.parse.quote_plus(query)
            url = f"https://html.duckduckgo.com/html/?q={encoded_query}"

            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }

            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code != 200:
                print(f"   ❌ DuckDuckGo returned status {response.status_code}")
                return []

            # Parse HTML with BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')

            # Find search results (DuckDuckGo HTML structure)
            results = []
            result_divs = soup.find_all('div', class_='result__body', limit=max_results)

            for div in result_divs:
                # Extract title
                title_tag = div.find('a', class_='result__a')
                title = title_tag.get_text(strip=True) if title_tag else ""

                # Extract URL
                url_tag = div.find('a', class_='result__url')
                result_url = url_tag.get('href', '') if url_tag else ""

                # Extract snippet
                snippet_tag = div.find('a', class_='result__snippet')
                content = snippet_tag.get_text(strip=True) if snippet_tag else ""

                if title and content:
                    results.append({
                        'title': title,
                        'url': result_url,
                        'content': content
                    })

            print(f"   ✅ Found {len(results)} results from DuckDuckGo")
            return results

        except Exception as e:
            print(f"   ❌ DuckDuckGo search failed: {e}")
            return []

    def validate_with_deepseek(self, product_name: str, search_results: List[Dict]) -> Dict:
        """
        Use DeepSeek to classify product based on search results

        Args:
            product_name: Product name being validated
            search_results: Search results from SearXNG

        Returns:
            Dict with validated product info
        """
        # Build context from search results
        search_context = "\n\n".join([
            f"Result {i+1}:\nTitle: {r['title']}\nSnippet: {r['content']}"
            for i, r in enumerate(search_results)
        ])

        prompt = f"""You are analyzing search results to classify a product/brand mentioned in a food delivery advertisement.

Product Name: {product_name}

Search Results:
{search_context}

Based on these search results, answer the following questions:

1. Is "{product_name}" a RESTAURANT or FOOD BRAND?
2. Is "{product_name}" a PHYSICAL PRODUCT (e.g., kitchen appliance, grocery item)?
3. Is "{product_name}" a PLATFORM SUBSCRIPTION SERVICE (e.g., Talabat Pro, Deliveroo Plus)?
4. What CATEGORY does it belong to?

Return your analysis in VALID JSON format (no other text):

{{
    "product_type": "restaurant" | "unknown_category" | "subscription" | "unknown",
    "is_restaurant": true/false,
    "is_unknown_category": true/false,
    "is_subscription": false,
    "category": "specific category name",
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation"
}}

IMPORTANT:
- If it's a restaurant/food brand → product_type: "restaurant"
- If it's a kitchen appliance, grocery item, etc → product_type: "unknown_category"
- If search results are unclear → product_type: "unknown", confidence < 0.5

Return ONLY valid JSON, no other text.
"""

        try:
            print(f"   🤖 Validating with DeepSeek...")

            response = requests.post(
                self.api_url,
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,  # Low temp for factual classification
                        "num_predict": 512
                    }
                },
                timeout=90
            )

            if response.status_code != 200:
                raise Exception(f"DeepSeek API error: {response.status_code}")

            result = response.json()
            response_text = result.get('response', '').strip()

            # Parse JSON from response
            # Remove markdown code blocks if present
            if response_text.startswith('```'):
                lines = response_text.split('\n')
                response_text = '\n'.join(lines[1:-1])

            # Extract JSON
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1

            if start_idx == -1 or end_idx == 0:
                raise ValueError("No JSON found in DeepSeek response")

            json_str = response_text[start_idx:end_idx]
            validation = json.loads(json_str)

            print(f"   ✅ DeepSeek classified as: {validation.get('product_type')} (confidence: {validation.get('confidence', 0):.2f})")

            return validation

        except Exception as e:
            print(f"   ❌ DeepSeek validation failed: {e}")
            # Return low-confidence unknown
            return {
                "product_type": "unknown",
                "is_restaurant": False,
                "is_unknown_category": False,
                "is_subscription": False,
                "category": "Unknown",
                "confidence": 0.3,
                "reasoning": f"Validation error: {str(e)}"
            }

    def validate_product(self, product_name: str) -> Dict:
        """
        Full validation pipeline: Search + Classify

        Args:
            product_name: Product/brand name to validate

        Returns:
            Dict with validated product info ready for caching
        """
        print(f"\n{'='*70}")
        print(f"🔍 VALIDATING PRODUCT: {product_name}")
        print(f"{'='*70}")

        # Step 1: Search web
        search_results = self.search_product(product_name)

        if not search_results:
            print("   ❌ No search results found - cannot validate")
            return {
                "product_name": product_name,
                "product_type": "unknown",
                "is_restaurant": False,
                "is_unknown_category": False,
                "is_subscription": False,
                "category": "Unknown",
                "confidence": 0.2,
                "search_source": "duckduckgo_failed",
                "cache_this": False,
                "validated_date": datetime.now().isoformat()
            }

        # Step 2: Validate with DeepSeek
        validation = self.validate_with_deepseek(product_name, search_results)

        # Step 3: Format for caching
        cached_data = {
            "product_name": product_name,
            "product_type": validation.get('product_type', 'unknown'),
            "category": validation.get('category', 'Unknown'),
            "is_restaurant": validation.get('is_restaurant', False),
            "is_unknown_category": validation.get('is_unknown_category', False),
            "is_subscription": validation.get('is_subscription', False),
            "metadata": {
                "reasoning": validation.get('reasoning', ''),
                "search_results_count": len(search_results)
            },
            "confidence": validation.get('confidence', 0.5),
            "search_source": "duckduckgo",
            "cache_this": validation.get('confidence', 0) >= 0.7,  # Only cache if confident
            "validated_date": datetime.now().isoformat()
        }

        print(f"{'='*70}")
        print(f"✅ VALIDATION COMPLETE")
        print(f"   Type: {cached_data['product_type']}")
        print(f"   Category: {cached_data['category']}")
        print(f"   Confidence: {cached_data['confidence']:.2f}")
        print(f"   Cache: {'YES' if cached_data['cache_this'] else 'NO (low confidence)'}")
        print(f"{'='*70}\n")

        return cached_data


# ============================================================================
# Test Function
# ============================================================================

def test_web_search():
    """Test the web search validator with sample products"""
    print("=" * 70)
    print("TESTING WEB SEARCH VALIDATOR")
    print("=" * 70)

    validator = WebSearchValidator()

    # Test cases
    test_products = [
        "Nutribullet",      # Physical product
        "McDonald's",       # Restaurant
        "Haldiram's",       # Restaurant/brand
        "Talabat Pro"       # Subscription service
    ]

    for product in test_products:
        result = validator.validate_product(product)
        print(f"\n{'='*70}")
        print(f"Product: {product}")
        print(f"Result: {json.dumps(result, indent=2)}")
        print(f"{'='*70}\n")


if __name__ == "__main__":
    test_web_search()
