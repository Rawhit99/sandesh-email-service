"""Merge per-user integration URLs into auxiliary channel payload."""

from __future__ import annotations

from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from services.user_integration import merge_channel_overrides_into_payload


def merge_user_webhooks_into_payload(
    db: Session, user_id: Optional[int], payload: Dict[str, Any]
) -> Dict[str, Any]:
    return merge_channel_overrides_into_payload(db, user_id, payload)
