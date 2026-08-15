#!/usr/bin/env python3
"""AI writing audit. Scan a document for the patterns catalogued in REFERENCE.md.

Usage:
    python3 tools/audit.py path/to/file.md
    python3 tools/audit.py path/to/file.pdf
    python3 tools/audit.py path/to/file.txt
    python3 tools/audit.py path/to/script.py   # extracts string literals

Grades every hit into one of three evidence bands and prints a cluster verdict:
    Band 1 (near-decisive)  leaked citation/tool markup; chat-mode leakage; very low
                            sentence-length variance
    Band 2 (fires in clusters)  negative parallelism, summaries, triplets, sycophancy,
                            copula-dodging, weasel attribution, document mechanics, ...
    Band 3 (contributory only)  vocabulary, hedging, transitions, flattery, em-dash density

Triage only. The scanner cannot judge rhythm nuance, elegant variation (REFERENCE.md §15),
brand voice, load-bearing formatting, or whether an attribution is earned. Read the
document yourself after the scan.
"""
from __future__ import annotations

import io
import re
import statistics
import sys
from pathlib import Path

# Every pattern is (name, regex, min_count): the pattern is reported only once the text
# contains at least min_count matches. Count gates keep phrases that are ordinary English
# in small doses ("rather than", "serves as") from firing on a single innocent use.
# Patterns in DENSITY_GATED are additionally judged per length — their words are common
# enough that any long document crosses a fixed count, so the gate scales to one hit per
# ~500 words. Distinctive phrase lists ("industry reports suggest") stay on absolute gates.
DENSITY_GATED = {"negative parallelism: X rather than Y", "copulative avoidance"}

# Band 1 — near-decisive. A single hit means the text was generated. These are leaked
# rendering tokens, not style; verify each was not a legitimate code sample.
ARTIFACTS: list[tuple[str, str, int]] = [
    ("ChatGPT citation markup",    r"oaicite|oai_citation|contentReference|attributableIndex|turn\d+(?:search|view|news|image)\d+", 1),
    ("Gemini citation markup",     r"\[cite:\s*\d+\]|\[cite_start\]|\[/?span_\d+\]|\[start_span\]", 1),
    ("Grok citation markup",       r"grok_card|grok_render_citation_card_json", 1),
    ("DeepSeek citation markup",   r"【[^】]{0,30}†[^】]{0,30}】", 1),
    ("Perplexity upload markup",   r"ppl-ai-file-upload|attached_file", 1),
    ("unclassified ':::writing'",  r":::(?:writing|écriture)\{", 1),
]

# Band 1 — chat-mode leakage. The assistant's own voice left in the document (REFERENCE.md
# §3). Provenance, not style; verify a hit is not quoted or deliberately meta text.
LEAKAGE: list[tuple[str, str, int]] = [
    ("AI self-disclosure",
                                   r"as\s+an\s+ai(?:\s+language)?\s+model|i\s+am\s+an\s+ai\b", 1),
    ("knowledge-cutoff disclaimer",
                                   r"(?:as\s+of|up\s+to)\s+my\s+(?:last|latest)\s+(?:training|knowledge)\s+(?:update|cut-?off)|my\s+knowledge\s+cut-?off", 1),
    ("source-availability disclaimer",
                                   r"not\s+(?:widely|extensively)\s+(?:available|documented|disclosed|transcribed)|in\s+the\s+provided\s+(?:sources?|search\s+results)|based\s+on\s+available\s+information|readily\s+available\s+sources", 1),
    ("direct address to operator",
                                   r"i\s+hope\s+this\s+helps|would\s+you\s+like\s+me\s+to\b|is\s+there\s+anything\s+else\s+(?:i|you)|i'?ve\s+inferred\b", 1),
    ("refusal residue",
                                   r"i\s+(?:cannot|can'?t)\s+(?:fulfil|fulfill|assist\s+with|help\s+with)\s+(?:this|that)\s+request", 1),
    ("unfilled placeholder",
                                   r"\[insert[^\]\n]{0,40}\]|\[your\s+\w{1,20}\]|\[describe[^\]\n]{0,60}\]|\[link\s+to[^\]\n]{0,40}\]|this\s+section\s+needs\s+expansion|\b20\d\d-xx-xx\b", 1),
]

# Band 2 — fires in clusters. Three or more distinct patterns stacked means AI-shaped.
CLUSTER: list[tuple[str, str, int]] = [
    ("negative parallelism: not only/but",
                                   r"\bnot\s+only\b[^.]{1,80}\bbut\b", 1),
    ("negative parallelism: not X, (it/but) Y",
                                   r"\b(?:it|this|that|we|you)(?:'s|'re|\s+(?:is|are|was|were))\s+not\s+[^.,;!?]{1,45}?[.,]\s+(?:it|but|this|that|we|you)\b", 1),
    ("negative parallelism: X rather than Y",
                                   r"\brather\s+than\b", 3),
    ("rule of three (x, y, and z)",
                                   r"\b(\w+),\s+(\w+),\s+and\s+(\w+)\b", 1),
    ("compulsive summary",
                                   r"\bin\s+conclusion\b|\bin\s+summary\b|\bto\s+summari[sz]e\b|(?:^|\.\s+)overall,", 1),
    ("outline-like conclusion",
                                   r"\bdespite\s+(?:these|the|its)\s+challenges\b|\bfaces?\s+several\s+challenges\b|\bfuture\s+(?:outlook|prospects|directions)\b|\blooking\s+ahead\b", 1),
    ("trailing -ing analysis",
                                   r",\s+\w+ing\s+(?:the|a|an|its|their|how|that|to)\b[^.]{1,80}\.", 1),
    ("false range: from X to Y",
                                   r"\bfrom\s+[a-z]+(?:\s+[a-z]+)?\s+to\s+[a-z]+\b", 1),
    ("sycophancy / collaborative framing",
                                   r"(?:^|\.\s+)(?:great\s+question|good\s+question|you'?re\s+absolutely\s+right|certainly!|of\s+course!|i'?d\s+be\s+happy\s+to|here'?s\s+the\s+kicker|the\s+truth\s+is\s+simple)|let'?s\s+(?:break\s+(?:this|it)\s+down|explore|dive\s+in|examine)|we\s+will\s+(?:explore|examine)|join\s+us\s+as\b|as\s+we\s+can\s+see\b", 1),
    ("copulative avoidance",
                                   r"\b(?:serves?|stands?|functions?|operates?)\s+as\b|\brepresents?\s+(?:a|an|the)\b|\bboasts?\s+(?:a|an|the)\b", 3),
    ("weasel attribution",
                                   r"\b(?:experts?|analysts?|observers?|critics?|scholars?|researchers?)\s+(?:argue|suggest|believe|note|say|claim|cite)|\bindustry\s+(?:reports?|publications?)\b|\bwidely\s+(?:regarded|considered|seen)\s+as\b|\bdescribed\s+in\s+scholarship\b", 2),
    ("significance inflation",
                                   r"\btestament\s+to\b|\benduring\s+(?:legacy|impact)\b|\bindelible\s+mark\b|\bpivotal\s+(?:role|moment)\b|\bkey\s+turning\s+point\b|\bevolving\s+landscape\b|\bdeeply\s+rooted\b|\bsetting\s+the\s+stage\s+for\b|\bcement(?:s|ed|ing)?\s+(?:its|his|her|their)\b|\bcontinues?\s+to\s+captivate\b|\bunderscor(?:es?|ing)\s+(?:its|the)\s+(?:importance|significance|role)\b|\bmaintains?\s+an?\s+active\s+social\s+media\s+presence\b", 2),
]

# Band 3 — contributory only. Never conclude from these alone; they count toward a cluster.
# Deliberately excludes flood-prone words ("key", "valuable", "crucial") that would bury
# the signal; REFERENCE.md §16 carries the full era-tagged list for the human pass.
WEAK: list[tuple[str, str, int]] = [
    ("vocab (fading GPT-4 era)",
                                   r"\bdelv\w*\b|\bintricate\w*\b|\btapestr\w*\b|\bpivotal\b|\bunderscor\w*\b|\bbolster\w*\b|\bgarner\w*\b|\binterplay\b", 1),
    ("vocab (still overused)",
                                   r"\bfoster\w*\b|\bseamless\b|\bleverag\w*\b|\bmyriad\b|\bplethora\b|\brealm\b", 1),
    ("vocab (Grok-flavoured)",
                                   r"\bcausal\b|\bempirical\b|\bcorrelate\w*\b", 2),
    ("hedging cliché",
                                   r"it\s+(?:is|'s)\s+(?:important\s+to\s+note|worth\s+noting)|(?:^|\.\s+)(?:notably|importantly),", 1),
    ("stock transition",
                                   r"(?:^|\.\s+)(?:furthermore|moreover|additionally),|that\s+being\s+said", 1),
    ("flattery / puffery",
                                   r"\bfascinat\w*\b|\bremarkable\b|\bcaptivat\w*\b|\btransformative\b|\bgroundbreaking\b|\bparadigm\s+shift\b|\bnestled\b|\bin\s+the\s+heart\s+of\b|\bdiverse\s+array\b|\brich\s+heritage\b", 1),
    ("double-hyphen dash",
                                   r"\w+--\w+", 1),
]

MD_SUFFIXES = {".md", ".markdown"}


def extract_text(path: Path) -> str:
    """Return body text from the file. Supports md, txt, py, pdf."""
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        try:
            import pypdf  # type: ignore
        except ImportError as e:
            sys.exit(
                "PDF input requires pypdf. Install with `pip3 install --break-system-packages pypdf`.\n"
                f"Original error: {e}"
            )
        reader = pypdf.PdfReader(str(path))
        return "\n".join(page.extract_text() or "" for page in reader.pages)

    text = path.read_text(encoding="utf-8", errors="replace")

    if suffix == ".py":
        # Extract string literals so we audit prose embedded in code.
        triple = re.findall(r'"""(.*?)"""', text, flags=re.DOTALL)
        triple += re.findall(r"'''(.*?)'''", text, flags=re.DOTALL)
        single = re.findall(r'"([^"\n]*)"', text)
        single += re.findall(r"'([^'\n]*)'", text)
        return "\n".join(triple + single)

    return text


def strip_frontmatter(text: str) -> str:
    """Remove a leading YAML frontmatter block so its --- fences are not counted as breaks."""
    m = re.match(r"\A---\s*\n.*?\n(?:---|\.\.\.)\s*\n", text, flags=re.DOTALL)
    return text[m.end():] if m else text


def scan(text: str, patterns: list[tuple[str, str, int]]) -> list[tuple[str, int, list[str]]]:
    """Return [(name, count, samples)] for patterns at or past their count gate."""
    words = len(text.split())
    results: list[tuple[str, int, list[str]]] = []
    for name, pattern, min_count in patterns:
        gate = max(min_count, words // 500) if name in DENSITY_GATED else min_count
        matches = re.findall(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
        if len(matches) >= gate:
            samples = []
            for m in matches[:3]:
                if isinstance(m, tuple):
                    samples.append(" ".join(s for s in m if s))
                else:
                    samples.append(str(m))
            results.append((name, len(matches), samples))
    results.sort(key=lambda r: -r[1])
    return results


def doc_mechanics(text: str) -> list[str]:
    """Markdown document-mechanics checks (REFERENCE.md §6), reported as ONE Band-2 pattern.

    The four sub-checks are habits of chat output that travel together; aggregating them
    stops correlated symptoms from counting as several independent cluster members.
    """
    text = strip_frontmatter(text)
    # Blank fenced code blocks: a `# comment` or `---` at column 0 inside a fence is
    # code, not a heading or a thematic break.
    text = re.sub(r"(?ms)^(```|~~~).*?^\1[^\n]*$", "", text)
    findings: list[str] = []

    headings = [(len(m.group(1)), m.group(2).strip())
                for m in re.finditer(r"(?m)^(#{1,6})\s+(\S.*)$", text)]

    l1 = sum(1 for level, _ in headings if level == 1)
    if l1 > 1:
        findings.append(f"{l1} top-level headings")

    jumps = sum(1 for (a, _), (b, _) in zip(headings, headings[1:]) if b - a >= 2)
    if jumps:
        findings.append(f"{jumps} skipped heading level(s)")

    stop = {"a", "an", "the", "and", "or", "of", "in", "on", "for", "to",
            "with", "at", "by", "from", "vs", "via", "as", "is", "are"}
    multi = []
    for _, title in headings:
        words = [w for w in re.findall(r"[A-Za-z][\w'-]*", title) if w.lower() not in stop]
        if len(words) >= 3:
            multi.append(all(w[0].isupper() for w in words))
    if len(multi) >= 2 and sum(multi) > len(multi) / 2:
        findings.append(f"Title Case in {sum(multi)}/{len(multi)} multi-word headings")

    breaks = len(re.findall(r"(?m)^(?:-{3,}|\*{3,}|_{3,})\s*$", text))
    if breaks >= 2:
        findings.append(f"{breaks} thematic breaks between sections")

    return findings


def burstiness(text: str) -> tuple[float | None, int]:
    """Sentence-length standard deviation and sentence count. See REFERENCE.md §2.

    Human academic prose runs ~8.2; GPT-4o ~4.1; Claude ~5.3. Low variance is the
    strongest stylistic tell. Returns (None, n) when there are too few sentences to judge.
    """
    sentences = [s for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s.strip()]
    lengths = [len(s.split()) for s in sentences if len(s.split()) >= 3]
    if len(lengths) < 8:
        return None, len(lengths)
    return statistics.pstdev(lengths), len(lengths)


def emdash_density(text: str) -> tuple[int, float]:
    """Em-dash count and rate per 100 words. See REFERENCE.md §20 (contributory, gameable)."""
    count = text.count("—") + len(re.findall(r"&mdash;", text, flags=re.IGNORECASE))
    words = max(1, len(text.split()))
    return count, count / words * 100


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    path = Path(argv[1]).expanduser()
    if not path.is_file():
        print(f"audit.py: {path} is not a file", file=sys.stderr)
        return 2

    try:
        text = extract_text(path)
    except Exception as e:  # noqa: BLE001 - triage tool, report and move on
        print(f"audit.py: failed to read {path}: {e}", file=sys.stderr)
        return 1

    words = len(text.split())
    artifacts = scan(text, ARTIFACTS)
    leakage = scan(text, LEAKAGE)
    cluster = scan(text, CLUSTER)
    if path.suffix.lower() in MD_SUFFIXES:
        mechanics = doc_mechanics(text)
        if mechanics:
            cluster.append(("document mechanics", len(mechanics), mechanics))
    weak = scan(text, WEAK)
    sd, n_sent = burstiness(text)
    em_count, em_rate = emdash_density(text)
    low_rhythm = sd is not None and sd < 5.0

    out = io.StringIO()
    out.write("AI writing audit\n")
    out.write(f"file:    {path}\n")
    out.write(f"length:  {len(text)} chars, ~{words} words\n")
    if sd is not None:
        out.write(f"rhythm:  sentence-length SD {sd:.1f} over {n_sent} sentences "
                  f"({'LOW — monotone, an AI tell' if low_rhythm else 'varied'})\n")
    else:
        out.write(f"rhythm:  too few sentences ({n_sent}) to judge burstiness\n")
    out.write(f"em-dash: {em_count} ({em_rate:.2f} per 100 words"
              f"{'; high' if em_rate > 1.0 else ''})\n\n")

    def dump(title: str, hits: list[tuple[str, int, list[str]]]) -> None:
        if not hits:
            return
        out.write(f"{title}\n")
        for name, count, samples in hits:
            sample_str = " | ".join(s[:40] for s in samples)
            out.write(f"  {count:>3}  {name:<38}  {sample_str}\n")
        out.write("\n")

    dump("Band 1 — near-decisive (leaked markup):", artifacts)
    dump("Band 1 — near-decisive (chat-mode leakage):", leakage)
    dump("Band 2 — fires in clusters:", cluster)
    dump("Band 3 — contributory only:", weak)

    # Verdict, mirroring REFERENCE.md "Scoring".
    if artifacts:
        verdict = "AI-shaped — leaked citation/tool markup (verify it is not a code sample)"
    elif leakage:
        verdict = "AI-shaped — chat-mode leakage (verify it is not quoted or meta text)"
    elif len(cluster) >= 3 or (len(cluster) >= 2 and low_rhythm):
        verdict = f"AI-shaped — {len(cluster)} Band-2 patterns clustered" + (
            " plus monotone rhythm" if low_rhythm else "")
    elif low_rhythm:
        verdict = "possibly AI-shaped — monotone rhythm; read for sentence variety before judging"
    elif cluster or weak:
        verdict = "inconclusive — scattered contributory hits; a person writes these too. Read for rhythm."
    else:
        verdict = "no tells found. Read the document yourself for tone and rhythm."
    out.write(f"VERDICT: {verdict}\n\n")

    out.write("Triage only. Rewrite to reduce cluster density, not to zero any single pattern.\n")
    out.write("The scanner cannot see rhythm nuance, elegant variation, brand voice, or\n")
    out.write("load-bearing bold. See REFERENCE.md.\n")
    print(out.getvalue())
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
