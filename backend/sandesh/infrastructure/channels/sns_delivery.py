"""AWS SNS — publish to a topic ARN (env) or mobile endpoint ARN (payload sns_target_arn)."""

import logging
from typing import Any, Dict

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from config import settings
from sandesh.infrastructure.channels.base import ChannelResult

logger = logging.getLogger(__name__)


async def deliver_sns(payload: Dict[str, Any]) -> ChannelResult:
    import asyncio

    topic = (payload.get("_sns_push_topic_arn") or settings.sns_push_topic_arn or "").strip()
    target = (payload.get("sns_target_arn") or payload.get("endpoint_arn") or "").strip() or topic
    if not target:
        return ChannelResult(ok=False, detail="sns_arn_missing")

    title = str(payload.get("title") or "Alert")[:100]
    body = str(payload.get("text") or "")[:4000]
    access_key = (payload.get("_sns_access_key_id") or settings.aws_access_key_id or "").strip() or None
    secret_key = (
        payload.get("_sns_secret_access_key") or settings.aws_secret_access_key or ""
    ).strip() or None
    session_token = (
        payload.get("_sns_session_token") or settings.aws_session_token or ""
    ).strip() or None
    region = (payload.get("_sns_region") or settings.aws_region or "us-east-1").strip()

    def _pub() -> None:
        client = boto3.client(
            "sns",
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            aws_session_token=session_token,
            region_name=region,
        )
        # Standard SNS topic ARN format:
        # arn:aws:sns:{region}:{account}:{topic_name}
        # Endpoint ARNs (mobile push/platform endpoints) contain ":endpoint/".
        if target.startswith("arn:") and ":sns:" in target and ":endpoint/" not in target:
            client.publish(TopicArn=target, Subject=title, Message=body)
        else:
            client.publish(TargetArn=target, Subject=title, Message=body)

    try:
        await asyncio.to_thread(_pub)
        return ChannelResult(ok=True, detail="sns_ok")
    except (ClientError, BotoCoreError, Exception) as exc:
        logger.exception("SNS publish failed")
        return ChannelResult(ok=False, detail=str(exc)[:500])
