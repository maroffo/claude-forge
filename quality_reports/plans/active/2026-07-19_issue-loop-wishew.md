# ABOUTME: ExecPlan for issue-loop-wishew: autonomous issue-to-PR loop on the Wishew monorepo
# ABOUTME: Port of issue-loop-hikma (PR #87) onto the Projects v2 board substrate, full-auto variant

# Plan: issue-loop-wishew (autonomous issue → plan-forge → worktree impl → PR)

Analysis verified in session 2026-07-19, do not re-derive:

- The hikma implementation shipped today (claude-forge PR #87, claude-hikma-skills repo) is the
  reference architecture: hard rails, claim collision guard (incident #569), graduated escalation,
  PR template with Manual-QA derivation rules. Port, don't reinvent.
- Wishew substrate differs: GitHub Projects v2 board (`wishew_common.py`: Status/Priority/Size
  fields, GraphQL node IDs, sorted Ready queue, In progress single-flight lock) instead of the
  hikma `agent:*` label protocol.
- `origin/dev` no longer exists on Wishew/wishew-monorepo (verified via `git ls-remote`); all PRs
  target `main`. `work-next-wishew/work.py:14,151,156` and `SKILL.md:37,44,53` are stale on `dev`.
- plan-forge emits ExecPlan + impl prompt + DoD (`SCORE ≥ 90, gate: pr`); its `/goal` handoff is
  human-only, so the loop replaces it with a mechanical DoD gate (fresh-context verification +
  score-evidence-guard).

## Decisions

| # | Decision | Choice | Rationale | Revisit if |
|---|----------|--------|-----------|------------|
| 1 | Human gate | Solo sul PR (full-auto, anche complex) | Max, this session; supersedes the hikma graduated gate for wishew | ≥2 of first 10 PRs closed unmerged as wrong (contract falsification) |
| 2 | Runtime | /loop interattivo locale | Docker (second-opinion, gemini-review) + hooks disponibili; headless li degrada | mai headless senza rivedere il contract |
| 3 | Concurrency | Sequenziale, una issue in flight | Superfici condivise del monorepo (migrations, package.json, barrel, Prisma) | coda cronicamente lunga E scope disgiunti provati |
| 4 | State machine | Ibrido board+label | Board = stati umani (Ready/In progress/In review, lock, sort P0→P2/XS→XL); label solo per i sottostati mancanti | drift fra board e label osservato |
| 5 | Complex audit | Piano postato come commento issue, non blocca | Finestra d'interruzione senza gate; loop gira sotto gli occhi di Max | Max chiede il gate graduato |
| 6 | Second-opinion down (tutti) | Escalate, mai procedere alla cieca | Sostituto meccanico del gate umano rimosso | — |
| 7 | Eligibility rubric | Claim-time dentro il loop, non 4ª skill | La coda Ready è già curata da triage-backlog; serve solo il filtro di sicurezza | rubric cresce oltre le 4 domande |
| 8 | Branch protocol | `agent/issue-<N>-<slug>`, unico push shape | Rail hikma: il loop non può toccare altri branch per costruzione | — |
| 9 | Worktree path | `/tmp/wishew-loop-<N>` | Non collide con `/tmp/wishew-work-<N>` di work-next | — |
| 10 | work.py dev→main fix | Stessa MR, commit separato, no contract | Ripristino di comportamento contro un remote branch morto, non mutazione harness | — |
| 11 | Worktree path (supersede #9) | `~/.cache/wishew-loop-<N>` | Security review: parent world-writable di /tmp = superficie di code-injection da utente co-residente | — |
| 12 | Rail CI/deploy surfaces | Il loop non tocca mai `.github/`, `cloudbuild*`, entrypoint, hooks, settings; issue che li richiedono → `agent:human` | Security review Major: workflow `pull_request` same-repo girano coi secrets al PR-open, prima della QA umana | il repo aggiunge un path-guard meccanico lato CI |
| 13 | Titoli issue mai in shell | Gli script fetchano il titolo server-side (`fetch_issue_title`); niente `--title` | Security review Major: titolo ostile attraversa il boundary metadata→shell del parent agent | — |
| 14 | Claim comment-first + steps_done | Commento prima del move; ogni mutazione tracciata nell'emit d'errore | Architecture review Major: claim half-failed incastrava il lock senza marker visibile | — |
| 15 | Meccanica condivisa in wishew_common | slugify/sort/lock/worktree/fetch_title estratti | Architecture review Major: terza copia in drift (lezione origin/dev) | — |

## Labels (bootstrap idempotente via loop.py)

| Label | Meaning | Set by |
|-------|---------|--------|
| `agent:human` | Veto permanente (rubric fallisce Safe/Scoped/Verifiable) | loop o Max; solo un umano la rimuove |
| `agent:needs-spec` | Sotto-specificata; domande nel commento | loop |
| `agent:blocked` | Escalation; item torna in Backlog | loop |
| `agent:qa` | Sul PR: checklist Manual QA in attesa | loop |

Board: claim = In progress, PR aperto = In review, escalation = Backlog + `agent:blocked`.

## Tasklist

| # | Task | Repo | Outcome osservabile |
|---|------|------|---------------------|
| W1 | `issue-loop-wishew/loop.py` (pick/claim/start-worktree/release/needs-spec/human/escalate/finish/bootstrap) | claude-skills-wishew | `ruff check` verde; `pick` su coda reale ritorna JSON coerente |
| W2 | `issue-loop-wishew/SKILL.md` (port hikma: rails, rubric, iterazione, common issues) | claude-skills-wishew | self-containment: eseguibile da sessione fresca |
| W3 | `issue-loop-wishew/references/pr-template.md` (Manual QA derivation) | claude-skills-wishew | regole 3-10 checkbox presenti |
| W4 | Fix staleness `work-next-wishew` dev→main | claude-skills-wishew | zero occorrenze `origin/dev`/`--base dev` |
| W5 | Registrazione `_INDEX.md` + `CLAUDE.md.example` + change contract + symlink | claude-forge | contract 6 campi; symlink risolve |
| W6 | Pilot: 1 issue banale, watched; poi /loop cap 2 | wishew-monorepo | PR aperto con checklist QA, item In review |

## DoD

- `make check` verde in claude-skills-wishew (ruff) dopo l'ultimo edit.
- Contract 6 campi committato con la modifica, riferito nel commit body.
- Nessun push automatico: Max pusha e apre le PR (regola git globale).
- Pilot W6 eseguito SOLO dopo approvazione delle due MR da parte di Max.

## Progress

- [x] 2026-07-19: analisi + decisioni lockate (questa sessione)
- [x] 2026-07-19: branch `feat/issue-loop-wishew` in entrambi i repo
- [x] 2026-07-19: W1-W4 + review fleet (0 Critical, 6 Major, 10 Minor, tutti fixati) + re-verify
  verde; claude-skills-wishew commit 1947629 (skill) + 9173bdf (work-next fix/refactor)
- [x] 2026-07-19: W5 su claude-forge (contract + _INDEX + CLAUDE.md.example + piano); symlink attivo
- [x] 2026-07-19: W6 pilot COMPLETO, end-to-end watched su #3030 → PR wishew-monorepo#3485
  (In review + agent:qa, follow-up #3484 filed). Percorsi esercitati dal vivo: verdetti
  human (#944) e needs-spec (#1749), claim+collision guard, plan-forge con verifica che ha
  REFUTATO un claim dell'issue (user_tags viva), second-opinion 2-lab (Claude timeout),
  impl subagent opus, review fleet (3 Minor fixati; security ritentata dopo stallo),
  SCORE 97/100, finish con recovery da steps_done. Prossimo: /loop cap 2

## Surprises & Discoveries

- `origin/dev` morto sul monorepo: scoperto in questa sessione, non documentato altrove.
- PR #87 (hikma) mergiata la mattina stessa della progettazione wishew: architettura convergente
  sviluppata in parallelo, il porting sostituisce il greenfield.
- Review fleet (architecture + security): 0 Critical, 6 Major, 10 Minor totali. I due Major
  security stanno entrambi al seam script/agente (titolo in shell, superfici CI pre-merge):
  lo script era pulito, il boundary no. Il pattern `--title` vulnerabile esisteva identico
  nel work.py pre-esistente: fixato anche lì.
- Pilot #3030: 3 bug reali di harness scovati e fixati in-flight: (1) skip_done troncava la
  paginazione e rendeva invisibili gli item freschi (claude-skills#2); (2) agent SSH senza
  identità in sessione remota → core.sshCommand repo-local sulla chiave -remote; (3) gh pr
  edit richiede read:org che il token non ha → label via REST (claude-skills#3). Più: Docker
  error-dialog ha richiesto intervento umano (rail all-reviewers-down aveva l'alternativa
  giusta: gate umano esplicito offerto via AskUserQuestion).

## Outcomes & Retrospective

(compilare alla chiusura)
