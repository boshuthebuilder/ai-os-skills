#!/usr/bin/env python3
"""Check that this skill's catalogue still covers Wikipedia's "Signs of AI writing" essay.

Fetches the live essay (one MediaWiki API request: section tree + wikitext + revid),
extracts its section inventory, and diffs it against the coverage map in coverage.json —
where every essay section is either mapped to a section of REFERENCE.md/SKILL.md or
recorded as a deliberate exclusion. Drift is therefore detectable deterministically
instead of by re-reading both documents.

Usage:
    python3 tools/sync_check.py            # check against the sibling coverage.json
    python3 tools/sync_check.py --map P    # check against a different map (testing)
    python3 tools/sync_check.py --emit     # print the live inventory as JSON and exit 0

Typed exit codes:
    0  in sync — every live section accounted for. A changed revid alone is reported
       as informational (a copyedit is not coverage drift).
    1  coverage drift — the essay has sections this map does not account for (MISSING),
       or the map lists sections the essay no longer has (STALE).
    2  usage or map error — bad arguments, unreadable/invalid coverage.json.
    3  fetch or extraction failure. A check that did not run must never look like one
       that passed: offline means exit 3, not "assume in sync".
    4  soft drift — inventory matches but the essay's vocabulary digest changed;
       re-verify the era-tagged tiers in REFERENCE.md §16.

Section keys: the essay's {{shortcut|WP:X}} anchors where present (rename-stable),
otherwise "heading:<parent-slug>/<heading-slug>" path-qualified fallbacks. Headings that
appear inside quoted AI-output examples (syntaxhighlight/pre blocks) are ignored; the
API's parsed section tree is the ground truth and each tree entry is matched strictly,
in order, against the real headings in the wikitext.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import ssl
import sys
import unicodedata
import urllib.error
import urllib.request
from pathlib import Path

API = "https://en.wikipedia.org/w/api.php"
PAGE = "Wikipedia:Signs_of_AI_writing"
USER_AGENT = "ai-writing-audit-sync/1.0 (ai-tradecraft-skills; https://github.com/boshuthebuilder/ai-tradecraft-skills)"
VOCAB_KEY = "WP:AIVOCAB"
STATUSES = {"covered", "excluded", "container", "boilerplate"}

HEADING = re.compile(r"(?m)^(={1,6})[ \t]*(.*?)[ \t]*\1[ \t]*$")
SHORTCUT = re.compile(r"\{\{\s*[Ss]hortcut\s*\|\s*(WP:[A-Z0-9!-]+)")
LITERAL_BLOCKS = (
    r"<syntaxhighlight\b[^>]*>.*?</syntaxhighlight>",
    r"<pre\b[^>]*>.*?</pre>",
    r"<source\b[^>]*>.*?</source>",
    r"<nowiki>.*?</nowiki>",
    r"<code\b[^>]*>.*?</code>",
    r"<!--.*?-->",
)


def ssl_context() -> ssl.SSLContext:
    """Default trust store, falling back to certifi for Pythons that ship without one
    (e.g. python.org macOS builds). certifi is optional, like pypdf in audit.py."""
    ctx = ssl.create_default_context()
    if ctx.cert_store_stats().get("x509_ca", 0) == 0:
        try:
            import certifi  # type: ignore
            ctx = ssl.create_default_context(cafile=certifi.where())
        except ImportError:
            pass  # the request will fail loudly; the exit-3 hint names the fix
    return ctx


def fetch_page() -> dict:
    """One API request returning the parsed section tree, raw wikitext, and revid."""
    url = (f"{API}?action=parse&page={PAGE.replace(' ', '_')}"
           "&prop=sections|wikitext|revid&format=json&formatversion=2")
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30, context=ssl_context()) as resp:
        payload = json.load(resp)
    if "parse" not in payload:
        raise RuntimeError(f"unexpected API response: {list(payload)}")
    return payload["parse"]


def blank_literals(text: str) -> str:
    """Blank quoted-example blocks, preserving length, so their fake headings vanish."""
    for pattern in LITERAL_BLOCKS:
        text = re.sub(pattern, lambda m: " " * len(m.group(0)), text,
                      flags=re.DOTALL | re.IGNORECASE)
    return text


def norm_heading(line: str) -> str:
    """Normalise a heading for comparison between the API tree and raw wikitext."""
    line = line.replace("{{=}}", "=")
    line = re.sub(r"\{\{[^{}]*\}\}", "", line)
    line = re.sub(r"<[^>]+>", "", line)
    line = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r"\1", line)
    line = re.sub(r"'{2,}", "", line)
    line = unicodedata.normalize("NFKC", line)
    return re.sub(r"\s+", " ", line).strip().lower()


def slug(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).replace("–", "-").replace("—", "-")
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def extract_inventory(parse: dict) -> tuple[list[dict], dict]:
    """Return ([{key, level, heading}], vocab_digest) for the live essay.

    Strictly matches each entry of the API's parsed section tree, in order, to a real
    heading in the (example-blanked) wikitext; fails loudly on any mismatch rather than
    guessing, because a mis-keyed section would corrupt the diff.
    """
    sections = [s for s in parse["sections"] if str(s.get("index", "")).isdigit()]
    clean = blank_literals(parse["wikitext"])
    heads = [(m.start(), m.end(), len(m.group(1)), norm_heading(m.group(2)))
             for m in HEADING.finditer(clean)]

    matched: list[tuple[dict, tuple[int, int, int, str]]] = []
    cursor = 0
    for sec in sections:
        want_level, want_text = int(sec["level"]), norm_heading(sec["line"])
        hit = next((j for j in range(cursor, len(heads))
                    if heads[j][2] == want_level and heads[j][3] == want_text), None)
        if hit is None:
            raise RuntimeError(f"section {sec['number']} {want_text!r} not found in wikitext")
        matched.append((sec, heads[hit]))
        cursor = hit + 1

    inventory: list[dict] = []
    vocab_digest = {"key": VOCAB_KEY, "terms": 0, "sha256": ""}
    parent = ""
    for i, (sec, head) in enumerate(matched):
        body_end = matched[i + 1][1][0] if i + 1 < len(matched) else len(clean)
        body = clean[head[1]:body_end]
        text = norm_heading(sec["line"])
        if int(sec["level"]) == 2:
            parent = slug(text)
            fallback = f"heading:{parent}"
        else:
            fallback = f"heading:{parent}/{slug(text)}"
        shortcut = SHORTCUT.search(body)
        key = shortcut.group(1) if shortcut else fallback
        inventory.append({"key": key, "level": int(sec["level"]), "heading": text})
        if key == VOCAB_KEY:
            vocab_digest = digest_vocab(body)
    return inventory, vocab_digest


def digest_vocab(body: str) -> dict:
    """Digest the italicised watch-terms in the vocabulary section (before its examples).

    A digest, not a word diff: cosmetic list edits change the hash and warrant a human
    re-verify (exit 4), without hard-failing the coverage check on every copyedit.
    """
    body = body.split("'''Examples'''")[0]
    body = re.sub(r"<ref[^>]*/>", "", body)
    body = re.sub(r"<ref[^>]*>.*?</ref>", "", body, flags=re.DOTALL)
    body = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r"\1", body)
    body = re.sub(r"'''(.*?)'''", r"\1", body, flags=re.DOTALL)
    terms = sorted({t.strip().lower() for t in re.findall(r"''([^']{1,60}?)''", body)
                    if t.strip()})
    sha = hashlib.sha256("\n".join(terms).encode("utf-8")).hexdigest()
    return {"key": VOCAB_KEY, "terms": len(terms), "sha256": sha}


def load_map(path: Path) -> dict:
    try:
        cover = json.loads(path.read_text(encoding="utf-8"))
    except OSError as e:
        raise ValueError(f"cannot read coverage map {path}: {e}") from e
    except json.JSONDecodeError as e:
        raise ValueError(f"coverage map {path} is not valid JSON: {e}") from e

    sections = cover.get("sections")
    if not isinstance(sections, list) or not sections:
        raise ValueError("coverage map has no 'sections' list")
    seen: set[str] = set()
    for entry in sections:
        key, status = entry.get("key"), entry.get("status")
        if not key or key in seen:
            raise ValueError(f"missing or duplicate key in coverage map: {key!r}")
        seen.add(key)
        if status not in STATUSES:
            raise ValueError(f"{key}: invalid status {status!r}")
        if status == "covered" and not entry.get("ref"):
            raise ValueError(f"{key}: status 'covered' requires a 'ref'")
        if status == "excluded" and not entry.get("reason"):
            raise ValueError(f"{key}: status 'excluded' requires a 'reason'")
    if not isinstance(cover.get("source", {}).get("revid"), int):
        raise ValueError("coverage map source.revid must be an integer")
    return cover


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--map", type=Path,
                        default=Path(__file__).resolve().parent / "coverage.json")
    parser.add_argument("--emit", action="store_true",
                        help="print the live inventory as JSON and exit")
    args = parser.parse_args(argv[1:])

    try:
        parse = fetch_page()
        inventory, vocab = extract_inventory(parse)
    except (urllib.error.URLError, TimeoutError, RuntimeError, KeyError, OSError) as e:
        print(f"sync_check: FETCH FAILED — {e}", file=sys.stderr)
        if "CERTIFICATE_VERIFY_FAILED" in str(e):
            print("sync_check: this Python has no CA trust store; install certifi "
                  "(`pip3 install --break-system-packages certifi`).", file=sys.stderr)
        print("sync_check: a check that did not run is not a pass. Exit 3.", file=sys.stderr)
        return 3

    if args.emit:
        print(json.dumps({"source": {"page": PAGE, "api": API, "revid": parse["revid"]},
                          "sections": inventory, "vocab_digest": vocab}, indent=1))
        return 0

    try:
        cover = load_map(args.map)
    except ValueError as e:
        print(f"sync_check: MAP ERROR — {e}", file=sys.stderr)
        return 2

    live = {e["key"]: e for e in inventory}
    mapped = {e["key"]: e for e in cover["sections"]}
    missing = [live[k] for k in live.keys() - mapped.keys()]
    stale = [mapped[k] for k in mapped.keys() - live.keys()]

    if missing or stale:
        for e in sorted(missing, key=lambda e: e["heading"]):
            print(f"MISSING  {e['key']}  (essay: '{e['heading']}', L{e['level']}) — "
                  "not accounted for in coverage.json")
        for e in sorted(stale, key=lambda e: e["key"]):
            print(f"STALE    {e['key']}  ('{e.get('heading', '?')}') — mapped but no "
                  "longer on the essay")
        print(f"\nDRIFT: {len(missing)} missing, {len(stale)} stale. Update the "
              "catalogue and coverage.json, then refresh source.revid. Exit 1.")
        return 1

    old_revid = cover["source"]["revid"]
    if vocab["sha256"] != cover.get("vocab_digest", {}).get("sha256"):
        print(f"VOCAB DRIFT: the essay's vocabulary lists changed "
              f"({cover.get('vocab_digest', {}).get('terms', '?')} -> {vocab['terms']} terms; "
              f"revid {old_revid} -> {parse['revid']}).")
        print("Re-verify the era-tagged tiers in REFERENCE.md §16, then refresh "
              "coverage.json via --emit. Exit 4.")
        return 4

    note = ("" if parse["revid"] == old_revid else
            f" (page edited since sync: revid {old_revid} -> {parse['revid']}; "
            "inventory and vocabulary unaffected — refresh source.revid at leisure)")
    print(f"IN SYNC: all {len(live)} essay sections accounted for "
          f"({sum(1 for e in mapped.values() if e['status'] == 'covered')} covered, "
          f"{sum(1 for e in mapped.values() if e['status'] == 'excluded')} excluded, "
          f"rest structural){note}.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
