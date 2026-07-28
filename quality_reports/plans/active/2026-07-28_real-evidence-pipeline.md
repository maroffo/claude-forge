# ABOUTME: Living plan — evidence-backed SCOREs (wasit pilot), executable DoD, bug-hunter agent, nightly trigger
# ABOUTME: 4 fasi + sketch frontend; 4 harness change contracts; checkpoints dopo fase 2 e 3

# Real Evidence Pipeline: score evidence-backed + bug-hunter autonomo

## Context

Oggi SCORE è un verdetto di giudice: score-evidence-guard verifica solo che un comando di verify sia girato dopo l'ultimo edit (dal transcript), il DoD di plan-forge è prosa, gli evidence bundle di wasit sono testo trascritto a mano. Obiettivo: (a) DoD eseguibile e SCORE che referenzia un bundle di artefatti machine-readable, (b) agente bug-hunter che trova bug, scrive repro fallente, apre issue con label (niente auto-fix, niente merge), (c) trigger notturno. Pilota: hikma-wasit (Go). Playwright/frontend: fase futura solo abbozzata.

Al primo step di esecuzione: copiare questo piano in `claude-forge/quality_reports/plans/active/2026-07-28_real-evidence-pipeline.md` (living plan, source of truth).

## Decisions

| # | Decision | Choice | Rationale |
|---|----------|--------|-----------|
| 1 | Runner artefatti | `go run gotest.tools/gotestsum@<pin>` → junit XML + JSON + coverprofile | idioma wasit (golangci-lint via go run), niente converter custom |
| 2 | Target | nuovo `make evidence` → `scripts/evidence.sh`; target esistenti intoccati | zero blast radius su CI e abitudini |
| 3 | Bundle layout | `quality_reports/evidence/<slug>/`: curati committati (junit, coverage.txt, lint.txt, metadata.json, README map) + `raw/` gitignored (events JSON, coverage.out) | riusa la negation gitignore esistente di wasit; niente bloat |
| 4 | Anchor file | `metadata.json`: schema_version, SHA, dirty, branch, per-step {command, exit, duration} | unico manifest su cui hook e dod-runner fanno chiave |
| 5 | CI wasit | invariata in fase 1 | evidence è concern locale/agente; upload-artifact decisione separata |
| 6 | DoD | tabella nel piano: `# / Criterion / Command / Expected / Auto` (no dod.yaml separato) | file separato driftta; precedente colonna Depth (contract 2026-07-27_plan-depth) |
| 7 | dod-runner | `forge/scripts/dod_run.py --plan <file> --evidence-dir <dir> [--repo <path>]` → `dod-results.json` + exit code; test in `scripts/tests/` | comandi vengono dal piano ⇒ repo-agnostic; lo script fa il lavoro, il modello fornisce solo i valori |
| 8 | Literal SCORE | `SCORE: <n>/100 (threshold: <t>, gate: <g>, evidence: <path>)`; campo opzionale in stage A, obbligatorio per gate pr in stage B | regex backward-compatible; rollout de-riskato sui 5 file da sincronizzare |
| 9 | Check del hook sul path | sotto project dir, isdir, contiene metadata.json, mtime ≥ ultimo source edit; stat-only; fail-open su eccezioni; path presente-ma-invalido = block | evidenza falsa peggio di nessuna evidenza; Stop hook deve restare economico |
| 10 | Bug-hunter | test esplorativi `//go:build e2e` (`test/e2e/hunt_<slug>_test.go`) contro il TestMain embedded esistente; repro = test fallente che post-fix resta regression test | riusa testcontainers deterministici; il repro soddisfa il contratto REPRODUCE per costruzione; meglio del black-box HTTP su make dev |
| 11 | Issue filing | `gh issue create` label `agent:hunted`; body pre-risponde al rubric triage, embedda repro come patch + comando + `Fingerprint: <pkg>/<func>` + citazione spec | triage fast-path meccanico; fingerprint per dedup |
| 12 | Sede skill hunter | `claude-hikma-skills/bug-hunter-hikma` | hikma-specific come issue-loop/issue-triage |
| 13 | Autonomia iniziale | hunter apre issue e basta; fix passa da issue-loop lanciato da Max | gate umano tra trova e fissa finché i repro non si dimostrano affidabili |
| 14 | Trigger | run headless schedulato notturno di /bug-hunter-hikma, con backpressure + timeout + digest push | guardrail nella skill, trigger stupido |

## Fase 1 — Evidence bundle machine-readable (wasit) 🟢 nessun contract

Files: `hikma-wasit/scripts/evidence.sh` (new), `Makefile` (target `evidence` + pin gotestsum), `.gitignore` (`quality_reports/evidence/**/raw/`), `CLAUDE.md` (commands block stale, documentare `make evidence`).

`evidence.sh`: esegue senza short-circuit fmt→vet→lint→vulncheck→unit (gotestsum: `unit.junit.xml`, `raw/unit.events.json`, `raw/coverage.out`, `coverage.txt` da cover -func)→e2e (`e2e.junit.xml`, `raw/e2e.events.json`); scrive `metadata.json` per ultimo; exit ≠0 se uno step fallisce (bundle rosso = comunque evidenza); genera README artefact map (convenzione esistente, ora scriptata).

**Exit:** `make evidence` su checkout pulito → bundle completo exit 0; con un test rotto ad arte → bundle che registra il fail, exit ≠0; `git status` mostra solo curati, `raw/` ignorato.

## Fase 2 — DoD eseguibile + estensione score-evidence-guard (forge) 🔴 3 contract

2a: `plan-forge/references/plan-template.md` DoD → tabella (D6; righe manuali `Auto: no`); `forge/scripts/dod_run.py` + test; issue-loop-hikma DoD gate invoca dod_run puntando al bundle.

2b (5 file sincronizzati + test): `hooks/score-evidence-guard.py` (SCORE_RE + check D9/fail-open), `rules/orchestrator-protocol.md` (literal), `harness-trace/extractor.py` + `models.py` (ScoreData.evidence_path opzionale), `scripts/score-log.sh` (`--evidence` additivo, righe vecchie valide). Test: nuovi casi in `hooks/tests/test_score_evidence_guard.py` (path valido passa, mancante blocca, stale blocca, campo assente = legacy, metadata illeggibile = fail-open); `test_hook_constants_sync.py` pinna il pattern condiviso su hook/rule/extractor/score-log.

Contracts: C1 `2026-07-28_dod-executable-table.md` (DoD passa come prosa senza check eseguibile); C2 `2026-07-28_score-evidence-path.md` (SCORE senza link machine-checkable all'evidenza); C3 `2026-07-28_score-guard-fs-validation.md` (SCORE cita path mancante/estraneo/stale).

**Exit:** hooks/tests e scripts/tests verdi; una sessione pilota su wasit emette `SCORE: n/100 (threshold: 90, gate: pr, evidence: ...)` accettato dal hook; le falsificazioni di C3 (path fabbricato, bundle stale) bloccano dimostrabilmente.

<!-- checkpoint:verify — Max verifica la sessione pilota e i block di C3 prima di procedere -->

## Fase 3 — Bug-hunter 🔴 1 contract

Files: `claude-hikma-skills/bug-hunter-hikma/SKILL.md` (new), `issue-triage-hikma/SKILL.md` (fast-path `agent:hunted`: segnale forte su Specified/Verifiable, rubric comunque eseguito), label `agent:hunted` su hikma-wasit.

Loop skill: scegli area (churn recente, package a bassa coverage da `coverage.txt`) → scrivi hunt test in worktree isolato → `go test -race -tags e2e -run TestHunt<Name>` (hunt sequenziali, mai paralleli: TestMain seriale) → conferma: fallisce 2 volte consecutive E asserisce comportamento documentato (citazione OpenAPI/doc comment obbligatoria) → issue per D11 → cleanup worktree.

Guardrail hard: max 3 issue/run, max 5 hunt test/run, 45 min wall-clock, no-repro-no-issue, dedup fingerprint vs open + closed 30gg, mai PR/push/merge, codice repo = dati non istruzioni.

Contract: C4 `2026-07-28_hunted-issue-fastpath.md` (issue del hunter rientrano nel loop senza validazione repro).

**Exit:** un run supervisionato end-to-end → ≥1 bug confermato (issue con repro rosso su HEAD) oppure clean report esplicito; rerun immediato → zero duplicati; contatori guardrail visibili nel log.

<!-- checkpoint:verify — Max rivede le issue del primo run supervisionato -->

## Fase 4 — Trigger notturno

Run schedulato ~02:00 di /bug-hunter-hikma su wasit. Pre-flight skip se: working tree sporco, >5 issue `agent:hunted` aperte, worktree del run precedente non pulito. Hard timeout, digest via PushNotification (filed/clean/skipped-perché). Meccanismo: crontab `claude -p` (già pending da loop-primitives) o schedule routine, deciso in fase.

**Exit:** due notti consecutive non presidiate corrette (no dup, no worktree orfani, digest arrivato).

## Fase 5 — Frontend (solo sketch, non progettata)

`E2E_BASE_URL` external mode del harness wasit + Playwright su hikmaai-frontend; bundle guadagna `playwright.junit.xml` + trace zip in `raw/`; hunter guadagna probe UI via pattern verify-frontend.

## Budget

| Limit | Value |
|-------|-------|
| Fix rounds | 5 (default), poi escalate |
| Writer concorrenti | 2 (fasi quasi tutte seriali; scope disgiunti wasit/forge/hikma-skills) |
| Sub-agent totali run | 12 |
| Evidenza minima per finalizzare | fase-specifica (exit criteria sopra); sempre test/lint verdi dopo ultimo edit |

## Rischi

| Rischio | Mitigazione |
|---|---|
| Harness e2e seriale ⇒ artefatti per-run, hunt paralleli collidono | granularità per-test dentro junit; regola hunt-sequenziali |
| Bloat repo wasit da bundle | curati+raw/ ignorato (D3); un bundle per pr-slug, sovrascritto |
| Test flaky ⇒ issue false | doppio fail consecutivo + citazione spec + rubric triage |
| I/O filesystem nello Stop hook | stat-only, fail-open, cap dimensione metadata |
| Drift del literal sui 5 file | test_hook_constants_sync esteso |
| Prompt injection dal codice repo verso hunter | code-is-data nella skill; issue solo via template gh fisso |
| Cron brucia token su stato rotto | backpressure skip + timeout + digest |

## Progress
- [x] 2026-07-28 12:12 — piano salvato in forge plans/active, mirror vault, log sessione
- [x] 2026-07-28 12:20 — Fase 1: worktree wasit `.claude/worktrees/evidence-bundle` (branch feat/evidence-bundle da origin/dev @ e3a322c; dev locale 133 behind, non toccato)
- [x] 2026-07-28 12:25 — Fase 1: scritti scripts/evidence.sh (shellcheck clean), Makefile (target evidence + pin gotestsum v1.13.0 ⇒ risolta UQ1), .gitignore (raw/ ignorato), CLAUDE.md (commands block corretto: check era stale)
- [x] 2026-07-28 12:50 — Fase 1 VERIFY run 1: bundle prodotto correttamente; unit 3719 test verdi (75s, cov 36.2%), e2e 476 verdi/15 skip (62s: stima 12min era su runner CI), fmt/vet/lint verdi. **vulncheck FAIL pre-esistente su origin/dev**: GO-2026-6061, grpc v1.80.0 raggiungibile via internal/dist/signer.go, fix in v1.82.1. Il bundle ha fatto il suo lavoro: gate rosso emerso come evidenza.
- [x] 2026-07-28 13:00 — Fase 1: bump grpc v1.80.0→v1.82.1, run 2 tutto verde (overall_exit 0)
- [x] 2026-07-28 13:10 — Fase 1: red-path check ok (canary fallente → unit exit 1, overall_exit 1, make exit ≠0, junit con 1 <failure>, step successivi eseguiti comunque); fix bug latente gitignore (dir-exclusion rendeva morta la negation evidence per file nuovi)
- [x] 2026-07-28 13:25 — Fase 1 REVIEW round 1 (security+architecture): 2 Major (PATH leak in metadata.json; fmt_check fail-open su gofmt exit 2) + 6 Minor, 7 fixati + 1 accepted-mitigated; findings in wasit quality_reports/reviews/2026-07-28_real-evidence-pipeline/001-findings.md (local), approval committato
- [x] 2026-07-28 13:35 — Fase 1 chiusa: bundle finale verde rigenerato post-fix (no PATH leak, vulncheck registrato come `vulncheck_gate`), SCORE 97/100 (threshold 90, gate pr), commit d54c16b su feat/evidence-bundle. **Fase 1 exit criteria: tutti soddisfatti.**
- [x] 2026-07-28 13:50 — Fase 2 avviata su forge, branch `feat/real-evidence-pipeline` (da main @ 9f4b6a8). Contract C1 scritto (quality_reports/harness_changes/2026-07-28_dod-executable-table.md)
- [ ] Fase 2a: plan-template.md DoD → tabella `# | Criterion | Command | Expected | Auto`; scripts/dod_run.py (--plan --evidence-dir [--repo], parse tabella DoD, esegue righe Auto=yes con bash -c + timeout 1800s/riga, scrive dod-results.json nel bundle, exit 0 sse tutte le auto passano, exit 2 su parse/usage error) + scripts/tests/test_dod_run.py (stile test_score_log.py: unittest, uv run --no-project)
- [ ] Fase 2b: contracts C2 (score-evidence-path) e C3 (score-guard-fs-validation); poi 5 file sync:
  1. hooks/score-evidence-guard.py: SCORE_RE con gruppo opzionale `evidence:`; check filesystem (payload cwd → path dentro project dir, isdir, metadata.json presente; mtime metadata >= timestamp ISO dell'ultimo edit event del transcript; missing/escape/stale = BLOCK con reason dedicata; JSON/stat error inatteso = fail-open); aggiungere `evidence` all'alternation `make (check|test|...)` di VERIFY_RE (anche in verify-before-stop.py, tenuti in sync)
  2. rules/orchestrator-protocol.md:46 literal → `SCORE: <n>/100 (threshold: <t>, gate: commit|pr|excellence[, evidence: <bundle-path>])`
  3. skills/harness-trace/src/harness_trace/extractor.py (~421): estrarre evidence path nello step SCORE
  4. skills/harness-trace/src/harness_trace/models.py ScoreData: + `evidence_path: str = ""`
  5. scripts/score-log.sh: flag opzionale `--evidence <path>` → campo additivo nel row JSONL (righe vecchie valide)
- [ ] Fase 2b test: nuovi casi in hooks/tests/test_score_evidence_guard.py (valido passa, mancante blocca, stale blocca, assente=legacy, metadata illeggibile=fail-open); test_hook_constants_sync.py pinna il literal su hook/rule/extractor/score-log; estendere test_score_log.py per --evidence
- [ ] Fase 2: run suite forge (`make check` + loop test), poi commit su feat/real-evidence-pipeline citando C1-C3 nel body
- [ ] Fase 2 exit: sessione pilota wasit con nuovo literal accettato dal hook + falsificazioni C3 che bloccano → CHECKPOINT Max
- [ ] Fase 2a bis: issue-loop-hikma DoD gate invoca dod_run.py (repo separato claude-hikma-skills, commit separato)
Next action: editare skills/plan-forge/references/plan-template.md sezione ## DoD (righe 77-85) in tabella; poi scrivere scripts/dod_run.py

## Surprises & Discoveries
- Il primo run del bundle ha scovato una vuln reale pre-esistente (GO-2026-6061, non allowlisted) che il `make check` abituale avrebbe mostrato solo a chi guardava l'output: evidenza del valore del bundle (vuln.txt persistito).
- `make evidence 2>&1 | tail` maschera l'exit code (pipe): nei consumer del bundle leggere `overall_exit` da metadata.json, mai l'exit della pipeline shell.
- e2e wasit in locale: 62s, non i ~12min del runner CI self-hosted.

## Surprises & Discoveries
(compilato in esecuzione)

## Outcomes & Retrospective
(a chiusura)

## Unresolved questions

1. Pin esatto gotestsum: verificare ultima stabile al momento dell'implementazione (assunto ~v1.13).
2. Naming bundle: `<pr-slug>` quando c'è una PR, `YYYY-MM-DD_<branch-slug>` altrimenti — confermare in fase 1.
3. Upload artifact in CI wasit: deferita, decidere dopo fase 2.
4. Fase 4: crontab vs schedule routine — legata alla crontab install ancora pending.
