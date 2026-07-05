# ABOUTME: Session log — import of the Bringles two-confirmation gate as the score-evidence-guard hook
# ABOUTME: Vault copy pending (Obsidian was not running); mirror to "claude-forge - Log" when available

## 2026-07-05: Import two-confirmation gate da Bringles

- Valutato `hikmaai-io/hikma-bringles` (M0): niente merge tra harness, travaso di idee. Importata la decision #2 (two-confirmation gate: exit code computazionale + verdetto judge, "the loop trusts evidence, not prose").
- Nuovo Stop hook `score-evidence-guard`: un turno che riporta `SCORE: <n>/100` viene bloccato se non esiste un comando di verifica riuscito dopo l'ultimo edit a sorgenti, dopo l'ultimo verify fallito e dopo l'ultimo lancio di subagent write-class (`software-engineer`). I reviewer read-only non invalidano l'evidenza (REVIEW segue VERIFY nel protocollo).
- Review architecture + security: 5 Major corretti (latest-evidence-must-be-green, RecursionError fail-open, verify senza id non è evidenza, buco subagent-edit chiuso parzialmente, drift-guard sulle costanti duplicate con verify-before-stop). Residui false-allow documentati nel contract (edit via Bash tipo `sed -i`, `pip install` che matcha VERIFY_RE).
- SCORE: 94/100 (threshold: 80, gate: commit). Commit `40319f6` su `feat/score-evidence-guard`.
- Contract: `quality_reports/harness_changes/2026-07-05_score-evidence-guard.md`.

### Aperture

- Post-merge: `ln -s` di `score-evidence-guard.sh` e `.py` in `~/.claude/hooks/` + entry Stop in `~/.claude/settings.json` (pattern noto dal treno del 2026-07-04).
- Follow-up: backport di `failed_ids` a `verify-before-stop.py` (oggi un verify fallito soddisfa quel gate), con contract separato.
