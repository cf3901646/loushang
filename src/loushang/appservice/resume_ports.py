"""Optional Product observation, reusing the closed transport data contract."""

from typing import Protocol, runtime_checkable

from loushang.appserver.resume_model import (
    ResumeInputLookupQueryV1,
    ResumeInputLookupResultV1,
    ResumeInputLookupStatusV1,
)

__all__ = [
    "HostedResumeInputLookupPortV1", "ResumeInputLookupQueryV1",
    "ResumeInputLookupResultV1", "ResumeInputLookupStatusV1",
]


@runtime_checkable
class HostedResumeInputLookupPortV1(Protocol):
    async def lookup_resume_input(
        self, query: ResumeInputLookupQueryV1,
    ) -> ResumeInputLookupResultV1: ...
