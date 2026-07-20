# ABOUTME: SSH auth for git automation on the workstation — agent empties out, Match exec doesn't fire in harness subprocesses
# ABOUTME: Fix: load the passphrase-less automation key, or pin it repo-local via core.sshCommand

# Problem

Mid-session, every `git fetch/push` over SSH started failing with `Permission denied (publickey)` — including from `loop.py` subprocesses that had worked minutes earlier. Diagnosis in layers:

1. `ssh-add -l` → "The agent has no identities": the default agent had emptied out (1Password agent locked / biometrics unavailable in a remote session).
2. `~/.ssh/config` has a `Match host github.com exec "test -n \"$SSH_CONNECTION\""` block that routes github.com to the on-disk `id_ed25519_remote` key *inside inbound SSH sessions* — but harness/tool subprocesses don't necessarily inherit `SSH_CONNECTION`, so the Match fails and everything falls through to `Host *` → the (locked) 1Password agent.

# Solution

Two levels, per Max's "usa la chiave -remote":

```bash
# one-off: load the passphrase-less automation key into the agent
ssh-add /Users/maroffo/.ssh/id_ed25519_remote

# durable, per-repo (inherited by all its worktrees — what the issue-loop relies on):
git -C ~/Development/Wishew/wishew-monorepo config core.sshCommand \
  "ssh -i /Users/maroffo/.ssh/id_ed25519_remote -o IdentitiesOnly=yes -o IdentityAgent=none"
```

Undo with `git config --unset core.sshCommand` in the repo.

# Why It Works

`core.sshCommand` bypasses both failure modes at once: no agent dependency (`IdentityAgent=none`) and no reliance on the `Match exec` environment probe. Repo-local scope keeps the biometric 1Password flow untouched for every other repo. The `-remote` key is passphrase-less by design (created for exactly this automation use), so subprocesses need no interactive unlock.
