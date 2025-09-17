#!/usr/bin/env python3
"""
Stock Symbols Service
Provides stock symbol validation and autocomplete suggestions
"""

import yfinance as yf
import pandas as pd
import json
import os
from typing import List, Dict, Optional
import logging

class StockSymbolsService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.symbols_cache = {}
        self.load_popular_symbols()
    
    def load_popular_symbols(self):
        """Load popular stock symbols for quick access"""
        # Popular stocks with company names for autocomplete
        self.popular_symbols = {
            # Tech Giants
            'AAPL': 'Apple Inc.',
            'MSFT': 'Microsoft Corporation',
            'GOOGL': 'Alphabet Inc. Class A',
            'GOOG': 'Alphabet Inc. Class C',
            'AMZN': 'Amazon.com Inc.',
            'META': 'Meta Platforms Inc.',
            'TSLA': 'Tesla Inc.',
            'NVDA': 'NVIDIA Corporation',
            'NFLX': 'Netflix Inc.',
            'CRM': 'Salesforce Inc.',
            'ORCL': 'Oracle Corporation',
            'ADBE': 'Adobe Inc.',
            'INTC': 'Intel Corporation',
            'AMD': 'Advanced Micro Devices Inc.',
            'PYPL': 'PayPal Holdings Inc.',
            'UBER': 'Uber Technologies Inc.',
            'LYFT': 'Lyft Inc.',
            'SNAP': 'Snap Inc.',
            'TWTR': 'Twitter Inc.',
            'SPOT': 'Spotify Technology S.A.',
            
            # Financial
            'JPM': 'JPMorgan Chase & Co.',
            'BAC': 'Bank of America Corporation',
            'WFC': 'Wells Fargo & Company',
            'GS': 'The Goldman Sachs Group Inc.',
            'MS': 'Morgan Stanley',
            'C': 'Citigroup Inc.',
            'V': 'Visa Inc.',
            'MA': 'Mastercard Incorporated',
            'AXP': 'American Express Company',
            'BRK.A': 'Berkshire Hathaway Inc. Class A',
            'BRK.B': 'Berkshire Hathaway Inc. Class B',
            
            # Healthcare & Pharma
            'JNJ': 'Johnson & Johnson',
            'PFE': 'Pfizer Inc.',
            'UNH': 'UnitedHealth Group Incorporated',
            'MRNA': 'Moderna Inc.',
            'BNTX': 'BioNTech SE',
            'ABT': 'Abbott Laboratories',
            'TMO': 'Thermo Fisher Scientific Inc.',
            'DHR': 'Danaher Corporation',
            'BMY': 'Bristol-Myers Squibb Company',
            'AMGN': 'Amgen Inc.',
            
            # Consumer & Retail
            'WMT': 'Walmart Inc.',
            'HD': 'The Home Depot Inc.',
            'PG': 'The Procter & Gamble Company',
            'KO': 'The Coca-Cola Company',
            'PEP': 'PepsiCo Inc.',
            'MCD': 'McDonald\'s Corporation',
            'SBUX': 'Starbucks Corporation',
            'NKE': 'NIKE Inc.',
            'DIS': 'The Walt Disney Company',
            'COST': 'Costco Wholesale Corporation',
            
            # Energy & Utilities
            'XOM': 'Exxon Mobil Corporation',
            'CVX': 'Chevron Corporation',
            'COP': 'ConocoPhillips',
            'SLB': 'Schlumberger Limited',
            'NEE': 'NextEra Energy Inc.',
            'DUK': 'Duke Energy Corporation',
            
            # Industrial & Materials
            'BA': 'The Boeing Company',
            'CAT': 'Caterpillar Inc.',
            'GE': 'General Electric Company',
            'MMM': '3M Company',
            'HON': 'Honeywell International Inc.',
            'LMT': 'Lockheed Martin Corporation',
            
            # ETFs
            'SPY': 'SPDR S&P 500 ETF Trust',
            'QQQ': 'Invesco QQQ Trust',
            'IWM': 'iShares Russell 2000 ETF',
            'VTI': 'Vanguard Total Stock Market ETF',
            'VOO': 'Vanguard S&P 500 ETF',
            'VEA': 'Vanguard FTSE Developed Markets ETF',
            'VWO': 'Vanguard FTSE Emerging Markets ETF',
            'GLD': 'SPDR Gold Shares',
            'SLV': 'iShares Silver Trust',
            'TLT': 'iShares 20+ Year Treasury Bond ETF',
            'HYG': 'iShares iBoxx $ High Yield Corporate Bond ETF',
            'XLF': 'Financial Select Sector SPDR Fund',
            'XLK': 'Technology Select Sector SPDR Fund',
            'XLE': 'Energy Select Sector SPDR Fund',
            'XLV': 'Health Care Select Sector SPDR Fund',
            'XLI': 'Industrial Select Sector SPDR Fund',
            'XLP': 'Consumer Staples Select Sector SPDR Fund',
            'XLY': 'Consumer Discretionary Select Sector SPDR Fund',
            'XLU': 'Utilities Select Sector SPDR Fund',
            'XLB': 'Materials Select Sector SPDR Fund',
            'XLRE': 'Real Estate Select Sector SPDR Fund',
            
            # Crypto-related
            'COIN': 'Coinbase Global Inc.',
            'MSTR': 'MicroStrategy Incorporated',
            'SQ': 'Block Inc.',
            'RIOT': 'Riot Platforms Inc.',
            'MARA': 'Marathon Digital Holdings Inc.',
            
            # Meme Stocks & Popular Trading
            'GME': 'GameStop Corp.',
            'AMC': 'AMC Entertainment Holdings Inc.',
            'BB': 'BlackBerry Limited',
            'NOK': 'Nokia Corporation',
            'PLTR': 'Palantir Technologies Inc.',
            'WISH': 'ContextLogic Inc.',
            'CLOV': 'Clover Health Investments Corp.',
            'SPCE': 'Virgin Galactic Holdings Inc.',
            'NIO': 'NIO Inc.',
            'XPEV': 'XPeng Inc.',
            'LI': 'Li Auto Inc.',
            'RIVN': 'Rivian Automotive Inc.',
            'LCID': 'Lucid Group Inc.',
        }
    
    def validate_symbol(self, symbol: str) -> Dict:
        """Validate if a stock symbol exists and get basic info"""
        try:
            symbol = symbol.upper().strip()
            
            # Check if it's in our popular symbols first
            if symbol in self.popular_symbols:
                return {
                    'valid': True,
                    'symbol': symbol,
                    'name': self.popular_symbols[symbol],
                    'source': 'cache'
                }
            
            # Try to fetch from Yahoo Finance
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Check if we got valid data
            if info and ('longName' in info or 'shortName' in info):
                company_name = info.get('longName', info.get('shortName', symbol))
                return {
                    'valid': True,
                    'symbol': symbol,
                    'name': company_name,
                    'sector': info.get('sector', ''),
                    'industry': info.get('industry', ''),
                    'market_cap': info.get('marketCap', 0),
                    'source': 'yfinance'
                }
            else:
                return {
                    'valid': False,
                    'symbol': symbol,
                    'error': 'Symbol not found'
                }
                
        except Exception as e:
            self.logger.error(f'Error validating symbol {symbol}: {str(e)}')
            return {
                'valid': False,
                'symbol': symbol,
                'error': str(e)
            }
    
    def get_suggestions(self, query: str, limit: int = 10) -> List[Dict]:
        """Get stock symbol suggestions based on query"""
        try:
            query = query.upper().strip()
            suggestions = []
            
            if not query:
                # Return popular symbols if no query
                popular_list = list(self.popular_symbols.items())[:limit]
                return [
                    {
                        'symbol': symbol,
                        'name': name,
                        'match_type': 'popular'
                    }
                    for symbol, name in popular_list
                ]
            
            # Search in popular symbols first
            for symbol, name in self.popular_symbols.items():
                if len(suggestions) >= limit:
                    break
                    
                # Match by symbol
                if symbol.startswith(query):
                    suggestions.append({
                        'symbol': symbol,
                        'name': name,
                        'match_type': 'symbol_start',
                        'score': 100
                    })
                elif query in symbol:
                    suggestions.append({
                        'symbol': symbol,
                        'name': name,
                        'match_type': 'symbol_contains',
                        'score': 80
                    })
                # Match by company name
                elif query in name.upper():
                    suggestions.append({
                        'symbol': symbol,
                        'name': name,
                        'match_type': 'name_contains',
                        'score': 60
                    })
            
            # Sort by score and match type priority
            suggestions.sort(key=lambda x: (-x['score'], x['symbol']))
            
            return suggestions[:limit]
            
        except Exception as e:
            self.logger.error(f'Error getting suggestions for query {query}: {str(e)}')
            return []
    
    def get_symbol_info(self, symbol: str) -> Dict:
        """Get comprehensive information about a stock symbol"""
        try:
            symbol = symbol.upper().strip()
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            if not info or not info.get('longName'):
                return {'error': 'Symbol not found'}
            
            # Get historical data for additional metrics
            hist_1y = ticker.history(period="1y")
            hist_5d = ticker.history(period="5d")
            
            result = {
                'symbol': symbol,
                'name': info.get('longName', ''),
                'sector': info.get('sector', ''),
                'industry': info.get('industry', ''),
                'market_cap': info.get('marketCap', 0),
                'current_price': info.get('currentPrice', 0),
                'previous_close': info.get('previousClose', 0),
                'day_high': info.get('dayHigh', 0),
                'day_low': info.get('dayLow', 0),
                'fifty_two_week_high': info.get('fiftyTwoWeekHigh', 0),
                'fifty_two_week_low': info.get('fiftyTwoWeekLow', 0),
                'volume': info.get('volume', 0),
                'avg_volume': info.get('averageVolume', 0),
                'pe_ratio': info.get('trailingPE', 0),
                'forward_pe': info.get('forwardPE', 0),
                'dividend_yield': info.get('dividendYield', 0),
                'beta': info.get('beta', 0),
                'earnings_date': info.get('earningsDate', None),
                'exchange': info.get('exchange', ''),
                'currency': info.get('currency', 'USD')
            }
            
            # Add volatility calculation if we have historical data
            if not hist_5d.empty:
                returns = hist_5d['Close'].pct_change().dropna()
                if len(returns) > 1:
                    result['volatility_5d'] = float(returns.std() * (252**0.5))  # Annualized
            
            return result
            
        except Exception as e:
            self.logger.error(f'Error getting symbol info for {symbol}: {str(e)}')
            return {'error': str(e)}
    
    def batch_validate(self, symbols: List[str]) -> Dict[str, Dict]:
        """Validate multiple symbols at once"""
        results = {}
        for symbol in symbols:
            results[symbol] = self.validate_symbol(symbol)
        return results

# Global instance
stock_symbols_service = StockSymbolsService()
