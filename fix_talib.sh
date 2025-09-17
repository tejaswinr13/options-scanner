#!/bin/bash

# Quick fix for TA-Lib installation on Ubuntu/Debian systems

echo "🔧 Installing TA-Lib C library..."

# Update system packages
sudo apt update
sudo apt install -y build-essential wget

# Download and install TA-Lib C library
cd /tmp
wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
tar -xzf ta-lib-0.4.0-src.tar.gz
cd ta-lib/
./configure --prefix=/usr/local
make
sudo make install
sudo ldconfig

echo "✅ TA-Lib C library installed successfully!"

# Now install the Python wrapper
echo "🐍 Installing TA-Lib Python wrapper..."
pip install TA-Lib

echo "🎉 TA-Lib installation complete!"
echo "You can now run your requirements.txt installation."
