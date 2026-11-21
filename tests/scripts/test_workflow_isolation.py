"""The host selects plugins. Starting a run changes only run state."""
import json
import os
import subprocess

from test_plan_tools import SCRIPTS, run

ROOT = SCRIPTS.parents[2]


def test_run_preserves_project_plugin_settings(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(ROOT))
    settings = tmp_path / ".claude" / "settings.local.json"
    settings.parent.mkdir()
    original = b'{"enabledPlugins": {"superpowers@claude-plugins-official": true}}\n'
    settings.write_bytes(original)
    assert run(SCRIPTS / "orchestrator.py", "set", "human", cwd=tmp_path).returncode == 0
    assert settings.read_bytes() == original
    assert run(SCRIPTS / "exclusive.py", "off", cwd=tmp_path).returncode == 0
    assert settings.read_bytes() == original


def test_prompt_bridge_requires_a_real_reply_after_the_plan(tmp_path):
    state = tmp_path / ".superlite"
    state.mkdir()
    (state / "orchestrator.json").write_text('{"mode":"human","approved":false}')
    review = tmp_path / "plan.review.md"
    review.write_text("# Review plan\n")
    os.utime(review, (1, 1))
    orch = SCRIPTS / "orchestrator.py"
    assert run(orch, "approve", "--review", review, cwd=tmp_path).returncode == 3

    def submit(prompt):
        subprocess.run(
            ["bash", str(ROOT / "hooks" / "record-reply")],
            cwd=tmp_path,
            input=json.dumps({"cwd": str(tmp_path), "prompt": prompt}),
            text=True,
            check=True,
        )

    submit("Do not approve.")
    refusal = json.loads((state / "human-replies.jsonl").read_text())
    assert refusal["approves"] is False
    submit("Looks good, go ahead.")
    assert run(orch, "approve", "--review", review, cwd=tmp_path).returncode == 0


def test_reply_bridge_does_not_treat_a_codex_subagent_prompt_as_human(tmp_path):
    state = tmp_path / ".superlite"
    state.mkdir()
    (state / "orchestrator.json").write_text('{"mode":"human","approved":false}')
    subprocess.run(
        ["bash", str(ROOT / "hooks" / "record-reply")],
        cwd=tmp_path,
        input=json.dumps({"cwd": str(tmp_path), "prompt": "approve", "agent_id": "child-1"}),
        text=True,
        check=True,
    )
    assert not (state / "human-replies.jsonl").exists()


def test_reply_bridge_stops_at_a_nested_linked_worktree(tmp_path):
    state = tmp_path / ".superlite"
    state.mkdir()
    (state / "orchestrator.json").write_text('{"mode":"human","approved":false}')
    checkout = tmp_path / ".claude/worktrees/other"
    checkout.mkdir(parents=True)
    (checkout / ".git").write_text("gitdir: /test/linked-worktree\n")
    subprocess.run(
        ["bash", str(ROOT / "hooks" / "record-reply")],
        cwd=checkout,
        input=json.dumps({"cwd": str(checkout), "prompt": "approve"}),
        text=True,
        check=True,
    )
    assert not (state / "human-replies.jsonl").exists()
