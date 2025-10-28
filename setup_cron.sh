#!/bin/bash
# Setup cron job to run scraper daily at 7pm
# For macOS/Linux

# Get absolute path to project directory
PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PYTHON_PATH=$(which python3)

echo "Setting up daily scraper..."
echo "Project directory: $PROJECT_DIR"
echo "Python path: $PYTHON_PATH"

# Create cron job (runs daily at 19:00 / 7pm)
# Logs output to scrape_cron.log
CRON_JOB="0 19 * * * cd $PROJECT_DIR && $PYTHON_PATH $PROJECT_DIR/scheduled_scraper.py >> $PROJECT_DIR/data/scrape_cron.log 2>&1"

# Check if cron job already exists
(crontab -l 2>/dev/null | grep -F "scheduled_scraper.py") && {
    echo "⚠️  Cron job already exists. Removing old one..."
    crontab -l | grep -v "scheduled_scraper.py" | crontab -
}

# Add new cron job
(crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -

echo "✅ Cron job installed!"
echo ""
echo "Schedule: Every day at 7:00 PM"
echo "Command: $CRON_JOB"
echo ""
echo "To view cron jobs: crontab -l"
echo "To remove cron job: crontab -e (then delete the line)"
echo "To view logs: cat data/scrape_cron.log"
echo ""
echo "To test now: python3 scheduled_scraper.py"
