from __future__ import annotations

import boto3
from botocore.exceptions import ClientError
from config import settings

from services.email_service import EmailService


def get_ses_quota() -> dict:
    ses_client = boto3.client(
        "ses",
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
        region_name=settings.aws_region,
    )
    response = ses_client.get_send_quota()
    return {
        "max_24_hour_send": response["Max24HourSend"],
        "sent_last_24_hours": response["SentLast24Hours"],
        "sending_rate": response["MaxSendRate"],
        "remaining_quota": response["Max24HourSend"] - response["SentLast24Hours"],
    }


def verify_email(email_service: EmailService, email: str) -> dict:
    ok = email_service.verify_email_address(email)
    if not ok:
        raise ValueError("Failed to send verification email")
    return {"message": f"Verification email sent to {email}"}


def get_verified_emails() -> dict:
    ses_client = boto3.client(
        "ses",
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
        region_name=settings.aws_region,
    )
    try:
        response = ses_client.list_verified_email_addresses()
        return {"verified_emails": response["VerifiedEmailAddresses"]}
    except ClientError as e:
        if e.response["Error"]["Code"] == "AccessDenied":
            return {
                "verified_emails": [],
                "message": (
                    "No permission to list verified emails. "
                    "Please verify the AWS IAM permissions."
                ),
            }
        raise
