"""Real Coding AgentSession binding behind the product-neutral hosted port."""

from __future__ import annotations

import asyncio
import hashlib
import inspect
import json
import sys
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from secrets import token_hex
from typing import cast

from loushang.agent.types import StreamFn
from loushang.ai.model import Model, ModelSelection
from loushang.ai.types import AssistantMessage, UserMessage
from loushang.apphost import SessionBindingKeyV1
from loushang.appserver.protocol import (
    AppErrorCodeV1,
    AppServiceError,
    SessionEventKindV1,
    SessionIdentityV1,
    SessionSnapshotRequestV1,
    TranscriptRecordKindV1,
    TranscriptRecordV1,
)
from loushang.appserver.resume_model import (
    ResumeInputLookupQueryV1,
    ResumeInputLookupResultV1,
)
from loushang.appservice.client_scope import AppClientScopeV1
from loushang.appservice.execution_contract import (
    ExecutionOutcomeV1,
    ExecutionStatusV1,
)
from loushang.appservice.execution_guard import ExecutionControlV1, ExecutionWorkV1
from loushang.harness.approval import (
    ApprovalOutcome,
    DenyApprovalResolver,
    InteractiveApprovalResolver,
)
from loushang.harness.events import RuntimeEvent
from loushang.harness.events.runtime_projection import project_session_runtime_event
from loushang.harness.package_product.product_runtime import (
    PackageProductRuntimeFactoryPort,
)
from loushang.harness.session import SessionControlPort
from loushang.harness.tools.core import ToolDefinition
from loushang.harness.tools.workspace import workspace_tool_runtime_settings
from loushang.harness.workspace.exec.capture_lease import ExecCaptureFactory

from .appservice_adapter import (
    CodingHostedEventProjectionV1,
    CodingHostedSessionBindingV1,
    CodingHostedSnapshotProjectionV1,
)
from .bootstrap import BootstrapServices, create_agent_session
from .composition_sets import resolve_coding_composition_set
from .hosted_catalog import (
    CodingHostedCandidateBindingV1,
    CodingHostedCatalogError,
    CodingHostedHistoryCandidateBindingV1,
    CodingHostedResumeSourceV1,
)
from .package_product_runtime import (
    CodingFencedProductApplicationSelection,
)
from .resume_history import CodingResumeHistoryPreview
from .resume_input_lookup import (
    CodingResumeInputLookupQueryV1,
    CodingResumeInputLookupResultV1,
)
from .resume_permission_confirmation import NativeResumePolicy
from .runtime.resume_planning import ResumePlanningSlot
from .session.agent_session import AgentSession
from .session_manager import SessionManager

_TEXT_LIMIT = 16_384
_MAX_INTERACTIONS = 16
CodingHostedProductRuntimeFactoryForSession = Callable[
    [SessionManager], PackageProductRuntimeFactoryPort
]


class CodingHostedHistoryBindingV1:
    """Detached historical display with no Writer or execution control.

    The catalog admits identity and the source revision before constructing this
    binding. AppService still owns caller read authorization. A display snapshot
    cannot be promoted into a current runtime or used as activation evidence.
    """

    def __init__(
        self, identity: SessionIdentityV1, history: CodingResumeHistoryPreview,
    ) -> None:
        if (
            type(identity) is not SessionIdentityV1
            or identity.product_id != "coding"
            or type(history) is not CodingResumeHistoryPreview
            or identity.session_id != history.header_preview.header.conversation_id
        ):
            raise CodingHostedCatalogError()
        self.identity = identity
        self._history = history
        self._closed = False
        records: list[TranscriptRecordV1] = []
        remaining = _TEXT_LIMIT
        omitted = False
        for entry in reversed(history.selected_records):
            record = _message_record(entry.payload)
            if record is None:
                continue
            if len(records) >= 128 or len(record.text) > remaining:
                omitted = True
                break
            records.append(record)
            remaining -= len(record.text)
        records.reverse()
        if omitted:
            records.insert(0, TranscriptRecordV1(
                TranscriptRecordKindV1.STATUS,
                "Earlier messages omitted from this bounded snapshot; the canonical transcript is unchanged.",
            ))
        records.append(TranscriptRecordV1(
            TranscriptRecordKindV1.STATUS,
            "Historical session is read-only; continuing requires current runtime activation.",
        ))
        self._projection = CodingHostedSnapshotProjectionV1(
            title="Coding", revision=0, running=False, records=tuple(records),
            truncated=omitted,
        )

    @property
    def control(self) -> None:
        return None

    @property
    def resume_history(self) -> CodingResumeHistoryPreview:
        if self._closed:
            raise RuntimeError("coding_hosted_session_closed")
        return self._history

    def project_snapshot(self) -> CodingHostedSnapshotProjectionV1:
        if self._closed:
            raise RuntimeError("coding_hosted_session_closed")
        return self._projection

    def project_event(
        self, event: RuntimeEvent[object],
    ) -> CodingHostedEventProjectionV1 | None:
        return None

    async def respond_interaction(self, interaction_id: str, outcome: str) -> bool:
        return False

    async def close(self) -> None:
        self._closed = True


class CodingRealHostedSessionV1:
    def __init__(
        self,
        session: AgentSession,
        identity: SessionIdentityV1,
        approval: InteractiveApprovalResolver,
    ) -> None:
        self._session = session
        self.identity = identity
        self._approval = approval
        self._interactions: dict[str, str] = {}
        self._interrupted = False
        self._revision = 0
        self._close_task: asyncio.Task[None] | None = None
        session.set_approval_presenter(
            self._present_approval, dismisser=self._dismiss_approval
        )

    @property
    def control(self) -> SessionControlPort:
        return self._session

    async def lookup_resume_input(
        self, query: CodingResumeInputLookupQueryV1,
    ) -> CodingResumeInputLookupResultV1:
        """Product observation for an already read-authorized Hosted caller.

        This internal port does not negotiate a new client protocol, authorize
        reads, or infer model outcome from durable message presence.
        """

        if self._close_task is not None:
            raise CodingHostedCatalogError()
        manager = self._session.session_manager
        if not isinstance(manager, SessionManager) or manager.header.conversation_id != self.identity.session_id:
            raise CodingHostedCatalogError()
        return await manager.lookup_resume_input(query)

    def project_snapshot(self) -> CodingHostedSnapshotProjectionV1:
        records: list[TranscriptRecordV1] = []
        remaining = _TEXT_LIMIT
        omitted = False
        truncated = False
        for message in reversed(self._session.messages):
            record = _message_record(message)
            if record is None:
                continue
            if len(records) >= 128 or len(record.text) > remaining:
                omitted = True
                break
            records.append(record)
            truncated |= len(_message_text(message)) > _TEXT_LIMIT
            remaining -= len(record.text)
        records.reverse()
        if omitted:
            records.insert(
                0,
                TranscriptRecordV1(
                    TranscriptRecordKindV1.STATUS,
                    "Earlier messages omitted from this bounded snapshot; the canonical transcript is unchanged.",
                ),
            )
        return CodingHostedSnapshotProjectionV1(
            title=_bounded(
                (self._session.session_name or "").strip() or "Coding", limit=256
            ),
            revision=self._revision,
            running=self._session.is_streaming,
            records=tuple(records),
            truncated=omitted or truncated,
        )

    def project_event(
        self, event: RuntimeEvent[object]
    ) -> CodingHostedEventProjectionV1 | None:
        self._revision += 1
        payload = project_session_runtime_event(event)
        if payload is None:
            return None
        kind = payload.get("type")
        if kind == "agent_start":
            self._interrupted = False
            return CodingHostedEventProjectionV1(SessionEventKindV1.TURN_STARTED)
        if kind == "agent_end":
            return CodingHostedEventProjectionV1(
                SessionEventKindV1.TURN_INTERRUPTED
                if self._interrupted
                else SessionEventKindV1.TURN_COMPLETED
            )
        if kind == "message_end":
            message = payload.get("message")
            if (
                isinstance(message, AssistantMessage)
                and message.stop_reason == "aborted"
            ):
                self._interrupted = True
            record = _message_record(message)
            if record is not None:
                return CodingHostedEventProjectionV1(
                    SessionEventKindV1.USER_MESSAGE
                    if record.kind is TranscriptRecordKindV1.USER
                    else SessionEventKindV1.ASSISTANT_MESSAGE,
                    record.text,
                )
        if kind == "message_update":
            update = payload.get("assistant_message_event")
            if isinstance(update, Mapping) and update.get("type") == "text_delta":
                delta = update.get("delta")
                if isinstance(delta, str):
                    return CodingHostedEventProjectionV1(
                        SessionEventKindV1.ASSISTANT_DELTA,
                        _bounded(delta),
                        truncated=len(delta) > _TEXT_LIMIT,
                    )
        if payload.get("hosted_presentation") is True and kind in {
            "tool_approval_requested",
            "tool_approval_resolved",
        }:
            return CodingHostedEventProjectionV1(
                SessionEventKindV1.INTERACTION_REQUESTED
                if kind == "tool_approval_requested"
                else SessionEventKindV1.INTERACTION_DISMISSED,
                cast(str | None, payload.get("text")),
                cast(str, payload["interaction_id"]),
            )
        return None

    async def _present_approval(self, request: dict[str, object]) -> None:
        action_id = request.get("action_id")
        if (
            not isinstance(action_id, str)
            or len(self._interactions) >= _MAX_INTERACTIONS
        ):
            raise RuntimeError("hosted_approval_unavailable")
        # Publish only once the existing ApprovalBroker has registered its waiter.
        text = "\n".join(
            (
                str(request.get("action", "Tool approval")),
                str(request.get("risk", "")),
                json.dumps(
                    request.get("arguments", {}), ensure_ascii=False, sort_keys=True
                ),
            )
        )
        if len(text) > _TEXT_LIMIT:
            raise RuntimeError("hosted_approval_too_large")
        interaction_id = token_hex(16)
        self._interactions[interaction_id] = action_id
        try:
            await self._session.runtime.dispatch_event(
                {
                    "type": "tool_approval_requested",
                    "hosted_presentation": True,
                    "interaction_id": interaction_id,
                    "text": text,
                }
            )
        except BaseException:
            self._interactions.pop(interaction_id, None)
            raise

    async def _dismiss_approval(self, action_id: str) -> None:
        for interaction_id, pending in tuple(self._interactions.items()):
            if pending == action_id:
                self._interactions.pop(interaction_id, None)
                await self._session.runtime.dispatch_event(
                    {
                        "type": "tool_approval_resolved",
                        "hosted_presentation": True,
                        "interaction_id": interaction_id,
                    }
                )

    async def respond_interaction(self, interaction_id: str, outcome: str) -> bool:
        action_id = self._interactions.get(interaction_id)
        if action_id is None or outcome not in {"allow_once", "deny", "abort"}:
            return False
        return await self._session.handle_screen_approval(
            {
                "action_id": action_id,
                "outcome": outcome,
            }
        )

    async def close(self) -> None:
        task = self._close_task
        if task is None or (
            task.done() and (task.cancelled() or task.exception() is not None)
        ):
            task = asyncio.create_task(self._close_once())
            task.add_done_callback(_observe_close)
            self._close_task = task
        await asyncio.shield(task)

    async def _close_once(self) -> None:
        self._approval.end_session()
        await self._session.dispose()
        self._interactions.clear()

    @property
    def execution_available(self) -> bool:
        return self._session.execution_available

    def create_execution_work(
        self, text: str, cancel_requested: Callable[[], bool],
    ) -> ExecutionWorkV1:
        from ._hosted_execution_work import CodingExecutionWorkV1

        return CodingExecutionWorkV1(self._session, text, cancel_requested)


class _DeferredHostedControlV1:
    """Stable control identity that later relays the activated Session."""

    def __init__(self, session_id: str) -> None:
        self._session_id = session_id
        self._delegate: SessionControlPort | None = None
        self._listeners: set[Callable[[RuntimeEvent[object]], object]] = set()
        self._unsubscribe: Callable[[], None] | None = None
        self._closed = False

    @property
    def session_id(self) -> str:
        return self._session_id

    @property
    def session_name(self) -> str | None:
        return None if self._delegate is None else self._delegate.session_name

    async def set_session_name(self, name: str | None) -> None:
        await self._require_active().set_session_name(name)

    def subscribe_runtime_events(
        self, listener: Callable[[RuntimeEvent[object]], object],
    ) -> Callable[[], None]:
        if self._closed or not callable(listener):
            raise RuntimeError("coding_hosted_session_closed")
        self._listeners.add(listener)
        return lambda: self._listeners.discard(listener)

    async def emit(self, event: RuntimeEvent[object]) -> None:
        for listener in tuple(self._listeners):
            try:
                result = listener(event)
                if inspect.isawaitable(result):
                    await result
            except Exception:
                self._listeners.discard(listener)

    def activate(self, control: SessionControlPort) -> None:
        if self._closed or self._delegate is not None:
            raise CodingHostedCatalogError()
        if control.session_id != self._session_id:
            raise CodingHostedCatalogError()

        async def relay(event: RuntimeEvent[object]) -> None:
            await self.emit(event)

        unsubscribe = control.subscribe_runtime_events(relay)
        if not callable(unsubscribe):
            raise CodingHostedCatalogError()
        self._delegate = control
        self._unsubscribe = unsubscribe

    async def prompt(self, user_input: str, images=None, **kwargs) -> None:
        await self._require_active().prompt(user_input, images=images, **kwargs)

    def steer(self, user_input: str, images=None) -> None:
        self._require_active().steer(user_input, images=images)

    def follow_up(self, user_input: str, images=None) -> None:
        self._require_active().follow_up(user_input, images=images)

    async def wait_for_idle(self) -> None:
        await self._require_active().wait_for_idle()

    def abort(self) -> bool:
        return False if self._delegate is None else self._delegate.abort()

    def close(self) -> None:
        self._closed = True
        if self._unsubscribe is not None:
            self._unsubscribe()
            self._unsubscribe = None
        self._listeners.clear()

    def _require_active(self) -> SessionControlPort:
        if self._closed:
            raise RuntimeError("coding_hosted_session_closed")
        if self._delegate is None:
            raise AppServiceError(AppErrorCodeV1.OPERATION_UNAVAILABLE)
        return self._delegate


class CodingDeferredHostedSessionV1:
    """One AppHost binding from detached history through first activation."""

    def __init__(
        self,
        source: CodingHostedResumeSourceV1,
        *,
        services: BootstrapServices,
        model: Model | ModelSelection | None,
        stream_fn: StreamFn | None,
        tools: list[ToolDefinition] | None,
        output_capture_factory: ExecCaptureFactory | None,
        product_owner_selection: CodingFencedProductApplicationSelection,
    ) -> None:
        self._source = source
        self.identity = source.record.identity
        self._services = services
        self._model = model
        self._stream_fn = stream_fn
        self._tools = tools
        self._output_capture_factory = output_capture_factory
        self._product_owner_selection = product_owner_selection
        self._approval = InteractiveApprovalResolver(fallback=DenyApprovalResolver())
        self._approval.open_session()
        self._approval.set_request_presenter(
            self._present_approval, dismisser=self._dismiss_approval
        )
        self._control = _DeferredHostedControlV1(self.identity.session_id)
        self._active: CodingRealHostedSessionV1 | None = None
        self._planning: ResumePlanningSlot | None = None
        self._activation_lock = asyncio.Lock()
        self._close_task: asyncio.Task[None] | None = None
        self._interactions: dict[str, str] = {}
        self._latest_input_query: CodingResumeInputLookupQueryV1 | None = None

    @property
    def control(self) -> SessionControlPort:
        return cast(SessionControlPort, self._control)

    @property
    def execution_available(self) -> bool:
        return self._close_task is None

    async def start_background_planning(self) -> None:
        from loushang.harness.tools.workspace import workspace_tool_runtime_settings

        self._source.require_current_source()
        policy = workspace_tool_runtime_settings(self._services.settings_manager)
        raw_policy_engine = policy.policy_engine
        if raw_policy_engine is None:
            raise CodingHostedCatalogError()
        policy_engine = cast(NativeResumePolicy, raw_policy_engine)
        digest = hashlib.sha256(
            (
                "coding.hosted.resume-plan/v1\0"
                + self.identity.continuity_id
                + "\0"
                + self.identity.session_id
                + "\0"
                + self._source.record.projection.reference.revision
            ).encode()
        ).hexdigest()
        planning = ResumePlanningSlot()
        self._planning = planning
        await planning.start(
            self._source.history,
            resolve_coding_composition_set("coding-standard"),
            workspace_root=self._source.record.scope.cwd,
            resource_loader=self._services.resource_loader,
            subject_digest=digest,
            policy_digest=policy_engine.configuration_fingerprint(),
            max_work_units=200,
            time_budget_seconds=5.0,
        )

    def create_execution_work(
        self, text: str, cancel_requested: Callable[[], bool],
    ) -> ExecutionWorkV1:
        from ._hosted_execution_work import (
            CodingExecutionWorkV1,
            current_coding_hosted_resume_subject,
            current_coding_hosted_resume_submission_id,
        )

        if self._active is not None:
            return CodingExecutionWorkV1(
                cast(AgentSession, self._active.control), text, cancel_requested
            )
        scope, control, subject_digest = current_coding_hosted_resume_subject()
        submission_id = current_coding_hosted_resume_submission_id()
        if submission_id is None:
            raise AppServiceError(AppErrorCodeV1.OPERATION_UNAVAILABLE)
        return _HostedResumeExecutionWorkV1(
            self, text, cancel_requested, scope, control, subject_digest,
            submission_id,
        )

    def project_snapshot(self) -> CodingHostedSnapshotProjectionV1:
        if self._close_task is not None:
            raise CodingHostedCatalogError()
        active = self._active
        return (
            active.project_snapshot()
            if active is not None
            else self._source.history_binding.project_snapshot()
        )

    def project_event(
        self, event: RuntimeEvent[object],
    ) -> CodingHostedEventProjectionV1 | None:
        active = self._active
        if active is not None:
            return active.project_event(event)
        payload = event if isinstance(event, Mapping) else None
        if payload is not None and payload.get("hosted_presentation") is True:
            kind = payload.get("type")
            if kind in {"tool_approval_requested", "tool_approval_resolved"}:
                return CodingHostedEventProjectionV1(
                    SessionEventKindV1.INTERACTION_REQUESTED
                    if kind == "tool_approval_requested"
                    else SessionEventKindV1.INTERACTION_DISMISSED,
                    cast(str | None, payload.get("text")),
                    cast(str, payload["interaction_id"]),
                )
        return None

    async def lookup_resume_input(
        self, query: CodingResumeInputLookupQueryV1,
    ) -> CodingResumeInputLookupResultV1:
        active = self._active
        if active is not None:
            return await active.lookup_resume_input(query)
        from .resume_activation_projection_v2 import (
            project_coding_activation_attempt_path_v2,
        )
        from .resume_input_lookup import coding_resume_input_record_digest

        try:
            records = self._source.history.selected_records
            projection = project_coding_activation_attempt_path_v2(
                records, current_session_id=self.identity.session_id
            )
            binding = projection.binding
            if (
                projection.binding_status == "bound"
                and binding is not None
                and binding.input_id == query.input_id
                and projection.binding_record_id is not None
            ):
                candidates = tuple(
                    record
                    for record in records
                    if record.record_id == projection.binding_record_id
                )
                if len(candidates) != 1:
                    return CodingResumeInputLookupResultV1(
                        query.input_id, None, "unknown"
                    )
                if coding_resume_input_record_digest(candidates[0]) != query.record_digest:
                    return CodingResumeInputLookupResultV1(
                        query.input_id, None, "conflict"
                    )
                return CodingResumeInputLookupResultV1(
                    query.input_id, candidates[0].record_id, "committed"
                )
        except ValueError:
            return CodingResumeInputLookupResultV1(query.input_id, None, "unknown")
        retained = self._latest_input_query
        if retained is not None and retained.input_id == query.input_id:
            return CodingResumeInputLookupResultV1(
                query.input_id,
                None,
                "unknown" if retained == query else "conflict",
            )
        return CodingResumeInputLookupResultV1(query.input_id, None, "unknown")

    async def respond_interaction(self, interaction_id: str, outcome: str) -> bool:
        active = self._active
        if active is not None:
            return await active.respond_interaction(interaction_id, outcome)
        action_id = self._interactions.get(interaction_id)
        mapped = cast(
            ApprovalOutcome | None,
            outcome if outcome in {"allow_once", "deny", "abort"} else None,
        )
        if action_id is None or mapped is None:
            return False
        return await self._approval.handle_result(action_id, outcome=mapped)

    async def _present_approval(self, request: dict[str, object]) -> None:
        action_id = request.get("action_id")
        if not isinstance(action_id, str) or len(self._interactions) >= _MAX_INTERACTIONS:
            raise RuntimeError("hosted_approval_unavailable")
        text = "\n".join((
            str(request.get("action", "Resume approval")),
            str(request.get("risk", "")),
            json.dumps(request.get("arguments", {}), ensure_ascii=False, sort_keys=True),
        ))
        if len(text) > _TEXT_LIMIT:
            raise RuntimeError("hosted_approval_too_large")
        interaction_id = token_hex(16)
        self._interactions[interaction_id] = action_id
        await self._control.emit(cast(RuntimeEvent[object], {
            "type": "tool_approval_requested",
            "hosted_presentation": True,
            "interaction_id": interaction_id,
            "text": text,
        }))

    async def _dismiss_approval(self, action_id: str) -> None:
        for interaction_id, pending in tuple(self._interactions.items()):
            if pending == action_id:
                self._interactions.pop(interaction_id, None)
                await self._control.emit(cast(RuntimeEvent[object], {
                    "type": "tool_approval_resolved",
                    "hosted_presentation": True,
                    "interaction_id": interaction_id,
                }))

    async def activate(
        self,
        text: str,
        *,
        scope: AppClientScopeV1,
        subject_control: SessionSnapshotRequestV1,
        subject_digest: str,
        submission_id: str,
    ) -> _ActivatedHostedResumeV1:
        from loushang.harness.tools.workspace import workspace_tool_runtime_settings

        from ._capability_plugin_composition import (
            prepare_coding_resume_plugin_effect_owners,
            require_coding_resume_plugin_effect_settlement,
        )
        from ._product_capability_plugin_composition import (
            prepare_coding_product_approval_state_root,
        )
        from .embedded_resume import (
            _capability_plugins_enabled,
            _require_no_capability_plugin_effects,
        )
        from .resume_activation_attempt import (
            CodingActivationAttemptV1,
            CodingResumeRecoveryRequired,
        )
        from .resume_activation_attempt_v2 import CodingActivationAttemptV2
        from .resume_activation_plan import plan_coding_resume_async
        from .resume_continuation import prepare_coding_resume_continuation
        from .resume_permission_confirmation import (
            CodingResumePermissionConfirmation,
            coding_resume_permission_request,
        )
        from .sandbox import coding_workspace_execution_profile

        async with self._activation_lock:
            if self._close_task is not None:
                raise CodingHostedCatalogError()
            if self._active is not None:
                raise CodingHostedCatalogError()

            def require_subject() -> None:
                scope.require_current_resume_subject(
                    subject_control,
                    subject_digest,
                    expected_session_id=plan.session_id,
                )

            self._source.require_current_source()
            policy = workspace_tool_runtime_settings(self._services.settings_manager)
            raw_policy_engine = policy.policy_engine
            if raw_policy_engine is None:
                raise CodingHostedCatalogError()
            policy_engine = cast(NativeResumePolicy, raw_policy_engine)
            plan_subject_digest = hashlib.sha256(
                (
                    "coding.hosted.resume-plan/v1\0"
                    + self.identity.continuity_id
                    + "\0"
                    + self.identity.session_id
                    + "\0"
                    + self._source.record.projection.reference.revision
                ).encode()
            ).hexdigest()
            plan = await plan_coding_resume_async(
                self._source.history,
                resolve_coding_composition_set("coding-standard"),
                workspace_root=self._source.record.scope.cwd,
                resource_loader=self._services.resource_loader,
                subject_digest=plan_subject_digest,
                policy_digest=policy_engine.configuration_fingerprint(),
                max_work_units=200,
                time_budget_seconds=5.0,
                priority="foreground",
            )
            if self._planning is not None:
                plan = self._planning.current(
                    self._source.history, current_owner_inputs=plan.owner_inputs
                ) or plan
            if plan.status != "needs_final_validation" or plan.ancestry_digest is None:
                raise CodingResumeRecoveryRequired("input.plan_unavailable")
            self._source.require_current_source()
            if self._planning is not None:
                await self._planning.close()
                self._planning = None
            workspace = Path(plan.workspace_root)

            require_subject()
            epoch_fingerprint = self._product_owner_selection.prepare_resume_epoch(
                workspace,
                require_current_admission=require_subject,
                settings_manager=self._services.settings_manager,
            )
            require_subject()
            plugins_enabled = _capability_plugins_enabled(
                plan_set_id=plan.composition_comparison.candidate_set_id,
                settings_manager=self._services.settings_manager,
                no_tools=None,
            )
            state_id = hashlib.sha256(
                b"loushang.coding-capability-plugin-state/v1\0"
                + plan.session_id.encode()
            ).hexdigest()
            plugin_state_root = (
                self._source.record.scope.session_dir
                / "plugin-state"
                / "coding-capability-plugins"
                / state_id
            )
            plugin_owners = (
                prepare_coding_resume_plugin_effect_owners(
                    session_id=plan.session_id, state_root=plugin_state_root
                )
                if plugins_enabled
                else ()
            )
            stable = hashlib.sha256(
                (
                    self.identity.continuity_id
                    + "\0"
                    + self.identity.session_id
                    + "\0"
                    + submission_id
                ).encode()
            ).hexdigest()
            attempt: CodingActivationAttemptV1 = CodingActivationAttemptV2(
                attempt_id=f"resume-attempt:{token_hex(16)}",
                request_id=f"resume-input:{stable}",
                session_id=plan.session_id,
                original_leaf_id=plan.selected_leaf_id,
                ancestry_digest=plan.ancestry_digest,
                plan_fingerprint=plan.plan_id,
                epoch_fingerprint=epoch_fingerprint,
                subject_digest=subject_digest,
                effect_owners=tuple(sorted(plugin_owners, key=lambda owner: owner.identity)),
            )
            execution_profile = coding_workspace_execution_profile(workspace, writable=True)
            confirmation = await self._approval.confirm(
                coding_resume_permission_request(
                    attempt,
                    actor_id="hosted-controller",
                    expansion_codes=("authority.unknown",),
                    execution_profile=execution_profile,
                    policy_evaluator=cast("NativeResumePolicy", policy_engine),
                    hosted_subject_scope=scope,
                    hosted_subject_control=subject_control,
                )
            )
            if confirmation is None:
                raise PermissionError("Coding Hosted Resume permission was not confirmed")
            permission = CodingResumePermissionConfirmation(
                attempt,
                "hosted-controller",
                ("authority.unknown",),
                self._approval,
                confirmation,
                execution_profile=execution_profile,
                policy_evaluator=cast("NativeResumePolicy", policy_engine),
                hosted_subject_scope=scope,
                hosted_subject_control=subject_control,
            )

            def current_policy() -> NativeResumePolicy:
                current = workspace_tool_runtime_settings(
                    self._services.settings_manager
                ).policy_engine
                if current is None:
                    raise CodingHostedCatalogError()
                return cast(NativeResumePolicy, current)

            def admit(observed: CodingActivationAttemptV1) -> None:
                if type(observed) is not CodingActivationAttemptV2:
                    raise CodingResumeRecoveryRequired(
                        "input.effect_owner_set_unsupported"
                    )
                permission.require_current(
                    observed,
                    current_execution_profile=coding_workspace_execution_profile(
                        workspace, writable=True
                    ),
                    current_policy_evaluator=current_policy(),
                )
                if self._close_task is not None:
                    raise CodingHostedCatalogError()

            def settle(
                observed: CodingActivationAttemptV1, receipt: Mapping[str, object]
            ) -> None:
                if type(observed) is not CodingActivationAttemptV2:
                    raise CodingResumeRecoveryRequired(
                        "input.effect_owner_set_unsupported"
                    )
                if plugin_owners:
                    require_coding_resume_plugin_effect_settlement(
                        observed,
                        receipt,
                        state_root=prepare_coding_product_approval_state_root(
                            plugin_state_root
                        ),
                        clock=lambda: time.time_ns() // 1_000_000,
                    )
                else:
                    _require_no_capability_plugin_effects(
                        observed,
                        receipt,
                        expected_set_id=plan.composition_comparison.candidate_set_id,
                    )

            try:
                continuation = await prepare_coding_resume_continuation(
                    manager_type=self._source.manager_type,
                    session_file=self._source.record.path,
                    plan=plan,
                    current_owner_inputs=plan.owner_inputs,
                    attempt=attempt,
                    input_record_id=f"resume-record:{stable}",
                    text=text,
                    created_at=datetime.now(UTC),
                    require_current_admission=admit,
                    require_current_epoch_settlement=settle,
                    services=self._services,
                    model=self._model,
                    stream_fn=self._stream_fn,
                    tools=self._tools,
                    output_capture_factory=self._output_capture_factory,
                    approval_resolver=self._approval,
                    tool_policy_evaluator=policy_engine,
                    observe_input_identity=self._observe_input_identity,
                    product_owner_selection=self._product_owner_selection,
                    resume_writer_factory=self._source.writer_factory,
                )
            except BaseException:
                self._approval.release_confirmation(confirmation)
                raise
            try:
                await self._source.close()
            except BaseException:
                await continuation.session.dispose()
                raise
            try:
                real = CodingRealHostedSessionV1(
                    continuation.session, self.identity, self._approval
                )
                self._control.activate(real.control)
                self._active = real
            except BaseException:
                await continuation.session.dispose()
                raise
            return _ActivatedHostedResumeV1(
                continuation.session,
                continuation.attempt_id,
                continuation.input_record_id,
            )

    def _observe_input_identity(self, query: CodingResumeInputLookupQueryV1) -> None:
        self._latest_input_query = query

    async def close(self) -> None:
        task = self._close_task
        if task is None or (task.done() and not task.cancelled() and task.exception()):
            task = asyncio.create_task(self._close_once())
            task.add_done_callback(_observe_close)
            self._close_task = task
        await asyncio.shield(task)

    async def _close_once(self) -> None:
        self._control.close()
        active = self._active
        if active is not None:
            await active.close()
        else:
            self._approval.end_session()
            await self._source.close()
        if self._planning is not None:
            await self._planning.close()
        self._interactions.clear()


@dataclass(frozen=True, slots=True)
class _ActivatedHostedResumeV1:
    session: AgentSession
    attempt_id: str
    input_record_id: str


class _HostedResumeExecutionWorkV1:
    def __init__(
        self,
        binding: CodingDeferredHostedSessionV1,
        text: str,
        cancel_requested: Callable[[], bool],
        scope: AppClientScopeV1,
        control: SessionSnapshotRequestV1,
        subject_digest: str,
        submission_id: str,
    ) -> None:
        self._binding = binding
        self._text = text
        self._cancel_requested = cancel_requested
        self._scope = scope
        self._control = control
        self._subject_digest = subject_digest
        self._submission_id = submission_id
        self._session: AgentSession | None = None
        self._interrupted = False
        self._outcome: ExecutionOutcomeV1 | None = None
        self._unsubscribe: Callable[[], None] | None = None
        self._unbind_turn: Callable[[], None] | None = None

    async def run(self, control: ExecutionControlV1) -> ExecutionOutcomeV1:
        from loushang.agent import AbortSignal
        from loushang.agent.types import AgentEvent
        from loushang.ai.types import AssistantMessage

        if self._cancel_requested():
            return ExecutionOutcomeV1(ExecutionStatusV1.INTERRUPTED)
        try:
            activated = await self._binding.activate(
                self._text,
                scope=self._scope,
                subject_control=self._control,
                subject_digest=self._subject_digest,
                submission_id=self._submission_id,
            )
            session = activated.session
            self._session = session

            def observe(event: AgentEvent, signal: AbortSignal) -> None:
                if event["type"] == "agent_end":
                    for message in reversed(event["messages"]):
                        if isinstance(message, AssistantMessage):
                            self._outcome = ExecutionOutcomeV1(
                                ExecutionStatusV1.INTERRUPTED
                                if message.stop_reason == "aborted"
                                else ExecutionStatusV1.FAILED
                                if message.stop_reason == "error"
                                else ExecutionStatusV1.SUCCEEDED,
                                error_code=(
                                    "assistant_response_error"
                                    if message.stop_reason == "error"
                                    else None
                                ),
                            )
                            break

            self._unsubscribe = session.agent.subscribe(observe)
            self._unbind_turn = control.bind_turn_interrupt(
                lambda: session.abort() if session.is_streaming else False
            )
            await session._run_published_resume_input(
                attempt_id=activated.attempt_id,
                input_record_id=activated.input_record_id,
            )
            return self._outcome or ExecutionOutcomeV1(
                ExecutionStatusV1.FAILED, error_code="missing_agent_outcome"
            )
        except asyncio.CancelledError:
            self._interrupted = True
            if self._session is not None:
                self._session.abort()
            raise
        finally:
            if self._unbind_turn is not None:
                self._unbind_turn()
                self._unbind_turn = None

    async def settle(self) -> None:
        if self._session is not None:
            await self._session.settle_execution(interrupted=self._interrupted)
        if self._unsubscribe is not None:
            self._unsubscribe()
            self._unsubscribe = None


class CodingRealHostedSessionFactoryV1:
    """Trusted outer configuration; no remote module, model or factory names."""

    def __init__(
        self,
        *,
        services_factory: Callable[[Path], BootstrapServices],
        model: Model | ModelSelection | None = None,
        stream_fn: StreamFn | None = None,
        tools: list[ToolDefinition] | None = None,
        output_capture_factory: ExecCaptureFactory | None = None,
        package_product_runtime_factory_for_session: (
            CodingHostedProductRuntimeFactoryForSession | None
        ) = None,
    ) -> None:
        self._services_factory = services_factory
        self._model = model
        self._stream_fn = stream_fn
        self._tools = tools
        self._output_capture_factory = output_capture_factory
        self._package_product_runtime_factory_for_session = (
            package_product_runtime_factory_for_session
        )
        self._product_owner_selection = CodingFencedProductApplicationSelection(
            windows_candidate=sys.platform == "win32"
        )
        self._closing = False
        self._closed = False

    def _default_product_factory_for_session(
        self, manager: SessionManager, services: BootstrapServices
    ) -> PackageProductRuntimeFactoryPort | None:
        return self._product_owner_selection.factory_for_session(
            manager, settings_manager=services.settings_manager
        )

    async def close(self) -> None:
        if self._closed:
            return
        self._closing = True
        self._product_owner_selection.close()
        self._closed = True

    async def create_session(
        self,
        *,
        binding_key: SessionBindingKeyV1,
        opaque_session_binding: object,
    ) -> (
        CodingRealHostedSessionV1
        | CodingHostedHistoryBindingV1
        | CodingDeferredHostedSessionV1
    ):
        if self._closing:
            raise CodingHostedCatalogError()
        if type(opaque_session_binding) not in (
            CodingHostedCandidateBindingV1, CodingHostedHistoryCandidateBindingV1,
        ):
            raise CodingHostedCatalogError()
        opaque_session_binding = cast(
            CodingHostedCandidateBindingV1 | CodingHostedHistoryCandidateBindingV1,
            opaque_session_binding,
        )
        identity = opaque_session_binding.record.identity
        if binding_key != SessionBindingKeyV1(
            identity.product_id, identity.continuity_id, identity.session_id
        ):
            raise CodingHostedCatalogError()
        if isinstance(opaque_session_binding, CodingHostedHistoryCandidateBindingV1):
            if not opaque_session_binding.supports_writable_resume:
                return opaque_session_binding.take_binding()
            source = opaque_session_binding.take_resume_source()
            try:
                binding = CodingDeferredHostedSessionV1(
                    source,
                    services=self._services_factory(source.record.scope.cwd),
                    model=self._model,
                    stream_fn=self._stream_fn,
                    tools=self._tools,
                    output_capture_factory=self._output_capture_factory,
                    product_owner_selection=self._product_owner_selection,
                )
                await binding.start_background_planning()
                return binding
            except BaseException:
                await source.close()
                raise
        manager = opaque_session_binding.manager_for_construction()
        try:
            approval = InteractiveApprovalResolver(fallback=DenyApprovalResolver())
            services = self._services_factory(opaque_session_binding.record.scope.cwd)
            policy = workspace_tool_runtime_settings(services.settings_manager)
            runtime_factory = None
            if self._package_product_runtime_factory_for_session is not None:
                runtime_factory = self._package_product_runtime_factory_for_session(
                    manager
                )
                if runtime_factory is None:
                    raise TypeError("Package Product runtime factory is required")
            else:
                runtime_factory = self._default_product_factory_for_session(
                    manager, services
                )
            session = create_agent_session(
                session_manager=manager,
                model=self._model,
                stream_fn=self._stream_fn,
                services=services,
                tools=self._tools,
                approval_resolver=approval,
                tool_policy_evaluator=policy.policy_engine,
                output_capture_factory=self._output_capture_factory,
                package_product_runtime_factory=runtime_factory,
            )
            opaque_session_binding.retain_constructed_owner(session.dispose)
            real_binding = CodingRealHostedSessionV1(session, identity, approval)
            opaque_session_binding.take_manager()
            return real_binding
        except BaseException:
            # The claimed candidate retains failed cleanup for the outer
            # AppHost owner to retry; no acquired owner disappears on failure.
            await opaque_session_binding.close()
            raise


def _bounded(text: str, *, limit: int = _TEXT_LIMIT) -> str:
    marker = " … [truncated]"
    return text if len(text) <= limit else text[: limit - len(marker)] + marker


def _message_record(message: object) -> TranscriptRecordV1 | None:
    if not isinstance(message, UserMessage | AssistantMessage):
        return None
    return TranscriptRecordV1(
        TranscriptRecordKindV1.USER
        if isinstance(message, UserMessage)
        else TranscriptRecordKindV1.ASSISTANT,
        _bounded(_message_text(message)),
    )


def _message_text(message: object) -> str:
    if not isinstance(message, UserMessage | AssistantMessage):
        return ""
    content = message.content
    text = (
        content
        if isinstance(content, str)
        else "".join(
            getattr(part, "text", "")
            for part in content
            if getattr(part, "type", None) == "text"
        )
    )
    return text


def _observe_close(task: asyncio.Task[None]) -> None:
    if not task.cancelled():
        task.exception()


__all__ = [
    "CodingDeferredHostedSessionV1",
    "CodingHostedHistoryBindingV1",
    "CodingHostedProductRuntimeFactoryForSession",
    "CodingRealHostedSessionFactoryV1",
    "CodingRealHostedSessionV1",
]


def _require_coding_hosted_binding(binding: object) -> None:
    for name in ("project_snapshot", "project_event"):
        if not callable(getattr(binding, name, None)):
            raise TypeError("Coding hosted Session binding is invalid")
    for name in ("respond_interaction", "close"):
        if not inspect.iscoroutinefunction(getattr(binding, name, None)):
            raise TypeError("Coding hosted Session binding is invalid")
    try:
        control = cast(CodingHostedSessionBindingV1, binding).control
    except BaseException:
        raise TypeError("Coding hosted Session binding is invalid") from None
    if control is None:
        return
    for name in (
        "subscribe_runtime_events",
        "prompt",
        "wait_for_idle",
        "steer",
        "follow_up",
        "abort",
    ):
        if not callable(getattr(control, name, None)):
            raise TypeError("Coding hosted Session control is invalid")


async def _lookup_coding_resume_input(
    binding: CodingHostedSessionBindingV1, query: ResumeInputLookupQueryV1,
) -> ResumeInputLookupResultV1:
    lookup = getattr(binding, "lookup_resume_input", None)
    if not inspect.iscoroutinefunction(lookup):
        raise AppServiceError(AppErrorCodeV1.OPERATION_UNAVAILABLE)
    result = await lookup(CodingResumeInputLookupQueryV1(query.input_id, query.record_digest))
    if type(result) is not CodingResumeInputLookupResultV1:
        raise AppServiceError(AppErrorCodeV1.SESSION_UNAVAILABLE)
    return ResumeInputLookupResultV1(result.input_id, result.record_id, result.status)
