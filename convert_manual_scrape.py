#!/usr/bin/env python3
"""
Convert manually scraped CSV files to the format expected by re_enrich.py

Input format (from manual scrape):
Advertiser,Creative,Format,Region Filter,Campaign Duration,First Seen,Last Seen,GATC Link

Output format (for enrichment):
advertiser_id,creative_id,advertiser_name,image_url,creative_url,first_shown,last_shown,regions,region_list,html_content,ad_text
"""

import csv
import re
from pathlib import Path
from datetime import datetime

def parse_gatc_link(url):
    """Extract advertiser_id and creative_id from GATC link"""
    # Example: https://adstransparency.google.com/advertiser/AR14306592000630063105/creative/CR14041690220382912513?region=qa
    advertiser_match = re.search(r'/advertiser/([^/]+)', url)
    creative_match = re.search(r'/creative/([^?]+)', url)

    advertiser_id = advertiser_match.group(1) if advertiser_match else None
    creative_id = creative_match.group(1) if creative_match else None

    return advertiser_id, creative_id

def parse_date(date_str):
    """Convert date string to unix timestamp"""
    try:
        # Parse format like "10/8/2025"
        dt = datetime.strptime(date_str, "%m/%d/%Y")
        return int(dt.timestamp())
    except:
        return ""

def convert_manual_csv(input_file, output_file):
    """Convert manual scrape CSV to enrichment format"""

    print(f"\n📄 Converting {input_file.name}...")

    with open(input_file, 'r', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)

        rows_converted = 0
        rows_skipped = 0

        output_rows = []

        for row in reader:
            # Extract IDs from GATC link
            gatc_link = row.get('GATC Link', '')
            advertiser_id, creative_id = parse_gatc_link(gatc_link)

            if not advertiser_id or not creative_id:
                rows_skipped += 1
                continue

            # Get image URL from Creative column
            creative_col = row.get('Creative', '').strip()

            # If Creative contains a URL, use it as image_url
            if creative_col.startswith('http'):
                image_url = creative_col
            else:
                image_url = ""  # No image URL

            # Parse dates
            first_shown = parse_date(row.get('First Seen', ''))
            last_shown = parse_date(row.get('Last Seen', ''))

            # Get region
            region = row.get('Region Filter', 'QA')

            # Create output row
            output_row = {
                'advertiser_id': advertiser_id,
                'creative_id': creative_id,
                'advertiser_name': row.get('Advertiser', 'Unknown'),
                'image_url': image_url,
                'creative_url': gatc_link,
                'first_shown': first_shown,
                'last_shown': last_shown,
                'regions': region,
                'region_list': f'["{region}"]' if region else '[]',
                'html_content': '',
                'ad_text': row.get('Advertiser', 'Unknown'),  # Use advertiser name as ad text
            }

            output_rows.append(output_row)
            rows_converted += 1

        # Write to output file
        if output_rows:
            fieldnames = ['advertiser_id', 'creative_id', 'advertiser_name', 'image_url',
                         'creative_url', 'first_shown', 'last_shown', 'regions',
                         'region_list', 'html_content', 'ad_text']

            with open(output_file, 'w', newline='', encoding='utf-8') as outfile:
                writer = csv.DictWriter(outfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(output_rows)

            print(f"   ✅ Converted {rows_converted} rows")
            if rows_skipped > 0:
                print(f"   ⚠️  Skipped {rows_skipped} rows (missing IDs)")

            # Count how many have images
            with_images = sum(1 for r in output_rows if r['image_url'])
            print(f"   📸 {with_images} ads have image URLs ({with_images/len(output_rows)*100:.1f}%)")

            return True
        else:
            print(f"   ❌ No rows to convert")
            return False

def main():
    input_dir = Path('/Users/muhannadsaad/Desktop/ad-intelligence/data/input')

    # Find all manual CSV files (the ones you just added)
    manual_files = [
        'talabaat.csv',
        'snoonu.csv',
        'keeta.csv',
        'rafeeq.csv'
    ]

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    print("🔄 Converting manually scraped CSV files to enrichment format\n")

    converted_count = 0

    for filename in manual_files:
        input_file = input_dir / filename

        if not input_file.exists():
            print(f"⚠️  {filename} not found, skipping")
            continue

        # Create output filename with timestamp
        base_name = input_file.stem
        output_file = input_dir / f"{base_name}_converted_{timestamp}.csv"

        if convert_manual_csv(input_file, output_file):
            converted_count += 1

    print(f"\n✅ Conversion complete! Converted {converted_count} files")
    print(f"\n💡 Next step: Run enrichment with:")
    print(f"   python3 re_enrich.py")

if __name__ == '__main__':
    main()
