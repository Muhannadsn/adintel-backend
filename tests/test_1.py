# test_models.py
import pandas as pd
from models.ad_creative import Creative, AdFormat

# Load your CSV
df = pd.read_csv('example_dataset.csv')

# Test with first row
row = df.iloc[0]
creative = Creative(
    advertiser=row['Advertiser'],
    creative=row['Creative'],
    format=row['Format'],
    region_filter=row['Region Filter'],
    campaign_duration=row['Campaign Duration'],
    first_seen=row['First Seen'],
    last_seen=row['Last Seen'],
    gatc_link=row['GATC Link'],
    row_index=0
)

print(f"Advertiser ID: {creative.advertiser_id}")
print(f"Creative ID: {creative.creative_id}")
print(f"Has URL: {creative.has_creative_url}")
print(f"Campaign Days: {creative.campaign_days}")
print(f"Format: {creative.format_enum}")