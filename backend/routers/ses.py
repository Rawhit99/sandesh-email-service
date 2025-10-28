import boto3
from botocore.exceptions import ClientError
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from models.models import get_db
from config import settings
from services.email_service import EmailService

router = APIRouter(prefix="/api", tags=["ses"])
email_service = EmailService()

@router.get("/v1/ses/quota")
async def get_ses_quota(db: Session = Depends(get_db)):
    try:
        ses_client = boto3.client(
            'ses',
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            region_name=settings.aws_region
        )
        response = ses_client.get_send_quota()
        return {
            "max_24_hour_send": response['Max24HourSend'],
            "sent_last_24_hours": response['SentLast24Hours'],
            "sending_rate": response['MaxSendRate'],
            "remaining_quota": response['Max24HourSend'] - response['SentLast24Hours']
        }
    except Exception:
        raise HTTPException(status_code=500, detail="Error fetching SES quota information")

@router.post("/ses/verify-email")
async def verify_email_address(email: str = Query(..., description="Email address to verify"), db: Session = Depends(get_db)):
    try:
        success = email_service.verify_email_address(email)
        if success:
            return {"message": f"Verification email sent to {email}"}
        else:
            raise HTTPException(status_code=400, detail="Failed to send verification email")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/v1/verified-emails")
async def get_verified_emails(db: Session = Depends(get_db)):
    try:
        ses_client = boto3.client(
            'ses',
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            region_name=settings.aws_region
        )
        try:
            response = ses_client.list_verified_email_addresses()
            return {"verified_emails": response['VerifiedEmailAddresses']}
        except ClientError as e:
            if e.response['Error']['Code'] == 'AccessDenied':
                return {"verified_emails": [], "message": "No permission to list verified emails. Please verify the AWS IAM permissions."}
            raise
    except Exception:
        raise HTTPException(status_code=500, detail="Error fetching verified emails. Please check AWS credentials and permissions.")


