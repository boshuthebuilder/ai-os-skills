# folder-curation archetype

The job pair for keeping a **curated** folder honest after `folder-curation` has run (or for a folder
the owner wants audited without curation). Unlike `file-ingest`, neither job writes the wiki, and
unlike `file-preprocessing`, neither job moves the owner's files: `audit` is a deterministic pass
with no model call, and `curate` is **propose-only**. The design rationale is in
[`ARCHITECTURE.md`](../../../../ARCHITECTURE.md); the method is the `folder-curation` skill.

| job | mode | scheduling | scope |
|---|---|---|---|
| `audit` | `audit` | **periodic** (e.g. weekly), and on demand before and after a curation round | deterministic: re-walk the folder under the scan contract, refresh `_Audit/manifest.json` and `AUDIT.md`, report drift by class with counts |
| `curate` | `curate` | **on demand**, or periodic at a low cadence (monthly) once a project is live | one model call over the latest audit: proposes the next round's move-plan at the owner's chosen depth; never executes |

`audit` sits **below the determinism boundary**: same folder state, same manifest, same rendering. It
is declared as a job so the deployment schedules and reports it like one (liveness, counts, fail-loud
on an unreadable subtree), but it has no prompt template; `audit.md` specifies the pass.

## Files

- **`jobs.yaml`** — the two declarations to copy into a project's config.
- **`audit.md`** — what the deterministic `audit` pass computes and renders (no placeholders).
- **`curate.md`** — the `curate` job's prompt template.
- **`scheduler.md`** — how to wire the periodic audit and the on-demand curate.

## How to use

Stamp this archetype beside `file-ingest` on any project that went through `folder-curation`, or
alone on a folder the owner wants watched without a wiki. The templates are generic by design; a
deployment supplies the timer, the hashing walk, the CSV plan reader, and the deterministic guards
the `folder-curation` skill describes.
