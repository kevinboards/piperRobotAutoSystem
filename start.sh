#!/bin/bash
# Piper Automation System - Start
# Usage: ./start.sh [can_interface] [bitrate]

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

CAN_NAME="${1:-can0}"
BITRATE="${2:-1000000}"

echo "========================================"
echo " Piper Automation System"
echo "========================================"

# Activate venv
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
else
    echo "[WARN] No venv found. Run ./setup.sh first, or using system Python."
fi

# Activate CAN bus
echo ""
echo "[1/2] Activating CAN bus ($CAN_NAME @ ${BITRATE}bps)..."
if [ -f "piper_sdk/piper_sdk/can_activate.sh" ]; then
    sudo bash piper_sdk/piper_sdk/can_activate.sh "$CAN_NAME" "$BITRATE" && echo "  CAN bus: OK" || echo "  CAN bus: FAILED (continuing in demo mode)"
else
    echo "  CAN activation script not found, attempting direct setup..."
    sudo ip link set "$CAN_NAME" down 2>/dev/null
    sudo ip link set "$CAN_NAME" type can bitrate "$BITRATE" 2>/dev/null
    sudo ip link set "$CAN_NAME" up 2>/dev/null && echo "  CAN bus: OK" || echo "  CAN bus: FAILED (continuing in demo mode)"
fi

# Start server
echo ""
echo "[2/2] Starting web server..."
echo "  Web UI:    http://localhost:8000"
echo "  WebSocket: ws://localhost:8080"
echo "  Press Ctrl+C to stop"
echo "========================================"
echo ""

python3 server.py
