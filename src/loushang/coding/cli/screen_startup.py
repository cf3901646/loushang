"""Coding ownership adapter for a screen displayed before Session bootstrap."""

from __future__ import annotations

import asyncio
import inspect
import os
import sys
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, TextIO, cast

from loushang.coding.cli.startup_route import screen_startup_eligible
from loushang.coding.ui.screen_app import ScreenCodingTuiApp
from loushang.harness.host.product_host import ProductHostLifecycle, stream_is_tty
from loushang.harnesstui.conversation.startup_host import (
    ScreenConversationStartup,
    join_screen_settlement,
    startup_failure_summary,
)
from loushang.tui import strip_control_sequences


@dataclass(slots=True)
class _EmbeddedResumeStartup:
    target: str
    history: Any
    model: Any = None


def _threaded_loading_supported(stdin: TextIO) -> bool:
    if sys.platform != "linux":
        return False
    try:
        return os.isatty(stdin.fileno())
    except (AttributeError, OSError, ValueError):
        return False


class StartupOutput:
    """Bounded Product output with TTY routing metadata, but no terminal writes."""

    def __init__(self, original: TextIO, *, limit: int = 65_536) -> None:
        self.original = original
        self.limit = limit
        self._text = ""
        self._truncated = False

    @property
    def encoding(self) -> str:
        return self.original.encoding or "utf-8"

    def isatty(self) -> bool:
        return stream_is_tty(self.original)

    def writable(self) -> bool:
        return True

    def flush(self) -> None:
        """Product flush never writes over the live screen."""

    def write(self, text: str) -> int:
        available = max(0, self.limit - len(self._text))
        self._text += text[:available]
        self._truncated |= len(text) > available
        return len(text)

    def drain(self) -> None:
        text, truncated = self._text, self._truncated
        self._text, self._truncated = "", False
        if text:
            self.original.write(text)
        if truncated:
            self.original.write("\n[Startup output truncated]\n")
        self.original.flush()

    def diagnostic_text(self) -> str:
        return strip_control_sequences(self._text).strip()[-1000:]


async def run_screen_first_cli(
    raw_argv: tuple[str, ...],
    *,
    binding: Any = None,
    host_binding: Any = None,
    host_runners: Any = None,
    project_root: Path,
    cwd: str | Path | None,
) -> int:
    streams = (
        binding.host_lifecycle.streams
        if binding is not None
        else ProductHostLifecycle.resolve().streams
    )
    output = StartupOutput(streams.stdout)
    errors = StartupOutput(streams.stderr)
    app = ScreenCodingTuiApp(
        model_label=None,
        cwd=str(project_root),
        branch=None,
        session_label=None,
    )
    owned_runtime: Any = None
    threaded_startup: Any = None

    async def run_tui(**kwargs: Any) -> int:
        if threaded_startup is not None:
            await threaded_startup.before_product_ui()
        from loushang.coding.ui.mode import run_coding_tui

        return await run_coding_tui(
            **kwargs,
            startup_app=app,
            prepared_screen_runner=startup.attach,
        )

    async def run_prepared_binding(
        binding: Any, host_binding: Any, host_runners: Any
    ) -> int:
        from loushang.harness.cli.application import (
            CliPhaseResult,
            invoke_agent_cli_runtime_builder,
            run_agent_cli_application,
        )

        async def build_runtime(**kwargs: Any) -> Any:
            nonlocal owned_runtime
            result = invoke_agent_cli_runtime_builder(binding.runtime_builder, **kwargs)
            owned_runtime = await result if inspect.isawaitable(result) else result
            return owned_runtime

        supports_resume_history = all(
            hasattr(binding, name)
            for name in (
                "pre_session_bootstrap",
                "configure_session",
                "session_operations",
            )
        )
        original_pre_session = getattr(binding, "pre_session_bootstrap", None)
        original_configure = getattr(
            binding, "configure_session", lambda _context: None
        )
        original_operations = getattr(
            binding, "session_operations", lambda _context: None
        )
        ordinary_host = host_binding.bind(replace(host_runners, tui=run_tui))

        async def pre_session(context: Any) -> Any:
            resume = context.state.args.resume
            if isinstance(resume, str):
                from loushang.coding.runtime.agent_session_runtime import (
                    AgentSessionRuntime,
                )

                if type(context.runtime) is not AgentSessionRuntime:
                    raise RuntimeError(
                        "Embedded Resume requires the native Coding Root"
                    )
                history = await context.runtime.preview_resume_history(resume)
                await context.runtime.start_configured_resume_planning(history)
                return CliPhaseResult.continue_with(
                    _EmbeddedResumeStartup(resume, history)
                )
            if original_pre_session is None:
                return None
            result = original_pre_session(context)
            return await result if inspect.isawaitable(result) else result

        async def configure(context: Any) -> int | None:
            if not isinstance(context.session, _EmbeddedResumeStartup):
                result = original_configure(context)
                return await result if inspect.isawaitable(result) else result
            from loushang.ai.model import parse_model_selection_reference

            context.session.model = parse_model_selection_reference(
                context.args.model,
                provider=context.args.provider,
                registry=getattr(
                    getattr(context.state.services, "model_registry", None),
                    "ai_registry",
                    None,
                ),
            )
            return None

        async def session_operations(context: Any) -> int | None:
            if isinstance(context.session, _EmbeddedResumeStartup):
                return None
            result = original_operations(context)
            return await result if inspect.isawaitable(result) else result

        async def run_host(context: Any) -> int:
            if not isinstance(context.session, _EmbeddedResumeStartup):
                return await ordinary_host(context)
            if threaded_startup is not None:
                await threaded_startup.before_product_ui()

            from loushang.coding.embedded_resume import (
                EmbeddedResumeApprovalInteraction,
                EmbeddedResumeInputCoordinator,
            )
            from loushang.coding.interaction.resume_history import (
                build_coding_resume_history_screen,
            )
            from loushang.coding.ui.screen_surfaces import ScreenSurfaceManager
            from loushang.harnesstui.conversation.agent_application import (
                handle_agent_screen_approval,
            )
            from loushang.harnesstui.conversation.application_host import (
                run_prepared_screen_conversation,
            )
            from loushang.harnesstui.status.provider import StatusProvider

            resume = context.session
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
            coordinator = EmbeddedResumeInputCoordinator(
                runtime=context.runtime,
                services=context.state.services,
                policy_evaluator=context.state.tool_policy_evaluator,
                model=resume.model,
                thinking_level=context.args.thinking,
                no_tools=no_tools,
                worker_candidate_plugin_id=context.args.worker_query_plugin,
            )
            app.state.cwd = str(context.bootstrap.project_root)
            app.state.session_label = (
                resume.history.header_preview.header.conversation_id
            )

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
                permission_profile=lambda: context.state.settings_manager.get_permission_profile_id(),
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
                prepare_input=prepare_input,
                surface=surface,
                stderr=context.bootstrap.stderr,
                approval_interaction=approval,
            )
            return await run_prepared_screen_conversation(
                prepared,
                stdin=context.bootstrap.stdin,
                stdout=context.bootstrap.stdout,
                screen_runner=startup.attach,
            )

        updates = {
            "runtime_builder": build_runtime,
            "host_lifecycle": ProductHostLifecycle.resolve(
                stdin=streams.stdin,
                stdout=cast(TextIO, output),
                stderr=cast(TextIO, errors),
            ),
            "run_host": run_host if supports_resume_history else ordinary_host,
        }
        if supports_resume_history:
            updates.update(
                pre_session_bootstrap=pre_session,
                configure_session=configure,
                session_operations=session_operations,
            )
        prepared_binding = replace(binding, **updates)
        return await run_agent_cli_application(
            raw_argv, binding=prepared_binding, cwd=cwd
        )

    async def prepare() -> int:
        primary_error: BaseException | None = None
        try:
            if binding is None:
                from loushang.coding.cli.application import run_cli

                return await run_cli(
                    raw_argv,
                    cwd=cwd,
                    _prepared_screen_runner=run_prepared_binding,
                )
            return await run_prepared_binding(binding, host_binding, host_runners)
        except BaseException as error:
            primary_error = error
            raise
        finally:
            startup.begin_cleanup()
            if owned_runtime is not None:
                # The Product runtime, not generic dispose(), owns Session shutdown.
                async def dispose() -> None:
                    try:
                        await owned_runtime.dispose_session_runtime()
                    except asyncio.CancelledError as error:
                        raise RuntimeError(
                            "Session runtime cleanup cancelled before settlement"
                        ) from error

                try:
                    await join_screen_settlement(asyncio.create_task(dispose()))
                except BaseException as cleanup_error:
                    if primary_error is not None:
                        raise BaseExceptionGroup(
                            "Session preparation and cleanup failed",
                            [primary_error, cleanup_error],
                        ) from None
                    raise

    def failure_summary(exit_code: int) -> str:
        # The existing launch shell reports non-verbose UI failures to stdout.
        parts = [stream.diagnostic_text() for stream in (output, errors)]
        detail = "\n".join(part[-500:] for part in parts if part)
        return detail or f"Session preparation failed (exit {exit_code})."

    startup = ScreenConversationStartup(app, prepare, failure_summary=failure_summary)
    if _threaded_loading_supported(streams.stdin):
        from loushang.harnesstui.conversation.threaded_startup import (
            ThreadedScreenStartup,
        )

        threaded_startup = ThreadedScreenStartup(startup)
    try:
        runner = threaded_startup if threaded_startup is not None else startup
        return await runner.run(stdin=streams.stdin, stdout=streams.stdout)
    except (Exception, BaseExceptionGroup) as error:
        errors.write(f"Error: {startup_failure_summary(error)}\n")
        return 1
    finally:
        # All Product output, including the resume hint, follows terminal restore.
        try:
            output.drain()
        finally:
            errors.drain()


__all__ = ["StartupOutput", "run_screen_first_cli", "screen_startup_eligible"]
