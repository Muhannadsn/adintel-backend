#!/usr/bin/env python3
"""
Backup the current database before doing a fresh scrape
"""
import shutil
from datetime import datetime
from pathlib import Path

db_path = Path("data/adintel.db")
backup_dir = Path("data/backups")

# Create backups directory if it doesn't exist
backup_dir.mkdir(exist_ok=True)

# Create timestamped backup
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = backup_dir / f"adintel_backup_{timestamp}.db"

if db_path.exists():
    shutil.copy2(db_path, backup_path)
    print(f"✅ Database backed up to: {backup_path}")
    print(f"   Size: {backup_path.stat().st_size / (1024*1024):.2f} MB")
else:
    print(f"❌ Database not found at {db_path}")
    exit(1)
