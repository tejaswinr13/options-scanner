#!/usr/bin/env python3
"""
Setup script for local data collection system
"""

import subprocess
import sys
import os

def install_requirements():
    """Install required packages for local data collection"""
    packages = [
        'yfinance',
        'pandas',
        'numpy',
        'schedule',
        'sqlite3'  # Built into Python
    ]
    
    print("📦 Installing required packages...")
    for package in packages:
        if package != 'sqlite3':  # sqlite3 is built-in
            try:
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
                print(f"✅ {package} installed")
            except subprocess.CalledProcessError:
                print(f"❌ Failed to install {package}")

def create_database():
    """Initialize the local database"""
    print("🗄️  Initializing local database...")
    from local_data_collector import LocalDataCollector
    
    collector = LocalDataCollector()
    print("✅ Database initialized with tables")
    
    # Run initial data collection
    print("📊 Running initial data collection...")
    collector.collect_all_data()
    print("✅ Initial data collection completed")

def create_startup_script():
    """Create a startup script for the data collector"""
    script_content = '''#!/bin/bash
# Startup script for local data collector
cd "$(dirname "$0")"
echo "🚀 Starting Local Stock Data Collector..."
python3 local_data_collector.py
'''
    
    with open('start_collector.sh', 'w') as f:
        f.write(script_content)
    
    # Make it executable
    os.chmod('start_collector.sh', 0o755)
    print("✅ Created start_collector.sh script")

def main():
    print("🏗️  Setting up Local Stock Data Collection System")
    print("=" * 50)
    
    # Install requirements
    install_requirements()
    
    # Create database
    create_database()
    
    # Create startup script
    create_startup_script()
    
    print("\n🎉 Setup completed!")
    print("\n📋 Next steps:")
    print("1. Run the data collector: python3 local_data_collector.py")
    print("2. Or use the startup script: ./start_collector.sh")
    print("3. Update your GCP app to use database_service.py")
    print("4. The collector will run continuously and update data every 30 seconds")
    print("\n💡 The database file 'stock_data.db' will be created in this directory")

if __name__ == "__main__":
    main()
