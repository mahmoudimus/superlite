"""Workflow markers and compatibility with settings changed by upstream."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from test_plan_tools import SCRIPTS, run

ROOT = SCRIPTS.parents[2]
EX = SCRIPTS / "exclusive.py"
ORCH = SCRIPTS / "orchestrator.py"
HOOK = ROOT / "hooks" / "session-start"
_GIT_BASH = r"C:\Program Files\Git\bin\bash.exe"
BASH = _GIT_BASH if os.name == "nt" and os.path.exists(_GIT_BASH) else shutil.which("bash")
PEER = "superpowers@claude-plugins-official"


def test_finish_restores_upstream_settings_marker(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(ROOT))
    settings = tmp_path / ".claude" / "settings.local.json"
    settings.parent.mkdir()
    settings.write_text(json.dumps({"enabledPlugins": {PEER: False, "other@market": True}, "theme": "dark"}))
    sl = tmp_path / ".superlite"
    sl.mkdir()
    marker = sl / "peers.json"
    legacy = {"suspended": True, "claude_plugin": PEER, "settings_skip": False, "previous_enabled": True}
    marker.write_text(json.dumps(legacy))
    assert run(ORCH, "set", "human", cwd=tmp_path).returncode == 0
    assert json.loads(marker.read_text()) == legacy
    (sl / "progress.md").write_text("# Progress ledger\n", encoding="utf-8")
    done = run(SCRIPTS / "finish.py", "--ledger", sl / "progress.md", "--log", sl / "i.jsonl", cwd=tmp_path)
    assert "peers: clear" in done.out
    assert not marker.is_file()
    restored = json.loads(settings.read_text(encoding="utf-8"))
    assert restored == {"enabledPlugins": {PEER: True, "other@market": True}, "theme": "dark"}


def test_unreadable_settings_are_left_alone(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(ROOT))
    settings = tmp_path / ".claude" / "settings.local.json"
    settings.parent.mkdir()
    settings.write_text("{not json", encoding="utf-8")
    assert run(EX, "on", cwd=tmp_path).returncode == 0
    assert settings.read_text(encoding="utf-8") == "{not json"
    run(EX, "off", cwd=tmp_path)
    assert settings.read_text(encoding="utf-8") == "{not json"


def test_session_start_mentions_the_suspension_only_while_it_holds(tmp_path):
    env = dict(os.environ, CLAUDE_PLUGIN_ROOT=str(ROOT), SUPERLITE_HOME=str(tmp_path / "home"))
    env.pop("COPILOT_CLI", None)
    (tmp_path / "home").mkdir()
    quiet = subprocess.run([BASH, str(HOOK)], cwd=tmp_path, capture_output=True, text=True, encoding="utf-8", env=env)
    assert quiet.returncode == 0
    assert "Use only Superlite lifecycle skills" not in json.loads(quiet.stdout)["hookSpecificOutput"]["additionalContext"]
    sl = tmp_path / ".superlite"
    sl.mkdir()
    (sl / "peers.json").write_text(json.dumps({"suspended": True, "peers": ["superpowers"]}) + "\n", encoding="utf-8")
    loud = subprocess.run([BASH, str(HOOK)], cwd=tmp_path, capture_output=True, text=True, encoding="utf-8", env=env)
    ctx = json.loads(loud.stdout)["hookSpecificOutput"]["additionalContext"]
    assert "Use only Superlite lifecycle skills" in ctx


def test_peers_released_after_last_run(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAUDE_CODE", "1")
    monkeypatch.delenv("CLAUDE_PLUGIN_ROOT", raising=False)
    monkeypatch.delenv("SUPERLITE_NO_AUTO_SESSION", raising=False)
    repo = tmp_path / "app"
    repo.mkdir()
    for cmd in (["init", "-q", "-b", "main"], ["config", "user.email", "t@t"], ["config", "user.name", "t"]):
        subprocess.run(["git", *cmd], cwd=repo, check=True)
    (repo / ".gitignore").write_text(".superlite/\n.claude/\n")
    (repo / "a.txt").write_text("a\n")
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "init"], cwd=repo, check=True)
    session = SCRIPTS / "session.py"
    assert run(session, "ensure", "--slug", "a", cwd=repo).returncode == 0
    assert run(session, "create", "--slug", "b", "--worktree", cwd=repo).returncode == 0
    wt = repo / ".claude" / "worktrees" / "sessions-b"
    run(EX, "on", cwd=repo)
    settings = repo / ".claude" / "settings.local.json"
    assert not settings.exists()
    # the run in the main checkout finishes while b is still open: peers stay off
    held = run(EX, "off", cwd=repo)
    assert "workflow selected" in held.out and "b" in held.out
    assert (repo / ".superlite" / "peers.json").is_file()
    assert not settings.exists()
    # b finishes last: peers are released
    sys.path.insert(0, str(SCRIPTS))
    import session as session_mod
    assert session_mod.mark_run(wt, "finished") == "b"
    done = run(EX, "off", cwd=repo)
    assert "clear" in done.out
    assert not (repo / ".superlite" / "peers.json").is_file()
    assert not settings.is_file()


def test_release_takes_the_registry_lock(tmp_path, monkeypatch):
    sys.path.insert(0, str(SCRIPTS))
    import exclusive
    import session_registry
    seen = []
    real = session_registry.registry_lock

    def spy(root):
        seen.append(root)
        return real(root)
    monkeypatch.setattr(session_registry, "registry_lock", spy)
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    (tmp_path / ".superlite").mkdir()
    exclusive.release(tmp_path / ".superlite")
    assert seen
