#!/usr/bin/env python3
"""
Ad Intelligence Platform - Easy Interactive Runner
Just run: python easy_run.py
"""
import os
import sys
import subprocess
import glob
from datetime import datetime

# Colors
GREEN = '\033[0;32m'
BLUE = '\033[0;34m'
YELLOW = '\033[1;33m'
RED = '\033[0;31m'
BOLD = '\033[1m'
NC = '\033[0m'

# Configuration
CHROME_PROFILE = "/Users/muhannadsaad/Library/Application Support/Google/Chrome/Profile 1"
DOWNLOAD_DIR = "/Users/muhannadsaad/Desktop/ad-intelligence/data/input"
PROJECT_DIR = "/Users/muhannadsaad/Desktop/ad-intelligence"

# Competitor URLs
COMPETITORS = {
    "Talabat": "https://adstransparency.google.com/advertiser/AR14306592000630063105?region=QA",
    "Careem": "https://adstransparency.google.com/advertiser/AR01234567890123456789?region=QA",
    # "Deliveroo": "https://adstransparency.google.com/advertiser/AR98765432109876543210?region=QA"  # Disabled - no transparency center data
}

def clear_screen():
    os.system('clear' if os.name != 'nt' else 'cls')

def print_header():
    clear_screen()
    print(f"{BOLD}{BLUE}")
    print("=" * 70)
    print("           AD INTELLIGENCE PLATFORM")
    print("         Competitor Ad Analysis Made Easy")
    print("=" * 70)
    print(f"{NC}\n")

def check_chrome_running():
    """Check if Chrome is running"""
    try:
        result = subprocess.run(['pgrep', '-x', 'Google Chrome'],
                              capture_output=True, text=True)
        return result.returncode == 0
    except:
        return False

def close_chrome():
    """Try to close Chrome"""
    try:
        subprocess.run(['killall', 'Google Chrome'],
                      stderr=subprocess.DEVNULL)
        return True
    except:
        return False

def scrape_competitor(url, name, max_ads):
    """Run the scraper"""
    print(f"\n{GREEN}Starting scraper...{NC}\n")

    cmd = [
        'python', 'scrapers/extension_scraper.py',
        '--url', url,
        '--name', name,
        '--max-ads', str(max_ads),
        '--chrome-profile', CHROME_PROFILE,
        '--download-dir', DOWNLOAD_DIR
    ]

    result = subprocess.run(cmd, cwd=PROJECT_DIR)
    return result.returncode == 0

def analyze_file(csv_file, analyzer='hybrid'):
    """Run analysis"""
    print(f"\n{GREEN}Starting analysis with {analyzer} analyzer...{NC}")
    print(f"{YELLOW}This may take a while (45-90 sec per ad){NC}\n")

    cmd = [
        'python', 'run_analysis.py',
        '--input', csv_file,
        '--analyzer', analyzer
    ]

    result = subprocess.run(cmd, cwd=PROJECT_DIR)
    return result.returncode == 0

def list_csv_files():
    """List available CSV files"""
    pattern = os.path.join(DOWNLOAD_DIR, '*.csv')
    files = glob.glob(pattern)
    return sorted(files, key=os.path.getmtime, reverse=True)

def list_analyses():
    """List existing analyses"""
    output_dir = os.path.join(PROJECT_DIR, 'data', 'output')
    analyses = glob.glob(os.path.join(output_dir, 'analysis_*'))
    return sorted(analyses, key=os.path.getmtime, reverse=True)

def main_menu():
    """Show main menu and get choice"""
    print(f"{BOLD}What would you like to do?{NC}\n")
    print("  1) Scrape competitor ads")
    print("  2) Analyze scraped ads")
    print("  3) Full workflow (scrape + analyze)")
    print("  4) View existing analyses")
    print("  5) Exit\n")

    choice = input("Enter your choice (1-5): ").strip()
    return choice

def scrape_menu():
    """Scraping workflow"""
    print_header()
    print(f"{BOLD}{BLUE}=== SCRAPE COMPETITOR ADS ==={NC}\n")

    print("Select competitor:")
    competitors_list = list(COMPETITORS.keys())
    for i, comp in enumerate(competitors_list, 1):
        print(f"  {i}) {comp}")
    print(f"  {len(competitors_list)+1}) Custom URL\n")

    choice = input(f"Enter choice (1-{len(competitors_list)+1}): ").strip()

    if choice.isdigit() and 1 <= int(choice) <= len(competitors_list):
        competitor = competitors_list[int(choice)-1]
        url = COMPETITORS[competitor]
    elif choice == str(len(competitors_list)+1):
        competitor = input("Enter competitor name: ").strip()
        url = input("Enter advertiser URL: ").strip()
    else:
        print(f"{RED}Invalid choice{NC}")
        input("\nPress Enter to continue...")
        return

    max_ads = input("Number of ads to scrape (default 400): ").strip()
    max_ads = int(max_ads) if max_ads else 400

    print(f"\n{YELLOW}⚠️  Chrome must be closed to proceed{NC}")
    input("Press Enter when Chrome is closed...")

    if check_chrome_running():
        print(f"\n{YELLOW}Chrome is still running. Attempting to close...{NC}")
        close_chrome()
        import time
        time.sleep(2)

    success = scrape_competitor(url, competitor, max_ads)

    if success:
        print(f"\n{GREEN}✓ Scraping complete!{NC}")
    else:
        print(f"\n{RED}❌ Scraping failed{NC}")

    input("\nPress Enter to continue...")

def analyze_menu():
    """Analysis workflow"""
    print_header()
    print(f"{BOLD}{BLUE}=== ANALYZE SCRAPED ADS ==={NC}\n")

    files = list_csv_files()

    if not files:
        print(f"{RED}No CSV files found in {DOWNLOAD_DIR}{NC}")
        input("\nPress Enter to continue...")
        return

    print("Available CSV files:\n")
    for i, f in enumerate(files, 1):
        print(f"  {i}) {os.path.basename(f)}")

    choice = input(f"\nSelect file number (1-{len(files)}): ").strip()

    if not choice.isdigit() or not (1 <= int(choice) <= len(files)):
        print(f"{RED}Invalid choice{NC}")
        input("\nPress Enter to continue...")
        return

    selected_file = files[int(choice)-1]

    print("\nSelect analyzer:")
    print("  1) Hybrid (Recommended - Fast, Free)")
    print("  2) Ollama (Slower, More accurate)")
    print("  3) Claude (Fastest, Paid API)")

    analyzer_choice = input("\nEnter choice (1-3): ").strip()

    analyzers = {'1': 'hybrid', '2': 'ollama', '3': 'claude'}
    analyzer = analyzers.get(analyzer_choice, 'hybrid')

    success = analyze_file(selected_file, analyzer)

    if success:
        print(f"\n{GREEN}✓ Analysis complete!{NC}")
        print("\nResults saved to: data/output/analysis_*/")
    else:
        print(f"\n{RED}❌ Analysis failed{NC}")

    input("\nPress Enter to continue...")

def full_workflow_menu():
    """Full workflow"""
    print_header()
    print(f"{BOLD}{BLUE}=== FULL WORKFLOW (SCRAPE + ANALYZE) ==={NC}\n")

    # Choose competitor
    print("Select competitor:")
    competitors_list = list(COMPETITORS.keys())
    for i, comp in enumerate(competitors_list, 1):
        print(f"  {i}) {comp}")
    print(f"  {len(competitors_list)+1}) Custom URL\n")

    choice = input(f"Enter choice (1-{len(competitors_list)+1}): ").strip()

    if choice.isdigit() and 1 <= int(choice) <= len(competitors_list):
        competitor = competitors_list[int(choice)-1]
        url = COMPETITORS[competitor]
    elif choice == str(len(competitors_list)+1):
        competitor = input("Enter competitor name: ").strip()
        url = input("Enter advertiser URL: ").strip()
    else:
        print(f"{RED}Invalid choice{NC}")
        input("\nPress Enter to continue...")
        return

    max_ads = input("Number of ads to scrape (default 400): ").strip()
    max_ads = int(max_ads) if max_ads else 400

    # Choose analyzer
    print("\nSelect analyzer:")
    print("  1) Hybrid (Recommended - Fast, Free)")
    print("  2) Ollama (Slower, More accurate)")
    print("  3) Claude (Fastest, Paid API)")

    analyzer_choice = input("\nEnter choice (1-3): ").strip()
    analyzers = {'1': 'hybrid', '2': 'ollama', '3': 'claude'}
    analyzer = analyzers.get(analyzer_choice, 'hybrid')

    # STEP 1: Scrape
    print(f"\n{BOLD}{GREEN}STEP 1/2: SCRAPING{NC}")
    print(f"{YELLOW}⚠️  Chrome must be closed to proceed{NC}")
    input("Press Enter when Chrome is closed...")

    if check_chrome_running():
        print(f"\n{YELLOW}Chrome is still running. Attempting to close...{NC}")
        close_chrome()
        import time
        time.sleep(2)

    scrape_success = scrape_competitor(url, competitor, max_ads)

    if not scrape_success:
        print(f"\n{RED}❌ Scraping failed{NC}")
        input("\nPress Enter to continue...")
        return

    # Find most recent file
    files = list_csv_files()
    if not files:
        print(f"\n{RED}❌ No CSV file found{NC}")
        input("\nPress Enter to continue...")
        return

    latest_file = files[0]
    print(f"\n{GREEN}✓ Scraping complete: {os.path.basename(latest_file)}{NC}")

    # STEP 2: Analyze
    print(f"\n{BOLD}{GREEN}STEP 2/2: ANALYZING{NC}")

    analyze_success = analyze_file(latest_file, analyzer)

    if analyze_success:
        print(f"\n{BOLD}{GREEN}✓✓ COMPLETE! ✓✓{NC}")
        print("\nView your insights:")
        print("  cd data/output")
        print("  cat analysis_*/campaign_report.txt")
    else:
        print(f"\n{RED}❌ Analysis failed{NC}")

    input("\nPress Enter to continue...")

def view_analyses_menu():
    """View existing analyses"""
    print_header()
    print(f"{BOLD}{BLUE}=== EXISTING ANALYSES ==={NC}\n")

    analyses = list_analyses()

    if not analyses:
        print(f"{RED}No analyses found{NC}")
        input("\nPress Enter to continue...")
        return

    for i, analysis in enumerate(analyses, 1):
        print(f"  {i}) {os.path.basename(analysis)}")

    choice = input(f"\nSelect analysis to view (1-{len(analyses)}, or 0 to go back): ").strip()

    if choice == '0':
        return

    if not choice.isdigit() or not (1 <= int(choice) <= len(analyses)):
        print(f"{RED}Invalid choice{NC}")
        input("\nPress Enter to continue...")
        return

    selected = analyses[int(choice)-1]
    report_path = os.path.join(selected, 'campaign_report.txt')

    print_header()
    print(f"{BOLD}{BLUE}=== {os.path.basename(selected)} ==={NC}\n")

    if os.path.exists(report_path):
        with open(report_path, 'r') as f:
            print(f.read())
    else:
        print(f"{RED}Report not found{NC}")

    print(f"\nFiles in this analysis:")
    for f in os.listdir(selected):
        fpath = os.path.join(selected, f)
        size = os.path.getsize(fpath) / 1024  # KB
        print(f"  {f} ({size:.1f} KB)")

    input("\nPress Enter to continue...")

def main():
    """Main loop"""
    while True:
        print_header()
        choice = main_menu()

        if choice == '1':
            scrape_menu()
        elif choice == '2':
            analyze_menu()
        elif choice == '3':
            full_workflow_menu()
        elif choice == '4':
            view_analyses_menu()
        elif choice == '5':
            print(f"\n{GREEN}Thanks for using Ad Intelligence Platform!{NC}\n")
            sys.exit(0)
        else:
            print(f"{RED}Invalid choice. Please enter 1-5.{NC}")
            input("\nPress Enter to continue...")

if __name__ == '__main__':
    main()
