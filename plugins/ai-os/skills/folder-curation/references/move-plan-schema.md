# move-plan.csv — the curation plan, approvals and execution record

One file per curation round at `_Audit/plans/<YYYY-MM-DD>/move-plan.csv`, UTF-8, header row,
RFC 4180 quoting (paths contain commas and quotes). The proposer fills the first eleven columns; the
owner fills the approval pair; the executor fills the last three. Rows are never deleted or
reordered; a withdrawn proposal is a row with `approved = declined`.

| column | filled by | values |
|---|---|---|
| `seq` | proposer | 1-based integer, execution order |
| `domain` | proposer | the owner's top-level folder or subject the row belongs to, for per-domain approval |
| `depth` | proposer | `light`, `medium`, `full`; never above the depth the owner chose for this round |
| `action` | proposer | `move`, `rename`, `delete`, `convert`, `create` |
| `from` | proposer | folder-relative path today (empty for `create`) |
| `to` | proposer | folder-relative path after (empty for `delete`) |
| `evidence` | proposer | the sha256 id of the file, or of the folder's manifest listing for a folder rename; the hash of the canonical copy for a `delete` |
| `reason` | proposer | one sentence, the audit finding it resolves (e.g. `redundant copy of <id> in the same folder`) |
| `kind` | proposer | for `delete`: `redundant` only (a `working_copy` or `pack` row is never a delete); for `convert`: the target format |
| `sweep` | proposer | for a folder `rename`: `yes` when the wiki-maintenance rename protocol must run; the consumers found are listed in the execution `note` |
| `needs_a_look` | proposer | empty, or the reason this row is a proposal the owner must judge rather than a mechanical one |
| `approved` | owner | `approved`, `declined`, `deferred`; a blank row is treated as `deferred` |
| `approved_at` | owner | ISO datetime |
| `status` | executor | `pending`, `done`, `skipped`, `failed`, `reverted` |
| `executed_at` | executor | ISO datetime |
| `note` | executor | the failure reason, the undo entry's id, or the rename sweep's consumer list |

Rules the schema encodes: a `delete` row's `evidence` must equal an existing entry's id whose
`dup_kind` is `redundant`; a `convert` row is `done` only after verification and archiving of the
original; a folder `rename` with `sweep = yes` is `done` only after every in-folder consumer of the
old path is rewritten and out-of-folder consumers are logged as watch items. The executor reads only
this file, never the audit.
