#!/usr/bin/env python3
"""
Fix cross-contamination where Vision AI labeled competitor ads with wrong brand names
Specifically: Remove "Talabat Pro" from non-Talabat advertisers (Keeta, Rafiq, Snoonu, Deliveroo)
"""
import sqlite3

db_path = "data/adintel.db"

# Advertiser mappings
TALABAT_ID = 'AR14306592000630063105'
KEETA_ID = 'AR02245493152427278337'
RAFIQ_ID = 'AR08778154730519003137'
SNOONU_ID = 'AR12079153035289296897'

with sqlite3.connect(db_path) as conn:
    cursor = conn.cursor()

    # Find all ads from non-Talabat advertisers that have "Talabat" in product_name
    query = '''
        SELECT
            a.id,
            a.advertiser_id,
            e.product_name
        FROM ads a
        LEFT JOIN ad_enrichment e ON a.id = e.ad_id
        WHERE a.advertiser_id != ?
            AND (e.product_name LIKE '%Talabat%')
    '''

    cursor.execute(query, (TALABAT_ID,))
    contaminated_ads = cursor.fetchall()

    print(f"Found {len(contaminated_ads)} ads from non-Talabat advertisers with 'Talabat' in product_name\n")

    if len(contaminated_ads) == 0:
        print("✅ No cross-contamination found!")
        exit(0)

    # Show examples
    print("Examples of contaminated entries:")
    for ad in contaminated_ads[:5]:
        print(f"  Ad ID {ad[0]} ({ad[1]}): {ad[2]}")

    print(f"\n🔧 Fixing by setting product_name to NULL for these {len(contaminated_ads)} ads...")

    # Update to set product_name to NULL for contaminated ads
    update_query = '''
        UPDATE ad_enrichment
        SET product_name = NULL
        WHERE ad_id IN (
            SELECT a.id
            FROM ads a
            LEFT JOIN ad_enrichment e ON a.id = e.ad_id
            WHERE a.advertiser_id != ?
                AND (e.product_name LIKE '%Talabat%')
        )
    '''

    cursor.execute(update_query, (TALABAT_ID,))
    conn.commit()

    print(f"✅ Fixed {cursor.rowcount} enrichment records")

    # Verify
    cursor.execute(query, (TALABAT_ID,))
    remaining = cursor.fetchall()

    if len(remaining) == 0:
        print("✅ Verification passed - no more cross-contamination!")
    else:
        print(f"⚠️  Warning: Still found {len(remaining)} contaminated ads")
