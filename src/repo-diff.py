from pathlib import Path
import subprocess
import sys
import logging
from typing import Optional, List, Tuple
from html import escape
import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from html_generator import generate_html_diff

try:
    from pygments import highlight
    from pygments.lexers import get_lexer_by_name, guess_lexer
    from pygments.formatters import HtmlFormatter
    PYGMENTS_AVAILABLE = True
except ImportError:
    PYGMENTS_AVAILABLE = False

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def init_repo(repo_path: Path) -> None:
    """Initialize a git repository at repo_path."""
    try:
        subprocess.run(['git', 'init'], cwd=repo_path, capture_output=True, text=True, encoding='utf-8', errors='replace', check=True)
        subprocess.run(['git', 'add', '.'], cwd=repo_path, capture_output=True, text=True, encoding='utf-8', errors='replace', check=True)
        subprocess.run(['git', 'commit', '-m', 'Initial commit'], cwd=repo_path, capture_output=True, text=True, encoding='utf-8', errors='replace', check=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to initialize git repository at {repo_path}: {e.stderr}")


def get_default_branch(repo_path: Path) -> str:
    """
    Get the default branch name for a repository.
    Tries master first, then main.
    """
    for branch in ['master', 'main']:
        result = subprocess.run(
            ['git', 'rev-parse', '--verify', f'refs/heads/{branch}'],
            cwd=repo_path,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        if result.returncode == 0:
            return branch

    raise RuntimeError(f"Cannot find default branch (master or main) in {repo_path}")


def validate_branch_exists(repo_path: Path, branch: str, is_remote: bool = False) -> bool:
    """Validate that a branch exists in the repository."""
    if is_remote:
        ref = f'refs/remotes/{branch}'
    else:
        ref = f'refs/heads/{branch}'

    result = subprocess.run(
        ['git', 'rev-parse', '--verify', ref],
        cwd=repo_path,
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='replace'
    )
    return result.returncode == 0


def add_temp_remote(repo_base: Path, repo_comp: Path) -> None:
    """Add comparison repository as a remote named 'comp'."""
    # Remove remote if it already exists (non-critical if it doesn't exist)
    subprocess.run(
        ['git', 'remote', 'remove', 'comp'],
        cwd=repo_base,
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='replace'
    )

    try:
        subprocess.run(
            ['git', 'remote', 'add', 'comp', str(repo_comp)],
            cwd=repo_base,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            check=True
        )
        subprocess.run(
            ['git', 'fetch', 'comp'],
            cwd=repo_base,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            check=True
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to add remote repository: {e.stderr}")


def remove_temp_remote(repo_base: Path) -> None:
    """Remove the temporary remote 'comp' to keep base repository clean."""
    subprocess.run(
        ['git', 'remote', 'remove', 'comp'],
        cwd=repo_base,
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='replace'
    )

def get_repo_diff(
    repo_base: Path,
    repo_comp: Path,
    branch_base: Optional[str] = None,
    branch_comp: Optional[str] = None
) -> Path:
    """
    Generate diff between two repositories on specified branches.

    Args:
        repo_base: Path to the base repository
        repo_comp: Path to the comparison repository
        branch_base: Branch name in base repository (default: master or main)
        branch_comp: Branch name in comparison repository (default: master or main)

    Returns:
        Path to the generated HTML report.
    """
    # Validate directories exist
    if not repo_base.is_dir():
        raise ValueError(f"{repo_base} is not a valid directory")
    if not repo_comp.is_dir():
        raise ValueError(f"{repo_comp} is not a valid directory")

    # Initialize repos if needed
    git_path_base = repo_base / '.git'
    git_path_comp = repo_comp / '.git'

    if not git_path_base.is_dir():
        init_repo(repo_base)

    if not git_path_comp.is_dir():
        init_repo(repo_comp)

    # Determine branch names - use defaults if not specified
    if branch_base is None:
        branch_base = get_default_branch(repo_base)

    if branch_comp is None:
        branch_comp = get_default_branch(repo_comp)

    # Validate branches exist
    if not validate_branch_exists(repo_base, branch_base):
        raise RuntimeError(f"Branch '{branch_base}' not found in {repo_base}")

    if not validate_branch_exists(repo_comp, branch_comp):
        raise RuntimeError(f"Branch '{branch_comp}' not found in {repo_comp}")

    # Add temporary remote and fetch
    add_temp_remote(repo_base, repo_comp)

    # Generate diff
    try:
        result = subprocess.run(
            ['git', 'diff', f'{branch_base}', f'comp/{branch_comp}'],
            cwd=repo_base,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            check=True
        )

        # Output to current directory / output
        output_dir = Path.cwd() / 'output'
        output_dir.mkdir(parents=True, exist_ok=True)

        basename = repo_base.resolve().name
        compname = repo_comp.resolve().name
        date_str = datetime.date.today().isoformat()
        html_file = output_dir / f"{date_str}-{basename}-{compname}-diffreport.html"

        title = f"Diff: {branch_base} → {branch_comp}"
        generate_html_diff(result.stdout, html_file, title)

        return html_file

    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to generate diff: {e.stderr}")
    finally:
        remove_temp_remote(repo_base)


def main() -> None:
    """Main entry point."""
    if len(sys.argv) < 3 or len(sys.argv) > 5:
        print("Usage: python repo-diff.py <repo_base> <repo_comp> [branch_base] [branch_comp]")
        print()
        print("Arguments:")
        print("  repo_base    - Path to the base repository")
        print("  repo_comp    - Path to the comparison repository")
        print("  branch_base  - Branch in base repository (default: master or main)")
        print("  branch_comp  - Branch in comparison repository (default: master or main)")
        print()
        print("Examples:")
        print("  # Compare master branches")
        print("  python repo-diff.py ./repo1 ./repo2")
        print()
        print("  # Compare specific branches")
        print("  python repo-diff.py ./repo1 ./repo2 develop feature/new")
        print()
        print("  # Compare develop in repo1 with main in repo2")
        print("  python repo-diff.py ./repo1 ./repo2 develop main")
        sys.exit(1)

    try:
        repo_base = Path(sys.argv[1])
        repo_comp = Path(sys.argv[2])
        branch_base = sys.argv[3] if len(sys.argv) > 3 else None
        branch_comp = sys.argv[4] if len(sys.argv) > 4 else None

        html_file = get_repo_diff(repo_base, repo_comp, branch_base, branch_comp)
        logger.info(f"Done: {html_file}")

    except (ValueError, RuntimeError) as e:
        logger.error(str(e))
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(130)


if __name__ == "__main__":
    main()
