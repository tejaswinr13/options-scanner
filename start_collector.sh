#!/bin/bash
# Startup script for local data collector
cd "$(dirname "$0")"
echo "🚀 Starting Local Stock Data Collector..."
python3 local_data_collector.py
