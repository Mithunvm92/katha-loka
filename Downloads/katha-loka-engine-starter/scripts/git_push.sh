#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

echo "======================================"
echo "       Katha Loka Git Push"
echo "======================================"

if ! command -v git >/dev/null 2>&1; then
    echo "ERROR: Git is not installed."
    exit 1
fi

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "ERROR: This project is not a Git repository."
    echo "Initialize Git and configure the GitHub remote first."
    exit 1
fi

if [[ -n "$(git ls-files --others --exclude-standard | grep -E '(^|/)\.env($|\.)|(^|/)id_rsa($|\.)' || true)" ]]; then
    echo "WARNING: Potentially sensitive files detected."
    echo "Review untracked files before proceeding."
    git status --short
    exit 1
fi

if ! git remote get-url origin >/dev/null 2>&1; then
    echo "ERROR: No 'origin' remote configured."
    echo "Configure your GitHub repository as origin first."
    exit 1
fi

echo
echo "Remote:"
git remote -v
echo
echo "Current changes:"
git status --short

if [[ -z "$(git status --porcelain)" ]]; then
    echo "No changes to commit. Pushing current branch..."
else
    echo
    read -r -p "Commit message [Update Katha Loka]: " COMMIT_MSG
    COMMIT_MSG="${COMMIT_MSG:-Update Katha Loka}"

    git add -A

    echo
    echo "Files staged for commit:"
    git diff --cached --stat
    git diff --cached --name-only

    echo
    echo "Review the staged changes above before continuing."
    read -r -p "Commit and push these files? (y/N): " CONFIRM
    [[ "$CONFIRM" =~ ^[Yy]$ ]] || {
        echo "Cancelled. Your changes remain uncommitted."
        exit 0
    }

    git commit -m "$COMMIT_MSG"
fi

BRANCH="$(git branch --show-current)"
if [[ -z "$BRANCH" ]]; then
    echo "ERROR: No current branch. Create or switch to a branch first."
    exit 1
fi

echo
echo "Pushing branch: $BRANCH"
git push -u origin "$BRANCH"

echo
echo "SUCCESS: Git push completed."
