# family-ai-preprocess-manifest/1 — the manifest schema

`manifest.json` at the staging-folder root. Top level:

```json
{
  "schema": "family-ai-preprocess-manifest/1",
  "generator_version": "<producer's own version string>",
  "generated_at": "<ISO datetime of the last write>",
  "entries": { "<sha256-hex>": { … } }
}
```

`entries` is keyed by the file's **SHA-256 content hash** — the entry's stable id. Identity follows
the bytes, not the name: renames and moves update `current_path`, never the key. An unknown
`schema` value must be treated as a foreign file (fail loud), never silently rewritten.

## Entry fields

| field | type | meaning |
|---|---|---|
| `id` | string | the sha256 hex, equal to the entry's key |
| `original_name` | string | the filename as dropped, before any rename |
| `current_path` | string | folder-relative path today, e.g. `Medical/Jiayu - Lab Report 2026-03-14 CA125.pdf` |
| `rename_history` | list | `{path, at, run_id}` per placement, oldest first |
| `category` | string | the category folder name |
| `title` | string | one-line title |
| `summary` | string | 2–3 sentences, the document's own language |
| `key_facts` | object | `{dates: [], amounts: [], reference_numbers: []}` — strings actually read from the document |
| `parties` | list of strings | every person/organisation involved |
| `doc_date` | string or null | ISO date from the document's content; null when none was trustworthy |
| `language` | string | primary language code (`en`, `zh`, …) |
| `pages` | int or null | page count when known |
| `extraction` | object | how the text was obtained: `{ocr: bool, tesseract: bool, speech: bool, status: string|null}` |
| `connections` | list | `{to: <sha256 of a related entry>, relation: <why>}` — real relationships only |
| `flags` | list of strings | named states, see below |
| `first_seen` | string | ISO datetime the file first entered the manifest |
| `processed_at` | string | ISO datetime of the last understanding pass |
| `departed_at` | string, optional | present only while `departed` is flagged |

## Flags

`low_confidence` (extraction was weak) · `unreadable` (no extractable text; filed to
`Needs Review/` unguessed) · `partial_read` (only part of the document was read, e.g. a page cap) ·
`undated` (no trustworthy document date) · `unknown_party` (party fell back to `Unknown`) ·
`departed` (the file is no longer anywhere in the folder; the entry is history, never deleted) ·
`needs_a_look` (a human should double-check the reading or an operation on it was skipped).

The vocabulary is extensible; consumers must ignore flags they don't know.

## Consumer rules

- Match files to entries by hash first, path second. A file whose hash is absent from `entries` has
  never been understood.
- Never delete an entry; `departed` marks absence.
- When writing, preserve identity fields you didn't re-derive (`first_seen`, `rename_history`,
  `original_name`), write atomically, and bump `generated_at`.
- `AUDIT.md` is derived; regenerate it from the manifest rather than editing it.
