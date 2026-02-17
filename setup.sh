#!/bin/bash
# Piper Automation System - One-time setup
# Run: chmod +x setup.sh && ./setup.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "========================================"
echo " Piper Automation System - Setup"
echo "========================================"

# Check Python
PYTHON=""
for cmd in python3 python; do
    if command -v "$cmd" &>/dev/null; then
        VER=$("$cmd" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
        MAJOR=$("$cmd" -c "import sys; print(sys.version_info.major)")
        MINOR=$("$cmd" -c "import sys; print(sys.version_info.minor)")
        if [ "$MAJOR" -ge 3 ] && [ "$MINOR" -ge 8 ]; then
            PYTHON="$cmd"
            echo "[OK] Python $VER found ($cmd)"
            break
        fi
    fi
done

if [ -z "$PYTHON" ]; then
    echo "[ERROR] Python 3.8+ required. Install with: sudo apt install python3 python3-venv python3-pip"
    exit 1
fi

# Install system dependencies
echo ""
echo "[1/4] Checking system dependencies..."
MISSING=""
command -v ip &>/dev/null || MISSING="$MISSING iproute2"
dpkg -l | grep -q "can-utils" 2>/dev/null || MISSING="$MISSING can-utils"
dpkg -l | grep -q "ethtool" 2>/dev/null || MISSING="$MISSING ethtool"

if [ -n "$MISSING" ]; then
    echo "  Installing:$MISSING"
    sudo apt-get update -qq && sudo apt-get install -y -qq $MISSING
else
    echo "  [OK] System deps present (can-utils, ethtool, iproute2)"
fi

# Create venv
echo ""
echo "[2/4] Setting up Python virtual environment..."
if [ ! -d "venv" ]; then
    $PYTHON -m venv venv
    echo "  Created venv/"
else
    echo "  [OK] venv/ already exists"
fi

source venv/bin/activate

# Install Python deps
echo ""
echo "[3/4] Installing Python dependencies..."
pip install --quiet --upgrade pip
pip install --quiet aiohttp websockets python-can typing-extensions

# Install piper_sdk from local copy
if [ -d "piper_sdk" ]; then
    pip install --quiet -e piper_sdk/
    echo "  [OK] piper_sdk installed from local directory"
else
    pip install --quiet piper_sdk
    echo "  [OK] piper_sdk installed from PyPI"
fi

# Make scripts executable
echo ""
echo "[4/4] Setting permissions..."
chmod +x start.sh 2>/dev/null || true
chmod +x piper_sdk/piper_sdk/can_activate.sh 2>/dev/null || true
mkdir -p recordings timelines

echo ""
echo "========================================"
echo " Setup complete!"
echo " Run: ./start.sh"
echo "========================================"
