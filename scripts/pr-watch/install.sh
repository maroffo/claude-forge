#!/usr/bin/env bash
# ABOUTME: Installs the pr-watch bot + menu-bar GUI launchd agents for the current user.
# ABOUTME: Substitutes machine paths into the plist templates and (re)loads both agents.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FORGE="$(cd "$HERE/../.." && pwd)"
USER_NAME="$(id -un)"
REPO_DIR="${1:-$HOME/Development/Wishew/wishew-monorepo}"   # repo whose PRs to review
LA="$HOME/Library/LaunchAgents"

mkdir -p "$HOME/.local/state/pr-watch" "$LA"

for name in com.wishew.pr-watch com.wishew.pr-watch-menubar; do
  dest="$LA/$name.plist"
  [ -f "$dest" ] && launchctl unload "$dest" 2>/dev/null || true
  sed -e "s#__FORGE__#$FORGE#g" \
      -e "s#__ABS_REPO__#$REPO_DIR#g" \
      -e "s#__USER__#$USER_NAME#g" \
      "$HERE/$name.plist" > "$dest"
  plutil -lint "$dest" >/dev/null
  launchctl load "$dest"
  echo "loaded $name"
done

echo "pr-watch installed. repo=$REPO_DIR  state/logs=~/.local/state/pr-watch/"
echo "stop:  launchctl unload ~/Library/LaunchAgents/com.wishew.pr-watch{,-menubar}.plist"
