#!/usr/bin/env python3
"""
Database Service for GCP App
Reads stock data from the local database instead of making API calls
"""

import sqlite3
import logging
import time
from typing import Dict, List, Optional
import os

class DatabaseService:
    def __init__(self, db_path="stock_data.db"):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self.cache = {}
        self.cache_duration = 30  # 30 seconds cache
        
    def get_stock_data(self, symbols: List[str]) -> Dict:
        """Get latest stock data from database for multiple symbols"""
        cache_key = f"stocks_{'_'.join(sorted(symbols))}"
        
        # Check cache first
        if cache_key in self.cache:
            cache_time, data = self.cache[cache_key]
            if time.time() - cache_time < self.cache_duration:
                return data
        
        try:
            if not os.path.exists(self.db_path):
                self.logger.warning(f"Database not found at {self.db_path}")
                return {}
                
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            stocks_data = {}
            
            for symbol in symbols:
                cursor.execute('''
                    SELECT symbol, price, change_amount, change_percent, volume, market_cap,
                           pe_ratio, beta, day_low, day_high, fifty_two_week_low, fifty_two_week_high,
                           previous_close, vwap, rsi, sma_20, sma_50, sma_200, macd,
                           dividend_yield, eps, timestamp
                    FROM stock_data 
                    WHERE symbol = ? 
                    ORDER BY timestamp DESC 
                    LIMIT 1
                ''', (symbol,))
                
                row = cursor.fetchone()
                if row:
                    # Convert database row to API format matching your existing structure
                    stocks_data[symbol] = {
                        'price': row[1] or 0,
                        'change': row[2] or 0,
                        'changePercent': row[3] or 0,
                        'volume': row[4] or 0,
                        'marketCap': row[5] or 0,
                        'peRatio': row[6] or 0,
                        'beta': row[7] or 0,
                        'dayRange': f"{row[8]:.2f} - {row[9]:.2f}" if row[8] and row[9] else "N/A",
                        'fiftyTwoWeekRange': f"{row[10]:.2f} - {row[11]:.2f}" if row[10] and row[11] else "N/A",
                        'vwap': row[13] or 0,
                        'rsi': row[14] or 50,
                        'dividendYield': f"{row[19]*100:.2f}%" if row[19] else "N/A",
                        'earnings': "N/A",
                        'eps': row[20] or 0,
                        'source': 'Local Database (Yahoo Finance)',
                        'timestamp': row[21]
                    }
                else:
                    self.logger.warning(f"No data found for symbol {symbol}")
            
            conn.close()
            
            # Cache the results
            self.cache[cache_key] = (time.time(), stocks_data)
            
            self.logger.info(f"Retrieved data for {len(stocks_data)} symbols from database")
            return stocks_data
            
        except Exception as e:
            self.logger.error(f"Database error: {e}")
            return {}
    
    def get_comprehensive_stock_data(self, symbol: str) -> Dict:
        """Get comprehensive stock data for individual stock pages"""
        try:
            if not os.path.exists(self.db_path):
                self.logger.warning(f"Database not found at {self.db_path}")
                return {}
                
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM stock_data 
                WHERE symbol = ? 
                ORDER BY timestamp DESC 
                LIMIT 1
            ''', (symbol,))
            
            row = cursor.fetchone()
            conn.close()
            
            if not row:
                self.logger.warning(f"No data found for symbol {symbol}")
                return {}
            
            # Extract data from database row
            current_price = row[2] or 0
            change = row[3] or 0
            change_percent = row[4] or 0
            volume = row[5] or 0
            market_cap = row[6] or 0
            pe_ratio = row[7] or 0
            beta = row[8] or 0
            day_low = row[9] or 0
            day_high = row[10] or 0
            week_52_low = row[11] or 0
            week_52_high = row[12] or 0
            vwap = row[14] or current_price
            rsi = row[15] or 50
            sma_20 = row[16] or 0
            sma_50 = row[17] or 0
            macd = row[19] or 0
            
            # Generate volume analytics (mock for now, can be enhanced)
            volume_analytics = self._generate_volume_analytics(volume)
            
            comprehensive_data = {
                'basic_info': {
                    'symbol': symbol.upper(),
                    'current_price': current_price,
                    'change': change,
                    'change_percent': change_percent,
                    'market_cap': market_cap,
                    'pe_ratio': pe_ratio,
                    'beta': beta,
                    'exchange': 'NASDAQ',
                    'currency': 'USD',
                    'timezone': 'EST',
                    'day_low': day_low,
                    'day_high': day_high,
                    'fifty_two_week_low': week_52_low,
                    'fifty_two_week_high': week_52_high,
                    'day_position_percent': ((current_price - day_low) / (day_high - day_low)) * 100 if day_high > day_low else 50,
                    'fifty_two_week_position_percent': ((current_price - week_52_low) / (week_52_high - week_52_low)) * 100 if week_52_high > week_52_low else 50,
                    'volume_analytics': volume_analytics,
                    'technical_indicators': {
                        'rsi': rsi,
                        'macd': macd,
                        'sma_20': sma_20,
                        'sma_50': sma_50,
                        'vwap': vwap
                    },
                    'price_statistics': {
                        '1_day_performance': change_percent,
                        '5_day_performance': 0,
                        '1_month_performance': 0,
                        '3_month_performance': 0,
                        '1_year_performance': 0
                    },
                    'source': 'Local Database (Yahoo Finance)'
                }
            }
            
            return comprehensive_data
            
        except Exception as e:
            self.logger.error(f"Error getting comprehensive data for {symbol}: {e}")
            return {}
    
    def _generate_volume_analytics(self, current_volume):
        """Generate volume analytics based on current volume"""
        # This is a simplified version - you could enhance this by storing historical volume data
        base_volume = current_volume if current_volume > 0 else 1000000
        
        return {
            'current_volume': current_volume,
            '5_day_avg': int(base_volume * 0.9),
            '10_day_avg': int(base_volume * 0.85),
            '15_day_avg': int(base_volume * 0.8),
            '30_day_avg': int(base_volume * 0.75),
            '3_month_avg': int(base_volume * 0.7),
            '6_month_avg': int(base_volume * 0.65),
            '1_year_avg': int(base_volume * 0.6),
            'volume_trend': 'Neutral',
            '30_day_ratio': 1.0
        }
    
    def get_database_stats(self) -> Dict:
        """Get statistics about the database"""
        try:
            if not os.path.exists(self.db_path):
                return {'status': 'Database not found'}
                
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get total records
            cursor.execute('SELECT COUNT(*) FROM stock_data')
            total_records = cursor.fetchone()[0]
            
            # Get unique symbols
            cursor.execute('SELECT COUNT(DISTINCT symbol) FROM stock_data')
            unique_symbols = cursor.fetchone()[0]
            
            # Get latest timestamp
            cursor.execute('SELECT MAX(timestamp) FROM stock_data')
            latest_update = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'status': 'Connected',
                'total_records': total_records,
                'unique_symbols': unique_symbols,
                'latest_update': latest_update,
                'database_path': self.db_path
            }
            
        except Exception as e:
            return {'status': f'Error: {e}'}

# Global instance
database_service = DatabaseService()
