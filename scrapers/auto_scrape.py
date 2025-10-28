#!/usr/bin/env python3
"""
Automated Competitor Ad Scraper
Runs on schedule to scrape competitor ads automatically.

Usage:
    python scrapers/auto_scrape.py --run-now
    python scrapers/auto_scrape.py --schedule
"""

import sys
import os
import argparse
import yaml
from datetime import datetime

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from scrapers.gatc_scraper import GATCScraper


def load_config():
    """Load competitor configuration from YAML file."""
    config_path = os.path.join(project_root, 'config', 'competitors.yaml')

    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def scrape_all_competitors(config):
    """Scrape ads for all enabled competitors."""
    print(f"\n{'='*80}")
    print(f"AUTOMATED COMPETITOR AD SCRAPING")
    print(f"{'='*80}\n")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    results = []

    for competitor in config['competitors']:
        if not competitor.get('enabled', True):
            print(f"⏭️  Skipping {competitor['name']} (disabled)")
            continue

        try:
            print(f"\n{'='*60}")
            print(f"Processing: {competitor['name']}")
            print(f"{'='*60}")

            scraper = GATCScraper(region=competitor['region'])

            # Find advertiser
            advertiser_id = scraper.search_advertiser(competitor['name'])

            if not advertiser_id:
                results.append({
                    'advertiser': competitor['name'],
                    'status': 'Failed',
                    'reason': 'Not found',
                    'ads_scraped': 0
                })
                continue

            # Scrape ads
            max_ads = config['scraping'].get('max_ads_per_competitor', 100)
            ads = scraper.scrape_advertiser_ads(advertiser_id, competitor['name'], max_ads=max_ads)

            # Save to CSV
            output_dir = os.path.join(project_root, config['output']['directory'])
            timestamp = datetime.now().strftime('%Y%m%d')
            filename = config['output']['filename_format'].format(
                advertiser=competitor['name'].replace(' ', '_'),
                date=timestamp
            )
            output_path = os.path.join(output_dir, filename)

            scraper.save_to_csv(ads, output_path)

            results.append({
                'advertiser': competitor['name'],
                'status': 'Success',
                'ads_scraped': len(ads),
                'output_file': output_path
            })

        except Exception as e:
            print(f"❌ Error processing {competitor['name']}: {e}")
            results.append({
                'advertiser': competitor['name'],
                'status': 'Failed',
                'reason': str(e),
                'ads_scraped': 0
            })

    # Print summary
    print(f"\n{'='*80}")
    print(f"SCRAPING SUMMARY")
    print(f"{'='*80}\n")

    total_ads = 0
    for result in results:
        status_icon = "✅" if result['status'] == 'Success' else "❌"
        ads_count = result.get('ads_scraped', 0)
        total_ads += ads_count

        print(f"{status_icon} {result['advertiser']}: {ads_count} ads scraped")

        if result['status'] == 'Failed':
            print(f"   Reason: {result.get('reason', 'Unknown')}")

    print(f"\n📊 Total ads scraped: {total_ads}")
    print(f"⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    return results


def main():
    parser = argparse.ArgumentParser(description='Automated competitor ad scraper')
    parser.add_argument('--run-now', action='store_true',
                       help='Run scraping immediately')
    parser.add_argument('--schedule', action='store_true',
                       help='Set up scheduled scraping (requires cron/Task Scheduler)')

    args = parser.parse_args()

    # Load configuration
    try:
        config = load_config()
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        return

    if args.run_now:
        # Run immediately
        scrape_all_competitors(config)

    elif args.schedule:
        # Show scheduling instructions
        schedule_config = config.get('schedule', {})
        frequency = schedule_config.get('frequency', 'daily')
        time_str = schedule_config.get('time', '02:00')

        print(f"\n📅 AUTOMATED SCHEDULING SETUP")
        print(f"{'='*60}\n")
        print(f"To run scraping {frequency} at {time_str}, add this to your crontab:\n")

        # Convert time to cron format
        hour, minute = time_str.split(':')

        if frequency == 'daily':
            cron_schedule = f"{minute} {hour} * * *"
        elif frequency == 'weekly':
            cron_schedule = f"{minute} {hour} * * 0"  # Sunday
        elif frequency == 'monthly':
            cron_schedule = f"{minute} {hour} 1 * *"  # 1st of month
        else:
            cron_schedule = f"{minute} {hour} * * *"  # Default daily

        script_path = os.path.abspath(__file__)
        cron_command = f"{cron_schedule} cd {project_root} && python {script_path} --run-now >> logs/scraper.log 2>&1"

        print(f"Cron entry:")
        print(f"{cron_command}\n")

        print(f"To add it, run:")
        print(f"  crontab -e")
        print(f"\nThen paste the line above and save.\n")

    else:
        print("Please specify --run-now or --schedule")
        parser.print_help()


if __name__ == '__main__':
    main()
