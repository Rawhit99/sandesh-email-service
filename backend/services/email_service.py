import boto3
import asyncio
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from botocore.exceptions import ClientError, BotoCoreError
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import Optional, List, Dict, Any
from datetime import datetime

from models.models import Notification, EmailTemplate, AuditLog
from models.schemas import NotificationCreate, NotificationResponse, StatsResponse, TemplateCreate, TemplateResponse
from config import settings
from services.template_service import TemplateService

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.template_service = TemplateService()
        
        # Initialize AWS SES client
        self.ses_client = boto3.client(
            'ses',
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            region_name=settings.aws_region
        )
        
    def get_notifications(
        self, 
        db: Session, 
        status: Optional[str] = None,
        template_id: Optional[str] = None,
        email: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[NotificationResponse]:
        """Get notifications with optional filtering"""
        query = db.query(Notification)
        
        if status and status.lower() != "all":
            query = query.filter(Notification.status == status)
        if template_id:
            query = query.filter(Notification.template_id == template_id)
        if email:
            query = query.filter(Notification.email.ilike(f"%{email}%"))
            
        notifications = query.order_by(
            Notification.executed_at.desc()
        ).offset(offset).limit(limit).all()
        
        return [NotificationResponse.from_orm(notif) for notif in notifications]
    
    def get_notification_by_id(self, db: Session, notification_id: int) -> Optional[NotificationResponse]:
        """Get specific notification by ID"""
        notification = db.query(Notification).filter(Notification.id == notification_id).first()
        return NotificationResponse.from_orm(notification) if notification else None
    
    def create_notification(self, db: Session, notification: NotificationCreate) -> NotificationResponse:
        """Create a new notification"""
        # Validate template exists
        template = db.query(EmailTemplate).filter(
            EmailTemplate.template_id == notification.template_id
        ).first()
        
        if not template:
            raise ValueError(f"Template with ID '{notification.template_id}' not found")
        
        db_notification = Notification(
            template_id=notification.template_id,
            email=notification.email,
            payload=notification.payload,
            status="pending"
        )
        
        db.add(db_notification)
        db.commit()
        db.refresh(db_notification)
        
        return NotificationResponse.from_orm(db_notification)
    
    def update_notification_status(
        self, 
        db: Session, 
        notification_id: int, 
        status: str, 
        error_message: Optional[str] = None
    ) -> Optional[NotificationResponse]:
        """Update notification status"""
        notification = db.query(Notification).filter(Notification.id == notification_id).first()
        
        if not notification:
            return None
            
        notification.status = status
        if error_message:
            notification.error_message = error_message
            
        db.commit()
        db.refresh(notification)
        
        return NotificationResponse.from_orm(notification)
    
    def get_notification_stats(self, db: Session) -> StatsResponse:
        """Get notification statistics"""
        total = db.query(Notification).count()
        success_count = db.query(Notification).filter(Notification.status == "success").count()
        failed_count = db.query(Notification).filter(Notification.status == "failed").count()
        pending_count = db.query(Notification).filter(Notification.status == "pending").count()
        total_templates = db.query(EmailTemplate).count()
        
        # Get recent notifications
        recent_notifications = db.query(Notification).order_by(
            Notification.executed_at.desc()
        ).limit(5).all()
        
        return StatsResponse(
            total_notifications=total,
            success_count=success_count,
            failed_count=failed_count,
            pending_count=pending_count,
            total_templates=total_templates,
            recent_notifications=[NotificationResponse.from_orm(n) for n in recent_notifications]
        )
    
    async def send_email_async(self, db: Session, notification_id: int):
        """Send email asynchronously using configured provider"""
        try:
            notification = db.query(Notification).filter(Notification.id == notification_id).first()
            if not notification:
                logger.error(f"Notification {notification_id} not found")
                return
            
            # Get template
            template = db.query(EmailTemplate).filter(
                EmailTemplate.template_id == notification.template_id
            ).first()
            
            if not template:
                logger.error(f"Template {notification.template_id} not found")
                self.update_notification_status(
                    db, notification_id, "failed", 
                    f"Template {notification.template_id} not found"
                )
                return
            
            # Render email content
            try:
                rendered_subject = self.template_service.render_template(template.subject, notification.payload)
                rendered_content = self.template_service.render_template(template.content, notification.payload)
            except Exception as e:
                logger.error(f"Error rendering template: {str(e)}")
                self.update_notification_status(
                    db, notification_id, "failed",
                    f"Error rendering template: {str(e)}"
                )
                return
            
            # Send email via configured provider
            try:
                cc_emails = notification.payload.get('cc_emails', [])
                logger.info(f"CC emails from payload: {cc_emails}")
                logger.info(f"Full notification payload: {notification.payload}")
                if settings.email_provider.lower() == "smtp":
                    success, message_id, error = await self._send_smtp_email(
                        to_email=notification.email,
                        subject=rendered_subject,
                        content=rendered_content,
                        cc_emails=cc_emails
                    )
                else:  # Default to SES
                    success, message_id, error = await self._send_ses_email(
                        to_email=notification.email,
                        subject=rendered_subject,
                        content=rendered_content,
                        cc_emails=cc_emails
                    )
                
                if success:
                    notification.payload['message_id'] = message_id
                    db.commit()
                    self.update_notification_status(db, notification_id, "success")
                    
                    # Update audit log status
                    audit_log = db.query(AuditLog).filter(
                        AuditLog.email_to == notification.email,
                        AuditLog.template_id == notification.template_id
                    ).order_by(AuditLog.created_at.desc()).first()
                    
                    if audit_log:
                        audit_log.status = "success"
                        db.commit()
                else:
                    self.update_notification_status(
                        db, notification_id, "failed", error or "Email sending failed"
                    )
                    
                    # Update audit log status
                    audit_log = db.query(AuditLog).filter(
                        AuditLog.email_to == notification.email,
                        AuditLog.template_id == notification.template_id
                    ).order_by(AuditLog.created_at.desc()).first()
                    
                    if audit_log:
                        audit_log.status = "failed"
                        audit_log.error_message = error or "Email sending failed"
                        db.commit()
            except Exception as e:
                logger.error(f"Error sending email: {str(e)}")
                self.update_notification_status(
                    db, notification_id, "failed",
                    f"Error sending email: {str(e)}"
                )
                
                # Update audit log status
                notification = db.query(Notification).filter(Notification.id == notification_id).first()
                if notification:
                    audit_log = db.query(AuditLog).filter(
                        AuditLog.email_to == notification.email,
                        AuditLog.template_id == notification.template_id
                    ).order_by(AuditLog.created_at.desc()).first()
                    
                    if audit_log:
                        audit_log.status = "failed"
                        audit_log.error_message = f"Error sending email: {str(e)}"
                        db.commit()
        except Exception as e:
            logger.error(f"Unexpected error in send_email_async: {str(e)}")
            self.update_notification_status(
                db, notification_id, "failed",
                f"Unexpected error: {str(e)}"
            )
            
            # Update audit log status
            notification = db.query(Notification).filter(Notification.id == notification_id).first()
            if notification:
                audit_log = db.query(AuditLog).filter(
                    AuditLog.email_to == notification.email,
                    AuditLog.template_id == notification.template_id
                ).order_by(AuditLog.created_at.desc()).first()
                
                if audit_log:
                    audit_log.status = "failed"
                    audit_log.error_message = f"Unexpected error: {str(e)}"
                    db.commit()
    
    async def _send_smtp_email(
        self, 
        to_email: str, 
        subject: str, 
        content: str, 
        cc_emails: Optional[List[str]] = None
    ) -> tuple[bool, Optional[str], Optional[str]]:
        """Send email using SMTP"""
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = settings.smtp_sender_email
            msg['To'] = to_email
            
            if cc_emails:
                msg['Cc'] = ', '.join(cc_emails)
            
            # Attach HTML content
            html_part = MIMEText(content, 'html')
            msg.attach(html_part)
            
            # Connect to SMTP server
            if settings.smtp_use_ssl:
                server = smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port)
            else:
                server = smtplib.SMTP(settings.smtp_host, settings.smtp_port)
                if settings.smtp_use_tls:
                    server.starttls()
            
            # Login
            server.login(settings.smtp_username, settings.smtp_password)
            
            # Send email
            recipients = [to_email]
            if cc_emails:
                recipients.extend(cc_emails)
            
            server.sendmail(settings.smtp_sender_email, recipients, msg.as_string())
            server.quit()
            
            # Generate a simple message ID for SMTP
            message_id = f"smtp_{int(datetime.utcnow().timestamp())}"
            
            logger.info(f"SMTP email sent successfully to {to_email}. MessageId: {message_id}")
            return True, message_id, None
            
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP Authentication Error: {str(e)}")
            return False, None, f"SMTP Authentication Error: {str(e)}"
            
        except smtplib.SMTPException as e:
            logger.error(f"SMTP Error: {str(e)}")
            return False, None, f"SMTP Error: {str(e)}"
            
        except Exception as e:
            logger.error(f"Unexpected SMTP error: {str(e)}")
            return False, None, f"Unexpected error: {str(e)}"
    
    async def _send_ses_email(
        self, 
        to_email: str, 
        subject: str, 
        content: str, 
        cc_emails: Optional[List[str]] = None
    ) -> tuple[bool, Optional[str], Optional[str]]:
        """Send email using AWS SES"""
        try:
            # Prepare destination
            destination = {'ToAddresses': [to_email]}
            if cc_emails:
                destination['CcAddresses'] = cc_emails
            
            # Prepare message
            message = {
                'Subject': {
                    'Data': subject,
                    'Charset': 'UTF-8'
                },
                'Body': {
                    'Html': {
                        'Data': content,
                        'Charset': 'UTF-8'
                    }
                }
            }
            
            # Send email
            kwargs = {
                'Source': settings.ses_sender_email,
                'Destination': destination,
                'Message': message
            }
            
            # Add configuration set if specified
            if settings.ses_configuration_set:
                kwargs['ConfigurationSetName'] = settings.ses_configuration_set
            
            response = self.ses_client.send_email(**kwargs)
            message_id = response['MessageId']
            
            logger.info(f"Email sent successfully to {to_email}. MessageId: {message_id}")
            return True, message_id, None
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"SES ClientError ({error_code}): {error_message}")
            return False, None, f"SES Error: {error_code} - {error_message}"
            
        except BotoCoreError as e:
            logger.error(f"SES BotoCoreError: {str(e)}")
            return False, None, f"SES Connection Error: {str(e)}"
            
        except Exception as e:
            logger.error(f"Unexpected SES error: {str(e)}")
            return False, None, f"Unexpected error: {str(e)}"
    
    async def retry_notification(self, db: Session, notification_id: int) -> bool:
        """Retry a failed notification"""
        try:
            notification = db.query(Notification).filter(Notification.id == notification_id).first()
            if not notification:
                return False
            
            # Reset status to pending
            notification.status = "pending"
            db.commit()
            
            # Trigger async email sending
            await self.send_email_async(db, notification_id)
            return True
        except Exception as e:
            logger.error(f"Error retrying notification {notification_id}: {str(e)}")
            return False
    
    def bulk_create_notifications(
        self, 
        db: Session, 
        template_id: str, 
        recipients: List[Dict[str, Any]]
    ) -> List[NotificationResponse]:
        """Create multiple notifications at once"""
        # Validate template exists
        template = db.query(EmailTemplate).filter(EmailTemplate.template_id == template_id).first()
        if not template:
            raise ValueError(f"Template with ID '{template_id}' not found")
        
        notifications = []
        for recipient in recipients:
            db_notification = Notification(
                template_id=template_id,
                email=recipient['email'],
                payload=recipient.get('payload', {}),
                status="pending"
            )
            db.add(db_notification)
            notifications.append(db_notification)
        
        db.commit()
        
        # Refresh all notifications
        for notif in notifications:
            db.refresh(notif)
        
        return [NotificationResponse.from_orm(notif) for notif in notifications]
    
    def get_ses_send_quota(self) -> Dict[str, Any]:
        """Get SES sending quota and statistics"""
        try:
            quota_response = self.ses_client.get_send_quota()
            stats_response = self.ses_client.get_send_statistics()
            
            return {
                "max_24_hour": quota_response.get('Max24HourSend', 0),
                "max_send_rate": quota_response.get('MaxSendRate', 0),
                "sent_last_24_hours": quota_response.get('SentLast24Hours', 0),
                "send_data_points": stats_response.get('SendDataPoints', [])
            }
        except Exception as e:
            logger.error(f"Error getting SES quota: {str(e)}")
            return {"error": str(e)}
    
    def verify_email_address(self, email: str) -> bool:
        """Verify an email address with SES"""
        try:
            self.ses_client.verify_email_identity(EmailAddress=email)
            logger.info(f"Verification email sent to {email}")
            return True
        except Exception as e:
            logger.error(f"Error verifying email {email}: {str(e)}")
            return False
    
    def get_verified_emails(self) -> List[str]:
        """Get list of verified email addresses"""
        try:
            response = self.ses_client.list_verified_email_addresses()
            return response.get('VerifiedEmailAddresses', [])
        except Exception as e:
            logger.error(f"Error getting verified emails: {str(e)}")
            return []
    
    def get_email_settings(self) -> Dict[str, Any]:
        """Get current email provider settings"""
        if settings.email_provider.lower() == "smtp":
            return {
                "email_provider": "smtp",
                "smtp_host": settings.smtp_host,
                "smtp_port": settings.smtp_port,
                "smtp_username": settings.smtp_username,
                "smtp_sender_email": settings.smtp_sender_email,
                "smtp_use_tls": settings.smtp_use_tls,
                "smtp_use_ssl": settings.smtp_use_ssl
            }
        else:
            return {
                "email_provider": "ses",
                "aws_access_key_id": settings.aws_access_key_id,
                "aws_region": settings.aws_region,
                "ses_sender_email": settings.ses_sender_email,
                "ses_configuration_set": settings.ses_configuration_set
            }
    
    def update_email_settings(self, new_settings: Dict[str, Any]) -> bool:
        """Update email provider settings"""
        try:
            provider = new_settings.get('email_provider', 'ses')
            
            if provider.lower() == "smtp":
                # Test SMTP settings
                if not self._test_smtp_settings(new_settings):
                    return False
                
                # Update SMTP settings
                settings.email_provider = "smtp"
                settings.smtp_host = new_settings.get('smtp_host')
                settings.smtp_port = int(new_settings.get('smtp_port', 587))
                settings.smtp_username = new_settings.get('smtp_username')
                settings.smtp_password = new_settings.get('smtp_password')
                settings.smtp_use_tls = new_settings.get('smtp_use_tls', True)
                settings.smtp_use_ssl = new_settings.get('smtp_use_ssl', False)
                settings.smtp_sender_email = new_settings.get('smtp_sender_email')
                
            else:
                # Test SES settings
                if not self._test_ses_settings(new_settings):
                    return False
                
                # Update SES settings
                settings.email_provider = "ses"
                settings.aws_access_key_id = new_settings.get('aws_access_key_id')
                settings.aws_secret_access_key = new_settings.get('aws_secret_access_key')
                settings.aws_region = new_settings.get('aws_region')
                settings.ses_sender_email = new_settings.get('ses_sender_email')
                settings.ses_configuration_set = new_settings.get('ses_configuration_set')
                
                # Reinitialize the SES client with new settings
                self.ses_client = boto3.client(
                    'ses',
                    aws_access_key_id=settings.aws_access_key_id,
                    aws_secret_access_key=settings.aws_secret_access_key,
                    region_name=settings.aws_region
                )
            
            return True
        except Exception as e:
            logger.error(f"Error updating email settings: {str(e)}")
            return False
    
    def _test_smtp_settings(self, test_settings: Dict[str, Any]) -> bool:
        """Test SMTP settings with provided credentials"""
        try:
            host = test_settings.get('smtp_host')
            port = int(test_settings.get('smtp_port', 587))
            username = test_settings.get('smtp_username')
            password = test_settings.get('smtp_password')
            use_tls = test_settings.get('smtp_use_tls', True)
            use_ssl = test_settings.get('smtp_use_ssl', False)
            
            if use_ssl:
                server = smtplib.SMTP_SSL(host, port)
            else:
                server = smtplib.SMTP(host, port)
                if use_tls:
                    server.starttls()
            
            server.login(username, password)
            server.quit()
            return True
        except Exception as e:
            logger.error(f"Error testing SMTP settings: {str(e)}")
            return False
    
    def _test_ses_settings(self, test_settings: Dict[str, Any]) -> bool:
        """Test AWS SES settings with provided credentials"""
        try:
            test_client = boto3.client(
                'ses',
                aws_access_key_id=test_settings.get('aws_access_key_id'),
                aws_secret_access_key=test_settings.get('aws_secret_access_key'),
                region_name=test_settings.get('aws_region')
            )
            
            # Test the connection by getting send quota
            test_client.get_send_quota()
            return True
        except Exception as e:
            logger.error(f"Error testing SES settings: {str(e)}")
            return False
    
    def test_email_settings(self, test_settings: Dict[str, Any]) -> bool:
        """Test email settings with provided credentials"""
        provider = test_settings.get('email_provider', 'ses')
        
        if provider.lower() == "smtp":
            return self._test_smtp_settings(test_settings)
        else:
            return self._test_ses_settings(test_settings)