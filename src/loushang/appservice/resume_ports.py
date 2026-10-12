"""Optional Product observation, reusing the closed transport data contract."""

import asyncio
from typing import Protocol, runtime_checkable

from loushang.appserver.protocol import AppErrorCodeV1, AppServiceError
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


async def _lookup_resume_product_input(
    port: object, query: ResumeInputLookupQueryV1,
) -> ResumeInputLookupResultV1:
    if not isinstance(port, HostedResumeInputLookupPortV1):
        raise AppServiceError(AppErrorCodeV1.OPERATION_UNAVAILABLE)
    try:
        value = await port.lookup_resume_input(query)
    except (asyncio.CancelledError, AppServiceError):
        raise
    except BaseException:
        raise AppServiceError(AppErrorCodeV1.SESSION_UNAVAILABLE) from None
    if type(value) is not ResumeInputLookupResultV1 or value.input_id != query.input_id:
        raise AppServiceError(AppErrorCodeV1.SESSION_UNAVAILABLE)
    return value
