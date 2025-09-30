# ☁️ Git Sync Tool (`git-sync`)

This is a command-line interface (CLI) tool written in Python that helps automate the daily `add -> commit -> push` workflow in a smart, safe, and fast way.

---
## ✨ Features

*   🚀 **Automation:** Combines the three commands `git add .`, `git commit`, and `git push` into a single command.
*   💬 **Quick Commits:** Supports flags like `--feat`, `--fix`, `--chore`, etc., to generate commit messages following the [Conventional Commits](https://www.conventionalcommits.org/) standard without manual typing.
*   🛡️ **Safe:** Automatically detects the current branch and issues a confirmation warning if you are trying to commit directly to protected branches (`main`, `master`, `develop`).
*   🔄 **Smart Error Handling:** When `git push` fails due to new commits on the remote, the tool will automatically ask if you want to run `git pull --rebase` and try again.

---
## 🛠️ Installation

#### **1. Prerequisites:**
*   **Python** and **Git** must be installed on your machine and added to the PATH environment variable.

#### **2. Configure as a Global Command (Windows):**
1.  Create the `D:\workspace\tools` directory (if it doesn't already exist).
2.  Create a subdirectory `D:\workspace\tools\git-sync`.
3.  Save the Python script file as `git_sync.py` inside the `git-sync` directory.
4.  In the `D:\workspace\tools` directory, create a new file named **`git-sync.bat`** with the following content:
    ```batch
    @echo off
    python "D:\workspace\tools\git-sync\git_sync.py" %*
    ```
5.  Ensure that the `D:\workspace\tools` directory has been added to your Windows PATH environment variable.

---
## 🎮 Usage

Open a terminal in your Git project directory and run the command.

**1. Interactive Mode (default):**
```bash
git-sync
```
The tool will run `git add .`, then prompt you for a commit message, and finally `git push`.

**2. Using Quick Commit Flags:**

```bash
# Add a new feature
git-sync --feat "Add login functionality"

# Fix a bug
git-sync --fix "Fix UI issue on mobile"

# Update documentation
git-sync --docs "Update installation guide"
```

**3. Example of Safety Warning:**
When you are on the `main` branch:
```
🚀 Starting Git sync process...
   Working on branch: [main]

⚠️  WARNING: You are about to commit directly to the 'main' branch.
   This action is not recommended. Are you sure you want to continue? (y/n):
```
---
## ⚙️ Custom Parameters
`--feat "MESSAGE"`: Commit with the `feat:` prefix.

`--fix "MESSAGE"`: Commit with the `fix:` prefix.

`--chore "MESSAGE"`: Commit with the `chore:` prefix.

`--refactor "MESSAGE"`: Commit with the `refactor:` prefix.

`--docs "MESSAGE"`: Commit with the `docs:` prefix.

`--style "MESSAGE"`: Commit with the `style:` prefix.

`-h, --help`: Show all available options.


---
