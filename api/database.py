#!/usr/bin/env python3
"""
Database Layer - Stores and retrieves ads with AI enrichment data
Supports both SQLite (local) and PostgreSQL (production)
"""

import sqlite3
import psycopg2
import psycopg2.extras
import json
import os
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from pathlib import Path


class AdDatabase:
    """
    Handles all database operations for ads + enrichment data

    Features:
    - Stores raw ad data + AI-extracted intelligence
    - Temporal tracking (first_seen, last_seen dates)
    - Efficient aggregations for insights endpoints
    - SQLite for zero-config setup
    """

    def __init__(self, db_path: str = None):
        """
        Initialize database connection

        Args:
            db_path: Path to SQLite database file (only used if DATABASE_URL not set)
                    Defaults to: data/adintel.db
        """
        # Check if DATABASE_URL is set (for Postgres)
        self.database_url = os.environ.get('DATABASE_URL')
        self.use_postgres = bool(self.database_url)

        if self.use_postgres:
            self.db_path = None
            print(f"✅ Database initialized: PostgreSQL")
        else:
            # Use SQLite for local development
            if db_path is None:
                project_root = Path(__file__).parent.parent
                data_dir = project_root / "data"
                data_dir.mkdir(exist_ok=True)
                db_path = str(data_dir / "adintel.db")

            self.db_path = db_path
            print(f"✅ Database initialized: SQLite at {self.db_path}")

        self._init_schema()

    def _get_connection(self):
        """Get database connection (Postgres or SQLite)"""
        if self.use_postgres:
            return psycopg2.connect(self.database_url)
        else:
            return sqlite3.connect(self.db_path)

    def _get_dict_cursor(self, conn):
        """Get a cursor that returns rows as dictionaries"""
        if self.use_postgres:
            return conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        else:
            conn.row_factory = sqlite3.Row
            return conn.cursor()

    def _param_placeholder(self):
        """Get parameter placeholder for SQL queries (? for SQLite, %s for Postgres)"""
        return '%s' if self.use_postgres else '?'

    def _true_val(self):
        """Get TRUE value for SQL queries"""
        return 'TRUE' if self.use_postgres else '1'

    def _false_val(self):
        """Get FALSE value for SQL queries"""
        return 'FALSE' if self.use_postgres else '0'

    def _init_schema(self):
        """Create database tables if they don't exist"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()

            # SQL syntax differs between SQLite and Postgres
            if self.use_postgres:
                id_type = "SERIAL PRIMARY KEY"
                bool_default = "DEFAULT TRUE"
                timestamp_default = "DEFAULT CURRENT_TIMESTAMP"
            else:
                id_type = "INTEGER PRIMARY KEY AUTOINCREMENT"
                bool_default = "DEFAULT 1"
                timestamp_default = "DEFAULT CURRENT_TIMESTAMP"

            # Table 1: Raw ads
            cursor.execute(f'''
                CREATE TABLE IF NOT EXISTS ads (
                    id {id_type},
                    advertiser_id TEXT NOT NULL,
                    ad_text TEXT,
                    image_url TEXT,
                    html_content TEXT,
                    regions TEXT,
                    first_seen_date TIMESTAMP {timestamp_default},
                    last_seen_date TIMESTAMP,
                    is_active BOOLEAN {bool_default},
                    created_at TIMESTAMP {timestamp_default},
                    UNIQUE(advertiser_id, ad_text, image_url)
                )
            ''')

            # Table 2: AI enrichment data
            cursor.execute(f'''
                CREATE TABLE IF NOT EXISTS ad_enrichment (
                    ad_id INTEGER PRIMARY KEY,
                    product_category TEXT,
                    product_name TEXT,
                    messaging_themes TEXT,
                    primary_theme TEXT,
                    audience_segment TEXT,
                    offer_type TEXT,
                    offer_details TEXT,
                    confidence_score REAL,
                    analysis_model TEXT,
                    analyzed_at TIMESTAMP {timestamp_default},
                    FOREIGN KEY (ad_id) REFERENCES ads(id) ON DELETE CASCADE
                )
            ''')

            # Migration-safe: Add new columns if they don't exist
            # Get existing columns (different syntax for SQLite vs Postgres)
            if self.use_postgres:
                cursor.execute("""
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_name = 'ad_enrichment'
                """)
                columns = [col[0] for col in cursor.fetchall()]
            else:
                cursor.execute("PRAGMA table_info(ad_enrichment)")
                columns = [col[1] for col in cursor.fetchall()]

            # Add is_qatar_only (region validation)
            if 'is_qatar_only' not in columns:
                if self.use_postgres:
                    cursor.execute('ALTER TABLE ad_enrichment ADD COLUMN is_qatar_only BOOLEAN DEFAULT TRUE')
                else:
                    cursor.execute('ALTER TABLE ad_enrichment ADD COLUMN is_qatar_only BOOLEAN DEFAULT 1')
                print("  📍 Added is_qatar_only column")

            # Add orchestrator-specific fields
            if 'brand' not in columns:
                cursor.execute('ALTER TABLE ad_enrichment ADD COLUMN brand TEXT')
                print("  🏷️  Added brand column")

            if 'food_category' not in columns:
                cursor.execute('ALTER TABLE ad_enrichment ADD COLUMN food_category TEXT')
                print("  🍔 Added food_category column")

            if 'rejected_wrong_region' not in columns:
                if self.use_postgres:
                    cursor.execute('ALTER TABLE ad_enrichment ADD COLUMN rejected_wrong_region BOOLEAN DEFAULT FALSE')
                else:
                    cursor.execute('ALTER TABLE ad_enrichment ADD COLUMN rejected_wrong_region BOOLEAN DEFAULT 0')
                print("  🚫 Added rejected_wrong_region column")

            if 'detected_region' not in columns:
                cursor.execute('ALTER TABLE ad_enrichment ADD COLUMN detected_region TEXT')
                print("  🌍 Added detected_region column")

            # RAG-ready: Add embedding vector field for future semantic search
            if 'embedding_vector' not in columns:
                cursor.execute('ALTER TABLE ad_enrichment ADD COLUMN embedding_vector TEXT')
                print("  🧠 Added embedding_vector column (RAG-ready)")

            # Table 3: Scrape runs (for tracking)
            cursor.execute(f'''
                CREATE TABLE IF NOT EXISTS scrape_runs (
                    id {id_type},
                    advertiser_id TEXT NOT NULL,
                    run_date TIMESTAMP {timestamp_default},
                    ads_found INTEGER,
                    ads_new INTEGER,
                    ads_retired INTEGER,
                    enrichment_enabled BOOLEAN DEFAULT {'FALSE' if self.use_postgres else '0'}
                )
            ''')

            # Table 4: Product Knowledge Base (for caching product lookups)
            cursor.execute(f'''
                CREATE TABLE IF NOT EXISTS product_knowledge (
                    id {id_type},
                    product_name TEXT UNIQUE NOT NULL,
                    product_type TEXT NOT NULL,
                    category TEXT,
                    is_restaurant BOOLEAN,
                    is_unknown_category BOOLEAN,
                    is_subscription BOOLEAN,
                    metadata TEXT,
                    confidence REAL DEFAULT 0.0,
                    verified_date TIMESTAMP {timestamp_default},
                    search_source TEXT,
                    created_at TIMESTAMP {timestamp_default}
                )
            ''')

            # Create indexes for faster queries
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_advertiser ON ads(advertiser_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_active ON ads(is_active)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_first_seen ON ads(first_seen_date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_product_cat ON ad_enrichment(product_category)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_primary_theme ON ad_enrichment(primary_theme)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_product_name ON product_knowledge(product_name)')

            conn.commit()
        finally:
            conn.close()

    def save_ads(self, ads: List[Dict], advertiser_id: str = None) -> Dict:
        """
        Save or update ads with enrichment data
        Handles temporal tracking (new vs existing ads)

        Args:
            ads: List of ad dicts with enrichment fields
            advertiser_id: Optional advertiser ID (will extract from ads if not provided)

        Returns:
            Dict with stats: {ads_new, ads_updated, ads_total}
        """
        stats = {
            'ads_new': 0,
            'ads_updated': 0,
            'ads_total': len(ads)
        }

        with self._get_connection() as conn:
            cursor = conn.cursor()

            for ad in ads:
                adv_id = advertiser_id or ad.get('advertiser_id')
                if not adv_id:
                    print(f"⚠️  Skipping ad without advertiser_id")
                    continue

                # Check if ad already exists
                ph = self._param_placeholder()
                cursor.execute(f'''
                    SELECT id, first_seen_date FROM ads
                    WHERE advertiser_id = {ph} AND ad_text = {ph} AND image_url = {ph}
                ''', (adv_id, ad.get('ad_text', ''), ad.get('image_url', '')))

                existing = cursor.fetchone()

                if existing:
                    # Update existing ad
                    ad_id, first_seen = existing
                    cursor.execute(f'''
                        UPDATE ads
                        SET last_seen_date = CURRENT_TIMESTAMP,
                            is_active = {'TRUE' if self.use_postgres else '1'}
                        WHERE id = {ph}
                    ''', (ad_id,))
                    stats['ads_updated'] += 1
                else:
                    # Insert new ad
                    cursor.execute(f'''
                        INSERT INTO ads (advertiser_id, ad_text, image_url, html_content, regions)
                        VALUES ({ph}, {ph}, {ph}, {ph}, {ph})
                    ''', (
                        adv_id,
                        ad.get('ad_text', ''),
                        ad.get('image_url', ''),
                        ad.get('html_content', ''),
                        ad.get('regions', '')
                    ))
                    if self.use_postgres:
                        cursor.execute('SELECT lastval()')
                        ad_id = cursor.fetchone()[0]
                    else:
                        ad_id = cursor.lastrowid
                    stats['ads_new'] += 1

                # Save enrichment data if present
                if 'product_category' in ad or 'brand' in ad:
                    # Convert messaging_themes dict to JSON string
                    themes_json = json.dumps(ad.get('messaging_themes', {}))

                    # Use ON CONFLICT for Postgres, INSERT OR REPLACE for SQLite
                    if self.use_postgres:
                        cursor.execute(f'''
                            INSERT INTO ad_enrichment
                            (ad_id, product_category, product_name, messaging_themes,
                             primary_theme, audience_segment, offer_type, offer_details,
                             confidence_score, analysis_model, is_qatar_only,
                             brand, food_category, detected_region, rejected_wrong_region)
                            VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph})
                            ON CONFLICT (ad_id) DO UPDATE SET
                                product_category = EXCLUDED.product_category,
                                product_name = EXCLUDED.product_name,
                                messaging_themes = EXCLUDED.messaging_themes,
                                primary_theme = EXCLUDED.primary_theme,
                                audience_segment = EXCLUDED.audience_segment,
                                offer_type = EXCLUDED.offer_type,
                                offer_details = EXCLUDED.offer_details,
                                confidence_score = EXCLUDED.confidence_score,
                                analysis_model = EXCLUDED.analysis_model,
                                is_qatar_only = EXCLUDED.is_qatar_only,
                                brand = EXCLUDED.brand,
                                food_category = EXCLUDED.food_category,
                                detected_region = EXCLUDED.detected_region,
                                rejected_wrong_region = EXCLUDED.rejected_wrong_region
                        ''', (
                            ad_id,
                            ad.get('product_category'),
                            ad.get('product_name'),
                            themes_json,
                            ad.get('primary_theme'),
                            ad.get('audience_segment'),
                            ad.get('offer_type'),
                            ad.get('offer_details'),
                            ad.get('confidence_score'),
                            ad.get('analysis_model', 'orchestrator'),
                            ad.get('is_qatar_only', True),  # Default to True (Qatar)
                            ad.get('brand'),  # Vision-extracted brand
                            ad.get('food_category'),  # Vision-extracted food category
                            ad.get('detected_region'),  # Region validator result
                            ad.get('rejected_wrong_region', False)  # Region filter flag
                        ))
                    else:
                        cursor.execute(f'''
                            INSERT OR REPLACE INTO ad_enrichment
                            (ad_id, product_category, product_name, messaging_themes,
                             primary_theme, audience_segment, offer_type, offer_details,
                             confidence_score, analysis_model, is_qatar_only,
                             brand, food_category, detected_region, rejected_wrong_region)
                            VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph})
                        ''', (
                            ad_id,
                            ad.get('product_category'),
                            ad.get('product_name'),
                            themes_json,
                            ad.get('primary_theme'),
                            ad.get('audience_segment'),
                            ad.get('offer_type'),
                            ad.get('offer_details'),
                            ad.get('confidence_score'),
                            ad.get('analysis_model', 'orchestrator'),
                            ad.get('is_qatar_only', True),  # Default to True (Qatar)
                            ad.get('brand'),  # Vision-extracted brand
                            ad.get('food_category'),  # Vision-extracted food category
                            ad.get('detected_region'),  # Region validator result
                            ad.get('rejected_wrong_region', False)  # Region filter flag
                        ))

            conn.commit()

        print(f"📊 Saved {stats['ads_new']} new ads, updated {stats['ads_updated']} existing ads")
        return stats

    def get_all_ads(self, active_only: bool = True) -> List[Dict]:
        """
        Retrieve ALL ads across all competitors with enrichment data

        Args:
            active_only: If True, only return active ads

        Returns:
            List of ad dicts with enrichment fields
        """
        conn = self._get_connection()
        cursor = self._get_dict_cursor(conn)  # Use database-agnostic dict cursor

        false_val = 'FALSE' if self.use_postgres else '0'
        true_val = 'TRUE' if self.use_postgres else '1'

        query = f'''
            SELECT
                a.*,
                e.product_category,
                e.product_name,
                e.messaging_themes,
                e.primary_theme,
                e.audience_segment,
                e.offer_type,
                e.offer_details,
                e.confidence_score,
                e.brand,
                e.food_category,
                e.detected_region,
                e.rejected_wrong_region
            FROM ads a
            LEFT JOIN ad_enrichment e ON a.id = e.ad_id
        '''

        if active_only:
            query += f' WHERE a.is_active = {true_val} AND (e.rejected_wrong_region = {false_val} OR e.rejected_wrong_region IS NULL)'
        else:
            query += f' WHERE (e.rejected_wrong_region = {false_val} OR e.rejected_wrong_region IS NULL)'

        cursor.execute(query)
        rows = cursor.fetchall()

        ads = []
        for row in rows:
            ad = dict(row)
            # Parse JSON messaging_themes back to dict
            if ad.get('messaging_themes'):
                ad['messaging_themes'] = json.loads(ad['messaging_themes'])
            ads.append(ad)

        conn.close()
        return ads

    def get_ads_by_competitor(self, advertiser_id: str, active_only: bool = True) -> List[Dict]:
        """
        Retrieve all ads for a competitor with enrichment data

        Args:
            advertiser_id: Competitor's advertiser ID
            active_only: If True, only return active ads

        Returns:
            List of ad dicts with enrichment fields
        """
        conn = self._get_connection()
        cursor = self._get_dict_cursor(conn)  # Get cursor that returns dicts

        ph = self._param_placeholder()
        false_val = 'FALSE' if self.use_postgres else '0'
        true_val = 'TRUE' if self.use_postgres else '1'

        query = f'''
            SELECT
                a.*,
                e.product_category,
                e.product_name,
                e.messaging_themes,
                e.primary_theme,
                e.audience_segment,
                e.offer_type,
                e.offer_details,
                e.confidence_score,
                e.brand,
                e.food_category,
                e.detected_region,
                e.rejected_wrong_region
            FROM ads a
            LEFT JOIN ad_enrichment e ON a.id = e.ad_id
            WHERE a.advertiser_id = {ph}
              AND (e.rejected_wrong_region = {false_val} OR e.rejected_wrong_region IS NULL)
        '''

        if active_only:
            query += f' AND a.is_active = {true_val}'
        cursor.execute(query, (advertiser_id,))
        rows = cursor.fetchall()

        ads = []
        for row in rows:
            ad = dict(row)
            # Parse JSON messaging_themes back to dict
            if ad.get('messaging_themes'):
                ad['messaging_themes'] = json.loads(ad['messaging_themes'])
            ads.append(ad)

        conn.close()
        return ads

    def get_products_by_competitor(self, advertiser_id: str = None) -> List[Dict]:
        """
        Aggregate ads by product category
        Used by: /api/insights/products endpoint

        Args:
            advertiser_id: Optional - filter to specific competitor

        Returns:
            List of product insights:
            [
                {
                    "competitor": "Talabat",
                    "category": "Meal Deals",
                    "ad_count": 180,
                    "unique_creatives": 45,
                    "days_active": 14
                },
                ...
            ]
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            ph = self._param_placeholder()
            false_val = 'FALSE' if self.use_postgres else '0'
            true_val = 'TRUE' if self.use_postgres else '1'

            # Days active calculation differs between SQLite and Postgres
            if self.use_postgres:
                days_calc = "CAST(EXTRACT(DAY FROM (CURRENT_TIMESTAMP - MIN(a.first_seen_date))) AS INTEGER)"
            else:
                days_calc = "CAST(julianday('now') - julianday(MIN(a.first_seen_date)) AS INTEGER)"

            query = f'''
                SELECT
                    a.advertiser_id,
                    e.product_category,
                    COUNT(DISTINCT a.id) as ad_count,
                    COUNT(DISTINCT a.image_url) as unique_creatives,
                    {days_calc} as days_active
                FROM ads a
                JOIN ad_enrichment e ON a.id = e.ad_id
                WHERE a.is_active = {true_val}
                  AND (e.rejected_wrong_region = {false_val} OR e.rejected_wrong_region IS NULL)
            '''

            if advertiser_id:
                query += f' AND a.advertiser_id = {ph}'
                cursor.execute(query + ' GROUP BY a.advertiser_id, e.product_category', (advertiser_id,))
            else:
                cursor.execute(query + ' GROUP BY a.advertiser_id, e.product_category')

            rows = cursor.fetchall()

            products = []
            for row in rows:
                products.append({
                    'advertiser_id': row[0],
                    'category': row[1],
                    'ad_count': row[2],
                    'unique_creatives': row[3],
                    'days_active': max(row[4], 1)  # At least 1 day
                })

            return products

    def get_messaging_breakdown(self, time_range: str = "all") -> Dict:
        """
        Calculate messaging theme distribution per competitor
        Used by: /api/insights/messaging endpoint

        Args:
            time_range: "week", "month", "quarter", or "all"

        Returns:
            Dict mapping advertiser_id to theme percentages:
            {
                "AR123": {"price": 45, "speed": 25, "quality": 15, "convenience": 15},
                ...
            }
        """
        # Calculate date filter
        date_filter = ""
        if time_range == "week":
            date_filter = "AND a.first_seen_date >= date('now', '-7 days')"
        elif time_range == "month":
            date_filter = "AND a.first_seen_date >= date('now', '-30 days')"
        elif time_range == "quarter":
            date_filter = "AND a.first_seen_date >= date('now', '-90 days')"

        with self._get_connection() as conn:
            cursor = conn.cursor()

            true_val = self._true_val()
            false_val = self._false_val()

            query = f'''
                SELECT
                    a.advertiser_id,
                    e.primary_theme,
                    COUNT(*) as count
                FROM ads a
                JOIN ad_enrichment e ON a.id = e.ad_id
                WHERE a.is_active = {true_val}
                  AND (e.rejected_wrong_region = {false_val} OR e.rejected_wrong_region IS NULL)
                  {date_filter}
                GROUP BY a.advertiser_id, e.primary_theme
            '''

            cursor.execute(query)
            rows = cursor.fetchall()

            # Aggregate by competitor
            breakdown = {}
            totals = {}

            for row in rows:
                adv_id, theme, count = row
                if adv_id not in breakdown:
                    breakdown[adv_id] = {'price': 0, 'speed': 0, 'quality': 0, 'convenience': 0}
                    totals[adv_id] = 0

                breakdown[adv_id][theme] = count
                totals[adv_id] += count

            # Convert to percentages
            for adv_id in breakdown:
                total = totals[adv_id]
                for theme in breakdown[adv_id]:
                    breakdown[adv_id][theme] = int((breakdown[adv_id][theme] / total) * 100) if total > 0 else 0

            return breakdown

    def get_daily_velocity(self, days: int = 30) -> List[Dict]:
        """
        Get daily new ad counts for velocity tracking
        Used by: /api/insights/velocity endpoint

        Args:
            days: Number of days to look back

        Returns:
            List of daily stats:
            [
                {
                    "date": "2025-10-17",
                    "total_new_ads": 12,
                    "by_competitor": {"AR123": 8, "AR456": 4}
                },
                ...
            ]
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            ph = self._param_placeholder()

            # Date arithmetic differs between SQLite and Postgres
            if self.use_postgres:
                date_filter = f"first_seen_date >= CURRENT_DATE - INTERVAL '{ph} days'"
                query = f'''
                    SELECT
                        DATE(first_seen_date) as ad_date,
                        advertiser_id,
                        COUNT(*) as count
                    FROM ads
                    WHERE {date_filter}
                    GROUP BY DATE(first_seen_date), advertiser_id
                    ORDER BY ad_date DESC
                '''
                cursor.execute(query.replace(ph, '%s'), (days,))
            else:
                query = f'''
                    SELECT
                        DATE(first_seen_date) as ad_date,
                        advertiser_id,
                        COUNT(*) as count
                    FROM ads
                    WHERE first_seen_date >= date('now', {ph} || ' days')
                    GROUP BY DATE(first_seen_date), advertiser_id
                    ORDER BY ad_date DESC
                '''
                cursor.execute(query, (-days,))
            rows = cursor.fetchall()

            # Group by date
            daily_data = {}
            for row in rows:
                date, adv_id, count = row
                if date not in daily_data:
                    daily_data[date] = {'total_new_ads': 0, 'by_competitor': {}}

                daily_data[date]['by_competitor'][adv_id] = count
                daily_data[date]['total_new_ads'] += count

            # Convert to list
            timeline = [
                {'date': date, **stats}
                for date, stats in sorted(daily_data.items(), reverse=True)
            ]

            return timeline

    def get_audience_breakdown(self) -> List[Dict]:
        """
        Get audience segment targeting breakdown across competitors
        Used by: /api/insights/audiences endpoint

        Returns:
            List of audience insights:
            [
                {
                    "segment": "New Customers",
                    "competitors": ["Talabat", "Deliveroo"],
                    "total_ads": 150,
                    "percentage": 35.2
                },
                ...
            ]
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            true_val = self._true_val()
            false_val = self._false_val()

            query = f'''
                SELECT
                    e.audience_segment,
                    a.advertiser_id,
                    COUNT(*) as ad_count
                FROM ads a
                JOIN ad_enrichment e ON a.id = e.ad_id
                WHERE a.is_active = {true_val}
                  AND e.audience_segment IS NOT NULL
                  AND (e.rejected_wrong_region = {false_val} OR e.rejected_wrong_region IS NULL)
                GROUP BY e.audience_segment, a.advertiser_id
                ORDER BY ad_count DESC
            '''

            cursor.execute(query)
            rows = cursor.fetchall()

            # Aggregate by segment
            segment_data = {}
            total_ads = 0

            for row in rows:
                segment, adv_id, count = row
                if segment not in segment_data:
                    segment_data[segment] = {
                        'total_ads': 0,
                        'competitors': []
                    }

                segment_data[segment]['total_ads'] += count
                segment_data[segment]['competitors'].append(adv_id)
                total_ads += count

            # Convert to list with percentages
            audience_list = []
            for segment, data in segment_data.items():
                percentage = round((data['total_ads'] / total_ads * 100), 1) if total_ads > 0 else 0
                audience_list.append({
                    'segment': segment,
                    'competitors': data['competitors'],
                    'total_ads': data['total_ads'],
                    'percentage': percentage
                })

            # Sort by total_ads descending
            audience_list.sort(key=lambda x: x['total_ads'], reverse=True)

            return audience_list

    def get_promo_timeline(self, days: int = 30) -> List[Dict]:
        """
        Get promo/offer activity over time
        Used by: /api/insights/promos endpoint

        Args:
            days: Number of days to look back

        Returns:
            List of daily promo stats with breakdown by offer type
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            ph = self._param_placeholder()

            # Date arithmetic differs between SQLite and Postgres
            if self.use_postgres:
                query = f'''
                    SELECT
                        DATE(a.first_seen_date) as promo_date,
                        e.offer_type,
                        COUNT(*) as count
                    FROM ads a
                    JOIN ad_enrichment e ON a.id = e.ad_id
                    WHERE a.first_seen_date >= CURRENT_DATE - INTERVAL '{days} days'
                      AND e.offer_type IS NOT NULL
                      AND e.offer_type != 'none'
                    GROUP BY DATE(a.first_seen_date), e.offer_type
                    ORDER BY promo_date DESC
                '''
                cursor.execute(query)
            else:
                query = f'''
                    SELECT
                        DATE(a.first_seen_date) as promo_date,
                        e.offer_type,
                        COUNT(*) as count
                    FROM ads a
                    JOIN ad_enrichment e ON a.id = e.ad_id
                    WHERE a.first_seen_date >= date('now', {ph} || ' days')
                      AND e.offer_type IS NOT NULL
                      AND e.offer_type != 'none'
                    GROUP BY DATE(a.first_seen_date), e.offer_type
                    ORDER BY promo_date DESC
                '''
                cursor.execute(query, (-days,))
            rows = cursor.fetchall()

            # Group by date
            daily_data = {}
            for row in rows:
                date, offer_type, count = row
                if date not in daily_data:
                    daily_data[date] = {
                        'total_promos': 0,
                        'by_offer_type': {}
                    }

                daily_data[date]['by_offer_type'][offer_type] = count
                daily_data[date]['total_promos'] += count

            # Convert to list
            timeline = [
                {'date': date, **stats}
                for date, stats in sorted(daily_data.items(), reverse=True)
            ]

            return timeline

    def get_offers_breakdown(self) -> List[Dict]:
        """
        Get active offers breakdown with % distribution
        Simple summary for marketing teams to scan quickly

        Returns:
            List of offer insights:
            [
                {
                    "offer_type": "percentage_discount",
                    "label": "% Off Discounts",
                    "ad_count": 45,
                    "percentage": 42.3,
                    "competitors": ["Talabat", "Deliveroo"],
                    "sample_offers": ["50% off", "30% off orders"]
                },
                ...
            ]
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            true_val = self._true_val()
            false_val = self._false_val()

            query = f'''
                SELECT
                    e.offer_type,
                    e.offer_details,
                    a.advertiser_id,
                    COUNT(*) as ad_count
                FROM ads a
                JOIN ad_enrichment e ON a.id = e.ad_id
                WHERE a.is_active = {true_val}
                  AND e.offer_type IS NOT NULL
                  AND e.offer_type != 'none'
                  AND e.offer_type != ''
                  AND (e.rejected_wrong_region = {false_val} OR e.rejected_wrong_region IS NULL)
                GROUP BY e.offer_type, a.advertiser_id
                ORDER BY ad_count DESC
            '''

            cursor.execute(query)
            rows = cursor.fetchall()

            # Aggregate by offer type
            offer_data = {}
            total_offers = 0

            for row in rows:
                offer_type, offer_details, adv_id, count = row

                if offer_type not in offer_data:
                    offer_data[offer_type] = {
                        'ad_count': 0,
                        'competitors': set(),
                        'sample_offers': set()
                    }

                offer_data[offer_type]['ad_count'] += count
                offer_data[offer_type]['competitors'].add(adv_id)
                if offer_details:
                    offer_data[offer_type]['sample_offers'].add(offer_details)
                total_offers += count

            # Convert to list with labels and percentages
            offer_labels = {
                'percentage_discount': '% Off Discounts',
                'fixed_discount': 'Fixed Amount Off',
                'free_delivery': 'Free Delivery',
                'bogo': 'Buy One Get One',
                'limited_time': 'Limited Time Offer',
                'new_product': 'New Product Launch'
            }

            offers_list = []
            for offer_type, data in offer_data.items():
                percentage = round((data['ad_count'] / total_offers * 100), 1) if total_offers > 0 else 0
                offers_list.append({
                    'offer_type': offer_type,
                    'label': offer_labels.get(offer_type, offer_type.replace('_', ' ').title()),
                    'ad_count': data['ad_count'],
                    'percentage': percentage,
                    'competitors': list(data['competitors']),
                    'sample_offers': list(data['sample_offers'])[:3]  # Top 3 samples
                })

            # Sort by ad_count descending
            offers_list.sort(key=lambda x: x['ad_count'], reverse=True)

            return offers_list

    def get_restaurants_breakdown(self) -> List[Dict]:
        """
        Get top restaurants being promoted with % distribution
        Extracted from product_name field via vision AI

        Returns:
            List of restaurant insights:
            [
                {
                    "restaurant": "Haldiram's",
                    "ad_count": 12,
                    "percentage": 15.3,
                    "food_category": "Asian Food",
                    "competitors": ["Talabat"]
                },
                ...
            ]
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            true_val = self._true_val()
            false_val = self._false_val()

            query = f'''
                SELECT
                    e.product_name,
                    e.product_category,
                    a.advertiser_id,
                    COUNT(*) as ad_count
                FROM ads a
                JOIN ad_enrichment e ON a.id = e.ad_id
                WHERE a.is_active = {true_val}
                  AND e.product_name IS NOT NULL
                  AND e.product_name != ''
                  AND e.product_name != 'Unknown'
                  AND e.product_category = 'Specific Restaurant/Brand Promo'
                  AND (e.rejected_wrong_region = {false_val} OR e.rejected_wrong_region IS NULL)
                GROUP BY e.product_name, a.advertiser_id
                ORDER BY ad_count DESC
                LIMIT 20
            '''

            cursor.execute(query)
            rows = cursor.fetchall()

            # Aggregate restaurants
            total_restaurant_ads = sum(row[3] for row in rows)

            restaurants_list = []
            for row in rows:
                product_name, product_category, adv_id, ad_count = row

                # Extract restaurant name (format: "Restaurant - Food Type")
                restaurant = product_name.split(' - ')[0] if ' - ' in product_name else product_name

                percentage = round((ad_count / total_restaurant_ads * 100), 1) if total_restaurant_ads > 0 else 0

                restaurants_list.append({
                    'restaurant': restaurant,
                    'ad_count': ad_count,
                    'percentage': percentage,
                    'food_category': product_category,
                    'competitors': [adv_id]
                })

            return restaurants_list

    def get_brands_breakdown(self) -> List[Dict]:
        """
        Get brand mentions breakdown with % distribution
        Vision-extracted brand data from LLaVA

        Returns:
            List of brand insights:
            [
                {
                    "brand": "Snoonu",
                    "ad_count": 25,
                    "percentage": 35.2,
                    "competitors": ["AR12079153035289296897"],
                    "food_categories": ["Pizza & Italian", "Burgers & Fast Food"]
                },
                ...
            ]
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            true_val = self._true_val()
            false_val = self._false_val()
            
            # GROUP_CONCAT vs STRING_AGG
            concat_func = "STRING_AGG(DISTINCT e.food_category, ',')" if self.use_postgres else "GROUP_CONCAT(DISTINCT e.food_category)"

            query = f'''
                SELECT
                    e.brand,
                    a.advertiser_id,
                    COUNT(*) as ad_count,
                    {concat_func} as food_categories
                FROM ads a
                JOIN ad_enrichment e ON a.id = e.ad_id
                WHERE a.is_active = {true_val}
                  AND e.brand IS NOT NULL
                  AND e.brand != ''
                  AND (e.rejected_wrong_region = {false_val} OR e.rejected_wrong_region IS NULL)
                GROUP BY e.brand, a.advertiser_id
                ORDER BY ad_count DESC
            '''

            cursor.execute(query)
            rows = cursor.fetchall()

            # Aggregate by brand
            brand_data = {}
            total_brand_ads = 0

            for row in rows:
                brand, adv_id, count, food_cats = row

                if brand not in brand_data:
                    brand_data[brand] = {
                        'ad_count': 0,
                        'competitors': set(),
                        'food_categories': set()
                    }

                brand_data[brand]['ad_count'] += count
                brand_data[brand]['competitors'].add(adv_id)

                # Parse food categories
                if food_cats:
                    for cat in food_cats.split(','):
                        if cat and cat.strip():
                            brand_data[brand]['food_categories'].add(cat.strip())

                total_brand_ads += count

            # Convert to list with percentages
            brands_list = []
            for brand, data in brand_data.items():
                percentage = round((data['ad_count'] / total_brand_ads * 100), 1) if total_brand_ads > 0 else 0
                brands_list.append({
                    'brand': brand,
                    'ad_count': data['ad_count'],
                    'percentage': percentage,
                    'competitors': list(data['competitors']),
                    'food_categories': list(data['food_categories'])
                })

            # Sort by ad_count descending
            brands_list.sort(key=lambda x: x['ad_count'], reverse=True)

            return brands_list

    def get_food_categories_breakdown(self) -> List[Dict]:
        """
        Get food categories breakdown with % distribution
        Vision-extracted food category data from LLaVA

        Returns:
            List of food category insights:
            [
                {
                    "food_category": "Pizza & Italian",
                    "ad_count": 15,
                    "percentage": 25.3,
                    "competitors": ["Snoonu", "Talabat"],
                    "brands": ["Domino's", "Pizza Hut"]
                },
                ...
            ]
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            true_val = self._true_val()
            false_val = self._false_val()

            # GROUP_CONCAT vs STRING_AGG
            concat_func = "STRING_AGG(DISTINCT e.brand, ',')" if self.use_postgres else "GROUP_CONCAT(DISTINCT e.brand)"

            query = f'''
                SELECT
                    e.food_category,
                    a.advertiser_id,
                    COUNT(*) as ad_count,
                    {concat_func} as brands
                FROM ads a
                JOIN ad_enrichment e ON a.id = e.ad_id
                WHERE a.is_active = {true_val}
                  AND e.food_category IS NOT NULL
                  AND e.food_category != ''
                  AND (e.rejected_wrong_region = {false_val} OR e.rejected_wrong_region IS NULL)
                GROUP BY e.food_category, a.advertiser_id
                ORDER BY ad_count DESC
            '''

            cursor.execute(query)
            rows = cursor.fetchall()

            # Aggregate by food category
            category_data = {}
            total_food_ads = 0

            for row in rows:
                food_cat, adv_id, count, brands_str = row

                if food_cat not in category_data:
                    category_data[food_cat] = {
                        'ad_count': 0,
                        'competitors': set(),
                        'brands': set()
                    }

                category_data[food_cat]['ad_count'] += count
                category_data[food_cat]['competitors'].add(adv_id)

                # Parse brands
                if brands_str:
                    for brand in brands_str.split(','):
                        if brand and brand.strip():
                            category_data[food_cat]['brands'].add(brand.strip())

                total_food_ads += count

            # Convert to list with percentages
            categories_list = []
            for food_cat, data in category_data.items():
                percentage = round((data['ad_count'] / total_food_ads * 100), 1) if total_food_ads > 0 else 0
                categories_list.append({
                    'food_category': food_cat,
                    'ad_count': data['ad_count'],
                    'percentage': percentage,
                    'competitors': list(data['competitors']),
                    'brands': list(data['brands'])
                })

            # Sort by ad_count descending
            categories_list.sort(key=lambda x: x['ad_count'], reverse=True)

            return categories_list

    def get_product_categories_breakdown(self) -> List[Dict]:
        """
        Get product categories breakdown with % distribution
        General product category data (retail, restaurant, electronics, beauty, etc.)

        Returns:
            List of product category insights:
            [
                {
                    "product_category": "retail",
                    "ad_count": 49,
                    "percentage": 43.4,
                    "competitors": ["Snoonu", "Keeta"],
                    "brands": ["Snoonu", "Keeta", "Talabat"]
                },
                ...
            ]
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            true_val = self._true_val()
            false_val = self._false_val()

            # GROUP_CONCAT vs STRING_AGG
            concat_func = "STRING_AGG(DISTINCT e.brand, ',')" if self.use_postgres else "GROUP_CONCAT(DISTINCT e.brand)"

            query = f'''
                SELECT
                    e.product_category,
                    a.advertiser_id,
                    COUNT(*) as ad_count,
                    {concat_func} as brands
                FROM ads a
                JOIN ad_enrichment e ON a.id = e.ad_id
                WHERE a.is_active = {true_val}
                  AND e.product_category IS NOT NULL
                  AND e.product_category != ''
                  AND (e.rejected_wrong_region = {false_val} OR e.rejected_wrong_region IS NULL)
                GROUP BY e.product_category, a.advertiser_id
                ORDER BY ad_count DESC
            '''

            cursor.execute(query)
            rows = cursor.fetchall()

            # Aggregate by product category
            category_data = {}
            total_ads = 0

            for row in rows:
                product_cat, adv_id, count, brands_str = row

                if product_cat not in category_data:
                    category_data[product_cat] = {
                        'ad_count': 0,
                        'competitors': set(),
                        'brands': set()
                    }

                category_data[product_cat]['ad_count'] += count
                category_data[product_cat]['competitors'].add(adv_id)

                # Parse brands
                if brands_str:
                    for brand in brands_str.split(','):
                        if brand and brand.strip():
                            category_data[product_cat]['brands'].add(brand.strip())

                total_ads += count

            # Convert to list with percentages
            categories_list = []
            for product_cat, data in category_data.items():
                percentage = round((data['ad_count'] / total_ads * 100), 1) if total_ads > 0 else 0

                # Friendly category name
                category_label = product_cat.replace('_', ' ').title()

                categories_list.append({
                    'product_category': product_cat,
                    'category_label': category_label,
                    'ad_count': data['ad_count'],
                    'percentage': percentage,
                    'competitors': list(data['competitors']),
                    'brands': list(data['brands'])
                })

            # Sort by ad_count descending
            categories_list.sort(key=lambda x: x['ad_count'], reverse=True)

            return categories_list

    def mark_ads_inactive(self, advertiser_id: str, ad_signatures: List[str]):
        """
        Mark ads as inactive if they're not in the provided list
        Used for incremental scraping to detect removed ads

        Args:
            advertiser_id: Competitor's advertiser ID
            ad_signatures: List of ad signatures (ad_text||image_url) that are ACTIVE
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            ph = self._param_placeholder()
            true_val = self._true_val()
            false_val = self._false_val()

            # Get all ads for this advertiser
            cursor.execute(f'''
                SELECT id, ad_text, image_url
                FROM ads
                WHERE advertiser_id = {ph} AND is_active = {true_val}
            ''', (advertiser_id,))

            rows = cursor.fetchall()

            inactive_count = 0
            for row in rows:
                ad_id, ad_text, image_url = row
                signature = f"{ad_text}||{image_url}"

                # If this ad is not in current scrape, mark inactive
                if signature not in ad_signatures:
                    cursor.execute(f'''
                        UPDATE ads
                        SET is_active = {false_val}, last_seen_date = CURRENT_TIMESTAMP
                        WHERE id = {ph}
                    ''', (ad_id,))
                    inactive_count += 1

            conn.commit()

            print(f"🔄 Marked {inactive_count} ads as inactive")
            return inactive_count

    def record_scrape_run(self, advertiser_id: str, stats: Dict):
        """
        Record a scrape run for tracking

        Args:
            advertiser_id: Competitor's advertiser ID
            stats: Dict with keys: ads_found, ads_new, ads_retired
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            ph = self._param_placeholder()

            cursor.execute(f'''
                INSERT INTO scrape_runs
                (advertiser_id, ads_found, ads_new, ads_retired, enrichment_enabled)
                VALUES ({ph}, {ph}, {ph}, {ph}, {ph})
            ''', (
                advertiser_id,
                stats.get('ads_total', 0),
                stats.get('ads_new', 0),
                stats.get('ads_updated', 0),
                1 if 'product_category' in stats else 0
            ))

            conn.commit()

    def get_stats(self) -> Dict:
        """Get overall database statistics"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            true_val = self._true_val()

            cursor.execute('SELECT COUNT(*) FROM ads')
            total_ads = cursor.fetchone()[0]

            cursor.execute(f'SELECT COUNT(*) FROM ads WHERE is_active = {true_val}')
            active_ads = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(DISTINCT advertiser_id) FROM ads')
            total_competitors = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM ad_enrichment')
            enriched_ads = cursor.fetchone()[0]

            return {
                'total_ads': total_ads,
                'active_ads': active_ads,
                'total_competitors': total_competitors,
                'enriched_ads': enriched_ads,
                'enrichment_percentage': int((enriched_ads / total_ads * 100)) if total_ads > 0 else 0
            }

    # ========================================================================
    # Product Knowledge Base Methods
    # ========================================================================

    def lookup_product(self, product_name: str) -> Optional[Dict]:
        """
        Look up a product in the knowledge base
        Returns cached product info if found, None otherwise

        Args:
            product_name: Product/restaurant name to look up

        Returns:
            Dict with product info or None if not found
        """
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            ph = self._param_placeholder()

            # Try exact match first
            cursor.execute(f'''
                SELECT * FROM product_knowledge
                WHERE LOWER(product_name) = LOWER({ph})
            ''', (product_name,))

            row = cursor.fetchone()

            if row:
                product = dict(row)
                # Parse JSON metadata if present
                if product.get('metadata'):
                    product['metadata'] = json.loads(product['metadata'])
                return product

            # Try fuzzy match (contains)
            cursor.execute(f'''
                SELECT * FROM product_knowledge
                WHERE LOWER(product_name) LIKE LOWER({ph})
                ORDER BY LENGTH(product_name) ASC
                LIMIT 1
            ''', (f'%{product_name}%',))

            row = cursor.fetchone()

            if row:
                product = dict(row)
                if product.get('metadata'):
                    product['metadata'] = json.loads(product['metadata'])
                return product

            return None

    def save_product_knowledge(self, product_data: Dict):
        """
        Save product information to knowledge base

        Args:
            product_data: Dict with keys:
                - product_name (required)
                - product_type (required): 'restaurant', 'unknown_category', 'subscription'
                - category (optional)
                - is_restaurant (optional bool)
                - is_unknown_category (optional bool)
                - is_subscription (optional bool)
                - metadata (optional dict)
                - confidence (optional float)
                - search_source (optional): 'web_search', 'manual', etc.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Convert metadata dict to JSON if present
            metadata_json = None
            if 'metadata' in product_data and product_data['metadata']:
                metadata_json = json.dumps(product_data['metadata'])

            ph = self._param_placeholder()

            # Use ON CONFLICT for Postgres, INSERT OR REPLACE for SQLite
            if self.use_postgres:
                cursor.execute(f'''
                    INSERT INTO product_knowledge
                    (product_name, product_type, category, is_restaurant, is_unknown_category,
                     is_subscription, metadata, confidence, search_source, verified_date)
                    VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, CURRENT_TIMESTAMP)
                    ON CONFLICT (product_name) DO UPDATE SET
                        product_type = EXCLUDED.product_type,
                        category = EXCLUDED.category,
                        is_restaurant = EXCLUDED.is_restaurant,
                        is_unknown_category = EXCLUDED.is_unknown_category,
                        is_subscription = EXCLUDED.is_subscription,
                        metadata = EXCLUDED.metadata,
                        confidence = EXCLUDED.confidence,
                        search_source = EXCLUDED.search_source,
                        verified_date = CURRENT_TIMESTAMP
                ''', (
                    product_data['product_name'],
                    product_data['product_type'],
                    product_data.get('category'),
                    product_data.get('is_restaurant', False),
                    product_data.get('is_unknown_category', False),
                    product_data.get('is_subscription', False),
                    metadata_json,
                    product_data.get('confidence', 0.0),
                    product_data.get('search_source', 'unknown')
                ))
            else:
                cursor.execute(f'''
                    INSERT OR REPLACE INTO product_knowledge
                    (product_name, product_type, category, is_restaurant, is_unknown_category,
                     is_subscription, metadata, confidence, search_source, verified_date)
                    VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, CURRENT_TIMESTAMP)
                ''', (
                    product_data['product_name'],
                    product_data['product_type'],
                    product_data.get('category'),
                    product_data.get('is_restaurant', False),
                    product_data.get('is_unknown_category', False),
                    product_data.get('is_subscription', False),
                    metadata_json,
                    product_data.get('confidence', 0.0),
                    product_data.get('search_source', 'unknown')
                ))

            conn.commit()

            print(f"   💾 Cached product knowledge: {product_data['product_name']} ({product_data['product_type']})")

    def get_product_knowledge_stats(self) -> Dict:
        """Get statistics about the product knowledge base"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute('SELECT COUNT(*) FROM product_knowledge')
            total_products = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM product_knowledge WHERE is_restaurant = 1')
            total_restaurants = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM product_knowledge WHERE is_unknown_category = 1')
            total_products_physical = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM product_knowledge WHERE is_subscription = 1')
            total_subscriptions = cursor.fetchone()[0]

            return {
                'total_cached': total_products,
                'restaurants': total_restaurants,
                'unknown_categorys': total_products_physical,
                'subscriptions': total_subscriptions
            }


# ============================================================================
# Utility Functions
# ============================================================================

def test_database():
    """Test the database layer"""
    print("=" * 70)
    print("Testing Database Layer")
    print("=" * 70)

    db = AdDatabase()

    # Test data
    sample_ads = [
        {
            'advertiser_id': 'AR_TEST_001',
            'ad_text': 'Get 50% off your first order!',
            'image_url': 'https://example.com/ad1.jpg',
            'regions': 'QA',
            'product_category': 'Meal Deals',
            'product_name': 'First Order Discount',
            'messaging_themes': {'price': 0.8, 'speed': 0.6, 'quality': 0.1, 'convenience': 0.3},
            'primary_theme': 'price',
            'audience_segment': 'New Customers',
            'offer_type': 'percentage_discount',
            'offer_details': '50% off',
            'confidence_score': 0.9,
            'analysis_model': 'llama3.1:8b'
        }
    ]

    print("\n1. Saving test ads...")
    stats = db.save_ads(sample_ads)
    print(f"   Stats: {stats}")

    print("\n2. Retrieving ads for competitor...")
    ads = db.get_ads_by_competitor('AR_TEST_001')
    print(f"   Found {len(ads)} ads")
    if ads:
        print(f"   First ad: {ads[0].get('ad_text')}")

    print("\n3. Getting product breakdown...")
    products = db.get_products_by_competitor()
    print(f"   Found {len(products)} product categories")

    print("\n4. Getting database stats...")
    stats = db.get_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")

    print("\n" + "=" * 70)
    print("Test Complete!")
    print("=" * 70)


if __name__ == "__main__":
    test_database()
