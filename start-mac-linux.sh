#!/bin/bash

echo "=============================================="
echo "  HireIQ AI Resume Screener - Startup Script"
echo "=============================================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "[INFO] Python3 not found. Attempting to install it..."
    if command -v brew &> /dev/null; then
        echo "[INFO] macOS detected (Homebrew). Installing python3..."
        brew install python
    elif command -v apt-get &> /dev/null; then
        echo "[INFO] Debian/Ubuntu detected. Installing python3..."
        sudo apt-get update
        sudo apt-get install -y python3 python3-venv python3-pip
    elif command -v dnf &> /dev/null; then
        echo "[INFO] Fedora/RHEL detected. Installing python3..."
        sudo dnf install -y python3
    else
        echo "[ERROR] Could not automatically install Python3."
        echo "Please install Python 3.8+ manually from python.org or using your package manager."
        exit 1
    fi
    # Check again if it installed
    if ! command -v python3 &> /dev/null; then
        echo "[ERROR] Python3 installation failed. Please install manually."
        exit 1
    fi
fi

# Ensure python3-venv module exists on Ubuntu/Debian 
if command -v apt-get &> /dev/null; then
    if ! dpkg -s python3-venv &> /dev/null; then
        echo "[INFO] Debian systems split python standard library. Installing python3-venv..."
        sudo apt-get install -y python3-venv
    fi
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "[INFO] Creating Python virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "[ERROR] Failed to create virtual environment."
        exit 1
    fi
fi

# Activate the virtual environment
echo "[INFO] Activating virtual environment..."
source venv/bin/activate

# Install requirements
echo "[INFO] Installing required dependencies (this may take a few minutes on first run)..."
python3 -m pip install --upgrade pip
pip install -r requirements.txt

# Run the application
echo ""
echo "[INFO] Starting the HireIQ application..."
echo "[INFO] The local server will be available at http://localhost:5000"
echo "[INFO] Your browser will open automatically in a few seconds..."
echo "=============================================="

# Determine generic open command for Mac and Linux
if command -v open > /dev/null; then
    (sleep 3 && open "http://localhost:5000") &
elif command -v xdg-open > /dev/null; then
    (sleep 3 && xdg-open "http://localhost:5000") &
fi

python3 run.py
