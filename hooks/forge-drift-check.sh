#!/usr/bin/env bash
# ABOUTME: SessionStart hook reporting drift between the forge checkout and the installed ~/.claude
# ABOUTME: Read-only and silent when clean: no network, no git, no auto-fix, always exits 0

# Two documented incidents motivate this: stale `agents/` copies that survived
# two manual audits, and new hook files that need a post-merge `ln -s` nobody
# remembers. install.sh guards symlinks at install time only; nothing looked at
# the installed tree afterwards.
#
# Deliberately unthrottled: the whole point is catching drift on the FIRST
# session after a merge, and a timestamp file would only add a clock-skew
# failure mode to a scan that costs a handful of forks. The noise budget is
# paid for by being silent when clean, not by running less often.

set +e
set -u

# Deterministic glob order regardless of the caller's locale.
LC_ALL=C
export LC_ALL

# The SessionStart payload is not needed (the matcher already selects
# startup|resume), but draining stdin keeps the writer from seeing a closed pipe.
[ -t 0 ] || cat >/dev/null 2>&1

NL='
'
FORGE_ROOT=""

# Follow a symlink chain lexically, then make the result physical. Dangling
# links resolve too: the raw target is exactly what the forge-origin test needs.
resolve_path() {
  local _p _n _l _d _b
  _p="$1"
  _n=0
  while [ -L "$_p" ] && [ "$_n" -lt 20 ]; do
    _l=$(readlink "$_p" 2>/dev/null) || break
    [ -n "$_l" ] || break
    case "$_l" in
      /*) _p="$_l" ;;
      *) _p="${_p%/*}/$_l" ;;
    esac
    _n=$((_n + 1))
  done
  # Fast path: a target already under the checkout needs no canonicalisation,
  # which is the common case and keeps the scan fork-free.
  if [ -n "$FORGE_ROOT" ]; then
    case "$_p" in "$FORGE_ROOT"/*) printf '%s\n' "$_p"; return 0 ;; esac
  fi
  case "$_p" in
    */*) _d="${_p%/*}" ;;
    *) _d="." ;;
  esac
  [ -n "$_d" ] || _d="/"
  _b="${_p##*/}"
  if _d=$(cd -P "$_d" 2>/dev/null && pwd -P); then
    printf '%s/%s\n' "$_d" "$_b"
  else
    printf '%s\n' "$_p"
  fi
}

self=$(resolve_path "$0")
hook_dir="${self%/*}"
FORGE_ROOT="${hook_dir%/*}"
CLAUDE_DIR="$HOME/.claude"

[ -n "$FORGE_ROOT" ] && [ -d "$FORGE_ROOT/hooks" ] && [ -d "$CLAUDE_DIR" ] || exit 0

# Installed as a plain copy rather than a symlink back to a checkout, the script
# would take ~/.claude itself for the forge repo and compare it against itself.
# It cannot detect its own missing installation (see the bootstrap note in
# README): better silent than nonsensical.
claude_phys=$(resolve_path "$CLAUDE_DIR")
case "$FORGE_ROOT" in
  "$claude_phys" | "$claude_phys"/*) exit 0 ;;
esac

# Intentionally-absent components on secondary machines with a partial install.
OMIT_LIST=""
if [ -f "$CLAUDE_DIR/.forge-omit" ]; then
  while IFS= read -r line || [ -n "$line" ]; do
    line="${line%%#*}"
    line="${line#"${line%%[![:space:]]*}"}"
    line="${line%"${line##*[![:space:]]}"}"
    [ -n "$line" ] || continue
    OMIT_LIST="$OMIT_LIST$line$NL"
  done < "$CLAUDE_DIR/.forge-omit"
fi

SETTINGS_BLOB=$(cat "$CLAUDE_DIR/settings.json" 2>/dev/null)
EXAMPLE_BLOB=$(cat "$FORGE_ROOT/hooks/settings.example.json" 2>/dev/null)

is_omitted() {
  case "$NL$OMIT_LIST" in *"$NL$1$NL"*) return 0 ;; esac
  return 1
}

is_forge() {
  case "$1" in "$FORGE_ROOT"/*) return 0 ;; esac
  return 1
}

finding() { printf '[forge-drift] %s\n' "$1"; }

# A forge hook that is installed but absent from settings.json never fires.
# Only hooks the shipped fragment registers are expected there, so helpers that
# are sourced rather than registered (_commit_target.sh, _freeze_boundary.sh)
# stay quiet. Substring match on the filename: matcher-format drift is a known
# gap, recorded in tech-debt.
check_registration() {
  _name="$1"
  [ -n "$SETTINGS_BLOB" ] && [ -n "$EXAMPLE_BLOB" ] || return 0
  case "$EXAMPLE_BLOB" in *"{{HOOKS_DIR}}/$_name"*) ;; *) return 0 ;; esac
  case "$SETTINGS_BLOB" in *"/$_name"*) return 0 ;; esac
  finding "$_name is installed but not registered in $CLAUDE_DIR/settings.json; fix: register it in settings.json as in $FORGE_ROOT/hooks/settings.example.json"
}

# A whole category installed as one symlink (rules/ and skills/ on a developer
# machine). The only drift possible there is the link going dangling, which
# removes every rule or skill at once without a word.
scan_dir_symlink() {
  _cat="$1"
  _dir="$CLAUDE_DIR/$_cat"
  [ -L "$_dir" ] || return 1
  if [ ! -e "$_dir" ]; then
    _target=$(resolve_path "$_dir")
    if is_forge "$_target" && ! is_omitted "$_cat"; then
      finding "$CLAUDE_DIR/$_cat is a dangling symlink to $_target; fix: ln -sfn $FORGE_ROOT/$_cat $CLAUDE_DIR/$_cat"
    fi
  fi
  return 0
}

# Takes a category and one or more globs: hooks ship as .sh entry points plus the
# .py files holding the logic, and install.sh installs both, so a scan of only one
# extension is blind to half the directory.
scan_entries() {
  _cat="$1"
  shift
  _dir="$CLAUDE_DIR/$_cat"
  [ -d "$_dir" ] || return 0
  _managed=0

  for _glob in "$@"; do
    for _entry in "$_dir"/$_glob; do
      [ -e "$_entry" ] || [ -L "$_entry" ] || continue
      _name="${_entry##*/}"
      is_omitted "$_name" && continue
      _src="$FORGE_ROOT/$_cat/$_name"
      if [ -L "$_entry" ] && [ -e "$_entry" ]; then
        # Non-forge entries (notify.sh, herdr-agent-state.sh) are out of scope by
        # construction: `-ef` compares device and inode through the link, so it
        # says the entry IS the checkout's file rather than merely that its path
        # looks like it. It is also a shell builtin, which keeps the whole clean
        # scan free of the ~30 readlink forks a resolved-path test would cost.
        if [ "$_entry" -ef "$_src" ]; then
          _managed=1
          [ "$_cat" = "hooks" ] && check_registration "$_name"
        elif [ -e "$_src" ]; then
          # Same name as a checkout file but a different inode: the link was
          # repointed away from the forge, which is the diverging install a
          # stale copy only makes visible when it is a regular file. Names with
          # no counterpart in the checkout stay out of scope, as above.
          _target=$(resolve_path "$_entry")
          finding "$_entry points at $_target, not at $_src; fix: ln -sfn $_src $_entry"
        fi
      elif [ -L "$_entry" ]; then
        # Dangling: no inode to compare, so read where it meant to point. Rare by
        # nature, which is why this is the branch that may fork.
        _target=$(resolve_path "$_entry")
        is_forge "$_target" || continue
        finding "dangling symlink $_entry -> $_target; fix: ln -sfn $_src $_entry"
      elif [ -f "$_entry" ]; then
        # The stale-copy incident class: a regular file shadowing a forge file,
        # frozen at whatever the repo held when it was copied.
        [ -f "$_src" ] || continue
        if cmp -s "$_entry" "$_src"; then
          # A byte-identical copy is what install.sh produces for a new hook, so
          # it is not drift, but it still has to be registered to ever fire.
          [ "$_cat" = "hooks" ] && check_registration "$_name"
        else
          finding "stale copy $_entry differs from $_src; fix: ln -sfn $_src $_entry"
        fi
      fi
    done
  done

  # A category with no forge symlink at all is simply not installed from the
  # checkout on this machine; listing everything it "lacks" would be noise.
  [ "$_managed" -eq 1 ] || return 0

  for _glob in "$@"; do
    for _src in "$FORGE_ROOT/$_cat"/$_glob; do
      [ -e "$_src" ] || continue
      _name="${_src##*/}"
      is_omitted "$_name" && continue
      _entry="$_dir/$_name"
      if [ -e "$_entry" ] || [ -L "$_entry" ]; then
        continue
      fi
      finding "$_cat/$_name is in the checkout but has no entry in $_dir; fix: ln -s $_src $_entry"
    done
  done
}

collect() {
  for _category in hooks agents rules skills; do
    scan_dir_symlink "$_category" && continue
    case "$_category" in
      # Per-entry skills scanning happens only when ~/.claude/skills is itself
      # forge-managed (handled above): a copy install is install.sh's supported
      # default, not drift, and flagging it would be a false-positive storm.
      skills) continue ;;
      hooks) scan_entries hooks '*.sh' '*.py' ;;
      agents) scan_entries agents '*' ;;
      rules) scan_entries rules '*.md' ;;
    esac
  done
}

findings=$(collect 2>/dev/null)
[ -n "$findings" ] || exit 0

count=$(printf '%s\n' "$findings" | wc -l | tr -d ' ')
if [ "$count" -le 3 ]; then
  printf '%s\n' "$findings"
else
  printf '%s\n' "$findings" | head -n 2
  finding "+$((count - 2)) more drift findings; fix: same pattern, ln -s $FORGE_ROOT/<dir>/<name> $CLAUDE_DIR/<dir>/<name> (or register in settings.json)"
fi
exit 0
