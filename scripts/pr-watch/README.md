# ABOUTME: Unattended PR-review bot + macOS menu-bar GUI that runs the /pr-review skill headless.
# ABOUTME: Poller, GUI, launchd templates, installer, and config for scripts/pr-watch/.

# pr-watch

Unattended PR-review bot with a macOS menu-bar GUI. Polls GitHub for review-worthy
PRs and dispatches a headless `claude -p` that invokes the `/pr-review` skill and
posts the review as a PR comment. Replaces the session-bound `/loop` watcher: it
survives logout/reboot and keeps no Claude session open.

## Files

| File | Role |
|------|------|
| `pr-watch.sh` | The poller. Mechanical scope filter (assigned-to-me OR terraform/infra/golang/database/build/security by path) + Haiku triage for the fuzzy "is it architecture?" residue. In-scope PRs get a `claude -p --model opus` `/pr-review` that posts the comment. |
| `pr-watch-menubar.py` | rumps menu-bar GUI (run via `uv run --script`). Status glyph + reviews-today count, last reviews (clickable to the PR), recent activity, Poll-now / Pause-Resume / open-log. `--selftest` prints status JSON, no GUI. |
| `com.wishew.pr-watch.plist` | LaunchAgent template for the bot (every 600s). |
| `com.wishew.pr-watch-menubar.plist` | LaunchAgent template for the GUI (KeepAlive). |
| `install.sh` | Substitutes machine paths into the templates and (re)loads both agents. |

## Install

```bash
./install.sh                                   # reviews ~/Development/Wishew/wishew-monorepo by default
./install.sh /abs/path/to/some-other-repo      # or point it at another repo
```

State and logs live outside any repo, in `~/.local/state/pr-watch/`:
`reviewed.txt` (append-only dedupe set), `context.log` (per-review digests fed back
for cross-PR memory), `pr-watch.log` (decisions/activity).

## Requirements

`gh` (authenticated), `jq`, `uv`, `claude`, and `docker` (for the `/second-opinion`
panel) on PATH. The reviewer needs `GEMINI_API_KEY` and `DEEPSEEK_API_KEY`; the
script exports them from `~/.config/{gemini,deepseek}-api-key` at runtime so the
composed `/gemini-review` and `/second-opinion` sub-steps work headless.

## Config (env, all optional)

`PR_WATCH_REPO` (default `Wishew/wishew-monorepo`), `PR_WATCH_ME` (assignee login),
`PR_WATCH_REPO_DIR` (working copy the reviewer runs in), `PR_WATCH_WINDOW_MIN`
(default 1440), `PR_WATCH_REVIEW_MODEL` (default `opus`), `PR_WATCH_TRIAGE_MODEL`
(default `haiku`), `PR_WATCH_DRY_RUN=1` (decide + log, do not review).

## Manage

```bash
launchctl unload ~/Library/LaunchAgents/com.wishew.pr-watch.plist          # stop the bot
launchctl load   ~/Library/LaunchAgents/com.wishew.pr-watch.plist          # start it
tail -f ~/.local/state/pr-watch/pr-watch.log                               # watch decisions
uv run --script pr-watch-menubar.py --selftest                             # GUI status without the GUI
```
