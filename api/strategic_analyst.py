#!/usr/bin/env python3
"""
Strategic Analyst - Personalized AI insights comparing YOUR company vs competitors
Uses DeepSeek/Llama to generate actionable intelligence based on real data
"""
import json
import requests
from typing import List, Dict, Any
from datetime import datetime, timedelta


class StrategicAnalyst:
    """AI-powered strategic analyst that compares YOUR company vs competitors"""

    YOUR_COMPANY_ID = "AR12079153035289296897"  # Snoonu
    YOUR_COMPANY_NAME = "Snoonu"

    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_url
        # Use DeepSeek or Llama - DeepSeek is better for analysis
        self.model = "deepseek-r1:latest"  # or "llama3.1:8b"

    def generate_quick_actions(
        self,
        db,
        module: str = "products"
    ) -> List[Dict[str, Any]]:
        """
        Generate 3 personalized quick actions for a specific module

        Args:
            db: Database instance
            module: products|messaging|velocity|audiences|platforms|promos|brands|food_categories

        Returns:
            List of 3 actionable insights comparing YOU vs competitors
        """
        print(f"🧠 AI Analyst: Generating strategic insights for {module}...")

        # Gather competitive intelligence from DB
        intel = self._gather_competitive_intel(db, module)

        # Generate AI insights using DeepSeek/Llama
        actions = self._generate_ai_actions(intel, module)

        return actions[:3]

    def _gather_competitive_intel(self, db, module: str) -> Dict[str, Any]:
        """Gather real data from database comparing YOU vs competitors"""

        # Get all competitors
        all_ads = db.get_all_ads()

        # Separate YOUR ads vs competitor ads
        your_ads = [ad for ad in all_ads if ad.get('advertiser_id') == self.YOUR_COMPANY_ID]
        competitor_ads = [ad for ad in all_ads if ad.get('advertiser_id') != self.YOUR_COMPANY_ID]

        # Group competitor ads by advertiser
        competitor_groups = {}
        for ad in competitor_ads:
            adv_id = ad.get('advertiser_id')
            if adv_id not in competitor_groups:
                competitor_groups[adv_id] = []
            competitor_groups[adv_id].append(ad)

        intel = {
            "your_company": {
                "name": self.YOUR_COMPANY_NAME,
                "total_ads": len(your_ads),
                "active_ads": len([ad for ad in your_ads if ad.get('is_active')]),
            },
            "competitors": [],
            "market_total": len(all_ads),
            "module": module
        }

        # Module-specific analysis
        if module == "products":
            intel["your_company"]["products"] = self._analyze_products(your_ads)
            for adv_id, ads in competitor_groups.items():
                intel["competitors"].append({
                    "advertiser_id": adv_id,
                    "name": self._get_competitor_name(adv_id),
                    "total_ads": len(ads),
                    "products": self._analyze_products(ads)
                })

        elif module == "promos":
            intel["your_company"]["promos"] = self._analyze_promos(your_ads)
            for adv_id, ads in competitor_groups.items():
                intel["competitors"].append({
                    "advertiser_id": adv_id,
                    "name": self._get_competitor_name(adv_id),
                    "total_ads": len(ads),
                    "promos": self._analyze_promos(ads)
                })

        elif module == "messaging":
            intel["your_company"]["messaging"] = self._analyze_messaging(your_ads)
            for adv_id, ads in competitor_groups.items():
                intel["competitors"].append({
                    "advertiser_id": adv_id,
                    "name": self._get_competitor_name(adv_id),
                    "total_ads": len(ads),
                    "messaging": self._analyze_messaging(ads)
                })

        elif module == "velocity":
            intel["your_company"]["velocity"] = self._analyze_velocity(your_ads)
            for adv_id, ads in competitor_groups.items():
                intel["competitors"].append({
                    "advertiser_id": adv_id,
                    "name": self._get_competitor_name(adv_id),
                    "total_ads": len(ads),
                    "velocity": self._analyze_velocity(ads)
                })

        elif module == "brands":
            intel["your_company"]["brands"] = self._analyze_brands(your_ads)
            for adv_id, ads in competitor_groups.items():
                intel["competitors"].append({
                    "advertiser_id": adv_id,
                    "name": self._get_competitor_name(adv_id),
                    "total_ads": len(ads),
                    "brands": self._analyze_brands(ads)
                })

        elif module == "food_categories":
            intel["your_company"]["food_categories"] = self._analyze_food_categories(your_ads)
            for adv_id, ads in competitor_groups.items():
                intel["competitors"].append({
                    "advertiser_id": adv_id,
                    "name": self._get_competitor_name(adv_id),
                    "total_ads": len(ads),
                    "food_categories": self._analyze_food_categories(ads)
                })

        return intel

    def _analyze_products(self, ads: List[Dict]) -> Dict[str, Any]:
        """Analyze product categories"""
        categories = {}
        for ad in ads:
            cat = ad.get('product_category')
            if cat:
                for c in cat.split(', '):
                    categories[c] = categories.get(c, 0) + 1

        total = len(ads)
        top_cat = max(categories.items(), key=lambda x: x[1]) if categories else (None, 0)

        return {
            "total_products": len(categories),
            "top_category": top_cat[0],
            "top_category_count": top_cat[1],
            "top_category_pct": round(top_cat[1] / total * 100, 1) if total > 0 else 0,
            "categories": categories
        }

    def _analyze_promos(self, ads: List[Dict]) -> Dict[str, Any]:
        """Analyze promotional offers"""
        promos = {}
        for ad in ads:
            offer = ad.get('offer_type')
            if offer and offer.lower() != 'none':
                promos[offer] = promos.get(offer, 0) + 1

        total = len(ads)
        promo_ads = sum(promos.values())

        return {
            "promo_ad_count": promo_ads,
            "promo_percentage": round(promo_ads / total * 100, 1) if total > 0 else 0,
            "promo_types": promos
        }

    def _analyze_messaging(self, ads: List[Dict]) -> Dict[str, Any]:
        """Analyze messaging themes"""
        themes = {}
        for ad in ads:
            theme = ad.get('primary_theme')
            if theme:
                themes[theme] = themes.get(theme, 0) + 1

        total = len(ads)
        top_theme = max(themes.items(), key=lambda x: x[1]) if themes else (None, 0)

        return {
            "top_theme": top_theme[0],
            "top_theme_count": top_theme[1],
            "top_theme_pct": round(top_theme[1] / total * 100, 1) if total > 0 else 0,
            "themes": themes
        }

    def _analyze_velocity(self, ads: List[Dict]) -> Dict[str, Any]:
        """Analyze ad launch velocity"""
        # Get ads from last 30 days
        now = datetime.now().timestamp()
        thirty_days_ago = (datetime.now() - timedelta(days=30)).timestamp()

        recent_ads = []
        for ad in ads:
            first_seen = ad.get('first_seen_date')
            if first_seen:
                try:
                    ts = datetime.fromisoformat(first_seen).timestamp()
                    if ts >= thirty_days_ago:
                        recent_ads.append(ad)
                except:
                    pass

        return {
            "ads_last_30_days": len(recent_ads),
            "ads_per_day": round(len(recent_ads) / 30, 1)
        }

    def _analyze_brands(self, ads: List[Dict]) -> Dict[str, Any]:
        """Analyze brand mentions from vision extraction"""
        brands = {}
        ads_with_brands = 0

        for ad in ads:
            brand = ad.get('brand')
            if brand and brand.strip():
                brands[brand] = brands.get(brand, 0) + 1
                ads_with_brands += 1

        total = len(ads)
        top_brand = max(brands.items(), key=lambda x: x[1]) if brands else (None, 0)

        return {
            "total_brands_mentioned": len(brands),
            "ads_with_brands": ads_with_brands,
            "brand_coverage": round(ads_with_brands / total * 100, 1) if total > 0 else 0,
            "top_brand": top_brand[0],
            "top_brand_count": top_brand[1],
            "top_brand_pct": round(top_brand[1] / total * 100, 1) if total > 0 else 0,
            "brands": brands
        }

    def _analyze_food_categories(self, ads: List[Dict]) -> Dict[str, Any]:
        """Analyze food categories from vision extraction"""
        categories = {}
        ads_with_categories = 0

        for ad in ads:
            category = ad.get('food_category')
            if category and category.strip():
                categories[category] = categories.get(category, 0) + 1
                ads_with_categories += 1

        total = len(ads)
        top_category = max(categories.items(), key=lambda x: x[1]) if categories else (None, 0)

        return {
            "total_food_categories": len(categories),
            "ads_with_food_category": ads_with_categories,
            "food_coverage": round(ads_with_categories / total * 100, 1) if total > 0 else 0,
            "top_food_category": top_category[0],
            "top_category_count": top_category[1],
            "top_category_pct": round(top_category[1] / total * 100, 1) if total > 0 else 0,
            "categories": categories
        }

    def _get_competitor_name(self, advertiser_id: str) -> str:
        """Map advertiser ID to name"""
        mapping = {
            "AR14306592000630063105": "Talabat",
            "AR08778154730519003137": "Rafiq",
            "AR13676304484790173697": "Keeta",
        }
        return mapping.get(advertiser_id, f"Competitor {advertiser_id[:8]}")

    def _generate_ai_actions(self, intel: Dict[str, Any], module: str) -> List[Dict[str, Any]]:
        """Call DeepSeek/Llama to generate personalized strategic actions"""

        prompt = self._create_strategic_prompt(intel, module)

        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "num_predict": 800
                    }
                },
                timeout=90
            )

            if response.status_code == 200:
                ai_response = response.json()['response']
                return self._parse_ai_actions(ai_response)
            else:
                print(f"❌ AI API error: {response.status_code}")
                return self._fallback_actions(intel, module)

        except Exception as e:
            print(f"❌ Error calling AI: {e}")
            return self._fallback_actions(intel, module)

    def _create_strategic_prompt(self, intel: Dict[str, Any], module: str) -> str:
        """Create strategic analysis prompt for AI"""

        your_data = intel["your_company"]
        competitors = intel["competitors"]

        # Build competitive landscape
        comp_summary = []
        for comp in competitors:
            name = comp["name"]
            count = comp["total_ads"]

            if module == "products" and "products" in comp:
                top = comp["products"]["top_category"]
                pct = comp["products"]["top_category_pct"]
                comp_summary.append(f"  • {name}: {count} ads, {pct}% focus on {top}")

            elif module == "promos" and "promos" in comp:
                promo_pct = comp["promos"]["promo_percentage"]
                comp_summary.append(f"  • {name}: {count} ads, {promo_pct}% are promotional")

            elif module == "messaging" and "messaging" in comp:
                theme = comp["messaging"]["top_theme"]
                pct = comp["messaging"]["top_theme_pct"]
                comp_summary.append(f"  • {name}: {count} ads, {pct}% use '{theme}' messaging")

            elif module == "velocity" and "velocity" in comp:
                velocity = comp["velocity"]["ads_per_day"]
                comp_summary.append(f"  • {name}: {count} total ads, {velocity} ads/day (last 30d)")

            elif module == "brands" and "brands" in comp:
                brands = comp["brands"]
                top_brand = brands.get("top_brand", "N/A")
                coverage = brands.get("brand_coverage", 0)
                comp_summary.append(f"  • {name}: {count} ads, {coverage}% show brand mentions, top: '{top_brand}'")

            elif module == "food_categories" and "food_categories" in comp:
                food = comp["food_categories"]
                top_cat = food.get("top_food_category", "N/A")
                coverage = food.get("food_coverage", 0)
                comp_summary.append(f"  • {name}: {count} ads, {coverage}% food category ads, focus: '{top_cat}'")

            else:
                comp_summary.append(f"  • {name}: {count} total ads")

        # Your company summary
        your_summary = f"{your_data['name']}: {your_data['total_ads']} total ads"
        if module == "products" and "products" in your_data:
            top = your_data["products"]["top_category"]
            pct = your_data["products"]["top_category_pct"]
            your_summary += f", {pct}% focus on {top}"
        elif module == "promos" and "promos" in your_data:
            promo_pct = your_data["promos"]["promo_percentage"]
            your_summary += f", {promo_pct}% are promotional"
        elif module == "messaging" and "messaging" in your_data:
            theme = your_data["messaging"]["top_theme"]
            pct = your_data["messaging"]["top_theme_pct"]
            your_summary += f", {pct}% use '{theme}' messaging"
        elif module == "velocity" and "velocity" in your_data:
            velocity = your_data["velocity"]["ads_per_day"]
            your_summary += f", {velocity} ads/day (last 30d)"
        elif module == "brands" and "brands" in your_data:
            brands = your_data["brands"]
            coverage = brands.get("brand_coverage", 0)
            top_brand = brands.get("top_brand", "N/A")
            your_summary += f", {coverage}% brand mentions, top: '{top_brand}'"
        elif module == "food_categories" and "food_categories" in your_data:
            food = your_data["food_categories"]
            coverage = food.get("food_coverage", 0)
            top_cat = food.get("top_food_category", "N/A")
            your_summary += f", {coverage}% food ads, focus: '{top_cat}'"

        prompt = f"""You are a strategic advertising analyst working for {your_data['name']} (a food delivery company in Qatar).

**YOUR COMPANY:**
{your_summary}

**YOUR COMPETITORS:**
{chr(10).join(comp_summary)}

**CONTEXT:** You're analyzing the "{module}" module - focus on {module}-specific insights.

**TASK:** Generate exactly 3 PERSONALIZED quick actions that help {your_data['name']} compete better.

Each action must:
1. Compare {your_data['name']} to specific competitors (use numbers, percentages, ratios)
2. Identify a gap, opportunity, or threat
3. Provide a specific, actionable recommendation
4. Be honest - if {your_data['name']} is winning, say so. If losing, be direct about what to fix.

**OUTPUT FORMAT:** Return ONLY a JSON array (no markdown, no extra text):
[
  {{
    "icon": "🎯|📊|💡|🔥|⚡|🏆|⚠️",
    "text": "Specific action based on competitive data (max 12 words)",
    "color": "blue|purple|green|orange|red|yellow"
  }}
]

**EXAMPLES:**
- {{"icon": "⚠️", "text": "Talabat runs 3x more promo ads - increase discount campaigns", "color": "red"}}
- {{"icon": "🏆", "text": "You dominate pizza (60% vs 30% avg) - double down", "color": "green"}}
- {{"icon": "💡", "text": "Zero burger ads while Deliveroo has 40 - untapped opportunity", "color": "blue"}}
- {{"icon": "🎯", "text": "Talabat mentions 15 brands, you mention 3 - expand partnerships", "color": "orange"}}
- {{"icon": "🍕", "text": "You lead in Italian food ads (45% vs 20%) - maintain focus", "color": "green"}}

Return ONLY valid JSON array."""

        return prompt

    def _parse_ai_actions(self, ai_response: str) -> List[Dict[str, Any]]:
        """Parse AI response into action items"""
        try:
            # Extract JSON array
            start = ai_response.find('[')
            end = ai_response.rfind(']') + 1

            if start != -1 and end > start:
                json_str = ai_response[start:end]
                actions = json.loads(json_str)
                return actions[:3]
        except Exception as e:
            print(f"❌ Error parsing AI response: {e}")

        return []

    def _fallback_actions(self, intel: Dict[str, Any], module: str) -> List[Dict[str, Any]]:
        """Fallback actions when AI fails"""

        your_data = intel["your_company"]
        competitors = intel["competitors"]

        if not competitors:
            return [
                {"icon": "📊", "text": "Scrape competitor data to enable insights", "color": "blue"},
                {"icon": "🎯", "text": "Add more competitors to compare performance", "color": "purple"},
                {"icon": "⚡", "text": "Enable AI enrichment for deeper analysis", "color": "green"}
            ]

        actions = []

        # Compare ad volume
        top_comp = max(competitors, key=lambda x: x["total_ads"])
        if top_comp["total_ads"] > your_data["total_ads"]:
            ratio = round(top_comp["total_ads"] / max(your_data["total_ads"], 1), 1)
            actions.append({
                "icon": "⚠️",
                "text": f"{top_comp['name']} has {ratio}x more ads - increase volume",
                "color": "red"
            })
        else:
            actions.append({
                "icon": "🏆",
                "text": f"You lead market with {your_data['total_ads']} ads - maintain pace",
                "color": "green"
            })

        # Module-specific insights
        if module == "products" and "products" in your_data:
            your_cat = your_data["products"]["top_category"]
            actions.append({
                "icon": "🎯",
                "text": f"You focus on {your_cat} - analyze competitor categories",
                "color": "blue"
            })
        elif module == "brands" and "brands" in your_data:
            your_brands = your_data["brands"]["total_brands_mentioned"]
            actions.append({
                "icon": "🏪",
                "text": f"You mention {your_brands} brands - track restaurant partnerships",
                "color": "blue"
            })
        elif module == "food_categories" and "food_categories" in your_data:
            your_coverage = your_data["food_categories"]["food_coverage"]
            actions.append({
                "icon": "🍽️",
                "text": f"{your_coverage}% ads show food categories - increase coverage",
                "color": "blue"
            })

        actions.append({
            "icon": "💡",
            "text": f"Compare {module} strategies across all {len(competitors)} competitors",
            "color": "purple"
        })

        return actions[:3]


# Singleton
_strategic_analyst = None

def get_strategic_analyst() -> StrategicAnalyst:
    """Get or create the global strategic analyst"""
    global _strategic_analyst
    if _strategic_analyst is None:
        _strategic_analyst = StrategicAnalyst()
    return _strategic_analyst
