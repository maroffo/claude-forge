#!/usr/bin/env bash
# ABOUTME: Interactive installer for claude-forge skills, rules, and agents
# ABOUTME: Copies selected categories to ~/.claude/ with personalized replacements
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_DIR="$HOME/.claude"
BACKUP_DIR="$TARGET_DIR/backup-$(date +%Y%m%d-%H%M%S)"

# --- Detect sed variant ---
if sed --version 2>/dev/null | grep -q GNU; then
  sed_inplace() { sed -i "$@"; }
else
  sed_inplace() { sed -i '' "$@"; }
fi

# --- Category definitions ---
declare -A CAT_LABELS=(
  [CORE]="Core (rules, CLAUDE.md, index files)"
  [LANGUAGES]="Languages and Frameworks"
  [REVIEW]="Code Review and Analysis"
  [KNOWLEDGE]="Obsidian / Knowledge Management"
  [EMAIL]="Email and Productivity"
  [CONTENT]="Blog and Content Creation"
  [ADR]="Architecture Decision Records"
)
CAT_ORDER=(CORE LANGUAGES REVIEW KNOWLEDGE EMAIL CONTENT ADR)

# Skills per category (directories under skills/ or top-level files)
declare -A CAT_SKILLS=(
  [CORE]="commit source-control refine-requirements releasing-software"
  [LANGUAGES]="golang python apple-swift android-kotlin rails ruby react-nextjs terraform cloud-infrastructure swiftui-liquid-glass ios-debugger"
  [REVIEW]="gemini-review second-opinion test-design-reviewer cognitive-load-analyzer legacy-code-expert skill-forge project-analyzer"
  [KNOWLEDGE]="obsidian knowledge-sync learning-docs notion-sync"
  [EMAIL]="inbox-triage email-cleanup newsletter-digest process-clippings process-email-bookmarks bujo bujo-sync clickup"
  [CONTENT]="blog-writer humanizer cover-image table-image"
  [ADR]="adr"
)
# Top-level skill files per category
declare -A CAT_FILES=(
  [CORE]="_INDEX.md _PATTERNS.md _AST_GREP.md"
  [KNOWLEDGE]="_OBSIDIAN.md _SECOND_BRAIN.md _VAULT_CONTEXT.md"
  [EMAIL]="_GMAIL.md"
  [CONTENT]="_generate_image.py"
)

# --- Banner ---
echo ""
echo "  claude-forge installer"
echo "  ======================"
echo ""
echo "  This script copies skills, rules, and agents to ~/.claude/"
echo "  with personalized values. Safe to re-run (backs up existing files)."
echo ""

# --- Category selection ---
echo "Available categories:"
echo ""
for i in "${!CAT_ORDER[@]}"; do
  num=$((i + 1))
  cat="${CAT_ORDER[$i]}"
  echo "  $num) ${CAT_LABELS[$cat]}"
done
echo ""
echo "  a) All categories"
echo ""
read -rp "Select categories (comma-separated numbers, or 'a' for all): " selection

declare -A SELECTED=()
if [[ "$selection" == "a" || "$selection" == "A" ]]; then
  for cat in "${CAT_ORDER[@]}"; do
    SELECTED[$cat]=1
  done
else
  IFS=',' read -ra nums <<< "$selection"
  for n in "${nums[@]}"; do
    n=$(echo "$n" | tr -d ' ')
    if [[ "$n" =~ ^[0-9]+$ ]] && (( n >= 1 && n <= ${#CAT_ORDER[@]} )); then
      SELECTED[${CAT_ORDER[$((n - 1))]}]=1
    else
      echo "Warning: ignoring invalid selection '$n'"
    fi
  done
fi

if [[ ${#SELECTED[@]} -eq 0 ]]; then
  echo "No categories selected. Exiting."
  exit 0
fi

echo ""
echo "Selected: ${!SELECTED[*]}"
echo ""

# --- Collect variables ---
# Always needed (Core is implicit for USER_NAME)
read -rp "Your first name (used in CLAUDE.md, skills): " USER_NAME
GITHUB_USER=$(git config user.name 2>/dev/null || echo "")
read -rp "GitHub username [${GITHUB_USER:-detect from git}]: " input_gh
GITHUB_USER="${input_gh:-$GITHUB_USER}"

FULL_NAME="" VAULT_PATH="" VAULT_NAME="" EMAIL_ADDRESS="" BLOG_PATH="" BLOG_VAULT_FOLDER=""

if [[ -n "${SELECTED[ADR]:-}" ]] || [[ -n "${SELECTED[CONTENT]:-}" ]]; then
  read -rp "Full name (for ADR author, blog bylines): " FULL_NAME
fi

if [[ -n "${SELECTED[KNOWLEDGE]:-}" ]]; then
  default_vault="$HOME/Library/Mobile Documents/iCloud~md~obsidian/Documents"
  read -rp "Obsidian vault path [$default_vault]: " input_vault
  VAULT_PATH="${input_vault:-$default_vault}"
  default_vname="$(basename "$VAULT_PATH")"
  read -rp "Vault name [$default_vname]: " input_vname
  VAULT_NAME="${input_vname:-$default_vname}"
fi

if [[ -n "${SELECTED[EMAIL]:-}" ]]; then
  read -rp "Email address (for Gmail skills): " EMAIL_ADDRESS
fi

if [[ -n "${SELECTED[CONTENT]:-}" ]]; then
  read -rp "Blog repo path (absolute): " BLOG_PATH
  if [[ -n "${SELECTED[KNOWLEDGE]:-}" ]]; then
    default_blogfolder="${USER_NAME,,}-blog"
    read -rp "Blog vault folder name [$default_blogfolder]: " input_blogfolder
    BLOG_VAULT_FOLDER="${input_blogfolder:-$default_blogfolder}"
  fi
fi

# --- Backup existing files ---
if [[ -d "$TARGET_DIR/skills" ]] || [[ -d "$TARGET_DIR/rules" ]] || [[ -d "$TARGET_DIR/agents" ]]; then
  echo ""
  echo "Backing up existing files to $BACKUP_DIR ..."
  mkdir -p "$BACKUP_DIR"
  for d in skills rules agents; do
    [[ -d "$TARGET_DIR/$d" ]] && cp -R "$TARGET_DIR/$d" "$BACKUP_DIR/$d"
  done
  [[ -f "$TARGET_DIR/CLAUDE.md" ]] && cp "$TARGET_DIR/CLAUDE.md" "$BACKUP_DIR/CLAUDE.md"
fi

# --- Create target directories ---
mkdir -p "$TARGET_DIR/skills" "$TARGET_DIR/rules" "$TARGET_DIR/agents"

# --- Copy functions ---
copy_skill_dir() {
  local name="$1"
  local src="$SCRIPT_DIR/skills/$name"
  [[ -d "$src" ]] || return 0
  # Skip .venv, .pytest_cache, .ruff_cache, __pycache__, .egg-info
  rsync -a --exclude='.venv' --exclude='.pytest_cache' --exclude='.ruff_cache' \
    --exclude='__pycache__' --exclude='*.egg-info' \
    "$src/" "$TARGET_DIR/skills/$name/"
}

copy_skill_file() {
  local name="$1"
  local src="$SCRIPT_DIR/skills/$name"
  [[ -f "$src" ]] || return 0
  cp "$src" "$TARGET_DIR/skills/$name"
}

installed_skills=()
installed_files=()

# --- Install selected categories ---
for cat in "${CAT_ORDER[@]}"; do
  [[ -n "${SELECTED[$cat]:-}" ]] || continue

  # Copy skill directories
  for skill in ${CAT_SKILLS[$cat]:-}; do
    copy_skill_dir "$skill"
    installed_skills+=("$skill")
  done

  # Copy top-level skill files
  for f in ${CAT_FILES[$cat]:-}; do
    copy_skill_file "$f"
    installed_files+=("$f")
  done
done

# --- Copy rules (always, if CORE selected) ---
if [[ -n "${SELECTED[CORE]:-}" ]]; then
  cp "$SCRIPT_DIR"/rules/*.md "$TARGET_DIR/rules/"
  installed_files+=("rules/*")
  # Copy agents
  cp -R "$SCRIPT_DIR"/agents/ "$TARGET_DIR/agents/"
  installed_files+=("agents/*")
  # Copy and personalize CLAUDE.md.example
  cp "$SCRIPT_DIR/CLAUDE.md.example" "$TARGET_DIR/CLAUDE.md"
  installed_files+=("CLAUDE.md")
fi

# --- Apply replacements ---
# Helper: replace string in all installed files under TARGET_DIR
replace_in_installed() {
  local old="$1" new="$2"
  [[ -n "$new" ]] || return 0
  # Use find + sed on all .md, .py, .yaml files under TARGET_DIR/skills, rules, agents, and CLAUDE.md
  find "$TARGET_DIR/skills" "$TARGET_DIR/rules" "$TARGET_DIR/agents" \
    -type f \( -name '*.md' -o -name '*.py' -o -name '*.yaml' \) \
    -exec sh -c 'for f; do
      if grep -qF "$1" "$f" 2>/dev/null; then
        if sed --version 2>/dev/null | grep -q GNU; then
          sed -i "s|$1|$2|g" "$f"
        else
          sed -i "" "s|$1|$2|g" "$f"
        fi
      fi
    done' _ "$old" "$new" {} +
  # Also handle CLAUDE.md at target root
  if [[ -f "$TARGET_DIR/CLAUDE.md" ]] && grep -qF "$old" "$TARGET_DIR/CLAUDE.md" 2>/dev/null; then
    sed_inplace "s|$old|$new|g" "$TARGET_DIR/CLAUDE.md"
  fi
}

echo ""
echo "Applying personalizations ..."

# Name replacements
if [[ -n "$USER_NAME" ]]; then
  replace_in_installed 'Address me as "Max"' "Address me as \"$USER_NAME\""
  replace_in_installed "Max's style" "$USER_NAME's style"
  replace_in_installed "Max's voice" "$USER_NAME's voice"
  replace_in_installed "Max's Hugo blog" "$USER_NAME's Hugo blog"
  replace_in_installed "Max expressed" "$USER_NAME expressed"
  replace_in_installed "let Max pick" "let $USER_NAME pick"
  replace_in_installed "assignee = Max" "assignee = $USER_NAME"
fi

if [[ -n "$FULL_NAME" ]]; then
  replace_in_installed "Max Aroffo" "$FULL_NAME"
fi

# Path replacements
if [[ -n "$VAULT_PATH" ]]; then
  replace_in_installed "/Users/maroffo/Library/Mobile Documents/iCloud~md~obsidian/Documents" "$VAULT_PATH"
fi

if [[ -n "$BLOG_PATH" ]]; then
  replace_in_installed "/Users/maroffo/Development/private/blog" "$BLOG_PATH"
fi

# Email replacement
if [[ -n "$EMAIL_ADDRESS" ]]; then
  replace_in_installed "maroffo@gmail.com" "$EMAIL_ADDRESS"
fi

# Blog vault folder replacement
if [[ -n "$BLOG_VAULT_FOLDER" ]]; then
  replace_in_installed "maroffo-blog/" "$BLOG_VAULT_FOLDER/"
fi

# --- Summary ---
echo ""
echo "Installation complete."
echo ""
echo "  Target:  $TARGET_DIR/"
if [[ -d "${BACKUP_DIR:-}" ]]; then
  echo "  Backup:  $BACKUP_DIR/"
fi
echo ""
echo "  Installed categories:"
for cat in "${CAT_ORDER[@]}"; do
  [[ -n "${SELECTED[$cat]:-}" ]] && echo "    - ${CAT_LABELS[$cat]}"
done
echo ""
echo "  Skills: ${installed_skills[*]}"
[[ ${#installed_files[@]} -gt 0 ]] && echo "  Files:  ${installed_files[*]}"
echo ""
echo "Done. Restart Claude Code to pick up the new skills."
