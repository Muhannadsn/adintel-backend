#!/usr/bin/env python3
"""
Real-time monitor for simple enrichment progress
"""
import time
import sqlite3
from pathlib import Path

def monitor_progress():
    """Monitor enrichment progress in real-time"""

    db_path = Path("data/adintel.db")

    if not db_path.exists():
        print("❌ Database not found yet")
        return

    print("=" * 70)
    print("SIMPLE ENRICHMENT PROGRESS MONITOR")
    print("=" * 70)
    print("\nPress Ctrl+C to stop monitoring\n")

    last_count = 0

    try:
        while True:
            with sqlite3.connect(str(db_path)) as conn:
                cursor = conn.cursor()

                # Total ads
                cursor.execute("SELECT COUNT(*) FROM ads")
                total_ads = cursor.fetchone()[0]

                # Enriched ads
                cursor.execute("SELECT COUNT(*) FROM ad_enrichment")
                enriched_ads = cursor.fetchone()[0]

                # Ads by category
                cursor.execute("""
                    SELECT product_category, COUNT(*)
                    FROM ad_enrichment
                    WHERE product_category IS NOT NULL
                    GROUP BY product_category
                    ORDER BY COUNT(*) DESC
                    LIMIT 10
                """)
                categories = cursor.fetchall()

                # Recent enrichments
                cursor.execute("""
                    SELECT e.brand, e.product_category, e.offer_type
                    FROM ad_enrichment e
                    ORDER BY e.analyzed_at DESC
                    LIMIT 5
                """)
                recent = cursor.fetchall()

                # New ads since last check
                new_ads = enriched_ads - last_count
                last_count = enriched_ads

                # Clear screen and display
                print("\033[H\033[J")  # Clear terminal
                print("=" * 70)
                print("SIMPLE ENRICHMENT PROGRESS")
                print("=" * 70)

                percentage = (enriched_ads / total_ads * 100) if total_ads > 0 else 0
                print(f"\n📊 Overall Progress:")
                print(f"   Total Ads: {total_ads}")
                print(f"   Enriched: {enriched_ads} ({percentage:.1f}%)")
                print(f"   Remaining: {total_ads - enriched_ads}")
                if new_ads > 0:
                    print(f"   🆕 New in last 3s: +{new_ads}")

                # Progress bar
                bar_width = 50
                filled = int(bar_width * enriched_ads / total_ads) if total_ads > 0 else 0
                bar = "█" * filled + "░" * (bar_width - filled)
                print(f"\n   [{bar}] {percentage:.1f}%")

                # Categories
                print(f"\n📂 Top Categories:")
                for cat, count in categories[:5]:
                    cat_display = cat if cat else "unknown"
                    print(f"   {cat_display}: {count} ads")

                # Recent enrichments
                print(f"\n🔥 Latest 5 Enrichments:")
                for brand, category, offer in recent:
                    brand_display = brand[:30] if brand else "Unknown"
                    cat_display = category[:20] if category else "unknown"
                    offer_display = offer[:20] if offer else "none"
                    print(f"   • {brand_display} | {cat_display} | {offer_display}")

                print(f"\n{'='*70}")
                print("⏳ Updating every 3 seconds... (Ctrl+C to stop)")

            time.sleep(3)

    except KeyboardInterrupt:
        print("\n\n✅ Monitoring stopped")
        print(f"\nFinal Stats:")
        print(f"   Total Ads: {total_ads}")
        print(f"   Enriched: {enriched_ads} ({percentage:.1f}%)")

    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    monitor_progress()
