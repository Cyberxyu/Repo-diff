#!/usr/bin/env python3
"""
Entry point for repo-diff tool.
Run from project root: python main.py <repo_base> <repo_comp> [branch_base] [branch_comp]
"""
import sys
from pathlib import Path

# Determine base path: PyInstaller frozen or normal script
if getattr(sys, 'frozen', False):
    base_path = Path(sys._MEIPASS)
else:
    base_path = Path(__file__).parent

# Add src directory to path so we can import the modules
sys.path.insert(0, str(base_path / 'src'))

# Import and run main from the src module
import importlib.util
spec = importlib.util.spec_from_file_location("repo_diff", base_path / 'src' / 'repo-diff.py')
repo_diff_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(repo_diff_module)

if __name__ == "__main__":
    repo_diff_module.main()

