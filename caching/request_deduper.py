"""
Request Deduplicator

Prevents duplicate concurrent requests from executing multiple times.
When multiple users request the same data simultaneously, only one request
executes while others wait for the result.

Example:
    10 technicians ask "What's the amp draw for 25HBC436A003?" at the same time
    → Only 1 API call to manufacturer service
    → All 10 get the same result

Impact:
- Reduce API costs during training sessions
- Improve response consistency
- Prevent thundering herd problem
"""

import asyncio
from typing import Any, Callable, Dict, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class RequestDeduplicator:
    """Deduplicate concurrent requests for the same resource"""

    def __init__(self):
        self._pending_requests: Dict[str, asyncio.Task] = {}
        self._request_counts: Dict[str, int] = {}  # Track how many waiting

    async def deduplicate(
        self,
        key: str,
        async_fn: Callable[[], Any],
        timeout: Optional[float] = 30.0
    ) -> Any:
        """
        Execute function or wait for pending execution

        Args:
            key: Unique identifier for this request
            async_fn: Async function to execute
            timeout: Max time to wait for result (seconds)

        Returns:
            Result from function execution
        """
        # Check if request already in progress
        if key in self._pending_requests:
            # Another request is already running - wait for it
            self._request_counts[key] = self._request_counts.get(key, 0) + 1

            logger.info(
                f"[RequestDeduper] Waiting for in-progress request: {key} "
                f"({self._request_counts[key]} waiting)"
            )

            try:
                # Wait for the existing request to complete
                result = await asyncio.wait_for(
                    self._pending_requests[key],
                    timeout=timeout
                )

                logger.info(
                    f"[RequestDeduper] Got result from deduplicated request: {key}"
                )

                return result

            except asyncio.TimeoutError:
                logger.error(
                    f"[RequestDeduper] Timeout waiting for request: {key}"
                )
                raise

            finally:
                # Decrement waiting count
                if key in self._request_counts:
                    self._request_counts[key] -= 1
                    if self._request_counts[key] <= 0:
                        del self._request_counts[key]

        # No pending request - create new one
        logger.info(f"[RequestDeduper] Starting new request: {key}")

        # Create task
        task = asyncio.create_task(self._execute_with_cleanup(key, async_fn))
        self._pending_requests[key] = task
        self._request_counts[key] = 0

        try:
            result = await task
            return result

        except Exception as e:
            logger.error(f"[RequestDeduper] Request failed: {key} - {e}")
            raise

    async def _execute_with_cleanup(
        self,
        key: str,
        async_fn: Callable[[], Any]
    ) -> Any:
        """Execute function and clean up tracking"""
        start_time = datetime.now()

        try:
            # Execute the function
            result = await async_fn()

            duration = (datetime.now() - start_time).total_seconds()
            logger.info(
                f"[RequestDeduper] Request completed: {key} "
                f"({duration:.2f}s, {self._request_counts.get(key, 0)} deduplicated)"
            )

            return result

        finally:
            # Clean up
            if key in self._pending_requests:
                del self._pending_requests[key]

            if key in self._request_counts:
                del self._request_counts[key]

    def get_stats(self) -> Dict[str, Any]:
        """Get deduplication statistics"""
        return {
            "pending_requests": len(self._pending_requests),
            "total_waiting": sum(self._request_counts.values()),
            "active_keys": list(self._pending_requests.keys())
        }


# Singleton instance
_deduper_instance: Optional[RequestDeduplicator] = None


def get_deduper() -> RequestDeduplicator:
    """Get singleton deduplicator instance"""
    global _deduper_instance

    if _deduper_instance is None:
        _deduper_instance = RequestDeduplicator()

    return _deduper_instance


# Usage example:
"""
from caching.request_deduper import get_deduper
from caching.response_cache import CacheKey

deduper = get_deduper()

# In a tool function
async def get_specification(model_number: str):
    key = CacheKey.generate("spec", model_number)

    # Deduplicate request
    result = await deduper.deduplicate(
        key=key,
        async_fn=lambda: manufacturer_api.get_spec(model_number)
    )

    return result

# If 10 users call get_specification("25HBC436A003") simultaneously:
# - First call triggers API request
# - Other 9 wait for the first to complete
# - All 10 get the same result
# - Only 1 API call made
"""
