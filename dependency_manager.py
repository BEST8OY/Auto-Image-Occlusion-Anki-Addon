"""
Dependency Manager for Auto Image Occlusion Addon

Ensures pytesseract and Pillow are available in the addon's libs/ directory.
"""

import os
import platform
import shutil
import subprocess
import sys

DEPS = {
    "pytesseract": {"version": "0.3.13", "import_name": "pytesseract"},
    "Pillow": {"version": "10.4.0", "import_name": "PIL"},
}
LIBS_DIR = os.path.join(os.path.dirname(__file__), "libs")
PIP_TIMEOUT = 30

_SYSTEM = platform.system()  # "Linux", "Darwin", "Windows"


def _python_executable(prefix):
    """Return the Python executable path for a given prefix."""
    if _SYSTEM == "Windows":
        return os.path.join(prefix, "Scripts", "python.exe")
    return os.path.join(prefix, "bin", "python3")


def _find_anki_python():
    """Find the Python interpreter that is running this addon.

    Since we're already inside Anki's Python process, sys.prefix points to
    the correct installation. We just need to locate the executable there.
    """
    for prefix in (sys.base_prefix, sys.prefix):
        exe = _python_executable(prefix)
        if os.path.isfile(exe):
            return exe

    # Fallback: walk up from addon dir looking for a python/ sibling folder
    addon_dir = os.path.dirname(__file__)
    for _ in range(6):
        exe = _python_executable(os.path.join(addon_dir, "python"))
        if os.path.isfile(exe):
            return exe
        addon_dir = os.path.dirname(addon_dir)

    return None


def _find_pip():
    """Locate a pip command compatible with the running Python."""
    anki_py = _find_anki_python()
    if anki_py:
        return [anki_py, "-m", "pip"]

    # Last resort: system pip
    for name in ("pip3", "pip"):
        path = shutil.which(name)
        if path:
            return [path]
    return None


def _is_installed(package):
    """Check if a package is already in libs/."""
    normalized = package.lower().replace("-", "_")
    if not os.path.isdir(LIBS_DIR):
        return False
    for entry in os.listdir(LIBS_DIR):
        if entry.endswith(".dist-info"):
            dist_name = entry.split("-", 1)[0].lower().replace("-", "_")
            if dist_name == normalized:
                return True
    return False


def _install(package, version):
    """Install a pinned package into libs/ via system pip."""
    pip = _find_pip()
    if not pip:
        raise RuntimeError("pip not found — install it manually (pip3 install pip)")

    cmd = pip + [
        "install",
        "--target", LIBS_DIR,
        "--no-deps",
        "--upgrade",
        "--no-warn-script-location",
        "--quiet",
        f"{package}=={version}",
    ]

    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )
    try:
        _, stderr = proc.communicate(timeout=PIP_TIMEOUT)
    except subprocess.TimeoutExpired:
        proc.kill()
        raise RuntimeError(
            f"pip timed out after {PIP_TIMEOUT}s — check your network"
        )

    if proc.returncode != 0:
        msg = stderr.decode("utf-8", errors="replace") if stderr else ""
        raise RuntimeError(f"pip install failed: {msg}")


def ensure_dependencies():
    """Ensure all dependencies are installed. Returns True on success."""
    os.makedirs(LIBS_DIR, exist_ok=True)

    if LIBS_DIR not in sys.path:
        sys.path.append(LIBS_DIR)

    for package, info in DEPS.items():
        if _is_installed(package):
            try:
                __import__(info["import_name"])
                continue
            except ImportError:
                pass

        print(f"[Auto Image Occlusion] Installing {package}=={info['version']}...")
        try:
            _install(package, info["version"])
            print(f"[Auto Image Occlusion] Installed {package}")
        except Exception as e:
            print(f"[Auto Image Occlusion] Failed to install {package}: {e}")
            return False

    return True
