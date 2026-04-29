#!/usr/bin/env python3
"""Build script to package repo-diff into a standalone executable."""

import subprocess
import sys

def main():
    """Run PyInstaller to create a single-file executable."""
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--name", "repo-diff",
        "--add-data", "src;src",
        "--add-data", "font;font",
        "--hidden-import", "html",
        "--hidden-import", "html.parser",
        "--hidden-import", "re",
        "--hidden-import", "datetime",
        "--hidden-import", "typing",
        "--hidden-import", "logging",
        "main.py"
    ]
    print("Running:", " ".join(cmd))
    subprocess.run(cmd, check=True)
    print("Build complete. Executable is in dist/repo-diff.exe")

if __name__ == "__main__":
    main()
