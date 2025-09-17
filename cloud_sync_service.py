#!/usr/bin/env python3
"""
Cloud Sync Service
Syncs local SQLite database to cloud database for GCP app access
"""

import sqlite3
import json
import requests
import time
import logging
from typing import Dict, List
import os
from datetime import datetime

class CloudSyncService:
    def __init__(self, local_db_path="stock_data.db", sync_url=None):
        self.local_db_path = local_db_path
        self.sync_url = sync_url or "http://34.28.161.37:8080/api/sync-data"
        self.logger = logging.getLogger(__name__)
        
    def get_latest_local_data(self) -> Dict:
        """Get latest data from local database"""
        if not os.path.exists(self.local_db_path):
            self.logger.error("Local database not found")
            return {}
            
        conn = sqlite3.connect(self.local_db_path)
        cursor = conn.cursor()
        
        # Get latest data for each symbol
        cursor.execute('''
            SELECT s1.* FROM stock_data s1
            INNER JOIN (
                SELECT symbol, MAX(timestamp) as max_timestamp
                FROM stock_data
                GROUP BY symbol
            ) s2 ON s1.symbol = s2.symbol AND s1.timestamp = s2.max_timestamp
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        # Convert to dictionary format
        stocks_data = {}
        for row in rows:
            symbol = row[1]
            stocks_data[symbol] = {
                'symbol': symbol,
                'price': row[2],
                'change': row[3],
                'changePercent': row[4],
                'volume': row[5],
                'marketCap': row[6],
                'peRatio': row[7],
                'beta': row[8],
                'dayRange': f"{row[9]:.2f} - {row[10]:.2f}" if row[9] and row[10] else "N/A",
                'fiftyTwoWeekRange': f"{row[11]:.2f} - {row[12]:.2f}" if row[11] and row[12] else "N/A",
                'vwap': row[14],
                'rsi': row[15],
                'source': 'Local Database Sync',
                'timestamp': row[22]
            }
        
        return stocks_data
    
    def sync_to_cloud(self) -> bool:
        """Sync local data to cloud endpoint"""
        try:
            data = self.get_latest_local_data()
            if not data:
                self.logger.warning("No data to sync")
                return False
            
            # Send data to cloud endpoint
            response = requests.post(
                self.sync_url,
                json={'stocks': data, 'sync_timestamp': datetime.now().isoformat()},
                timeout=30
            )
            
            if response.status_code == 200:
                self.logger.info(f"Successfully synced {len(data)} stocks to cloud")
                return True
            else:
                self.logger.error(f"Sync failed with status {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"Sync error: {e}")
            return False
    
    def start_continuous_sync(self, interval=60):
        """Start continuous syncing every interval seconds"""
        self.logger.info(f"Starting continuous sync every {interval} seconds")
        
        while True:
            try:
                self.sync_to_cloud()
                time.sleep(interval)
            except KeyboardInterrupt:
                self.logger.info("Sync stopped by user")
                break
            except Exception as e:
                self.logger.error(f"Sync loop error: {e}")
                time.sleep(interval)

# Alternative: Direct database connection approach
class DatabaseConnector:
    """Direct database connection for GCP app"""
    
    def __init__(self, db_url=None):
        # This could be a connection to Google Cloud SQL, PostgreSQL, etc.
        self.db_url = db_url
        
    def setup_cloud_database(self):
        """Setup cloud database tables"""
        # Example for PostgreSQL/Cloud SQL
        create_table_sql = '''
        CREATE TABLE IF NOT EXISTS stock_data (
            id SERIAL PRIMARY KEY,
            symbol VARCHAR(10) NOT NULL,
            price DECIMAL(10,2),
            change_amount DECIMAL(10,2),
            change_percent DECIMAL(5,2),
            volume BIGINT,
            market_cap BIGINT,
            pe_ratio DECIMAL(8,2),
            beta DECIMAL(5,2),
            day_low DECIMAL(10,2),
            day_high DECIMAL(10,2),
            fifty_two_week_low DECIMAL(10,2),
            fifty_two_week_high DECIMAL(10,2),
            previous_close DECIMAL(10,2),
            vwap DECIMAL(10,2),
            rsi DECIMAL(5,2),
            sma_20 DECIMAL(10,2),
            sma_50 DECIMAL(10,2),
            sma_200 DECIMAL(10,2),
            macd DECIMAL(8,4),
            dividend_yield DECIMAL(5,4),
            eps DECIMAL(8,2),
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            source VARCHAR(50) DEFAULT 'local_sync'
        );
        
        CREATE INDEX IF NOT EXISTS idx_symbol_timestamp ON stock_data(symbol, timestamp);
        '''
        
        return create_table_sql

if __name__ == "__main__":
    # Example usage
    sync_service = CloudSyncService()
    
    print("🔄 Starting cloud sync service...")
    print("This will sync your local database to your GCP app every 60 seconds")
    print("Press Ctrl+C to stop\n")
    
    sync_service.start_continuous_sync(interval=60)
