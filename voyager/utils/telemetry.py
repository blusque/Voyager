"""Telemetry compatibility helpers."""

from __future__ import annotations

from typing import Any, Callable

import posthog

_PATCH_ATTR = "_chromadb_compat_patched"


def ensure_posthog_compat() -> None:
    """Patch posthog.capture to accept the legacy positional signature used by chromadb."""
    if getattr(posthog, _PATCH_ATTR, False):  # pragma: no cover - guard clause
        return

    original_capture: Callable[..., Any] = posthog.capture

    def compat_capture(*args: Any, **kwargs: Any) -> Any:
        if len(args) >= 2 and isinstance(args[0], str) and isinstance(args[1], str):
            distinct_id, event_name = args[0], args[1]
            remaining_args = args[2:]
            properties = None
            if remaining_args:
                candidate = remaining_args[0]
                if isinstance(candidate, dict):
                    properties = candidate
                    remaining_args = remaining_args[1:]
            kwargs.setdefault("distinct_id", distinct_id)
            if properties is not None and "properties" not in kwargs:
                kwargs["properties"] = properties
            args = (event_name, *remaining_args)
        return original_capture(*args, **kwargs)

    setattr(compat_capture, _PATCH_ATTR, True)
    posthog.capture = compat_capture
    setattr(posthog, _PATCH_ATTR, True)
