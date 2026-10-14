"""Shared history-first host for explicit and picker-selected Coding Resume."""

from __future__ import annotations

import sys
from collections.abc import Awaitable, Callable
from typing import Any

from loushang.ai.model import parse_model_selection_reference
from loushang.coding.embedded_resume import (
    EmbeddedResumeApprovalInteraction,
    EmbeddedResumeInputCoordinator,
    EmbeddedResumeStartup,
)
from loushang.coding.interaction.resume_history import (
    build_coding_resume_history_screen,
)
from loushang.coding.resume_history import CodingResumeHistoryPreview
from loushang.coding.ui.screen_app import ScreenCodingTuiApp
from loushang.coding.ui.screen_surfaces import ScreenSurfaceManager
from loushang.harnesstui.conversation.agent_application import (
    handle_agent_screen_approval,
)
from loushang.harnesstui.conversation.application_host import (
    ActionHostScreenRunner,
    run_prepared_screen_conversation,
)
from loushang.harnesstui.conversation.host import (
    run_action_host_conversation_screen,
)
from loushang.harnesstui.status.provider import StatusProvider


def embedded_resume_history_route_admitted() -> bool:
    """Return whether history-first first-input continuation is admitted."""

    return sys.platform == "linux"


def configure_embedded_resume_startup(context: Any) -> None:
    """Apply CLI model selection without configuring a nonexistent Session."""

    resume = context.session
    if not isinstance(resume, EmbeddedResumeStartup):
        raise TypeError("Embedded Resume startup state is invalid")
    resume.model = parse_model_selection_reference(
        context.args.model,
        provider=context.args.provider,
        registry=getattr(
            getattr(context.state.services, "model_registry", None),
            "ai_registry",
            None,
        ),
    )


async def run_embedded_resume_history_host(
    context: Any,
    *,
    app: ScreenCodingTuiApp | None = None,
    screen_runner: ActionHostScreenRunner = run_action_host_conversation_screen,
    before_product_ui: Callable[[], Awaitable[None]] | None = None,
) -> int:
    """Display authoritative history and defer Session birth to first input."""

    resume = context.session
    if not isinstance(resume, EmbeddedResumeStartup):
        raise TypeError("Embedded Resume startup state is invalid")
    if before_product_ui is not None:
        await before_product_ui()

    app = app or ScreenCodingTuiApp(
        model_label=None,
        cwd=str(context.bootstrap.project_root),
        branch=None,
        session_label=None,
    )
    approval = EmbeddedResumeApprovalInteraction(
        context.state.approval_resolver,
        context.state.settings_manager,
    )
    no_tools: Any = (
        "all"
        if context.args.no_tools
        else "builtin"
        if context.args.no_builtin_tools
        else None
    )
    coordinator = (
        EmbeddedResumeInputCoordinator(
            runtime=context.runtime,
            services=context.state.services,
            policy_evaluator=context.state.tool_policy_evaluator,
            model=resume.model,
            thinking_level=context.args.thinking,
            no_tools=no_tools,
            worker_candidate_plugin_id=context.args.worker_query_plugin,
        )
        if isinstance(resume.history, CodingResumeHistoryPreview)
        else None
    )
    app.state.cwd = str(context.bootstrap.project_root)
    app.state.session_label = resume.history.header_preview.header.conversation_id

    def current_approval() -> Any:
        current = context.runtime.current_session
        return (
            getattr(current, "approval_interaction", None)
            if current is not None
            else approval
        )

    status = StatusProvider(
        model_label=None,
        cwd=app.state.cwd,
        branch=app.state.branch,
        session_label=lambda: app.state.session_label,
        thinking_level=lambda: None,
        running=lambda: app.state.running,
        permission_profile=(
            lambda: context.state.settings_manager.get_permission_profile_id()
        ),
    )
    surface = ScreenSurfaceManager(
        app=app,
        session=resume,
        runtime=context.runtime,
        status_provider=status,
        on_approval=lambda event: handle_agent_screen_approval(
            current_approval(), event
        ),
        approval_interaction_provider=current_approval,
    )

    async def prepare_input(action: Any, observe: Any) -> Any:
        if coordinator is None:
            raise RuntimeError("Writable continuation requires verified history")
        return await coordinator.prepare_input(
            session_file=resume.target,
            history=resume.history,
            action=action,
            observe_input_identity=observe,
        )

    prepared = build_coding_resume_history_screen(
        runtime=context.runtime,
        session_ref=resume.target,
        history=resume.history,
        app=app,
        prepare_input=prepare_input if coordinator is not None else None,
        surface=surface,
        stderr=context.bootstrap.stderr,
        approval_interaction=approval,
    )
    return await run_prepared_screen_conversation(
        prepared,
        stdin=context.bootstrap.stdin,
        stdout=context.bootstrap.stdout,
        screen_runner=screen_runner,
    )


__all__ = [
    "configure_embedded_resume_startup",
    "embedded_resume_history_route_admitted",
    "run_embedded_resume_history_host",
]
