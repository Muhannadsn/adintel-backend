#!/usr/bin/env python3
"""
Migrate data from SQLite to Postgres
Run this once after setting up Postgres on Railway
"""

import sqlite3
import psycopg2
import os
from pathlib import Path

# Your Railway Postgres URL
DATABASE_URL = "postgresql://postgres:TpDpnjWIwiYilnhXFaRIviqLSaycqafp@mainline.proxy.rlwy.net:39036/railway"

# Local SQLite database
SQLITE_DB = Path(__file__).parent / "data" / "adintel.db"

def migrate():
    """Migrate all data from SQLite to Postgres"""

    print("🔄 Starting migration from SQLite to Postgres...")

    # Connect to both databases
    sqlite_conn = sqlite3.connect(SQLITE_DB)
    sqlite_conn.row_factory = sqlite3.Row
    pg_conn = psycopg2.connect(DATABASE_URL)

    try:
        # Initialize Postgres schema first
        print("📋 Creating Postgres tables...")
        os.environ['DATABASE_URL'] = DATABASE_URL
        from api.database import AdDatabase
        db = AdDatabase()  # This will create the schema

        sqlite_cursor = sqlite_conn.cursor()
        pg_cursor = pg_conn.cursor()

        # Migrate ads table
        print("📦 Migrating ads...")
        sqlite_cursor.execute("SELECT * FROM ads")
        ads = sqlite_cursor.fetchall()

        for ad in ads:
            # Convert SQLite boolean (0/1) to Postgres boolean (True/False)
            ad_tuple = tuple(ad)
            ad_list = list(ad_tuple)
            ad_list[8] = bool(ad_list[8])  # is_active
            pg_cursor.execute('''
                INSERT INTO ads (id, advertiser_id, ad_text, image_url, html_content, regions,
                                first_seen_date, last_seen_date, is_active, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
            ''', tuple(ad_list))

        print(f"   ✅ Migrated {len(ads)} ads")

        # Migrate ad_enrichment table
        print("🎨 Migrating ad enrichment data...")
        sqlite_cursor.execute("SELECT * FROM ad_enrichment")
        enrichments = sqlite_cursor.fetchall()

        for enrich in enrichments:
            # Convert boolean fields
            enrich_list = list(enrich)
            if len(enrich_list) > 11 and enrich_list[11] is not None:
                enrich_list[11] = bool(enrich_list[11])  # is_qatar_only
            if len(enrich_list) > 14 and enrich_list[14] is not None:
                enrich_list[14] = bool(enrich_list[14])  # rejected_wrong_region

            pg_cursor.execute('''
                INSERT INTO ad_enrichment
                (ad_id, product_category, product_name, messaging_themes, primary_theme,
                 audience_segment, offer_type, offer_details, confidence_score, analysis_model,
                 analyzed_at, is_qatar_only, brand, food_category, rejected_wrong_region, detected_region,
                 embedding_vector)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (ad_id) DO NOTHING
            ''', tuple(enrich_list))

        print(f"   ✅ Migrated {len(enrichments)} enrichment records")

        # Migrate scrape_runs table
        print("📊 Migrating scrape runs...")
        sqlite_cursor.execute("SELECT * FROM scrape_runs")
        runs = sqlite_cursor.fetchall()

        for run in runs:
            # Convert boolean
            run_list = list(run)
            if len(run_list) > 6 and run_list[6] is not None:
                run_list[6] = bool(run_list[6])  # enrichment_enabled

            pg_cursor.execute('''
                INSERT INTO scrape_runs (id, advertiser_id, run_date, ads_found, ads_new, ads_retired, enrichment_enabled)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
            ''', tuple(run_list))

        print(f"   ✅ Migrated {len(runs)} scrape runs")

        # Migrate product_knowledge table
        print("📚 Migrating product knowledge...")
        sqlite_cursor.execute("SELECT * FROM product_knowledge")
        products = sqlite_cursor.fetchall()

        for product in products:
            # Convert boolean fields
            product_list = list(product)
            if len(product_list) > 4 and product_list[4] is not None:
                product_list[4] = bool(product_list[4])  # is_restaurant
            if len(product_list) > 5 and product_list[5] is not None:
                product_list[5] = bool(product_list[5])  # is_unknown_category
            if len(product_list) > 6 and product_list[6] is not None:
                product_list[6] = bool(product_list[6])  # is_subscription

            pg_cursor.execute('''
                INSERT INTO product_knowledge
                (id, product_name, product_type, category, is_restaurant, is_unknown_category,
                 is_subscription, metadata, confidence, verified_date, search_source, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
            ''', tuple(product_list))

        print(f"   ✅ Migrated {len(products)} product records")

        # Commit all changes
        pg_conn.commit()

        print("\n🎉 Migration completed successfully!")
        print(f"   Total ads: {len(ads)}")
        print(f"   Total enrichments: {len(enrichments)}")
        print(f"   Total scrape runs: {len(runs)}")
        print(f"   Total products: {len(products)}")

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        pg_conn.rollback()
    finally:
        sqlite_conn.close()
        pg_conn.close()

if __name__ == "__main__":
    migrate()
