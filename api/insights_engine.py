#!/usr/bin/env python3
"""
AI-Powered Insights Engine with Vision Analysis
Analyzes competitor ad images using Llava and generates intelligent insights
"""
import json
import csv
import base64
import requests
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from collections import Counter
import io
from PIL import Image


class VisionAnalyzer:
    """Analyze ad images using Llava vision model"""

    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_url
        self.vision_model = "llava:latest"

    def analyze_ad_image(self, image_url: str) -> Dict[str, Any]:
        """
        Analyze a single ad image to extract themes, content, and strategy

        Returns:
            {
                'category': 'food|promo|brand|product',
                'has_text': bool,
                'text_content': str,
                'primary_theme': str,
                'colors': str,
                'emotion': str
            }
        """
        try:
            # Download image
            img_response = requests.get(image_url, timeout=10)
            if img_response.status_code != 200:
                return self._default_analysis()

            # Convert to base64
            img_base64 = base64.b64encode(img_response.content).decode('utf-8')

            # Analyze with Llava
            prompt = """Analyze this advertisement image and extract key information.

Return ONLY a JSON object with this exact structure:
{
  "category": "food|promo|brand|product|service",
  "has_text": true/false,
  "text_content": "any text visible in the image",
  "primary_theme": "brief description of main visual theme",
  "visual_elements": "what's shown (people, food, products, etc.)",
  "colors": "dominant colors",
  "emotion": "energetic|calm|urgent|friendly|professional"
}

Focus on marketing strategy - is this about food appeal, discounts/promos, brand building, or product features?"""

            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.vision_model,
                    "prompt": prompt,
                    "images": [img_base64],
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "num_predict": 300
                    }
                },
                timeout=45
            )

            if response.status_code == 200:
                result = response.json()['response']
                return self._parse_vision_result(result)
            else:
                return self._default_analysis()

        except Exception as e:
            print(f"Error analyzing image {image_url}: {e}")
            return self._default_analysis()

    def _parse_vision_result(self, result: str) -> Dict[str, Any]:
        """Parse Llava's response"""
        try:
            # Find JSON in response
            start_idx = result.find('{')
            end_idx = result.rfind('}') + 1

            if start_idx != -1 and end_idx > start_idx:
                json_str = result[start_idx:end_idx]
                return json.loads(json_str)
            else:
                return self._default_analysis()
        except:
            return self._default_analysis()

    def _default_analysis(self) -> Dict[str, Any]:
        """Default analysis when vision fails"""
        return {
            'category': 'unknown',
            'has_text': False,
            'text_content': '',
            'primary_theme': 'generic',
            'visual_elements': 'unknown',
            'colors': 'unknown',
            'emotion': 'neutral'
        }


class InsightsEngine:
    """Generate AI-powered competitive intelligence insights with vision analysis"""

    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_url
        self.text_model = "llama3.1:8b"
        self.vision_analyzer = VisionAnalyzer(ollama_url)

    def analyze_competitor_data(
        self,
        competitors_data: List[Dict[str, Any]],
        csv_dir: Path,
        sample_size: int = 10  # Analyze top N ads per competitor
    ) -> List[Dict[str, Any]]:
        """
        Analyze all competitor data with vision AI and generate 3 insights

        Args:
            competitors_data: List of competitor summaries
            csv_dir: Directory containing CSV files with ad data
            sample_size: Number of ads to analyze per competitor (default: 10)

        Returns:
            List of 3 insights with title, description, metric, type, cta, link
        """
        if not competitors_data:
            return []

        print("🔍 Analyzing competitor ad campaigns with Vision AI...")

        # Gather comprehensive data including vision analysis
        analysis_data = self._gather_analysis_data(competitors_data, csv_dir, sample_size)

        # Generate AI insights using text LLM
        insights = self._generate_ai_insights(analysis_data)

        return insights[:3]

    def _gather_analysis_data(
        self,
        competitors_data: List[Dict[str, Any]],
        csv_dir: Path,
        sample_size: int
    ) -> Dict[str, Any]:
        """Gather comprehensive data including vision analysis of ad images"""

        analysis = {
            "total_competitors": len(competitors_data),
            "total_ads": sum(c.get('total_ads', 0) for c in competitors_data),
            "competitors": []
        }

        for competitor in competitors_data:
            print(f"  📊 Analyzing {competitor.get('name', 'Unknown')}...")

            csv_file = Path(competitor.get('csv_file', ''))

            competitor_analysis = {
                "name": competitor.get('name', 'Unknown'),
                "advertiser_id": competitor.get('advertiser_id', ''),
                "total_ads": competitor.get('total_ads', 0),
                "last_scraped": str(competitor.get('last_scraped', '')),
            }

            # Read and analyze ads
            if csv_file.exists():
                try:
                    with open(csv_file, 'r') as f:
                        reader = csv.DictReader(f)
                        ads = list(reader)

                        # Filter ads with images
                        ads_with_images = [ad for ad in ads if ad.get('image_url')]

                        # Analyze timing patterns
                        recent_ads = 0
                        now = datetime.now().timestamp()
                        week_ago = (datetime.now() - timedelta(days=7)).timestamp()

                        for ad in ads:
                            last_shown = ad.get('last_shown', '')
                            if last_shown:
                                try:
                                    if int(last_shown) > week_ago:
                                        recent_ads += 1
                                except:
                                    pass

                        # Vision analysis on sample
                        vision_results = []
                        sample_ads = ads_with_images[:sample_size]

                        print(f"    🖼️  Analyzing {len(sample_ads)} ad images with Llava...")

                        for idx, ad in enumerate(sample_ads):
                            img_url = ad.get('image_url', '')
                            if img_url:
                                print(f"      [{idx+1}/{len(sample_ads)}] Analyzing creative...")
                                vision_analysis = self.vision_analyzer.analyze_ad_image(img_url)
                                vision_results.append(vision_analysis)

                        # Aggregate vision insights (safely handle missing keys)
                        categories = Counter(r.get('category', 'unknown') for r in vision_results)
                        themes = Counter(r.get('primary_theme', 'generic') for r in vision_results)
                        emotions = Counter(r.get('emotion', 'neutral') for r in vision_results)
                        has_text_count = sum(1 for r in vision_results if r.get('has_text', False))

                        # Extract common text patterns
                        text_samples = [r.get('text_content', '') for r in vision_results if r.get('text_content')]

                        competitor_analysis["ad_details"] = {
                            "total": len(ads),
                            "with_images": len(ads_with_images),
                            "recent_ads_7d": recent_ads,
                            "analyzed_sample": len(vision_results)
                        }

                        competitor_analysis["visual_strategy"] = {
                            "top_category": categories.most_common(1)[0][0] if categories else 'unknown',
                            "category_breakdown": dict(categories),
                            "top_theme": themes.most_common(1)[0][0] if themes else 'generic',
                            "top_emotion": emotions.most_common(1)[0][0] if emotions else 'neutral',
                            "text_heavy": (has_text_count / len(vision_results) * 100) if vision_results else 0,
                            "sample_text": text_samples[:3]  # Top 3 text samples
                        }

                except Exception as e:
                    print(f"    ❌ Error analyzing {competitor.get('name')}: {e}")
                    import traceback
                    traceback.print_exc()
                    competitor_analysis["ad_details"] = {"total": competitor.get('total_ads', 0)}
                    competitor_analysis["visual_strategy"] = {}
            else:
                # CSV file doesn't exist
                competitor_analysis["ad_details"] = {"total": competitor.get('total_ads', 0)}
                competitor_analysis["visual_strategy"] = {}

            analysis["competitors"].append(competitor_analysis)

        # Sort by total ads
        analysis["competitors"] = sorted(
            analysis["competitors"],
            key=lambda x: x['total_ads'],
            reverse=True
        )

        return analysis

    def _generate_ai_insights(self, analysis_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Use LLM to generate intelligent insights from vision analysis"""

        prompt = self._create_insights_prompt(analysis_data)

        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.text_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "num_predict": 1000
                    }
                },
                timeout=60
            )

            if response.status_code == 200:
                ai_response = response.json()['response']
                insights = self._parse_ai_response(ai_response, analysis_data)
                return insights
            else:
                print(f"LLM API error: {response.status_code}")
                return self._fallback_insights(analysis_data)

        except Exception as e:
            print(f"Error calling LLM: {e}")
            return self._fallback_insights(analysis_data)

    def _create_insights_prompt(self, analysis_data: Dict[str, Any]) -> str:
        """Create detailed prompt with vision analysis data"""

        competitors_summary = []
        for c in analysis_data['competitors']:
            visual = c.get('visual_strategy', {})
            ads = c.get('ad_details', {})

            summary = f"""- {c['name']}: {c['total_ads']} total ads
  • Visual Strategy: {visual.get('top_category', 'unknown')} focus ({visual.get('text_heavy', 0):.0f}% text-heavy)
  • Creative Theme: {visual.get('top_theme', 'generic')}
  • Tone: {visual.get('top_emotion', 'neutral')}
  • Recent Activity: {ads.get('recent_ads_7d', 0)} ads in last 7 days
  • Categories: {visual.get('category_breakdown', {})}"""

            if visual.get('sample_text'):
                summary += f"\n  • Sample Messages: {', '.join(visual['sample_text'][:2])}"

            competitors_summary.append(summary)

        prompt = f"""You are a competitive intelligence analyst specializing in advertising strategy.

**Market Overview:**
- Total Competitors: {analysis_data['total_competitors']}
- Total Ads Tracked: {analysis_data['total_ads']}

**Competitor Analysis (with Vision AI):**
{chr(10).join(competitors_summary)}

**Task:**
Generate exactly 3 HIGH-VALUE competitive insights in JSON format. Focus on:

1. **Strategic Differences**: How competitors differ in visual approach, messaging, and ad themes
2. **Market Opportunities**: Gaps or weaknesses you can exploit
3. **Competitive Threats**: Aggressive moves or new campaigns to watch

Each insight must be:
- Specific and data-driven (use percentages, ratios, comparisons)
- Actionable (what should the user do?)
- Based on the vision analysis data

Return ONLY a JSON array:
[
  {{
    "title": "Attention-grabbing headline (max 10 words)",
    "description": "Detailed insight with specific visual/strategic differences (2-3 sentences)",
    "metric": "Key stat (e.g., '70%', '3x', '45 ads')",
    "type": "warning|info|success",
    "insight_type": "visual_strategy|messaging|market_leader|opportunity|threat"
  }}
]

Examples of great insights:
- "Talabat uses food imagery in 80% of ads vs your 40% - stronger appetite appeal"
- "Rafiq just launched 15 'free delivery' promo ads - aggressive price war starting"
- "Only you are using 'friendly' tone - competitors are 70% urgent/promotional"

Return ONLY valid JSON, no markdown or extra text."""

        return prompt

    def _parse_ai_response(self, ai_response: str, analysis_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse AI response and format as insights"""

        try:
            start_idx = ai_response.find('[')
            end_idx = ai_response.rfind(']') + 1

            if start_idx != -1 and end_idx > start_idx:
                json_str = ai_response[start_idx:end_idx]
                ai_insights = json.loads(json_str)

                formatted_insights = []
                for insight in ai_insights[:3]:
                    # Determine link based on insight type
                    insight_type = insight.get('insight_type', 'info')
                    link = "/compare"
                    cta = "View Analysis"

                    if 'market_leader' in insight_type or 'threat' in insight_type:
                        top = analysis_data['competitors'][0]
                        link = f"/competitor/{top['advertiser_id']}"
                        cta = f"View {top['name']}'s Ads"
                    elif 'opportunity' in insight_type:
                        link = "/scrape"
                        cta = "Analyze Your Ads"
                    elif 'visual_strategy' in insight_type or 'messaging' in insight_type:
                        link = "/compare"
                        cta = "Compare Strategies"

                    formatted_insights.append({
                        "title": insight.get('title', ''),
                        "description": insight.get('description', ''),
                        "metric": insight.get('metric', ''),
                        "type": insight.get('type', 'info'),
                        "cta": cta,
                        "link": link
                    })

                return formatted_insights

        except Exception as e:
            print(f"Error parsing AI response: {e}")
            return self._fallback_insights(analysis_data)

        return self._fallback_insights(analysis_data)

    def _fallback_insights(self, analysis_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate vision-based insights when AI fails"""

        insights = []
        competitors = analysis_data['competitors']

        if not competitors:
            return insights

        # Insight 1: Visual strategy comparison
        top = competitors[0]
        visual = top.get('visual_strategy', {})

        if visual:
            category = visual.get('top_category', 'unknown')
            text_heavy = visual.get('text_heavy', 0)

            insights.append({
                "title": f"{top['name']} focuses {text_heavy:.0f}% on text-heavy ads",
                "description": f"{top['name']}'s ads are primarily '{category}' themed with heavy text overlay. This suggests a promotional/offer-driven strategy vs brand building.",
                "metric": f"{text_heavy:.0f}%",
                "type": "warning",
                "cta": f"View {top['name']}'s Ads",
                "link": f"/competitor/{top['advertiser_id']}"
            })

        # Insight 2: Market activity
        total_ads = analysis_data['total_ads']
        insights.append({
            "title": f"Tracking {total_ads} ads across {len(competitors)} competitors",
            "description": f"Comprehensive visual analysis reveals diverse strategies. Use vision insights to identify gaps in your creative approach.",
            "metric": f"{total_ads}",
            "type": "info",
            "cta": "Compare All Strategies",
            "link": "/compare"
        })

        # Insight 3: Creative diversity
        if len(competitors) > 1:
            categories = [c.get('visual_strategy', {}).get('top_category') for c in competitors]
            category_diversity = len(set(categories))

            insights.append({
                "title": f"{category_diversity} distinct creative strategies in market",
                "description": f"Competitors are using varied approaches: {', '.join(set(categories))}. Consider testing underutilized categories.",
                "metric": f"{category_diversity}",
                "type": "success",
                "cta": "Explore Opportunities",
                "link": "/scrape"
            })

        return insights[:3]


# Singleton instance
_insights_engine = None

def get_insights_engine() -> InsightsEngine:
    """Get or create the global insights engine"""
    global _insights_engine
    if _insights_engine is None:
        _insights_engine = InsightsEngine()
    return _insights_engine
