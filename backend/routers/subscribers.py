from typing import List

from api.contracts.subscribers import SubscriberCreateRequestV1
from fastapi import APIRouter, Depends
from middleware.tenant_scope import get_scope_tenant_user
from models.models import User, get_db
from models.schema_domains.subscribers import (
    SubscriberCreate,
    SubscriberDeactivate,
    SubscriberResponse,
    SubscriberUpdate,
)
from services.subscriber_service import (
    create_subscriber,
    create_subscriber_v1,
    deactivate_subscriber,
    get_subscriber,
    list_subscribers,
    update_subscriber,
)
from sqlalchemy.orm import Session

router = APIRouter(tags=["subscribers"])


@router.post("/api/v1/subscribers", response_model=SubscriberResponse)
def create_subscriber_legacy(
    body: SubscriberCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_scope_tenant_user),
):
    return create_subscriber(db, user, body)


@router.post("/v1/subscribers", response_model=SubscriberResponse)
def create_subscriber_contract_v1(
    body: SubscriberCreateRequestV1,
    db: Session = Depends(get_db),
    user: User = Depends(get_scope_tenant_user),
):
    return create_subscriber_v1(db, user, body)


@router.get(
    "/api/v1/subscribers/{subscriber_id}", response_model=SubscriberResponse
)
def get_subscriber_endpoint(
    subscriber_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_scope_tenant_user),
):
    return get_subscriber(db, user, subscriber_id)


@router.patch(
    "/api/v1/subscribers/deactivate",
    response_model=SubscriberResponse,
)
def deactivate_subscriber_from_body_endpoint(
    body: SubscriberDeactivate,
    db: Session = Depends(get_db),
    user: User = Depends(get_scope_tenant_user),
):
    return deactivate_subscriber(db, user, body.subscriber_id)


@router.patch(
    "/api/v1/subscribers/{subscriber_id}", response_model=SubscriberResponse
)
def update_subscriber_endpoint(
    subscriber_id: str,
    body: SubscriberUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_scope_tenant_user),
):
    return update_subscriber(db, user, subscriber_id, body)


@router.get("/api/v1/subscribers", response_model=List[SubscriberResponse])
def list_subscribers_endpoint(
    db: Session = Depends(get_db),
    user: User = Depends(get_scope_tenant_user),
):
    return list_subscribers(db, user)


@router.patch(
    "/api/v1/subscribers/{subscriber_id}/deactivate",
    response_model=SubscriberResponse,
)
def deactivate_subscriber_endpoint(
    subscriber_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_scope_tenant_user),
):
    return deactivate_subscriber(db, user, subscriber_id)
