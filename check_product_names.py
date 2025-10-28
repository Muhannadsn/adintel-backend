#!/usr/bin/env python3
"""
Quick script to check if product names are correctly associated with advertisers
"""
import sqlite3

db_path = "data/adintel.db"

with sqlite3.connect(db_path) as conn:
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get a sample of ads with product names
    query = '''
        SELECT
            a.advertiser_id,
            e.product_name,
            COUNT(*) as count
        FROM ads a
        LEFT JOIN ad_enrichment e ON a.id = e.ad_id
        WHERE e.product_name IS NOT NULL
        GROUP BY a.advertiser_id, e.product_name
        ORDER BY a.advertiser_id, count DESC
        LIMIT 40
    '''

    cursor.execute(query)
    rows = cursor.fetchall()

    print(f"\n{'Advertiser ID':<30} {'Product Name':<60} {'Count'}")
    print("=" * 100)

    for row in rows:
        print(f"{row['advertiser_id']:<30} {row['product_name']:<60} {row['count']}")

    print(f"\n\nTotal unique combinations: {len(rows)}")

    # Check for potential issues
    print("\n\n=== Checking for cross-contamination ===")
    talabat_ids = ['AR14306592000630063105']
    keeta_ids = ['AR02245493152427278337']

    # Check if Keeta ads have Talabat product names
    query2 = '''
        SELECT
            a.id,
            a.advertiser_id,
            e.product_name
        FROM ads a
        LEFT JOIN ad_enrichment e ON a.id = e.ad_id
        WHERE a.advertiser_id = ?
            AND e.product_name LIKE '%Talabat%'
        LIMIT 10
    '''

    cursor.execute(query2, (keeta_ids[0],))
    keeta_with_talabat = cursor.fetchall()

    if keeta_with_talabat:
        print(f"\n❌ Found {len(keeta_with_talabat)} Keeta ads with 'Talabat' in product_name:")
        for row in keeta_with_talabat:
            print(f"   Ad ID {row['id']}: {row['product_name']}")
    else:
        print("\n✅ No Keeta ads have 'Talabat' in product_name")

    # Check the opposite
    cursor.execute(query2.replace('Talabat', 'Keeta'), (talabat_ids[0],))
    talabat_with_keeta = cursor.fetchall()

    if talabat_with_keeta:
        print(f"\n❌ Found {len(talabat_with_keeta)} Talabat ads with 'Keeta' in product_name:")
        for row in talabat_with_keeta:
            print(f"   Ad ID {row['id']}: {row['product_name']}")
    else:
        print("\n✅ No Talabat ads have 'Keeta' in product_name")
