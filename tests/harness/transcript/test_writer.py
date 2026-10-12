from __future__ import annotations

import asyncio
from datetime import UTC, datetime

import pytest

from loushang.ai.types import UserMessage
from loushang.harness.conversation import (
    ConversationHeader,
    ConversationKey,
    MemoryConversationStore,
    StoreCommitOutcomeUnknown,
)
from loushang.harness.transcript import (
    AGENT_MESSAGE_KIND,
    APPLICATION_MESSAGE_KIND,
    AgentTranscriptRecordFactory,
    AgentTranscriptUnitOfWork,
    ApplicationMessage,
    ApplicationMessageIdentityConflictError,
    PrebuiltUserMessageIdentityConflictError,
    TranscriptCommitter,
)
from loushang.harness.transcript.unit_of_work import AgentTranscriptCommit


def _ids(*values: str):
    values_iter = iter(values)
    return lambda: next(values_iter)


def _message(content: str = "notice") -> ApplicationMessage:
    return ApplicationMessage(
        application_message_id="application-1",
        custom_type="notice",
        content=content,
        timestamp=1.0,
    )


async def _store(*, ids) -> AgentTranscriptUnitOfWork:
    backend = MemoryConversationStore(record_id=lambda record: record.record_id)
    return await AgentTranscriptUnitOfWork.create(
        backend,
        ConversationKey("test", "conversation-1"),
        ConversationHeader(
            conversation_id="conversation-1",
            version=1,
            created_at="2026-07-16T00:00:00Z",
        ),
        clock=lambda: datetime(2026, 7, 16, tzinfo=UTC),
        id_factory=ids,
    )


def test_record_factory_builds_records_without_committing_them() -> None:
    factory = AgentTranscriptRecordFactory(
        clock=lambda: datetime(2026, 7, 16, tzinfo=UTC),
        id_factory=_ids("record-1"),
    )

    record = factory.create(
        APPLICATION_MESSAGE_KIND,
        _message(),
        parent_id="parent-1",
    )

    assert record.record_id == "record-1"
    assert record.parent_id == "parent-1"
    assert record.created_at == "2026-07-16T00:00:00Z"


def test_committer_is_idempotent_and_rejects_identity_conflicts() -> None:
    async def scenario() -> None:
        store = await _store(ids=_ids("record-1"))
        committer = TranscriptCommitter(store)

        first = await committer.commit_application_message(_message())
        duplicate = await committer.commit_application_message(_message())

        assert first.disposition == "committed"
        assert duplicate.disposition == "already_committed"
        assert duplicate.record_id == first.record_id
        assert len(store.records) == 1
        assert store.records[0].kind == APPLICATION_MESSAGE_KIND

        with pytest.raises(
            ApplicationMessageIdentityConflictError,
            match="different payload",
        ):
            await committer.commit_application_message(_message("changed"))
        assert len(store.records) == 1

    asyncio.run(scenario())


def test_failed_append_is_not_memoized_as_committed() -> None:
    async def scenario() -> None:
        store = await _store(ids=_ids("same", "same", "recovered"))
        await store.append_application_message(
            ApplicationMessage(
                application_message_id="existing",
                custom_type="notice",
                content="existing",
                timestamp=0.0,
            )
        )
        committer = TranscriptCommitter(store)

        with pytest.raises(ValueError, match="Duplicate branch record id"):
            await committer.commit_application_message(_message())

        recovered = await committer.commit_application_message(_message())
        assert recovered.disposition == "committed"
        assert recovered.record_id == "recovered"

    asyncio.run(scenario())


def test_committer_rebuilds_application_message_identity_from_loaded_records() -> None:
    async def scenario() -> None:
        store = await _store(ids=_ids("record-1"))
        first = await TranscriptCommitter(store).commit_application_message(_message())
        loaded = await AgentTranscriptUnitOfWork.load(store.backend, store.key)

        duplicate = await TranscriptCommitter(loaded).commit_application_message(
            _message()
        )

        assert duplicate.disposition == "already_committed"
        assert duplicate.record_id == first.record_id
        assert loaded.revision == 1

    asyncio.run(scenario())


def test_record_factory_requires_timezone_aware_clock() -> None:
    factory = AgentTranscriptRecordFactory(
        clock=lambda: datetime(2026, 7, 16),
        id_factory=_ids("record-1"),
    )

    with pytest.raises(ValueError, match="timezone-aware"):
        factory.create(APPLICATION_MESSAGE_KIND, _message(), parent_id=None)


def _prebuilt_user_record(*, content: str = "continue"):
    return AgentTranscriptRecordFactory(
        clock=lambda: datetime(2026, 7, 16, tzinfo=UTC),
        id_factory=lambda: "stable-input-record",
    ).create(
        AGENT_MESSAGE_KIND,
        UserMessage(role="user", content=content, timestamp=1.0),
        parent_id=None,
        metadata={
            "coding.runtimeBindingV1": {"version": 1, "inputId": "input-1"},
            "harness.resourceEvidenceV1": {"version": 1},
        },
    )


def test_prebuilt_user_record_is_committed_once_across_reload() -> None:
    async def scenario() -> None:
        store = await _store(ids=_ids("unused"))
        record = _prebuilt_user_record()
        committer = TranscriptCommitter(store)

        first = await committer.commit_prebuilt_user_message(record)
        duplicate = await committer.commit_prebuilt_user_message(record)
        loaded = await AgentTranscriptUnitOfWork.load(store.backend, store.key)
        after_restart = await TranscriptCommitter(loaded).commit_prebuilt_user_message(
            record
        )

        assert first.disposition == "committed"
        assert duplicate.disposition == "already_committed"
        assert after_restart.disposition == "already_committed"
        assert loaded.records == (record,)
        assert loaded.revision == 1

        with pytest.raises(PrebuiltUserMessageIdentityConflictError):
            await TranscriptCommitter(loaded).commit_prebuilt_user_message(
                _prebuilt_user_record(content="different")
            )
        loaded.reset_branch()
        with pytest.raises(
            PrebuiltUserMessageIdentityConflictError, match="selected branch",
        ):
            await TranscriptCommitter(loaded).commit_prebuilt_user_message(record)
        assert loaded.records == (record,)

    asyncio.run(scenario())


def test_prebuilt_user_record_reconciles_lost_ack_by_fixed_record_id() -> None:
    class LostAckStore(MemoryConversationStore):
        append_calls = 0

        async def append(self, key, record, *, expected_revision, operation_id):
            self.append_calls += 1
            await super().append(
                key, record,
                expected_revision=expected_revision,
                operation_id=operation_id,
            )
            raise StoreCommitOutcomeUnknown("ack lost after durable append")

    async def scenario() -> None:
        backend = LostAckStore(record_id=lambda record: record.record_id)
        key = ConversationKey("test", "conversation-1")
        store = await AgentTranscriptUnitOfWork.create(
            backend,
            key,
            ConversationHeader(
                conversation_id="conversation-1",
                version=1,
                created_at="2026-07-16T00:00:00Z",
            ),
        )
        record = _prebuilt_user_record()
        committer = TranscriptCommitter(store)
        with pytest.raises(StoreCommitOutcomeUnknown):
            await committer.commit_prebuilt_user_message(record)
        with pytest.raises(StoreCommitOutcomeUnknown, match="authoritative reload"):
            await committer.commit_prebuilt_user_message(record)
        assert backend.append_calls == 2

        loaded = await AgentTranscriptUnitOfWork.load(backend, key)
        result = await TranscriptCommitter(loaded).commit_prebuilt_user_message(record)
        assert result.disposition == "already_committed"
        assert loaded.records == (record,)
        assert loaded.revision == 1

    asyncio.run(scenario())


def test_prebuilt_user_record_without_durable_receipt_requires_reload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def scenario() -> None:
        store = await _store(ids=_ids("unused"))
        record = _prebuilt_user_record()
        committer = TranscriptCommitter(store)
        calls = 0

        async def missing_receipt(_record):
            nonlocal calls
            calls += 1
            return AgentTranscriptCommit(record=record, receipt=None)

        monkeypatch.setattr(store, "commit", missing_receipt)
        with pytest.raises(StoreCommitOutcomeUnknown, match="durable receipt"):
            await committer.commit_prebuilt_user_message(record)
        with pytest.raises(StoreCommitOutcomeUnknown, match="authoritative reload"):
            await committer.commit_prebuilt_user_message(record)
        assert calls == 1
        assert store.records == ()

    asyncio.run(scenario())
