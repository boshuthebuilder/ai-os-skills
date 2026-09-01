# audit — the deterministic pass (a specification, not a prompt)

**This pass makes no model call and takes no placeholders.** It is a hashing walk plus a pure render,
so it sits entirely below the determinism boundary: the same folder state yields the same
`_Audit/manifest.json` and the same `_Audit/AUDIT.md`, byte for byte. The file is here because the
archetype's other job has a template and a reader will look for this one's; what it specifies is code
the deployment writes, not text a model reads.

The walk itself is the manifest reference's **scan contract**
(`plugins/ai-os/skills/file-preprocessing/references/manifest-schema.md`) — hash under the class
policy, confirm recorded paths, adopt human moves, spot edited files and strays, flag departed
entries. The manifest it maintains is `family-ai-preprocess-manifest/2`. The method behind every
computed field is the `folder-curation` skill; this file states what a conforming `audit` job must
produce, and nothing about *why*.

## What the pass computes

Per entry, on top of the scan contract's own fields:

- **A type class** from the project's class policy (`classes:` in `jobs.yaml`), which decides whether
  the entry is hashed in full or counted only.
- **Duplicate groups** by content hash across the whole tree, each member tagged `dup_kind`:
  `redundant`, `working_copy`, or `pack`. A count-only entry is never a duplicate candidate. A pack
  member carries `reference_copy_of` the canonical id.
- **Overlapping homes** — one subject with more than one folder its documents land in, detected by
  name and by duplicate groups spanning two trees. Recorded as a pair id on every participating
  entry (`overlap`), with the file count on each side.
- **Generic names** — a stem that is a device or scanner default (`generic_name`), counted per folder.
- **Unconverted formats** — an `iwork` or other proprietary file with no converted sibling
  (`unconverted`), counted per class and per folder, never per run.
- **Hygiene defects** (`hygiene`, kind in `look_reason`) — leading/trailing whitespace in a name,
  hidden system files, names differing only by case, path components over the filesystem's byte limit.
- **Root strays** (`root_stray`) — anything at the folder root that is not a declared reserved name.
- **Live vs closed** per top-level folder, from the newest modification and the density of recent
  changes.
- **Drift since the last pass** (from the second run on): added, removed, moved (same hash at a new
  path — adopted, not flagged), edited (same path, new hash), new duplicate groups, new root strays,
  and new files landing in an overlapping home.

## What the pass renders

`AUDIT.md` is a pure function of the manifest — **stamped from the manifest's own `generated_at`,
never from the clock**, so re-rendering an unchanged manifest is a no-op. Sections, in this order:

1. Header (folder, schema, `generated_at`, entry count)
2. **Summary by class** — per class: files, bytes, hashed vs count-only
3. **Root strays**
4. **Overlapping homes** — each pair with the count on each side
5. **Duplicate groups** — split by kind, with a per-kind count and per-kind totals
6. **Generic names** — per folder
7. **Unconverted formats** — per class and folder
8. **Hygiene**
9. **Live vs closed** — per top-level folder
10. **Drift since last pass** — omitted only on the first pass, which says so
11. **Needs a look** — findings a person must judge, each with its reason

**Every section prints its count, including zero.** A sweep that saw nothing and a healthy folder
must never read alike; a section that renders nothing at all is indistinguishable from a section that
never ran.

## Fail loud

- **An unreadable subtree is `error`, named with its path**, and the pass reports partial counts as
  partial — never a clean total over a tree it could not finish walking.
- **A cloud placeholder is `placeholder`**: refuse to hash it, report it, and carry on. This job is
  read-only, so a placeholder is a finding rather than the refusal-to-start it is in
  `file-preprocessing`.
- **A walk that cannot finish inside its budget reports `partial`** with the subtree it stopped in.
  A truncated walk that reports a clean count is the failure this whole archetype exists to make
  visible.
