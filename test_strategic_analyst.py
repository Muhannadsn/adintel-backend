#!/usr/bin/env python3
"""
Test the enhanced Strategic Analyst with vision-enriched data
"""
import sys
sys.path.insert(0, '/Users/muhannadsaad/Desktop/ad-intelligence')

from api.database import AdDatabase
from api.strategic_analyst import StrategicAnalyst

def test_module(analyst, db, module_name):
    """Test a specific module"""
    print(f"\n{'='*80}")
    print(f"MODULE: {module_name.upper()}")
    print(f"{'='*80}\n")

    try:
        actions = analyst.generate_quick_actions(db, module=module_name)

        if not actions:
            print(f"❌ No actions generated for {module_name}")
            return

        print(f"✅ Generated {len(actions)} strategic actions:\n")
        for i, action in enumerate(actions, 1):
            icon = action.get('icon', '📊')
            text = action.get('text', 'No text')
            color = action.get('color', 'blue')
            print(f"  {i}. {icon} [{color.upper()}] {text}")

    except Exception as e:
        print(f"❌ Error testing {module_name}: {e}")
        import traceback
        traceback.print_exc()

def main():
    print("\n🧠 STRATEGIC ANALYST - ENHANCED WITH VISION DATA")
    print("="*80)

    # Initialize
    db = AdDatabase()
    analyst = StrategicAnalyst()

    # Get stats
    all_ads = db.get_all_ads()
    vision_ads = [ad for ad in all_ads if ad.get('brand') or ad.get('food_category')]

    print(f"\n📊 Database Stats:")
    print(f"   Total ads: {len(all_ads)}")
    print(f"   Vision-enriched ads: {len(vision_ads)}")
    print(f"   Coverage: {len(vision_ads)/len(all_ads)*100:.1f}%")

    # Test all modules
    modules = [
        "products",
        "brands",
        "food_categories",
        "messaging",
        "promos",
        "velocity"
    ]

    for module in modules:
        test_module(analyst, db, module)

    print(f"\n{'='*80}")
    print("✅ STRATEGIC ANALYST TESTING COMPLETE")
    print(f"{'='*80}\n")

if __name__ == '__main__':
    main()
