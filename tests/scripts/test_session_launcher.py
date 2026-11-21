"""Verify native launch arguments without changing a live host's settings."""
import json
import subprocess
import sys

from test_plan_tools import SCRIPTS

ROOT = SCRIPTS.parents[2]
LAUNCH = ROOT / "scripts" / "superlite-session"


def test_codex_overlay_disables_only_other_workflows(tmp_path, monkeypatch):
    monkeypatch.setenv("CODEX_HOME", str(tmp_path))
    config = tmp_path / "config.toml"
    config.write_text(
        '[plugins."superpowers@custom.example"]\nenabled = true\n'
        '[plugins."superlite@superlite-dev"]\nenabled = true\n'
        '[plugins."other@market"]\nenabled = true\n'
    )
    before = config.read_bytes()
    result = subprocess.run([sys.executable, LAUNCH, "codex-config"], text=True, capture_output=True)
    assert result.returncode == 0, result.stderr
    import tomllib

    plugins = tomllib.loads(result.stdout)["plugins"]
    assert plugins["superpowers@custom.example"]["enabled"] is False
    assert plugins["superlite@superlite-dev"]["enabled"] is False
    assert plugins["superlite@superlite-maintained"]["enabled"] is True
    assert "other@market" not in plugins
    assert config.read_bytes() == before


def test_claude_overrides_the_installed_marketplace_id(monkeypatch):
    import importlib.machinery
    import types

    mod = types.ModuleType("superlite_session")
    mod.__file__ = str(LAUNCH)
    importlib.machinery.SourceFileLoader(mod.__name__, str(LAUNCH)).exec_module(mod)
    monkeypatch.setattr(mod, "claude_plugins", lambda: [
        {"id": "superpowers@private-market"}, {"id": "other@market"},
    ])
    args = mod.claude_command(["--model", "sonnet"])
    plugins = json.loads(args[args.index("--settings") + 1])["enabledPlugins"]
    assert plugins == {"superpowers@private-market": False}
    assert args[args.index("--plugin-dir") + 1] == str(ROOT)
    assert args[-2:] == ["--model", "sonnet"]


def test_codex_cli_refuses_a_conflicting_project_plugin_setting(tmp_path, monkeypatch):
    home = tmp_path / "codex"
    home.mkdir()
    (home / "config.toml").write_text('')
    monkeypatch.setenv("CODEX_HOME", str(home))
    checkout = tmp_path / "checkout"
    (checkout / ".codex").mkdir(parents=True)
    (checkout / ".git").mkdir()
    (checkout / ".codex/config.toml").write_text('[plugins."superpowers@project-market"]\nenabled = true\n')
    result = subprocess.run(
        [sys.executable, LAUNCH, "codex", "--help"], text=True, capture_output=True, cwd=checkout,
    )
    assert result.returncode == 1
    assert "superpowers@project-market" in result.stderr


def test_codex_config_includes_competitors_only_in_the_named_profile(tmp_path, monkeypatch):
    monkeypatch.setenv("CODEX_HOME", str(tmp_path))
    (tmp_path / "superlite.config.toml").write_text(
        '[plugins."superpowers@profile-market"]\nenabled = true\n'
        '[plugins."superlite@superlite-maintained"]\nenabled = true\n'
    )
    result = subprocess.run([sys.executable, LAUNCH, "codex-config"], text=True, capture_output=True)
    assert result.returncode == 0, result.stderr
    import tomllib

    assert tomllib.loads(result.stdout)["plugins"]["superpowers@profile-market"]["enabled"] is False
    launch = subprocess.run([sys.executable, LAUNCH, "codex", "--help"], text=True, capture_output=True)
    assert launch.returncode == 1
    assert "superlite.config.toml" in launch.stderr
