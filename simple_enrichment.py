#!/usr/bin/env python3
"""
Simple Enrichment Pipeline - OCR -> LLM -> Database
No complex agents, just clean extraction using LLM.
"""

import os
import glob
import pandas as pd
from pathlib import Path
from agents.simple_llm_extractor import SimpleLLMExtractor
from api.database import AdDatabase


def process_csvs_simple():
    """
    Process all manual CSVs with the simple LLM approach
    """

    print("=" * 70)
    print("SIMPLE ENRICHMENT PIPELINE")
    print("OCR -> Llama -> Database")
    print("=" * 70)

    # Initialize
    extractor = SimpleLLMExtractor()
    db = AdDatabase()

    # Find all CSV files
    csv_files = glob.glob("data/input/*.csv", recursive=False)

    if not csv_files:
        print("❌ No CSV files found in data/input/")
        return

    print(f"\n📂 Found {len(csv_files)} CSV files")

    total_processed = 0
    total_enriched = 0

    for csv_path in csv_files:
        print(f"\n{'='*70}")
        print(f"📄 Processing: {Path(csv_path).name}")
        print(f"{'='*70}")

        # Read CSV
        df = pd.read_csv(csv_path)

        # Get advertiser_id from filename (e.g., AR123456789.csv)
        filename = Path(csv_path).stem
        advertiser_id = filename

        print(f"   Advertiser: {advertiser_id}")
        print(f"   Rows: {len(df)}")

        enriched_ads = []

        for idx, row in df.iterrows():
            ad_text = str(row.get('ad_text', ''))
            image_url = str(row.get('image_url', ''))

            if not ad_text or ad_text == 'nan':
                print(f"   ⏭️  Skipping row {idx}: no ad_text")
                continue

            total_processed += 1

            print(f"\n   📝 Ad {idx + 1}/{len(df)}")
            print(f"      Text: {ad_text[:100]}...")

            # Extract with simple LLM
            result = extractor.extract(ad_text)

            print(f"      ✅ Brand: {result.brand_name}")
            print(f"      ✅ Category: {result.product_category}")
            print(f"      ✅ Offer: {result.offer_type} - {result.offer_details}")
            print(f"      ✅ Confidence: {result.confidence:.2f}")

            # Prepare ad data for database
            ad_data = {
                'advertiser_id': advertiser_id,
                'ad_text': ad_text,
                'image_url': image_url,
                'html_content': row.get('html_content', ''),
                'regions': row.get('regions', ''),
                # Enrichment data
                'brand': result.brand_name,
                'product_category': result.product_category,
                'product_name': result.brand_name,  # Use brand as product name
                'offer_type': result.offer_type,
                'offer_details': result.offer_details,
                'confidence_score': result.confidence,
                'analysis_model': 'simple_llm_llama3.1',
                'primary_theme': result.offer_type if result.offer_type != 'none' else 'brand_awareness',
                'messaging_themes': {result.offer_type: 1.0} if result.offer_type != 'none' else {'brand_awareness': 1.0},
            }

            enriched_ads.append(ad_data)
            total_enriched += 1

        # Save to database
        if enriched_ads:
            print(f"\n   💾 Saving {len(enriched_ads)} ads to database...")
            stats = db.save_ads(enriched_ads, advertiser_id)
            print(f"   ✅ Saved: {stats['ads_new']} new, {stats['ads_updated']} updated")

    print(f"\n{'='*70}")
    print(f"✅ ENRICHMENT COMPLETE")
    print(f"{'='*70}")
    print(f"   Total processed: {total_processed}")
    print(f"   Total enriched: {total_enriched}")
    print(f"\n🚀 Frontend should now show enriched data!")


if __name__ == "__main__":
    process_csvs_simple()
