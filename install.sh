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

# --- Category definitions (bash 3.x compatible) ---
# Categories indexed 0-6
CAT_ORDER=(CORE LANGUAGES REVIEW KNOWLEDGE EMAIL CONTENT ADR)

# Labels by index
CAT_LABEL_0="Core (rules, CLAUDE.md, index files)"
CAT_LABEL_1="Languages and Frameworks"
CAT_LABEL_2="Code Review and Analysis"
CAT_LABEL_3="Obsidian / Knowledge Management"
CAT_LABEL_4="Productivity (BuJo, ClickUp, clippings)"
CAT_LABEL_5="Blog and Content Creation"
CAT_LABEL_6="Architecture Decision Records"

get_label() {
  case "$1" in
    0) echo "$CAT_LABEL_0" ;;
    1) echo "$CAT_LABEL_1" ;;
    2) echo "$CAT_LABEL_2" ;;
    3) echo "$CAT_LABEL_3" ;;
    4) echo "$CAT_LABEL_4" ;;
    5) echo "$CAT_LABEL_5" ;;
    6) echo "$CAT_LABEL_6" ;;
  esac
}

# Skills per category
CAT_SKILLS_0="commit source-control refine-requirements releasing-software score project-checks"
CAT_SKILLS_1="golang python apple-swift android-kotlin rails ruby react-nextjs terraform cloud-infrastructure swiftui-liquid-glass ios-debugger"
CAT_SKILLS_2="gemini-review verify-frontend second-opinion test-design-reviewer cognitive-load-analyzer legacy-code-expert skill-forge project-analyzer harness-trace harness-mechanic"
CAT_SKILLS_3="obsidian knowledge-sync learning-docs learning-loop notion-sync"
CAT_SKILLS_4="process-clippings bujo bujo-sync clickup"
CAT_SKILLS_5="blog-writer humanizer cover-image table-image"
CAT_SKILLS_6="adr"

get_skills() {
  case "$1" in
    0) echo "$CAT_SKILLS_0" ;;
    1) echo "$CAT_SKILLS_1" ;;
    2) echo "$CAT_SKILLS_2" ;;
    3) echo "$CAT_SKILLS_3" ;;
    4) echo "$CAT_SKILLS_4" ;;
    5) echo "$CAT_SKILLS_5" ;;
    6) echo "$CAT_SKILLS_6" ;;
    *) echo "" ;;
  esac
}

# Top-level skill files per category (empty string for categories with none)
CAT_FILES_0="_INDEX.md _PATTERNS.md _AST_GREP.md"
CAT_FILES_1=""
CAT_FILES_2=""
CAT_FILES_3="_OBSIDIAN.md _SECOND_BRAIN.md _VAULT_CONTEXT.md"
CAT_FILES_4=""
CAT_FILES_5="_generate_image.py"
CAT_FILES_6=""

get_files() {
  case "$1" in
    0) echo "$CAT_FILES_0" ;;
    1) echo "$CAT_FILES_1" ;;
    2) echo "$CAT_FILES_2" ;;
    3) echo "$CAT_FILES_3" ;;
    4) echo "$CAT_FILES_4" ;;
    5) echo "$CAT_FILES_5" ;;
    6) echo "$CAT_FILES_6" ;;
    *) echo "" ;;
  esac
}

# Selection tracking: SELECTED_X=1 means category index X is selected
SELECTED_0="" ; SELECTED_1="" ; SELECTED_2="" ; SELECTED_3=""
SELECTED_4="" ; SELECTED_5="" ; SELECTED_6=""

set_selected() {
  case "$1" in
    0) SELECTED_0=1 ;; 1) SELECTED_1=1 ;; 2) SELECTED_2=1 ;;
    3) SELECTED_3=1 ;; 4) SELECTED_4=1 ;; 5) SELECTED_5=1 ;;
    6) SELECTED_6=1 ;;
  esac
}

is_selected() {
  case "$1" in
    0) [[ -n "$SELECTED_0" ]] ;; 1) [[ -n "$SELECTED_1" ]] ;;
    2) [[ -n "$SELECTED_2" ]] ;; 3) [[ -n "$SELECTED_3" ]] ;;
    4) [[ -n "$SELECTED_4" ]] ;; 5) [[ -n "$SELECTED_5" ]] ;;
    6) [[ -n "$SELECTED_6" ]] ;; *) return 1 ;;
  esac
}

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
  echo "  $num) $(get_label "$i")"
done
echo ""
echo "  a) All categories"
echo ""
read -rp "Select categories (comma-separated numbers, or 'a' for all): " selection

if [[ "$selection" == "a" || "$selection" == "A" ]]; then
  for i in "${!CAT_ORDER[@]}"; do
    set_selected "$i"
  done
else
  IFS=',' read -ra nums <<< "$selection"
  for n in "${nums[@]}"; do
    n=$(echo "$n" | tr -d ' ')
    if [[ "$n" =~ ^[0-9]+$ ]] && (( n >= 1 && n <= ${#CAT_ORDER[@]} )); then
      set_selected $((n - 1))
    else
      echo "Warning: ignoring invalid selection '$n'"
    fi
  done
fi

selected_count=0
selected_names=""
for i in "${!CAT_ORDER[@]}"; do
  if is_selected "$i"; then
    selected_count=$((selected_count + 1))
    selected_names="$selected_names ${CAT_ORDER[$i]}"
  fi
done

if [[ $selected_count -eq 0 ]]; then
  echo "No categories selected. Exiting."
  exit 0
fi

echo ""
echo "Selected:$selected_names"
echo ""

# --- Collect variables ---
read -rp "Your first name (used in CLAUDE.md, skills): " USER_NAME
GITHUB_USER=$(git config user.name 2>/dev/null || echo "")
read -rp "GitHub username [${GITHUB_USER:-detect from git}]: " input_gh
GITHUB_USER="${input_gh:-$GITHUB_USER}"

FULL_NAME="" ; VAULT_PATH="" ; EMAIL_ADDRESS="" ; BLOG_PATH="" ; BLOG_VAULT_FOLDER=""

# ADR=6, CONTENT=5
if is_selected 6 || is_selected 5; then
  read -rp "Full name (for ADR author, blog bylines): " FULL_NAME
fi

# KNOWLEDGE=3
if is_selected 3; then
  default_vault="$HOME/Library/Mobile Documents/iCloud~md~obsidian/Documents"
  read -rp "Obsidian vault path [$default_vault]: " input_vault
  VAULT_PATH="${input_vault:-$default_vault}"
fi

# EMAIL=4
if is_selected 4; then
  read -rp "Email address (for Gmail skills): " EMAIL_ADDRESS
fi

# CONTENT=5
if is_selected 5; then
  read -rp "Blog repo path (absolute): " BLOG_PATH
  if is_selected 3; then
    default_blogfolder="$(echo "$USER_NAME" | tr '[:upper:]' '[:lower:]')-blog"
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
for i in "${!CAT_ORDER[@]}"; do
  is_selected "$i" || continue

  # Copy skill directories
  for skill in $(get_skills "$i"); do
    copy_skill_dir "$skill"
    installed_skills+=("$skill")
  done

  # Copy top-level skill files
  for f in $(get_files "$i"); do
    copy_skill_file "$f"
    installed_files+=("$f")
  done
done

# --- Copy rules (always, if CORE selected) ---
# CORE=0
if is_selected 0; then
  cp "$SCRIPT_DIR"/rules/*.md "$TARGET_DIR/rules/"
  installed_files+=("rules/*")
  cp -R "$SCRIPT_DIR"/agents/ "$TARGET_DIR/agents/"
  installed_files+=("agents/*")
  cp "$SCRIPT_DIR/CLAUDE.md.example" "$TARGET_DIR/CLAUDE.md"
  installed_files+=("CLAUDE.md")
  # Portability: AGENTS.md is the emerging cross-tool convention; keep a relative
  # symlink so both Claude Code (CLAUDE.md) and tools reading AGENTS.md see the same content.
  ln -sf CLAUDE.md "$TARGET_DIR/AGENTS.md"
  installed_files+=("AGENTS.md -> CLAUDE.md")
  # Enforcement layer: copy hook scripts (settings.json registration stays manual; see summary)
  if [[ -d "$SCRIPT_DIR/hooks" ]]; then
    mkdir -p "$TARGET_DIR/hooks"
    for h in "$SCRIPT_DIR"/hooks/*.sh "$SCRIPT_DIR"/hooks/*.py; do
      [[ -f "$h" ]] || continue
      cp "$h" "$TARGET_DIR/hooks/$(basename "$h")"
      chmod +x "$TARGET_DIR/hooks/$(basename "$h")"
    done
    installed_files+=("hooks/*")
    INSTALLED_HOOKS=1
  fi
fi

# --- Apply replacements ---
replace_in_installed() {
  local old="$1" new="$2"
  [[ -n "$new" ]] || return 0
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
  if [[ -f "$TARGET_DIR/CLAUDE.md" ]] && grep -qF "$old" "$TARGET_DIR/CLAUDE.md" 2>/dev/null; then
    sed_inplace "s|$old|$new|g" "$TARGET_DIR/CLAUDE.md"
  fi
}

echo ""
echo "Applying personalizations ..."

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

if [[ -n "$VAULT_PATH" ]]; then
  replace_in_installed "/Users/maroffo/Library/Mobile Documents/iCloud~md~obsidian/Documents" "$VAULT_PATH"
fi

if [[ -n "$BLOG_PATH" ]]; then
  replace_in_installed "/Users/maroffo/Development/private/blog" "$BLOG_PATH"
fi

if [[ -n "$EMAIL_ADDRESS" ]]; then
  replace_in_installed "maroffo@gmail.com" "$EMAIL_ADDRESS"
fi

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
for i in "${!CAT_ORDER[@]}"; do
  is_selected "$i" && echo "    - $(get_label "$i")"
done
echo ""
echo "  Skills: ${installed_skills[*]}"
[[ ${#installed_files[@]} -gt 0 ]] && echo "  Files:  ${installed_files[*]}"
echo ""

if [[ -n "${INSTALLED_HOOKS:-}" ]]; then
  echo "  Enforcement hooks copied to $TARGET_DIR/hooks/."
  echo "  To activate, merge the following into $TARGET_DIR/settings.json"
  echo "  (under the top-level \"permissions\" and \"hooks\" keys):"
  echo ""
  if [[ -f "$SCRIPT_DIR/hooks/settings.example.json" ]]; then
    # Render the template with the real hooks path substituted in
    sed "s|{{HOOKS_DIR}}|$TARGET_DIR/hooks|g" "$SCRIPT_DIR/hooks/settings.example.json"
  else
    echo "  (see hooks/settings.example.json in the repo)"
  fi
  echo ""
fi

echo "Done. Restart Claude Code (or open /hooks) to pick up the new skills and hooks."
