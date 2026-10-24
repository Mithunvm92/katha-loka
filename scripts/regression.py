#!/usr/bin/env python3
"""
Katha Loka smoke/regression checks.
Run from repository root:
  python3 scripts/regression.py
  python3 scripts/regression.py --url http://127.0.0.1:8788
  python3 scripts/regression.py --url https://YOUR-PAGES-DOMAIN
Uses Python standard library only.
"""
from __future__ import annotations
import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
STORIES_DIR = ROOT / "stories"

class MarkupParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids, self.links, self.images, self.scripts, self.styles = set(), [], [], [], []
        self.text_bits = []
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get("id"): self.ids.add(a["id"])
        if tag == "a" and a.get("href"): self.links.append(a["href"])
        if tag == "img" and a.get("src"): self.images.append(a["src"])
        if tag == "script" and a.get("src"): self.scripts.append(a["src"])
        if tag == "link" and a.get("rel") == "stylesheet" and a.get("href"): self.styles.append(a["href"])
    def handle_data(self, data):
        self.text_bits.append(data)

def fail(msg):
    print(f"FAIL  {msg}")
    return False

def ok(msg):
    print(f"PASS  {msg}")
    return True

def fetch(url, timeout=12):
    req = urllib.request.Request(url, headers={"User-Agent": "KathaLokaRegression/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return response.status, response.read(), response.headers.get_content_type()

def local_checks():
    results = []
    index = SITE / "index.html"
    if not index.exists():
        results.append(fail("site/index.html exists")); return results
    html = index.read_text(encoding="utf-8")
    parser = MarkupParser(); parser.feed(html)
    results.append(ok("site/index.html exists and parses"))
    for required in ("site-language", "story-grid", "new", "library"):
        results.append(ok(f"homepage has #{required}") if required in parser.ids else fail(f"homepage missing #{required}"))
    js = SITE / "assets/js/site.js"
    css = SITE / "assets/css/site.css"
    results.append(ok("homepage JavaScript exists") if js.is_file() else fail("homepage JavaScript missing"))
    results.append(ok("homepage CSS exists") if css.is_file() else fail("homepage CSS missing"))
    if js.exists():
        source = js.read_text(encoding="utf-8")
        results.append(ok("English and Kannada UI translations are defined") if '"en"' in source and '"kn"' in source else fail("language translations not found in site.js"))
        results.append(ok("story catalogue fetch is wired") if "stories.json" in source else fail("site.js does not load stories.json"))
    try:
        catalogue = json.loads((SITE / "stories.json").read_text(encoding="utf-8"))
        stories = catalogue.get("stories", [])
        results.append(ok(f"stories.json parses ({len(stories)} published stories)") if isinstance(stories, list) else fail("stories.json 'stories' must be a list"))
    except Exception as exc:
        stories = []
        results.append(fail(f"stories.json missing or invalid: {exc}"))
    for story in stories:
        slug = story.get("slug", "")
        for lang in ("en", "kn"):
            if not story.get("title", {}).get(lang) or not story.get("description", {}).get(lang):
                results.append(fail(f"{slug}: title/description missing {lang}"))
        reader = SITE / "stories" / slug / "index.html"
        results.append(ok(f"{slug}: generated reader page exists") if reader.is_file() else fail(f"{slug}: reader page missing"))
        story_dir = STORIES_DIR / slug
        try:
            scenes = json.loads((story_dir / "scenes.json").read_text(encoding="utf-8")).get("scenes", [])
            results.append(ok(f"{slug}: scene count matches metadata") if len(scenes) == story.get("sceneCount") else fail(f"{slug}: sceneCount mismatch"))
            for i, scene in enumerate(scenes, 1):
                for lang in ("en", "kn"):
                    if not scene.get("narration", {}).get(lang):
                        results.append(fail(f"{slug} scene {i}: missing {lang} narration"))
        except Exception as exc:
            results.append(fail(f"{slug}: scene file invalid: {exc}"))
    # Check all local image references declared by story catalogue.
    for story in stories:
        cover = story.get("cover", "")
        if cover.startswith("/") and not (SITE / cover.lstrip("/")).is_file():
            results.append(fail(f"{story.get('slug')}: cover asset missing: {cover}"))
        else:
            results.append(ok(f"{story.get('slug')}: cover asset exists"))
    # Reader controls and language code are simple source-level checks.
    reader_js = SITE / "assets/js/reader.js"
    reader_css = SITE / "assets/css/reader.css"
    for path, label in ((reader_js, "reader JavaScript"), (reader_css, "reader CSS")):
        results.append(ok(f"{label} exists") if path.is_file() else fail(f"{label} missing"))
    if reader_js.exists():
        s = reader_js.read_text(encoding="utf-8")
        for token, label in (("previous-scene", "Previous control"), ("next-scene", "Next control"), ("reader-language", "reader language selector")):
            results.append(ok(f"{label} is wired") if token in s else fail(f"{label} not wired"))
    return results

def http_checks(base):
    base = base.rstrip("/")
    results = []
    paths = ["/", "/stories.json", "/assets/js/site.js", "/assets/css/site.css", "/assets/css/reader.css", "/assets/js/reader.js", "/assets/images/story-world-hero.jpg", "/assets/images/tortoise-hare-cover.jpg", "/manifest.webmanifest"]
    try:
        for path in paths:
            try:
                status, body, content_type = fetch(base + path)
                good = status == 200 and len(body) > 0
                results.append(ok(f"HTTP {status} {path} ({len(body)} bytes)") if good else fail(f"{path}: unexpected response"))
            except Exception as exc:
                results.append(fail(f"{path}: {exc}"))
        try:
            status, body, _ = fetch(base + "/stories.json")
            catalogue = json.loads(body)
            for story in catalogue.get("stories", []):
                path = f"/stories/{story['slug']}/"
                try:
                    status, body, _ = fetch(base + path)
                    results.append(ok(f"HTTP {status} {path}") if status == 200 else fail(f"{path}: HTTP {status}"))
                except Exception as exc:
                    results.append(fail(f"{path}: {exc}"))
        except Exception as exc:
            results.append(fail(f"could not test reader routes: {exc}"))
    except Exception as exc:
        results.append(fail(f"HTTP test setup failed: {exc}"))
    return results

def main():
    ap = argparse.ArgumentParser(description="Katha Loka regression smoke tests")
    ap.add_argument("--url", help="Optional running local or deployed site URL")
    args = ap.parse_args()
    print("Katha Loka regression checks")
    print("============================")
    results = local_checks()
    if args.url:
        print(f"\nHTTP checks against {args.url}")
        results += http_checks(args.url)
    passed = sum(1 for x in results if x)
    failed = len(results) - passed
    print(f"\nResult: {passed} passed, {failed} failed")
    if failed:
        print("Do not publish until the failures are understood.")
        sys.exit(1)
    print("Smoke checks passed. Run the browser interaction suite before calling the site fully regression-tested.")

if __name__ == "__main__":
    main()
