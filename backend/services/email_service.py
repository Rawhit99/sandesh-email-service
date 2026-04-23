import base64
import logging
import smtplib
from datetime import datetime
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr, parseaddr
from typing import Any, Dict, List, Optional

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from config import settings
from models.models import (
    AuditLog,
    EmailTemplate,
    IntegrationCredential,
    Notification,
    User,
)
from models.schema_domains.notifications import (
    NotificationCreate,
    NotificationResponse,
    StatsResponse,
)
from sandesh.application.aux_delivery import deliver_auxiliary_channels
from sandesh.infrastructure.queue.publisher import (
    enqueue_email_delivery,
    is_queue_enabled,
)
from sqlalchemy.orm import Session

from services.template_service import (
    TemplateService,
    resolve_email_template_row,
)

logger = logging.getLogger(__name__)


def _resolve_user_email_delivery(
    db: Session, user_id: Optional[int]
) -> Optional[Dict[str, Any]]:
    """Resolve per-user email config from settings + default credentials."""
    if user_id is None:
        return None
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None
    base_cfg = (
        user.email_delivery_settings
        if isinstance(user.email_delivery_settings, dict)
        else {}
    )
    merged: Dict[str, Any] = dict(base_cfg)

    preferred_provider = (
        str(merged.get("email_provider") or settings.email_provider or "ses")
        .lower()
        .strip()
    )
    default_creds = (
        db.query(IntegrationCredential)
        .filter(
            IntegrationCredential.user_id == user_id,
            IntegrationCredential.is_default.is_(True),
            IntegrationCredential.channel.in_(["aws_ses", "smtp"]),
        )
        .all()
    )

    by_channel: Dict[str, Dict[str, Any]] = {}
    for cred in default_creds:
        cfg = dict(cred.config or {})
        channel = str(cred.channel or "").strip()
        if not channel:
            continue
        by_channel[channel] = cfg

    chosen_channel: Optional[str] = None
    if preferred_provider == "smtp" and "smtp" in by_channel:
        chosen_channel = "smtp"
    elif preferred_provider == "ses" and "aws_ses" in by_channel:
        chosen_channel = "aws_ses"
    elif "aws_ses" in by_channel:
        chosen_channel = "aws_ses"
    elif "smtp" in by_channel:
        chosen_channel = "smtp"

    if not chosen_channel:
        if merged.get("email_provider"):
            return merged
        return None

    cfg = by_channel[chosen_channel]

    def pick(*keys: str) -> Optional[str]:
        for key in keys:
            value = cfg.get(key)
            if value is None:
                continue
            text = str(value).strip()
            if text:
                return text
        return None

    if chosen_channel == "aws_ses":
        merged["email_provider"] = "ses"
        merged["aws_access_key_id"] = pick(
            "aws_access_key_id",
            "access_key_id",
            "key_id",
        ) or merged.get("aws_access_key_id")
        merged["aws_secret_access_key"] = pick(
            "aws_secret_access_key",
            "secret_access_key",
            "secret_key",
        ) or merged.get("aws_secret_access_key")
        merged["aws_session_token"] = pick(
            "aws_session_token",
            "session_token",
        ) or merged.get("aws_session_token")
        merged["aws_region"] = pick(
            "aws_region",
            "region",
        ) or merged.get("aws_region")
        merged["ses_sender_email"] = pick(
            "ses_sender_email",
            "sender_email",
            "from_email",
            "email_from",
        ) or merged.get("ses_sender_email")
        merged["ses_configuration_set"] = pick(
            "ses_configuration_set",
            "configuration_set",
        ) or merged.get("ses_configuration_set")
    else:
        merged["email_provider"] = "smtp"
        merged["smtp_host"] = pick("smtp_host", "host") or merged.get(
            "smtp_host"
        )
        merged["smtp_port"] = pick("smtp_port", "port") or merged.get(
            "smtp_port"
        )
        merged["smtp_username"] = pick(
            "smtp_username",
            "username",
            "user",
        ) or merged.get("smtp_username")
        merged["smtp_password"] = pick(
            "smtp_password",
            "password",
            "pass",
        ) or merged.get("smtp_password")
        merged["smtp_sender_email"] = pick(
            "smtp_sender_email",
            "sender_email",
            "from_email",
            "email_from",
        ) or merged.get("smtp_sender_email")
        merged["smtp_use_tls"] = cfg.get(
            "smtp_use_tls", merged.get("smtp_use_tls")
        )
        merged["smtp_use_ssl"] = cfg.get(
            "smtp_use_ssl", merged.get("smtp_use_ssl")
        )

    return merged


def _optional_str(*candidates: Any) -> Optional[str]:
    for v in candidates:
        if v is None:
            continue
        t = str(v).strip()
        if t:
            return t
    return None


def _coerce_attachment_list(raw: Any) -> List[Dict[str, Any]]:
    """Build send-ready attachment dicts from ORM JSON."""
    if not raw or not isinstance(raw, list):
        return []
    out: List[Dict[str, Any]] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        b64 = item.get("content_base64") or item.get("contentBase64")
        if not b64 or not isinstance(b64, str):
            continue
        out.append(
            {
                "filename": str(item.get("filename") or "attachment"),
                "content_base64": b64,
                "mime_type": str(
                    item.get("mime_type")
                    or item.get("mimeType")
                    or "application/octet-stream"
                ),
            }
        )
    return out


def _mime_attachment_part(item: Dict[str, Any]) -> MIMEBase:
    mt = (item.get("mime_type") or "application/octet-stream").strip().lower()
    if "/" in mt:
        main, sub = mt.split("/", 1)
        main = (main or "application").strip() or "application"
        sub = (sub or "octet-stream").strip() or "octet-stream"
    else:
        main, sub = "application", "octet-stream"
    part = MIMEBase(main, sub)
    part.set_payload(base64.b64decode(item["content_base64"]))
    encoders.encode_base64(part)
    part.add_header(
        "Content-Disposition",
        "attachment",
        filename=item.get("filename", "attachment.bin"),
    )
    return part


class EmailService:
    def __init__(self):
        self.template_service = TemplateService()

        # Initialize AWS SES client
        self.ses_client = boto3.client(
            "ses",
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            region_name=settings.aws_region,
        )

    def get_notifications(
        self,
        db: Session,
        status: Optional[str] = None,
        template_id: Optional[str] = None,
        email: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
        scope_user_id: Optional[int] = None,
    ) -> List[NotificationResponse]:
        """Get notifications with optional filtering for tenant-owned rows."""
        query = db.query(Notification)
        if scope_user_id is not None:
            query = query.filter(Notification.user_id == scope_user_id)

        if status and status.lower() != "all":
            sl = status.lower()
            if sl == "pending":
                query = query.filter(
                    Notification.status.in_(["pending", "queued", "running"])
                )
            else:
                query = query.filter(Notification.status == sl)
        if template_id:
            query = query.filter(Notification.template_id == template_id)
        if email:
            query = query.filter(Notification.email.ilike(f"%{email}%"))

        notifications = (
            query.order_by(Notification.executed_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        return [
            NotificationResponse.from_orm(notif) for notif in notifications
        ]

    def get_notification_by_id(
        self,
        db: Session,
        notification_id: int,
        scope_user_id: Optional[int] = None,
    ) -> Optional[NotificationResponse]:
        """Get notification by ID with optional tenant ownership check."""
        q = db.query(Notification).filter(Notification.id == notification_id)
        if scope_user_id is not None:
            q = q.filter(Notification.user_id == scope_user_id)
        notification = q.first()
        return (
            NotificationResponse.from_orm(notification)
            if notification
            else None
        )

    def create_notification(
        self, db: Session, notification: NotificationCreate
    ) -> NotificationResponse:
        """Create a new notification"""
        # Validate template exists
        template = resolve_email_template_row(
            db, notification.template_id, None
        )

        if not template:
            raise ValueError(
                f"Template with ID '{notification.template_id}' not found"
            )

        db_notification = Notification(
            template_id=notification.template_id,
            email=notification.email,
            payload=notification.payload,
            status="pending",
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
        error_message: Optional[str] = None,
        scope_user_id: Optional[int] = None,
    ) -> Optional[NotificationResponse]:
        """Update notification status with optional tenant ownership check."""
        q = db.query(Notification).filter(Notification.id == notification_id)
        if scope_user_id is not None:
            q = q.filter(Notification.user_id == scope_user_id)
        notification = q.first()

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
        success_count = (
            db.query(Notification)
            .filter(Notification.status == "success")
            .count()
        )
        failed_count = (
            db.query(Notification)
            .filter(Notification.status == "failed")
            .count()
        )
        pending_count = (
            db.query(Notification)
            .filter(Notification.status == "pending")
            .count()
        )
        total_templates = db.query(EmailTemplate).count()

        # Get recent notifications
        recent_notifications = (
            db.query(Notification)
            .order_by(Notification.executed_at.desc())
            .limit(5)
            .all()
        )

        return StatsResponse(
            total_notifications=total,
            success_count=success_count,
            failed_count=failed_count,
            pending_count=pending_count,
            total_templates=total_templates,
            recent_notifications=[
                NotificationResponse.from_orm(n) for n in recent_notifications
            ],
        )

    async def send_email_async(self, db: Session, notification_id: int):
        """Send email asynchronously using configured provider"""
        try:
            notification = (
                db.query(Notification)
                .filter(Notification.id == notification_id)
                .first()
            )
            if not notification:
                logger.error(f"Notification {notification_id} not found")
                return

            uid = getattr(notification, "user_id", None)
            template = resolve_email_template_row(
                db, notification.template_id, uid
            )

            if not template:
                logger.error(f"Template {notification.template_id} not found")
                self.update_notification_status(
                    db,
                    notification_id,
                    "failed",
                    f"Template {notification.template_id} not found",
                )
                return

            # Render email content
            try:
                rendered_subject = self.template_service.render_template(
                    template.subject, notification.payload
                )
                rendered_content = self.template_service.render_template(
                    template.content, notification.payload
                )
            except Exception as e:
                logger.error(f"Error rendering template: {str(e)}")
                self.update_notification_status(
                    db,
                    notification_id,
                    "failed",
                    f"Error rendering template: {str(e)}",
                )
                return

            # Send email via configured provider
            try:
                cc_emails = notification.payload.get("cc_emails", [])
                # Prefer ORM attachments to avoid duplicate payload merges.
                if notification.attachments:
                    attach_list = _coerce_attachment_list(
                        notification.attachments
                    )
                else:
                    attach_list = _coerce_attachment_list(
                        notification.payload.get("_attachments")
                    )
                tpl_attach = (
                    getattr(template, "default_attachments", None) or []
                )
                if tpl_attach:
                    attach_list = attach_list + _coerce_attachment_list(
                        list(tpl_attach)
                    )
                from_override = _optional_str(
                    notification.from_email_override,
                    notification.payload.get("_from_email"),
                )
                sender_name = _optional_str(
                    notification.sender_display_name,
                    notification.payload.get("_sender_name"),
                )
                logger.info(
                    (
                        "Send id=%s attachments=%s "
                        "from_override=%s sender_name=%s"
                    ),
                    notification_id,
                    len(attach_list),
                    bool(from_override),
                    bool(sender_name),
                )
                logger.info(f"CC emails from payload: {cc_emails}")
                logger.info(
                    f"Full notification payload: {notification.payload}"
                )
                mail_cfg = _resolve_user_email_delivery(db, uid)
                provider = (
                    str(mail_cfg.get("email_provider") or "ses")
                    .lower()
                    .strip()
                    if mail_cfg
                    else settings.email_provider.lower()
                )
                if provider == "smtp":
                    success, message_id, error = await self._send_smtp_email(
                        to_email=notification.email,
                        subject=rendered_subject,
                        content=rendered_content,
                        cc_emails=cc_emails,
                        from_email=from_override,
                        sender_name=sender_name,
                        attachments=attach_list,
                        mail_cfg=mail_cfg,
                    )
                else:
                    success, message_id, error = await self._send_ses_email(
                        to_email=notification.email,
                        subject=rendered_subject,
                        content=rendered_content,
                        cc_emails=cc_emails,
                        source_email=from_override,
                        sender_name=sender_name,
                        attachments=attach_list,
                        mail_cfg=mail_cfg,
                    )

                if success:
                    notification.payload["message_id"] = message_id
                    db.commit()
                    self.update_notification_status(
                        db, notification_id, "success"
                    )

                    # Update audit log status
                    audit_log = (
                        db.query(AuditLog)
                        .filter(
                            AuditLog.email_to == notification.email,
                            AuditLog.template_id == notification.template_id,
                        )
                        .order_by(AuditLog.created_at.desc())
                        .first()
                    )

                    if audit_log:
                        audit_log.status = "success"
                        db.commit()

                    db.refresh(notification)
                    await deliver_auxiliary_channels(
                        db, notification, rendered_subject, rendered_content
                    )
                else:
                    self.update_notification_status(
                        db,
                        notification_id,
                        "failed",
                        error or "Email sending failed",
                    )

                    # Update audit log status
                    audit_log = (
                        db.query(AuditLog)
                        .filter(
                            AuditLog.email_to == notification.email,
                            AuditLog.template_id == notification.template_id,
                        )
                        .order_by(AuditLog.created_at.desc())
                        .first()
                    )

                    if audit_log:
                        audit_log.status = "failed"
                        audit_log.error_message = (
                            error or "Email sending failed"
                        )
                        db.commit()
            except Exception as e:
                logger.error(f"Error sending email: {str(e)}")
                self.update_notification_status(
                    db,
                    notification_id,
                    "failed",
                    f"Error sending email: {str(e)}",
                )

                # Update audit log status
                notification = (
                    db.query(Notification)
                    .filter(Notification.id == notification_id)
                    .first()
                )
                if notification:
                    audit_log = (
                        db.query(AuditLog)
                        .filter(
                            AuditLog.email_to == notification.email,
                            AuditLog.template_id == notification.template_id,
                        )
                        .order_by(AuditLog.created_at.desc())
                        .first()
                    )

                    if audit_log:
                        audit_log.status = "failed"
                        audit_log.error_message = (
                            f"Error sending email: {str(e)}"
                        )
                        db.commit()
        except Exception as e:
            logger.error(f"Unexpected error in send_email_async: {str(e)}")
            self.update_notification_status(
                db, notification_id, "failed", f"Unexpected error: {str(e)}"
            )

            # Update audit log status
            notification = (
                db.query(Notification)
                .filter(Notification.id == notification_id)
                .first()
            )
            if notification:
                audit_log = (
                    db.query(AuditLog)
                    .filter(
                        AuditLog.email_to == notification.email,
                        AuditLog.template_id == notification.template_id,
                    )
                    .order_by(AuditLog.created_at.desc())
                    .first()
                )

                if audit_log:
                    audit_log.status = "failed"
                    audit_log.error_message = f"Unexpected error: {str(e)}"
                    db.commit()

    async def _send_smtp_email(
        self,
        to_email: str,
        subject: str,
        content: str,
        cc_emails: Optional[List[str]] = None,
        from_email: Optional[str] = None,
        sender_name: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
        mail_cfg: Optional[Dict[str, Any]] = None,
    ) -> tuple[bool, Optional[str], Optional[str]]:
        """Send email using SMTP with optional per-user config overrides."""
        try:

            def pick(key: str, fallback: Any) -> Any:
                if (
                    mail_cfg is not None
                    and key in mail_cfg
                    and mail_cfg.get(key) not in (None, "")
                ):
                    return mail_cfg.get(key)
                return fallback

            smtp_host = str(pick("smtp_host", settings.smtp_host))
            smtp_port = int(pick("smtp_port", settings.smtp_port))
            smtp_username = str(pick("smtp_username", settings.smtp_username))
            smtp_password = str(pick("smtp_password", settings.smtp_password))
            smtp_use_ssl = bool(pick("smtp_use_ssl", settings.smtp_use_ssl))
            smtp_use_tls = bool(pick("smtp_use_tls", settings.smtp_use_tls))
            envelope_from = from_email or str(
                pick("smtp_sender_email", settings.smtp_sender_email)
            )

            if attachments:
                msg = MIMEMultipart("mixed")
                msg["Subject"] = subject
                msg["To"] = to_email
                if sender_name:
                    msg["From"] = formataddr((sender_name, envelope_from))
                else:
                    msg["From"] = envelope_from
                if cc_emails:
                    msg["Cc"] = ", ".join(cc_emails)
                alt = MIMEMultipart("alternative")
                alt.attach(MIMEText(content, "html", "utf-8"))
                msg.attach(alt)
                for item in attachments:
                    msg.attach(_mime_attachment_part(item))
            else:
                msg = MIMEMultipart("alternative")
                msg["Subject"] = subject
                if sender_name:
                    msg["From"] = formataddr((sender_name, envelope_from))
                else:
                    msg["From"] = envelope_from
                msg["To"] = to_email
                if cc_emails:
                    msg["Cc"] = ", ".join(cc_emails)
                html_part = MIMEText(content, "html", "utf-8")
                msg.attach(html_part)

            if smtp_use_ssl:
                server = smtplib.SMTP_SSL(smtp_host, smtp_port)
            else:
                server = smtplib.SMTP(smtp_host, smtp_port)
                if smtp_use_tls:
                    server.starttls()

            server.login(smtp_username, smtp_password)

            recipients = [to_email]
            if cc_emails:
                recipients.extend(cc_emails)

            server.sendmail(envelope_from, recipients, msg.as_string())
            server.quit()

            message_id = f"smtp_{int(datetime.utcnow().timestamp())}"

            logger.info(
                "SMTP email sent successfully to %s. MessageId: %s",
                to_email,
                message_id,
            )
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
        cc_emails: Optional[List[str]] = None,
        source_email: Optional[str] = None,
        sender_name: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
        mail_cfg: Optional[Dict[str, Any]] = None,
    ) -> tuple[bool, Optional[str], Optional[str]]:
        """Send email using AWS SES (optional per-user mail_cfg)."""
        try:
            if mail_cfg:
                ses_client = boto3.client(
                    "ses",
                    aws_access_key_id=mail_cfg.get("aws_access_key_id")
                    or settings.aws_access_key_id,
                    aws_secret_access_key=mail_cfg.get("aws_secret_access_key")
                    or settings.aws_secret_access_key,
                    aws_session_token=mail_cfg.get("aws_session_token")
                    or settings.aws_session_token
                    or None,
                    region_name=mail_cfg.get("aws_region")
                    or settings.aws_region,
                )
                default_sender = (
                    mail_cfg.get("ses_sender_email")
                    or settings.ses_sender_email
                    or ""
                ).strip()
                config_set = (
                    mail_cfg.get("ses_configuration_set")
                    or settings.ses_configuration_set
                    or ""
                ).strip()
            else:
                ses_client = self.ses_client
                default_sender = (settings.ses_sender_email or "").strip()
                config_set = (settings.ses_configuration_set or "").strip()

            source = source_email or default_sender
            if sender_name:
                source = formataddr((sender_name, source))

            destination = {"ToAddresses": [to_email]}
            if cc_emails:
                destination["CcAddresses"] = cc_emails

            if attachments:
                root = MIMEMultipart("mixed")
                root["Subject"] = subject
                root["From"] = source
                root["To"] = to_email
                if cc_emails:
                    root["Cc"] = ", ".join(cc_emails)
                alt = MIMEMultipart("alternative")
                alt.attach(MIMEText(content, "html", "utf-8"))
                root.attach(alt)
                for item in attachments:
                    root.attach(_mime_attachment_part(item))
                raw = root.as_string()
                _, source_addr = parseaddr(source)
                source_addr = source_addr or default_sender
                destinations = [to_email] + (cc_emails or [])
                raw_kwargs: Dict[str, Any] = {
                    "Source": source_addr,
                    "Destinations": destinations,
                    "RawMessage": {"Data": raw},
                }
                if config_set:
                    raw_kwargs["ConfigurationSetName"] = config_set
                response = ses_client.send_raw_email(**raw_kwargs)
            else:
                message = {
                    "Subject": {"Data": subject, "Charset": "UTF-8"},
                    "Body": {"Html": {"Data": content, "Charset": "UTF-8"}},
                }
                kwargs = {
                    "Source": source,
                    "Destination": destination,
                    "Message": message,
                }
                if config_set:
                    kwargs["ConfigurationSetName"] = config_set
                response = ses_client.send_email(**kwargs)
            message_id = response["MessageId"]

            logger.info(
                "Email sent successfully to %s. MessageId: %s",
                to_email,
                message_id,
            )
            return True, message_id, None

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_message = e.response["Error"]["Message"]
            logger.error(f"SES ClientError ({error_code}): {error_message}")
            return False, None, f"SES Error: {error_code} - {error_message}"

        except BotoCoreError as e:
            logger.error(f"SES BotoCoreError: {str(e)}")
            return False, None, f"SES Connection Error: {str(e)}"

        except Exception as e:
            logger.error(f"Unexpected SES error: {str(e)}")
            return False, None, f"Unexpected error: {str(e)}"

    async def retry_notification(
        self,
        db: Session,
        notification_id: int,
        scope_user_id: Optional[int] = None,
    ) -> bool:
        """Retry a failed notification with optional tenant scoping."""
        try:
            q = db.query(Notification).filter(
                Notification.id == notification_id
            )
            if scope_user_id is not None:
                q = q.filter(Notification.user_id == scope_user_id)
            notification = q.first()
            if not notification:
                return False

            if is_queue_enabled():
                notification.status = "queued"
                db.commit()
                try:
                    if enqueue_email_delivery(notification_id):
                        return True
                except Exception:
                    logger.exception("Retry enqueue failed")
                if not settings.queue_inline_fallback:
                    notification.status = "failed"
                    notification.error_message = "Queue enqueue failed"
                    db.commit()
                    return False

            notification.status = "pending"
            db.commit()
            await self.send_email_async(db, notification_id)
            return True
        except Exception as e:
            logger.error(
                f"Error retrying notification {notification_id}: {str(e)}"
            )
            return False

    def bulk_create_notifications(
        self, db: Session, template_id: str, recipients: List[Dict[str, Any]]
    ) -> List[NotificationResponse]:
        """Create multiple notifications at once"""
        # Validate template exists
        template = resolve_email_template_row(db, template_id, None)
        if not template:
            raise ValueError(f"Template with ID '{template_id}' not found")

        notifications = []
        for recipient in recipients:
            db_notification = Notification(
                template_id=template_id,
                email=recipient["email"],
                payload=recipient.get("payload", {}),
                status="pending",
            )
            db.add(db_notification)
            notifications.append(db_notification)

        db.commit()

        # Refresh all notifications
        for notif in notifications:
            db.refresh(notif)

        return [
            NotificationResponse.from_orm(notif) for notif in notifications
        ]

    def get_ses_send_quota(self) -> Dict[str, Any]:
        """Get SES sending quota and statistics"""
        try:
            quota_response = self.ses_client.get_send_quota()
            stats_response = self.ses_client.get_send_statistics()

            return {
                "max_24_hour": quota_response.get("Max24HourSend", 0),
                "max_send_rate": quota_response.get("MaxSendRate", 0),
                "sent_last_24_hours": quota_response.get("SentLast24Hours", 0),
                "send_data_points": stats_response.get("SendDataPoints", []),
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
            return response.get("VerifiedEmailAddresses", [])
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
                "smtp_use_ssl": settings.smtp_use_ssl,
            }
        else:
            return {
                "email_provider": "ses",
                "aws_access_key_id": settings.aws_access_key_id,
                "aws_region": settings.aws_region,
                "ses_sender_email": settings.ses_sender_email,
                "ses_configuration_set": settings.ses_configuration_set,
            }

    def update_email_settings(self, new_settings: Dict[str, Any]) -> bool:
        """Update email provider settings"""
        try:
            provider = new_settings.get("email_provider", "ses")

            if provider.lower() == "smtp":
                # Test SMTP settings
                if not self._test_smtp_settings(new_settings):
                    return False

                # Update SMTP settings
                settings.email_provider = "smtp"
                settings.smtp_host = new_settings.get("smtp_host")
                settings.smtp_port = int(new_settings.get("smtp_port", 587))
                settings.smtp_username = new_settings.get("smtp_username")
                settings.smtp_password = new_settings.get("smtp_password")
                settings.smtp_use_tls = new_settings.get("smtp_use_tls", True)
                settings.smtp_use_ssl = new_settings.get("smtp_use_ssl", False)
                settings.smtp_sender_email = new_settings.get(
                    "smtp_sender_email"
                )

            else:
                # Test SES settings
                if not self._test_ses_settings(new_settings):
                    return False

                # Update SES settings
                settings.email_provider = "ses"
                settings.aws_access_key_id = new_settings.get(
                    "aws_access_key_id"
                )
                settings.aws_secret_access_key = new_settings.get(
                    "aws_secret_access_key"
                )
                settings.aws_region = new_settings.get("aws_region")
                settings.ses_sender_email = new_settings.get(
                    "ses_sender_email"
                )
                settings.ses_configuration_set = new_settings.get(
                    "ses_configuration_set"
                )

                # Reinitialize the SES client with new settings
                self.ses_client = boto3.client(
                    "ses",
                    aws_access_key_id=settings.aws_access_key_id,
                    aws_secret_access_key=settings.aws_secret_access_key,
                    region_name=settings.aws_region,
                )

            return True
        except Exception as e:
            logger.error(f"Error updating email settings: {str(e)}")
            return False

    def _test_smtp_settings(self, test_settings: Dict[str, Any]) -> bool:
        """Test SMTP settings with provided credentials"""
        try:
            host = test_settings.get("smtp_host")
            port = int(test_settings.get("smtp_port", 587))
            username = test_settings.get("smtp_username")
            password = test_settings.get("smtp_password")
            use_tls = test_settings.get("smtp_use_tls", True)
            use_ssl = test_settings.get("smtp_use_ssl", False)

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
                "ses",
                aws_access_key_id=test_settings.get("aws_access_key_id"),
                aws_secret_access_key=test_settings.get(
                    "aws_secret_access_key"
                ),
                region_name=test_settings.get("aws_region"),
            )

            # Test the connection by getting send quota
            test_client.get_send_quota()
            return True
        except Exception as e:
            logger.error(f"Error testing SES settings: {str(e)}")
            return False

    def test_email_settings(self, test_settings: Dict[str, Any]) -> bool:
        """Test email settings with provided credentials"""
        provider = test_settings.get("email_provider", "ses")

        if provider.lower() == "smtp":
            return self._test_smtp_settings(test_settings)
        else:
            return self._test_ses_settings(test_settings)
