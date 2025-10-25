import time
from fastapi import FastAPI, HTTPException, Depends, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional, List
import logging
from config import settings
from models.models import Base, engine, get_db, EmailTemplate, Notification, User, APIKey, AuditLog
from models.schemas import (
    NotificationCreate, NotificationResponse, NotificationUpdate,
    TemplateCreate, TemplateResponse, TemplateUpdate,
    StatsResponse, TemplatePreview, TemplateValidationRequest, NotificationSummary,
    UserCreate, UserResponse, LoginRequest, LoginResponse,
    APIKeyCreate, APIKeyResponse, APIKeyCreateResponse, AuditLogResponse
)
from services.email_service import EmailService
from services.template_service import TemplateService
from sqlalchemy import func
from datetime import datetime, timedelta
import boto3
from botocore.exceptions import ClientError
from middleware.auth import get_current_api_key, get_current_user_from_token
from middleware.auth_utils import verify_password, get_password_hash, create_access_token

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="Email Notification System API",
    description="API for managing email notifications and templates",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
email_service = EmailService()
template_service = TemplateService()

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "Email Notification System API is running"}

# Authentication endpoints
@app.post("/api/v1/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    # Check if username already exists
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        username=user_data.username,
        password_hash=hashed_password,
        organization_name=user_data.organization_name,
        is_active=True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user

@app.post("/api/v1/auth/login", response_model=LoginResponse)
async def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    """Login and get access token"""
    # Find user
    user = db.query(User).filter(User.username == credentials.username).first()
    
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(status_code=403, detail="User account is inactive")
    
    # Create access token
    access_token = create_access_token(data={"sub": user.username, "user_id": user.id})
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(
            id=user.id,
            username=user.username,
            organization_name=user.organization_name,
            is_active=user.is_active,
            created_at=user.created_at
        )
    )

@app.get("/api/v1/auth/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: dict = Depends(get_current_user_from_token)
):
    """Get current user information"""
    db = next(get_db())
    user = db.query(User).filter(User.username == current_user["sub"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# API Key Management endpoints
@app.post("/api/v1/api-keys", response_model=APIKeyCreateResponse)
async def create_api_key(
    api_key_data: APIKeyCreate,
    current_user: dict = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Create a new API key for the current user"""
    user = db.query(User).filter(User.username == current_user["sub"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Generate new API key
    new_key = APIKey.generate_key()
    key_hash = APIKey.hash_key(new_key)
    key_prefix = new_key[:20]  # First 20 chars for display
    
    # Create API key record
    api_key_obj = APIKey(
        user_id=user.id,
        key_hash=key_hash,
        key_prefix=key_prefix,
        is_active=True
    )
    db.add(api_key_obj)
    db.commit()
    db.refresh(api_key_obj)
    
    return APIKeyCreateResponse(
        id=api_key_obj.id,
        key=new_key,  # Return the actual key only once
        key_prefix=key_prefix,
        created_at=api_key_obj.created_at
    )

@app.get("/api/v1/api-keys", response_model=List[APIKeyResponse])
async def get_api_keys(
    current_user: dict = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Get all API keys for the current user"""
    user = db.query(User).filter(User.username == current_user["sub"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    api_keys = db.query(APIKey).filter(APIKey.user_id == user.id).all()
    return api_keys

@app.delete("/api/v1/api-keys/{key_id}")
async def delete_api_key(
    key_id: int,
    current_user: dict = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Delete an API key"""
    user = db.query(User).filter(User.username == current_user["sub"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    api_key = db.query(APIKey).filter(
        APIKey.id == key_id,
        APIKey.user_id == user.id
    ).first()
    
    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")
    
    db.delete(api_key)
    db.commit()
    
    return {"message": "API key deleted successfully"}

# Audit Log endpoints
@app.get("/api/v1/audit-logs", response_model=List[AuditLogResponse])
async def get_audit_logs(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Get all audit logs (including unauthenticated requests)"""
    # Get all audit logs, not just for the current user
    audit_logs = db.query(AuditLog).order_by(
        AuditLog.created_at.desc()
    ).offset(offset).limit(limit).all()
    
    return audit_logs

# Notification endpoints
@app.get("/api/v1/notifications", response_model=List[NotificationResponse])
async def get_notifications(
    status: Optional[str] = Query(None, description="Filter by status: pending, success, failed"),
    template_id: Optional[str] = Query(None, description="Filter by template ID"),
    email: Optional[str] = Query(None, description="Filter by email"),
    limit: int = Query(100, ge=1, le=1000, description="Number of notifications to return"),
    offset: int = Query(0, ge=0, description="Number of notifications to skip"),
    db: Session = Depends(get_db),
    # api_key: str = Depends(get_current_api_key)  # Commented out for testing
):
    """Get notifications with optional filtering"""
    try:
        notifications = email_service.get_notifications(
            db=db, status=status, template_id=template_id, 
            email=email, limit=limit, offset=offset
        )
        return notifications
    except Exception as e:
        logger.error(f"Error fetching notifications: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/notifications", response_model=NotificationResponse)
async def create_notification(
    notification: NotificationCreate,
    request: Request,
    db: Session = Depends(get_db),
    # api_key: str = Depends(get_current_api_key)  # Commented out for testing
):
    """Create a new notification"""
    try:
        logger.info(f"Creating notification with template_id: {notification.template_id}")
        
        # Get user from API key if provided
        user = None
        try:
            from middleware.auth import get_current_user_optional
            user = await get_current_user_optional(request, None, db)
        except:
            pass
        
        # First create the template if it doesn't exist
        template = db.query(EmailTemplate).filter(
            EmailTemplate.template_id == notification.template_id
        ).first()
        
        if not template:
            logger.info("Template not found, creating new template")
            try:
                # Create a new template
                template = EmailTemplate(
                    template_id=notification.template_id,
                    name=notification.template_id,  # Use template_id as name
                    subject=notification.subject or "No Subject",  # Use provided subject or default
                    content=notification.content or "",  # Use provided content or empty string
                    is_active=True
                )
                db.add(template)
                db.commit()
                db.refresh(template)
                logger.info("New template created successfully")
            except Exception as e:
                logger.error(f"Error creating template: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Error creating template: {str(e)}")
        
        # Now create the notification
        try:
            # Include cc_emails in payload if provided
            payload = notification.payload.copy()
            logger.info(f"Original payload: {notification.payload}")
            logger.info(f"CC emails from request: {notification.cc_emails}")
            if notification.cc_emails:
                payload['cc_emails'] = notification.cc_emails
                logger.info(f"Added CC emails to payload: {payload}")
            else:
                logger.info("No CC emails provided")
            
            db_notification = Notification(
                template_id=notification.template_id,
                email=notification.email,
                payload=payload,
                status="pending"
            )
            
            db.add(db_notification)
            db.commit()
            db.refresh(db_notification)
            logger.info(f"Notification created with ID: {db_notification.id}")
            
            # Create audit log entry
            audit_log = AuditLog(
                user_id=user.id if user else None,
                action="email_triggered",
                email_to=notification.email,
                template_id=notification.template_id,
                payload=notification.payload,
                status="pending",
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent")
            )
            db.add(audit_log)
            db.commit()
            
            # Trigger email sending asynchronously
            await email_service.send_email_async(db, db_notification.id)
            
            return NotificationResponse.from_orm(db_notification)
        except Exception as e:
            logger.error(f"Error creating notification: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error creating notification: {str(e)}")
            
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.put("/api/notifications/{notification_id}", response_model=NotificationResponse)
async def update_notification(
    notification_id: int,
    update_data: NotificationUpdate,
    db: Session = Depends(get_db)
):
    """Update notification status"""
    try:
        notification = email_service.update_notification_status(
            db=db, notification_id=notification_id, status=update_data.status
        )
        if not notification:
            raise HTTPException(status_code=404, detail="Notification not found")
        return notification
    except Exception as e:
        logger.error(f"Error updating notification: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/notifications/{notification_id}", response_model=NotificationResponse)
async def get_notification(
    notification_id: int,
    db: Session = Depends(get_db)
):
    """Get specific notification by ID"""
    try:
        notification = email_service.get_notification_by_id(db=db, notification_id=notification_id)
        if not notification:
            raise HTTPException(status_code=404, detail="Notification not found")
        return notification
    except Exception as e:
        logger.error(f"Error fetching notification: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Template endpoints
@app.get("/api/v1/templates", response_model=List[TemplateResponse])
async def get_templates(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    active_only: bool = Query(False, description="Filter to show only active templates"),
    db: Session = Depends(get_db)
):
    """Get all templates with optional filtering"""
    try:
        templates = template_service.get_templates(
            db=db, 
            limit=limit, 
            offset=offset, 
            active_only=active_only
        )
        return templates
    except Exception as e:
        logger.error(f"Error fetching templates: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/v1/templates/preview")
async def preview_template(
    template: TemplatePreview,
    db: Session = Depends(get_db)
):
    """Preview template with sample data"""
    try:
        preview = template_service.preview_template(template.content, template.variables)
        return {"preview": preview}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error previewing template: {str(e)}")
        raise HTTPException(status_code=500, detail="Error previewing template")

@app.post("/api/v1/templates/validate")
async def validate_template(
    template: TemplateCreate,
    db: Session = Depends(get_db)
):
    """Validate template syntax and variables"""
    try:
        # Extract variables from content and subject
        extracted_vars = TemplateCreate.extract_variables(template.content, template.subject)
        
        # Update template with extracted variables
        template.variables = extracted_vars
        
        validation = template_service.validate_template_syntax(template.content)
        return validation
    except Exception as e:
        logger.error(f"Error validating template: {str(e)}")
        raise HTTPException(status_code=500, detail="Error validating template")

@app.post("/api/v1/templates", response_model=TemplateResponse)
async def create_template(
    template: TemplateCreate,
    db: Session = Depends(get_db)
):
    """Create a new email template"""
    try:
        # Extract variables from content and subject
        extracted_vars = TemplateCreate.extract_variables(template.content, template.subject)
        
        # Update template with extracted variables
        template.variables = extracted_vars
        
        # Create the template
        return template_service.create_template(db, template)
    except Exception as e:
        logger.error(f"Error creating template: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/templates/{template_id}", response_model=TemplateResponse)
async def get_template(
    template_id: str,
    db: Session = Depends(get_db)
):
    """Get specific template by template_id"""
    try:
        template = template_service.get_template_by_id(db=db, template_id=template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        return template
    except Exception as e:
        logger.error(f"Error fetching template: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.put("/api/v1/templates/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: str,
    template: TemplateUpdate,
    db: Session = Depends(get_db)
):
    """Update an existing template"""
    try:
        existing_template = template_service.get_template_by_id(db=db, template_id=template_id)
        if not existing_template:
            raise HTTPException(status_code=404, detail="Template not found")
            
        db_template = template_service.update_template(db=db, template_id=template_id, template=template)
        return db_template
    except Exception as e:
        logger.error(f"Error updating template: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/templates/{template_id}")
async def delete_template(
    template_id: str,
    db: Session = Depends(get_db)
):
    """Delete a template"""
    try:
        success = template_service.delete_template(db=db, template_id=template_id)
        if not success:
            raise HTTPException(status_code=404, detail="Template not found")
        return {"message": "Template deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting template: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Stats endpoint
@app.get("/api/v1/stats", response_model=StatsResponse)
async def get_stats(db: Session = Depends(get_db)):
    """Get system statistics"""
    try:
        # Get total counts
        total_notifications = db.query(func.count(Notification.id)).scalar() or 0
        total_templates = db.query(func.count(EmailTemplate.id)).scalar() or 0
        
        # Get status counts
        status_counts = dict(db.query(
            Notification.status,
            func.count(Notification.id)
        ).group_by(Notification.status).all())
        
        # Get last 24 hours stats
        last_24h = datetime.utcnow() - timedelta(days=1)
        notifications_24h = db.query(func.count(Notification.id)).filter(
            Notification.created_at >= last_24h
        ).scalar() or 0
        
        # Get individual status counts
        success_count = status_counts.get('success', 0)
        failed_count = status_counts.get('failed', 0)
        pending_count = status_counts.get('pending', 0)
        
        # Calculate success rate
        success_rate = (success_count / total_notifications * 100) if total_notifications > 0 else 0
        
        # Get recent notifications (last 5)
        recent_notifications = db.query(Notification).order_by(
            Notification.created_at.desc()
        ).limit(5).all()
        
        return StatsResponse(
            total_notifications=total_notifications,
            total_templates=total_templates,
            notifications_24h=notifications_24h,
            success_rate=round(success_rate, 2),
            status_counts=status_counts,
            success_count=success_count,
            failed_count=failed_count,
            pending_count=pending_count,
            recent_notifications=[NotificationSummary.from_orm(n) for n in recent_notifications]
        )
    except Exception as e:
        logger.error(f"Error fetching stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching statistics: {str(e)}")

# Retry failed notifications
@app.post("/api/v1/notifications/{notification_id}/retry")
async def retry_notification(notification_id: int, db: Session = Depends(get_db)):
    """Retry a failed notification"""
    try:
        success = await email_service.retry_notification(db, notification_id)
        if success:
            return {"message": "Notification retry initiated successfully"}
        else:
            raise HTTPException(status_code=404, detail="Notification not found")
    except Exception as e:
        logger.error(f"Error retrying notification: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retry notification")

# SES endpoints
@app.get("/api/v1/ses/quota")
async def get_ses_quota(db: Session = Depends(get_db)):
    """Get AWS SES sending quota information"""
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
    except Exception as e:
        logger.error(f"Error fetching SES quota: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching SES quota information")

@app.post("/api/ses/verify-email")
async def verify_email_address(
    email: str = Query(..., description="Email address to verify"),
    db: Session = Depends(get_db)
):
    """Verify an email address with AWS SES"""
    try:
        success = email_service.verify_email_address(email)
        if success:
            return {"message": f"Verification email sent to {email}"}
        else:
            raise HTTPException(status_code=400, detail="Failed to send verification email")
    except Exception as e:
        logger.error(f"Error verifying email: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/verified-emails")
async def get_verified_emails(db: Session = Depends(get_db)):
    """Get list of verified email addresses in SES"""
    try:
        ses_client = boto3.client(
            'ses',
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            region_name=settings.aws_region
        )
        
        try:
            response = ses_client.list_verified_email_addresses()
            return {
                "verified_emails": response['VerifiedEmailAddresses']
            }
        except ClientError as e:
            if e.response['Error']['Code'] == 'AccessDenied':
                # Return empty list if user doesn't have permission
                return {
                    "verified_emails": [],
                    "message": "No permission to list verified emails. Please verify the AWS IAM permissions."
                }
            raise
    except Exception as e:
        logger.error(f"Error fetching verified emails: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail="Error fetching verified emails. Please check AWS credentials and permissions."
        )

# SES Settings endpoints
@app.get("/api/v1/settings/ses")
async def get_ses_settings(db: Session = Depends(get_db)):
    """Get AWS SES settings"""
    try:
        return {
            "aws_access_key_id": settings.aws_access_key_id,
            "aws_region": settings.aws_region,
            "ses_sender_email": settings.ses_sender_email,
            "ses_configuration_set": settings.ses_configuration_set
        }
    except Exception as e:
        logger.error(f"Error fetching SES settings: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching SES settings")

@app.post("/api/settings/ses")
async def update_ses_settings(
    settings: dict,
    db: Session = Depends(get_db)
):
    """Update AWS SES settings"""
    try:
        success = email_service.update_ses_settings(settings)
        if success:
            return {"message": "SES settings updated successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to update SES settings")
    except Exception as e:
        logger.error(f"Error updating SES settings: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update SES settings")

@app.post("/api/settings/ses/test")
async def test_ses_settings(
    settings: dict,
    db: Session = Depends(get_db)
):
    """Test AWS SES settings with provided credentials"""
    try:
        success = email_service.test_ses_settings(settings)
        if success:
            return {"message": "SES settings test successful"}
        else:
            raise HTTPException(status_code=400, detail="SES settings test failed")
    except Exception as e:
        logger.error(f"Error testing SES settings: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to test SES settings")

# Add these routes to handle the new email settings endpoints

@app.get("/api/v1/settings/email")
async def get_email_settings():
    """Get current email provider settings"""
    try:
        settings = email_service.get_email_settings()
        return {"success": True, "data": settings}
    except Exception as e:
        logger.error(f"Error getting email settings: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/v1/settings/email")
async def update_email_settings(settings: dict):
    """Update email provider settings"""
    try:
        success = email_service.update_email_settings(settings)
        if success:
            return {"success": True, "message": "Settings updated successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to update settings")
    except Exception as e:
        logger.error(f"Error updating email settings: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/settings/email/test")
async def test_email_settings(settings: dict):
    """Test email provider settings"""
    try:
        success = email_service.test_email_settings(settings)
        if success:
            return {"success": True, "message": "Test successful"}
        else:
            raise HTTPException(status_code=400, detail="Test failed")
    except Exception as e:
        logger.error(f"Error testing email settings: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True
    )