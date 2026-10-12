from __future__ import annotations

import asyncio
import inspect
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, cast

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
from loushang.harness.runtime.session_operations import SessionOperationResult
from loushang.harness.session import AgentProductSessionRuntime
from loushang.harness.session.lifecycle import (
    PreparedSessionLifecycleOperation,
    SessionLifecycleTransition,
)
from loushang.harness.session.multiagent import compose_multiagent_before_release
from loushang.harness.transcript.session_catalog import (
    session_file_authority_fingerprint,
)

from .._resume_cleanup import (
    CodingResumeContinuationCleanupFailure,
    retain_resume_cleanup_failure,
)
from ..resume_history import CodingResumeHistoryPreview, read_coding_resume_snapshot

if TYPE_CHECKING:
    from loushang.ai.model import Model, ModelSelection
    from loushang.ai.types import ImagePart
    from loushang.harness.approval import InteractiveApprovalResolver
    from loushang.harness.policy import PolicyEvaluator

    from ..bootstrap import BootstrapServices
    from ..resume_activation_attempt import CodingActivationAttemptV1
    from ..resume_activation_plan import (
        ActivationOwnerInputRefV1,
        SessionActivationPlanV1,
    )
    from ..resume_continuation import CodingResumePreparedContinuation
    from ..resume_input_lookup import CodingResumeInputLookupQueryV1

SessionFactory = Callable[..., AgentSession]
_copy_import_file = copy_file_exclusive


@dataclass(frozen=True, slots=True)
class CodingRuntimePreparedResume:
    """One original lifecycle operation and its already committed input."""

    _root: AgentSessionRuntime
    _operation: PreparedSessionLifecycleOperation[AgentSession, str]
    continuation: CodingResumePreparedContinuation

    @property
    def consumed(self) -> bool:
        return self._operation.consumed

    async def consume(self) -> SessionOperationResult[AgentSession, str | None]:
        return await self._root._consume_resume_preparation(self)

    async def abort(self) -> None:
        await self._root._abort_resume_preparation(self)


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
        self._resume_activation_tasks: set[asyncio.Task[CodingRuntimePreparedResume]] = set()
        self._resume_delivery_tasks: dict[
            PreparedSessionLifecycleOperation[AgentSession, str],
            asyncio.Task[SessionOperationResult[AgentSession, str | None]],
        ] = {}
        self._resume_prepared_operations: set[PreparedSessionLifecycleOperation[AgentSession, str]] = set()
        self._resume_cleanup_debts: list[CodingResumeContinuationCleanupFailure] = []
        self._resume_activation_loop: asyncio.AbstractEventLoop | None = None
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

    async def prepare_resume_continuation(
        self, *, session_file: str | Path, plan: SessionActivationPlanV1,
        current_owner_inputs: Sequence[ActivationOwnerInputRefV1],
        attempt: CodingActivationAttemptV1, input_record_id: str,
        text: str, created_at: datetime,
        require_current_admission: Callable[[CodingActivationAttemptV1], None],
        require_current_epoch_settlement: Callable[[CodingActivationAttemptV1, Mapping[str, object]], None],
        images: list[ImagePart] | None = None,
        services: BootstrapServices | None = None,
        model: Model | ModelSelection | None = None,
        no_tools: bool | None = None,
        approval_resolver: InteractiveApprovalResolver | None = None,
        tool_policy_evaluator: PolicyEvaluator | None = None,
        observe_input_identity: Callable[[CodingResumeInputLookupQueryV1], None] | None = None,
        worker_candidates: bool = False,
    ) -> CodingRuntimePreparedResume:
        """Retain native Resume preparation until original consume or abort.

        Live actor/policy and effect settlement remain mandatory owner inputs.
        This entry neither dispatches a model nor resubmits the committed input.
        """

        from ..resume_continuation import prepare_coding_resume_continuation

        if self._resume_history_closed:
            raise RuntimeError("coding_resume_root_closed")
        factory = self._owned_transcript_factory
        selection = self._product_owner_selection
        if factory is None or selection is None:
            raise RuntimeError("Coding Resume requires original application Transcript and Product owners")
        loop = asyncio.get_running_loop()
        if self._resume_activation_loop is None:
            self._resume_activation_loop = loop
        elif self._resume_activation_loop is not loop:
            raise RuntimeError("coding_resume_activation_loop_changed")
        self._resume_prepared_operations = {
            operation for operation in self._resume_prepared_operations if not operation.consumed
        }
        if self._resume_activation_tasks or self._resume_prepared_operations or self._resume_cleanup_debts:
            raise RuntimeError("coding_resume_activation_pending")
        if not callable(require_current_admission) or inspect.iscoroutinefunction(require_current_admission):
            raise TypeError("Coding Resume requires synchronous current owner checks")
        previous = self.current_session
        continuation: CodingResumePreparedContinuation | None = None
        operation: PreparedSessionLifecycleOperation[AgentSession, str] | None = None

        def admit(observed: CodingActivationAttemptV1) -> None:
            if self._resume_history_closed:
                raise RuntimeError("coding_resume_root_closed")
            expected = (
                continuation.session if operation is not None and operation.consumed
                and continuation is not None else previous
            )
            if self.current_session is not expected:
                raise RuntimeError("coding_resume_active_session_changed")
            result = cast("Callable[[CodingActivationAttemptV1], object]", require_current_admission)(observed)
            if result is not None:
                if inspect.iscoroutine(result):
                    result.close()
                raise TypeError("Coding Resume owner check must return None")

        async def build(current: AgentSession | None) -> AgentSession:
            nonlocal continuation
            if current is not previous:
                raise RuntimeError("coding_resume_active_session_changed")
            continuation = await prepare_coding_resume_continuation(
                manager_type=_bind_owned_session_manager(factory), session_file=session_file,
                plan=plan, current_owner_inputs=current_owner_inputs, attempt=attempt,
                input_record_id=input_record_id, text=text, created_at=created_at,
                require_current_admission=admit,
                require_current_epoch_settlement=require_current_epoch_settlement,
                images=images, services=services, model=model, no_tools=no_tools,
                approval_resolver=approval_resolver, tool_policy_evaluator=tool_policy_evaluator,
                observe_input_identity=observe_input_identity,
                product_owner_selection=selection, worker_candidates=worker_candidates,
            )
            # Native model transport checks the original Root's actual slot.
            try:
                continuation.session.set_extension_runtime_host(self)
            except BaseException as error:
                try:
                    await continuation.session.dispose()
                except BaseException as cleanup_error:
                    raise retain_resume_cleanup_failure(
                        original_owner=continuation.session, original_error=error,
                        cleanup_error=cleanup_error,
                    ) from error
                raise
            return continuation.session

        async def prepare() -> CodingRuntimePreparedResume:
            nonlocal operation
            try:
                operation = await self.lifecycle._prepare_candidate(
                    SessionLifecycleTransition(
                        reason="resume", target_session_ref=str(session_file),
                        metadata={"activate_extensions": False, "emit_before_transition": False, "schedule_index": False},
                    ), build,
                )
            except CodingResumeContinuationCleanupFailure as debt:
                self._resume_cleanup_debts.append(debt)
                raise
            assert continuation is not None
            self._resume_prepared_operations.add(operation)
            return CodingRuntimePreparedResume(self, operation, continuation)

        task = asyncio.create_task(prepare())
        self._resume_activation_tasks.add(task)
        try:
            return await asyncio.shield(task)
        except asyncio.CancelledError:
            task.cancel()
            # Root keeps the original task until all native cleanup settles.
            while not task.done():
                try:
                    await asyncio.shield(task)
                except asyncio.CancelledError:
                    continue
                except BaseException:
                    break
            if not task.cancelled() and task.exception() is None:
                await task.result().abort()
            raise
        finally:
            self._resume_activation_tasks.discard(task)

    async def _consume_resume_preparation(
        self, prepared: CodingRuntimePreparedResume,
    ) -> SessionOperationResult[AgentSession, str | None]:
        if self._resume_history_closed:
            raise RuntimeError("coding_resume_root_closed")
        operation = prepared._operation
        if prepared._root is not self or operation not in self._resume_prepared_operations:
            raise RuntimeError("coding_resume_preparation_not_owned")
        if operation in self._resume_delivery_tasks:
            raise RuntimeError("coding_resume_delivery_pending")
        task = asyncio.create_task(operation.consume())
        self._resume_delivery_tasks[operation] = task
        try:
            return await asyncio.shield(task)
        except asyncio.CancelledError:
            task.cancel()
            await self._settle_cancelled_resume_task(task)
            raise
        finally:
            self._resume_delivery_tasks.pop(operation, None)

    @staticmethod
    async def _settle_cancelled_resume_task(task: asyncio.Task[object]) -> None:
        while not task.done():
            try:
                await asyncio.shield(task)
            except asyncio.CancelledError:
                continue
            except BaseException:
                break
        if not task.cancelled():
            task.exception()

    async def _abort_resume_preparation(self, prepared: CodingRuntimePreparedResume) -> None:
        if prepared._root is not self:
            raise RuntimeError("coding_resume_preparation_not_owned")
        operation = prepared._operation
        task = self._resume_delivery_tasks.get(operation)
        if task is not None:
            task.cancel()
            await self._settle_cancelled_resume_task(task)
        await operation.abort()
        self._resume_prepared_operations.discard(operation)

    async def _drain_resume_activations(self) -> None:
        if self._resume_activation_loop is not None and self._resume_activation_loop is not asyncio.get_running_loop():
            raise RuntimeError("coding_resume_activation_loop_changed")
        tasks = tuple(self._resume_activation_tasks)
        deliveries = tuple(self._resume_delivery_tasks.items())
        for task in tasks:
            task.cancel()
        for _, delivery in deliveries:
            delivery.cancel()
        for task in tasks:
            try:
                await asyncio.shield(task)
            except asyncio.CancelledError:
                if not task.done():
                    raise
            except Exception:
                pass  # Preparation caller and retained debt own the failure.
            self._resume_activation_tasks.discard(task)
        for operation, delivery in deliveries:
            await self._settle_cancelled_resume_task(delivery)
            self._resume_delivery_tasks.pop(operation, None)
        for operation in tuple(self._resume_prepared_operations):
            await operation.abort()  # Native operation retains failed aborts for retry.
            self._resume_prepared_operations.discard(operation)
        for debt in tuple(self._resume_cleanup_debts):
            await debt.retry_cleanup()
            self._resume_cleanup_debts.remove(debt)

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
        # Preparation holds the native transition lock. Settle it and original
        # undelivered candidates before closing their dependent owner factories.
        await self._drain_resume_activations()
        try:
            await super().dispose_session_runtime(metadata=metadata)
        except BaseException as error:
            if failure is None:
                failure = error
            else:
                failure.add_note(f"Session cleanup retained: {type(error).__name__}")
            # The original lifecycle/construction owner retains failed Session
            # retirement. Its dependent factories must wait for that retry.
            raise failure
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
