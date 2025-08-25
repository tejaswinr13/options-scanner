#!/usr/bin/env python3
"""
Options Scanner Web UI
Flask web application for the Yahoo Finance Options Scanner
"""

from flask import Flask, render_template, request, jsonify, make_response
import json
from yahoo_options_scanner import YahooOptionsScanner
from options_simulator import OptionsSimulator
import threading
import time

app = Flask(__name__)

# Global variables for storing scan results and simulator
scan_results = {}
scan_status = {"running": False, "progress": "", "error": None}
simulator = OptionsSimulator()

@app.route('/')
def index():
    """Main page"""
    response = make_response(render_template('index.html'))
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
    
    if not symbols:
        return jsonify({"error": "Please enter at least one symbol"}), 400
    
    # Parse symbols
    symbol_list = [s.strip() for s in symbols.split(',') if s.strip()]
    
    if scan_status["running"]:
        return jsonify({"error": "Scan already in progress"}), 400
    
    # Start scan in background thread
    def run_scan():
        global scan_status, scan_results
        try:
            scan_status = {"running": True, "progress": "Starting scan...", "error": None}
            scanner = YahooOptionsScanner()
            
            scan_status["progress"] = f"Scanning {len(symbol_list)} symbols..."
            results = scanner.scan_custom_symbols(symbol_list, volume_threshold)
            
            scan_results = {
                "options": results,
                "summary": {
                    "total_options": len(results),
                    "total_volume": sum(int(opt['volume']) for opt in results),
                    "calls": len([opt for opt in results if opt['type'] == 'CALL']),
                    "puts": len([opt for opt in results if opt['type'] == 'PUT']),
                    "symbols_scanned": symbol_list,
                    "volume_threshold": volume_threshold
                }
            }
            
            scan_status = {"running": False, "progress": "Scan completed!", "error": None}
            
        except Exception as e:
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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
