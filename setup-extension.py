"""
SVG2Plotter — Inkscape Extension Setup
────────────────────────────────────────────────────────────────────
Installs dependencies and configures the environment.

  Linux / macOS : configures serial port permissions (dialout group)
  Windows       : installs pyserial via pip

Run once after cloning or extracting the repo:
  python setup-extension.py

Centro de Inovação Carlos Fiolhais · CDI Portugal
© 2026 David Marques — Vibe Coding with Claude.ai
"""

import sys
import os
import subprocess
import platform
import shutil

EXTENSION_FILES = ["svg2plotter_cut.inx", "svg2plotter_cut.py"]

def _find_inkscape_extensions_dir():
    """
    Returns the User Extensions path — checks real filesystem locations.
    Handles apt/deb, Flatpak, Snap and Windows installer variants.
    """
    home = os.path.expanduser("~")
    os_name = get_os()
    candidates = []
    if os_name == "linux":
        candidates = [
            os.path.join(home, ".config", "inkscape", "extensions"),
            os.path.join(home, ".var", "app", "org.inkscape.Inkscape",
                         "config", "inkscape", "extensions"),
            os.path.join(home, "snap", "inkscape", "current",
                         ".config", "inkscape", "extensions"),
        ]
    elif os_name == "darwin":
        candidates = [
            os.path.join(home, "Library", "Application Support",
                         "org.inkscape.Inkscape", "config", "inkscape", "extensions"),
        ]
    elif os_name == "windows":
        appdata = os.environ.get("APPDATA", "")
        candidates = [os.path.join(appdata, "inkscape", "extensions")]
    for path in candidates:
        if os.path.isdir(path):
            return path
    return candidates[0] if candidates else None

def banner():
    print()
    print("═" * 56)
    print("  SVG2Plotter — Inkscape Extension Setup")
    print("  Centro de Inovação Carlos Fiolhais · CDI Portugal")
    print("═" * 56)
    print()

def step(n, total, msg):
    print(f"  [{n}/{total}] {msg}")

def ok(msg=""):
    print(f"         ✓  {msg}" if msg else "         ✓")

def warn(msg):
    print(f"         ⚠  {msg}")

def err(msg):
    print(f"         ✗  {msg}")

def get_os():
    p = sys.platform
    if p.startswith("linux"):   return "linux"
    if p.startswith("darwin"):  return "darwin"
    if p.startswith("win"):     return "windows"
    return "unknown"

# ── Step 1: Python version ────────────────────────────────────────────────────
def check_python():
    step(1, 4, "Checking Python version...")
    v = sys.version_info
    if v.major < 3 or (v.major == 3 and v.minor < 8):
        err(f"Python 3.8+ required (found {v.major}.{v.minor})")
        sys.exit(1)
    ok(f"Python {v.major}.{v.minor}.{v.micro}")

# ── Step 2: Serial backend ────────────────────────────────────────────────────
def setup_serial():
    step(2, 4, "Checking serial communication backend...")
    os_name = get_os()

    if os_name in ("linux", "darwin"):
        # termios is stdlib — always available
        try:
            import termios
            ok("termios (stdlib) — no extra packages needed")
        except ImportError:
            warn("termios not available — trying pyserial as fallback...")
            _install_pyserial()
        return

    if os_name == "windows":
        try:
            import serial
            ok("pyserial already installed")
        except ImportError:
            print("         → pyserial not found. Installing...")
            _install_pyserial()
        return

    warn(f"Unrecognised OS ({os_name}) — trying pyserial...")
    _install_pyserial()

def _install_pyserial():
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "pyserial", "--quiet"],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        ok("pyserial installed")
    else:
        err("pip install pyserial failed")
        print(f"         {result.stderr.strip()}")
        print()
        print("         Try manually:")
        print(f"           pip install pyserial")
        sys.exit(1)

# ── Step 3: Serial port permissions (Linux) ───────────────────────────────────
def setup_permissions():
    step(3, 4, "Checking serial port permissions...")
    os_name = get_os()

    if os_name != "linux":
        ok("N/A on this OS")
        return

    user = os.environ.get("USER") or os.environ.get("LOGNAME", "")
    if not user:
        warn("Could not determine current user — skip permission setup")
        return

    # Check if already in dialout
    result = subprocess.run(["groups", user], capture_output=True, text=True)
    if "dialout" in result.stdout:
        ok(f"User '{user}' already in dialout group")
        return

    print(f"         → Adding '{user}' to dialout group...")
    result = subprocess.run(
        ["sudo", "usermod", "-aG", "dialout", user],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        ok("Done — log out and back in for the change to take effect")
    else:
        warn("Could not add to dialout automatically.")
        print()
        print("         Run this command manually and then log out/in:")
        print(f"           sudo usermod -aG dialout {user}")

# ── Step 4: Copy to Inkscape extensions folder ────────────────────────────────
def install_extension():
    step(4, 4, "Installing extension files into Inkscape...")
    os_name   = get_os()
    ext_dir   = _find_inkscape_extensions_dir()
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if ext_dir:
        print(f"         → Detected: {ext_dir}")

    if not ext_dir:
        warn("Could not determine Inkscape extensions folder.")
        _print_manual_instructions(script_dir)
        return

    # Check extension files exist next to this script
    missing = [f for f in EXTENSION_FILES
               if not os.path.exists(os.path.join(script_dir, f))]
    if missing:
        warn(f"Extension files not found next to setup script: {missing}")
        warn("Make sure svg2plotter_cut.inx and svg2plotter_cut.py are in the same folder.")
        return

    # Create folder if needed
    if not os.path.exists(ext_dir):
        try:
            os.makedirs(ext_dir, exist_ok=True)
            print(f"         → Created: {ext_dir}")
        except PermissionError:
            warn(f"Cannot create folder: {ext_dir}")
            _print_manual_instructions(script_dir)
            return

    # Copy files
    copied = []
    for f in EXTENSION_FILES:
        src = os.path.join(script_dir, f)
        dst = os.path.join(ext_dir, f)
        try:
            shutil.copy2(src, dst)
            copied.append(f)
        except Exception as e:
            warn(f"Could not copy {f}: {e}")

    if len(copied) == len(EXTENSION_FILES):
        ok(f"Copied to: {ext_dir}")
        print()
        print("         → Restart Inkscape")
        print("         → Extension appears at:")
        print("             Extensions → Export → Send to SVG2Plotter")
    else:
        warn("Some files could not be copied.")
        _print_manual_instructions(script_dir)

def _print_manual_instructions(script_dir):
    os_name = get_os()
    ext_dir = INKSCAPE_EXT_DIRS.get(os_name, "<inkscape extensions folder>")
    print()
    print("         Copy these files manually:")
    for f in EXTENSION_FILES:
        print(f"           {os.path.join(script_dir, f)}")
    print(f"         → to: {ext_dir}")
    print()
    print("         Or use Inkscape → Extensions → Manage Extensions")
    print("         → Install from file → select svg2plotter-inkscape-direct.zip")

# ── Summary ───────────────────────────────────────────────────────────────────
def summary():
    print()
    print("═" * 56)
    print("  SETUP COMPLETE")
    print()
    os_name = get_os()
    if os_name == "linux":
        print("  If dialout group was just added:")
        print("    → Log out and back in")
        print()
    print("  Restart Inkscape, then go to:")
    print("  Extensions → Export → Send to SVG2Plotter")
    print("═" * 56)
    print()

# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    banner()
    check_python()
    setup_serial()
    setup_permissions()
    install_extension()
    summary()
