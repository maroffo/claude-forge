# ABOUTME: macOS menu-bar GUI to monitor and control the pr-watch review bot.
# ABOUTME: Reads ~/.local/state/pr-watch/* and drives the launchd agent; run via `uv run --script`.
# /// script
# requires-python = ">=3.11"
# dependencies = ["rumps>=0.4.0"]
# ///
"""Menu-bar companion for scripts/pr-watch.sh.

Selftest (no GUI): `uv run --script scripts/pr-watch-menubar.py --selftest`
Run:               `uv run --script scripts/pr-watch-menubar.py`
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

LABEL = "com.wishew.pr-watch"
STATE = Path(os.environ.get("PR_WATCH_STATE", Path.home() / ".local/state/pr-watch"))
PLIST = Path.home() / "Library/LaunchAgents" / f"{LABEL}.plist"
SCRIPT = Path(__file__).resolve().parent / "pr-watch.sh"
REPO_URL = "https://github.com/Wishew/wishew-monorepo/pulls"
REFRESH_SECONDS = 20
MENU_PATH = "/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:" + str(Path.home() / ".local/bin")

LOG = STATE / "pr-watch.log"
CONTEXT = STATE / "context.log"
REVIEWED = STATE / "reviewed.txt"
LOCKDIR = STATE / "lock.d"

DIGEST_RE = re.compile(r"^DIGEST #(\d+)\s+(\S+)\s+(.*)$")
LOGLINE_RE = re.compile(r"^(\S+)\s+(SKIP|REVIEW|DONE|FAIL)\s+#(\d+)")


def _agent() -> dict:
    """launchctl status: {loaded, pid, last_exit} for the watcher agent."""
    try:
        out = subprocess.run(
            ["launchctl", "list", LABEL], capture_output=True, text=True, timeout=5
        )
    except Exception:
        return {"loaded": False, "pid": None, "last_exit": None}
    if out.returncode != 0:
        return {"loaded": False, "pid": None, "last_exit": None}
    pid = re.search(r'"PID"\s*=\s*(\d+)', out.stdout)
    exit_ = re.search(r'"LastExitStatus"\s*=\s*(\d+)', out.stdout)
    return {
        "loaded": True,
        "pid": int(pid.group(1)) if pid else None,
        "last_exit": int(exit_.group(1)) if exit_ else None,
    }


def _age(ts: str) -> str:
    try:
        when = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        return "?"
    secs = (datetime.now(timezone.utc) - when).total_seconds()
    if secs < 90:
        return f"{int(secs)}s fa"
    if secs < 5400:
        return f"{int(secs // 60)}m fa"
    if secs < 172800:
        return f"{int(secs // 3600)}h fa"
    return f"{int(secs // 86400)}g fa"


def _tail(path: Path, n: int) -> list[str]:
    if not path.exists():
        return []
    # The log grows unbounded; let the system tail read only the last n lines
    # instead of loading the whole file into the UI process every refresh.
    try:
        out = subprocess.run(
            ["tail", "-n", str(n), str(path)],
            capture_output=True, text=True, timeout=5,
        )
        return out.stdout.splitlines()
    except Exception:
        return path.read_text(errors="replace").splitlines()[-n:]


def status() -> dict:
    agent = _agent()
    polling = LOCKDIR.exists()
    log_lines = _tail(LOG, 400)
    last_poll = next(
        (ln.split(" ", 1)[0] for ln in reversed(log_lines) if "poll complete" in ln),
        None,
    )
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    done_today = sum(1 for ln in log_lines if ln[:10] == today and " DONE " in ln)
    fails = [ln for ln in log_lines if " FAIL " in ln][-5:]

    digests = []
    for ln in reversed(_tail(CONTEXT, 40)):
        m = DIGEST_RE.match(ln.strip())
        if m:
            digests.append({"pr": m.group(1), "score": m.group(2), "text": m.group(3)})
        if len(digests) >= 8:
            break

    activity = []
    for ln in reversed(log_lines):
        m = LOGLINE_RE.match(ln)
        if m:
            activity.append(
                {"ts": m.group(1), "kind": m.group(2).upper(), "pr": m.group(3)}
            )
        if len(activity) >= 8:
            break

    try:
        reviewed_count = len(REVIEWED.read_text().split())
    except Exception:
        reviewed_count = 0

    return {
        "loaded": agent["loaded"],
        "pid": agent["pid"],
        "last_exit": agent["last_exit"],
        "polling": polling,
        "last_poll": last_poll,
        "done_today": done_today,
        "reviewed_count": reviewed_count,
        "fails": fails,
        "digests": digests,
        "activity": activity,
    }


def _open(target: str) -> None:
    subprocess.Popen(["open", target])


def _run_env() -> dict:
    env = dict(os.environ)
    env["PATH"] = MENU_PATH
    return env


# --------------------------------------------------------------------------- GUI

def main() -> None:
    import rumps
    from AppKit import NSApplication, NSApplicationActivationPolicyAccessory

    class PRWatch(rumps.App):
        def __init__(self) -> None:
            super().__init__("PR", quit_button=None)
            self.refresh(None)
            rumps.Timer(self.refresh, REFRESH_SECONDS).start()

        # actions -------------------------------------------------------------
        def poll_now(self, _):
            subprocess.Popen(["/bin/bash", str(SCRIPT)], env=_run_env())
            rumps.notification("PR watch", "Poll avviato", "Giro manuale in corso")

        def toggle(self, _):
            loaded = _agent()["loaded"]
            action = "unload" if loaded else "load"
            subprocess.run(["launchctl", action, str(PLIST)], env=_run_env())
            self.refresh(None)

        def open_log(self, _):
            _open(str(LOG))

        def open_state(self, _):
            _open(str(STATE))

        def open_prs(self, _):
            _open(REPO_URL)

        def _open_pr(self, sender):
            pr = getattr(sender, "_pr", None)
            if pr:
                _open(f"https://github.com/Wishew/wishew-monorepo/pull/{pr}")

        def quit(self, _):
            rumps.quit_application()

        # rendering -----------------------------------------------------------
        def refresh(self, _):
            s = status()

            if not s["loaded"]:
                glyph, head = "⏸", "In pausa (agent scaricato)"
            elif s["polling"]:
                glyph, head = "🔄", "Poll in corso…"
            elif s["last_exit"] not in (0, None):
                glyph, head = "⚠️", f"Ultimo exit {s['last_exit']}"
            else:
                glyph, head = "🟢", "Attivo"
            self.title = f"{glyph}{s['done_today']}" if s["done_today"] else glyph

            last = f"ultimo poll {_age(s['last_poll'])}" if s["last_poll"] else "nessun poll ancora"
            self.menu.clear()
            items: list = [
                rumps.MenuItem(f"PR review watcher — {head}"),
                rumps.MenuItem(f"   {last} · {s['done_today']} review oggi · {s['reviewed_count']} totali"),
                rumps.separator,
            ]

            if s["digests"]:
                items.append(rumps.MenuItem("Ultime review"))
                for d in s["digests"]:
                    label = f"   #{d['pr']}  {d['score']}  {d['text'][:60]}"
                    mi = rumps.MenuItem(label, callback=self._open_pr)
                    mi._pr = d["pr"]
                    items.append(mi)
                items.append(rumps.separator)

            if s["activity"]:
                items.append(rumps.MenuItem("Attività recente"))
                for a in s["activity"]:
                    pr = f"#{a['pr']}" if a["pr"] else ""
                    items.append(rumps.MenuItem(f"   {_age(a['ts'])}  {a['kind']} {pr}"))
                items.append(rumps.separator)

            if s["fails"]:
                items.append(rumps.MenuItem(f"⚠️ {len(s['fails'])} fail recenti (vedi log)"))
                items.append(rumps.separator)

            items += [
                rumps.MenuItem("Poll ora", callback=self.poll_now),
                rumps.MenuItem("Riprendi" if not s["loaded"] else "Pausa", callback=self.toggle),
                rumps.separator,
                rumps.MenuItem("Apri log attività", callback=self.open_log),
                rumps.MenuItem("Apri cartella stato", callback=self.open_state),
                rumps.MenuItem("Apri PR su GitHub", callback=self.open_prs),
                rumps.separator,
                rumps.MenuItem("Aggiorna", callback=self.refresh),
                rumps.MenuItem("Esci", callback=self.quit),
            ]
            for it in items:
                self.menu.add(it)

    NSApplication.sharedApplication().setActivationPolicy_(
        NSApplicationActivationPolicyAccessory
    )
    PRWatch().run()


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        print(json.dumps(status(), indent=2, ensure_ascii=False))
    else:
        main()
