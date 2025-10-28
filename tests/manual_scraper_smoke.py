"""
Manual smoke test for the Google Ad Transparency scraper.

Usage (run outside the sandbox / with network access):
    python tests/manual_scraper_smoke.py

The script will:
    - Fetch up to 5 creatives for Talabat and Keeta in the QA region
    - Save CSV exports under data/input/scraper_testing/
    - Download creative images into scraper_testing_screenshots/<advertiser_id>/
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path
from typing import Iterable, Tuple, Dict, Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scrapers.api_scraper import GATCAPIScraper  # noqa: E402


ADVERTISERS: Iterable[Tuple[str, str]] = (
    ("Talabat", "AR14306592000630063105"),
    ("Keeta", "AR02245493152427278337"),
)

OUTPUT_ROOT = Path("data/input/scraper_testing")
SCREENSHOT_ROOT = Path("scraper_testing_screenshots")
CLEAN_SCREENSHOTS = True

# Raw cookie header captured from Chrome DevTools (replace with fresh values when expired)
COOKIE_HEADER = (
    " _ga=GA1.1.1815610471.1758093873; "
    "_ga_YMYR0M0J94=GS2.1.s1760381539$o17$g0$t1760381539$j60$l0$h0; "
    "SID=g.a0002QhfqfOIb5YPWN-bCf0pDa81HVgGj74yD3exOcgKbuoXgSinS8dJo99CSMkpnVtRgNQr5QACgYKAR4SARcSFQHGX2Mi4qPwEecSdTX5d94mIBJ2ihoVAUF8yKqMHA_zhisRg-aFIx7DLxmg0076; "
    "__Secure-1PSID=g.a0002QhfqfOIb5YPWN-bCf0pDa81HVgGj74yD3exOcgKbuoXgSinr2vaYNvsnxbjSd0J-FF4JQACgYKAZ0SARcSFQHGX2MinKkuzi0wLLGo0HdjkhriqRoVAUF8yKrH8cwcVAZknLL7ljTqGB6H0076; "
    "__Secure-3PSID=g.a0002QhfqfOIb5YPWN-bCf0pDa81HVgGj74yD3exOcgKbuoXgSinL99Rcr669N0PsnbOtJ2olwACgYKAUASARcSFQHGX2MiE6rBdDe0R2mYnY2IJ7L3qhoVAUF8yKpj-Dn5FZAB8qJT3SPDEcfD0076; "
    "HSID=AyWboUB3JRZBWpOaD; "
    "SSID=AfuM5WQqCgFvNRXq0; "
    "APISID=7J1h8eFXkN-qoYNv/ACvL8Yyoy9tjdk0s1; "
    "SAPISID=YWqxqMos97gQKc_n/A2Ot_alzS9jqwXccH; "
    "__Secure-1PAPISID=YWqxqMos97gQKc_n/A2Ot_alzS9jqwXccH; "
    "__Secure-3PAPISID=YWqxqMos97gQKc_n/A2Ot_alzS9jqwXccH; "
    "AEC=AaJma5sh07x27II_ZAvhebngTDSNEYtqOu8thCyNZLRII7R-208jxGiQofk; "
    "NID=525=kz6IhgTHyS4FKfNttuqTuyWyn08_VsbS08t1c1Fim9t-tVCVLyCyBH06sdQVCRFXW7W9i_hzHBDJcw4WT1bSfKOR3kcZRquUfovN_-2KjU5Fea7RbMYN0EfP1lfR51cQCokB3Fsfh9NzZiAoMyS1zF22Dm33RsAZPhh9UUPMvvieVWveDsU0Mjk6Fa_7xd6pvhEGCMoNsBnV2HPhw8_OzLnNByHq_B5jAIb66ZE8VXIheTxmw545uNHZqt3jPSRZ-MM6PQpqJcuXUGASiR6lUNOHCfgiw-GoRkbDd9Jymu8vSNkZyT1J36_hDTNDWK6NMD8bymp30OcvjmlKRgPmPRCiDa_NpW7i7A_jd49Z4XoZM-aWGv7kGzmzFLhGso2-jZGwT5zoeCIj7DoKQIe8AJxro7pvDpfXQCYQLyeYtARv8Ur2Ph9_h1-MQs70CCx40BLM0O2g0DXkIZ-hNIC-YFzzHM1OvVy8zkRKm2QvQeNm9gDfwr1InOb6dHWAoSN4vA0dzgza2mDZLMsruOdKROSEIW7hiG89Ya6RLoiroKrV3KL-E7z_kp8S7pz0M46YWifP1mRYbrs8mNLHFhBd3lv5afIYED1ITgj5H9DwSBz_oWkIzS7jbVojkLtjFqNeqYNHWCM06qDUXrZLD2LlY42Ms1zD2p7DGL-MhdEOth4ISoyg59XUk7R-c4GsTUfRAicsXDcQHxaVRVbfDgjBjbEzylMrAG23xtDdYLaN_T-3TF8rKrappgBfb3UIomgNX6wRDIZCIFN8SoORW0tmSF0ej8Dzt8Fur0ifmvtWRxRk2o_FUzXghXerSIuLnaeJWwUBgUMmRRu7r9F3OqxFkHXDvjes3TtQ5dZvwF7FiaFP-35_MiDr9gKuDTXuJjbbl5yyl02r21ZJT2OFVSBDef_FrC_gCdNdXVT0NogEoT5gmBEZvIpt-giPxz8sK6KC8ak2fNW6t79izxGhtjjTgnHFrBNM9O6PqRJ9mEydBn0MqZOAkdga570ZbEz-ioTx_D6yAtshjo_p8P71I7nvV8bbyfQc2ahxVIci8zUtlvvvZ-AfdEQsyaEIk2u0qSoPaOVQYvMZwERVR08dHTcRNXR0TLPhP1fK2_zbIPlFeqAsxnkZhWUoIQlSvmLegU2xQhJJr9a0VXPgli-XkEJ79pR6voue9PRdFsQjblpIfy4TnQaCrtK3vecv0fSmVTAm8HEDHxMp4x1h7wrlq7kyROgPNCducNvlnYgedIx_Kw8qcVfRdjgphco_SHH6DH_tGdeRGjAuK-rhbReTp0l91t5z4n26l32h4cLO63df-CTocYonK3VldxU_cTOFiZBski3h2FdwhK5SS8c51bmouOsTp6NPVo66692jkc1QMHaXUmtq9lIaOS_PhfdHedPvA0fsIkyeAZASooJDbjVJeN9DGgHJ5wIec9lG9mG9-6o739F9by7Gy9X3y-sy14MscNJ4FKJYBi6FqyeFAWoya-EsDUECJlvx-yRWRd4c5EOqMBxpIHbYkGiElqfB-IBZcUumq0E-ymsRWXY72MECXc3VbHg4CY3waXwL9yAOxe2SHfoHl3QJkKKNpZ9bmWhDOuBvkbM01ZT39kozkYME231lpHqV-RCRInsiOaqw_rlpfWqCsO2BaGo0bf1KFb3vXw; "
    "__Secure-1PSIDTS=sidts-CjEBmkD5S5RHs8AUj_yUiGX2FajnZCF6zovBy4N6D01y9udlcTOYK2K3b8at6VCQtAXeEAA; "
    "__Secure-3PSIDTS=sidts-CjEBmkD5S5RHs8AUj_yUiGX2FajnZCF6zovBy4N6D01y9udlcTOYK2K3b8at6VCQtAXeEAA; "
    "SIDCC=AKEyXzUt2NzBj7QHKmKOrzmVgLmC78821ISi7LsSYMTbKonsyNqSFWX53xPJaycA6izHrUzqGak; "
    "__Secure-1PSIDCC=AKEyXzWyE40-dirny9_N2p1R2eqAieVET-5EAvp12-yx8RTC9rh1DsP0c7d9PJyZnsC59U2muJY; "
    "__Secure-3PSIDCC=AKEyXzXrdT8OumokxMWR0btofPv2O7Z4TNJTy-7HO0Q9F_x0nfwpSspWodlicXn3h4MJKuJk_z8"
)


def download_images(scraper: GATCAPIScraper, ads: Iterable[Dict[str, Any]], advertiser_id: str) -> int:
    """Download image assets for the supplied ads into the screenshot directory."""
    adv_dir = SCREENSHOT_ROOT / advertiser_id
    adv_dir.mkdir(parents=True, exist_ok=True)

    downloaded = 0
    for ad in ads:
        image_url = ad.get("image_url")
        creative_id = ad.get("creative_id")
        if not image_url or not creative_id:
            continue

        target_path = adv_dir / f"{creative_id}.jpg"
        try:
            response = scraper.session.get(image_url, timeout=15)
            response.raise_for_status()
            target_path.write_bytes(response.content)
            downloaded += 1
        except Exception as exc:  # noqa: broad-except (manual test script)
            print(f"   ⚠️  Failed to download screenshot for {creative_id}: {exc}")

    return downloaded


def parse_cookie_header(header: str) -> Dict[str, str]:
    cookies: Dict[str, str] = {}
    for part in header.split(";"):
        part = part.strip()
        if not part:
            continue
        if "=" not in part:
            continue
        key, value = part.split("=", 1)
        cookies[key.strip()] = value.strip()
    return cookies


def run_smoke_test(max_ads: int = 5, region: str = "QA") -> None:
    print("\n==============================")
    print("SCRAPER SMOKE TEST (MANUAL)")
    print("==============================\n")

    cookies = parse_cookie_header(COOKIE_HEADER)
    scraper = GATCAPIScraper(cookies=cookies)
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    if CLEAN_SCREENSHOTS and SCREENSHOT_ROOT.exists():
        shutil.rmtree(SCREENSHOT_ROOT)
    SCREENSHOT_ROOT.mkdir(parents=True, exist_ok=True)

    for label, advertiser_id in ADVERTISERS:
        print(f"\n>>> {label} ({advertiser_id})")
        ads = scraper.scrape_advertiser(
            advertiser_id=advertiser_id,
            region=region,
            max_ads=max_ads,
            enrich=False,
            save_to_db=False,
        )

        if not ads:
            print("   ⚠️  No ads scraped.")
            continue

        csv_path = OUTPUT_ROOT / f"{label.lower()}_{region.lower()}.csv"
        scraper.save_to_csv(ads, str(csv_path))
        print(f"   💾 CSV saved: {csv_path}")

        downloaded = download_images(scraper, ads, advertiser_id)
        print(f"   📸 Screenshots downloaded: {downloaded}/{len(ads)}")


if __name__ == "__main__":
    try:
        run_smoke_test()
    except KeyboardInterrupt:
        sys.exit(1)
