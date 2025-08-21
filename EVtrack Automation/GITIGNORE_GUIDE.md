# .gitignore Guide

Purpose

The `.gitignore` file tells Git which files and folders to ignore — i.e., not track or commit. It's essential for keeping secrets, local environment files, generated artifacts, large binaries and OS/IDE clutter out of your repository history.

Why this matters

- Prevents accidental commits of sensitive files (e.g. `.env`) containing credentials.
- Keeps repository size small by excluding build artifacts, dependencies and binary blobs.
- Avoids noisy diffs from editor or OS files (e.g. `.DS_Store`, `.vscode/`).

What to keep in `.gitignore` (recommended for this repo)

- Environment config / secrets: `.env`, `.env.*`
- Virtualenvs: `venv/`, `.venv/`, `env/`
- Python caches & builds: `__pycache__/`, `*.py[cod]`, `build/`, `dist/`
- Node packages: `node_modules/` (for deployment tooling)
- Deployment packaging: `.serverless/`, `*.zip`
- Editor/OS files: `.vscode/`, `.idea/`, `.DS_Store`, `Thumbs.db`
- Logs & temporary files: `*.log`, `tmp/`, `/tmp/`

Best practices

- Keep a `.env.example` (committed) with placeholder keys and no secrets so developers know required variables.
- Never commit secrets. If a secret is committed, rotate the secret immediately and remove it from Git history.
- Use environment-specific config only in CI/CD or in secret stores (AWS Secrets Manager, SSM Parameter Store, GitHub Secrets).

If a file is already committed

If a file is already tracked by Git (committed), simply adding it to `.gitignore` will not remove it from the repo. To stop tracking a file that is already committed, run:

- `git rm --cached <path/to/file>`
- Commit the change: `git commit -m "Stop tracking <file> and add to .gitignore"`

If the file contains sensitive values that must be removed from history, use specialized tools (BFG Repo-Cleaner or `git filter-branch`) and rotate secrets after cleanup. These operations rewrite history — coordinate with collaborators.
