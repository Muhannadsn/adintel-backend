#!/usr/bin/env python3
"""
Simple Python client to test the AdIntel API
"""
import requests
import time
import json
from typing import Dict, Any

API_BASE = "http://localhost:8001"

def scrape_competitor(url: str, max_ads: int = 400) -> Dict[str, Any]:
    """
    Scrape competitor ads

    Args:
        url: Full GATC URL
        max_ads: Maximum number of ads to scrape

    Returns:
        dict: Job information
    """
    print(f"🚀 Starting scrape for: {url}")
    response = requests.post(
        f"{API_BASE}/api/scrape",
        json={"url": url, "max_ads": max_ads}
    )
    result = response.json()
    print(f"📊 Job ID: {result['job_id']}")
    print(f"⏱️  Estimated time: {result['estimated_time']}")
    return result

def check_job(job_id: str) -> Dict[str, Any]:
    """Check job status"""
    response = requests.get(f"{API_BASE}/api/jobs/{job_id}")
    return response.json()

def wait_for_job(job_id: str, check_interval: int = 2) -> Dict[str, Any]:
    """
    Wait for job to complete

    Args:
        job_id: Job ID to monitor
        check_interval: Seconds between checks

    Returns:
        dict: Final job status
    """
    print(f"⏳ Waiting for job {job_id}...")

    while True:
        status = check_job(job_id)
        progress = status.get('progress', 0)

        print(f"   Status: {status['status']} - Progress: {progress}%")

        if status['status'] == 'completed':
            print(f"✅ Job completed!")
            return status
        elif status['status'] == 'failed':
            print(f"❌ Job failed: {status.get('error', 'Unknown error')}")
            return status

        time.sleep(check_interval)

def analyze_ads(csv_file: str, analyzer: str = "hybrid", sample_size: int = 50) -> Dict[str, Any]:
    """
    Analyze ads with AI

    Args:
        csv_file: Path to CSV file
        analyzer: Analyzer type (hybrid, ollama, claude)
        sample_size: Number of ads to analyze

    Returns:
        dict: Job information
    """
    print(f"\n🧠 Starting analysis...")
    print(f"   CSV: {csv_file}")
    print(f"   Analyzer: {analyzer}")
    print(f"   Sample size: {sample_size}")

    response = requests.post(
        f"{API_BASE}/api/analyze",
        json={
            "csv_file": csv_file,
            "analyzer": analyzer,
            "sample_size": sample_size
        }
    )
    result = response.json()
    print(f"📊 Analysis Job ID: {result['job_id']}")
    print(f"⏱️  Estimated time: {result['estimated_time']}")
    return result

def list_competitors() -> list:
    """List all competitors"""
    response = requests.get(f"{API_BASE}/api/competitors")
    return response.json()

# ============================================================================
# Example Usage
# ============================================================================

def example_scrape_talabat():
    """Example: Scrape Talabat ads"""
    print("\n" + "="*80)
    print("EXAMPLE: Scrape Talabat")
    print("="*80 + "\n")

    # Start scraping
    scrape_result = scrape_competitor(
        url="https://adstransparency.google.com/advertiser/AR14306592000630063105?region=QA",
        max_ads=50
    )

    # Wait for completion
    final_status = wait_for_job(scrape_result['job_id'])

    if final_status['status'] == 'completed':
        result = final_status['result']
        print(f"\n✅ SUCCESS!")
        print(f"   Advertiser: {result['advertiser_id']}")
        print(f"   Region: {result['region']}")
        print(f"   Total ads: {result['total_ads']}")
        print(f"   CSV file: {result['csv_file']}")
        print(f"\n📸 Preview (first 3 ads):")
        for i, ad in enumerate(result['ads'][:3], 1):
            print(f"\n   Ad #{i}:")
            print(f"   - ID: {ad['creative_id']}")
            print(f"   - Image: {ad['image_url']}")

        return result['csv_file']

    return None

def example_analyze_ads(csv_file: str):
    """Example: Analyze scraped ads"""
    print("\n" + "="*80)
    print("EXAMPLE: Analyze Ads")
    print("="*80 + "\n")

    # Start analysis
    analysis_result = analyze_ads(
        csv_file=csv_file,
        analyzer="hybrid",
        sample_size=10  # Small sample for demo
    )

    # Wait for completion
    final_status = wait_for_job(analysis_result['job_id'], check_interval=5)

    if final_status['status'] == 'completed':
        print(f"\n✅ ANALYSIS COMPLETE!")
        result = final_status['result']
        print(f"   Output dir: {result['output_dir']}")
        print(f"   Total analyzed: {result['total_analyzed']}")

    return final_status

def example_list_competitors():
    """Example: List all competitors"""
    print("\n" + "="*80)
    print("EXAMPLE: List Competitors")
    print("="*80 + "\n")

    competitors = list_competitors()

    if competitors:
        print(f"📋 Found {len(competitors)} competitor(s):\n")
        for comp in competitors:
            print(f"   Name: {comp['name']}")
            print(f"   ID: {comp['advertiser_id']}")
            print(f"   Region: {comp['region']}")
            print(f"   Total ads: {comp['total_ads']}")
            print(f"   Last scraped: {comp['last_scraped']}")
            print(f"   CSV: {comp['csv_file']}")
            print()
    else:
        print("   No competitors found yet.")

if __name__ == "__main__":
    import sys

    print("\n" + "="*80)
    print("🎯 AdIntel API Test Client")
    print("="*80)

    # Check if API is running
    try:
        response = requests.get(f"{API_BASE}/")
        api_info = response.json()
        print(f"\n✅ API is running!")
        print(f"   Version: {api_info['version']}")
    except Exception as e:
        print(f"\n❌ ERROR: Cannot connect to API at {API_BASE}")
        print(f"   Make sure the API is running: cd api && python main.py")
        sys.exit(1)

    # Menu
    print("\n📋 Choose an example:")
    print("   1. Scrape Talabat ads")
    print("   2. Analyze existing CSV")
    print("   3. List all competitors")
    print("   4. Full workflow (scrape + analyze)")
    print("   0. Exit")

    choice = input("\nEnter choice (1-4): ").strip()

    if choice == "1":
        csv_file = example_scrape_talabat()
        if csv_file:
            print(f"\n💡 TIP: To analyze these ads, run:")
            print(f"   python api/test_client.py --analyze {csv_file}")

    elif choice == "2":
        csv_file = input("Enter CSV file path: ").strip()
        if csv_file:
            example_analyze_ads(csv_file)

    elif choice == "3":
        example_list_competitors()

    elif choice == "4":
        print("\n🚀 Running full workflow...")
        csv_file = example_scrape_talabat()
        if csv_file:
            example_analyze_ads(csv_file)

    elif choice == "0":
        print("\n👋 Goodbye!")

    else:
        print("\n❌ Invalid choice")

    print("\n" + "="*80)
    print("✅ Done!")
    print("="*80 + "\n")
