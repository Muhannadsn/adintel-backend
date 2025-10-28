#!/usr/bin/env python3
"""
Ad Intelligence Analysis Pipeline
Extracts creatives, analyzes them with LLM, and generates insights report.

Usage:
    python run_analysis.py --input data/input/gatc-scraped-data.csv --limit 10
"""

import sys
import os
import argparse
from datetime import datetime

# Add the project root to the Python path
project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, project_root)

from storage.csv_handler import read_input_csv
from extractors.gatc import GATCIExtractor
from analyzers.ollama import OllamaAnalyzer
from analyzers.claude import ClaudeAnalyzer
from analyzers.hybrid import HybridAnalyzer
from analyzers.aggregator import CampaignAggregator


def main():
    parser = argparse.ArgumentParser(description='Run ad intelligence analysis pipeline')
    parser.add_argument('--input', type=str,
                       default='data/input/gatc-scraped-data (1).csv',
                       help='Path to input CSV file')
    parser.add_argument('--limit', type=int, default=None,
                       help='Limit number of ads to process (for testing)')
    parser.add_argument('--skip-extraction', action='store_true',
                       help='Skip screenshot extraction (use existing screenshots)')
    parser.add_argument('--output-json', type=str,
                       default='data/output/insights.json',
                       help='Path to output JSON insights file')
    parser.add_argument('--advertiser', type=str, default=None,
                       help='Filter by specific advertiser name')
    parser.add_argument('--analyzer', type=str, default='hybrid',
                       choices=['ollama', 'claude', 'hybrid'],
                       help='Which analyzer to use (default: hybrid - fastest!)')

    args = parser.parse_args()

    print(f"\n{'='*80}")
    print(f"AD INTELLIGENCE ANALYSIS PIPELINE")
    print(f"{'='*80}\n")
    print(f"Input file: {args.input}")
    print(f"Processing limit: {args.limit if args.limit else 'All ads'}")
    print(f"Skip extraction: {args.skip_extraction}")
    print(f"\nStarting pipeline at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Step 1: Read input CSV
    print(f"📖 Step 1: Reading input CSV...")
    creatives = read_input_csv(args.input)

    if not creatives:
        print("❌ No creatives found in input CSV!")
        return

    # Filter by advertiser if specified
    if args.advertiser:
        creatives = [c for c in creatives if args.advertiser.lower() in c.advertiser.lower()]
        print(f"   Filtered to {len(creatives)} ads for advertiser: {args.advertiser}")

    # Limit if specified
    if args.limit:
        creatives = creatives[:args.limit]

    print(f"   ✓ Loaded {len(creatives)} creatives\n")

    # Step 2: Extract screenshots
    screenshots = []
    if not args.skip_extraction:
        print(f"📸 Step 2: Extracting screenshots...")
        extractor = GATCIExtractor()

        for idx, creative in enumerate(creatives, 1):
            try:
                print(f"   [{idx}/{len(creatives)}] Extracting: {creative.creative[:60]}...")
                screenshot = extractor.extract_creative(creative)
                screenshots.append((screenshot, creative))
            except Exception as e:
                print(f"   ⚠️  Failed to extract creative: {e}")
                continue

        print(f"   ✓ Extracted {len(screenshots)} screenshots\n")
    else:
        print(f"⏭️  Step 2: Skipping extraction (using existing screenshots)\n")

    # Step 3: Analyze with LLM
    if args.analyzer == 'claude':
        print(f"🤖 Step 3: Analyzing with LLM (Claude Vision)...")
        analyzer = ClaudeAnalyzer()
    elif args.analyzer == 'hybrid':
        print(f"🤖 Step 3: Analyzing with LLM (Hybrid: llava + deepseek - FAST!)...")
        analyzer = HybridAnalyzer()
    else:
        print(f"🤖 Step 3: Analyzing with LLM (Ollama)...")
        analyzer = OllamaAnalyzer()

    aggregator = CampaignAggregator()

    for idx, (screenshot, creative) in enumerate(screenshots, 1):
        try:
            print(f"   [{idx}/{len(screenshots)}] Analyzing screenshot for {creative.format} ad...")
            analysis = analyzer.analyze_screenshot(screenshot)

            # Add to aggregator
            aggregator.add_analysis(analysis, creative)

            # Print quick preview
            print(f"      Category: {analysis.product_category}")
            print(f"      Offer: {analysis.offer_type}")
            if analysis.headline:
                print(f"      Headline: {analysis.headline[:60]}...")
            print()

        except Exception as e:
            print(f"   ⚠️  Failed to analyze screenshot: {e}\n")
            continue

    print(f"   ✓ Analyzed {len(aggregator.analyses)} ads\n")

    # Step 4: Generate insights report
    print(f"📊 Step 4: Generating insights report...\n")

    # Print text report
    advertiser_name = args.advertiser or (creatives[0].advertiser if creatives else None)
    text_report = aggregator.generate_text_report(advertiser_name)
    print(text_report)

    # Export JSON
    if args.output_json:
        os.makedirs(os.path.dirname(args.output_json), exist_ok=True)
        aggregator.export_to_json(args.output_json)
        print(f"\n✓ JSON insights exported to: {args.output_json}")

    print(f"\n{'='*80}")
    print(f"Pipeline completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}\n")


if __name__ == '__main__':
    main()
