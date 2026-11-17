#!/usr/bin/env python3
"""Basic safety checks for the CryptoNovice static HTML site."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
import sys

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_PAGES = {
    "index.html",
    "airdrops.html",
    "bitcoin-atms.html",
    "bitcoin-pizza-day.html",
    "coins-vs-tokens.html",
    "dont-sleep-on-altcoins.html",
    "fear-and-greed-index.html",
    "on-chain-analysis.html",
    "privacy-coins.html",
    "research-tools.html",
    "rwa-real-world-assets.html",
    "why-invest-in-bitcoin.html",
}

class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.targets = []
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        value = attrs.get("href") if tag == "a" else None
        if value:
            self.targets.append(value.strip())

def fail(message):
    print(f"FAIL: {message}")
    return False

ok = True
html_files = sorted(ROOT.glob("*.html"))
present = {p.name for p in html_files}
missing = sorted(REQUIRED_PAGES - present)
if missing:
    ok = fail("Required page(s) missing: " + ", ".join(missing)) and ok
else:
    print(f"PASS: all {len(REQUIRED_PAGES)} required pages are present.")

index = ROOT / "index.html"
if not index.exists():
    ok = fail("index.html is missing.") and ok
else:
    lines = len(index.read_text(encoding="utf-8").splitlines())
    if lines < 300:
        ok = fail(f"index.html has only {lines} lines; expected at least 300. Check for accidental truncation.") and ok
    else:
        print(f"PASS: homepage length looks plausible ({lines} lines).")

for page in html_files:
    content = page.read_text(encoding="utf-8")
    lowered = content.lower()
    if "<!doctype html" not in lowered[:200]:
        ok = fail(f"{page.name}: missing HTML doctype near the start.") and ok
    if "</html>" not in lowered:
        ok = fail(f"{page.name}: missing closing </html> tag.") and ok
    parser = Links()
    parser.feed(content)
    for raw in parser.targets:
        if not raw or raw.startswith(("#", "mailto:", "tel:", "javascript:", "data:")):
            continue
        parts = urlsplit(raw)
        if parts.scheme or parts.netloc:
            continue
        path = unquote(parts.path)
        if not path or not path.lower().endswith(".html"):
            continue
        target = (ROOT / path.lstrip("/")) if path.startswith("/") else (page.parent / path)
        target = target.resolve()
        try:
            target.relative_to(ROOT.resolve())
        except ValueError:
            ok = fail(f"{page.name}: link escapes the site directory: {raw}") and ok
            continue
        if not target.is_file():
            ok = fail(f"{page.name}: broken local HTML link: {raw}") and ok

if ok:
    print(f"PASS: checked {len(html_files)} HTML pages and their local HTML links.")
    sys.exit(0)
print("Site validation failed. Fix the reported issue before merging.")
sys.exit(1)
