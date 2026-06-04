#!/bin/sh
# ABOUTME: Entrypoint that restores .claude.json from volume backup before running claude
# ABOUTME: Suppresses "configuration file not found" warnings on read-only volume mounts

# If .claude.json doesn't exist but a backup does, restore the latest one
if [ ! -f "$HOME/.claude.json" ] && [ -d "$HOME/.claude/backups" ]; then
  BACKUP=$(ls -t "$HOME/.claude/backups/.claude.json.backup."* 2>/dev/null | head -1)
  if [ -n "$BACKUP" ]; then
    cp "$BACKUP" "$HOME/.claude.json" 2>/dev/null || true
  fi
fi

exec claude "$@"
