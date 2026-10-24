# Katha Loka regression testing

## 1) Static/build checks (no extra packages)
From the repository root:
```bash
python3 scripts/build.py
python3 scripts/regression.py
```

## 2) Check the running website (no extra packages)
Terminal 1:
```bash
python3 -m http.server 8788 --directory site
```
Terminal 2:
```bash
python3 scripts/regression.py --url http://127.0.0.1:8788
```
Can also pass the Cloudflare Pages URL after deployment.

## 3) Browser interaction checks (optional, recommended)
Install:
```bash
python3 -m pip install playwright
python3 -m playwright install chromium
```
Start server as above, then:
```bash
python3 -m unittest tests/test_browser.py -v
```
Tests cover homepage/story card rendering, image loading, English/Kannada switching, story reader opening, previous/next scene buttons, JS exceptions, and a 390px mobile viewport.

Note: the static smoke tests do not click browser controls. The Playwright tests do. Resolve failures before pushing a release. These are baseline tests; add a test whenever a new user-facing feature is added.
