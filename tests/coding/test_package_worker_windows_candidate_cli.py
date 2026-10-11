"""The explicit Windows Worker operator entry stays platform gated."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

import loushang.coding.cli.package_worker_windows_candidate as cli


@pytest.mark.parametrize("windows_candidate", (True, False))
def test_windows_worker_candidate_cli_requires_native_platform(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    windows_candidate: bool,
) -> None:
    monkeypatch.setattr(cli, "os", SimpleNamespace(name="posix"))
    args = ["--workspace", str(tmp_path)]
    if windows_candidate:
        args.append("--windows-candidate")
    args.extend(("recover-crash", "--attempt-id", "a" * 32))
    with patch.object(cli, "open_coding_fenced_product_application_owner") as opened:
        assert cli.main(args) == 1
    opened.assert_not_called()
    assert "windows_worker_candidate_platform_closed" in capsys.readouterr().err
    assert tuple(tmp_path.iterdir()) == ()


def test_windows_worker_explicit_operator_command_needs_no_candidate_switch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(cli, "os", SimpleNamespace(name="nt"))
    with (
        patch.object(cli.platform, "machine", return_value="AMD64"),
        patch.object(cli, "resolve_coding_plugin_lifecycle_state_layout") as layout,
        patch.object(
            cli, "_run_product_action", return_value={"workerSelection": "checked"}
        ) as action,
    ):
        assert (
            cli.main(
                (
                    "--workspace",
                    str(tmp_path),
                    "candidate-status",
                    "--plugin-id",
                    "demo",
                )
            )
            == 0
        )
    layout.assert_called_once_with(tmp_path)
    action.assert_called_once()
    assert '"workerSelection": "checked"' in capsys.readouterr().out
