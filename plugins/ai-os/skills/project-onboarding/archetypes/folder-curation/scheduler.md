# Scheduling the folder-curation jobs

How a deployment wires the two jobs. Platform-agnostic — the concrete timer is yours (a launch agent,
a cron entry, a systemd timer, a person running a command). The shared design is in
[`ARCHITECTURE.md`](../../../../ARCHITECTURE.md).

## `audit` — periodic, plus on demand around a round

A whole-folder hashing walk is not triggered by a single change, so it runs on a **fixed cadence**
(e.g. weekly, off-hours). It is also run **on demand twice per curation round**: once before, as the
baseline every proposed row is evidenced against, and once after, as the verify pass that proves the
executed rows and nothing else.

It makes **no model call at all**, so its cost is disk and wall-clock, not spend. The class policy is
what keeps that bounded: count-only classes cost a count rather than a hash walk, so a library that is
mostly photographs or imaging stays cheap to keep.

- **Contention is a clean skip, not an error.** A tick that fires while a previous run still holds the
  project lock skips quietly. Under a weekly cadence this is rare; treat "already running" as success.
- **A walk that cannot finish inside its budget reports `partial`**, naming the subtree it stopped in
  — never a clean count over a tree it did not finish. This is the whole liveness signal of the job:
  an `audit` that never ran and an `audit` that ran over a healthy folder must look different.
- **Run at load** so a folder that changed while the machine was down is re-walked on restart.

## `curate` — on demand, or a low periodic cadence

`curate` runs when a person asks for the next round, or on a low cadence (e.g. monthly) once a project
is live, to surface the depth the folder has grown into. It reads the **latest audit**, never the
folder, so it is worthless without a fresh `audit` — order the two, or let `curate` refuse on a stale
manifest rather than propose against one.

Its output is a file the owner opens and marks up (`_Audit/plans/<date>/move-plan.csv`), so it needs
no notification beyond "a plan is waiting". Do not wire it to notify per row.

**Execution is not a job.** An approved plan is executed by a separate, owner-triggered act under the
move guards — never on a timer, and never as a continuation of the `curate` run that proposed it.

## The one constraint worth checking

**Write context.** Both jobs need a context that can actually write `_Audit/` on the synced folder. On
some platforms an unattended background scheduler cannot write a synced cloud folder — the scheduler
then **hops into a logged-in session** that holds the capability, exactly as the `file-ingest`
archetype's reactive `ingest` does. Wire the timer to dispatch through whatever hop your platform
needs; don't assume the background context can write.
