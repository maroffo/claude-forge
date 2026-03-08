#!/usr/bin/env bash
# ABOUTME: One-liner bootstrap for claude-forge: curl -sL https://raw.githubusercontent.com/maroffo/claude-forge/main/get.sh | bash
# ABOUTME: Clones the repo to ~/.claude-forge and runs the interactive installer
set -euo pipefail

REPO="https://github.com/maroffo/claude-forge.git"
INSTALL_DIR="$HOME/.claude-forge"

echo ""
echo "  claude-forge bootstrap"
echo "  ======================"
echo ""

# Clone or update
if [[ -d "$INSTALL_DIR/.git" ]]; then
  echo "  Updating existing clone at $INSTALL_DIR ..."
  git -C "$INSTALL_DIR" pull --ff-only
else
  if [[ -d "$INSTALL_DIR" ]]; then
    echo "  $INSTALL_DIR exists but is not a git repo. Backing up ..."
    mv "$INSTALL_DIR" "$INSTALL_DIR.bak-$(date +%Y%m%d-%H%M%S)"
  fi
  echo "  Cloning claude-forge to $INSTALL_DIR ..."
  git clone "$REPO" "$INSTALL_DIR"
fi

echo ""

# Run installer
exec "$INSTALL_DIR/install.sh"
