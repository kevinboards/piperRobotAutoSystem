"""
Verify Installation Script

Quick script to verify all dependencies are installed correctly.
"""

import sys
import importlib

def check_python_version():
    """Check if Python version is sufficient."""
    print("Checking Python version...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"✓ Python {version.major}.{version.minor}.{version.micro} OK")
        return True
    else:
        print(f"✗ Python {version.major}.{version.minor}.{version.micro} - Need 3.8+")
        return False

def check_module(module_name, display_name=None):
    """Check if a module can be imported."""
    if display_name is None:
        display_name = module_name
    
    try:
        mod = importlib.import_module(module_name)
        version = getattr(mod, '__version__', 'unknown')
        print(f"✓ {display_name:20} OK (version: {version})")
        return True
    except ImportError as e:
        print(f"✗ {display_name:20} MISSING - {e}")
        return False

def check_tkinter():
    """Check if tkinter is available."""
    try:
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
        root.destroy()
        print(f"✓ {'tkinter':20} OK")
        return True
    except ImportError:
        print(f"✗ {'tkinter':20} MISSING - Install python3-tk")
        return False
    except Exception as e:
        print(f"⚠ {'tkinter':20} WARNING - {e}")
        return False

def check_project_modules():
    """Check if project modules can be imported."""
    print("\nChecking project modules...")
    modules = [
        ('ppr_file_handler', 'File Handler'),
        ('recorder', 'Recorder'),
        ('player', 'Player'),
    ]
    
    results = []
    for module_name, display_name in modules:
        try:
            importlib.import_module(module_name)
            print(f"✓ {display_name:20} OK")
            results.append(True)
        except ImportError as e:
            print(f"✗ {display_name:20} MISSING - {e}")
            results.append(False)
    
    return all(results)

def main():
    """Run all verification checks."""
    print("=" * 60)
    print(" PIPER AUTOMATION SYSTEM - INSTALLATION VERIFICATION")
    print("=" * 60)
    print()
    
    results = []
    
    # Check Python version
    results.append(check_python_version())
    print()
    
    # Check required packages
    print("Checking required packages...")
    results.append(check_module('piper_sdk', 'Piper SDK'))
    results.append(check_module('can', 'python-can'))
    results.append(check_module('typing_extensions', 'typing-extensions'))
    results.append(check_tkinter())
    print()
    
    # Check standard library
    print("Checking standard library modules...")
    results.append(check_module('threading', 'threading'))
    results.append(check_module('logging', 'logging'))
    results.append(check_module('pathlib', 'pathlib'))
    results.append(check_module('json', 'json'))
    results.append(check_module('time', 'time'))
    results.append(check_module('datetime', 'datetime'))
    print()
    
    # Check project modules
    results.append(check_project_modules())
    print()
    
    # Summary
    print("=" * 60)
    if all(results):
        print(" ✓ ALL CHECKS PASSED!")
        print(" Installation is complete and verified.")
        print()
        print(" You can now run:")
        print("   - python main.py          (Launch GUI)")
        print("   - python test_system.py   (Run tests)")
    else:
        print(" ✗ SOME CHECKS FAILED")
        print(" Please install missing dependencies:")
        print("   pip install -r requirements.txt")
        print()
        print(" For tkinter on Linux:")
        print("   sudo apt-get install python3-tk")
    print("=" * 60)
    print()

if __name__ == "__main__":
    main()

