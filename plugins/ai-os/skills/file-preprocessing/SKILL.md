---
name: file-preprocessing
description: >-
  Preprocess a staging folder of unorganised files (scans, photos of documents, emptied-out drives —
  any type) that belong to no project yet: understand each file, categorise it, rename it to a
  descriptive party-first name in UK English, merge split scans back into whole documents, and hand
  back a finished, self-contained run folder — while maintaining a portable audit pair inside the
  folder: manifest.json (hash-keyed machine source of truth, schema family-ai-preprocess-manifest/1)
  and AUDIT.md (its human-readable rendering). Hash-keyed idempotency makes runs incremental and
  lets any conforming agent (an automated engine, a Claude Code session, any other AI with file
  access) continue another's work on the same folder. Use when handed a drop folder of accumulated
  files to triage before they join any project; the audit is the durable artefact that makes a later
  onboarding — by any system — cheap.
---

# file-preprocessing

A staging folder is a **conveyor, not a library**: files are dropped into `Incoming/`, a run turns
the batch into its own dated folder under `Runs/`, and that finished parcel is carried off. The
folder stays self-describing through two files that travel with it:

- **`manifest.json`** — the machine source of truth. One entry per file, keyed by the file's SHA-256
  content hash, so identity survives renames and moves. Schema
  `family-ai-preprocess-manifest/1` (authoritative definition: `references/manifest-schema.md`).
- **`AUDIT.md`** — a deterministic rendering of the manifest for humans and cold AI readers:
  category sections, per-file summaries and key facts, connections between files, a "Needs a look"
  list, and a "No longer present" list. Regenerated wholesale from the manifest every run — it is a
  view, never a second source of truth.

Colocation is the export story: each run folder also carries its own manifest+audit **slice** (paths
rebased relative to the run folder), so a collected parcel still explains itself wherever it ends
up; the root pair is the long memory that survives parcels leaving.

## The folder contract

```
<Staging Folder>/
  Incoming/            ← humans drop files here (nested drops fine)
  INSTRUCTIONS.md      ← optional standing operator context, family-editable. The per-run pasted
                         note is the SAME capability behind the same parser: either channel may
                         open with a ---fenced YAML front-matter of STRUCTURED engine directives
                         (split-scan merge geometry; themes), stripped from the model-facing body
                         and validated strictly — a malformed block refuses the run naming its
                         source; a note-declared structure wins over a file-declared one. The
                         operator normally writes NEITHER: the planning step extracts structure
                         from plain prose (see the method), so context arrives as ordinary words
  manifest.json        ← maintained by this method (root memory)
  AUDIT.md             ← maintained by this method
  Runs/<YYYY-MM-DD HHMM>/          ← one folder per run — the parcel a run hands back
    <Category>/…                   ← processed files, one level of category folders
    <Theme>/<Category>/…           ← only when the operator declared themes: worlds above the
                                     categories, each file assigned against the declared list,
                                     unknowns in the declared catch-all
    Needs a look/<Reason>/…        ← ONLY files a human must decide about (see below) — always at
                                     the run root, never per-theme
    _Archive/…                     ← originals of merged split scans, straightened sideways scans, and split bundles
    manifest.json · AUDIT.md       ← this run's slice, paths rebased
    NEEDS A LOOK.md                ← written ONLY when Needs a look/ is non-empty
```

The run-folder name is minute-granular, so it must be **collision-safe by rule**: if the name
already exists (two runs in one minute, an immediate retry), suffix deterministically —
` (2)`, ` (3)`… — never reuse or overwrite an existing parcel.

Reserved names (`Incoming`, `Runs`, `INSTRUCTIONS.md`, `manifest.json`, `AUDIT.md`,
`NEEDS A LOOK.md`, dotfiles, and any `_`-prefixed system folder) are never treated as content.
Pending vs done is visible at a glance: `Incoming/` empties as work completes.

## Needs a look — a reasoned surface, never a dumping ground

"Needs a look" means **"read, but a human should decide"** — it must never mean "processing
failed". Two consequences:

- A file the understanding step simply failed to answer for **stays in `Incoming/`** with no
  manifest entry, and the next run retries it as an ordinary drop. Failures retry; they are not
  filed.
- A file lands under `Needs a look/` only with a **stated reason, and the subfolder IS the
  reason**: `Unrecognisable/` (no substantive read possible — keeps its original filename; there is
  nothing trustworthy to rename it by), `No date/` (a date exists on the document but could not be
  read; an undated-but-understood file just files normally with the date absent from its name),
  `Too large/` (beyond every processing tier — terminal, original name, never retried), and
  `Flagged/` (the model flags with a concrete stated reason). An unexplained "low confidence" is
  NOT a reason: it files the document normally. `NEEDS A LOOK.md` inside the run folder lists each
  file with its reason; its very presence is the signal — a clean run writes none.

## The method

Work through these steps; every step except **Understand** is deterministic.

1. **Scan.** Hash every file (SHA-256). In `Runs/`: confirm each manifest entry's file is still at
   its recorded path; adopt human moves (same hash at a new path → update the entry's placement —
   the human won that argument); spot edited files (known path, new hash) and strays (unknown path
   and hash). In `Incoming/`: a hash already live in the tree is a **duplicate** — leave it and
   note it; a hash whose entry is flagged `departed` is a **return** — reuse its
   recorded classification and filename with no model call, but place it into the CURRENT run's
   parcel, never back into the departed parcel its history names (that parcel has been carried
   off; recreating it would break the one-self-contained-parcel-per-run promise); the rest are
   candidates. Refuse to start while any dropped
   file is still a cloud placeholder — a partial run splits one logical drop across two parcels.
2. **Read — no arbitrary caps, a tiered ladder instead.** Extract text however the environment
   allows (a text read, OCR for scans/images, speech transcription for audio). Never truncate a
   long document and report it as whole: probe cheaply first (page count, text-layer presence) and
   pick a tier — a real text layer lifts in full at any size; a scan within the local OCR tier's
   measured capacity is read in full; past that, hand the whole file to a vision-capable model to
   read directly; past every tier, `Needs a look/Too large/` — a terminal, visible stop, never an
   infinite retry. A file with no extractable text at all is never guessed at: it goes to
   `Needs a look/Unrecognisable/` keeping its original stem, entry flagged `unreadable`.
3. **Straighten sideways scans — before pairing, so merges consume upright halves.** Decide the
   clockwise correction (0/90/180/270) from the READING DIRECTION of the page's recognised text
   lines, never from recognition scores (modern recognisers read text at any rotation nearly
   equally well, so every orientation scores the same); vote weighted by characters over
   confident lines, and act only on a clear win — a genuinely mixed page is left alone. Rewrite a
   clear-verdict scan upright (a content-lossless page-rotation), re-extract it so OCR reads
   upright pages, file the upright copy as the work item, and rest the sideways original in the
   run's `_Archive/` — lineage `rotated_from` on the filed copy, `rotated_into` +
   `archived_original` on the original, mirroring the merge pair's, and archived only once the
   upright copy's own move lands. A failed orientation check is counted and the file proceeds
   as-is — the check is an enhancement, never a hostage-taker.
4. **Merge split scans.** A duplex-less scanner saves one document as two PDFs: odd pages and even
   pages, marked in the name (单数/双数, 奇数页/偶数页, 单页/双页, "odd pages"/"even pages" — an
   extensible marker table; never bare "odd"/"even", which appear in ordinary titles). Pair
   marker-named files whose remaining stems match; gate on page counts that can actually
   interleave — odd leads by default (odd = even or even+1), and an operator directive in the
   `INSTRUCTIONS.md` front-matter can declare a pair **even-first** (its first odd page is
   missing) and/or a half **scanned backwards**, with the gate evaluated for the declared
   geometry:

   ```yaml
   ---
   merge:
     - match: "<substring of the marker-cleaned stem>"
       order: even_first          # default odd_first
       reverse_even: true         # and/or reverse_odd
       note: "<free text, recorded in the audit>"
   ---
   ```

   The planning step (step 7's whole-batch planning, which runs BEFORE this one) also extracts this
   geometry from the operator's plain prose, so the operator normally writes no YAML at all —
   extracted structure passes the same validators, and declared front-matter always wins.
   Interleave into ONE new document and process that as the work
   item; move both originals to the run's `_Archive/` with entries pointing at the merged entry.
   The merged entry's id is the merged FILE's own SHA-256, like every entry — the hash contract
   and the move guards in step 9 are unchanged. **Re-merge deduplication works through the
   halves**: each half keeps its own hash-keyed entry (`archived_half`, `merged_into` → the merged
   id; the merged entry lists both in `merged_from`), so a re-dropped half is an ordinary
   duplicate of an already-filed file and the pair is never re-merged. That linkage — not the
   merged bytes — is what makes the merge deduplicable at all: PDF writers embed creation
   metadata, so the same halves never merge to identical bytes twice. **A marker-named file whose
   twin is not in this batch files VISIBLY**: it is understood like any file and lands in
   `Needs a look/` under its understood name with an engine-derived "(odd pages only)"-style note
   in the filename — an invisible wait state misleads ("waiting" on a finished run implies the
   run will act later; it never does). The entry keeps `original_name` (marker intact), so a
   human can still pair it by hand if the twin ever arrives. (Supersedes v4.0–4.1's wait-state
   rule.) Only a pair whose counts cannot
   interleave (under its declared geometry, when one is declared), or a merge that failed, is a
   human decision (`Needs a look/Flagged/`, reason stated). **The originals archive in the same step that files the merged document, never
   earlier** — if understanding the merged document fails, the halves must still be sitting in
   `Incoming/` as ordinary candidates and no parcel may reference a document nobody filed.
5. **Split confident bundles.** One physical file sometimes holds several standalone documents
   (five reminder letters scanned as one PDF). The understanding step may propose a `split` —
   page ranges plus per-part fields — ONLY when the boundaries are certain and each part has its
   own date/type/parties. The engine validates a strict partition (every page exactly once, in
   order, ≥2 parts) and executes it whole or rejects it whole: a rejected proposal files the
   bundle as ONE document flagged with the reason, never a partial split. Parts are validated
   through the same entry path as any answer and flow through every later step; lineage mirrors
   the merge contract — parts carry `split_from`, the bundle archives to the run's `_Archive/`
   with `split_into` + the `archived_bundle` flag, and ONLY once every part's own move has
   landed. Keep part names concise ("PAYE Statutory Payment Repayment"), never an inventory.
6. **Understand** (the only non-deterministic step). For each readable candidate, decide: `party`,
   `doc_type` (short English type), `doc_date` (from the document's own content, ISO, never
   invented), `detail`, `title`, a rich 2–3 sentence `summary`, `key_facts` (dates, amounts,
   reference numbers actually read), `parties`, `category`, `connections` (real relationships to
   already-audited files, referenced by manifest id), an optional structured
   `look` + `look_reason` (see above), and honest flags. **Judge every file fresh from its
   content** — when re-processing a file the manifest already knows, exclude its own prior entry
   from any index shown to the model, so a stale verdict is never inherited; a rich summary is
   incompatible with an "unreadable"-style title. **A `date_unreadable` verdict from a text-only
   read earns one bounded second look with the actual file open before `No date/` ever sees it**
   — the proven failure is an extraction that truncated a date a human reads at a glance; only an
   answer with a real date and no attention request replaces the original judgement. **Name and
   describe in UK English by default**
   (general terms translate; a hard-to-translate proper noun keeps both forms side by side, so the
   file stays findable by either); `INSTRUCTIONS.md` is the channel to ask otherwise. Reuse an
   existing category when one fits; create a new one only when none does (case-insensitively —
   "medical" must never mint a second "Medical"). The attention buckets ("Needs a look", legacy
   "Needs Review") are never categories the model may choose.
7. **Reduce across the whole batch — after every group's answers validate, before anything
   applies.** (Its sibling, the whole-batch PLANNING call, runs before the merge: it designs the
   category vocabulary AND extracts operator structure — merge geometry, themes — from plain
   prose through exactly the front-matter validators; declared always wins over extracted.) Understanding in bounded groups leaves two things no group can settle: category
   consistency (a group's pick is an accident of packing) and relationships between files read in
   different groups. One reduce pass over every accepted entry's compact row (id, prospective
   filename, category, title, a short summary, date, parties) plus the prior-run index settles
   both: re-route files whose category disagrees with how the whole batch hangs together (never
   into an attention or archive placement — those are the engine's), and record the real
   relationships **on BOTH entries** — an invoice knows its receipt exactly as the receipt knows
   its invoice, including reverse links onto prior-run entries. Advisory by construction: a
   failed reduce leaves the groups' own judgements standing.
8. **Name and place — deterministically, from the fields.** Filename pattern:
   `<Party> - <DocType> <YYYY-MM-DD> <Detail>.<ext>` (e.g.
   `Jiayu - Lab Report 2026-03-14 CA125.pdf`). Fallbacks are fixed: unknown party → `Unknown`; no
   trustworthy date → the date segment is omitted, never fabricated; empty detail → omitted. Keep
   the extension, lowercased. Sanitise every segment (NFC-normalise; strip path separators,
   control characters, trailing dots/spaces; cap length in UTF-8 bytes — filesystem limits are
   byte limits). On a name collision append ` (2)`, ` (3)`… — never overwrite, never skip.
9. **Move under guards.** Source and target must both stay inside the folder (refuse `..`,
   absolute paths, and any symlinked path component). Create category/reason folders only when
   needed. After the move, verify the moved bytes' hash equals the entry id; a mismatch is a loud
   error, never a silent success. If the environment supports it, write a two-phase op log
   (intent → committed) fsync'd inside the folder (e.g. `.familyai/preprocess-log.jsonl`) and
   replay it on the next run so an interrupted move is resolved by content, and a committed move
   the manifest never learnt about is repaired from the log.
10. **Record.** Merge each entry into `manifest.json` (atomic write). A re-understood file keeps its
   identity fields (first seen, name history, placement) and refreshes the descriptive ones. An
   edited file is a new entry (new hash) understood **in place** — do not rename or move a file the
   human has already accepted under its name; the old entry departs.
11. **Reconcile presence — against a full walk, never a limited subset.** Entries whose file is no
   longer anywhere in the folder gain the `departed` flag with a last-seen stamp; entries are
   **never deleted** — the audit's history is the point. Under the conveyor model a whole run
   folder leaving is normal; its entries simply depart. A departed file's return sheds the flag.
12. **Render the views** from the manifest: `AUDIT.md` (self-describing header, sections by
   category, connections rendered to current filenames, "Needs a look" with each file's reason,
   "No longer present"), the run folder's manifest+audit slice, and `NEEDS A LOOK.md` when — and
   only when — the run's look folder is non-empty.

## Interop

Because entries are keyed by content hash and every mutation is guarded and recorded, runs are
idempotent and **agents compose**: an automated engine can do the bulk pass, a human can hand-move
files (adopted next run), and any other AI following this skill can pick up the same folder and
continue — same manifest, same naming, same semantics. Cost control on big backlogs: process a
bounded batch per run (oldest first) and re-run; the manifest makes every pass incremental. The
bound must be **split-scan aware** or it starves: a waiting half must not consume a batch slot
(oldest-first would re-select it every run, and with a small bound its twin — sitting just past
the boundary — would never be admitted, deadlocking the queue), and a selected half pulls its
twin into the same batch even from beyond the boundary, so a pair always travels together (the
bound is a cost cap, not an exact count).

The reference implementation is family-ai-os's `preprocess` engine (dashboard-triggered, chunked
LLM calls under a context budget with parallel chunk reads and strictly ordered applies, on-device
OCR + probe + orientation, native interleave-merge and page-rotation tools); this skill is the
portable spec any agent can execute by hand.
