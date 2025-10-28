# AdIntel API Documentation

Competitive Ad Intelligence Dashboard for Food Delivery

  AdIntel is a real-time competitive intelligence platform that monitors advertising strategies across Qatar's food delivery market (Talabat, Deliveroo, Keeta, Rafiq, Snoonu).

  How It Works:
  1. Automated Scraping: Pulls ad data from Google Ad Transparency Center API
  2. AI Enrichment: Uses local Ollama models (LLaMA 3.1 for text, LLaVa for vision) to analyze each ad and extract:
    - Product categories (Fast Food, Pharmacy, Groceries, etc.)
    - Promotional offers (discounts, BOGO, free delivery)
    - Messaging themes (speed, price, convenience)
    - Target audiences and restaurant brands
  3. Strategic Insights: Displays competitive intelligence through interactive dashboards showing category dominance, promo intensity, creative velocity, and messaging battles

  Problem It Solves:
  Marketing teams waste hours manually tracking competitor ads across platforms. They lack visibility into what categories competitors are pushing, which promotions are running, and how aggressive their ad
  spend is.

  Value Delivered:
  - Gap Analysis: Instantly identifies categories where competitors advertise but you don't
  - Promo Intelligence: Tracks discount wars and offer timing
  - Category Insights: Shows which product categories each platform prioritizes (e.g., Rafiq's pharmacy push)
  - Market Share: Visualizes ad volume distribution across competitors
  - Qatar-Specific: Filters out UAE/Dubai noise to focus on Qatar market only

  Result: Teams make data-driven decisions on ad budgets, promotional strategies, and category expansion—turning weeks of manual research into instant, actionable intelligence.

This file provides documentation for the AdIntel API.

## `api/main.py`

This module provides the main API for the Ad Intelligence platform. It exposes endpoints for scraping competitor ads, analyzing them with AI, and retrieving strategic insights.

The API is built with FastAPI and uses a combination of in-memory job storage and a SQLite database for persistence. It is designed to be run as a standalone service that can be consumed by a frontend application.

### Endpoints

#### `GET /`

-   **Purpose:** Health check endpoint to verify that the API is running.
-   **Returns:** A JSON object with a welcome message, API version, and a list of available endpoints.

#### `POST /api/scrape`

-   **Purpose:** Scrapes competitor ads from a given Google Ad Transparency Center URL. This is an asynchronous job.
-   **Request Body:**
    -   `url` (str): The full GATC URL to scrape.
    -   `max_ads` (int, optional): The maximum number of ads to scrape. Defaults to 400.
    -   `name` (str, optional): The name of the competitor.
-   **Returns:** A JSON object with the job ID, status, and other details.

#### `GET /api/jobs/{job_id}`

-   **Purpose:** Checks the status of a scraping or analysis job.
-   **Path Parameters:**
    -   `job_id` (str): The ID of the job to check.
-   **Returns:** A JSON object with the job status, progress, and results if completed.

#### `POST /api/analyze`

-   **Purpose:** Analyzes scraped ads from a CSV file using an AI analyzer. This is an asynchronous job.
-   **Request Body:**
    -   `csv_file` (str): The path to the CSV file to analyze.
    -   `analyzer` (str, optional): The analyzer to use (`hybrid`, `ollama`, or `claude`). Defaults to `hybrid`.
    -   `sample_size` (int, optional): The number of ads to analyze. Defaults to 50.
-   **Returns:** A JSON object with the job ID, status, and other details.

#### `GET /api/competitors`

-   **Purpose:** Lists all scraped competitors, deduplicated by advertiser ID and showing the most recent scrape.
-   **Returns:** A list of JSON objects, each representing a competitor.

#### `GET /api/insights/products`

-   **Purpose:** Provides a breakdown of product categories by competitor.
-   **Query Parameters:**
    -   `advertiser_id` (str, optional): Filter by a specific advertiser ID.
-   **Returns:** A JSON object with a list of product insights.

#### `GET /api/insights/messaging`

-   **Purpose:** Provides a breakdown of messaging themes across competitors.
-   **Query Parameters:**
    -   `time_range` (str, optional): Filter by time range (`7d`, `30d`, `all`). Defaults to `all`.
    -   `advertiser_id` (str, optional): Filter by a specific advertiser ID.
-   **Returns:** A JSON object with a list of messaging insights.

#### `GET /api/insights/velocity`

-   **Purpose:** Provides the creative velocity (daily new ad launch frequency) for the last N days.
-   **Query Parameters:**
    -   `days` (int, optional): The number of days to look back. Defaults to 30.
-   **Returns:** A JSON object with a timeline of daily ad launch data.

#### `GET /api/insights/audiences`

-   **Purpose:** Provides a breakdown of audience segment targeting across competitors.
-   **Returns:** A JSON object with a list of audience insights.

#### `GET /api/insights/promos`

-   **Purpose:** Provides a timeline of promo/offer intensity.
-   **Query Parameters:**
    -   `days` (int, optional): The number of days to look back. Defaults to 30.
-   **Returns:** A JSON object with a timeline of daily promo stats.

#### `GET /api/competitors/{advertiser_id}/insights`

-   **Purpose:** Provides strategic insights for a specific competitor.
-   **Path Parameters:**
    -   `advertiser_id` (str): The ID of the advertiser.
-   **Returns:** A JSON object with strategic insights for the competitor.

#### `GET /api/competitors/{advertiser_id}/ads`

-   **Purpose:** Retrieves all ads for a specific competitor.
-   **Path Parameters:**
    -   `advertiser_id` (str): The ID of the advertiser.
-   **Query Parameters:**
    -   `limit` (int, optional): The maximum number of ads to return. Defaults to 50.
    -   `active_only` (bool, optional): Whether to return only active ads. Defaults to `True`.
    -   `category` (str, optional): Filter by product category.
-   **Returns:** A JSON object with a list of ads for the competitor.

#### `GET /api/insights/offers`

-   **Purpose:** Provides a breakdown of active offers with percentage distribution.
-   **Returns:** A JSON object with a list of offer insights.

#### `GET /api/insights/restaurants`

-   **Purpose:** Provides a breakdown of the top restaurants being promoted.
-   **Returns:** A JSON object with a list of restaurant insights.

#### `GET /api/insights/weekly`

-   **Purpose:** Generates AI-powered weekly insights comparing all competitors.
-   **Query Parameters:**
    -   `use_ai` (bool, optional): Whether to use Vision AI analysis. Defaults to `False`.
    -   `sample_size` (int, optional): The number of ads to analyze per competitor. Defaults to 3.
-   **Returns:** A JSON object with a strategic summary and top 3 actionable insights.

#### `GET /api/insights/strategic/{module}`

-   **Purpose:** Generates personalized AI strategic insights comparing your company vs competitors.
-   **Path Parameters:**
    -   `module` (str): The module to generate insights for (`products`, `messaging`, `velocity`, `audiences`, `platforms`, or `promos`).
-   **Returns:** A JSON object with a list of actionable quick actions.

### Helper Functions

#### `get_advertiser_name(advertiser_id: str) -> str`

-   **Purpose:** Returns a friendly name for a given advertiser ID.
-   **Args:**
    -   `advertiser_id` (str): The advertiser ID.
-   **Returns:** The advertiser's name, or the ID if not found.

#### `create_job(job_type: str, params: dict) -> str`

-   **Purpose:** Creates a new job in the in-memory job store.
-   **Args:**
    -   `job_type` (str): The type of job (`scrape` or `analyze`).
    -   `params` (dict): The parameters for the job.
-   **Returns:** The job ID.

#### `update_job(job_id: str, updates: dict)`

-   **Purpose:** Updates the status of a job in the in-memory job store.
-   **Args:**
    -   `job_id` (str): The ID of the job to update.
    -   `updates` (dict): A dictionary of updates to apply to the job.

#### `run_scraper_task(job_id: str, url: str, max_ads: int)`

-   **Purpose:** A background task that runs the ad scraper.
-   **Args:**
    -   `job_id` (str): The ID of the job.
    -   `url` (str): The GATC URL to scrape.
    -   `max_ads` (int): The maximum number of ads to scrape.

#### `run_analyzer_task(job_id: str, csv_file: str, analyzer: str, sample_size: int)`

-   **Purpose:** A background task that runs the ad analyzer.
-   **Args:**
    -   `job_id` (str): The ID of the job.
    -   `csv_file` (str): The path to the CSV file to analyze.
    -   `analyzer` (str): The analyzer to use.
    -   `sample_size` (int): The number of ads to analyze.

## `scrapers/api_scraper.py`

This module provides a native Python implementation for scraping ads from the Google Ad Transparency Center (GATC) API. It is designed to be fast and efficient, as it does not require a browser to run.

The scraper works by reverse-engineering the GATC's internal `SearchCreatives` RPC API. It can be used to fetch ads for a specific advertiser and region, and it also supports optional AI enrichment of the scraped data using local Ollama models.

### Class `GATCAPIScraper`

This class provides a direct API scraper for the Google Ad Transparency Center.

#### `__init__(self, cookies=None)`

-   **Purpose:** Initializes the scraper with optional authentication cookies.
-   **Args:**
    -   `cookies` (dict, optional): A dictionary of cookies from an authenticated session.

#### `search_creatives(self, advertiser_id, region='QA', batch_size=40)`

-   **Purpose:** Fetches ads using the `SearchCreatives` API.
-   **Args:**
    -   `advertiser_id` (str): The advertiser ID to search for.
    -   `region` (str, optional): The region code (e.g., 'QA', 'AE', 'US'). Defaults to 'QA'.
    -   `batch_size` (int, optional): The number of ads to fetch per request (max 40). Defaults to 40.
-   **Returns:** A list of ad dictionaries.

#### `scrape_advertiser(self, advertiser_id, region='QA', max_ads=400, enrich=False, save_to_db=False)`

-   **Purpose:** Scrapes all ads for an advertiser with optional AI enrichment.
-   **Args:**
    -   `advertiser_id` (str): The advertiser ID.
    -   `region` (str, optional): The region code. Defaults to 'QA'.
    -   `max_ads` (int, optional): The maximum number of ads to fetch. Defaults to 400.
    -   `enrich` (bool, optional): If `True`, analyzes ads with AI. Defaults to `False`.
    -   `save_to_db` (bool, optional): If `True`, saves the scraped data to the database. Defaults to `False`.
-   **Returns:** A list of ads (enriched if `enrich=True`).

#### `save_to_csv(self, ads, filename)`

-   **Purpose:** Saves a list of ads to a CSV file.
-   **Args:**
    -   `ads` (list): A list of ad dictionaries.
    -   `filename` (str): The name of the output CSV file.

### Functions

#### `parse_advertiser_url(url)`

-   **Purpose:** Extracts the advertiser ID and region from a GATC URL.
-   **Args:**
    -   `url` (str): The full GATC URL.
-   **Returns:** A tuple containing the advertiser ID and region, or `(None, None)` if parsing fails.

#### `parse_cookies_from_curl(curl_command)`

-   **Purpose:** Parses cookies from a cURL command.
-   **Args:**
    -   `curl_command` (str): The cURL command string.
-   **Returns:** A dictionary of cookies.

## `analyzers/hybrid.py`

This module provides a two-stage hybrid analyzer for speed optimization. It uses a combination of a vision model (`llava`) and a text model (`deepseek-r1`) to analyze ad creatives.

The analysis is performed in two stages:
1.  The vision model extracts text from the ad screenshot.
2.  The text model analyzes the extracted text to extract structured information.

This approach is significantly faster than using a single vision model for both text extraction and analysis.

### Class `HybridAnalyzer`

This class implements the `BaseAnalyzer` interface and provides a two-stage hybrid analyzer for ad creatives.

#### `__init__(self, api_endpoint="http://localhost:11434/api/chat")`

-   **Purpose:** Initializes the hybrid analyzer.
-   **Args:**
    -   `api_endpoint` (str, optional): The API endpoint for the Ollama server. Defaults to `http://localhost:11434/api/chat`.

#### `analyze_screenshot(self, screenshot: Screenshot) -> Analysis`

-   **Purpose:** Analyzes a screenshot in two stages: text extraction with a vision model and text analysis with a fast text model.
-   **Args:**
    -   `screenshot` (Screenshot): The screenshot to analyze.
-   **Returns:** An `Analysis` object containing the extracted information.

## `analyzers/aggregator.py`

This module provides a `CampaignAggregator` class that aggregates analysis results from multiple ad creatives to generate campaign-level insights. It can produce both structured JSON data and human-readable text reports.

### Class `CampaignAggregator`

This class is responsible for aggregating analysis results and generating campaign-level insights.

#### `__init__(self)`

-   **Purpose:** Initializes the campaign aggregator.

#### `add_analysis(self, analysis: Analysis, creative: Creative = None)`

-   **Purpose:** Adds an analysis result to the aggregator.
-   **Args:**
    -   `analysis` (Analysis): The analysis result to add.
    -   `creative` (Creative, optional): The creative associated with the analysis.

#### `generate_insights(self) -> Dict`

-   **Purpose:** Generates comprehensive insights from all analyzed ads.
-   **Returns:** A dictionary with campaign-level statistics, including offer distribution, category distribution, top keywords, and more.

#### `generate_text_report(self, advertiser_name: str = None) -> str`

-   **Purpose:** Generates a human-readable text report summarizing the campaign insights.
-   **Args:**
    -   `advertiser_name` (str, optional): The name of the advertiser.
-   **Returns:** A string containing the text report.

#### `export_to_json(self, output_path: str)`

-   **Purpose:** Exports the generated insights to a JSON file.
-   **Args:**
    -   `output_path` (str): The path to the output JSON file.

## `utils/browser.py`

Helper utilities for launching a Selenium Chrome WebDriver that mirrors the user's existing profile configuration.

### Function `get_browser()`

-   **Purpose:** Clones the configured Chrome profile (including cookies and extensions) into a temporary directory and returns a Selenium `webdriver.Chrome` wired for scraping.
-   **Returns:** A ready-to-use WebDriver instance; callers are responsible for quitting it after use.

## `extractors/gatc.py`

Implements a Selenium-based extractor that converts GATC creative links into local screenshots for analysis.

### Class `GATCIExtractor`

-   **Purpose:** Implements `BaseExtractor` by navigating to either the direct creative URL or the fallback GATC view, waiting for dynamic content/iframes, and saving a screenshot under `data/screenshots/`.
-   **Returns:** A `Screenshot` dataclass populated with the saved image path and a hash linking back to the creative.

## `extractors/base.py`

Defines the abstract interface for creative extractors.

### Class `BaseExtractor`

-   **Purpose:** Declares the `extract_creative(creative: Creative) -> Screenshot` contract that concrete extractors must implement.

## `models/ad_creative.py`

Dataclasses that represent the core entities flowing through the pipeline.

-   **`Creative`:** Captures advertiser metadata, creative URLs, formats, and timing information exported from GATC.
-   **`Screenshot`:** Links a captured image (and optional video) back to the creative via `creative_id`.
-   **`Analysis`:** Stores structured AI output, extending category/offer/messaging with extracted text, CTA, discount, keywords, brand name, and other enrichment fields.

## `analyzers/base.py`

Abstract base class for screenshot analyzers.

### Class `BaseAnalyzer`

-   **Purpose:** Establishes the `analyze_screenshot(screenshot: Screenshot) -> Analysis` interface implemented by Ollama, Claude, and Hybrid analyzers.

## `analyzers/ollama.py`

Vision + text analyzer that relies on a locally hosted Ollama server.

### Class `OllamaAnalyzer`

-   **Purpose:** Sends screenshot bytes to the `llava` vision model, coaxes JSON from the response, and maps it into an `Analysis` dataclass.
-   **Error Handling:** Detects HTTP/network/JSON issues and returns error-tagged `Analysis` objects to keep the pipeline resilient.
-   **Configuration:** Accepts a custom `api_endpoint` for non-default Ollama hosts.

## `analyzers/claude.py`

Anthropic Claude-based analyzer for vision-enabled enrichment.

### Class `ClaudeAnalyzer`

-   **Purpose:** Uploads screenshots to Claude 3.5 Sonnet, prompts for rich JSON output, and converts the response into an `Analysis`.
-   **Notables:** Requires `ANTHROPIC_API_KEY`, normalizes JSON whether or not Claude wraps it in Markdown fences, and falls back to error-labelled analyses if parsing fails.
-   **CLI Test Stub:** Running the module directly analyzes a hardcoded screenshot for smoke testing.

## `storage/base.py`

Placeholder describing the expected storage interface (`save_analysis`, `get_analysis`, `list_campaigns`) for future backends.

## `storage/csv_handler.py`

Utilities for loading exported GATC CSV data into structured objects.

### Function `read_input_csv(file_path: str) -> List[Creative]`

-   **Purpose:** Renames CSV columns to match the `Creative` dataclass, instantiates one object per row, and returns them for downstream extraction/analysis.

## `scrapers/gatc_scraper.py`

Selenium scraper that searches GATC, finds advertiser IDs, and exports creative metadata.

### Class `GATCScraper`

-   **Purpose:** Automates advertiser lookup, infinite-scroll loading, and creative harvesting using `utils.browser.get_browser()`.
-   **Key Methods:** `search_advertiser` (discovers advertiser IDs), `scrape_advertiser_ads` (collects creatives with minimal metadata), and `save_to_csv`.
-   **CLI Usage:** Provides an argparse `main()` to run `python scrapers/gatc_scraper.py --advertiser "Talabat" --region QA --max-ads 100`.

## `scrapers/advanced_scraper.py`

High-throughput Selenium scraper that aggressively scrolls and extracts creatives without needing the Chrome extension.

### Class `AdvancedGATCScraper`

-   **Purpose:** Launches a hardened Chrome session, fast-scrolls through ad grids, and parses each creative's text, images, and metadata.
-   **Key Methods:** `scroll_to_load_ads`, `extract_ad_data`, and `save_to_csv` manage dynamic content loading and structured export.
-   **CLI:** The `main()` entry point accepts URL, headless mode, max ads, and optional date filters; outputs CSV files under `data/input/`.

## `scrapers/extension_scraper.py`

Automates the Chrome "GATC Scraper" extension for users who already have the extension installed.

### Class `ExtensionScraper`

-   **Purpose:** Reuses an existing Chrome profile, programmatically opens the extension popup, sets the ad count, triggers scraping, and watches the download directory for CSV output.
-   **Fallbacks:** Includes manual-trigger helpers to recover when DOM automation fails.
-   **Inputs:** Requires `--chrome-profile` and `--download-dir`; leaves the browser open briefly so the user can inspect results.

## `scrapers/cdp_scraper.py`

Variant that leverages Chrome DevTools Protocol to control the GATC extension more directly.

### Class `CDPExtensionScraper`

-   **Purpose:** Launches Chrome with remote debugging enabled, discovers the extension ID, and operates the popup via CDP scripting.
-   **Workflow:** `start_browser` ➜ `get_extension_id` ➜ `trigger_extension` ➜ `wait_for_download`, returning the downloaded CSV path.

## `scrapers/simple_scraper.py`

Minimal helper that only opens the advertiser page and relies on the user to click the extension manually.

-   **Flow:** Launch Chrome with the nominated profile, navigate to the advertiser, print manual instructions, and poll the download directory until a new CSV appears.
-   **CLI:** Accepts URL, name, `max-ads`, and Chrome profile paths—ideal for quick manual runs.

## `scrapers/auto_scrape.py`

Scheduler-friendly orchestrator that runs multiple competitors from YAML configuration.

-   **Functions:** `load_config()` (reads `config/competitors.yaml`) and `scrape_all_competitors()` (loops competitors, invokes `GATCScraper`, and summarizes results).
-   **CLI Options:** `--run-now` executes immediately; `--schedule` prints cron instructions based on the config-defined cadence.

## `api/ai_analyzer.py`

High-level enrichment service that combines local Ollama text and vision models to categorize ads.

### Class `AdIntelligence`

-   **Purpose:** Provides `categorize_ad` and `batch_analyze` methods that fuse OCR, prompt-engineered analysis, and Qatar-specific heuristics (e.g., detecting subscription campaigns).
-   **Models:** Defaults to `llama3.1:8b` for text and `llava` for vision, with connectivity tests during initialization.
-   **Capabilities:** Generates product categories, offers, messaging themes, audience segments, and flags Qatar-only messaging; gracefully falls back when models are unreachable.

## `api/database.py`

SQLite-backed persistence layer for raw ads and AI enrichment.

### Class `AdDatabase`

-   **Purpose:** Manages schema creation, deduplicates creatives, tracks first/last seen timestamps, stores enrichment JSON, and exposes utilities for insights queries.
-   **Schema:** Tables for `ads`, `ad_enrichment`, and `scrape_runs`, with indexes and migration-safe columns such as `is_qatar_only`.
-   **Methods:** `save_ads` handles insert/update logic and enrichment storage while returning summary stats.

## `api/insights_engine.py`

Vision-first insights builder that turns CSV exports into narrative intelligence.

-   **`VisionAnalyzer`:** Downloads ad images, runs them through `llava`, and extracts visual themes, colors, and mood into structured JSON.
-   **`InsightsEngine`:** Aggregates CSV data, merges vision findings, counts weekly velocity, and prompts a text model to craft top insights (limited to the three most relevant recommendations).

## `api/strategic_analyst.py`

Generates personalized quick actions comparing "your" company vs competitors using database records.

### Class `StrategicAnalyst`

-   **Purpose:** Ingests data from `AdDatabase`, separates Snoonu vs competitors, and runs module-specific analyses (products, promos, messaging, velocity) before prompting DeepSeek/Llama for actions.
-   **Outputs:** Returns up to three actionable items tailored to the requested module with supporting metrics.

## `api/test_client.py`

Command-line helper to exercise the FastAPI endpoints end-to-end.

-   **Functions:** `scrape_competitor`, `wait_for_job`, `analyze_ads`, and `list_competitors` wrap HTTP calls to the API service.
-   **Interactive Mode:** Running the script presents a menu for scraping Talabat, analyzing existing CSVs, listing competitors, or completing the full scrape + analyze loop.

## `run_analysis.py`

End-to-end offline pipeline that turns a GATC CSV into enriched insights.

-   **Steps:** Reads creatives via `storage.csv_handler`, optionally extracts screenshots with `GATCIExtractor`, analyzes them with the selected analyzer, aggregates results, prints a text report, and writes JSON summaries.
-   **CLI Options:** Supports filtering by advertiser, limiting sample size, skipping extraction, and choosing the analyzer implementation.

## `easy_run.py`

Interactive TUI that wraps scraping and analysis into a single guided experience.

-   **Features:** Menus for scraping preset/custom competitors, running analyzers, reviewing existing CSVs/analyses, and performing full workflows.
-   **Integrations:** Calls `scrapers/extension_scraper.py` and `run_analysis.py` via subprocesses, handles Chrome profile management, and provides colorful status output.

## `debug_vision.py`

Utility script for inspecting the raw text produced by `AdIntelligence._extract_text_from_image()` to debug vision model accuracy on specific creatives.

## `utils/logger.py`

Placeholder describing the intent to standardize logging with rotation and environment-specific log levels.

## `main.py`

Stub comment noting that the repository's orchestrator should wire CSV ingestion, screenshot extraction, analysis, storage, and reporting.

## Validation Approach

We intentionally skipped documenting the unit test suite, but we still validate the production pipeline end to end:

- Run `easy_run.py` to exercise the scrape → analyze → report workflow with real inputs.
- Use `api/test_client.py` to hit the FastAPI endpoints, monitor async job progress, and sanity-check responses.
- Review `scrapers/auto_scrape.py` run summaries (ads scraped, output paths) to confirm scheduled jobs complete successfully.
- Inspect generated CSV/JSON artifacts and the `CampaignAggregator` text report for expected counts, offer splits, and category breakdowns after each run.
