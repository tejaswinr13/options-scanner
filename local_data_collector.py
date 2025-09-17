#!/usr/bin/env python3
"""
Local Data Collector for Mac
Continuously fetches Yahoo Finance data and stores it in a cloud database
The GCP app then reads from this database instead of making API calls
"""

import yfinance as yf
import pandas as pd
import numpy as np
import time
import logging
import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Dict
import schedule
import threading
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data_collector.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class LocalDataCollector:
    def __init__(self, db_path="stock_data.db"):
        self.db_path = db_path
        self.watchlist = [
            'LMND', 'HIMS', 'RKLB', 'TEM', 'SOUN', 'NBIS', 'GTLB', 'ESTC', 
            'WULF', 'RKT', 'DLO', 'CMG', 'FIG', 'OSCR', 'FIGR', 'VKTX', 
            'OPEN', 'RDW', 'KROS', 'PLTR', 'MSTR', 'SYM', 'OKLO', 'SOFI', 
            'IONQ', 'GRAB', 'EOSE', 'CRWV', 'BULL', 'APLD', 'BN', 'ASPI', 
            'IREN', 'AAPL', 'TSLA', 'NVDA', 'MSFT', 'GOOGL'
        ]
        self.init_database()
        
    def init_database(self):
        """Initialize SQLite database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create real-time stock data table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stock_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                price REAL,
                change_amount REAL,
                change_percent REAL,
                volume INTEGER,
                market_cap REAL,
                pe_ratio REAL,
                beta REAL,
                day_low REAL,
                day_high REAL,
                fifty_two_week_low REAL,
                fifty_two_week_high REAL,
                previous_close REAL,
                vwap REAL,
                rsi REAL,
                sma_20 REAL,
                sma_50 REAL,
                sma_200 REAL,
                macd REAL,
                dividend_yield REAL,
                eps REAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                source TEXT DEFAULT 'yfinance_local'
            )
        ''')
        
        # Create historical data table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS historical_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                date DATE,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create index for faster queries
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_symbol_timestamp ON stock_data(symbol, timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_historical_symbol_date ON historical_data(symbol, date)')
        
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")
    
    def calculate_technical_indicators(self, hist_data):
        """Calculate technical indicators from historical data"""
        if hist_data.empty:
            return {}
            
        close_prices = hist_data['Close']
        
        # RSI calculation
        def calculate_rsi(prices, period=14):
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi.iloc[-1] if not rsi.empty else 50
        
        # VWAP calculation
        def calculate_vwap(data):
            if 'Volume' in data.columns and not data['Volume'].empty:
                vwap = (data['Close'] * data['Volume']).sum() / data['Volume'].sum()
                return vwap
            return data['Close'].mean()
        
        # SMA calculations
        def calculate_sma(prices, period):
            return prices.rolling(window=period).mean().iloc[-1] if len(prices) >= period else prices.mean()
        
        # MACD calculation
        def calculate_macd(prices):
            ema_12 = prices.ewm(span=12).mean()
            ema_26 = prices.ewm(span=26).mean()
            macd = ema_12 - ema_26
            return macd.iloc[-1] if not macd.empty else 0
        
        return {
            'rsi': calculate_rsi(close_prices),
            'vwap': calculate_vwap(hist_data),
            'sma_20': calculate_sma(close_prices, 20),
            'sma_50': calculate_sma(close_prices, 50),
            'sma_200': calculate_sma(close_prices, 200),
            'macd': calculate_macd(close_prices)
        }
    
    def fetch_stock_data(self, symbol: str) -> Dict:
        """Fetch comprehensive stock data for a single symbol"""
        try:
            ticker = yf.Ticker(symbol)
            
            # Get basic info
            info = ticker.info
            
            # Get historical data for technical indicators
            hist_1mo = ticker.history(period="1mo", interval="1d")
            hist_1d = ticker.history(period="1d", interval="1m")
            
            # Calculate technical indicators
            tech_indicators = self.calculate_technical_indicators(hist_1mo)
            
            # Extract current data
            current_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
            previous_close = info.get('previousClose', 0)
            change_amount = current_price - previous_close if current_price and previous_close else 0
            change_percent = (change_amount / previous_close) * 100 if previous_close else 0
            
            stock_data = {
                'symbol': symbol,
                'price': current_price,
                'change_amount': change_amount,
                'change_percent': change_percent,
                'volume': info.get('volume', 0),
                'market_cap': info.get('marketCap', 0),
                'pe_ratio': info.get('trailingPE', 0),
                'beta': info.get('beta', 0),
                'day_low': info.get('dayLow', 0),
                'day_high': info.get('dayHigh', 0),
                'fifty_two_week_low': info.get('fiftyTwoWeekLow', 0),
                'fifty_two_week_high': info.get('fiftyTwoWeekHigh', 0),
                'previous_close': previous_close,
                'vwap': tech_indicators.get('vwap', current_price),
                'rsi': tech_indicators.get('rsi', 50),
                'sma_20': tech_indicators.get('sma_20', 0),
                'sma_50': tech_indicators.get('sma_50', 0),
                'sma_200': tech_indicators.get('sma_200', 0),
                'macd': tech_indicators.get('macd', 0),
                'dividend_yield': info.get('dividendYield', 0),
                'eps': info.get('trailingEps', 0)
            }
            
            return stock_data
            
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            return None
    
    def store_stock_data(self, stock_data: Dict):
        """Store stock data in database"""
        if not stock_data:
            return
            
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO stock_data (
                symbol, price, change_amount, change_percent, volume, market_cap,
                pe_ratio, beta, day_low, day_high, fifty_two_week_low, fifty_two_week_high,
                previous_close, vwap, rsi, sma_20, sma_50, sma_200, macd,
                dividend_yield, eps, source
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            stock_data['symbol'], stock_data['price'], stock_data['change_amount'],
            stock_data['change_percent'], stock_data['volume'], stock_data['market_cap'],
            stock_data['pe_ratio'], stock_data['beta'], stock_data['day_low'],
            stock_data['day_high'], stock_data['fifty_two_week_low'], stock_data['fifty_two_week_high'],
            stock_data['previous_close'], stock_data['vwap'], stock_data['rsi'],
            stock_data['sma_20'], stock_data['sma_50'], stock_data['sma_200'], stock_data['macd'],
            stock_data['dividend_yield'], stock_data['eps'], 'yfinance_local'
        ))
        
        conn.commit()
        conn.close()
    
    def collect_all_data(self):
        """Collect data for all symbols in watchlist"""
        logger.info(f"Starting data collection for {len(self.watchlist)} symbols")
        
        for symbol in self.watchlist:
            try:
                stock_data = self.fetch_stock_data(symbol)
                if stock_data:
                    self.store_stock_data(stock_data)
                    logger.info(f"✅ Collected data for {symbol}: ${stock_data['price']:.2f}")
                else:
                    logger.warning(f"❌ Failed to collect data for {symbol}")
                
                # Small delay to avoid overwhelming Yahoo Finance
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error processing {symbol}: {e}")
        
        logger.info("Data collection cycle completed")
    
    def get_latest_data(self, symbols: List[str] = None) -> Dict:
        """Get latest data from database for API consumption"""
        if not symbols:
            symbols = self.watchlist
            
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        stocks_data = {}
        
        for symbol in symbols:
            cursor.execute('''
                SELECT * FROM stock_data 
                WHERE symbol = ? 
                ORDER BY timestamp DESC 
                LIMIT 1
            ''', (symbol,))
            
            row = cursor.fetchone()
            if row:
                # Convert database row to API format
                stocks_data[symbol] = {
                    'price': row[2],
                    'change': row[3],
                    'changePercent': row[4],
                    'volume': row[5],
                    'marketCap': row[6],
                    'peRatio': row[7],
                    'beta': row[8],
                    'dayRange': f"{row[9]:.2f} - {row[10]:.2f}",
                    'fiftyTwoWeekRange': f"{row[11]:.2f} - {row[12]:.2f}",
                    'vwap': row[14],
                    'rsi': row[15],
                    'source': 'Local Yahoo Finance Data'
                }
        
        conn.close()
        return stocks_data
    
    def start_scheduler(self):
        """Start the data collection scheduler"""
        # Collect data every 30 seconds during market hours
        schedule.every(30).seconds.do(self.collect_all_data)
        
        # Also collect every 5 minutes as backup
        schedule.every(5).minutes.do(self.collect_all_data)
        
        logger.info("Data collection scheduler started")
        logger.info("Collecting data every 30 seconds during runtime")
        
        # Run initial collection
        self.collect_all_data()
        
        # Keep running
        while True:
            schedule.run_pending()
            time.sleep(1)

def main():
    """Main function to run the data collector"""
    collector = LocalDataCollector()
    
    print("🚀 Starting Local Stock Data Collector")
    print("📊 This will continuously collect Yahoo Finance data")
    print("💾 Data will be stored in local SQLite database")
    print("🔄 Your GCP app can read from this database")
    print("\nPress Ctrl+C to stop\n")
    
    try:
        collector.start_scheduler()
    except KeyboardInterrupt:
        print("\n⏹️  Data collector stopped")
        logger.info("Data collector stopped by user")

if __name__ == "__main__":
    main()
