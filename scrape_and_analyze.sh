#!/bin/bash
# Ad Intelligence Platform - Interactive Menu
# Simple interface for scraping and analyzing competitor ads

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Configuration
CHROME_PROFILE="/Users/muhannadsaad/Library/Application Support/Google/Chrome/Profile 1"
DOWNLOAD_DIR="/Users/muhannadsaad/Desktop/ad-intelligence/data/input"
PROJECT_DIR="/Users/muhannadsaad/Desktop/ad-intelligence"

# Pre-defined competitor URLs
declare -A COMPETITOR_URLS
COMPETITOR_URLS["Talabat"]="https://adstransparency.google.com/advertiser/AR14306592000630063105?region=QA"
COMPETITOR_URLS["Careem"]="https://adstransparency.google.com/advertiser/AR01234567890123456789?region=QA"

clear

echo -e "${BOLD}${BLUE}"
echo "=================================================================="
echo "           AD INTELLIGENCE PLATFORM"
echo "         Competitor Ad Analysis Made Easy"
echo "=================================================================="
echo -e "${NC}"
echo ""

# Main Menu
while true; do
    echo -e "${BOLD}What would you like to do?${NC}"
    echo ""
    echo "  1) Scrape competitor ads (400 ads)"
    echo "  2) Analyze scraped ads"
    echo "  3) Full workflow (scrape + analyze)"
    echo "  4) View existing analyses"
    echo "  5) Exit"
    echo ""
    read -p "Enter your choice (1-5): " choice

    case $choice in
        1)
            # SCRAPE ONLY
            clear
            echo -e "${BOLD}${BLUE}=== SCRAPE COMPETITOR ADS ===${NC}"
            echo ""
            echo "Select competitor:"
            echo "  1) Talabat"
            echo "  2) Careem"
            echo "  3) Custom URL"
            echo ""
            read -p "Enter choice (1-3): " comp_choice

            case $comp_choice in
                1)
                    COMPETITOR="Talabat"
                    URL="${COMPETITOR_URLS[Talabat]}"
                    ;;
                2)
                    COMPETITOR="Careem"
                    URL="${COMPETITOR_URLS[Careem]}"
                    ;;
                3)
                    read -p "Enter competitor name: " COMPETITOR
                    read -p "Enter advertiser URL: " URL
                    ;;
                *)
                    echo -e "${RED}Invalid choice${NC}"
                    continue
                    ;;
            esac

            read -p "Number of ads to scrape (default 400): " MAX_ADS
            MAX_ADS=${MAX_ADS:-400}

            echo ""
            echo -e "${YELLOW}⚠️  Important: Chrome must be closed to proceed${NC}"
            echo ""
            read -p "Press Enter when Chrome is closed..." dummy

            # Check if Chrome is running
            if pgrep -x "Google Chrome" > /dev/null; then
                echo ""
                echo -e "${YELLOW}Chrome is still running. Attempting to close...${NC}"
                killall "Google Chrome" 2>/dev/null
                sleep 2
            fi

            echo ""
            echo -e "${GREEN}Starting scraper...${NC}"
            echo ""

            cd "$PROJECT_DIR"
            python scrapers/extension_scraper.py \
              --url "$URL" \
              --name "$COMPETITOR" \
              --max-ads "$MAX_ADS" \
              --chrome-profile "$CHROME_PROFILE" \
              --download-dir "$DOWNLOAD_DIR"

            echo ""
            read -p "Press Enter to continue..." dummy
            clear
            ;;

        2)
            # ANALYZE ONLY
            clear
            echo -e "${BOLD}${BLUE}=== ANALYZE SCRAPED ADS ===${NC}"
            echo ""
            echo "Available CSV files:"
            echo ""

            # List CSV files
            cd "$PROJECT_DIR/data/input"
            files=(*.csv)

            if [ ${#files[@]} -eq 0 ] || [ "${files[0]}" == "*.csv" ]; then
                echo -e "${RED}No CSV files found in data/input/${NC}"
                echo ""
                read -p "Press Enter to continue..." dummy
                clear
                continue
            fi

            for i in "${!files[@]}"; do
                echo "  $((i+1))) ${files[$i]}"
            done
            echo ""
            read -p "Select file number: " file_choice

            if [ "$file_choice" -lt 1 ] || [ "$file_choice" -gt "${#files[@]}" ]; then
                echo -e "${RED}Invalid choice${NC}"
                read -p "Press Enter to continue..." dummy
                clear
                continue
            fi

            SELECTED_FILE="${files[$((file_choice-1))]}"

            echo ""
            echo "Select analyzer:"
            echo "  1) Hybrid (Recommended - Fast, Free)"
            echo "  2) Ollama (Slower, More accurate)"
            echo "  3) Claude (Fastest, Paid API)"
            echo ""
            read -p "Enter choice (1-3): " analyzer_choice

            case $analyzer_choice in
                1) ANALYZER="hybrid" ;;
                2) ANALYZER="ollama" ;;
                3) ANALYZER="claude" ;;
                *)
                    echo -e "${RED}Invalid choice, using hybrid${NC}"
                    ANALYZER="hybrid"
                    ;;
            esac

            echo ""
            echo -e "${GREEN}Starting analysis with $ANALYZER analyzer...${NC}"
            echo -e "${YELLOW}This may take a while (45-90 sec per ad)${NC}"
            echo ""

            cd "$PROJECT_DIR"
            python run_analysis.py \
              --input "data/input/$SELECTED_FILE" \
              --analyzer "$ANALYZER"

            echo ""
            echo -e "${GREEN}✓ Analysis complete!${NC}"
            echo ""
            echo "Results saved to: data/output/analysis_*/"
            echo ""
            read -p "Press Enter to continue..." dummy
            clear
            ;;

        3)
            # FULL WORKFLOW
            clear
            echo -e "${BOLD}${BLUE}=== FULL WORKFLOW (SCRAPE + ANALYZE) ===${NC}"
            echo ""
            echo "Select competitor:"
            echo "  1) Talabat"
            echo "  2) Careem"
            echo "  3) Custom URL"
            echo ""
            read -p "Enter choice (1-3): " comp_choice

            case $comp_choice in
                1)
                    COMPETITOR="Talabat"
                    URL="${COMPETITOR_URLS[Talabat]}"
                    ;;
                2)
                    COMPETITOR="Careem"
                    URL="${COMPETITOR_URLS[Careem]}"
                    ;;
                3)
                    read -p "Enter competitor name: " COMPETITOR
                    read -p "Enter advertiser URL: " URL
                    ;;
                *)
                    echo -e "${RED}Invalid choice${NC}"
                    continue
                    ;;
            esac

            read -p "Number of ads to scrape (default 400): " MAX_ADS
            MAX_ADS=${MAX_ADS:-400}

            echo ""
            echo "Select analyzer:"
            echo "  1) Hybrid (Recommended - Fast, Free)"
            echo "  2) Ollama (Slower, More accurate)"
            echo "  3) Claude (Fastest, Paid API)"
            echo ""
            read -p "Enter choice (1-3): " analyzer_choice

            case $analyzer_choice in
                1) ANALYZER="hybrid" ;;
                2) ANALYZER="ollama" ;;
                3) ANALYZER="claude" ;;
                *)
                    echo -e "${RED}Invalid choice, using hybrid${NC}"
                    ANALYZER="hybrid"
                    ;;
            esac

            # STEP 1: SCRAPE
            echo ""
            echo -e "${BOLD}${GREEN}STEP 1/2: SCRAPING${NC}"
            echo -e "${YELLOW}⚠️  Chrome must be closed to proceed${NC}"
            echo ""
            read -p "Press Enter when Chrome is closed..." dummy

            if pgrep -x "Google Chrome" > /dev/null; then
                echo ""
                echo -e "${YELLOW}Chrome is still running. Attempting to close...${NC}"
                killall "Google Chrome" 2>/dev/null
                sleep 2
            fi

            echo ""
            echo -e "${GREEN}Starting scraper...${NC}"
            echo ""

            cd "$PROJECT_DIR"
            python scrapers/extension_scraper.py \
              --url "$URL" \
              --name "$COMPETITOR" \
              --max-ads "$MAX_ADS" \
              --chrome-profile "$CHROME_PROFILE" \
              --download-dir "$DOWNLOAD_DIR"

            # Find the most recent CSV file
            LATEST_FILE=$(ls -t "$DOWNLOAD_DIR"/*.csv 2>/dev/null | head -1)

            if [ -z "$LATEST_FILE" ]; then
                echo ""
                echo -e "${RED}❌ No CSV file found. Scraping may have failed.${NC}"
                read -p "Press Enter to continue..." dummy
                clear
                continue
            fi

            echo ""
            echo -e "${GREEN}✓ Scraping complete: $LATEST_FILE${NC}"
            echo ""

            # STEP 2: ANALYZE
            echo -e "${BOLD}${GREEN}STEP 2/2: ANALYZING${NC}"
            echo -e "${YELLOW}This may take a while (45-90 sec per ad)${NC}"
            echo ""

            python run_analysis.py \
              --input "$LATEST_FILE" \
              --analyzer "$ANALYZER"

            echo ""
            echo -e "${BOLD}${GREEN}✓✓ COMPLETE! ✓✓${NC}"
            echo ""
            echo "View your insights:"
            echo "  cd data/output"
            echo "  cat analysis_*/campaign_report.txt"
            echo ""
            read -p "Press Enter to continue..." dummy
            clear
            ;;

        4)
            # VIEW ANALYSES
            clear
            echo -e "${BOLD}${BLUE}=== EXISTING ANALYSES ===${NC}"
            echo ""

            cd "$PROJECT_DIR/data/output"
            analyses=(analysis_*)

            if [ ${#analyses[@]} -eq 0 ] || [ "${analyses[0]}" == "analysis_*" ]; then
                echo -e "${RED}No analyses found${NC}"
                echo ""
                read -p "Press Enter to continue..." dummy
                clear
                continue
            fi

            for i in "${!analyses[@]}"; do
                echo "  $((i+1))) ${analyses[$i]}"
            done
            echo ""
            read -p "Select analysis to view (or 0 to go back): " analysis_choice

            if [ "$analysis_choice" -eq 0 ]; then
                clear
                continue
            fi

            if [ "$analysis_choice" -lt 1 ] || [ "$analysis_choice" -gt "${#analyses[@]}" ]; then
                echo -e "${RED}Invalid choice${NC}"
                read -p "Press Enter to continue..." dummy
                clear
                continue
            fi

            SELECTED_ANALYSIS="${analyses[$((analysis_choice-1))]}"

            clear
            echo -e "${BOLD}${BLUE}=== $SELECTED_ANALYSIS ===${NC}"
            echo ""

            if [ -f "$SELECTED_ANALYSIS/campaign_report.txt" ]; then
                cat "$SELECTED_ANALYSIS/campaign_report.txt"
            else
                echo -e "${RED}Report not found${NC}"
            fi

            echo ""
            echo "Files in this analysis:"
            ls -lh "$SELECTED_ANALYSIS/" | tail -n +2
            echo ""
            read -p "Press Enter to continue..." dummy
            clear
            ;;

        5)
            # EXIT
            echo ""
            echo -e "${GREEN}Thanks for using Ad Intelligence Platform!${NC}"
            echo ""
            exit 0
            ;;

        *)
            echo -e "${RED}Invalid choice. Please enter 1-5.${NC}"
            echo ""
            ;;
    esac
done
