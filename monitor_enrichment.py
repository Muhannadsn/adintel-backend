#!/usr/bin/env python3
"""
Real-time monitor for enrichment process
"""
import time
import subprocess

print("=" * 70)
print("ENRICHMENT PROGRESS MONITOR")
print("=" * 70)
print("\nMonitoring process_manual_csvs.py...\n")

try:
    while True:
        # Get process status
        result = subprocess.run(
            ["ps", "aux"],
            capture_output=True,
            text=True
        )

        if "process_manual_csvs.py" not in result.stdout:
            print("\n❌ Process not running!")
            break

        # Check database stats
        try:
            from api.database import AdDatabase
            db = AdDatabase()
            stats = db.get_stats()

            print(f"\r📊 Progress: {stats['total_ads']} total ads | Active: {stats['active_ads']} | Enriched: {stats.get('enriched_ads', 'N/A')}", end="", flush=True)

        except Exception as e:
            print(f"\r⏳ Processing... (database loading)", end="", flush=True)

        time.sleep(3)  # Update every 3 seconds

except KeyboardInterrupt:
    print("\n\n✅ Monitoring stopped")
    print("\nFinal stats:")
    from api.database import AdDatabase
    db = AdDatabase()
    print(db.get_stats())
