# Installation Guide - Piper Automation System

## Prerequisites

- **Python 3.8 or higher**
- **CAN bus interface** configured on your system
- **Piper robot** connected and powered

---

## Quick Install

### Step 1: Create Virtual Environment

```bash
# Navigate to project directory
cd PiperAutomationSystem

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate

# On Linux/Mac:
source venv/bin/activate
```

### Step 2: Install Dependencies

```bash
# Install all required packages
pip install -r requirements.txt
```

### Step 3: Verify Installation

```bash
# Run the test suite
python test_system.py
```

### Step 4: Launch Application

```bash
# Start the GUI
python main.py
```

---

## Detailed Installation Steps

### For Windows:

```powershell
# 1. Open PowerShell in PiperAutomationSystem directory
cd C:\path\to\PiperAutomationSystem

# 2. Create virtual environment
python -m venv venv

# 3. Activate virtual environment
.\venv\Scripts\Activate.ps1

# If you get execution policy error, run:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 4. Upgrade pip
python -m pip install --upgrade pip

# 5. Install dependencies
pip install -r requirements.txt

# 6. Test installation
python test_system.py

# 7. Run application
python main.py
```

### For Linux:

```bash
# 1. Navigate to directory
cd /path/to/PiperAutomationSystem

# 2. Install tkinter (if not already installed)
sudo apt-get update
sudo apt-get install python3-tk

# 3. Create virtual environment
python3 -m venv venv

# 4. Activate virtual environment
source venv/bin/activate

# 5. Upgrade pip
pip install --upgrade pip

# 6. Install dependencies
pip install -r requirements.txt

# 7. Configure CAN interface (if not done already)
# See piper_sdk documentation for CAN setup

# 8. Test installation
python test_system.py

# 9. Run application
python main.py
```

### For macOS:

```bash
# 1. Navigate to directory
cd /path/to/PiperAutomationSystem

# 2. Create virtual environment
python3 -m venv venv

# 3. Activate virtual environment
source venv/bin/activate

# 4. Upgrade pip
pip install --upgrade pip

# 5. Install dependencies
pip install -r requirements.txt

# 6. Test installation
python test_system.py

# 7. Run application
python main.py
```

---

## Dependency Details

### Required Packages:

| Package | Version | Purpose |
|---------|---------|---------|
| `piper_sdk` | ≥0.6.1 | Piper robot communication |
| `python-can` | ≥4.3.1 | CAN bus interface |
| `typing-extensions` | ≥4.5.0 | Type hints support |

### Standard Library (Included with Python):
- `tkinter` - GUI framework
- `threading` - Multi-threading support
- `asyncio` - Async operations
- `logging` - Logging framework
- `pathlib` - Path operations
- `time`, `datetime` - Time utilities
- `json` - JSON parsing

---

## Troubleshooting

### Issue: "No module named tkinter"

**Solution:**
```bash
# Ubuntu/Debian
sudo apt-get install python3-tk

# Fedora/RHEL/CentOS
sudo dnf install python3-tkinter

# macOS (usually included, but if needed)
brew install python-tk

# Windows
# Reinstall Python and check "tcl/tk and IDLE" in installer
```

### Issue: "pip install fails"

**Solution:**
```bash
# Upgrade pip
python -m pip install --upgrade pip

# Try installing packages individually
pip install python-can
pip install piper_sdk
```

### Issue: "CAN interface not found"

**Solution:**
- Check CAN hardware is connected
- Verify CAN drivers are installed
- See Piper SDK documentation: `piper_sdk/asserts/can_config.MD`

### Issue: "Permission denied" on Linux

**Solution:**
```bash
# Add user to dialout group for serial/CAN access
sudo usermod -a -G dialout $USER

# Reboot or log out/in for changes to take effect
```

---

## Verifying Installation

Run the following Python commands to verify everything is installed:

```python
# Test 1: Check Python version
import sys
print(f"Python: {sys.version}")

# Test 2: Check piper_sdk
import piper_sdk
print(f"Piper SDK: OK")

# Test 3: Check python-can
import can
print(f"python-can: OK")

# Test 4: Check tkinter
import tkinter as tk
root = tk.Tk()
root.withdraw()
print(f"tkinter: OK")

print("\n✓ All dependencies installed successfully!")
```

Save as `verify_install.py` and run:
```bash
python verify_install.py
```

---

## Updating Dependencies

To update all packages to their latest versions:

```bash
# Activate virtual environment first
pip install --upgrade -r requirements.txt
```

To update a specific package:

```bash
pip install --upgrade piper_sdk
```

---

## Uninstalling

To remove the virtual environment:

```bash
# Deactivate virtual environment (if active)
deactivate

# Remove virtual environment directory
# Windows:
rmdir /s venv

# Linux/Mac:
rm -rf venv
```

---

## Alternative: Using Conda

If you prefer Conda:

```bash
# Create conda environment
conda create -n piper_automation python=3.10

# Activate environment
conda activate piper_automation

# Install pip packages
pip install -r requirements.txt

# Or install via conda where available
conda install -c conda-forge python-can
pip install piper_sdk
```

---

## Development Setup

For development, you may want additional packages:

```bash
# Install development tools
pip install pytest       # Testing framework
pip install black        # Code formatter
pip install pylint       # Code linter
pip install mypy         # Type checker
```

---

## Notes

1. **Virtual Environment**: Always activate the virtual environment before running the application
2. **CAN Bus**: Ensure CAN interface is configured before connecting to robot
3. **Permissions**: On Linux, you may need sudo/dialout group for CAN access
4. **Python Version**: Python 3.8+ required, Python 3.10+ recommended

---

**For more information:**
- See `QUICKSTART.md` for usage examples
- See `Available Tools.md` for SDK documentation
- See Piper SDK docs: `piper_sdk/asserts/`

---

**Installation complete! You're ready to use the Piper Automation System!** 🚀

