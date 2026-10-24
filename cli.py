#!/usr/bin/env python3
"""Katha Loka CLI Studio: stories, tests, GitHub and Cloudflare."""

import json
import re
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SCRIPTS = ROOT / "scripts"
STORIES = ROOT / "stories"
SITE = ROOT / "site"
TEST_URL = "http://127.0.0.1:8788"

# Explicitly approved project paths for staging.
# Never stage the entire working tree automatically.
APPROVED_PATHS = [
    "cli.py",
    "README.md",
    ".gitignore",
    "package.json",
    "wrangler.toml",
    "scripts",
    "tests",
    "stories",
    "site",
    ".github",
]

BLOCKED = re.compile(
    r"(^|/)(\.env($|\.)|\.venv|\.wrangler|backups|node_modules|"
    r"__pycache__)(/|$)|(^|/)(id_rsa|id_ed25519|credentials|"
    r"secrets\.json)$|\.(pem|key|p12|pfx)$",
    re.I,
)


def command(args, capture=False):
    print("\n$ " + " ".join(map(str, args)))
    try:
        result = subprocess.run(
            list(map(str, args)), cwd=ROOT, text=True,
            capture_output=capture
        )
    except FileNotFoundError:
        print(f"ERROR: command not found: {args[0]}")
        return None

    if capture:
        if result.stdout:
            print(result.stdout, end="")
        if result.stderr:
            print(result.stderr, end="", file=sys.stderr)
    if result.returncode:
        print(f"Command failed with exit code {result.returncode}")
    return result


def confirm(message):
    return input(f"{message} [y/N]: ").strip().lower() in ("y", "yes")


def pause():
    input("\nPress Enter to return to menu...")


def git_root():
    if not shutil.which("git"):
        print("Git is not installed.")
        return None

    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=ROOT, text=True, capture_output=True
    )
    if result.returncode:
        print("This directory is not inside a Git repository.")
        return None

    actual = Path(result.stdout.strip()).resolve()
    if actual != ROOT.resolve():
        print("\nGIT SAFETY STOP")
        print(f"Expected repository root: {ROOT.resolve()}")
        print(f"Actual repository root:   {actual}")
        print("No Git changes will be staged, committed or pushed.")
        print("Fix the repository boundary before using Git options.")
        return None
    return actual


def git_status():
    if git_root():
        command(["git", "status", "--short", "--branch"])


def list_stories():
    print("\nSTORIES")
    if not STORIES.exists():
        print("stories/ directory not found.")
        return

    folders = sorted(p for p in STORIES.iterdir() if p.is_dir())
    if not folders:
        print("No stories found.")
        return

    for folder in folders:
        path = folder / "story.json"
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            title = data.get("title", folder.name)
            if isinstance(title, dict):
                title = title.get("en", folder.name)
            status = data.get("status", "unknown")
        except Exception:
            title, status = folder.name, "invalid/missing JSON"
        print(f"{folder.name:30} | {status:12} | {title}")


def create_story():
    slug = input("Story slug (e.g. the-lion-and-the-mouse): ").strip().lower()
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
        print("Use lowercase letters, numbers and hyphens.")
        return
    if (STORIES / slug).exists():
        print("That story already exists.")
        return

    script = SCRIPTS / "new_story.py"
    if not script.exists():
        print("Missing scripts/new_story.py")
        return
    if confirm(f"Create draft '{slug}'?"):
        result = command([sys.executable, script, slug])
        if result and result.returncode == 0:
            print("Draft created. Add translations and artwork before publishing.")


def build():
    script = SCRIPTS / "build.py"
    if not script.exists():
        print("Missing scripts/build.py")
        return False
    result = command([sys.executable, script])
    return result is not None and result.returncode == 0


def regression():
    script = SCRIPTS / "regression.py"
    if not script.exists():
        print("Missing scripts/regression.py")
        return False
    result = command([sys.executable, script])
    return result is not None and result.returncode == 0


def browser_tests():
    testfile = ROOT / "tests" / "test_browser.py"
    if not testfile.exists():
        print("Missing tests/test_browser.py")
        return False

    try:
        urllib.request.urlopen(TEST_URL, timeout=1).close()
        server = None
    except Exception:
        server = subprocess.Popen(
            [sys.executable, "-m", "http.server", "8788",
             "--bind", "127.0.0.1", "--directory", str(SITE)],
            cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        ready = False
        for _ in range(30):
            if server.poll() is not None:
                break
            try:
                urllib.request.urlopen(TEST_URL, timeout=1).close()
                ready = True
                break
            except Exception:
                time.sleep(0.25)
        if not ready:
            print("Could not start test server on port 8788.")
            server.terminate()
            server.wait()
            return False

    try:
        result = command([
            sys.executable, "-m", "unittest", "tests.test_browser", "-v"
        ])
        return result is not None and result.returncode == 0
    finally:
        if server is not None:
            server.terminate()
            try:
                server.wait(timeout=3)
            except subprocess.TimeoutExpired:
                server.kill()


def all_checks():
    print("\n=== BUILD ===")
    if not build():
        return False
    print("\n=== REGRESSION TESTS ===")
    if not regression():
        return False
    print("\n=== BROWSER TESTS ===")
    if not browser_tests():
        return False
    print("\nALL CHECKS PASSED.")
    return True


def safe_commit():
    if not git_root():
        return

    print("\nCurrent status:")
    command(["git", "status", "--short", "--branch"])

    if not confirm("Stage approved project paths for review?"):
        return

    # Stage only paths explicitly inside this repository.
    args = ["git", "add", "--"] + APPROVED_PATHS
    result = command(args)
    if result is None or result.returncode:
        return

    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        cwd=ROOT, text=True, capture_output=True
    )
    files = result.stdout.splitlines()
    if not files:
        print("No staged changes.")
        return

    print("\nFiles staged for commit:")
    for filename in files:
        print("  " + filename)

    blocked = [f for f in files if BLOCKED.search(f)]
    outside = [
        f for f in files
        if Path(f).is_absolute() or ".." in Path(f).parts
    ]
    if blocked or outside:
        print("SAFETY STOP: suspicious staged paths detected.")
        print("Review and unstage them before proceeding.")
        return

    if not confirm("Commit exactly these files?"):
        print("Changes remain staged; no commit made.")
        return

    message = input("Commit message: ").strip()
    if not message:
        print("Commit message cannot be empty.")
        return

    command(["git", "commit", "-m", message])


def push():
    if not git_root():
        return

    status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=ROOT, text=True, capture_output=True
    )
    if status.stdout.strip():
        print("Working tree has uncommitted changes.")
        print("Commit or review them before pushing.")
        command(["git", "status", "--short"])
        return

    branch = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=ROOT, text=True, capture_output=True
    ).stdout.strip()
    remote = subprocess.run(
        ["git", "remote", "get-url", "origin"],
        cwd=ROOT, text=True, capture_output=True
    )
    if not branch or remote.returncode:
        print("Could not identify branch or origin remote.")
        return

    print(f"Repository: {ROOT}")
    print(f"Remote: {remote.stdout.strip()}")
    print(f"Branch: {branch}")
    if confirm("Push this branch to origin?"):
        command(["git", "push", "-u", "origin", branch])


def deploy():
    if not shutil.which("npx"):
        print("npx not found. Install Node.js/npm first.")
        return
    if not (ROOT / "wrangler.toml").exists():
        print("wrangler.toml missing.")
        return

    if not confirm("Build and run every check before deployment?"):
        return
    if not all_checks():
        print("Deployment blocked: a check failed.")
        return

    if confirm("Deploy verified site to Cloudflare now?"):
        command(["npx", "wrangler", "deploy"])


def live_check():
    url = "https://katha-loka.delimstudio.workers.dev"
    try:
        with urllib.request.urlopen(url, timeout=15) as response:
            print(f"Live homepage: HTTP {response.status}")
        with urllib.request.urlopen(url + "/stories.json", timeout=15) as response:
            data = json.loads(response.read().decode("utf-8"))
            print(f"Story data: HTTP {response.status}; {len(data.get('stories', []))} stories")
    except Exception as exc:
        print(f"Live check failed: {exc}")


def main():
    while True:
        print("""
========================================
       KATHA LOKA — CLI STUDIO
========================================
STORIES
  1. List stories
  2. Create new story
  3. Build website

TESTING
  4. Run regression tests
  5. Run browser tests
  6. Run all checks

GITHUB
  7. View Git status
  8. Commit approved changes
  9. Push to GitHub

CLOUDFLARE
 10. Deploy (build + test first)
 11. Check live website

  0. Exit
========================================
""")
        choice = input("Select option: ").strip()
        if choice == "1":
            list_stories(); pause()
        elif choice == "2":
            create_story(); pause()
        elif choice == "3":
            build(); pause()
        elif choice == "4":
            regression(); pause()
        elif choice == "5":
            browser_tests(); pause()
        elif choice == "6":
            all_checks(); pause()
        elif choice == "7":
            git_status(); pause()
        elif choice == "8":
            safe_commit(); pause()
        elif choice == "9":
            push(); pause()
        elif choice == "10":
            deploy(); pause()
        elif choice == "11":
            live_check(); pause()
        elif choice == "0":
            print("Katha Loka CLI closed.")
            break
        else:
            print("Choose a valid option.")


if __name__ == "__main__":
    main()
