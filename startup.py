"""
Quick start guide for running the Stripe Reconciliation Accelerator locally.
"""

import os
import sys
from pathlib import Path

def print_banner():
    """Display welcome banner."""
    banner = """
    ╔═══════════════════════════════════════════════════════════════╗
    ║   Stripe Reconciliation Accelerator                          ║
    ║   Automated Settlement Matching for eCommerce Bookkeeping    ║
    ╚═══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def check_requirements():
    """Check if all required packages are installed."""
    print("🔍 Checking dependencies...")
    
    required = ['flask', 'pandas', 'openpyxl']
    missing = []
    
    for package in required:
        try:
            __import__(package)
            print(f"  ✓ {package}")
        except ImportError:
            print(f"  ✗ {package}")
            missing.append(package)
    
    if missing:
        print(f"\n⚠️  Missing packages: {', '.join(missing)}")
        print(f"   Install with: pip install -r requirements.txt\n")
        return False
    
    return True

def create_directories():
    """Create necessary directories."""
    print("\n📁 Setting up directories...")
    
    dirs = ['uploads', 'sample_data']
    for dir_name in dirs:
        path = Path(dir_name)
        if not path.exists():
            path.mkdir()
            print(f"  ✓ Created {dir_name}/")
        else:
            print(f"  ✓ Found {dir_name}/")

def main():
    """Main startup routine."""
    print_banner()
    
    if not check_requirements():
        sys.exit(1)
    
    create_directories()
    
    print("\n✅ Environment ready!")
    print("\n📝 Next steps:")
    print("  1. Run: python app.py")
    print("  2. Open: http://localhost:5000")
    print("  3. Select a client portal and upload CSV files")
    print("\n💡 Sample files are available in sample_data/ folder")
    print("\n📖 See README.md for detailed documentation\n")

if __name__ == '__main__':
    main()
