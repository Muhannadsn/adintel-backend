import sys
import os
import pandas as pd
from typing import List

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from models.ad_creative import Creative

def read_input_csv(file_path: str) -> List[Creative]:
    """
    Reads the input CSV file and returns a list of Creative objects.
    """
    df = pd.read_csv(file_path)

    # It's crucial to map the CSV column names to the dataclass field names.
    column_mapping = {
        'Advertiser': 'advertiser',
        'Creative': 'creative',
        'Format': 'format',
        'Region Filter': 'region_filter',
        'Campaign Duration': 'campaign_duration',
        'First Seen': 'first_seen',
        'Last Seen': 'last_seen',
        'GATC Link': 'gatc_link'
    }
    df = df.rename(columns=column_mapping)

    creatives = [Creative(**row) for index, row in df.iterrows()]
    return creatives

if __name__ == '__main__':
    # Example usage:
    input_file = '/Users/muhannadsaad/Desktop/ad-intelligence/data/input/gatc-scraped-data (1).csv'
    creatives_list = read_input_csv(input_file)
    if creatives_list:
        print(f"Successfully read {len(creatives_list)} creatives.")
        print("First creative:", creatives_list[0])
