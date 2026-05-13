from __future__ import annotations

from typing import List

from api.contracts.subscribers import SubscriberCreateRequestV1
from exceptions import ConflictError, NotFoundError
from models.models import Subscriber, User
from models.schema_domains.subscribers import (
    SubscriberCreate,
    SubscriberResponse,
    SubscriberUpdate,
)
from sqlalchemy.orm import Session


def _get_owned_subscriber(
    db: Session,
    user: User,
    subscriber_id: str,
) -> Subscriber:
    row = (
        db.query(Subscriber)
        .filter(
            Subscriber.user_id == user.id,
            Subscriber.subscriber_id == subscriber_id,
        )
        .first()
    )
    if not row:
        raise NotFoundError("Subscriber not found")
    return row


def _to_legacy_create(body: SubscriberCreateRequestV1) -> SubscriberCreate:
    data = {
        "firstName": (body.firstName or "").strip(),
        "lastName": (body.lastName or "").strip(),
    }
    return SubscriberCreate(
        subscriber_id=body.subscriberId.strip(),
        email=body.email,
        data=data,
        channels=None,
    )


def create_subscriber_v1(
    db: Session,
    user: User,
    body: SubscriberCreateRequestV1,
) -> SubscriberResponse:
    return create_subscriber(db, user, _to_legacy_create(body))


def create_subscriber(
    db: Session,
    user: User,
    body: SubscriberCreate,
) -> SubscriberResponse:
    exists = (
        db.query(Subscriber)
        .filter(
            Subscriber.user_id == user.id,
            Subscriber.subscriber_id == body.subscriber_id,
        )
        .first()
    )
    if exists:
        raise ConflictError("subscriber_id already exists for this account")
    row = Subscriber(
        user_id=user.id,
        subscriber_id=body.subscriber_id.strip(),
        email=str(body.email),
        data=body.data,
        channels=body.channels,
        is_active=True,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return SubscriberResponse.from_orm(row)


def get_subscriber(
    db: Session,
    user: User,
    subscriber_id: str,
) -> SubscriberResponse:
    return SubscriberResponse.from_orm(
        _get_owned_subscriber(db, user, subscriber_id)
    )


def update_subscriber(
    db: Session,
    user: User,
    subscriber_id: str,
    body: SubscriberUpdate,
) -> SubscriberResponse:
    row = _get_owned_subscriber(db, user, subscriber_id)
    if body.email is not None:
        row.email = str(body.email)
    if body.data is not None:
        row.data = body.data
    if body.channels is not None:
        row.channels = body.channels
    if body.is_active is not None:
        row.is_active = body.is_active
    db.commit()
    db.refresh(row)
    return SubscriberResponse.from_orm(row)


def list_subscribers(db: Session, user: User) -> List[SubscriberResponse]:
    rows = (
        db.query(Subscriber)
        .filter(Subscriber.user_id == user.id)
        .order_by(Subscriber.created_at.desc())
        .all()
    )
    return [SubscriberResponse.from_orm(r) for r in rows]


def deactivate_subscriber(
    db: Session,
    user: User,
    subscriber_id: str,
) -> SubscriberResponse:
    row = _get_owned_subscriber(db, user, subscriber_id)
    row.is_active = False
    db.commit()
    db.refresh(row)
    return SubscriberResponse.from_orm(row)


def activate_subscriber(
    db: Session,
    user: User,
    subscriber_id: str,
) -> SubscriberResponse:
    row = _get_owned_subscriber(db, user, subscriber_id)
    row.is_active = True
    db.commit()
    db.refresh(row)
    return SubscriberResponse.from_orm(row)
