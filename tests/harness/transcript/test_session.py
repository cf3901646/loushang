from __future__ import annotations

import asyncio
import threading

import pytest

from loushang.ai.types import UserMessage
from loushang.harness.conversation import (
    ConversationHeader,
    ConversationKey,
    MemoryConversationStore,
)
from loushang.harness.conversation.repository import ConversationRepository
from loushang.harness.transcript import (
    AgentTranscriptSession,
    AgentTranscriptUnitOfWork,
)


def test_agent_transcript_session_owns_standard_commit_and_label_operations() -> None:
    async def scenario() -> None:
        backend = MemoryConversationStore(record_id=lambda record: record.record_id)
        transcript = await AgentTranscriptUnitOfWork.create(
            backend,
            ConversationKey("test", "conversation-1"),
            ConversationHeader(
                conversation_id="conversation-1",
                version=1,
                created_at="2026-07-18T00:00:00Z",
            ),
            id_factory=iter(("record-1", "record-2", "record-3")).__next__,
        )
        session = AgentTranscriptSession(
            transcript=transcript,
            application_message_id_factory=lambda: "application-1",
        )
        committed: list[str] = []
        session.set_commit_observer(lambda result: committed.append(result.record_id))

        message_id = await session.append_message(
            UserMessage(role="user", content="hello", timestamp=1.0)
        )
        await session.append_label(message_id, "important")
        application_id = await session.append_custom_message_entry(
            "notice",
            "saved",
            display=True,
        )

        assert session.get_label(message_id) == "important"
        assert [record.record_id for record in session.get_branch()] == [
            message_id,
            "record-2",
            application_id,
        ]
        assert [message.role for message in session.build_context().messages] == [
            "user",
            "application",
        ]
        assert committed == [message_id, "record-2", application_id]

    asyncio.run(scenario())


def test_graph_append_preparation_does_not_block_event_loop(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def scenario() -> None:
        backend = MemoryConversationStore(record_id=lambda record: record.record_id)
        transcript = await AgentTranscriptUnitOfWork.create(
            backend,
            ConversationKey("test", "responsive-append"),
            ConversationHeader(
                conversation_id="responsive-append",
                version=1,
                created_at="2026-07-18T00:00:00Z",
            ),
        )
        await transcript.append_agent_message(
            UserMessage(role="user", content="first", timestamp=1.0)
        )
        entered = threading.Event()
        release = threading.Event()
        original = ConversationRepository.with_appended

        def held_append(repository, record):
            entered.set()
            assert release.wait(2), "graph append was not released"
            return original(repository, record)

        monkeypatch.setattr(ConversationRepository, "with_appended", held_append)
        operation = asyncio.create_task(
            transcript.append_agent_message(
                UserMessage(role="user", content="second", timestamp=2.0)
            )
        )
        try:
            assert await asyncio.to_thread(entered.wait, 1)
            await asyncio.sleep(0)
            assert not operation.done()
        finally:
            release.set()
            if operation.done():
                await asyncio.gather(operation, return_exceptions=True)
        await operation
        assert transcript.revision == 2
        assert (await backend.load(transcript.key)).snapshot.revision == 2

    asyncio.run(scenario())
