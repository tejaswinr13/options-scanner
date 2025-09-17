#!/usr/bin/env python3
"""
Options Analytics Service
Provides comprehensive options data analysis including Greeks, volatility, and flow analysis
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional
from scipy.stats import norm
import math
import json

class OptionsAnalyticsService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def get_options_chain(self, symbol: str) -> Dict:
        """Get comprehensive options chain data for a symbol"""
        try:
            ticker = yf.Ticker(symbol)
            
            # Get current stock price
            info = ticker.info
            current_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
            
            # Get options expiration dates
            expirations = ticker.options
            
            if not expirations:
                return {'error': 'No options data available for this symbol'}
            
            options_data = {
                'symbol': symbol,
                'current_price': current_price,
                'expirations': list(expirations),
                'chains': {},
                'analytics': {}
            }
            
            # Process each expiration date (limit to first 6 for performance)
            for expiration in expirations[:6]:
                try:
                    chain = ticker.option_chain(expiration)
                    calls = chain.calls
                    puts = chain.puts
                    
                    # Calculate Greeks and additional metrics
                    calls_enhanced = self._enhance_options_data(calls, current_price, expiration, 'call')
                    puts_enhanced = self._enhance_options_data(puts, current_price, expiration, 'put')
                    
                    # Convert to JSON-serializable format
                    calls_records = self._convert_to_json_serializable(calls_enhanced.to_dict('records')) if not calls_enhanced.empty else []
                    puts_records = self._convert_to_json_serializable(puts_enhanced.to_dict('records')) if not puts_enhanced.empty else []
                    
                    options_data['chains'][expiration] = {
                        'calls': calls_records,
                        'puts': puts_records,
                        'expiration_date': expiration,
                        'days_to_expiry': self._calculate_days_to_expiry(expiration)
                    }
                    
                except Exception as e:
                    self.logger.error(f'Error processing expiration {expiration}: {str(e)}')
                    continue
            
            # Calculate overall options analytics
            analytics = self._calculate_options_analytics(options_data['chains'], current_price)
            options_data['analytics'] = self._convert_to_json_serializable(analytics)
            
            return options_data
            
        except Exception as e:
            self.logger.error(f'Error getting options chain for {symbol}: {str(e)}')
            return {'error': str(e)}
    
    def _enhance_options_data(self, options_df: pd.DataFrame, current_price: float, expiration: str, option_type: str) -> pd.DataFrame:
        """Enhance options data with Greeks and additional metrics"""
        if options_df.empty:
            return options_df
        
        try:
            # Calculate time to expiration in years
            days_to_expiry = self._calculate_days_to_expiry(expiration)
            time_to_expiry = days_to_expiry / 365.0
            
            # Risk-free rate (approximate)
            risk_free_rate = 0.05
            
            enhanced_df = options_df.copy()
            
            # Calculate implied volatility if not available
            if 'impliedVolatility' not in enhanced_df.columns:
                enhanced_df['impliedVolatility'] = 0.3  # Default IV
            
            # Calculate Greeks
            greeks = []
            for _, row in enhanced_df.iterrows():
                strike = row['strike']
                iv = row.get('impliedVolatility', 0.3)
                
                if iv > 0 and time_to_expiry > 0:
                    greek_values = self._calculate_greeks(
                        current_price, strike, time_to_expiry, risk_free_rate, iv, option_type
                    )
                else:
                    greek_values = {'delta': 0, 'gamma': 0, 'theta': 0, 'vega': 0, 'rho': 0}
                
                greeks.append(greek_values)
            
            # Add Greeks to dataframe
            greeks_df = pd.DataFrame(greeks)
            enhanced_df = pd.concat([enhanced_df, greeks_df], axis=1)
            
            # Calculate additional metrics
            enhanced_df['moneyness'] = enhanced_df['strike'] / current_price
            enhanced_df['intrinsic_value'] = enhanced_df.apply(
                lambda row: max(0, current_price - row['strike']) if option_type == 'call' 
                else max(0, row['strike'] - current_price), axis=1
            )
            enhanced_df['time_value'] = enhanced_df['lastPrice'] - enhanced_df['intrinsic_value']
            enhanced_df['days_to_expiry'] = days_to_expiry
            
            # Volume and open interest analysis
            enhanced_df['volume_oi_ratio'] = enhanced_df['volume'] / enhanced_df['openInterest'].replace(0, 1)
            enhanced_df['liquidity_score'] = self._calculate_liquidity_score(enhanced_df)
            
            return enhanced_df
            
        except Exception as e:
            self.logger.error(f'Error enhancing options data: {str(e)}')
            return options_df
    
    def _calculate_greeks(self, S: float, K: float, T: float, r: float, sigma: float, option_type: str) -> Dict:
        """Calculate Black-Scholes Greeks"""
        try:
            if T <= 0 or sigma <= 0:
                return {'delta': 0, 'gamma': 0, 'theta': 0, 'vega': 0, 'rho': 0}
            
            d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
            d2 = d1 - sigma * np.sqrt(T)
            
            if option_type == 'call':
                delta = norm.cdf(d1)
                rho = K * T * np.exp(-r * T) * norm.cdf(d2) / 100
                theta = (-S * norm.pdf(d1) * sigma / (2 * np.sqrt(T)) - 
                        r * K * np.exp(-r * T) * norm.cdf(d2)) / 365
            else:  # put
                delta = -norm.cdf(-d1)
                rho = -K * T * np.exp(-r * T) * norm.cdf(-d2) / 100
                theta = (-S * norm.pdf(d1) * sigma / (2 * np.sqrt(T)) + 
                        r * K * np.exp(-r * T) * norm.cdf(-d2)) / 365
            
            gamma = norm.pdf(d1) / (S * sigma * np.sqrt(T))
            vega = S * norm.pdf(d1) * np.sqrt(T) / 100
            
            return {
                'delta': round(delta, 4),
                'gamma': round(gamma, 4),
                'theta': round(theta, 4),
                'vega': round(vega, 4),
                'rho': round(rho, 4)
            }
            
        except Exception as e:
            self.logger.error(f'Error calculating Greeks: {str(e)}')
            return {'delta': 0, 'gamma': 0, 'theta': 0, 'vega': 0, 'rho': 0}
    
    def _calculate_days_to_expiry(self, expiration_str: str) -> int:
        """Calculate days to expiration"""
        try:
            expiration_date = datetime.strptime(expiration_str, '%Y-%m-%d')
            today = datetime.now()
            return max(0, (expiration_date - today).days)
        except:
            return 0
    
    def _calculate_liquidity_score(self, df: pd.DataFrame) -> pd.Series:
        """Calculate liquidity score based on volume and open interest"""
        try:
            volume_score = np.log1p(df['volume']) / 10
            oi_score = np.log1p(df['openInterest']) / 10
            bid_ask_spread = (df['ask'] - df['bid']) / df['lastPrice'].replace(0, 1)
            spread_score = np.maximum(0, 1 - bid_ask_spread)
            
            liquidity_score = (volume_score + oi_score + spread_score) / 3
            return np.clip(liquidity_score, 0, 1)
        except:
            return pd.Series([0.5] * len(df))
    
    def _calculate_options_analytics(self, chains: Dict, current_price: float) -> Dict:
        """Calculate overall options analytics"""
        try:
            analytics = {
                'total_call_volume': 0,
                'total_put_volume': 0,
                'total_call_oi': 0,
                'total_put_oi': 0,
                'put_call_ratio': 0,
                'max_pain': 0,
                'gamma_exposure': 0,
                'implied_volatility_rank': 0,
                'most_active_strikes': [],
                'unusual_activity': []
            }
            
            all_calls = []
            all_puts = []
            
            # Aggregate data from all expirations
            for expiration, chain_data in chains.items():
                all_calls.extend(chain_data['calls'])
                all_puts.extend(chain_data['puts'])
            
            if all_calls:
                calls_df = pd.DataFrame(all_calls)
                analytics['total_call_volume'] = calls_df['volume'].fillna(0).sum()
                analytics['total_call_oi'] = calls_df['openInterest'].fillna(0).sum()
            
            if all_puts:
                puts_df = pd.DataFrame(all_puts)
                analytics['total_put_volume'] = puts_df['volume'].fillna(0).sum()
                analytics['total_put_oi'] = puts_df['openInterest'].fillna(0).sum()
            
            # Calculate put/call ratio
            if analytics['total_call_volume'] > 0:
                analytics['put_call_ratio'] = analytics['total_put_volume'] / analytics['total_call_volume']
            
            # Calculate max pain (simplified)
            analytics['max_pain'] = self._calculate_max_pain(all_calls, all_puts, current_price)
            
            # Find most active strikes
            analytics['most_active_strikes'] = self._find_most_active_strikes(all_calls, all_puts)
            
            # Detect unusual activity
            analytics['unusual_activity'] = self._detect_unusual_activity(all_calls, all_puts)
            
            return analytics
            
        except Exception as e:
            self.logger.error(f'Error calculating options analytics: {str(e)}')
            return {}
    
    def _calculate_max_pain(self, calls: List, puts: List, current_price: float) -> float:
        """Calculate max pain point (simplified version)"""
        try:
            if not calls and not puts:
                return current_price
            
            # Get all strikes
            strikes = set()
            if calls:
                strikes.update([c.get('strike') for c in calls if c.get('strike') is not None])
            if puts:
                strikes.update([p.get('strike') for p in puts if p.get('strike') is not None])
            
            if not strikes:
                return current_price
            
            min_strike = min(strikes)
            max_strike = max(strikes)
            
            # Test strikes around current price
            test_strikes = np.linspace(min_strike, max_strike, 50)
            min_pain = float('inf')
            max_pain_strike = current_price
            
            for strike in test_strikes:
                total_pain = 0
                
                # Calculate pain for calls
                for call in calls:
                    call_strike = call.get('strike', 0)
                    call_oi = call.get('openInterest', 0)
                    if call_strike and call_oi and strike > call_strike:
                        total_pain += (strike - call_strike) * call_oi
                
                # Calculate pain for puts
                for put in puts:
                    put_strike = put.get('strike', 0)
                    put_oi = put.get('openInterest', 0)
                    if put_strike and put_oi and strike < put_strike:
                        total_pain += (put_strike - strike) * put_oi
                
                if total_pain < min_pain:
                    min_pain = total_pain
                    max_pain_strike = strike
            
            return round(max_pain_strike, 2)
            
        except Exception as e:
            self.logger.error(f'Error calculating max pain: {str(e)}')
            return current_price
    
    def _find_most_active_strikes(self, calls: List, puts: List) -> List:
        """Find most active option strikes by volume"""
        try:
            strike_activity = {}
            
            # Aggregate call activity
            for call in calls:
                strike = call.get('strike')
                volume = call.get('volume', 0)
                if strike is not None and volume is not None:
                    if strike not in strike_activity:
                        strike_activity[strike] = {'volume': 0, 'type': 'mixed'}
                    strike_activity[strike]['volume'] += volume
            
            # Aggregate put activity
            for put in puts:
                strike = put.get('strike')
                volume = put.get('volume', 0)
                if strike is not None and volume is not None:
                    if strike not in strike_activity:
                        strike_activity[strike] = {'volume': 0, 'type': 'mixed'}
                    strike_activity[strike]['volume'] += volume
            
            # Sort by volume and return top 10
            sorted_strikes = sorted(
                strike_activity.items(), 
                key=lambda x: x[1]['volume'], 
                reverse=True
            )[:10]
            
            return [
                {
                    'strike': strike,
                    'volume': data['volume'],
                    'type': data['type']
                }
                for strike, data in sorted_strikes
            ]
            
        except Exception as e:
            self.logger.error(f'Error finding most active strikes: {str(e)}')
            return []
    
    def _detect_unusual_activity(self, calls: List, puts: List) -> List:
        """Detect unusual options activity"""
        try:
            unusual_activity = []
            
            # Combine all options
            all_options = []
            for call in calls:
                call_copy = call.copy()
                call_copy['type'] = 'call'
                all_options.append(call_copy)
            for put in puts:
                put_copy = put.copy()
                put_copy['type'] = 'put'
                all_options.append(put_copy)
            
            if not all_options:
                return unusual_activity
            
            # Calculate volume percentiles - handle None values
            volumes = []
            for opt in all_options:
                vol = opt.get('volume', 0)
                if vol is not None and vol > 0:
                    volumes.append(vol)
            
            if not volumes:
                return unusual_activity
            
            volume_95th = np.percentile(volumes, 95)
            
            # Find options with unusual volume
            for option in all_options:
                volume = option.get('volume', 0)
                open_interest = option.get('openInterest', 0)
                
                if volume is not None and volume >= volume_95th and volume > 100:
                    unusual_activity.append({
                        'strike': option.get('strike', 0),
                        'type': option.get('type', 'unknown'),
                        'volume': volume,
                        'open_interest': open_interest or 0,
                        'last_price': option.get('lastPrice', 0),
                        'volume_oi_ratio': volume / max(1, open_interest or 1)
                    })
            
            # Sort by volume and limit to top 20
            unusual_activity.sort(key=lambda x: x['volume'], reverse=True)
            return unusual_activity[:20]
            
        except Exception as e:
            self.logger.error(f'Error detecting unusual activity: {str(e)}')
            return []
    
    def _convert_to_json_serializable(self, data):
        """Convert numpy/pandas data types to JSON-serializable types"""
        if isinstance(data, list):
            return [self._convert_to_json_serializable(item) for item in data]
        elif isinstance(data, dict):
            return {key: self._convert_to_json_serializable(value) for key, value in data.items()}
        elif isinstance(data, (np.integer, np.int64, np.int32)):
            return int(data)
        elif isinstance(data, (np.floating, np.float64, np.float32)):
            return float(data)
        elif pd.isna(data) or data is None:
            return None
        elif hasattr(data, 'item'):  # Handle numpy scalars
            return data.item()
        else:
            return data

# Global instance
options_analytics_service = OptionsAnalyticsService()
