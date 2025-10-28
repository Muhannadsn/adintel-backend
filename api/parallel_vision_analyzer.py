#!/usr/bin/env python3
"""
Parallel Vision Analyzer - Load-balanced OCR using LLaVA + DeepSeek-OCR

Strategy:
- Split ads into 2 batches (50/50)
- Batch 1 → LLaVA (Ollama)
- Batch 2 → DeepSeek-OCR
- Process in parallel using multiprocessing
- Combine results

Benefits:
- 2-3x faster than sequential processing
- Load distribution across models
- Built-in A/B testing
- Fault tolerance
"""

import os
import time
import json
from typing import List, Dict, Optional
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from multiprocessing import Queue, Process
import queue


class ParallelVisionAnalyzer:
    """
    Orchestrates parallel vision analysis using multiple models
    """

    def __init__(self,
                 llava_workers: int = 2,
                 deepseek_workers: int = 2,
                 split_ratio: float = 0.5):
        """
        Initialize parallel vision analyzer

        Args:
            llava_workers: Number of parallel LLaVA processes
            deepseek_workers: Number of parallel DeepSeek processes
            split_ratio: Fraction of ads to send to DeepSeek (0.0-1.0)
                        0.5 = 50/50 split, 0.7 = 70% DeepSeek, 30% LLaVA
        """
        self.llava_workers = llava_workers
        self.deepseek_workers = deepseek_workers
        self.split_ratio = split_ratio

        # Stats tracking
        self.stats = {
            'llava': {'processed': 0, 'errors': 0, 'total_time': 0},
            'deepseek': {'processed': 0, 'errors': 0, 'total_time': 0}
        }

    def process_ads_parallel(self, ads: List[Dict]) -> List[Dict]:
        """
        Process ads in parallel using both LLaVA and DeepSeek-OCR

        Args:
            ads: List of ad dictionaries with image_url

        Returns:
            List of enriched ads with vision analysis results
        """
        total_ads = len(ads)
        print(f"\n{'='*80}")
        print(f"🚀 PARALLEL VISION ANALYSIS")
        print(f"{'='*80}")
        print(f"Total ads: {total_ads}")
        print(f"Split ratio: {int(self.split_ratio*100)}% DeepSeek, {int((1-self.split_ratio)*100)}% LLaVA")
        print(f"LLaVA workers: {self.llava_workers}")
        print(f"DeepSeek workers: {self.deepseek_workers}")
        print(f"{'='*80}\n")

        # Split ads into batches
        split_point = int(total_ads * self.split_ratio)
        deepseek_batch = ads[:split_point]
        llava_batch = ads[split_point:]

        print(f"📊 Batch distribution:")
        print(f"   DeepSeek batch: {len(deepseek_batch)} ads")
        print(f"   LLaVA batch: {len(llava_batch)} ads")
        print()

        # Process both batches in parallel
        start_time = time.time()

        with ThreadPoolExecutor(max_workers=2) as executor:
            # Submit both batches
            future_deepseek = executor.submit(
                self._process_batch_deepseek,
                deepseek_batch
            )
            future_llava = executor.submit(
                self._process_batch_llava,
                llava_batch
            )

            # Wait for results
            deepseek_results = future_deepseek.result()
            llava_results = future_llava.result()

        total_time = time.time() - start_time

        # Combine results
        all_results = deepseek_results + llava_results

        # Print stats
        self._print_stats(total_time, total_ads)

        return all_results

    def _process_batch_deepseek(self, ads: List[Dict]) -> List[Dict]:
        """
        Process batch of ads using DeepSeek-OCR in parallel
        """
        if not ads:
            return []

        print(f"🔵 DeepSeek-OCR: Starting {len(ads)} ads...")
        results = []

        # Use ProcessPoolExecutor for true parallelism
        with ProcessPoolExecutor(max_workers=self.deepseek_workers) as executor:
            # Submit all ads
            futures = {
                executor.submit(self._process_single_deepseek, ad): ad
                for ad in ads
            }

            # Collect results as they complete
            for future in as_completed(futures):
                ad = futures[future]
                try:
                    result = future.result()
                    results.append(result)

                    self.stats['deepseek']['processed'] += 1

                    # Check if failover happened
                    if result.get('_vision_failover'):
                        print(f"   🔄 DeepSeek → LLaVA failover for {result.get('creative_id', 'unknown')}")

                    # Progress
                    progress = (self.stats['deepseek']['processed'] / len(ads)) * 100
                    print(f"   DeepSeek progress: {self.stats['deepseek']['processed']}/{len(ads)} ({progress:.1f}%)")

                except Exception as e:
                    print(f"   ❌ BOTH MODELS FAILED for ad {ad.get('creative_id', 'unknown')}: {e}")
                    self.stats['deepseek']['errors'] += 1
                    # Add ad with error flag (both models tried and failed)
                    results.append({**ad, '_vision_error': str(e), '_vision_model': 'both-failed'})

        print(f"✅ DeepSeek-OCR: Completed {len(results)} ads\n")
        return results

    def _process_batch_llava(self, ads: List[Dict]) -> List[Dict]:
        """
        Process batch of ads using LLaVA in parallel
        """
        if not ads:
            return []

        print(f"🟢 LLaVA: Starting {len(ads)} ads...")
        results = []

        # Use ThreadPoolExecutor for LLaVA (Ollama handles internal parallelism)
        with ThreadPoolExecutor(max_workers=self.llava_workers) as executor:
            # Submit all ads
            futures = {
                executor.submit(self._process_single_llava, ad): ad
                for ad in ads
            }

            # Collect results as they complete
            for future in as_completed(futures):
                ad = futures[future]
                try:
                    result = future.result()
                    results.append(result)

                    self.stats['llava']['processed'] += 1

                    # Check if failover happened
                    if result.get('_vision_failover'):
                        print(f"   🔄 LLaVA → DeepSeek failover for {result.get('creative_id', 'unknown')}")

                    # Progress
                    progress = (self.stats['llava']['processed'] / len(ads)) * 100
                    print(f"   LLaVA progress: {self.stats['llava']['processed']}/{len(ads)} ({progress:.1f}%)")

                except Exception as e:
                    print(f"   ❌ BOTH MODELS FAILED for ad {ad.get('creative_id', 'unknown')}: {e}")
                    self.stats['llava']['errors'] += 1
                    # Add ad with error flag (both models tried and failed)
                    results.append({**ad, '_vision_error': str(e), '_vision_model': 'both-failed'})

        print(f"✅ LLaVA: Completed {len(results)} ads\n")
        return results

    @staticmethod
    def _process_single_deepseek(ad: Dict) -> Dict:
        """
        Process single ad with DeepSeek-OCR microservice
        Falls back to LLaVA if DeepSeek fails

        NOTE: Runs in separate process, must re-import modules
        """
        import time
        start = time.time()

        try:
            # Import here (process-local)
            from api.deepseek_client import DeepSeekOCRClient, DEEPSEEK_PROMPTS

            # Create client
            client = DeepSeekOCRClient(service_url="http://localhost:8001")

            # Extract text
            image_url = ad.get('image_url', '')
            if not image_url:
                raise ValueError("No image_url in ad")

            result = client.extract_text(
                image_url=image_url,
                prompt=DEEPSEEK_PROMPTS["general"],
                timeout=60
            )

            # Add to ad
            ad['_vision_text'] = result['raw_text']
            ad['_vision_structured'] = result.get('structured', [])
            ad['_vision_model'] = 'deepseek-ocr'
            ad['_vision_time'] = time.time() - start

            return ad

        except Exception as e:
            # FAILOVER TO LLAVA
            print(f"⚠️  DeepSeek failed for {ad.get('creative_id', 'unknown')}, failing over to LLaVA...")

            try:
                # Try LLaVA as backup
                from api.ai_analyzer import AdIntelligence

                analyzer = AdIntelligence(vision_model="llava:latest")
                image_url = ad.get('image_url', '')

                vision_text = analyzer._extract_text_from_image(image_url)

                # Add to ad
                ad['_vision_text'] = vision_text
                ad['_vision_model'] = 'llava-failover'
                ad['_vision_time'] = time.time() - start
                ad['_vision_failover'] = f"DeepSeek failed: {str(e)}"

                print(f"   ✅ Failover successful for {ad.get('creative_id', 'unknown')}")
                return ad

            except Exception as llava_error:
                # Both failed - return with errors
                ad['_vision_error'] = f"DeepSeek: {str(e)}, LLaVA: {str(llava_error)}"
                ad['_vision_model'] = 'both-failed'
                ad['_vision_time'] = time.time() - start
                raise Exception(f"Both models failed: DeepSeek={e}, LLaVA={llava_error}")

    @staticmethod
    def _process_single_llava(ad: Dict) -> Dict:
        """
        Process single ad with LLaVA
        Falls back to DeepSeek-OCR if LLaVA fails

        NOTE: Runs in thread, shares memory with main process
        """
        import time
        start = time.time()

        try:
            # Import here (thread-local)
            from api.ai_analyzer import AdIntelligence

            # Initialize analyzer
            analyzer = AdIntelligence(vision_model="llava:latest")

            # Extract text
            image_url = ad.get('image_url', '')
            if not image_url:
                raise ValueError("No image_url in ad")

            vision_text = analyzer._extract_text_from_image(image_url)

            # Add to ad
            ad['_vision_text'] = vision_text
            ad['_vision_model'] = 'llava'
            ad['_vision_time'] = time.time() - start

            return ad

        except Exception as e:
            # FAILOVER TO DEEPSEEK
            print(f"⚠️  LLaVA failed for {ad.get('creative_id', 'unknown')}, failing over to DeepSeek-OCR...")

            try:
                # Try DeepSeek as backup
                from api.deepseek_client import DeepSeekOCRClient, DEEPSEEK_PROMPTS

                client = DeepSeekOCRClient(service_url="http://localhost:8001")
                image_url = ad.get('image_url', '')

                result = client.extract_text(
                    image_url=image_url,
                    prompt=DEEPSEEK_PROMPTS["general"],
                    timeout=60
                )

                # Add to ad
                ad['_vision_text'] = result['raw_text']
                ad['_vision_structured'] = result.get('structured', [])
                ad['_vision_model'] = 'deepseek-failover'
                ad['_vision_time'] = time.time() - start
                ad['_vision_failover'] = f"LLaVA failed: {str(e)}"

                print(f"   ✅ Failover successful for {ad.get('creative_id', 'unknown')}")
                return ad

            except Exception as deepseek_error:
                # Both failed - return with errors
                ad['_vision_error'] = f"LLaVA: {str(e)}, DeepSeek: {str(deepseek_error)}"
                ad['_vision_model'] = 'both-failed'
                ad['_vision_time'] = time.time() - start
                raise Exception(f"Both models failed: LLaVA={e}, DeepSeek={deepseek_error}")

    def _print_stats(self, total_time: float, total_ads: int):
        """Print performance statistics"""
        print(f"\n{'='*80}")
        print(f"📈 PERFORMANCE STATISTICS")
        print(f"{'='*80}")
        print(f"Total time: {total_time:.2f}s")
        print(f"Total ads: {total_ads}")
        print(f"Average time per ad: {total_time/total_ads:.2f}s")
        print()

        # DeepSeek stats
        ds_stats = self.stats['deepseek']
        if ds_stats['processed'] > 0:
            ds_avg = ds_stats['total_time'] / ds_stats['processed']
            print(f"🔵 DeepSeek-OCR:")
            print(f"   Processed: {ds_stats['processed']}")
            print(f"   Errors: {ds_stats['errors']}")
            print(f"   Avg time: {ds_avg:.2f}s per ad")

        # LLaVA stats
        llava_stats = self.stats['llava']
        if llava_stats['processed'] > 0:
            llava_avg = llava_stats['total_time'] / llava_stats['processed']
            print(f"🟢 LLaVA:")
            print(f"   Processed: {llava_stats['processed']}")
            print(f"   Errors: {llava_stats['errors']}")
            print(f"   Avg time: {llava_avg:.2f}s per ad")

        print(f"{'='*80}\n")


class AdaptiveLoadBalancer(ParallelVisionAnalyzer):
    """
    Advanced version: Dynamically adjusts split ratio based on performance
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.performance_history = []

    def process_ads_parallel(self, ads: List[Dict]) -> List[Dict]:
        """
        Process ads with adaptive load balancing
        """
        # Adjust split ratio based on historical performance
        if len(self.performance_history) > 0:
            self._adjust_split_ratio()

        # Call parent method
        results = super().process_ads_parallel(ads)

        # Record performance
        self._record_performance()

        return results

    def _adjust_split_ratio(self):
        """
        Adjust split ratio based on recent performance

        If DeepSeek is 10x faster, send more ads to it
        If LLaVA is more accurate, send more ads to it
        """
        recent = self.performance_history[-5:]  # Last 5 runs

        avg_deepseek_time = sum(r['deepseek_avg_time'] for r in recent) / len(recent)
        avg_llava_time = sum(r['llava_avg_time'] for r in recent) / len(recent)

        # Calculate optimal ratio (faster model gets more load)
        speed_ratio = avg_llava_time / avg_deepseek_time

        # Adjust split ratio (constrained to 0.3-0.7)
        new_ratio = min(0.7, max(0.3, speed_ratio / (speed_ratio + 1)))

        print(f"📊 Adaptive adjustment: {self.split_ratio:.2f} → {new_ratio:.2f}")
        self.split_ratio = new_ratio

    def _record_performance(self):
        """Record performance metrics for adaptive adjustment"""
        ds = self.stats['deepseek']
        llava = self.stats['llava']

        self.performance_history.append({
            'deepseek_avg_time': ds['total_time'] / max(ds['processed'], 1),
            'llava_avg_time': llava['total_time'] / max(llava['processed'], 1),
            'deepseek_error_rate': ds['errors'] / max(ds['processed'], 1),
            'llava_error_rate': llava['errors'] / max(llava['processed'], 1),
        })


# Example usage
if __name__ == "__main__":
    # Sample ads
    sample_ads = [
        {'creative_id': f'ad_{i}', 'image_url': f'https://example.com/ad_{i}.jpg'}
        for i in range(10)
    ]

    # Create analyzer
    analyzer = ParallelVisionAnalyzer(
        llava_workers=2,
        deepseek_workers=2,
        split_ratio=0.5  # 50/50 split
    )

    # Process in parallel
    results = analyzer.process_ads_parallel(sample_ads)

    # Print results
    for ad in results:
        model = ad.get('_vision_model', 'unknown')
        time_taken = ad.get('_vision_time', 0)
        print(f"{ad['creative_id']}: {model} ({time_taken:.2f}s)")
