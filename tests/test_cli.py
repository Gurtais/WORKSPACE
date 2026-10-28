from workspace_memory.cli import main


def test_cli_status_and_list(tmp_path, monkeypatch):
    import os

    monkeypatch.chdir(tmp_path)
    exit_code = main(["init"])
    assert exit_code == 0

    exit_code = main(["add-note", "Capture launch notes", "--category", "ops", "--tag", "launch", "--tag", "release"])
    assert exit_code == 0

    exit_code = main(["add-task", "Prepare QA checklist", "--category", "planning", "--tag", "qa"])
    assert exit_code == 0

    exit_code = main(["list", "--category", "ops"])
    assert exit_code == 0

    exit_code = main(["categories"])
    assert exit_code == 0
