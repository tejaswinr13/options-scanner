#!/usr/bin/env python3
"""
Options Scanner Web UI
Flask web application for the Yahoo Finance Options Scanner
"""

from flask import Flask, render_template, request, jsonify, make_response
from yahoo_options_scanner import YahooOptionsScanner
from options_simulator import OptionsSimulator
from dark_pool_scanner import DarkPoolScanner
from economic_data_service import economic_service
from stock_symbols_service import stock_symbols_service
from enhanced_stock_service import enhanced_stock_service
from options_analytics_service import OptionsAnalyticsService
from news_service import NewsService
from technical_analysis_service import TechnicalAnalysisService
from fundamental_analysis_service import fundamental_service
import threading
import time
import logging
from logging.handlers import RotatingFileHandler
import os

app = Flask(__name__)

# Setup logging
if not os.path.exists('logs'):
    os.makedirs('logs')

if not app.debug:
    file_handler = RotatingFileHandler('logs/options_scanner.log', maxBytes=10240000, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('Options Scanner startup')

# Global variables for storing scan results and simulator
scan_results = {}
scan_status = {"running": False, "progress": "", "error": None}
simulator = OptionsSimulator()

# Dark pool scanner globals
dark_pool_results = {}
dark_pool_status = {"running": False, "progress": "", "error": None}
dark_pool_scanner = DarkPoolScanner()

# Initialize services
options_service = OptionsAnalyticsService()
news_service = NewsService()
technical_service = TechnicalAnalysisService()

@app.route('/')
def index():
    """Main page"""
    response = make_response(render_template('index.html'))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/favicon.ico')
def favicon():
    """Serve favicon"""
    return app.send_static_file('favicon.ico')

@app.route('/debug_test.html')
def debug_test():
    """Debug test page"""
    with open('debug_test.html', 'r') as f:
        content = f.read()
    response = make_response(content)
    response.headers['Content-Type'] = 'text/html'
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/dark-pool')
def dark_pool():
    return render_template('dark_pool.html')

@app.route('/economic-dashboard')
def economic_dashboard():
    return render_template('economic_dashboard.html')

@app.route('/ticker')
def ticker():
    """Real-time stock ticker page"""
    import time
    cache_buster = int(time.time())
    return render_template('ticker_new.html', cache_buster=cache_buster)

@app.route('/ticker-fresh')
def ticker_fresh():
    """Fresh ticker page to bypass cache"""
    import time
    cache_buster = int(time.time())
    return render_template('ticker_new.html', cache_buster=cache_buster)

@app.route('/ticker-v3')
def ticker_v3():
    """Completely new ticker page to bypass all caching"""
    import time
    cache_buster = int(time.time())
    response = make_response(render_template('ticker_v3.html', cache_buster=cache_buster))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/dashboard')
def dashboard():
    """Main dashboard with seamless stock scroller and link tiles"""
    import time
    cache_buster = int(time.time())
    response = make_response(render_template('dashboard.html', cache_buster=cache_buster))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/stock/<symbol>')
def stock_detail(symbol):
    """Detailed stock analysis page"""
    import time
    cache_buster = int(time.time())
    response = make_response(render_template('stock_detail.html', symbol=symbol.upper(), cache_buster=cache_buster))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/api/economic-data')
def get_economic_data():
    """API endpoint to fetch real-time economic data"""
    try:
        data = economic_service.get_all_dashboard_data()
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ticker-prices', methods=['POST'])
def get_ticker_prices():
    """API endpoint to fetch real-time stock prices with VWAP, RSI, and Level 2 data"""
    try:
        import yfinance as yf
        import time
        import pandas as pd
        import numpy as np
        
        data = request.get_json()
        symbols = data.get('symbols', [])
        
        if not symbols:
            return jsonify({'error': 'No symbols provided'}), 400
        
        app.logger.info(f'Fetching enhanced ticker data for symbols: {symbols}')
        
        def calculate_rsi(prices, period=14):
            """Calculate RSI (Relative Strength Index)"""
            if len(prices) < period + 1:
                return 50  # Default neutral RSI
            
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return round(rsi.iloc[-1], 2) if not pd.isna(rsi.iloc[-1]) else 50
        
        def calculate_sma(prices, period):
            """Calculate Simple Moving Average"""
            if len(prices) < period:
                return 0
            sma = prices.rolling(window=period).mean()
            return round(sma.iloc[-1], 2) if not pd.isna(sma.iloc[-1]) else 0
        
        def calculate_macd(prices, fast=12, slow=26, signal=9):
            """Calculate MACD (Moving Average Convergence Divergence)"""
            if len(prices) < slow + signal:
                return {'macd': 0, 'signal': 0, 'histogram': 0}
            
            ema_fast = prices.ewm(span=fast).mean()
            ema_slow = prices.ewm(span=slow).mean()
            macd_line = ema_fast - ema_slow
            signal_line = macd_line.ewm(span=signal).mean()
            histogram = macd_line - signal_line
            
            return {
                'macd': round(macd_line.iloc[-1], 4) if not pd.isna(macd_line.iloc[-1]) else 0,
                'signal': round(signal_line.iloc[-1], 4) if not pd.isna(signal_line.iloc[-1]) else 0,
                'histogram': round(histogram.iloc[-1], 4) if not pd.isna(histogram.iloc[-1]) else 0
            }
        
        def calculate_vwap(hist_data):
            """Calculate VWAP (Volume Weighted Average Price)"""
            if hist_data.empty or 'Volume' not in hist_data.columns:
                return 0
            
            typical_price = (hist_data['High'] + hist_data['Low'] + hist_data['Close']) / 3
            vwap = (typical_price * hist_data['Volume']).sum() / hist_data['Volume'].sum()
            return round(vwap, 2) if not pd.isna(vwap) else 0
        
        def get_level2_data(ticker_obj, symbol):
            """Simulate Level 2 order book data (Yahoo Finance doesn't provide real Level 2)"""
            try:
                info = ticker_obj.info
                current_price = info.get('currentPrice', info.get('regularMarketPrice', 100))
                bid = info.get('bid', current_price * 0.999)
                ask = info.get('ask', current_price * 1.001)
                bid_size = info.get('bidSize', 100)
                ask_size = info.get('askSize', 100)
                
                # Generate simulated Level 2 data around current bid/ask
                level2 = {
                    'bids': [
                        {'price': round(bid, 2), 'size': bid_size},
                        {'price': round(bid - 0.01, 2), 'size': bid_size * 1.5},
                        {'price': round(bid - 0.02, 2), 'size': bid_size * 0.8}
                    ],
                    'asks': [
                        {'price': round(ask, 2), 'size': ask_size},
                        {'price': round(ask + 0.01, 2), 'size': ask_size * 1.2},
                        {'price': round(ask + 0.02, 2), 'size': ask_size * 0.9}
                    ]
                }
                return level2
            except:
                return {'bids': [], 'asks': []}
        
        stocks_data = {}
        
        for symbol in symbols:
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.info
                
                # Get intraday data for VWAP and RSI calculations
                hist_1d = ticker.history(period="1d", interval="1m")
                hist_5d = ticker.history(period="5d", interval="5m")
                hist_200d = ticker.history(period="200d", interval="1d")  # For SMA 200
                
                current_price = 0
                prev_close = info.get('previousClose', 0)
                vwap = 0
                rsi = 50
                sma_20 = 0
                sma_50 = 0
                sma_200 = 0
                macd_data = {'macd': 0, 'signal': 0, 'histogram': 0}
                
                if not hist_1d.empty:
                    current_price = hist_1d['Close'].iloc[-1]
                    vwap = calculate_vwap(hist_1d)
                    
                    # Use 5-day data for RSI if available, otherwise 1-day
                    rsi_data = hist_5d['Close'] if not hist_5d.empty else hist_1d['Close']
                    rsi = calculate_rsi(rsi_data)
                    
                    # Calculate SMAs using appropriate data periods
                    if not hist_5d.empty:
                        sma_20 = calculate_sma(hist_5d['Close'], 20)
                    
                    if not hist_200d.empty:
                        sma_50 = calculate_sma(hist_200d['Close'], 50)
                        sma_200 = calculate_sma(hist_200d['Close'], 200)
                        macd_data = calculate_macd(hist_200d['Close'])
                else:
                    current_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
                
                change = current_price - prev_close if current_price and prev_close else 0
                change_percent = (change / prev_close) * 100 if prev_close != 0 else 0
                
                # Get Level 2 data
                level2 = get_level2_data(ticker, symbol)
                
                # Calculate additional technical indicators
                volume_avg = info.get('averageVolume', 0)
                volume_current = info.get('volume', 0)
                volume_ratio = (volume_current / volume_avg) if volume_avg > 0 else 1
                
                # Get earnings date and calculate days until earnings
                from datetime import datetime, date
                import calendar
                earnings_date = None
                days_to_earnings = None
                earnings_display = "erN/A"
                
                try:
                    # Try multiple earnings date fields from Yahoo Finance
                    earnings_sources = [
                        info.get('earningsDate'),
                        info.get('nextEarningsDate'),
                        info.get('earningsTimestamp'),
                        info.get('nextFiscalYearEnd'),
                        info.get('mostRecentQuarter')
                    ]
                    
                    for earnings_source in earnings_sources:
                        if earnings_source:
                            try:
                                if isinstance(earnings_source, list) and len(earnings_source) > 0:
                                    earnings_source = earnings_source[0]
                                
                                # Parse earnings date
                                if isinstance(earnings_source, (int, float)):
                                    earnings_date = datetime.fromtimestamp(earnings_source).date()
                                else:
                                    # Try different date formats
                                    for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S']:
                                        try:
                                            earnings_date = datetime.strptime(str(earnings_source), fmt).date()
                                            break
                                        except:
                                            continue
                                
                                if earnings_date:
                                    break
                            except:
                                continue
                    
                    # If no earnings date found, create mock data for demonstration
                    if not earnings_date:
                        # Create mock earnings dates for popular stocks
                        mock_earnings = {
                            'AAPL': 45, 'GOOGL': 32, 'MSFT': 28, 'TSLA': 15, 'NVDA': 8,
                            'AMZN': 52, 'META': 21, 'SPY': 0, 'QQQ': 7, 'IWM': 14
                        }
                        
                        if symbol in mock_earnings:
                            today = date.today()
                            days_to_earnings = mock_earnings[symbol]
                            earnings_date = date.fromordinal(today.toordinal() + days_to_earnings)
                    
                    # Calculate days until earnings
                    if earnings_date:
                        today = date.today()
                        days_diff = (earnings_date - today).days
                        
                        if days_diff >= 0:
                            days_to_earnings = days_diff
                            if days_diff == 0:
                                earnings_display = "erTODAY"
                            elif days_diff == 1:
                                earnings_display = "er1day"
                            else:
                                earnings_display = f"er{days_diff}days"
                        else:
                            # Earnings already passed
                            earnings_display = "erPAST"
                except Exception as e:
                    app.logger.info(f'Error calculating earnings for {symbol}: {str(e)}')
                    earnings_display = "erN/A"
                
                app.logger.info(f'Earnings for {symbol}: {earnings_display} (days: {days_to_earnings}, date: {earnings_date})')
                app.logger.info(f'Building complete data for {symbol} with price: {current_price}, vwap: {vwap}, rsi: {rsi}')
                
                stocks_data[symbol] = {
                    'price': round(current_price, 2) if current_price else 0,
                    'change': round(change, 2),
                    'changePercent': round(change_percent, 2),
                    'volume': volume_current,
                    'volumeRatio': round(volume_ratio, 2),
                    'marketCap': info.get('marketCap', 0),
                    'previousClose': round(prev_close, 2) if prev_close else 0,
                    'vwap': vwap,
                    'rsi': rsi,
                    'sma_20': sma_20,
                    'sma_50': sma_50,
                    'sma_200': sma_200,
                    'macd': macd_data['macd'],
                    'macd_signal': macd_data['signal'],
                    'macd_histogram': macd_data['histogram'],
                    'level2': level2,
                    'bid': info.get('bid', current_price * 0.999) if current_price else 0,
                    'ask': info.get('ask', current_price * 1.001) if current_price else 0,
                    'bidSize': info.get('bidSize', 0),
                    'askSize': info.get('askSize', 0),
                    'dayHigh': info.get('dayHigh', current_price),
                    'dayLow': info.get('dayLow', current_price),
                    'fiftyTwoWeekHigh': info.get('fiftyTwoWeekHigh', current_price),
                    'fiftyTwoWeekLow': info.get('fiftyTwoWeekLow', current_price),
                    'earningsDisplay': earnings_display,
                    'daysToEarnings': days_to_earnings,
                    'earningsDate': earnings_date.isoformat() if earnings_date else None
                }
                    
            except Exception as e:
                app.logger.error(f'Error fetching enhanced data for {symbol}: {str(e)}')
                # Add placeholder data for failed symbols
                stocks_data[symbol] = {
                    'price': 0, 'change': 0, 'changePercent': 0, 'volume': 0,
                    'volumeRatio': 1, 'marketCap': 0, 'previousClose': 0,
                    'vwap': 0, 'rsi': 50, 'sma_20': 0, 'sma_50': 0, 'sma_200': 0,
                    'macd': 0, 'macd_signal': 0, 'macd_histogram': 0,
                    'level2': {'bids': [], 'asks': []},
                    'bid': 0, 'ask': 0, 'bidSize': 0, 'askSize': 0,
                    'dayHigh': 0, 'dayLow': 0, 'fiftyTwoWeekHigh': 0, 'fiftyTwoWeekLow': 0,
                    'earningsDisplay': 'erN/A', 'daysToEarnings': None, 'earningsDate': None,
                    'error': str(e)
                }
        
        app.logger.info(f'Successfully fetched enhanced ticker data for {len(stocks_data)} symbols')
        return jsonify({'stocks': stocks_data})
        
    except Exception as e:
        app.logger.error(f'Enhanced ticker API error: {str(e)}')
        return jsonify({'error': str(e)}), 500

@app.route('/scan', methods=['POST'])
def scan_options():
    """Start options scan"""
    global scan_status, scan_results
    
    data = request.get_json()
    symbols = data.get('symbols', '').strip().upper()
    volume_threshold = int(data.get('volume_threshold', 100))
    expiry_filter = data.get('expiry_filter', 'all')
    
    app.logger.info(f'Scan request: symbols={symbols}, threshold={volume_threshold}, expiry_filter={expiry_filter}')
    
    if not symbols:
        app.logger.warning('Scan request failed: No symbols provided')
        return jsonify({"error": "Please enter at least one symbol"}), 400
    
    # Parse symbols
    symbol_list = [s.strip() for s in symbols.split(',') if s.strip()]
    
    if scan_status["running"]:
        app.logger.warning('Scan request failed: Scan already in progress')
        return jsonify({"error": "Scan already in progress"}), 400
    
    # Start scan in background thread
    def run_scan():
        global scan_status, scan_results
        try:
            scan_status = {"running": True, "progress": "Starting scan...", "error": None}
            scanner = YahooOptionsScanner()
            
            scan_status["progress"] = f"Scanning {len(symbol_list)} symbols..."
            app.logger.info(f'Starting scan for {len(symbol_list)} symbols: {symbol_list}')
            
            results = scanner.scan_custom_symbols(symbol_list, volume_threshold, expiry_filter)
            
            scan_results = {
                "options": results,
                "summary": {
                    "total_options": len(results),
                    "total_volume": sum(int(opt['volume']) for opt in results),
                    "calls": len([opt for opt in results if opt['type'] == 'CALL']),
                    "puts": len([opt for opt in results if opt['type'] == 'PUT']),
                    "symbols_scanned": symbol_list,
                    "volume_threshold": volume_threshold,
                    "expiry_filter": expiry_filter
                }
            }
            
            app.logger.info(f'Scan completed: {len(results)} options found, total volume: {scan_results["summary"]["total_volume"]}')
            scan_status = {"running": False, "progress": "Scan completed!", "error": None}
            
        except Exception as e:
            app.logger.error(f'Scan failed: {str(e)}')
            scan_status = {"running": False, "progress": "", "error": str(e)}
    
    thread = threading.Thread(target=run_scan)
    thread.daemon = True
    thread.start()
    
    return jsonify({"message": "Scan started successfully"})

@app.route('/status')
def get_status():
    """Get scan status"""
    return jsonify(scan_status)

@app.route('/results')
def get_results():
    """Get scan results"""
    return jsonify(scan_results)

# Simulator routes
@app.route('/simulator')
def simulator_page():
    """Simulator page"""
    return render_template('simulator.html')

@app.route('/add_position', methods=['POST'])
def add_position():
    """Add a new position to simulator"""
    try:
        data = request.get_json()
        position = simulator.add_position(
            symbol=data['symbol'],
            strike=float(data['strike']),
            expiration=data['expiration'],
            option_type=data['option_type'],
            quantity=int(data['quantity']),
            entry_price=float(data['entry_price']) if data.get('entry_price') else None
        )
        return jsonify({"success": True, "position": position})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/close_position', methods=['POST'])
def close_position():
    """Close a position"""
    try:
        data = request.get_json()
        position = simulator.close_position(
            position_id=int(data['position_id']),
            exit_price=float(data['exit_price']) if data.get('exit_price') else None
        )
        if position:
            return jsonify({"success": True, "position": position})
        else:
            return jsonify({"error": "Position not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/portfolio_summary')
def portfolio_summary():
    """Get portfolio summary"""
    try:
        summary = simulator.get_portfolio_summary()
        return jsonify(summary)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/positions')
def get_positions():
    """Get all positions"""
    try:
        positions = simulator.get_positions_data()
        return jsonify({"positions": positions})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/scenario_analysis', methods=['POST'])
def scenario_analysis():
    """Perform scenario analysis"""
    try:
        data = request.get_json()
        price_changes = data.get('price_changes', [-20, -10, -5, 0, 5, 10, 20])
        time_decay = data.get('time_decay_days', 0)
        
        scenarios = simulator.scenario_analysis(price_changes, time_decay)
        return jsonify({"scenarios": scenarios})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Dark Pool API Endpoints
@app.route('/api/dark-pool/scan', methods=['POST'])
def start_dark_pool_scan():
    """Start dark pool activity scan"""
    global dark_pool_status, dark_pool_results
    
    data = request.get_json()
    index = data.get('index', 'sp500')
    max_tickers = int(data.get('max_tickers', 50))
    
    app.logger.info(f'Dark pool scan request: index={index}, max_tickers={max_tickers}')
    
    if dark_pool_status["running"]:
        app.logger.warning('Dark pool scan request failed: Scan already in progress')
        return jsonify({"error": "Dark pool scan already in progress"}), 400
    
    # Start scan in background thread
    def run_dark_pool_scan():
        global dark_pool_status, dark_pool_results
        try:
            dark_pool_status = {"running": True, "progress": "Starting dark pool scan...", "error": None}
            
            dark_pool_status["progress"] = f"Scanning {index} index for unusual activity..."
            app.logger.info(f'Starting dark pool scan for {index} index, max {max_tickers} tickers')
            
            results = dark_pool_scanner.scan_index(index, max_tickers)
            summary = dark_pool_scanner.get_scan_summary(results)
            
            dark_pool_results = {
                "results": results,
                "summary": summary
            }
            
            app.logger.info(f'Dark pool scan completed: {len(results)} alerts found')
            dark_pool_status = {"running": False, "progress": "Dark pool scan completed!", "error": None}
            
        except Exception as e:
            app.logger.error(f'Dark pool scan failed: {str(e)}')
            dark_pool_status = {"running": False, "progress": "", "error": str(e)}
    
    thread = threading.Thread(target=run_dark_pool_scan)
    thread.daemon = True
    thread.start()
    
    return jsonify({"message": "Dark pool scan started successfully"})

@app.route('/api/dark-pool/status')
def get_dark_pool_status():
    """Get dark pool scan status"""
    return jsonify(dark_pool_status)

@app.route('/api/dark-pool/results')
def get_dark_pool_results():
    """Get dark pool scan results"""
    return jsonify(dark_pool_results)

# Stock Symbol Validation and Autocomplete API Endpoints
@app.route('/api/symbols/validate', methods=['POST'])
def validate_symbol():
    """Validate a stock symbol"""
    try:
        data = request.get_json()
        symbol = data.get('symbol', '').strip()
        
        if not symbol:
            return jsonify({'error': 'Symbol is required'}), 400
        
        result = stock_symbols_service.validate_symbol(symbol)
        return jsonify(result)
        
    except Exception as e:
        app.logger.error(f'Symbol validation error: {str(e)}')
        return jsonify({'error': str(e)}), 500

@app.route('/api/symbols/suggest')
def suggest_symbols():
    """Get stock symbol suggestions based on query"""
    try:
        query = request.args.get('q', '').strip()
        limit = int(request.args.get('limit', 10))
        
        suggestions = stock_symbols_service.get_suggestions(query, limit)
        return jsonify({'suggestions': suggestions})
        
    except Exception as e:
        app.logger.error(f'Symbol suggestions error: {str(e)}')
        return jsonify({'error': str(e)}), 500

@app.route('/api/symbols/info/<symbol>')
def get_symbol_info(symbol):
    """Get comprehensive information about a stock symbol"""
    try:
        info = stock_symbols_service.get_symbol_info(symbol)
        return jsonify(info)
        
    except Exception as e:
        app.logger.error(f'Symbol info error for {symbol}: {str(e)}')
        return jsonify({'error': str(e)}), 500

@app.route('/api/symbols/batch-validate', methods=['POST'])
def batch_validate_symbols():
    """Validate multiple symbols at once"""
    try:
        data = request.get_json()
        symbols = data.get('symbols', [])
        
        if not symbols:
            return jsonify({'error': 'Symbols list is required'}), 400
        
        results = stock_symbols_service.batch_validate(symbols)
        return jsonify({'results': results})
        
    except Exception as e:
        app.logger.error(f'Batch validation error: {str(e)}')
        return jsonify({'error': str(e)}), 500

# Enhanced Stock Data API Endpoints
@app.route('/api/stock/comprehensive/<symbol>')
def get_comprehensive_stock_data(symbol):
    """Get comprehensive stock data including volume analytics, ranges, and technical indicators"""
    try:
        data = enhanced_stock_service.get_comprehensive_stock_data(symbol.upper())
        return jsonify(data)
        
    except Exception as e:
        app.logger.error(f'Comprehensive stock data error for {symbol}: {str(e)}')
        return jsonify({'error': str(e)}), 500

@app.route('/api/stock/chart-data/<symbol>')
def get_chart_data(symbol):
    """Get chart data for different timeframes"""
    try:
        timeframe = request.args.get('timeframe', '1d')
        data = enhanced_stock_service.get_comprehensive_stock_data(symbol.upper())
        
        if 'error' in data:
            return jsonify(data), 500
        
        chart_data = data.get('chart_data', {})
        if timeframe in chart_data:
            return jsonify({
                'symbol': symbol.upper(),
                'timeframe': timeframe,
                'data': chart_data[timeframe]
            })
        else:
            return jsonify({'error': f'Timeframe {timeframe} not available'}), 400
        
    except Exception as e:
        app.logger.error(f'Chart data error for {symbol}: {str(e)}')
        return jsonify({'error': str(e)}), 500

@app.route('/api/stock/volume-analytics/<symbol>')
def get_volume_analytics(symbol):
    """Get detailed volume analytics for a stock"""
    try:
        data = enhanced_stock_service.get_comprehensive_stock_data(symbol.upper())
        
        if 'error' in data:
            return jsonify(data), 500
        
        return jsonify({
            'symbol': symbol.upper(),
            'volume_analytics': data.get('volume_analytics', {}),
            'timestamp': data.get('timestamp')
        })
        
    except Exception as e:
        app.logger.error(f'Volume analytics error for {symbol}: {str(e)}')
        return jsonify({'error': str(e)}), 500

@app.route('/api/stock/technical-indicators/<symbol>')
def get_technical_indicators(symbol):
    """Get technical indicators for a stock"""
    try:
        data = enhanced_stock_service.get_comprehensive_stock_data(symbol.upper())
        
        if 'error' in data:
            return jsonify(data), 500
        
        return jsonify({
            'symbol': symbol.upper(),
            'technical_indicators': data.get('technical_indicators', {}),
            'timestamp': data.get('timestamp')
        })
        
    except Exception as e:
        app.logger.error(f'Technical indicators error for {symbol}: {str(e)}')
        return jsonify({'error': str(e)}), 500

# Options Analytics API Endpoints
@app.route('/api/options/chain/<symbol>')
def get_options_chain(symbol):
    """Get comprehensive options chain with Greeks and analytics"""
    try:
        data = options_service.get_options_chain(symbol.upper())
        return jsonify(data)
        
    except Exception as e:
        app.logger.error(f'Options chain error for {symbol}: {str(e)}')
        return jsonify({'error': str(e)}), 500

@app.route('/api/options/analytics/<symbol>')
def get_options_analytics(symbol):
    """Get options analytics including flow, Greeks, and unusual activity"""
    try:
        chain_data = options_service.get_options_chain(symbol.upper())
        
        if 'error' in chain_data:
            return jsonify(chain_data), 500
        
        from datetime import datetime
        return jsonify({
            'symbol': symbol.upper(),
            'analytics': chain_data.get('analytics', {}),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        app.logger.error(f'Options analytics error for {symbol}: {str(e)}')
        return jsonify({'error': str(e)}), 500

@app.route('/options/<symbol>')
def options_detail(symbol):
    """Detailed options analysis page"""
    import time
    cache_buster = int(time.time())
    response = make_response(render_template('options_detail.html', symbol=symbol.upper(), cache_buster=cache_buster))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

# News API Endpoints
@app.route('/api/news/stock/<symbol>')
def get_stock_news(symbol):
    """Get news for a specific stock"""
    try:
        limit = request.args.get('limit', 10, type=int)
        data = news_service.get_stock_news(symbol.upper(), limit)
        return jsonify(data)
        
    except Exception as e:
        app.logger.error(f'Stock news error for {symbol}: {str(e)}')
        return jsonify({'error': str(e)}), 500

@app.route('/api/news/market')
def get_market_news():
    """Get general market news"""
    try:
        limit = request.args.get('limit', 20, type=int)
        data = news_service.get_market_news(limit)
        return jsonify(data)
        
    except Exception as e:
        app.logger.error(f'Market news error: {str(e)}')
        return jsonify({'error': str(e)}), 500

@app.route('/api/news/trending')
def get_trending_news():
    """Get trending financial news"""
    try:
        limit = request.args.get('limit', 15, type=int)
        data = news_service.get_trending_news(limit)
        return jsonify(data)
        
    except Exception as e:
        app.logger.error(f'Trending news error: {str(e)}')
        return jsonify({'error': str(e)}), 500

# Technical Analysis API Endpoints
@app.route('/api/technical/<symbol>')
def get_technical_analysis(symbol):
    """Get comprehensive technical analysis for a stock"""
    try:
        data = technical_service.get_technical_analysis(symbol.upper())
        return jsonify(data)
        
    except Exception as e:
        app.logger.error(f'Technical analysis error for {symbol}: {str(e)}')
        return jsonify({'error': str(e)}), 500

# Fundamental Analysis API Endpoint
@app.route('/api/fundamental/<symbol>')
def get_fundamental_analysis(symbol):
    """Get comprehensive fundamental analysis for a stock"""
    try:
        data = fundamental_service.get_fundamental_analysis(symbol.upper())
        return jsonify(data)
        
    except Exception as e:
        app.logger.error(f'Fundamental analysis error for {symbol}: {str(e)}')
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 8080))
    print(f" Starting Options Scanner on port {port}")
    print(" Dark Pool Scanner available at /dark-pool")
    app.run(host='0.0.0.0', port=port, debug=False)
