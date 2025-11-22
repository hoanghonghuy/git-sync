# Git Sync Tool (`git-sync`)

A smart, safe, and fast command-line tool to automate your daily `add -> commit -> push` workflow. Written in Python, `git-sync` is designed to be highly configurable and extensible to fit your needs.

---
## Features

*   **Automation**: Combines `git add .`, `git commit`, and `git push` into a single, intelligent command.
*   **Conventional Commits**: Use flags like `--feat`, `--fix` to create standardized commit messages effortlessly.
*   **Branch Protection**: Warns you before committing directly to protected branches like `main` or `develop`.
*   **Smart Error Handling**: Automatically suggests running `git pull --rebase` on non-fast-forward errors.
*   **Auto Stash**: Use the `--stash` flag to automatically stash uncommitted changes before syncing and pop them after.
*   **Quick Tagging**: Add and push a Git tag for your releases with the `--tag` flag.
*   **Multi-Branch Sync**: Keep your main branches updated with the `--update-after` flag.
*   **Non-Interactive & Dry-Run**: Use `-y/--yes` to skip confirmations and `--dry-run` to print Git commands without changing anything.
*   **Hooks for Safety**: Optional `pre_sync` / `post_sync` hooks let you run tests or checks before/after syncing.
*   **Highly Configurable**: Customize protected branches, commit aliases, commit types, commit template, auto ticket-from-branch behavior, hooks, and language via a `.gitsyncrc` file.
*   **Multi-Language**: Supports English and Vietnamese out of the box.

---
## Installation

1.  **Prerequisites**: Ensure you have **Python** and **Git** installed and accessible in your system's PATH.
2.  Download the project files and place them in a dedicated directory (e.g., `D:\tools\git-sync`).
3.  **Create a batch file** (e.g., `git-sync.bat`) in a folder that is in your PATH (e.g., `D:\tools`). The content should be:
    ```batch
    @echo off
    python "D:\tools\git-sync\git_sync.py" %*
    ```
    *Replace `D:\tools\git-sync` with the actual path to your project.*

---
## Configuration

Create a `.gitsyncrc` file in your user home directory (for global settings) or in your project's root directory (for project-specific settings).

**Example `.gitsyncrc`:**
```ini
[settings]
# 'en' or 'vi'
language = vi
protected_branches = main, master, develop, release

# Optional: override default commit types used by the CLI flags
commit_types = feat, fix, chore, refactor, docs, style, perf, test, ci

# Optional: template for commit messages when using commit-type flags
# Available placeholders: {type}, {scope}, {message}, {ticket}
commit_template = [{ticket}] {type}{scope}: {message}

# Optional: automatically extract ticket IDs (e.g. ABC-123) from branch names
auto_ticket_from_branch = true

[hooks]
# Optional: run before/after sync (useful for tests, lint, etc.)
pre_sync = python -m pytest -q
post_sync = git status -sb

[commit_aliases]
# alias = full_commit_type
ref = refactor
ui = style
test = test
```

---
## Usage
Open your terminal in any Git repository and run the command.

### Basic Sync
```bash
# Interactive mode, will prompt for a commit message
git-sync
```

### Quick Commits & Aliases
```bash
# Using a standard commit type
git-sync --feat "Implement user login"

# Using a custom alias (if 'ui = style' is in .gitsyncrc)
git-sync --ui "Update button colors"
```

### Non-Interactive & Dry Run
```bash
# Skip confirmations on protected branches, commit review, and pull prompts
git-sync --feat "Implement login API" -s api -y

# See what would happen without changing anything
git-sync --feat "Check commands" -s api -y --dry-run
```

### Power Features
```bash
# Stash uncommitted changes, sync, and pop them back
git-sync --chore "Refactor config loader" --stash

# Create and push a tag after syncing
git-sync --feat "Release version 2.0.0" --tag v2.0.0

# Sync current branch, then update 'develop' and return
git-sync --fix "Hotfix critical bug" --update-after develop
```

### Dangerous Operations
```bash
# DANGER: Discard all local changes to match origin/main
git-sync --force-reset-to origin/main
```

---
## Testing

To run the automated test suite (unit + basic integration tests):

```bash
pip install pytest
pytest
```

For optional static type checking with `mypy`:

```bash
pip install mypy
mypy core git_sync.py
```

The repository also includes a GitHub Actions workflow (`.github/workflows/ci.yml`) that runs `mypy` and `pytest` on pushes and pull requests to `main` / `master`.

---