#!/usr/bin/env python3
"""
Quick Options Scanner - Enter symbols directly
"""

import sys
from yahoo_options_scanner import YahooOptionsScanner

def quick_scan(symbols_str, volume_threshold=100):
    """Quick scan with symbols as command line argument"""
    scanner = YahooOptionsScanner()
    
    # Parse symbols
    symbols = [s.strip().upper() for s in symbols_str.split(',') if s.strip()]
    
    if not symbols:
        print("No valid symbols provided")
        return
    
    print(f"🔍 Quick scanning: {', '.join(symbols)}")
    print(f"Volume threshold: {volume_threshold}+\n")
    
    # Scan
    unusual_options = scanner.scan_custom_symbols(symbols, volume_threshold)
    
    # Display results
    scanner.format_results(unusual_options)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 quick_scan.py 'AAPL,TSLA,NVDA' [volume_threshold]")
        print("Example: python3 quick_scan.py 'AAPL,TSLA,NVDA' 50")
        sys.exit(1)
    
    symbols = sys.argv[1]
    volume_threshold = int(sys.argv[2]) if len(sys.argv) > 2 else 100
    
    quick_scan(symbols, volume_threshold)
