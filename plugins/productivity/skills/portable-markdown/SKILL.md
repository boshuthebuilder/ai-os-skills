---
name: portable-markdown
description: >-
  Generate markdown files a person will actually open in a desktop editor — Typora, Obsidian, or a plain
  viewer — so the links land and no raw markup shows. Covers the link policy (a name that names a document
  should open it), destination encoding for spaces, brackets and CJK, anchors that render invisibly, table
  cells that survive model-written text, and HTML escaping inside inline elements. Use when a program or
  agent WRITES markdown for someone else to read: an audit or report over a folder of files, a generated
  index, a wiki page, a handover doc. Triggers include "the links don't work in Typora", "renders wrong in
  Obsidian", "markdown link with spaces or Chinese characters", "raw HTML showing in my markdown", "linking
  to a heading", and any task that emits .md a human opens rather than a browser renders.
---

# Portable markdown

A generated markdown file has two audiences: a renderer and a person. The trap is that "the renderer" is
not one renderer — the same file is opened in Typora, in Obsidian, and in whatever previews it in a
terminal or on GitHub, and their behaviour diverges in exactly the places generated documents lean on:
links, anchors, tables and inline HTML.

This skill is the set of rules that survive all of them, and the method for settling a question none of
them document. The verified behaviour matrix is in [`REFERENCE.md`](REFERENCE.md).

## The rule that prevents most of the damage

**A link's destination follows from what the link is FOR — and a name that names a document should open
that document.**

This sounds obvious and is the single most common defect in generated markdown, because the author is
thinking about document structure while the reader is thinking about the file. A summary table listing
"what happened to each of your files" exists to hand over documents; if its names jump to a section
further down the same page instead, every click is a small betrayal and the reader reports it as *the
links are broken*. They are not broken. They point at the wrong thing.

Split it by purpose:

| the link is… | destination |
|---|---|
| a name in a summary table, index, or list of documents | **the file** |
| a cross-reference inside an entry ("see the related entry", "merged from") | **in-document anchor** |
| a heading that titles a document's entry | **the file** (see *Anchors*) |

The file link is also the only form both Obsidian's and Typora's own help documents. Prefer it; treat the
in-document anchor as the extra you verified.

## Link destinations

**URL-encode the destination.** Obsidian's help is explicit — "make sure to URL encode the link
destination. For example, blank spaces become `%20`" — and Typora resolves the same. In Python:

```python
from urllib.parse import quote
quote(relative_path, safe="/")     # spaces → %20, & → %26, ( ) → %28 %29, CJK → percent-encoded
```

**Encoding the brackets is load-bearing, not cosmetic.** Most tooling parses a link destination as
`[^)]+` — including link linters you may already run — so a raw `)` inside a filename silently truncates
the destination. Filenames written by humans and scanners contain `(1)`, `& Co`, `#2` constantly.

**Keep the file extension.** Obsidian: "Links to file formats other than Markdown needs to include a file
extension."

**Relative destinations, resolved from the file's own folder.** If your document is nested (a dated run
folder, a subdirectory index), state the depth as a deliberate constant with a comment, not an accident —
and note that a path stored relative to a *different* root has to be rebased before it becomes a link.

## Anchors

If you need in-document targets — cross-references between entries — you need an id per entry. Three
constraints collide:

1. **An empty `<a id="x"></a>` renders as literal visible text in Typora.** Not invisible, not ignored:
   the reader sees `<a id="doc-4b1671ff4451"></a>` in front of every heading. Putting it on its own line
   is no better; it becomes a grey HTML block.
2. **A slug of the heading text is not portable.** Typora lowercases and hyphenates; Obsidian matches
   literal heading text via `[[Note#Heading]]` wikilinks; GitHub has its own slugger and its own
   duplicate-disambiguation order. Long, CJK-heavy, punctuation-heavy headings — exactly what filenames
   produce — diverge between all three, and two folders can hold the same basename.
3. **Custom heading id syntax (`{#id}`) is documented by neither**, though Typora happens to consume it.

What works: **one element carrying both the id and the href**, wrapping the visible text.

```markdown
### <a id="doc-4b1671ff4451" href="Design/ALWAYSFLOW%20-%20Price%20List.pdf">ALWAYSFLOW - Price List.pdf</a>
```

An `<a>` **with content** renders only its content, in Typora and in any CommonMark renderer, while still
providing the target that `[name](#doc-4b1671ff4451)` resolves against. Where there is no file to open
(the target is gone), keep the element and drop the `href` — never emit an empty one.

Mint the id from a **stable identity you already have** — a content hash, a record id — not from the
title. Twelve hex characters is collision-free at any realistic scale and is ASCII, so no renderer has to
agree with you about slugging.

**Assert that no empty anchor survives.** `assert "></a>" not in rendered` is one line and catches the
exact regression.

## Text inside an inline element must be HTML-escaped

The moment a name sits inside `<a>…</a>` it is HTML, not markdown text. `html.escape()` it. Filenames
carry `&` constantly ("Goldfish & Cruise Ship", "Teaware & Mino Ware") and an unescaped one is at best
wrong and at worst breaks the element. The `href` is separately percent-encoded, where `&` is already
`%26` — the two escapings are different and both are needed.

## Tables

- **Escape pipes** in any cell text you did not write yourself. Obsidian documents `\|`. A `|` inside a
  model-written sentence or a filename breaks the ROW rather than erroring, silently swallowing the
  remaining columns.
- **Collapse newlines** in cell text for the same reason.
- Both apply to *any* text you did not author: model output, filenames, user notes.

```python
def table_cell(text: str) -> str:
    return " ".join(str(text).split()).replace("|", "\\|")
```

## Keep the render a pure function

If the document is regenerated — an audit, an index, a dashboard page — make the renderer a pure function
of its data, with no clock and no filesystem probing, and stamp it from the data's own timestamp rather
than `now()`. Then an unchanged input renders byte-identical, which is what lets you detect a hand-edited
or deleted file and heal it without rewriting an intact one on every run. A single `datetime.now()` in the
header destroys that property.

## The method: verify by driving the editor

**None of the behaviour above is fully documented by either editor.** Typora's reference does not mention
custom heading ids; Obsidian's help covers only `&nbsp;` and `<br>` for HTML. So the honest way to settle
a question is a probe document, opened in the real application, clicked.

Write one markdown file containing the same destination in every form and context you are considering —
paragraph, list item, table cell, heading; markdown link and HTML anchor; encoded and raw — plus a target
that says plainly when it has been reached. Then open it and click each one. Ten minutes of this beats any
amount of reasoning about what *should* work, and it is the only way to catch the asymmetries: a construct
that renders correctly but does not navigate, or navigates but shows raw markup.

Two failure modes this catches that reading cannot:

- **A change that fixes rendering and breaks behaviour.** Moving a heading's file link out of a markdown
  link and into an HTML `href` can render more cleanly and still open the file — but you only know that
  because you clicked it, and if you verified only the rendering you shipped a regression.
- **A defect that is neither the format nor the setup.** Before blaming an editor's configuration, count
  what your document actually contains. "The links don't work" turned out, in the case this skill came
  from, to be 657 in-document anchors versus 177 file links: every link the reader clicked was doing
  exactly what it was told, and what it was told was wrong.

## Checklist

Before shipping a generator that writes markdown for a person:

- [ ] Every name that names a document links to **the document**, not to a section about it
- [ ] Destinations percent-encoded with `safe="/"`; brackets encoded; extension present
- [ ] No empty `<a></a>` anywhere — asserted in a test
- [ ] Ids minted from a stable identity, not from the title
- [ ] Text inside an inline element HTML-escaped; hrefs percent-encoded
- [ ] Table cells: pipes escaped, newlines collapsed, for any text you did not author
- [ ] Render is a pure function of its data — no clock, no filesystem
- [ ] Opened the real output in the editor the reader uses, and **clicked the links**

## Provenance

Rules verified 2026-08 against **Typora 1.14.9** (macOS) and the published help for both editors
([support.typora.io](https://support.typora.io/), [obsidian.md/help](https://obsidian.md/help/)). The
per-construct results, including which forms navigate and which only render, are in
[`REFERENCE.md`](REFERENCE.md). Re-verify after a major version of either editor: several of these
behaviours are undocumented and can therefore change without a note.
