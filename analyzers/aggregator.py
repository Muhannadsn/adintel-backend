import sys
import os
from collections import Counter, defaultdict
from typing import List, Dict
import json

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from models.ad_creative import Analysis, Creative

class CampaignAggregator:
    """
    Aggregates analysis results to generate campaign-level insights.
    Produces reports like: "Talabat today is pushing X ads, 40% free delivery, 25% BOGO"
    """

    def __init__(self):
        self.analyses: List[Analysis] = []
        self.creatives: List[Creative] = []

    def add_analysis(self, analysis: Analysis, creative: Creative = None):
        """Add an analysis result to the aggregator"""
        self.analyses.append(analysis)
        if creative:
            self.creatives.append(creative)

    def generate_insights(self) -> Dict:
        """
        Generate comprehensive insights from all analyzed ads.
        Returns a dictionary with campaign-level statistics.
        """
        if not self.analyses:
            return {"error": "No analyses to aggregate"}

        total_ads = len(self.analyses)

        # Count offer types
        offer_counts = Counter(a.offer_type for a in self.analyses if a.offer_type != 'N/A')
        offer_percentages = {
            offer: (count / total_ads) * 100
            for offer, count in offer_counts.items()
        }

        # Count product categories
        category_counts = Counter(a.product_category for a in self.analyses if a.product_category != 'N/A')
        category_percentages = {
            cat: (count / total_ads) * 100
            for cat, count in category_counts.items()
        }

        # Aggregate all keywords (normalize and clean)
        all_keywords = []
        for a in self.analyses:
            if a.keywords:
                # Clean and normalize keywords
                cleaned = [kw.lower().strip() for kw in a.keywords if kw and len(kw) > 2]
                all_keywords.extend(cleaned)
        keyword_frequency = Counter(all_keywords)

        # Aggregate all products mentioned
        all_products = []
        for a in self.analyses:
            if a.products_mentioned:
                all_products.extend(a.products_mentioned)
        product_frequency = Counter(all_products)

        # Count discount types
        discount_counts = Counter(
            a.discount_percentage for a in self.analyses
            if a.discount_percentage and a.discount_percentage != 'N/A'
        )

        # Get advertiser breakdown
        advertiser_counts = Counter(c.advertiser for c in self.creatives) if self.creatives else {}

        # Count by format (Text, Image, Video)
        format_counts = Counter(c.format for c in self.creatives) if self.creatives else {}

        insights = {
            "summary": {
                "total_ads": total_ads,
                "total_unique_keywords": len(keyword_frequency),
                "total_unique_products": len(product_frequency),
            },
            "offer_distribution": {
                "counts": dict(offer_counts),
                "percentages": {k: round(v, 1) for k, v in offer_percentages.items()}
            },
            "category_distribution": {
                "counts": dict(category_counts),
                "percentages": {k: round(v, 1) for k, v in category_percentages.items()}
            },
            "top_keywords": dict(keyword_frequency.most_common(20)),
            "top_products": dict(product_frequency.most_common(20)),
            "discount_types": dict(discount_counts),
            "advertiser_breakdown": dict(advertiser_counts),
            "format_breakdown": dict(format_counts)
        }

        return insights

    def generate_text_report(self, advertiser_name: str = None) -> str:
        """
        Generate a human-readable text report.
        Example: "Talabat today is pushing 50 ads, 40% free delivery, 25% BOGO"
        """
        insights = self.generate_insights()

        if "error" in insights:
            return insights["error"]

        # Determine advertiser name
        if not advertiser_name and insights["advertiser_breakdown"]:
            advertiser_name = list(insights["advertiser_breakdown"].keys())[0]

        total = insights["summary"]["total_ads"]

        report_lines = []
        report_lines.append(f"\n{'='*80}")
        report_lines.append(f"CAMPAIGN INTELLIGENCE REPORT")
        if advertiser_name:
            report_lines.append(f"Advertiser: {advertiser_name}")
        report_lines.append(f"{'='*80}\n")

        # Summary
        report_lines.append(f"📊 OVERVIEW")
        report_lines.append(f"Total ads analyzed: {total}")

        if insights["format_breakdown"]:
            format_str = ", ".join([f"{count} {fmt}" for fmt, count in insights["format_breakdown"].items()])
            report_lines.append(f"Formats: {format_str}")

        # Offer distribution
        report_lines.append(f"\n🎁 OFFER DISTRIBUTION")
        if insights["offer_distribution"]["percentages"]:
            for offer, pct in sorted(insights["offer_distribution"]["percentages"].items(),
                                    key=lambda x: x[1], reverse=True):
                count = insights["offer_distribution"]["counts"][offer]
                report_lines.append(f"  • {pct}% ({count} ads) - {offer}")
        else:
            report_lines.append("  No offer data available")

        # Category distribution
        report_lines.append(f"\n📦 CATEGORY DISTRIBUTION")
        if insights["category_distribution"]["percentages"]:
            for cat, pct in sorted(insights["category_distribution"]["percentages"].items(),
                                  key=lambda x: x[1], reverse=True):
                count = insights["category_distribution"]["counts"][cat]
                report_lines.append(f"  • {pct}% ({count} ads) - {cat}")

        # Top keywords
        report_lines.append(f"\n🔑 TOP KEYWORDS (Most Frequent)")
        if insights["top_keywords"]:
            for keyword, count in list(insights["top_keywords"].items())[:10]:
                report_lines.append(f"  • '{keyword}' - mentioned {count} times")
        else:
            report_lines.append("  No keyword data available")

        # Top products
        report_lines.append(f"\n🛍️  TOP PRODUCTS MENTIONED")
        if insights["top_products"]:
            for product, count in list(insights["top_products"].items())[:10]:
                report_lines.append(f"  • '{product}' - mentioned {count} times")
        else:
            report_lines.append("  No product data available")

        # One-liner summary (like you requested)
        report_lines.append(f"\n{'='*80}")
        report_lines.append("📝 ONE-LINE SUMMARY")
        report_lines.append(f"{'='*80}")

        summary_parts = [f"{advertiser_name if advertiser_name else 'Brand'} is pushing {total} ads"]

        if insights["offer_distribution"]["percentages"]:
            top_offers = sorted(insights["offer_distribution"]["percentages"].items(),
                              key=lambda x: x[1], reverse=True)[:3]
            offer_summary = ", ".join([f"{int(pct)}% {offer}" for offer, pct in top_offers])
            summary_parts.append(offer_summary)

        if insights["category_distribution"]["percentages"]:
            top_cat = max(insights["category_distribution"]["percentages"].items(), key=lambda x: x[1])
            summary_parts.append(f"Most highlighted category: {top_cat[0]}")

        if insights["top_products"]:
            top_product = list(insights["top_products"].items())[0]
            summary_parts.append(f"Most mentioned product: {top_product[0]}")

        report_lines.append(". ".join(summary_parts) + ".")
        report_lines.append(f"{'='*80}\n")

        return "\n".join(report_lines)

    def export_to_json(self, output_path: str):
        """Export insights to JSON file"""
        insights = self.generate_insights()
        with open(output_path, 'w') as f:
            json.dump(insights, f, indent=2)
        print(f"Insights exported to: {output_path}")


if __name__ == '__main__':
    # Example usage with mock data
    from models.ad_creative import Analysis, Creative

    # Create some sample analyses
    aggregator = CampaignAggregator()

    sample_analysis_1 = Analysis(
        screenshot_id=1,
        product_category="Food Delivery",
        offer_type="Free Delivery",
        messaging="Order online from top restaurants",
        raw_ai_response="{}",
        extracted_text="Order now, Free delivery on all orders",
        headline="Free Delivery on All Orders",
        call_to_action="Order Now",
        discount_percentage="Free",
        products_mentioned=["Restaurant Food", "Groceries"],
        keywords=["delivery", "fast", "online", "free"],
        brand_name="Talabat",
        price_mentioned=None
    )

    sample_creative_1 = Creative(
        advertiser="DELIVERY HERO TALABAT",
        creative="https://example.com/1",
        format="Text",
        region_filter="QA",
        campaign_duration="1 month",
        first_seen="10/01/2025",
        last_seen="10/15/2025",
        gatc_link="https://example.com/gatc/1"
    )

    aggregator.add_analysis(sample_analysis_1, sample_creative_1)

    # Add a few more for demonstration
    for i in range(5):
        aggregator.add_analysis(sample_analysis_1, sample_creative_1)

    print(aggregator.generate_text_report())
