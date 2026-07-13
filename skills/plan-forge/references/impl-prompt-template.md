# ABOUTME: Implementation-prompt and /goal templates emitted by plan-forge (step 4).
# ABOUTME: Placeholders in <angle brackets>; drop (bugfix)/(hot-path) clauses when not applicable.

# Implementation prompt template

Present this to the user as a paste-ready block for a FRESH session. Fill every placeholder
from the plan; delete clauses that do not apply. Keep the wording of the git guards verbatim:
each line exists because its absence caused a real incident.

```
Implementa <issue ref / task title> seguendo ALLA LETTERA il piano
<absolute path to the plan file written in step 3>
- e' la source of truth: contiene l'analisi verificata, le <N> decisioni bloccate
(<one-line summary of the key locked decisions>), la tasklist W0-W<n>, la matrice E2E
esaustiva e il DoD.

Regole di esecuzione:
- Lavora in un worktree separato di <repo> (EnterWorktree) su branch <branch> da
  origin/<integration-branch> aggiornato. COPIA il piano dal path sopra nel worktree
  (quality_reports/plans/active/) e committalo col PRIMO commit.
- ORDINE OBBLIGATORIO: (hot-path) prima `make bench-baseline` sul tree pulito pre-edit
  (macchina scarica: verifica load e nessun processo *.test concorrente); (bugfix) poi
  W0 REPRODUCE: il test del bug DEVE fallire sul codice non fixato, registra l'output
  rosso nel piano PRIMA di scrivere una riga di fix; poi W1->W<n> in ordine.
- <the one or two load-bearing implementation constraints from the locked decisions,
  stated imperatively, e.g. "il verify DEVE usare la catena completa X->Y->Z con lo
  snapshot armato, MAI un fresh config load">.
- Subagent: software-engineer, model opus-4.8. Il subagent condivide il worktree: nel suo
  brief vieta git checkout/switch/pull e git commit --amend; prima di OGNI commit verifica
  `git branch --show-current` nella stessa call; stage per path espliciti, mai `git add -A`;
  mai --no-verify.
- Dopo OGNI task aggiorna il piano (Progress + Surprises con evidenza, Decisions
  append-only): e' parte della DoD.
- VERIFY freschi dopo l'ultimo edit, tutti pristine: <repo verify commands>.
  (hot-path) Poi `make bench-compare` contro la baseline pre-edit: exit!=0 = Major
  finding, fixa o accept-with-rationale nel piano, mai silente.
- Review: <reviewer set from the plan's DoD> sul diff vs origin/<integration-branch>.
  Fixa CRITICAL/MAJOR, re-verifica, ri-scora col formato canonico.
- Chiusura: fila le follow-up issue draftate nel piano, apri la PR verso
  <integration-branch> (NON mergiarla) linkando <issue ref> e le follow-up, riporta
  SCORE: <n>/100 (threshold: 90, gate: pr) con evidenza computazionale fresca.
```

# /goal template

The user types this in the fresh session right after pasting the prompt (only the user can
set /goal; never claim to set it for them). The condition must be transcript-evaluable and
key on the canonical SCORE line.

```
/goal the transcript reports a line matching SCORE: <n>/100 (threshold: 90, gate: pr) with n >= 90 for <slug> on branch <branch>, after <(bugfix) the REPRODUCE test is shown failing on unfixed code and passing on the final code, and> <verify commands, comma-separated> <(hot-path) and make bench-compare> all pass on the final code, or stop after 5 fix rounds
```

## Why these clauses exist (incident-backed, keep them)

| Clause | Incident it prevents |
|--------|----------------------|
| plan copied + committed FIRST | fresh worktree sessions executing without the source of truth in-repo |
| bench-baseline pre-edit, quiet machine | baseline polluted by a stray *.test at 100% CPU produced uniform +/-500% garbage (2026-07-12) |
| REPRODUCE red recorded before fix | tests written after the fix that never bound to the bug (tautology theatre) |
| no checkout/switch/pull in subagent brief | engineer's checkout retargeted the orchestrator's next commit (Wave 3B.1) |
| no --amend in subagent brief | engineer's amend rewrote the orchestrator's already-pushed commit (gemini-bench, 2026-07-12) |
| branch-guard in the SAME call as commit | guard in an earlier turn missed a mid-task branch switch |
| SCORE canonical format | free-form scoring produced 0 extractable SCORE events across 6 traced sessions |
| PR opened, never merged by the agent | merge stays a human (or explicitly delegated automerge) decision |
| stop after 5 fix rounds | mirrors the orchestrator's global escalation ceiling |
```
