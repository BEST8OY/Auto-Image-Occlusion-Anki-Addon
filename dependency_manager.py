"""
Dependency Manager for Auto Image Occlusion Addon
Automatically downloads and installs required packages on first startup.
"""

import sys
import os
import subprocess
import json
from pathlib import Path


def get_libs_dir():
    """Get the libs directory path"""
    return os.path.join(os.path.dirname(__file__), "libs")


def get_requirements_file():
    """Get the requirements.json path"""
    return os.path.join(os.path.dirname(__file__), "requirements.json")


def load_requirements():
    """Load required packages from requirements.json"""
    req_file = get_requirements_file()
    
    # Default requirements if file doesn't exist
    default_requirements = {
        "packages": {
            "Pillow": ">=10.0.0",
            "pytesseract": ">=0.3.10"
        }
    }
    
    if os.path.exists(req_file):
        try:
            with open(req_file, 'r') as f:
                return json.load(f)
        except Exception:
            return default_requirements
    
    return default_requirements


def check_package_installed(package_name):
    """Check if a package is already installed in libs"""
    libs_dir = get_libs_dir()
    
    try:
        # Try to import from libs
        spec = __import__('importlib.util').util.find_spec(package_name)
        if spec and libs_dir in str(spec.origin or ''):
            return True
    except (ImportError, AttributeError, ValueError):
        pass
    
    return False


def ensure_dependencies():
    """Ensure all required dependencies are installed. Downloads them on first startup."""
    libs_dir = get_libs_dir()
    
    # Create libs directory if it doesn't exist
    os.makedirs(libs_dir, exist_ok=True)
    
    # Add libs to path first
    if libs_dir not in sys.path:
        sys.path.insert(0, libs_dir)
    
    # Load requirements
    requirements = load_requirements()
    packages = requirements.get("packages", {})
    
    if not packages:
        return True  # No packages required
    
    all_installed = True
    
    for package_name, version_spec in packages.items():
        try:
            # Try importing to see if it's already available
            __import__(package_name)
            # If we get here, it's installed
            continue
        except ImportError:
            # Package not installed, need to download it
            all_installed = False
            print(f"[Auto Image Occlusion] Installing {package_name}...")
            
            try:
                install_package(package_name, version_spec, libs_dir)
                print(f"[Auto Image Occlusion] ✓ {package_name} installed successfully")
            except Exception as e:
                print(f"[Auto Image Occlusion] ✗ Failed to install {package_name}: {e}")
                return False
    
    if all_installed:
        print("[Auto Image Occlusion] All dependencies are available")
    
    return True


def install_package(package_name, version_spec, target_dir):
    """
    Install a package to the target directory using pip.
    
    Args:
        package_name: Name of the package to install
        version_spec: Version specification (e.g., ">=10.0.0")
        target_dir: Directory to install to
    """
    package_spec = f"{package_name}{version_spec}" if version_spec else package_name
    
    cmd = [
        sys.executable,
        "-m",
        "pip",
        "install",
        "--target", target_dir,
        "--no-warn-script-location",
        "--quiet",
        package_spec
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        raise Exception(f"pip install failed: {result.stderr}")


def create_requirements_file():
    """Create a requirements.json file in the addon directory"""
    req_file = get_requirements_file()
    
    if os.path.exists(req_file):
        return  # Already exists
    
    requirements = {
        "packages": {
            "Pillow": ">=10.0.0",
            "pytesseract": ">=0.3.10"
        },
        "description": "Dependencies for Auto Image Occlusion Addon"
    }
    
    try:
        with open(req_file, 'w') as f:
            json.dump(requirements, f, indent=2)
    except Exception as e:
        print(f"[Auto Image Occlusion] Could not create requirements.json: {e}")
