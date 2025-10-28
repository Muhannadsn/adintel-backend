#!/usr/bin/env python3
"""
Test Parallel Vision with DeepSeek-OCR Microservice

This test validates:
1. DeepSeek-OCR microservice is running
2. LLaVA (Ollama) is running
3. Both can process images in parallel
4. Performance comparison
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


def test_services():
    """Test 1: Are both services running?"""
    print("\n" + "="*80)
    print("TEST 1: Service Health Checks")
    print("="*80)

    # Test DeepSeek-OCR
    from api.deepseek_client import DeepSeekOCRClient

    deepseek_client = DeepSeekOCRClient()
    deepseek_healthy = deepseek_client.health_check()

    if deepseek_healthy:
        print("✅ DeepSeek-OCR service is healthy (http://localhost:8001)")
    else:
        print("❌ DeepSeek-OCR service is DOWN")
        print("   Start it with:")
        print("   cd ~/Desktop/DeepSeek-OCR && ./start_service.sh")
        return False

    # Test LLaVA (Ollama)
    import requests
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        if response.status_code == 200:
            models = [m['name'] for m in response.json().get('models', [])]
            if any('llava' in m for m in models):
                print("✅ LLaVA service is healthy (Ollama)")
            else:
                print("⚠️  Ollama is running but LLaVA not found")
                print("   Install: ollama pull llava")
                return False
        else:
            print("❌ Ollama not responding")
            return False
    except:
        print("❌ Ollama service is DOWN")
        print("   Start it with: ollama serve")
        return False

    return True


def test_parallel_with_real_images():
    """Test 2: Parallel processing with real images"""
    print("\n" + "="*80)
    print("TEST 2: Parallel Processing with Real Images")
    print("="*80)

    # Get test images from user
    print("\nProvide 2+ image URLs to test parallel processing:")
    print("(These will be split 50/50 between DeepSeek and LLaVA)")
    print()

    image_urls = []
    for i in range(1, 5):
        url = input(f"Image {i} URL (or press Enter to finish): ").strip()
        if not url:
            break
        image_urls.append(url)

    if len(image_urls) < 2:
        print("⏭️  Need at least 2 images for parallel test. Skipping...")
        return True

    # Create test ads
    test_ads = [
        {
            'creative_id': f'test_{i}',
            'image_url': url,
            'ad_text': f'Test ad {i}'
        }
        for i, url in enumerate(image_urls, 1)
    ]

    print(f"\n🚀 Processing {len(test_ads)} ads in parallel...")
    print(f"   {len(test_ads)//2} → DeepSeek-OCR")
    print(f"   {len(test_ads) - len(test_ads)//2} → LLaVA")

    # Run parallel processing
    from api.parallel_vision_analyzer import ParallelVisionAnalyzer

    analyzer = ParallelVisionAnalyzer(
        llava_workers=2,
        deepseek_workers=2,
        split_ratio=0.5  # 50/50 split
    )

    start = time.time()
    results = analyzer.process_ads_parallel(test_ads)
    elapsed = time.time() - start

    # Print results
    print(f"\n{'='*80}")
    print("RESULTS")
    print(f"{'='*80}")
    print(f"Total time: {elapsed:.2f}s")
    print(f"Average per ad: {elapsed/len(results):.2f}s")
    print()

    # Group by model
    deepseek_results = [r for r in results if r.get('_vision_model') == 'deepseek-ocr']
    llava_results = [r for r in results if r.get('_vision_model') == 'llava']

    print(f"🔵 DeepSeek-OCR: {len(deepseek_results)} ads")
    for ad in deepseek_results:
        error = ad.get('_vision_error')
        if error:
            print(f"   ❌ {ad['creative_id']}: {error}")
        else:
            text_len = len(ad.get('_vision_text', ''))
            time_taken = ad.get('_vision_time', 0)
            print(f"   ✅ {ad['creative_id']}: {text_len} chars in {time_taken:.2f}s")

    print(f"\n🟢 LLaVA: {len(llava_results)} ads")
    for ad in llava_results:
        error = ad.get('_vision_error')
        if error:
            print(f"   ❌ {ad['creative_id']}: {error}")
        else:
            text_len = len(ad.get('_vision_text', ''))
            time_taken = ad.get('_vision_time', 0)
            print(f"   ✅ {ad['creative_id']}: {text_len} chars in {time_taken:.2f}s")

    # Show sample outputs
    print(f"\n{'='*80}")
    print("SAMPLE OUTPUTS")
    print(f"{'='*80}")

    if deepseek_results and not deepseek_results[0].get('_vision_error'):
        print(f"\n🔵 DeepSeek-OCR sample ({deepseek_results[0]['creative_id']}):")
        print(deepseek_results[0]['_vision_text'][:300] + "...")

    if llava_results and not llava_results[0].get('_vision_error'):
        print(f"\n🟢 LLaVA sample ({llava_results[0]['creative_id']}):")
        print(llava_results[0]['_vision_text'][:300] + "...")

    return True


def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("PARALLEL VISION ANALYZER - MICROSERVICE TEST")
    print("="*80)

    # Test 1: Services
    if not test_services():
        print("\n❌ Services not ready. Fix the issues above and try again.")
        return

    # Test 2: Parallel processing
    test_parallel_with_real_images()

    print("\n" + "="*80)
    print("✅ TEST COMPLETE")
    print("="*80)
    print("\nYour parallel vision system is ready!")
    print("\nNext steps:")
    print("1. Integrate into your scraper pipeline")
    print("2. Monitor performance and error rates")
    print("3. Adjust split_ratio based on results")


if __name__ == "__main__":
    main()
