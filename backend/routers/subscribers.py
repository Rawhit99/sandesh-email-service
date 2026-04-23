from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from middleware.tenant_scope import get_scope_tenant_user
from models.models import Subscriber, User, get_db
from models.schemas import SubscriberCreate, SubscriberResponse, SubscriberUpdate

router = APIRouter(prefix="/api", tags=["subscribers"])


@router.post("/v1/subscribers", response_model=SubscriberResponse)
def create_subscriber(
    body: SubscriberCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_scope_tenant_user),
):
    exists = (
        db.query(Subscriber)
        .filter(Subscriber.user_id == user.id, Subscriber.subscriber_id == body.subscriber_id)
        .first()
    )
    if exists:
        raise HTTPException(status_code=409, detail="subscriber_id already exists for this account")
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


@router.get("/v1/subscribers/{subscriber_id}", response_model=SubscriberResponse)
def get_subscriber(
    subscriber_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_scope_tenant_user),
):
    row = (
        db.query(Subscriber)
        .filter(Subscriber.user_id == user.id, Subscriber.subscriber_id == subscriber_id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Subscriber not found")
    return SubscriberResponse.from_orm(row)


@router.patch("/v1/subscribers/{subscriber_id}", response_model=SubscriberResponse)
def update_subscriber(
    subscriber_id: str,
    body: SubscriberUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_scope_tenant_user),
):
    row = (
        db.query(Subscriber)
        .filter(Subscriber.user_id == user.id, Subscriber.subscriber_id == subscriber_id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Subscriber not found")
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


@router.get("/v1/subscribers", response_model=List[SubscriberResponse])
def list_subscribers(
    db: Session = Depends(get_db),
    user: User = Depends(get_scope_tenant_user),
):
    rows = db.query(Subscriber).filter(Subscriber.user_id == user.id).order_by(Subscriber.created_at.desc()).all()
    return [SubscriberResponse.from_orm(r) for r in rows]


@router.patch("/v1/subscribers/{subscriber_id}/deactivate", response_model=SubscriberResponse)
def deactivate_subscriber(
    subscriber_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_scope_tenant_user),
):
    row = (
        db.query(Subscriber)
        .filter(Subscriber.user_id == user.id, Subscriber.subscriber_id == subscriber_id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Subscriber not found")
    row.is_active = False
    db.commit()
    db.refresh(row)
    return SubscriberResponse.from_orm(row)
