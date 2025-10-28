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
                 model: str = "llama3.1:8b"):
        """
        Initialize web search validator

        Args:
            ollama_host: Ollama API endpoint
            model: LLM model name (using llama3.1:8b for speed)
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
        # Always use "What is" prefix for better definitional results
        # This helps DuckDuckGo return more informative content for classification
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

        prompt = f"""You are analyzing search results to classify a product/brand mentioned in an advertisement.

Product Name: {product_name}

Search Results:
{search_context}

Based on these search results, classify this product into ONE of the following categories:

PRODUCT TYPES (with examples):
- restaurant: Food establishments, cafes, dining chains (McDonald's, Subway, local cafes)
- electronics: Phones, TVs, computers, smart devices (Samsung Galaxy, iPhone, PS5, laptops)
- home_appliances: Kitchen appliances, cleaning devices (NutriBullet, washing machine, fridge, microwave)
- fashion: ALL clothing & accessories - modern OR traditional (dejellaba, kaftan, jalabiya, abaya, dress, shirt, shoes, handbags, jewelry, traditional garments, men's/women's clothing)
- beauty: Cosmetics, skincare, perfumes, personal care, wellness products, health & beauty supplements (makeup, lotion, fragrance, shampoo, Anuage Biolance, skincare products, beauty supplements, health supplements, wellness brands)
- sports: Athletic gear, fitness equipment, sportswear (dumbbells, yoga mat, running shoes, gym clothes)
- pharmacy: Medicine, health products, medical supplies (vitamins, pain relief, prescription drugs, medical devices)
- toys: Children's toys, games, entertainment products (dolls, board games, video games)
- subscription: Platform memberships, delivery subscriptions (Talabat Pro, Netflix, Amazon Prime, Rafeeq)
- category_promotion: Generic category ads (e.g., "All Electronics 50% Off", "Summer Fashion Sale")
- unknown: Cannot determine from search results

IMPORTANT CLARIFICATIONS:
- If the product is ANY type of clothing/garment (traditional OR modern), choose "fashion"
- "Traditional garments", "men's clothing", "women's clothing" → ALL are "fashion"
- If the product is skincare, cosmetics, beauty supplements, health & wellness products → choose "beauty"
- "Health & Wellness", "Skincare", "Beauty Products", "Supplements" → ALL are "beauty"
- Only use "pharmacy" for actual medicine/medical supplies, not beauty/wellness products

Return your analysis in VALID JSON format (no other text):

{{
    "product_type": "one of the types above",
    "category": "specific category name",
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation based on search results"
}}

IMPORTANT:
- Use the MOST SPECIFIC product_type that matches the search results
- High confidence (>0.7) only if search results clearly identify the product
- Low confidence (<0.5) if search results are ambiguous or irrelevant

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
