#!/usr/bin/env python3
"""
Options Scanner Web UI
Flask web application for the Yahoo Finance Options Scanner
"""

from flask import Flask, render_template, request, jsonify, make_response
import json
from yahoo_options_scanner import YahooOptionsScanner
from options_simulator import OptionsSimulator
from dark_pool_scanner import DarkPoolScanner
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
def dark_pool_page():
    """Dark pool activity scanner page"""
    response = make_response(render_template('dark_pool.html'))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

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

if __name__ == '__main__':
    print(" Starting Options Scanner on http://127.0.0.1:8080")
    print(" Dark Pool Scanner available at http://127.0.0.1:8080/dark-pool")
    app.run(host='0.0.0.0', port=8080, debug=False)
