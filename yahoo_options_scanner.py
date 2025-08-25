#!/usr/bin/env python3
"""
Yahoo Finance Options Volume Scanner
Alternative scanner using Yahoo Finance for options data
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict
from tabulate import tabulate
from colorama import Fore, Style, init
from scipy.stats import norm
import math
import warnings
warnings.filterwarnings('ignore')

# Initialize colorama
init()

class YahooOptionsScanner:
    def __init__(self):
        """Initialize the scanner"""
        self.symbols = [
            'CHGG'
        ]
        self.risk_free_rate = 0.05  # 5% risk-free rate (approximate)
    
    def calculate_greeks(self, S, K, T, r, sigma, option_type='call'):
        """Calculate option Greeks using Black-Scholes model"""
        try:
            if T <= 0 or sigma <= 0:
                return {'delta': 0, 'gamma': 0, 'theta': 0, 'rho': 0}
            
            # Black-Scholes calculations
            d1 = (np.log(S/K) + (r + 0.5*sigma**2)*T) / (sigma*np.sqrt(T))
            d2 = d1 - sigma*np.sqrt(T)
            
            if option_type.lower() == 'call':
                delta = norm.cdf(d1)
                rho = K*T*np.exp(-r*T)*norm.cdf(d2) / 100
                theta = (-S*norm.pdf(d1)*sigma/(2*np.sqrt(T)) - r*K*np.exp(-r*T)*norm.cdf(d2)) / 365
            else:  # put
                delta = norm.cdf(d1) - 1
                rho = -K*T*np.exp(-r*T)*norm.cdf(-d2) / 100
                theta = (-S*norm.pdf(d1)*sigma/(2*np.sqrt(T)) + r*K*np.exp(-r*T)*norm.cdf(-d2)) / 365
            
            gamma = norm.pdf(d1) / (S*sigma*np.sqrt(T))
            
            return {
                'delta': round(delta, 4),
                'gamma': round(gamma, 4),
                'theta': round(theta, 4),
                'rho': round(rho, 4)
            }
        except:
            return {'delta': 0, 'gamma': 0, 'theta': 0, 'rho': 0}
    
    
    def get_options_data(self, symbol: str, volume_threshold: int = 100):
        """
        Get options data for a symbol with volume filtering and sentiment analysis
        """
        try:
            ticker = yf.Ticker(symbol)
            
            # Get current stock price and market cap
            stock_info = ticker.info
            current_price = stock_info.get('currentPrice') or stock_info.get('regularMarketPrice')
            market_cap = stock_info.get('marketCap', 0)
            
            if not current_price:
                # Fallback to recent price data
                hist = ticker.history(period="1d")
                if not hist.empty:
                    current_price = hist['Close'].iloc[-1]
                else:
                    print(f"Could not get current price for {symbol}")
                    return []
            
            # Get all expiration dates
            exp_dates = ticker.options
            if not exp_dates:
                print(f"No options data available for {symbol}")
                return []
            
            all_options = []
            total_call_volume = 0
            total_put_volume = 0
            total_call_oi = 0
            total_put_oi = 0
            
            for exp_date in exp_dates:
                try:
                    # Get options chain for this expiration
                    opt_chain = ticker.option_chain(exp_date)
                    
                    # Process calls
                    calls = opt_chain.calls
                    calls['type'] = 'CALL'
                    calls['expiration'] = exp_date
                    
                    # Process puts
                    puts = opt_chain.puts
                    puts['type'] = 'PUT'
                    puts['expiration'] = exp_date
                    
                    # Calculate volume totals for sentiment analysis
                    call_volume = calls['volume'].fillna(0).sum()
                    put_volume = puts['volume'].fillna(0).sum()
                    call_oi = calls['openInterest'].fillna(0).sum()
                    put_oi = puts['openInterest'].fillna(0).sum()
                    
                    total_call_volume += call_volume
                    total_put_volume += put_volume
                    total_call_oi += call_oi
                    total_put_oi += put_oi
                    
                    # Combine calls and puts
                    options = pd.concat([calls, puts], ignore_index=True)
                    
                    # Filter by volume
                    options = options[options['volume'] >= volume_threshold]
                    
                    if not options.empty:
                        # Calculate Greeks for each option
                        for idx, row in options.iterrows():
                            greeks = self.calculate_greeks(
                                current_price, row['strike'], (datetime.strptime(exp_date, '%Y-%m-%d') - datetime.now()).days / 365.0, 
                                self.risk_free_rate, row.get('impliedVolatility', 0.2), row['type']
                            )
                            options.at[idx, 'delta'] = greeks['delta']
                            options.at[idx, 'gamma'] = greeks['gamma']
                            options.at[idx, 'theta'] = greeks['theta']
                            options.at[idx, 'rho'] = greeks['rho']
                        
                        all_options.append(options)
                        
                except Exception as e:
                    print(f"Error processing {exp_date} for {symbol}: {e}")
                    continue
            
            if all_options:
                final_options = pd.concat(all_options, ignore_index=True)
                final_options['symbol'] = symbol
                final_options['current_stock_price'] = current_price
                
                # Add market data to each option record
                for idx in range(len(final_options)):
                    option_data = final_options.iloc[idx].to_dict()
                    option_data['market_cap'] = market_cap
                    option_data['current_price'] = current_price
                    final_options.iloc[idx] = option_data
                
                # Replace NaN values with None before converting to dict
                final_options = final_options.fillna(0)
                return final_options.to_dict('records')
            else:
                return []
                
        except Exception as e:
            print(f"Error getting options data for {symbol}: {e}")
            return []
    
    def scan_all_symbols(self, volume_threshold: int = 100) -> List[Dict]:
        """Scan all symbols for unusual options activity"""
        print(f"{Fore.GREEN}🔍 Starting Yahoo Finance Options Volume Scan{Style.RESET_ALL}")
        print(f"Volume threshold: {volume_threshold}+ contracts")
        print(f"Symbols: {', '.join(self.symbols)}\n")
        
        all_unusual_options = []
        
        for symbol in self.symbols:
            try:
                unusual_options = self.get_options_data(symbol, volume_threshold)
                all_unusual_options.extend(unusual_options)
            except Exception as e:
                print(f"{Fore.RED}Error scanning {symbol}: {str(e)}{Style.RESET_ALL}")
                continue
        
        return all_unusual_options
    
    def format_results(self, options_data: List[Dict]):
        """Format and display the results in a nice table"""
        if not options_data:
            print(f"{Fore.YELLOW}No unusual options activity found.{Style.RESET_ALL}")
            return
        
        # Create DataFrame for better formatting
        df = pd.DataFrame(options_data)
        
        # Sort by volume descending
        df = df.sort_values('volume', ascending=False)
        
        print(f"\n{Fore.GREEN}📊 UNUSUAL OPTIONS ACTIVITY DETECTED{Style.RESET_ALL}")
        print("=" * 140)
        
        # Group by symbol for better organization
        for symbol in df['symbol'].unique():
            symbol_data = df[df['symbol'] == symbol]
            first_row = symbol_data.iloc[0]
            
            # Display sentiment analysis
            sentiment_color = first_row.get('sentiment_color', '⚪')
            sentiment_label = first_row.get('sentiment_label', 'NEUTRAL')
            sentiment_score = first_row.get('sentiment_score', 50)
            cp_ratio = first_row.get('call_put_volume_ratio', 1.0)
            
            print(f"\n{Fore.CYAN}🔸 {symbol} (Current: ${first_row['current_stock_price']:.2f}){Style.RESET_ALL}")
            print(f"{sentiment_color} {Fore.MAGENTA}SENTIMENT: {sentiment_label} ({sentiment_score}/100) | C/P Ratio: {cp_ratio:.2f}{Style.RESET_ALL}")
            print("-" * 120)
            
            # Create table data
            table_data = []
            for _, row in symbol_data.iterrows():
                table_data.append([
                    row['expiration'],
                    f"${row['strike']:.2f}",
                    row['type'],
                    f"{row['volume']:,}",
                    f"{row.get('openInterest', row.get('open_interest', 0)):,}",
                    f"${row.get('bid', 0):.2f}",
                    f"${row.get('ask', 0):.2f}",
                    f"${row.get('lastPrice', row.get('last_price', 0)):.2f}",
                    f"{row.get('impliedVolatility', row.get('implied_volatility', 0)):.1%}",
                    f"{row['delta']:.3f}",
                    f"{row['gamma']:.4f}",
                    f"{row['theta']:.3f}",
                    f"{row['rho']:.3f}"
                ])
            
            headers = ['Exp', 'Strike', 'Type', 'Volume', 'OI', 'Bid', 'Ask', 'Last', 'IV', 'Δ', 'Γ', 'Θ', 'Ρ']
            
            print(tabulate(table_data, headers=headers, tablefmt='grid', stralign='center'))
            
            
        print(f"\n{Fore.GREEN}✅ Found {len(df)} options with unusual activity{Style.RESET_ALL}")
        print(f"{Fore.BLUE}💡 High volume may indicate significant market moves or institutional activity{Style.RESET_ALL}")

    def scan_custom_symbols(self, symbols: List[str], volume_threshold: int = 100) -> List[Dict]:
        """Scan custom list of symbols for unusual options activity"""
        print(f"{Fore.GREEN}🔍 Starting Custom Options Volume Scan{Style.RESET_ALL}")
        print(f"Volume threshold: {volume_threshold}+ contracts")
        print(f"Symbols: {', '.join(symbols)}\n")
        
        all_unusual_options = []
        
        for symbol in symbols:
            try:
                unusual_options = self.get_options_data(symbol.upper(), volume_threshold)
                all_unusual_options.extend(unusual_options)
            except Exception as e:
                print(f"{Fore.RED}Error scanning {symbol}: {str(e)}{Style.RESET_ALL}")
                continue
        
        return all_unusual_options

def main():
    """Main function"""
    scanner = YahooOptionsScanner()
    
    print(f"{Fore.BLUE}Yahoo Finance Options Volume Scanner{Style.RESET_ALL}")
    print("=" * 50)
    
    # Ask user for scan type
    print(f"{Fore.CYAN}Choose scan type:{Style.RESET_ALL}")
    print("1. Scan all default symbols (20 popular stocks)")
    print("2. Scan specific symbols")
    
    choice = input("\nEnter your choice (1 or 2): ").strip()
    
    # Get volume threshold
    volume_input = input("Enter volume threshold (default 100): ").strip()
    volume_threshold = int(volume_input) if volume_input.isdigit() else 100
    
    try:
        if choice == "2":
            # Custom symbols
            print(f"\n{Fore.YELLOW}Enter symbols separated by commas (e.g., AAPL,TSLA,NVDA):{Style.RESET_ALL}")
            symbols_input = input("Symbols: ").strip().upper()
            
            if not symbols_input:
                print(f"{Fore.RED}No symbols entered. Exiting.{Style.RESET_ALL}")
                return
            
            custom_symbols = [s.strip() for s in symbols_input.split(',') if s.strip()]
            unusual_options = scanner.scan_custom_symbols(custom_symbols, volume_threshold)
        else:
            # Default symbols
            unusual_options = scanner.scan_all_symbols(volume_threshold)
        
        # Display results
        scanner.format_results(unusual_options)
        
        print(f"\n{Fore.GREEN}✅ Scan completed successfully!{Style.RESET_ALL}")
        
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Scan interrupted by user{Style.RESET_ALL}")
    except Exception as e:
        print(f"\n{Fore.RED}Unexpected error: {str(e)}{Style.RESET_ALL}")

if __name__ == "__main__":
    main()
