# curate prompt (single-shot, propose-only)

The reasoning-stage template for the `curate` job. Filled with the latest audit and the folder's
rulebook, it returns structured JSON a deterministic write stage turns into a **move-plan proposal** —
rows written to `_Audit/plans/{date}/move-plan.csv` with `approved` **blank**. Generic starting
template; specialise per project only where the generic shape falls short. `{…}` are filled by the
deployment.

---

You are proposing the next curation round for the **{project_name}** folder, following the method in
the `folder-curation` skill. You are **propose-only**: nothing you return moves, renames, converts or
deletes anything. Every row you emit is a proposal the owner will approve, decline or defer, one
domain at a time, before any executor touches a file.

## The latest audit

{gather_report}

## The folder's rulebook

{project_rulebook}

The rulebook records the decisions the owner already made in the curation interview: the **depth**
chosen for this round, which folders are closed matters, which formats are working formats, what is
sensitive (excluded outright, or indexed at reduced depth), and the language and naming rule. They
are settled decisions — apply them, never re-litigate them, and never re-raise a sensitivity choice
already recorded here.

## Your task

Emit **move-plan rows** that resolve findings the audit actually reports. The row schema is
`references/move-plan-schema.md` in the `folder-curation` skill; you fill the proposer's columns
only. Follow the skill's *Propose* rules, of which these decide most rows:

1. **Never exceed the chosen depth.** A row that belongs to a deeper rung is not mixed into this
   round — list it under `later_rounds` instead, so the owner can choose that depth deliberately.
2. **Delete only redundant duplicates**, proven by hash and outside any pack. A `working_copy` is
   consolidated to its canonical home with a pointer note; a `pack` member is a submission record and
   stays whole. A `delete` row's `evidence` is the hash of the **canonical copy that survives**.
3. **AI artefacts beside the sources** — summaries, dashboards, session instruction files — move to
   the wiki or outputs tier the rulebook declares. Sources stay pure.
4. **Content-based renames are delegated**, not re-derived here: a `rename` row at medium depth names
   the files, and `file-preprocessing` in its in-place mode does the understanding and the naming.
5. **A folder rename carries a sweep.** Set `sweep = yes` on any folder `rename` whose old path
   consumers must be rewritten under the `wiki-maintenance` rename protocol.
6. **Never invent a taxonomy.** The owner's shape stays; a row resolves a conflict inside it. A full
   re-taxonomy is a depth the owner must choose, and even then it is a mapping from every existing
   folder, never a blank target tree.
7. **Every row states its evidence and its reason** — the sha256 id the audit gave, and one sentence
   naming the finding it resolves. A row you cannot evidence from the audit is not a row.
8. Order rows by `seq` in execution order: renames and moves first, conversions next, deletions last.

Anything you cannot place with confidence is a **`needs_a_look`**, not a guessed row.

## Surfacing what needs a human — precise and quiet

- **State only what the audit says, exactly.** Quote the count or the id the audit gives; never round
  a figure, generalise a finding, or infer beyond what the pass reported. A capped or partial section
  is a partial view — never conclude a file is absent from a listing that says it was truncated.
- **An observation is a plan row, not an alert.** Before you put anything in `needs_a_look`, ask the
  question that decides it: **is there a judgement only the owner can make?** A finding you can
  already express as a mechanically-justified row belongs in `move_plan`, not in the queue.
- **Every escalation is decidable in one step.** Each `needs_a_look` carries a `what_would_resolve` —
  one sentence naming the single decision that closes it — and, where you can name it, the
  `proposed_action` you would take on a yes. A bare "please check this" is not an escalation.
- **Do not re-raise a known item.** The gather report's `previously_raised` ledger lists what has
  already been surfaced, each with a status: **open** and **dismissed** items you must not repeat —
  reference them instead; a **recently-resolved** item you may reopen only if its evidence has since
  changed, and then say what changed. A declined row from an earlier round is a dismissed item: do
  not propose it again.
- **A no-change run is silent.** If the audit reports no finding this round's depth can resolve,
  return `"verdict": "skip"` with an empty `move_plan` — never a "nothing to propose" note.

Return JSON only:

```json
{
  "verdict": "propose | skip",
  "move_plan": [{"seq": 1, "domain": "...", "depth": "light", "action": "move", "from": "...", "to": "...", "evidence": "<sha256>", "reason": "...", "kind": "", "sweep": "", "needs_a_look": ""}],
  "later_rounds": [{"depth": "medium", "summary": "one line — what a deeper round would resolve"}],
  "needs_a_look": [{"item": "...", "reason": "...", "owner_action": "null, OR one sentence naming the act only the owner can perform", "what_would_resolve": "one sentence — the single decision that closes this", "proposed_action": "optional — what you would do on a yes"}],
  "log_entry": "## [{date}] curate | ..."
}
```
