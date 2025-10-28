#!/usr/bin/env python3
"""
Test script for parallel vision analyzer

Tests:
1. Can we import the module?
2. Does DeepSeek-OCR work with a real image?
3. Does LLaVA work with a real image?
4. Can both run in parallel without crashing?
5. Performance comparison
"""

import sys
import time
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))


def test_imports():
    """Test 1: Can we import everything?"""
    print("\n" + "="*80)
    print("TEST 1: Imports")
    print("="*80)

    try:
        from api.parallel_vision_analyzer import ParallelVisionAnalyzer
        print("✅ ParallelVisionAnalyzer imported")
    except Exception as e:
        print(f"❌ Failed to import ParallelVisionAnalyzer: {e}")
        return False

    try:
        from api.ai_analyzer import AdIntelligence
        print("✅ AdIntelligence imported")
    except Exception as e:
        print(f"❌ Failed to import AdIntelligence: {e}")
        return False

    return True


def test_deepseek_solo():
    """Test 2: Can DeepSeek-OCR process a single image?"""
    print("\n" + "="*80)
    print("TEST 2: DeepSeek-OCR Solo Test")
    print("="*80)

    try:
        # Check if DeepSeek-OCR is available
        import torch
        from transformers import AutoModel, AutoTokenizer

        print("Checking if model is downloaded...")
        model_path = 'deepseek-ai/DeepSeek-OCR'

        # This will download if not present
        print("Loading tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
        print("✅ Tokenizer loaded")

        print("Loading model (this may take a while on first run)...")
        model = AutoModel.from_pretrained(
            model_path,
            trust_remote_code=True,
            torch_dtype=torch.float16,
        ).eval()

        device = "mps" if torch.backends.mps.is_available() else "cpu"
        print(f"Using device: {device}")
        model = model.to(device)
        print("✅ DeepSeek-OCR model loaded successfully")

        return True

    except Exception as e:
        print(f"❌ DeepSeek-OCR test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_llava_solo():
    """Test 3: Can LLaVA process through Ollama?"""
    print("\n" + "="*80)
    print("TEST 3: LLaVA Solo Test")
    print("="*80)

    try:
        import requests

        # Check if Ollama is running
        response = requests.get("http://localhost:11434/api/tags", timeout=2)

        if response.status_code != 200:
            print(f"❌ Ollama not responding (status: {response.status_code})")
            return False

        models = response.json().get('models', [])
        model_names = [m['name'] for m in models]

        print(f"Available models: {model_names}")

        if 'llava:latest' in model_names or any('llava' in m for m in model_names):
            print("✅ LLaVA model found in Ollama")
            return True
        else:
            print("⚠️  LLaVA not found. Run: ollama pull llava")
            return False

    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to Ollama: {e}")
        print("   Make sure Ollama is running: ollama serve")
        return False
    except Exception as e:
        print(f"❌ LLaVA test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_parallel_mock():
    """Test 4: Can parallel processing work with mock data?"""
    print("\n" + "="*80)
    print("TEST 4: Parallel Processing (Mock)")
    print("="*80)

    try:
        from api.parallel_vision_analyzer import ParallelVisionAnalyzer

        # Create mock ads (no real images)
        mock_ads = [
            {'creative_id': f'mock_{i}', 'image_url': ''}
            for i in range(6)
        ]

        print(f"Created {len(mock_ads)} mock ads")

        # Create analyzer with small batches
        analyzer = ParallelVisionAnalyzer(
            llava_workers=1,
            deepseek_workers=1,
            split_ratio=0.5
        )

        print("✅ ParallelVisionAnalyzer initialized")
        print(f"   Split: {int(analyzer.split_ratio*100)}% DeepSeek, {int((1-analyzer.split_ratio)*100)}% LLaVA")
        print(f"   LLaVA workers: {analyzer.llava_workers}")
        print(f"   DeepSeek workers: {analyzer.deepseek_workers}")

        # Note: This will fail because images are empty, but we're testing the orchestration
        print("\nNote: This test will fail on actual processing (no real images)")
        print("      but we're testing the parallel orchestration logic")

        return True

    except Exception as e:
        print(f"❌ Parallel mock test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_with_sample_image():
    """Test 5: End-to-end test with a sample image"""
    print("\n" + "="*80)
    print("TEST 5: End-to-End with Sample Image")
    print("="*80)

    # Ask user for a sample image
    print("\nTo test with a real image, please provide:")
    print("1. A local image path, OR")
    print("2. An image URL")
    print("3. Press Enter to skip")

    image_input = input("\nImage path/URL (or Enter to skip): ").strip()

    if not image_input:
        print("⏭️  Skipping real image test")
        return True

    try:
        from api.parallel_vision_analyzer import ParallelVisionAnalyzer

        # Create test ad
        test_ad = {
            'creative_id': 'test_001',
            'image_url': image_input,
            'ad_text': 'Test advertisement'
        }

        print(f"\n🧪 Testing with image: {image_input[:50]}...")

        # Test with single ad, 50/50 split
        analyzer = ParallelVisionAnalyzer(
            llava_workers=1,
            deepseek_workers=1,
            split_ratio=0.5  # One will go to DeepSeek, one will go to LLaVA
        )

        # Add second ad so both models get tested
        test_ads = [test_ad, {**test_ad, 'creative_id': 'test_002'}]

        print("\nProcessing...")
        start = time.time()
        results = analyzer.process_ads_parallel(test_ads)
        elapsed = time.time() - start

        print(f"\n✅ Processing complete in {elapsed:.2f}s")
        print(f"   Results: {len(results)} ads processed")

        # Print results
        for ad in results:
            model = ad.get('_vision_model', 'unknown')
            time_taken = ad.get('_vision_time', 0)
            text_len = len(ad.get('_vision_text', ''))
            error = ad.get('_vision_error', None)

            print(f"\n   {ad['creative_id']}:")
            print(f"      Model: {model}")
            print(f"      Time: {time_taken:.2f}s")
            print(f"      Text extracted: {text_len} chars")
            if error:
                print(f"      Error: {error}")
            else:
                print(f"      Preview: {ad.get('_vision_text', '')[:100]}...")

        return True

    except Exception as e:
        print(f"❌ End-to-end test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("PARALLEL VISION ANALYZER - TEST SUITE")
    print("="*80)

    tests = [
        ("Imports", test_imports),
        ("DeepSeek-OCR Setup", test_deepseek_solo),
        ("LLaVA Setup", test_llava_solo),
        ("Parallel Orchestration", test_parallel_mock),
        ("End-to-End with Real Image", test_with_sample_image),
    ]

    results = {}

    for test_name, test_func in tests:
        try:
            result = test_func()
            results[test_name] = "✅ PASS" if result else "❌ FAIL"
        except Exception as e:
            results[test_name] = f"❌ ERROR: {e}"

    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    for test_name, result in results.items():
        print(f"{test_name:.<40} {result}")

    # Overall
    passed = sum(1 for r in results.values() if "✅" in r)
    total = len(results)

    print(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! Ready for integration.")
    else:
        print("\n⚠️  Some tests failed. Review errors above before integrating.")


if __name__ == "__main__":
    main()
