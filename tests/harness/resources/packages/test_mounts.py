from __future__ import annotations

import json
from pathlib import Path

import pytest

from loushang.harness.resources.packages.mounts import PackageResourceMount
from loushang.harness.resources.plugins.manifest import PluginManifestParser
from loushang.harness.resources.plugins.revisions import PluginRevisionStore


def test_verified_package_mount_binds_root_digest_lease_and_relative_reads(
    tmp_path: Path,
) -> None:
    source = _plugin(tmp_path / "source")
    published = PluginRevisionStore(tmp_path / "revisions").publish(
        PluginManifestParser().parse(source)
    )
    handle = published.revision_handle
    assert handle is not None

    mount = PackageResourceMount(
        root=published.package_root,
        content_digest=published.content_digest,
        revision_handle=handle,
    )

    assert mount.verified is True
    assert mount.verify() is None
    prompt = published.package_root / "prompts" / "review.md"
    assert mount.read_text(prompt) == "review v1"
    reference = mount.reference(prompt)
    assert reference is not None
    assert reference.content_digest == published.content_digest
    assert reference.relative_path == "resources/prompts/review.md"
    assert reference.kind == "file"


def test_verified_package_mount_rejects_mismatched_digest_and_escape(
    tmp_path: Path,
) -> None:
    source = _plugin(tmp_path / "source")
    published = PluginRevisionStore(tmp_path / "revisions").publish(
        PluginManifestParser().parse(source)
    )
    handle = published.revision_handle
    assert handle is not None

    with pytest.raises(ValueError, match="content digest"):
        PackageResourceMount(
            root=published.package_root,
            content_digest="0" * 64,
            revision_handle=handle,
        )

    mount = PackageResourceMount(
        root=published.package_root,
        content_digest=published.content_digest,
        revision_handle=handle,
    )
    with pytest.raises(ValueError, match="outside Package mount"):
        mount.reference(tmp_path / "outside.md")
    with pytest.raises(ValueError, match="outside Package mount"):
        mount.read_text(tmp_path / "outside.md")
    with pytest.raises(ValueError, match="kind does not match"):
        mount.reference(
            published.package_root / "prompts" / "review.md",
            kind="directory",
        )


def test_path_backed_package_mount_preserves_legacy_read_semantics(
    tmp_path: Path,
) -> None:
    root = tmp_path / "package"
    root.mkdir()
    prompt = root / "review.md"
    prompt.write_text("review", encoding="utf-8")

    mount = PackageResourceMount(root=root)

    assert mount.verified is False
    assert mount.reference(prompt) is None
    assert mount.read_text(prompt) == "review"


@pytest.mark.parametrize("portable", (False, True))
def test_verified_revision_cancellation_preserves_handle_and_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, portable: bool,
) -> None:
    from concurrent.futures import CancelledError

    from loushang.harness.resources.plugins import revisions

    if portable:
        monkeypatch.setattr(revisions, "_supports_descriptor_relative_revision_io", lambda: False)
    source = _plugin(tmp_path / "source")
    published = PluginRevisionStore(tmp_path / "revisions").publish(
        PluginManifestParser().parse(source)
    )
    handle = published.revision_handle
    assert handle is not None
    mount = PackageResourceMount(
        root=published.package_root, content_digest=published.content_digest,
        revision_handle=handle,
    )
    calls = 0

    def stop():
        nonlocal calls
        calls += 1
        if calls == 3:
            raise CancelledError("revision scan cancelled")

    try:
        with pytest.raises(CancelledError, match="revision scan cancelled"):
            mount.verify(work_probe=stop)
        assert calls == 3
        assert handle.closed is False
        mount.verify()
        assert mount.read_text(published.package_root / "prompts" / "review.md") == "review v1"
    finally:
        mount.close()


@pytest.mark.parametrize("portable", (False, True))
def test_verified_revision_cancellation_checks_between_digest_chunks(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, portable: bool,
) -> None:
    from concurrent.futures import CancelledError

    from loushang.harness.resources.plugins import revisions

    if portable:
        monkeypatch.setattr(revisions, "_supports_descriptor_relative_revision_io", lambda: False)
    source = _plugin(tmp_path / "source")
    (source / "resources" / "prompts" / "review.md").write_bytes(b"a" * (256 * 1024))
    published = PluginRevisionStore(tmp_path / "revisions").publish(
        PluginManifestParser().parse(source)
    )
    handle = published.revision_handle
    assert handle is not None
    digest_name = "_digest_file_portable" if portable else "_digest_file"
    original_digest = getattr(revisions, digest_name)
    chunks = 0
    in_digest = False

    def stop():
        nonlocal chunks
        if in_digest:
            chunks += 1
            if chunks == 2:
                raise CancelledError("digest read cancelled")

    def digest(*args, **kwargs):
        name = args[0].name if portable else args[1]
        original_probe = kwargs.get("work_probe")
        if name != "review.md" or original_probe is None:
            return original_digest(*args, **kwargs)

        def probe():
            nonlocal in_digest
            in_digest = True
            try:
                original_probe()
            finally:
                in_digest = False

        return original_digest(*args, **{**kwargs, "work_probe": probe})

    try:
        with monkeypatch.context() as patch:
            patch.setattr(revisions, digest_name, digest)
            with pytest.raises(CancelledError, match="digest read cancelled"):
                handle.verify(work_probe=stop)
        assert chunks == 2
        assert handle.closed is False
        handle.verify()
    finally:
        handle.close()


def _plugin(root: Path) -> Path:
    prompt_root = root / "resources" / "prompts"
    prompt_root.mkdir(parents=True)
    (root / "plugin.json").write_text(
        json.dumps(
            {
                "name": "review-pack",
                "packageRoot": "resources",
            }
        ),
        encoding="utf-8",
    )
    (prompt_root / "review.md").write_text("review v1", encoding="utf-8")
    return root
