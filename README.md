# Options Volume Scanner

A comprehensive web-based tool to scan for unusual options activity using Yahoo Finance data, featuring real-time analysis with Greeks calculations and integrated visual analytics.

## Features

- 🌐 **Modern Web UI**: Beautiful, responsive interface with real-time updates
- 📊 **Volume Analysis**: Scans puts and calls for unusual volume (customizable threshold)
- 📅 **All Expirations**: Checks all available expiration dates (2025, 2026, 2027+)
- 🎯 **Custom Symbols**: Enter any stock symbols you want to analyze
- 📈 **Greeks Calculations**: Delta, Gamma, Theta, Rho for all options
- 🔄 **Live Filtering**: Filter between calls only, puts only, or all options
- 📊 **Visual Analytics**: Integrated pie chart showing call vs put volume distribution
- 📝 **Production Logging**: Comprehensive logging with automatic rotation and cleanup
- 🚀 **GCP Ready**: Deployment scripts for cloud hosting
- 🆓 **100% Free**: Uses Yahoo Finance data - no API keys or fees required

## Installation

1. **Install Dependencies**:
```bash
pip install -r requirements.txt
```

2. **Start the Web Server**:
```bash
python3 app.py
```

3. **Open in Browser**:
Navigate to `http://127.0.0.1:8080`

## Usage

### Web Interface
1. **Enter Symbols**: Type symbols like `AAPL,TSLA,NVDA` in the input field
2. **Set Volume Threshold**: Adjust minimum volume (default: 100 contracts)
3. **Click "Start Scan"**: Watch real-time progress
4. **View Results**: Interactive table with filtering options

### Command Line (Alternative)
```bash
# Scan specific symbols
python3 quick_scan.py 'AAPL,TSLA,NVDA' 100

# Interactive mode
python3 yahoo_options_scanner.py
```

## Web UI Features

### Input Controls
- **Symbol Input**: Enter comma-separated symbols
- **Volume Threshold**: Set minimum volume to display
- **Real-time Status**: Live progress updates during scanning

### Results Display
- **Summary Cards**: Total options, volume, calls/puts breakdown with unified styling
- **Visual Analytics**: Integrated pie chart showing call vs put volume distribution
- **Filter Buttons**: Show all, calls only, or puts only
- **Interactive Table**: Sort and view all option data
- **Greeks Display**: Complete risk metrics for each option

### Data Columns
- Symbol, Expiration, Strike, Type (Call/Put)
- Volume, Open Interest, Bid/Ask, Last Price
- Implied Volatility percentage
- **Greeks**: Delta, Gamma, Theta, Rho

## Command Line Options

### Quick Scan
```bash
python3 quick_scan.py 'CHGG,AAPL,TSLA' 50
```

### Custom Symbols in Code
Edit `yahoo_options_scanner.py` line 26:
```python
self.symbols = ['AAPL', 'TSLA', 'NVDA', 'YOUR_SYMBOLS_HERE']
```

## Technical Details

### Data Source
- **Yahoo Finance**: Free, reliable options data
- **Real-time**: During market hours
- **Historical**: All available expiration dates
- **No Rate Limits**: For reasonable personal use

### Greeks Calculation
- **Black-Scholes Model**: Industry-standard calculations
- **Delta**: Price sensitivity to underlying movement
- **Gamma**: Rate of change of delta
- **Theta**: Time decay (daily value loss)
- **Rho**: Interest rate sensitivity

## GCP Deployment

### Quick Deploy
```bash
# On your GCP VM
cd ~/options-scanner
./deploy.sh
```

### Manual Setup
1. **Clone Repository**:
```bash
git clone https://github.com/tejaswinr13/options-scanner.git
cd options-scanner
```

2. **Install Dependencies**:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3. **Start Production Server**:
```bash
# Background process
nohup python3 app.py > app.log 2>&1 &

# Or use the deployment script
./deploy.sh
```

4. **Stop Server**:
```bash
./stop.sh
```

### Log Management

**Automatic Logging**:
- Production logs: `logs/options_scanner.log`
- Automatic rotation at 10MB (keeps 10 files)
- Detailed request/response logging

**Log Cleanup**:
```bash
# Manual cleanup
./log_cleanup.sh

# Automated weekly cleanup (add to crontab)
0 0 * * 0 /home/username/options-scanner/log_cleanup.sh >> /home/username/cron.log 2>&1
```

**Monitor Logs**:
```bash
# Real-time monitoring
tail -f logs/options_scanner.log

# Check disk usage
df -h
du -sh logs/
```

## File Structure

```
options/
├── app.py                    # Flask web server with logging
├── yahoo_options_scanner.py  # Core scanner logic
├── quick_scan.py            # Command line utility
├── options_simulator.py     # Options simulation engine
├── deploy.sh                # GCP deployment script
├── stop.sh                  # Server stop script
├── log_cleanup.sh           # Log management utility
├── templates/
│   ├── index.html           # Main web interface
│   └── simulator.html       # Options simulator
├── static/
│   ├── css/                 # Stylesheets
│   └── js/                  # JavaScript files
├── logs/
│   └── options_scanner.log  # Application logs
├── requirements.txt         # Dependencies
└── README.md               # This file
```

## Troubleshooting

### Web Server Issues
- **Port 8080 in use**: Change port in `app.py`
- **Dependencies missing**: Run `pip install -r requirements.txt`
- **Process not stopping**: Use `./stop.sh` or `pkill -f app.py`

### Data Issues
- **No options found**: Verify symbols have options trading
- **Slow loading**: Large symbol lists take more time
- **Missing data**: Some options may have incomplete information

### Performance
- **Memory usage**: Large scans use more memory
- **Speed**: Scanning many symbols takes time
- **Network**: Requires internet connection

### Logging Issues
- **No logs appearing**: Check `logs/` directory exists and permissions
- **Log files too large**: Run `./log_cleanup.sh` to clean up
- **Disk space full**: Monitor with `df -h` and clean old logs

## Disclaimer

This tool is for educational and informational purposes only. Options trading involves significant financial risk. Always verify data independently and consult with financial professionals before making trading decisions. Yahoo Finance data may have delays or inaccuracies.
