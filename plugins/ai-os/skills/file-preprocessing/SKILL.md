---
name: file-preprocessing
description: >-
  Preprocess a staging folder of unorganised files (scans, photos of documents, emptied-out drives —
  any type) that belong to no project yet: understand each file, categorise it, rename it to a
  descriptive party-first name, move it into a category subfolder, and maintain a portable audit pair
  inside the folder — manifest.json (hash-keyed machine source of truth, schema
  family-ai-preprocess-manifest/1) and AUDIT.md (its human-readable rendering). Hash-keyed
  idempotency makes runs incremental and lets any conforming agent (an automated engine, a Claude
  Code session, any other AI with file access) continue another's work on the same folder. Use when
  handed a drop folder of accumulated files to triage before they join any project; the audit is the
  durable artefact that makes a later onboarding — by any system — cheap.
---

# file-preprocessing

A staging folder is a holding pen, not a project. Files land in its `_Inbox/`; preprocessing moves
them out into category subfolders at the folder root under names that say what they are, and keeps
the folder self-describing through two files that travel with it:

- **`manifest.json`** — the machine source of truth. One entry per file, keyed by the file's SHA-256
  content hash, so identity survives renames and moves. Schema
  `family-ai-preprocess-manifest/1` (authoritative definition: `references/manifest-schema.md`).
- **`AUDIT.md`** — a deterministic rendering of the manifest for humans and cold AI readers:
  category sections, per-file summaries and key facts, connections between files, a "Needs a look"
  list, and a "No longer present" list. Regenerated wholesale from the manifest every run — it is a
  view, never a second source of truth.

Colocation is the export story: copy or share the folder and the audit goes with it. A future
project-onboarding (or any other AI) reads `manifest.json` instead of re-reading every file.

## The folder contract

```
<Staging Folder>/
  _Inbox/            ← humans drop files here (nested drops fine)
  INSTRUCTIONS.md    ← optional standing operator context, family-editable
  manifest.json      ← maintained by this method
  AUDIT.md           ← maintained by this method
  <Category>/…       ← processed files live here, at the root, one level of category folders
```

Reserved names (`_Inbox`, `INSTRUCTIONS.md`, `manifest.json`, `AUDIT.md`, dotfiles) are never
treated as content. Pending vs done is visible at a glance: `_Inbox` empties as work completes.

## The method

Work through these steps; every step except **Understand** is deterministic.

1. **Scan.** Hash every file (SHA-256). In the category tree: confirm each manifest entry's file is
   still at its recorded path; adopt human moves (same hash at a new path → update the entry's
   placement — the human won that argument); spot edited files (known path, new hash) and strays
   (unknown path and hash). In `_Inbox`: a hash already live in the tree is a **duplicate** — leave
   it and note it; a hash whose entry is flagged `departed` is a **return** — re-place it from its
   own recorded history with no model call; the rest are candidates.
2. **Read.** Extract text however the environment allows (a text read, OCR for scans/images, speech
   transcription for audio). A file with no extractable text is never guessed at: it goes to
   `Needs Review/` keeping its original stem, entry flagged `unreadable`.
3. **Understand** (the only non-deterministic step). For each readable candidate, decide: `party`
   (the person/organisation the document is about or addressed to), `doc_type` (short English
   type), `doc_date` (from the document's own content, ISO, never invented), `detail` (short
   distinguisher, in the document's own language), `title`, a rich 2–3 sentence `summary` (the
   document's language), `key_facts` (dates, amounts, reference numbers actually read),
   `parties`, `category`, `connections` (real relationships to already-audited files — an invoice
   and its receipt, an earlier result of the same test — referenced by manifest id), and honest
   flags. Follow `INSTRUCTIONS.md` and any per-run note; they outrank defaults. **Reuse an
   existing category when one fits; create a new one only when none does** (match
   case-insensitively — "medical" must never mint a second "Medical").
4. **Name and place — deterministically, from the fields.** Filename pattern:
   `<Party> - <DocType> <YYYY-MM-DD> <Detail>.<ext>` (e.g.
   `Jiayu - Lab Report 2026-03-14 CA125.pdf`). Fallbacks are fixed: unknown party → `Unknown`; no
   trustworthy date → the date segment is omitted, never fabricated; empty detail → omitted. Keep
   the extension, lowercased. Sanitise every segment (NFC-normalise; strip path separators,
   control characters, trailing dots/spaces; cap length in UTF-8 bytes — filesystem limits are
   byte limits). On a name collision append ` (2)`, ` (3)`… — never overwrite, never skip.
5. **Move under guards.** Source and target must both stay inside the folder (refuse `..`,
   absolute paths, and any symlinked path component). Create the category folder only when needed.
   After the move, verify the moved bytes' hash equals the entry id; a mismatch is a loud error,
   never a silent success. If the environment supports it, write a two-phase op log
   (intent → committed) fsync'd inside the folder (e.g. `.familyai/preprocess-log.jsonl`) and
   replay it on the next run so an interrupted move is resolved by content, and a committed move
   the manifest never learnt about is repaired from the log.
6. **Record.** Merge each entry into `manifest.json` (atomic write). A re-understood file keeps its
   identity fields (first seen, name history, placement) and refreshes the descriptive ones. An
   edited file is a new entry (new hash) understood **in place** — do not rename or move a file the
   human has already accepted under its name; the old entry departs.
7. **Reconcile presence — against a full walk, never a limited subset.** Entries whose file is no
   longer anywhere in the folder gain the `departed` flag with a last-seen stamp; entries are
   **never deleted** — the audit's history is the point. A departed file's return sheds the flag.
8. **Render `AUDIT.md`** from the manifest: self-describing header (what this file is, the schema
   id, a pointer to this skill, counts, generated-by), sections by category, connections rendered
   to current filenames, then "Needs a look" (unreadable / low-confidence / partial reads /
   anything the model flagged) and "No longer present".

## Interop

Because entries are keyed by content hash and every mutation is guarded and recorded, runs are
idempotent and **agents compose**: an automated engine can do the bulk pass, a human can hand-move
files (adopted next run), and any other AI following this skill can pick up the same folder and
continue — same manifest, same naming, same semantics. Cost control on big backlogs: process a
bounded batch per run (oldest first) and re-run; the manifest makes every pass incremental.

The reference implementation is family-ai-os's `preprocess` engine (dashboard-triggered, chunked
LLM calls under a context budget, on-device OCR); this skill is the portable spec any agent can
execute by hand.
