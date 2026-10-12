from __future__ import annotations

import asyncio
from collections.abc import Callable
from pathlib import Path

from loushang.coding.package_product_runtime import (
    CodingFencedProductApplicationSelection,
)
from loushang.coding.session import AgentSession
from loushang.coding.session_manager import (
    SessionManager,
    _bind_owned_session_manager,
    _create_owned_session_factory,
)
from loushang.foundation.json import JSONValue
from loushang.harness.diagnostics.service import DiagnosticsService
from loushang.harness.journal._owned_io import settled_io
from loushang.harness.runtime import copy_file_exclusive
from loushang.harness.session import AgentProductSessionRuntime
from loushang.harness.session.multiagent import compose_multiagent_before_release
from loushang.harness.transcript.session_catalog import (
    session_file_authority_fingerprint,
)

from ..resume_history import CodingResumeHistoryPreview, read_coding_resume_snapshot

SessionFactory = Callable[..., AgentSession]
_copy_import_file = copy_file_exclusive


def _copy_session_import(
    source: Path,
    destination: Path,
    *,
    expected_source_fingerprint: str | None = None,
) -> None:
    if expected_source_fingerprint is None:
        _copy_import_file(source, destination)
    else:
        _copy_import_file(
            source,
            destination,
            expected_source_fingerprint=expected_source_fingerprint,
        )


class AgentSessionRuntime(
    AgentProductSessionRuntime[AgentSession, SessionManager],
):
    """Coding type binding for the shared Agent Product runtime."""

    def __init__(
        self,
        *,
        session_dir: Path,
        session_factory: SessionFactory,
        persist: bool = True,
        materialize_new_transcript: bool = False,
        new_session_header_metadata: dict[str, JSONValue] | None = None,
        current_session: AgentSession | None = None,
        diagnostics_service: DiagnosticsService | None = None,
        auto_refresh_session_index: bool = False,
        session_index_refresh_interval: float = 0.5,
        session_index_flush_delay: float = 0.25,
        owned_transcripts: bool = False,
        store_state_root: Path | None = None,
        enroll_legacy_shared_store: bool = False,
        product_owner_selection: CodingFencedProductApplicationSelection | None = None,
    ) -> None:
        if type(owned_transcripts) is not bool or type(enroll_legacy_shared_store) is not bool:
            raise TypeError("invalid owned transcript activation")
        if type(materialize_new_transcript) is not bool:
            raise TypeError("Coding transcript materialization must be explicit")
        if materialize_new_transcript and not persist:
            raise ValueError("Coding Worker transcript materialization requires persistence")
        if owned_transcripts and current_session is not None:
            raise ValueError("owned runtime must construct its own initial Session")
        if store_state_root is not None and not owned_transcripts:
            raise ValueError("store admission requires owned transcripts")
        if enroll_legacy_shared_store and store_state_root is None:
            raise ValueError("legacy store enrollment requires store admission")
        if product_owner_selection is not None and not isinstance(
            product_owner_selection, CodingFencedProductApplicationSelection
        ):
            raise TypeError("Coding Product owner selection is invalid")
        self._owned_transcript_factory = (
            _create_owned_session_factory(
                store_state_root=store_state_root,
                enroll_legacy_shared_store=enroll_legacy_shared_store,
            ) if owned_transcripts else None
        )
        self._product_owner_selection = product_owner_selection
        self._resume_history_reads: set[asyncio.Task[CodingResumeHistoryPreview]] = set()
        self._resume_history_loop: asyncio.AbstractEventLoop | None = None
        self._resume_history_closed = False
        transcript_type = (
            _bind_owned_session_manager(self._owned_transcript_factory)
            if self._owned_transcript_factory is not None else SessionManager
        )
        super().__init__(
            transcript_session_type=transcript_type,
            session_dir=session_dir,
            session_factory=session_factory,
            persist=persist,
            materialize_new_transcript=materialize_new_transcript,
            new_session_header_metadata=new_session_header_metadata,
            current_session=current_session,
            diagnostics_service=diagnostics_service,
            copy_file=_copy_session_import,
            verified_copy_file=_copy_session_import,
            before_release=compose_multiagent_before_release(
                resolve_runtime=lambda session: getattr(
                    session,
                    "multiagent_runtime",
                    None,
                )
            ),
            auto_refresh_session_index=auto_refresh_session_index,
            session_index_refresh_interval=session_index_refresh_interval,
            session_index_flush_delay=session_index_flush_delay,
        )

    async def preview_resume_history(
        self, session_id: str | Path, *, max_bytes: int = 1024 * 1024,
        selected_leaf_id: str | None = None,
    ) -> CodingResumeHistoryPreview:
        """Observe discovered history without selecting a writable Session.

        The root retains cancelled waiters' native reads until completion. This
        is a data entry, not a lifecycle replacement or execution admission.
        """

        if type(max_bytes) is not int or not 1 <= max_bytes <= 8 * 1024 * 1024:
            raise ValueError("invalid Coding Resume history byte budget")
        if self._resume_history_closed:
            raise RuntimeError("coding_resume_history_closed")
        loop = asyncio.get_running_loop()
        if self._resume_history_loop is None:
            self._resume_history_loop = loop
        elif self._resume_history_loop is not loop:
            raise RuntimeError("coding_resume_history_loop_changed")
        if len(self._resume_history_reads) >= 2:
            raise RuntimeError("coding_resume_history_capacity_exceeded")
        source = self.resolve_discovered_session_source(session_id)

        async def read() -> CodingResumeHistoryPreview:
            return await settled_io(
                read_coding_resume_snapshot, source.path, max_bytes=max_bytes,
                selected_leaf_id=selected_leaf_id,
                expected_source_fingerprint=source.authority_fingerprint,
            )

        work = read()
        try:
            task = asyncio.create_task(work)
        except BaseException:
            work.close()
            raise
        self._resume_history_reads.add(task)

        def settled(completed: asyncio.Task[CodingResumeHistoryPreview]) -> None:
            self._resume_history_reads.discard(completed)
            if not completed.cancelled():
                completed.exception()  # Observe errors after a waiter leaves.

        task.add_done_callback(settled)
        history = await asyncio.shield(task)
        if self._resume_history_closed:
            raise RuntimeError("coding_resume_history_closed")
        if session_file_authority_fingerprint(source.path) != history.source_fingerprint:
            raise ValueError("coding_resume_history_stale")
        return history

    async def _drain_resume_history_reads(self) -> None:
        cancellation: asyncio.CancelledError | None = None
        for task in tuple(self._resume_history_reads):
            while not task.done():
                try:
                    await asyncio.shield(task)
                except asyncio.CancelledError as error:
                    cancellation = error
                except Exception:
                    break  # The read caller or completion callback observes it.
        if cancellation is not None:
            raise cancellation

    async def dispose_session_runtime(
        self,
        *,
        metadata: dict[str, object] | None = None,
    ) -> None:
        from loushang.coding.continuity import shutdown_coding_continuity

        if self._resume_history_reads and self._resume_history_loop is not asyncio.get_running_loop():
            raise RuntimeError("coding_resume_history_loop_changed")
        failure: BaseException | None = None
        self._resume_history_closed = True
        factory = self._owned_transcript_factory
        product_selection = self._product_owner_selection
        if product_selection is not None:
            product_selection.fence()
        if factory is not None:
            factory._on_loop()
            try:
                factory.fence()
            except BaseException as error:
                failure = error
        try:
            await super().dispose_session_runtime(metadata=metadata)
        except BaseException as error:
            if failure is None:
                failure = error
            else:
                failure.add_note(f"Session cleanup retained: {type(error).__name__}")
        try:
            await self._drain_resume_history_reads()
        except BaseException as error:
            if failure is None:
                failure = error
            else:
                failure.add_note(f"history read settlement retained: {type(error).__name__}")
        if factory is not None:
            try:
                await factory.close()
            except BaseException as error:
                if failure is None:
                    failure = error
                else:
                    failure.add_note(f"transcript factory cleanup retained: {type(error).__name__}")
        try:
            await shutdown_coding_continuity(self)
        except BaseException as error:
            if failure is None:
                failure = error
            else:
                failure.add_note(f"continuity cleanup retained: {type(error).__name__}")
        if product_selection is not None:
            try:
                product_selection.close()
            except BaseException as error:
                if failure is None:
                    failure = error
                else:
                    failure.add_note(
                        f"Product owner cleanup retained: {type(error).__name__}"
                    )
        if failure is not None:
            raise failure
