"""
Dark Pool Activity Detection Scanner
Scans major indices for unusual trading activity patterns
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from typing import List, Dict, Any
import time

class DarkPoolScanner:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.detection_thresholds = {
            'volume_spike_multiplier': 3.0,
            'block_trade_size': 10000,
            'price_volume_divergence': 0.02,  # 2% price change threshold
            'min_volume': 100000  # Minimum daily volume to consider
        }
        
    def get_index_tickers(self, index_name: str) -> List[str]:
        """Get ticker symbols for major indices"""
        indices = {
            'sp500': [
                'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'META', 'BRK-B',
                'UNH', 'JNJ', 'JPM', 'V', 'PG', 'XOM', 'HD', 'CVX', 'MA', 'BAC',
                'ABBV', 'PFE', 'AVGO', 'KO', 'COST', 'DIS', 'TMO', 'WMT', 'DHR',
                'LIN', 'VZ', 'ABT', 'ADBE', 'CRM', 'NFLX', 'CMCSA', 'ACN', 'NKE',
                'TXN', 'RTX', 'QCOM', 'PM', 'HON', 'UPS', 'NEE', 'T', 'SPGI',
                'LOW', 'IBM', 'CAT', 'GS', 'INTU', 'AMD', 'AMGN', 'ISRG', 'CVS'
            ],
            'nasdaq100': [
                'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'META', 'AVGO',
                'COST', 'ADBE', 'NFLX', 'CRM', 'TXN', 'QCOM', 'CMCSA', 'HON',
                'AMD', 'INTU', 'AMGN', 'ISRG', 'BKNG', 'GILD', 'ADP', 'VRTX',
                'SBUX', 'FISV', 'CSX', 'REGN', 'ATVI', 'PYPL', 'CHTR', 'MRNA'
            ],
            'dow30': [
                'AAPL', 'MSFT', 'UNH', 'JNJ', 'JPM', 'V', 'PG', 'HD', 'CVX',
                'MRK', 'BAC', 'KO', 'DIS', 'WMT', 'CRM', 'VZ', 'AXP', 'IBM',
                'CAT', 'GS', 'HON', 'NKE', 'MMM', 'TRV', 'MCD', 'INTC', 'WBA', 'DOW'
            ]
        }
        return indices.get(index_name.lower(), indices['sp500'])
    
    def calculate_volume_metrics(self, ticker: str, days: int = 20) -> Dict[str, float]:
        """Calculate volume-based metrics for unusual activity detection"""
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period=f"{days + 5}d")
            
            if len(hist) < days:
                return None
                
            current_volume = hist['Volume'].iloc[-1]
            avg_volume = hist['Volume'].iloc[-days:-1].mean()
            volume_spike = current_volume / avg_volume if avg_volume > 0 else 0
            
            # Price change analysis
            current_price = hist['Close'].iloc[-1]
            prev_price = hist['Close'].iloc[-2]
            price_change_pct = ((current_price - prev_price) / prev_price) * 100
            
            # Volume-weighted average price (VWAP) analysis
            typical_price = (hist['High'] + hist['Low'] + hist['Close']) / 3
            vwap = (typical_price * hist['Volume']).sum() / hist['Volume'].sum()
            vwap_deviation = ((current_price - vwap) / vwap) * 100
            
            return {
                'ticker': ticker,
                'current_volume': int(current_volume),
                'avg_volume': int(avg_volume),
                'volume_spike_ratio': round(volume_spike, 2),
                'price_change_pct': round(price_change_pct, 2),
                'current_price': round(current_price, 2),
                'vwap': round(vwap, 2),
                'vwap_deviation': round(vwap_deviation, 2),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating metrics for {ticker}: {str(e)}")
            return None
    
    def detect_unusual_activity(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Detect various types of unusual trading activity"""
        if not metrics:
            return None
            
        alerts = []
        risk_score = 0
        
        # Volume spike detection
        if metrics['volume_spike_ratio'] >= self.detection_thresholds['volume_spike_multiplier']:
            alerts.append(f"Volume spike: {metrics['volume_spike_ratio']}x average")
            risk_score += 30
            
        # Large volume with minimal price movement (potential dark pool)
        if (metrics['current_volume'] > self.detection_thresholds['min_volume'] and 
            abs(metrics['price_change_pct']) < self.detection_thresholds['price_volume_divergence']):
            alerts.append("High volume, low price movement - potential institutional flow")
            risk_score += 25
            
        # VWAP deviation analysis
        if abs(metrics['vwap_deviation']) > 2.0:
            alerts.append(f"VWAP deviation: {metrics['vwap_deviation']}%")
            risk_score += 15
            
        # Block trade detection (estimated)
        if metrics['current_volume'] > self.detection_thresholds['block_trade_size'] * 10:
            alerts.append("Potential block trading activity")
            risk_score += 20
            
        # Price momentum with volume
        if abs(metrics['price_change_pct']) > 3.0 and metrics['volume_spike_ratio'] > 2.0:
            alerts.append("Strong price momentum with volume confirmation")
            risk_score += 25
            
        activity_type = "NORMAL"
        if risk_score >= 50:
            activity_type = "HIGH_UNUSUAL"
        elif risk_score >= 25:
            activity_type = "MODERATE_UNUSUAL"
        elif risk_score >= 10:
            activity_type = "LOW_UNUSUAL"
            
        return {
            **metrics,
            'alerts': alerts,
            'risk_score': risk_score,
            'activity_type': activity_type,
            'alert_count': len(alerts)
        }
    
    def scan_index(self, index_name: str = 'sp500', max_tickers: int = 50) -> List[Dict[str, Any]]:
        """Scan an entire index for unusual activity"""
        self.logger.info(f"Starting dark pool scan for {index_name} index")
        
        tickers = self.get_index_tickers(index_name)[:max_tickers]
        results = []
        
        for i, ticker in enumerate(tickers):
            try:
                self.logger.info(f"Scanning {ticker} ({i+1}/{len(tickers)})")
                
                # Calculate metrics
                metrics = self.calculate_volume_metrics(ticker)
                if not metrics:
                    continue
                    
                # Detect unusual activity
                analysis = self.detect_unusual_activity(metrics)
                if analysis and analysis['alert_count'] > 0:
                    results.append(analysis)
                    
                # Rate limiting to avoid overwhelming Yahoo Finance
                time.sleep(0.1)
                
            except Exception as e:
                self.logger.error(f"Error scanning {ticker}: {str(e)}")
                continue
                
        # Sort by risk score (highest first)
        results.sort(key=lambda x: x['risk_score'], reverse=True)
        
        self.logger.info(f"Dark pool scan completed. Found {len(results)} unusual activities")
        return results
    
    def get_scan_summary(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary statistics for the scan"""
        if not results:
            return {
                'total_alerts': 0,
                'high_risk_count': 0,
                'moderate_risk_count': 0,
                'low_risk_count': 0,
                'avg_risk_score': 0,
                'top_ticker': None,
                'scan_timestamp': datetime.now().isoformat()
            }
            
        high_risk = len([r for r in results if r['activity_type'] == 'HIGH_UNUSUAL'])
        moderate_risk = len([r for r in results if r['activity_type'] == 'MODERATE_UNUSUAL'])
        low_risk = len([r for r in results if r['activity_type'] == 'LOW_UNUSUAL'])
        
        avg_risk = sum(r['risk_score'] for r in results) / len(results)
        top_ticker = results[0]['ticker'] if results else None
        
        return {
            'total_alerts': len(results),
            'high_risk_count': high_risk,
            'moderate_risk_count': moderate_risk,
            'low_risk_count': low_risk,
            'avg_risk_score': round(avg_risk, 1),
            'top_ticker': top_ticker,
            'scan_timestamp': datetime.now().isoformat()
        }

if __name__ == "__main__":
    # Test the scanner
    scanner = DarkPoolScanner()
    results = scanner.scan_index('sp500', max_tickers=10)
    
    print(f"Found {len(results)} unusual activities:")
    for result in results[:5]:
        print(f"{result['ticker']}: {result['activity_type']} (Score: {result['risk_score']})")
        for alert in result['alerts']:
            print(f"  - {alert}")
