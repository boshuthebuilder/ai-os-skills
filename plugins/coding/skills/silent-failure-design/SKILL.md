---
name: silent-failure-design
description: >-
  Design and audit controls so that a control which never ran is distinguishable from one that ran
  and passed. Covers the failure class where absence wears the appearance of success — CI that was
  never scheduled, a watchdog whose exception is swallowed, a guard that cannot start and therefore
  denies nothing, a test whose seam moved so it passes for the wrong reason, a skipped job counted as
  a pass, a review that ran against the wrong target. The method is one question asked of every
  control ("if this had never run, what would I see?"), plus the four properties that make the answer
  different from silence: a liveness signal, an artifact-based success test, per-item error isolation,
  and a status vocabulary that separates verified from unverified. Use when building or reviewing any
  guard, gate, watchdog, health check, backup, scheduled job or CI pipeline — and when diagnosing why
  something everyone believed was protecting them turns out not to have run for weeks. Pairs with
  implementation-discipline, which governs conduct while a change is written where this skill governs
  whether the resulting control can be seen to work — the two are reconciled explicitly where they
  touch, on per-item isolation and on scope — and with adversarial-review, the gate that is itself
  subject to this failure class.
---

# silent-failure-design

A control that fails *loudly* is a good day: something goes red, someone looks. The dangerous control
is the one that stops running. It raises nothing, logs nothing, and every surface stays exactly as
green as it was when it worked — because a control that never ran produces the same observable output
as a control that ran and found nothing wrong.

This is not an exotic failure. In a single week on one real system it happened six times, in six
different mechanisms, and **not one was caught by the control itself**:

| what stopped | what it looked like |
|---|---|
| CI never scheduled for a commit (conflicting PR ⇒ no merge ref) | `gh pr checks` said "no checks reported" — reads as *not yet* |
| a health watchdog crashed on its first row (`except: pass`, output to `DEVNULL`) | `watchdog: 0 red row(s) pushed` — identical to a healthy system |
| a fail-closed read guard could not start (unquoted path with a space) | every read denied, silently, for weeks |
| a test's monkeypatch seam moved when a default was refactored | the test passed — against the operator's **real** production data |
| a workflow skipped in its entirety | zero failures, zero incomplete ⇒ the merge gate said READY |
| an adversarial review ran against the wrong PR | a verdict was posted, on someone else's diff |

Every one was found by accident, by a human noticing something adjacent. That is the tell: if your
control's failure mode can only be discovered by luck, you do not have a control — you have a habit
that has been holding so far.

## The question

Ask it of every guard, gate, watchdog, health check, scheduled job, backup and test:

> **If this had never run, what would I see?**

If the answer is *"exactly what I see now"*, the control is undetectable when dead, and everything
downstream that depends on it is trusting a signal that carries no information. The fix is never "be
more careful" — it is to make the two states produce different output.

## Four properties that make absence visible

**1 · A liveness signal, separate from the finding.** A control must report *that it ran*, not only
*what it found*. "0 problems" and "did not execute" must be different strings. The cheapest form is a
timestamp the control writes on every completed pass, and a separate check that the stamp is fresh —
so "no pass completed in N intervals" becomes its own alarm. Without this, a control's silence is
indistinguishable from its success, and the longer it stays dead the more reassuring it looks.

When you are *building* a control, its liveness output is part of the requirement, not unrequested
scope: "it can be shown to have run" is a property the thing must have to be a control at all, so it
belongs in the change that creates it. That is different from retrofitting one to an existing control
you merely noticed was silent — see *When you find one, fix the class*.

**2 · Verify by artifact, never by exit code.** Ask what the control was supposed to *produce* and
check for that: the posted comment, the written row, the published file, the recorded timestamp. Exit
codes lie in both directions — headless CLIs exit 0 on auth failure, a swallowed exception returns
the same value as a clean run, and a wrapper's success says nothing about the thing it wrapped. If a
control produces nothing checkable, give it something to produce.

**3 · Per-item error isolation.** A control that iterates must not let one bad item abort the rest.
The watchdog above enumerated 25 health rows inside a single `try`; row 3 raised, and rows 4–25 were
neither checked nor cleared — the whole control silently became a no-op because one unrelated part of
the system was broken. Isolate per item, report the failed one, keep going. A blanket
`except Exception: pass` around a loop is this bug waiting to happen.

*Report* is load-bearing: **isolation is not swallowing.** Each item still fails loudly on its own;
only the *sweep* survives. This does not contradict `implementation-discipline`'s "an assertion that
fails loudly beats a defensive branch that handles-and-continues" — that rule governs a state which
genuinely **cannot** occur, where a branch hides an impossible condition. A control that checks
twenty-five things lives in the opposite case: some item failing is expected, and letting it abort the
other twenty-four is precisely how the control becomes a silent no-op. Assert on the impossible;
isolate *and report* the possible; swallow neither.

And isolate on the **expected** failure, not on everything. A per-item `except Exception` re-creates
the original bug one level down, quietly reclassifying a programming error — an `AttributeError` after
a refactor, a typo'd attribute — as "that item failed". The watchdog above died on exactly such an
error. Catch what an item can legitimately do to you (a timeout, an unreachable endpoint, a malformed
row) and let anything else escape as the bug it is.

**4 · A status vocabulary that separates *verified* from *unverified*.** Two states get wrongly
collapsed into "fine":
- **"I could not check"** is not "it is healthy". A degraded, evicted, unreachable or not-applicable
  reading must have its own name and must never satisfy a check that means *verified*.
- **"Nothing ran"** is not "nothing failed". A skipped job, an empty result set and a cancelled run
  each produce zero failures; none is evidence. Require positive proof — at least one thing actually
  succeeded — not merely the absence of a recorded failure.

The same discipline applies to *clearing*: only a confirmed-good observation may close an alert. A
control that clears on "not currently red" will silently close a live problem the moment it cannot
see it, which is exactly when you most need the alert to stand.

**A default cannot fail, so a default is never a decision.** The failure class above is a control that
did not run; this is its quieter twin — a control that ran, on a value nobody chose. Where a routing
or safety parameter has a sensible default, an omitted argument and a deliberate one are byte-identical
at the call site, so the wrong answer produces no error, no log line and no diff to review. Ask the
question of the *parameter*: **if the caller had never thought about this, what would I see?** If the
answer is "the same thing I see now", the default is a silent failure waiting for its first caller who
should have chosen differently.

A live instance: a notification lane defaulted to `household`, one sender omitted it, and an
infrastructure alert addressed to the operator sat in a family's queue for eleven days. Nothing was
broken, nothing was logged, and the earlier work that built the operator lane had simply missed one
call site — invisibly, because a default cannot fail.

The remedy is to make omission *loud at the boundary you already own*: not a runtime exception (too
late, and it fails production for a wiring mistake), but a structural test that enumerates the call
sites and fails on any that did not state the value. An AST walk over every construction of the type,
asserting the parameter is present, converts "someone forgot" from an invisible default into a red
build — and it costs nothing at run time. Prefer this to removing the default outright when the
default is genuinely right for most callers; the goal is a *stated* choice, not a burdensome one.

## Auditing an existing system

A standing audit of a running system — not a checklist for a single PR. Steps 3 and 5 in particular
ask what a system has done *over time* and what its queries cannot see, which needs the deployment in
front of you, not a diff. Cheap and high-yield, roughly in order:

1. **Grep for the swallows**: `except.*:\s*pass`, `|| true`, `2>/dev/null`, `DEVNULL`, `catch {}`. For
   each, ask what state the system is in if that path is taken every time from now on. Some are
   correct (a best-effort cleanup); the ones guarding a *control* are not.
2. **Find the controls with no output.** Anything spawned detached, or whose stdout goes nowhere,
   cannot be shown to have run. Give it a log line or a stamp.
3. **Check the last-run time of every scheduled thing**, not its last result. A backup, sweep or probe
   whose newest artifact is older than its interval has stopped, whatever its status row says.
4. **Test the tests.** A test that would pass if the code under it were deleted is not a test. After
   any refactor that moves a default behind an indirection, re-check what the tests were patching —
   a seam that moved turns a passing test into decoration, and worse, can point it at production.
5. **Ask what a control cannot see.** Scope gaps are silent by construction: an item outside every
   query's filter is missing from every count, so the queue looks clean precisely because the item is
   unreachable.

## When you find one, fix the class

The instinct is to fix the instance — add the missing grant, correct the path, restore the trigger.
Do that, and then ask why nothing noticed for however long it was broken. The instance is a bug; the
absent liveness signal is the defect.

**This is not licence to widen the diff.** `implementation-discipline` binds here — *unrequested
improvements become issues, not diff hunks* — so if the instance is what you were asked to
fix, fix it and file the class; if you merely *noticed* it while doing something else, **file both** —
the instance is no more in scope than the class, and a drive-by fix in an unrelated diff is the same
violation wearing a helpful face. Either way the filed issue names the control, what its silence
looked like, and what would have made it visible. The point is that the class-level defect gets *recorded* rather than
forgotten the moment the instance stops hurting. Whether it is fixed now or next sprint is a scheduling
decision; taking it silently inside an unrelated PR is not yours to make. A system that has had this failure once will have it again in a
different mechanism, and only the general property — *dead looks different from healthy* — prevents
the next one.

Prefer removal to accumulation. Several of these failures were introduced by a guard added to satisfy
an earlier concern; the durable fix was deleting the special case and leaving one path that always
runs. A control you can reason about in one place is a control whose silence you will notice.
