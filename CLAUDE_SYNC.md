# Claude Sync Notes

## 2025-01-22 – Subscription Detector

- Codex implemented Agent 3 (`agents.subscription_detector.SubscriptionDetector`) along with the shared `AdContext` schema (`agents.context`).
- Unit coverage lives in `tests/test_subscription_detector.py`; please run `pytest tests/test_subscription_detector.py` inside the container to confirm parity.
- If your Docker/SearXNG setup changes subscription handling, let me know so we can adjust the shared catalog (`DEFAULT_SUBSCRIPTIONS`) and the contract documented in `ENRICHMENT_AGENTS_BLUEPRINT.md`.

## 2025-01-22 – Brand Extractor

- Codex implemented Agent 4 (`agents.brand_extractor.BrandExtractor`) with catalog lookups plus an optional LLM resolver hook.
- New dataclasses `BrandMatch`/`BrandRecord` live in `agents.context` and `agents.brand_extractor`; see `AdContext.brand_matches`.
- Tests are in `tests/test_brand_extractor.py`; please run `pytest tests/test_brand_extractor.py` to verify in your environment.
- Blueprint updated with the implementation reference so we stay aligned on the contract.
- Latest update adds fuzzy typo recovery, position/frequency boosts, and grocery brands (Lulu, Al Meera, Monoprix, Snoomart, TalabatMart). Threshold sits at 0.86; feel free to tune if DeepSeek feedback suggests otherwise.
- Added safe-substring guards + heuristics to surface unknown merchants (Talabat URL slugs, title-case nouns, Arabic phrases). These surface as `entity_type="unknown"` so downstream agents can cross-check before committing. Let me know if you want different confidence caps for the heuristics.
- Advertiser-aware prioritisation now available: pass `advertiser_brand_map` to boost the owning brand, infer it when text is silent, and automatically flag conflicts (`brand_conflict_with_advertiser`). `BrandMatch` now exposes `is_advertiser_match`.
- Orchestrator now loads `config/advertiser_brand_map.yaml`; file is pre-populated with Talabat/Snoonu/etc plus placeholder slots for direct electronics/fashion advertisers. Keep this list in sync with your KB so fast paths light up for new merchant IDs.
- Category taxonomy expanded for electronics/fashion/home appliances/sports. `BrandRecord.entity_type` accepts `electronics|fashion|sports|home_appliances`, and `ProductTypeClassifier`/`AI` prompt now expect new product categories (Consumer Electronics, Smartphones & Tablets, etc.). Please mirror any KB additions when you wire new merchants.
