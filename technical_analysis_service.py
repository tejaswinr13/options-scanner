#!/usr/bin/env python3
"""
Technical Analysis Service
Provides advanced technical indicators, pattern recognition, and forecasting
"""

import yfinance as yf
import pandas as pd
import numpy as np
from scipy import stats
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
import pandas_ta as ta
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json
import time

class TechnicalAnalysisService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.cache = {}
        self.cache_duration = 300  # 5 minutes cache
        
    def get_technical_analysis(self, symbol: str) -> Dict:
        """Get comprehensive technical analysis for a stock"""
        try:
            # Check cache first
            cache_key = f"tech_analysis_{symbol}"
            if self._is_cached(cache_key):
                return self.cache[cache_key]['data']
            
            # Get stock data
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1y", interval="1d")
            
            if hist.empty:
                return {'error': f'No data available for {symbol}'}
            
            analysis = {
                'symbol': symbol,
                'last_updated': datetime.now().isoformat(),
                'technical_indicators': self._calculate_technical_indicators(hist),
                'pattern_recognition': self._detect_patterns(hist),
                'support_resistance': self._find_support_resistance(hist),
                'trend_analysis': self._analyze_trends(hist),
                'forecasting': self._generate_forecasts(hist),
                'risk_metrics': self._calculate_risk_metrics(hist),
                'trading_signals': self._generate_trading_signals(hist)
            }
            
            # Cache the result
            self._cache_data(cache_key, analysis)
            
            return analysis
            
        except Exception as e:
            self.logger.error(f'Error in technical analysis for {symbol}: {str(e)}')
            return {'error': str(e)}
    
    def _calculate_technical_indicators(self, data: pd.DataFrame) -> Dict:
        """Calculate comprehensive technical indicators"""
        try:
            close = data['Close']
            high = data['High']
            low = data['Low']
            volume = data['Volume']
            
            indicators = {}
            
            # Moving Averages
            sma_20 = ta.sma(close, length=20)
            indicators['sma_20'] = float(sma_20.iloc[-1]) if sma_20 is not None and len(sma_20.dropna()) > 0 else None
            sma_50 = ta.sma(close, length=50)
            indicators['sma_50'] = float(sma_50.iloc[-1]) if sma_50 is not None and len(sma_50.dropna()) > 0 else None
            sma_200 = ta.sma(close, length=200)
            indicators['sma_200'] = float(sma_200.iloc[-1]) if sma_200 is not None and len(sma_200.dropna()) > 0 else None
            ema_12 = ta.ema(close, length=12)
            indicators['ema_12'] = float(ema_12.iloc[-1]) if ema_12 is not None and len(ema_12.dropna()) > 0 else None
            ema_26 = ta.ema(close, length=26)
            indicators['ema_26'] = float(ema_26.iloc[-1]) if ema_26 is not None and len(ema_26.dropna()) > 0 else None
            
            # Oscillators
            rsi = ta.rsi(close, length=14)
            indicators['rsi'] = float(rsi.iloc[-1]) if rsi is not None and len(rsi.dropna()) > 0 else None
            
            try:
                stoch = ta.stoch(high, low, close)
                if stoch is not None and not stoch.empty:
                    indicators['stoch_k'] = float(stoch['STOCHk_14_3_3'].iloc[-1]) if 'STOCHk_14_3_3' in stoch.columns else None
                    indicators['stoch_d'] = float(stoch['STOCHd_14_3_3'].iloc[-1]) if 'STOCHd_14_3_3' in stoch.columns else None
                else:
                    indicators['stoch_k'] = None
                    indicators['stoch_d'] = None
            except:
                indicators['stoch_k'] = None
                indicators['stoch_d'] = None
            
            # MACD
            try:
                macd = ta.macd(close)
                if macd is not None and not macd.empty:
                    indicators['macd'] = float(macd['MACD_12_26_9'].iloc[-1]) if 'MACD_12_26_9' in macd.columns else None
                    indicators['macd_signal'] = float(macd['MACDs_12_26_9'].iloc[-1]) if 'MACDs_12_26_9' in macd.columns else None
                    indicators['macd_histogram'] = float(macd['MACDh_12_26_9'].iloc[-1]) if 'MACDh_12_26_9' in macd.columns else None
                else:
                    indicators['macd'] = None
                    indicators['macd_signal'] = None
                    indicators['macd_histogram'] = None
            except:
                indicators['macd'] = None
                indicators['macd_signal'] = None
                indicators['macd_histogram'] = None
            
            # Bollinger Bands
            try:
                bb = ta.bbands(close)
                if bb is not None and not bb.empty:
                    indicators['bb_upper'] = float(bb['BBU_5_2.0'].iloc[-1]) if 'BBU_5_2.0' in bb.columns else None
                    indicators['bb_middle'] = float(bb['BBM_5_2.0'].iloc[-1]) if 'BBM_5_2.0' in bb.columns else None
                    indicators['bb_lower'] = float(bb['BBL_5_2.0'].iloc[-1]) if 'BBL_5_2.0' in bb.columns else None
                else:
                    indicators['bb_upper'] = None
                    indicators['bb_middle'] = None
                    indicators['bb_lower'] = None
            except:
                indicators['bb_upper'] = None
                indicators['bb_middle'] = None
                indicators['bb_lower'] = None
            
            indicators['bb_width'] = (indicators['bb_upper'] - indicators['bb_lower']) / indicators['bb_middle'] * 100 if all([indicators['bb_upper'], indicators['bb_lower'], indicators['bb_middle']]) else None
            
            # Volume indicators
            obv = ta.obv(close, volume)
            indicators['obv'] = float(obv.iloc[-1]) if obv is not None and len(obv.dropna()) > 0 else None
            ad = ta.ad(high, low, close, volume)
            indicators['ad_line'] = float(ad.iloc[-1]) if ad is not None and len(ad.dropna()) > 0 else None
            
            # Momentum indicators
            willr = ta.willr(high, low, close)
            indicators['williams_r'] = float(willr.iloc[-1]) if willr is not None and len(willr.dropna()) > 0 else None
            cci = ta.cci(high, low, close)
            indicators['cci'] = float(cci.iloc[-1]) if cci is not None and len(cci.dropna()) > 0 else None
            atr = ta.atr(high, low, close)
            indicators['atr'] = float(atr.iloc[-1]) if atr is not None and len(atr.dropna()) > 0 else None
            
            # Clean None values and convert numpy types to Python types
            cleaned_indicators = {}
            for k, v in indicators.items():
                if v is not None and not (isinstance(v, (int, float)) and np.isnan(v)):
                    if isinstance(v, np.ndarray):
                        cleaned_indicators[k] = float(v) if len(v) > 0 else None
                    elif isinstance(v, (np.integer, np.floating)):
                        cleaned_indicators[k] = float(v)
                    elif isinstance(v, np.bool_):
                        cleaned_indicators[k] = bool(v)
                    else:
                        cleaned_indicators[k] = v
            
            return cleaned_indicators
            
        except Exception as e:
            self.logger.error(f'Error calculating technical indicators: {str(e)}')
            return {}
    
    def _detect_patterns(self, data: pd.DataFrame) -> Dict:
        """Detect candlestick patterns and chart patterns"""
        try:
            open_prices = data['Open'].values
            high = data['High'].values
            low = data['Low'].values
            close = data['Close'].values
            
            patterns = {}
            
            # Candlestick patterns - using pandas-ta or custom logic
            patterns['doji'] = self._detect_doji(open_prices, high, low, close)
            patterns['hammer'] = self._detect_hammer(open_prices, high, low, close)
            patterns['shooting_star'] = self._detect_shooting_star(open_prices, high, low, close)
            patterns['engulfing_bullish'] = self._detect_bullish_engulfing(open_prices, high, low, close)
            patterns['engulfing_bearish'] = self._detect_bearish_engulfing(open_prices, high, low, close)
            patterns['morning_star'] = self._detect_morning_star(open_prices, high, low, close)
            patterns['evening_star'] = self._detect_evening_star(open_prices, high, low, close)
            
            # Chart patterns (simplified detection)
            patterns.update(self._detect_chart_patterns(data))
            
            return patterns
            
        except Exception as e:
            self.logger.error(f'Error detecting patterns: {str(e)}')
            return {}
    
    def _detect_chart_patterns(self, data: pd.DataFrame) -> Dict:
        """Detect chart patterns like head and shoulders, triangles, etc."""
        try:
            close = data['Close'].values
            patterns = {}
            
            if len(close) < 50:
                return patterns
            
            # Simple trend detection
            recent_data = close[-20:]
            slope, _, r_value, _, _ = stats.linregress(range(len(recent_data)), recent_data)
            
            patterns['trend_direction'] = 'bullish' if slope > 0 else 'bearish'
            patterns['trend_strength'] = abs(r_value)
            
            # Support/Resistance breakout detection
            recent_high = np.max(close[-10:])
            recent_low = np.min(close[-10:])
            prev_high = np.max(close[-30:-10])
            prev_low = np.min(close[-30:-10])
            
            patterns['resistance_breakout'] = bool(recent_high > prev_high * 1.02)
            patterns['support_breakdown'] = bool(recent_low < prev_low * 0.98)
            
            # Volatility patterns
            volatility = np.std(close[-20:]) / np.mean(close[-20:])
            patterns['high_volatility'] = bool(volatility > 0.03)
            patterns['low_volatility'] = bool(volatility < 0.01)
            
            return patterns
            
        except Exception as e:
            self.logger.error(f'Error detecting chart patterns: {str(e)}')
            return {}
    
    def _find_support_resistance(self, data: pd.DataFrame) -> Dict:
        """Find support and resistance levels"""
        try:
            close = data['Close'].values
            high = data['High'].values
            low = data['Low'].values
            
            # Find local maxima and minima
            from scipy.signal import argrelextrema
            
            # Resistance levels (local maxima)
            resistance_indices = argrelextrema(high, np.greater, order=5)[0]
            resistance_levels = [float(high[i]) for i in resistance_indices[-5:]]  # Last 5 resistance levels
            
            # Support levels (local minima)
            support_indices = argrelextrema(low, np.less, order=5)[0]
            support_levels = [float(low[i]) for i in support_indices[-5:]]  # Last 5 support levels
            
            current_price = float(close[-1])
            
            # Find nearest levels
            nearest_resistance = min([r for r in resistance_levels if r > current_price], default=None)
            nearest_support = max([s for s in support_levels if s < current_price], default=None)
            
            return {
                'resistance_levels': sorted(resistance_levels, reverse=True),
                'support_levels': sorted(support_levels, reverse=True),
                'nearest_resistance': nearest_resistance,
                'nearest_support': nearest_support,
                'current_price': current_price
            }
            
        except Exception as e:
            self.logger.error(f'Error finding support/resistance: {str(e)}')
            return {}
    
    def _analyze_trends(self, data: pd.DataFrame) -> Dict:
        """Analyze price trends and momentum"""
        try:
            close = data['Close'].values
            
            trends = {}
            
            # Short-term trend (20 days)
            if len(close) >= 20:
                short_slope, _, short_r, _, _ = stats.linregress(range(20), close[-20:])
                trends['short_term'] = {
                    'direction': 'bullish' if short_slope > 0 else 'bearish',
                    'strength': abs(short_r),
                    'slope': float(short_slope)
                }
            
            # Medium-term trend (50 days)
            if len(close) >= 50:
                med_slope, _, med_r, _, _ = stats.linregress(range(50), close[-50:])
                trends['medium_term'] = {
                    'direction': 'bullish' if med_slope > 0 else 'bearish',
                    'strength': abs(med_r),
                    'slope': float(med_slope)
                }
            
            # Long-term trend (200 days)
            if len(close) >= 200:
                long_slope, _, long_r, _, _ = stats.linregress(range(200), close[-200:])
                trends['long_term'] = {
                    'direction': 'bullish' if long_slope > 0 else 'bearish',
                    'strength': abs(long_r),
                    'slope': float(long_slope)
                }
            
            # Momentum analysis
            if len(close) >= 10:
                momentum_5d = (close[-1] - close[-6]) / close[-6] * 100
                momentum_10d = (close[-1] - close[-11]) / close[-11] * 100
                
                trends['momentum'] = {
                    '5_day': float(momentum_5d),
                    '10_day': float(momentum_10d)
                }
            
            return trends
            
        except Exception as e:
            self.logger.error(f'Error analyzing trends: {str(e)}')
            return {}
    
    def _generate_forecasts(self, data: pd.DataFrame) -> Dict:
        """Generate price forecasts using multiple models"""
        try:
            close = data['Close'].values
            
            if len(close) < 30:
                return {'error': 'Insufficient data for forecasting'}
            
            forecasts = {}
            
            # Linear regression forecast
            X = np.arange(len(close)).reshape(-1, 1)
            y = close
            
            model = LinearRegression()
            model.fit(X, y)
            
            # Forecast next 5 days
            future_days = np.arange(len(close), len(close) + 5).reshape(-1, 1)
            linear_forecast = model.predict(future_days)
            
            forecasts['linear_regression'] = {
                'next_5_days': [float(x) for x in linear_forecast],
                'confidence': float(model.score(X, y))
            }
            
            # Moving average forecast
            sma_20 = np.mean(close[-20:])
            ema_12 = close[-1]
            for i in range(11):
                ema_12 = 0.15 * close[-1-i] + 0.85 * ema_12
            
            forecasts['moving_average'] = {
                'sma_20_target': float(sma_20),
                'ema_12_trend': float(ema_12)
            }
            
            # Volatility-based forecast
            volatility = np.std(close[-20:])
            current_price = close[-1]
            
            forecasts['volatility_bands'] = {
                'upper_1std': float(current_price + volatility),
                'lower_1std': float(current_price - volatility),
                'upper_2std': float(current_price + 2 * volatility),
                'lower_2std': float(current_price - 2 * volatility)
            }
            
            # Price targets based on technical levels
            resistance_levels = self._find_support_resistance(data).get('resistance_levels', [])
            support_levels = self._find_support_resistance(data).get('support_levels', [])
            
            forecasts['technical_targets'] = {
                'upside_target': resistance_levels[0] if resistance_levels else None,
                'downside_target': support_levels[0] if support_levels else None
            }
            
            return forecasts
            
        except Exception as e:
            self.logger.error(f'Error generating forecasts: {str(e)}')
            return {}
    
    def _calculate_risk_metrics(self, data: pd.DataFrame) -> Dict:
        """Calculate risk and volatility metrics"""
        try:
            close = data['Close'].values
            
            if len(close) < 20:
                return {}
            
            returns = np.diff(close) / close[:-1]
            
            metrics = {
                'volatility_20d': float(np.std(returns[-20:]) * np.sqrt(252)),  # Annualized
                'volatility_60d': float(np.std(returns[-60:]) * np.sqrt(252)) if len(returns) >= 60 else None,
                'sharpe_ratio': float(np.mean(returns[-60:]) / np.std(returns[-60:]) * np.sqrt(252)) if len(returns) >= 60 and np.std(returns[-60:]) > 0 else None,
                'max_drawdown': self._calculate_max_drawdown(close),
                'var_95': float(np.percentile(returns[-60:], 5)) if len(returns) >= 60 else None,
                'var_99': float(np.percentile(returns[-60:], 1)) if len(returns) >= 60 else None
            }
            
            # Clean None values
            metrics = {k: v for k, v in metrics.items() if v is not None and not np.isnan(v)}
            
            return metrics
            
        except Exception as e:
            self.logger.error(f'Error calculating risk metrics: {str(e)}')
            return {}
    
    def _calculate_max_drawdown(self, prices: np.ndarray) -> float:
        """Calculate maximum drawdown"""
        try:
            peak = np.maximum.accumulate(prices)
            drawdown = (prices - peak) / peak
            return float(np.min(drawdown))
        except:
            return 0.0
    
    def _generate_trading_signals(self, data: pd.DataFrame) -> Dict:
        """Generate trading signals based on technical analysis"""
        try:
            indicators = self._calculate_technical_indicators(data)
            patterns = self._detect_patterns(data)
            
            signals = {
                'overall_signal': 'neutral',
                'signal_strength': 0.0,
                'signals': []
            }
            
            signal_score = 0
            signal_count = 0
            
            # RSI signals
            if 'rsi' in indicators:
                rsi = indicators['rsi']
                if rsi < 30:
                    signals['signals'].append({'type': 'buy', 'reason': 'RSI oversold', 'strength': 0.7})
                    signal_score += 0.7
                elif rsi > 70:
                    signals['signals'].append({'type': 'sell', 'reason': 'RSI overbought', 'strength': 0.7})
                    signal_score -= 0.7
                signal_count += 1
            
            # MACD signals
            if all(k in indicators for k in ['macd', 'macd_signal']):
                if indicators['macd'] > indicators['macd_signal']:
                    signals['signals'].append({'type': 'buy', 'reason': 'MACD bullish crossover', 'strength': 0.6})
                    signal_score += 0.6
                else:
                    signals['signals'].append({'type': 'sell', 'reason': 'MACD bearish crossover', 'strength': 0.6})
                    signal_score -= 0.6
                signal_count += 1
            
            # Moving average signals
            if all(k in indicators for k in ['sma_20', 'sma_50']):
                if indicators['sma_20'] > indicators['sma_50']:
                    signals['signals'].append({'type': 'buy', 'reason': 'SMA 20 > SMA 50', 'strength': 0.5})
                    signal_score += 0.5
                else:
                    signals['signals'].append({'type': 'sell', 'reason': 'SMA 20 < SMA 50', 'strength': 0.5})
                    signal_score -= 0.5
                signal_count += 1
            
            # Pattern signals
            if patterns.get('engulfing_bullish'):
                signals['signals'].append({'type': 'buy', 'reason': 'Bullish engulfing pattern', 'strength': 0.8})
                signal_score += 0.8
                signal_count += 1
            elif patterns.get('engulfing_bearish'):
                signals['signals'].append({'type': 'sell', 'reason': 'Bearish engulfing pattern', 'strength': 0.8})
                signal_score -= 0.8
                signal_count += 1
            
            # Calculate overall signal
            if signal_count > 0:
                avg_score = signal_score / signal_count
                signals['signal_strength'] = abs(avg_score)
                
                if avg_score > 0.3:
                    signals['overall_signal'] = 'buy'
                elif avg_score < -0.3:
                    signals['overall_signal'] = 'sell'
                else:
                    signals['overall_signal'] = 'neutral'
            
            return signals
            
        except Exception as e:
            self.logger.error(f'Error generating trading signals: {str(e)}')
            return {'overall_signal': 'neutral', 'signal_strength': 0.0, 'signals': []}
    
    def _is_cached(self, cache_key: str) -> bool:
        """Check if data is cached and still valid"""
        if cache_key not in self.cache:
            return False
        
        cache_time = self.cache[cache_key]['timestamp']
        return (time.time() - cache_time) < self.cache_duration
    
    def _cache_data(self, cache_key: str, data: Dict):
        """Cache data with timestamp"""
        self.cache[cache_key] = {
            'data': data,
            'timestamp': time.time()
        }
    
    def _detect_doji(self, open_prices, high, low, close):
        """Detect Doji candlestick pattern"""
        if len(close) < 1:
            return False
        body = abs(close[-1] - open_prices[-1])
        range_val = high[-1] - low[-1]
        return body <= (range_val * 0.1) if range_val > 0 else False
    
    def _detect_hammer(self, open_prices, high, low, close):
        """Detect Hammer candlestick pattern"""
        if len(close) < 1:
            return False
        body = abs(close[-1] - open_prices[-1])
        lower_shadow = min(open_prices[-1], close[-1]) - low[-1]
        upper_shadow = high[-1] - max(open_prices[-1], close[-1])
        return lower_shadow >= (body * 2) and upper_shadow <= (body * 0.5)
    
    def _detect_shooting_star(self, open_prices, high, low, close):
        """Detect Shooting Star candlestick pattern"""
        if len(close) < 1:
            return False
        body = abs(close[-1] - open_prices[-1])
        upper_shadow = high[-1] - max(open_prices[-1], close[-1])
        lower_shadow = min(open_prices[-1], close[-1]) - low[-1]
        return upper_shadow >= (body * 2) and lower_shadow <= (body * 0.5)
    
    def _detect_bullish_engulfing(self, open_prices, high, low, close):
        """Detect Bullish Engulfing pattern"""
        if len(close) < 2:
            return False
        prev_bearish = close[-2] < open_prices[-2]
        curr_bullish = close[-1] > open_prices[-1]
        engulfing = open_prices[-1] < close[-2] and close[-1] > open_prices[-2]
        return prev_bearish and curr_bullish and engulfing
    
    def _detect_bearish_engulfing(self, open_prices, high, low, close):
        """Detect Bearish Engulfing pattern"""
        if len(close) < 2:
            return False
        prev_bullish = close[-2] > open_prices[-2]
        curr_bearish = close[-1] < open_prices[-1]
        engulfing = open_prices[-1] > close[-2] and close[-1] < open_prices[-2]
        return prev_bullish and curr_bearish and engulfing
    
    def _detect_morning_star(self, open_prices, high, low, close):
        """Detect Morning Star pattern"""
        if len(close) < 3:
            return False
        first_bearish = close[-3] < open_prices[-3]
        small_body = abs(close[-2] - open_prices[-2]) < abs(close[-3] - open_prices[-3]) * 0.5
        third_bullish = close[-1] > open_prices[-1]
        gap_down = high[-2] < min(open_prices[-3], close[-3])
        gap_up = low[-1] > max(open_prices[-2], close[-2])
        return first_bearish and small_body and third_bullish and gap_down and gap_up
    
    def _detect_evening_star(self, open_prices, high, low, close):
        """Detect Evening Star pattern"""
        if len(close) < 3:
            return False
        first_bullish = close[-3] > open_prices[-3]
        small_body = abs(close[-2] - open_prices[-2]) < abs(close[-3] - open_prices[-3]) * 0.5
        third_bearish = close[-1] < open_prices[-1]
        gap_up = low[-2] > max(open_prices[-3], close[-3])
        gap_down = high[-1] < min(open_prices[-2], close[-2])
        return first_bullish and small_body and third_bearish and gap_up and gap_down

# Global instance
technical_analysis_service = TechnicalAnalysisService()
