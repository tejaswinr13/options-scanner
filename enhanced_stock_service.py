#!/usr/bin/env python3
"""
Enhanced Stock Service
Provides comprehensive stock analytics including volume analysis, ranges, and technical indicators
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import time
from typing import Dict, List, Optional

class EnhancedStockService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.cache = {}
        self.cache_duration = 300  # 5 minutes

    def get_stock_data(self, symbol):
        """Get comprehensive stock data with caching and rate limiting protection"""
        cache_key = f"stock_data_{symbol}"
        
        # Check cache first
        if cache_key in self.cache:
            cache_time, data = self.cache[cache_key]
            if time.time() - cache_time < self.cache_duration:
                return data
        
        try:
            # Add delay to prevent rate limiting
            time.sleep(0.5)
            
            ticker = yf.Ticker(symbol)
            
            # Get basic info with error handling
            try:
                info = ticker.info
            except Exception as e:
                self.logger.warning(f"Failed to get info for {symbol}: {e}")
                # Return minimal data structure if API fails
                return self._get_fallback_data(symbol)
            
            # Get historical data for calculations
            try:
                hist_1d = ticker.history(period="1d", interval="1m")
                hist_5d = ticker.history(period="5d", interval="5m")
                hist_1mo = ticker.history(period="1mo", interval="1d")
                hist_3mo = ticker.history(period="3mo", interval="1d")
                hist_6mo = ticker.history(period="6mo", interval="1d")
                hist_1y = ticker.history(period="1y", interval="1d")
                hist_2y = ticker.history(period="2y", interval="1d")
                hist_5y = ticker.history(period="5y", interval="1d")
                hist_max = ticker.history(period="max", interval="1d")
            except Exception as e:
                self.logger.warning(f"Failed to get history for {symbol}: {e}")
                return self._get_fallback_data(symbol)
            hist_5y = ticker.history(period="5y", interval="1d")
            hist_max = ticker.history(period="max", interval="1d")
            
            # Basic stock information
            current_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
            if not current_price and not hist_1d.empty:
                current_price = hist_1d['Close'].iloc[-1]
            
            # Day range (high/low)
            day_high = info.get('dayHigh', current_price)
            day_low = info.get('dayLow', current_price)
            if not hist_1d.empty:
                day_high = max(day_high, hist_1d['High'].max())
                day_low = min(day_low, hist_1d['Low'].min())
            
            # 52-week range
            fifty_two_week_high = info.get('fiftyTwoWeekHigh', current_price)
            fifty_two_week_low = info.get('fiftyTwoWeekLow', current_price)
            
            # Volume analytics
            volume_analytics = self._calculate_volume_analytics(
                hist_1d, hist_5d, hist_1mo, hist_3mo, hist_6mo, hist_1y
            )
            
            # Technical indicators
            technical_indicators = self._calculate_technical_indicators(
                hist_1d, hist_5d, hist_1mo, hist_3mo, hist_6mo, hist_1y
            )
            
            # Price ranges and statistics
            price_statistics = self._calculate_price_statistics(
                current_price, hist_1d, hist_5d, hist_1mo, hist_3mo, hist_6mo, hist_1y
            )
            
            # Chart data for different timeframes
            chart_data = self._prepare_chart_data(
                hist_1d, hist_5d, hist_1mo, hist_3mo, hist_6mo, hist_1y, hist_2y, hist_5y, hist_max
            )
            
            result = {
                'symbol': symbol,
                'name': info.get('longName', info.get('shortName', symbol)),
                'sector': info.get('sector', ''),
                'industry': info.get('industry', ''),
                'market_cap': info.get('marketCap', 0),
                'current_price': float(current_price) if current_price else 0,
                'previous_close': info.get('previousClose', 0),
                
                # Day range
                'day_high': float(day_high) if day_high else 0,
                'day_low': float(day_low) if day_low else 0,
                'day_range_percent': ((day_high - day_low) / current_price * 100) if current_price and day_high and day_low else 0,
                
                # 52-week range
                'fifty_two_week_high': float(fifty_two_week_high) if fifty_two_week_high else 0,
                'fifty_two_week_low': float(fifty_two_week_low) if fifty_two_week_low else 0,
                'fifty_two_week_range_percent': ((fifty_two_week_high - fifty_two_week_low) / current_price * 100) if current_price and fifty_two_week_high and fifty_two_week_low else 0,
                
                # Position in ranges
                'day_position_percent': ((current_price - day_low) / (day_high - day_low) * 100) if day_high != day_low else 50,
                'fifty_two_week_position_percent': ((current_price - fifty_two_week_low) / (fifty_two_week_high - fifty_two_week_low) * 100) if fifty_two_week_high != fifty_two_week_low else 50,
                
                # Volume analytics
                'volume_analytics': volume_analytics,
                
                # Technical indicators
                'technical_indicators': technical_indicators,
                
                # Price statistics
                'price_statistics': price_statistics,
                
                # Chart data
                'chart_data': chart_data,
                
                # Additional info
                'pe_ratio': info.get('trailingPE', 0),
                'forward_pe': info.get('forwardPE', 0),
                'dividend_yield': info.get('dividendYield', 0),
                'beta': info.get('beta', 0),
                'earnings_date': info.get('earningsDate', None),
                'exchange': info.get('exchange', ''),
                'currency': info.get('currency', 'USD'),
                'timestamp': datetime.now().isoformat()
            }
            
            return result
            
        except Exception as e:
            self.logger.error(f'Error getting comprehensive data for {symbol}: {str(e)}')
            return {'error': str(e), 'symbol': symbol}
    
    def _calculate_volume_analytics(self, hist_1d, hist_5d, hist_1mo, hist_3mo, hist_6mo, hist_1y) -> Dict:
        """Calculate comprehensive volume analytics"""
        try:
            volume_data = {}
            
            # Current volume
            current_volume = 0
            if not hist_1d.empty and 'Volume' in hist_1d.columns:
                current_volume = hist_1d['Volume'].iloc[-1] if len(hist_1d) > 0 else 0
            
            volume_data['current_volume'] = int(current_volume)
            
            # Volume averages for different periods
            periods = {
                '1_day': hist_1d,
                '5_day': hist_5d,
                '10_day': hist_1mo.tail(10) if len(hist_1mo) >= 10 else hist_1mo,
                '15_day': hist_1mo.tail(15) if len(hist_1mo) >= 15 else hist_1mo,
                '30_day': hist_1mo,
                '3_month': hist_3mo,
                '6_month': hist_6mo,
                '1_year': hist_1y
            }
            
            for period_name, data in periods.items():
                if not data.empty and 'Volume' in data.columns:
                    avg_volume = data['Volume'].mean()
                    volume_data[f'{period_name}_avg'] = int(avg_volume) if not pd.isna(avg_volume) else 0
                else:
                    volume_data[f'{period_name}_avg'] = 0
            
            # Volume ratios (current vs averages)
            for period in ['5_day', '10_day', '15_day', '30_day', '3_month', '6_month', '1_year']:
                avg_key = f'{period}_avg'
                ratio_key = f'{period}_ratio'
                if volume_data[avg_key] > 0:
                    volume_data[ratio_key] = round(current_volume / volume_data[avg_key], 2)
                else:
                    volume_data[ratio_key] = 1.0
            
            # Volume trend analysis
            if not hist_5d.empty and 'Volume' in hist_5d.columns and len(hist_5d) >= 5:
                recent_volumes = hist_5d['Volume'].tail(5).tolist()
                volume_data['volume_trend'] = self._analyze_trend(recent_volumes)
            else:
                volume_data['volume_trend'] = 'neutral'
            
            return volume_data
            
        except Exception as e:
            self.logger.error(f'Error calculating volume analytics: {str(e)}')
            return {'error': str(e)}
    
    def _calculate_technical_indicators(self, hist_1d, hist_5d, hist_1mo, hist_3mo, hist_6mo, hist_1y) -> Dict:
        """Calculate comprehensive technical indicators"""
        try:
            indicators = {}
            
            # Use the most appropriate dataset for each indicator
            price_data_short = hist_5d['Close'] if not hist_5d.empty else hist_1d['Close'] if not hist_1d.empty else pd.Series()
            price_data_medium = hist_1mo['Close'] if not hist_1mo.empty else price_data_short
            price_data_long = hist_1y['Close'] if not hist_1y.empty else price_data_medium
            
            # RSI (14-period)
            if len(price_data_short) >= 15:
                indicators['rsi'] = self._calculate_rsi(price_data_short, 14)
            else:
                indicators['rsi'] = 50
            
            # Moving Averages
            sma_periods = [5, 10, 20, 50, 100, 200]
            for period in sma_periods:
                if len(price_data_long) >= period:
                    sma = price_data_long.rolling(window=period).mean().iloc[-1]
                    indicators[f'sma_{period}'] = float(sma) if not pd.isna(sma) else 0
                else:
                    indicators[f'sma_{period}'] = 0
            
            # Exponential Moving Averages
            ema_periods = [12, 26, 50]
            for period in ema_periods:
                if len(price_data_medium) >= period:
                    ema = price_data_medium.ewm(span=period).mean().iloc[-1]
                    indicators[f'ema_{period}'] = float(ema) if not pd.isna(ema) else 0
                else:
                    indicators[f'ema_{period}'] = 0
            
            # MACD
            if len(price_data_medium) >= 26:
                macd_data = self._calculate_macd(price_data_medium)
                indicators.update(macd_data)
            else:
                indicators.update({'macd': 0, 'macd_signal': 0, 'macd_histogram': 0})
            
            # Bollinger Bands
            if len(price_data_short) >= 20:
                bb_data = self._calculate_bollinger_bands(price_data_short, 20, 2)
                indicators.update(bb_data)
            else:
                indicators.update({'bb_upper': 0, 'bb_middle': 0, 'bb_lower': 0, 'bb_width': 0})
            
            # VWAP (Volume Weighted Average Price)
            if not hist_1d.empty and 'Volume' in hist_1d.columns:
                vwap = self._calculate_vwap(hist_1d)
                indicators['vwap'] = vwap
            else:
                indicators['vwap'] = 0
            
            # Stochastic Oscillator
            if not hist_5d.empty and len(hist_5d) >= 14:
                stoch_data = self._calculate_stochastic(hist_5d, 14, 3)
                indicators.update(stoch_data)
            else:
                indicators.update({'stoch_k': 50, 'stoch_d': 50})
            
            return indicators
            
        except Exception as e:
            self.logger.error(f'Error calculating technical indicators: {str(e)}')
            return {'error': str(e)}
    
    def _calculate_price_statistics(self, current_price, hist_1d, hist_5d, hist_1mo, hist_3mo, hist_6mo, hist_1y) -> Dict:
        """Calculate price statistics and performance metrics"""
        try:
            stats = {}
            
            # Performance over different periods
            periods = {
                '1_day': hist_1d,
                '5_day': hist_5d,
                '1_month': hist_1mo,
                '3_month': hist_3mo,
                '6_month': hist_6mo,
                '1_year': hist_1y
            }
            
            for period_name, data in periods.items():
                if not data.empty and len(data) > 1:
                    start_price = data['Close'].iloc[0]
                    if start_price > 0:
                        performance = ((current_price - start_price) / start_price) * 100
                        stats[f'{period_name}_performance'] = round(performance, 2)
                    else:
                        stats[f'{period_name}_performance'] = 0
                else:
                    stats[f'{period_name}_performance'] = 0
            
            # Volatility calculations
            for period_name, data in periods.items():
                if not data.empty and len(data) > 1:
                    returns = data['Close'].pct_change().dropna()
                    if len(returns) > 1:
                        volatility = returns.std() * np.sqrt(252)  # Annualized
                        stats[f'{period_name}_volatility'] = round(volatility * 100, 2)
                    else:
                        stats[f'{period_name}_volatility'] = 0
                else:
                    stats[f'{period_name}_volatility'] = 0
            
            return stats
            
        except Exception as e:
            self.logger.error(f'Error calculating price statistics: {str(e)}')
            return {'error': str(e)}
    
    def _prepare_chart_data(self, hist_1d, hist_5d, hist_1mo, hist_3mo, hist_6mo, hist_1y, hist_2y, hist_5y, hist_max) -> Dict:
        """Prepare chart data for different timeframes"""
        try:
            chart_data = {}
            
            timeframes = {
                '1d': hist_1d,
                '3d': hist_1d,  # Use 1d data for 3d view
                '5d': hist_5d,
                '15d': hist_1mo.tail(15) if len(hist_1mo) >= 15 else hist_1mo,
                '1m': hist_1mo,
                '3m': hist_3mo,
                '6m': hist_6mo,
                'ytd': self._get_ytd_data(hist_1y),
                '1y': hist_1y,
                '2y': hist_2y,
                '5y': hist_5y,
                'max': hist_max
            }
            
            for timeframe, data in timeframes.items():
                if not data.empty:
                    # Limit data points for performance
                    max_points = 500
                    if len(data) > max_points:
                        step = len(data) // max_points
                        data = data.iloc[::step]
                    
                    chart_data[timeframe] = {
                        'timestamps': [int(ts.timestamp() * 1000) for ts in data.index],
                        'open': data['Open'].tolist(),
                        'high': data['High'].tolist(),
                        'low': data['Low'].tolist(),
                        'close': data['Close'].tolist(),
                        'volume': data['Volume'].tolist() if 'Volume' in data.columns else []
                    }
                else:
                    chart_data[timeframe] = {
                        'timestamps': [],
                        'open': [],
                        'high': [],
                        'low': [],
                        'close': [],
                        'volume': []
                    }
            
            return chart_data
            
        except Exception as e:
            self.logger.error(f'Error preparing chart data: {str(e)}')
            return {'error': str(e)}
    
    def _get_ytd_data(self, hist_1y):
        """Get year-to-date data"""
        try:
            if hist_1y.empty:
                return pd.DataFrame()
            
            current_year = datetime.now().year
            ytd_start = datetime(current_year, 1, 1)
            
            # Filter data from start of current year
            ytd_data = hist_1y[hist_1y.index >= ytd_start]
            return ytd_data
            
        except Exception:
            return pd.DataFrame()
    
    def _calculate_rsi(self, prices, period=14):
        """Calculate RSI"""
        try:
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else 50
        except:
            return 50
    
    def _calculate_macd(self, prices, fast=12, slow=26, signal=9):
        """Calculate MACD"""
        try:
            ema_fast = prices.ewm(span=fast).mean()
            ema_slow = prices.ewm(span=slow).mean()
            macd_line = ema_fast - ema_slow
            signal_line = macd_line.ewm(span=signal).mean()
            histogram = macd_line - signal_line
            
            return {
                'macd': float(macd_line.iloc[-1]) if not pd.isna(macd_line.iloc[-1]) else 0,
                'macd_signal': float(signal_line.iloc[-1]) if not pd.isna(signal_line.iloc[-1]) else 0,
                'macd_histogram': float(histogram.iloc[-1]) if not pd.isna(histogram.iloc[-1]) else 0
            }
        except:
            return {'macd': 0, 'macd_signal': 0, 'macd_histogram': 0}
    
    def _calculate_bollinger_bands(self, prices, period=20, std_dev=2):
        """Calculate Bollinger Bands"""
        try:
            sma = prices.rolling(window=period).mean()
            std = prices.rolling(window=period).std()
            upper = sma + (std * std_dev)
            lower = sma - (std * std_dev)
            
            return {
                'bb_upper': float(upper.iloc[-1]) if not pd.isna(upper.iloc[-1]) else 0,
                'bb_middle': float(sma.iloc[-1]) if not pd.isna(sma.iloc[-1]) else 0,
                'bb_lower': float(lower.iloc[-1]) if not pd.isna(lower.iloc[-1]) else 0,
                'bb_width': float((upper.iloc[-1] - lower.iloc[-1]) / sma.iloc[-1] * 100) if not pd.isna(upper.iloc[-1]) and not pd.isna(lower.iloc[-1]) and sma.iloc[-1] > 0 else 0
            }
        except:
            return {'bb_upper': 0, 'bb_middle': 0, 'bb_lower': 0, 'bb_width': 0}
    
    def _calculate_vwap(self, hist_data):
        """Calculate VWAP"""
        try:
            if hist_data.empty or 'Volume' not in hist_data.columns:
                return 0
            typical_price = (hist_data['High'] + hist_data['Low'] + hist_data['Close']) / 3
            vwap = (typical_price * hist_data['Volume']).sum() / hist_data['Volume'].sum()
            return float(vwap) if not pd.isna(vwap) else 0
        except:
            return 0
    
    def _calculate_stochastic(self, hist_data, k_period=14, d_period=3):
        """Calculate Stochastic Oscillator"""
        try:
            if len(hist_data) < k_period:
                return {'stoch_k': 50, 'stoch_d': 50}
            
            low_min = hist_data['Low'].rolling(window=k_period).min()
            high_max = hist_data['High'].rolling(window=k_period).max()
            k_percent = 100 * ((hist_data['Close'] - low_min) / (high_max - low_min))
            d_percent = k_percent.rolling(window=d_period).mean()
            
            return {
                'stoch_k': float(k_percent.iloc[-1]) if not pd.isna(k_percent.iloc[-1]) else 50,
                'stoch_d': float(d_percent.iloc[-1]) if not pd.isna(d_percent.iloc[-1]) else 50
            }
        except:
            return {'stoch_k': 50, 'stoch_d': 50}
    
    def _analyze_trend(self, values):
        """Analyze trend direction from a list of values"""
        try:
            if len(values) < 3:
                return 'neutral'
            
            # Calculate trend using linear regression slope
            x = list(range(len(values)))
            slope = np.polyfit(x, values, 1)[0]
            
            if slope > 0.1:
                return 'increasing'
            elif slope < -0.1:
                return 'decreasing'
            else:
                return 'neutral'
        except Exception as e:
            self.logger.error(f"Error analyzing trend: {e}")
            return 'neutral'

    def _get_fallback_data(self, symbol):
        """Return fallback data when API fails due to rate limiting"""
        return {
            'symbol': symbol,
            'current_price': 0.00,
            'price_change': 0.00,
            'price_change_percent': 0.00,
            'day_high': 0.00,
            'day_low': 0.00,
            'fifty_two_week_high': 0.00,
            'fifty_two_week_low': 0.00,
            'volume': 0,
            'market_cap': 'N/A',
            'pe_ratio': 'N/A',
            'dividend_yield': 'N/A',
            'beta': 'N/A',
            'eps': 'N/A',
            'volume_analytics': {
                '1day_avg': 0,
                '5day_avg': 0,
                '10day_avg': 0,
                '15day_avg': 0,
                '30day_avg': 0,
                '3month_avg': 0,
                '6month_avg': 0,
                '1year_avg': 0
            },
            'technical_indicators': {
                'rsi': 50.0,
                'macd': 0.0,
                'sma_20': 0.0,
                'sma_50': 0.0,
                'sma_200': 0.0,
                'bollinger_upper': 0.0,
                'bollinger_lower': 0.0
            },
            'price_statistics': {
                '1day_return': 0.0,
                '5day_return': 0.0,
                '1month_return': 0.0,
                '3month_return': 0.0,
                '6month_return': 0.0,
                '1year_return': 0.0,
                'volatility': 0.0
            },
            'chart_data': {
                '1day': [],
                '5day': [],
                '1month': [],
                '3month': [],
                '6month': [],
                '1year': [],
                '2year': [],
                '5year': [],
                'max': []
            },
            'error': 'Rate limited - showing cached/fallback data'
        }

# Global instance
enhanced_stock_service = EnhancedStockService()
