import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = os.getenv("DATABASE_URL", "")
    api_host: str = os.getenv("API_HOST", "0.0.0.0")
    api_port: int = int(os.getenv("API_PORT", "8000"))

    # Redis / RQ — leave empty to process sends inline (dev); set for burst traffic
    redis_url: str = os.getenv("REDIS_URL", "")

    # When true, /notifications and /events/trigger require an existing subscriber
    subscriber_required: bool = os.getenv("SUBSCRIBER_REQUIRED", "false").lower() == "true"
    
    # API Authentication
    api_keys: str = os.getenv("API_KEYS", "")
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    jwt_access_token_expire_minutes: int = int(
        os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", str(60 * 24 * 7))
    )

    # Comma-separated usernames treated as platform admins (in addition to users.is_platform_admin).
    platform_admin_usernames: str = os.getenv("PLATFORM_ADMIN_USERNAMES", "")
    
    # Email Provider Configuration
    email_provider: str = os.getenv("EMAIL_PROVIDER", "ses")  # "ses" or "smtp"
    
    # AWS SES Configuration
    aws_access_key_id: str = os.getenv("AWS_ACCESS_KEY_ID", "")
    aws_secret_access_key: str = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    aws_session_token: str = os.getenv("AWS_SESSION_TOKEN", "")
    aws_region: str = os.getenv("AWS_REGION", "ap-south-1")
    ses_sender_email: str = os.getenv("SES_SENDER_EMAIL", "")
    ses_configuration_set: str = os.getenv("SES_CONFIGURATION_SET", "")
    
    # SMTP Configuration
    smtp_host: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    smtp_username: str = os.getenv("SMTP_USERNAME", "")
    smtp_password: str = os.getenv("SMTP_PASSWORD", "")
    smtp_use_tls: bool = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
    smtp_use_ssl: bool = os.getenv("SMTP_USE_SSL", "false").lower() == "true"
    smtp_sender_email: str = os.getenv("SMTP_SENDER_EMAIL", "")

    # Multi-channel (optional; configure via .env)
    slack_incoming_webhook_url: str = os.getenv("SLACK_INCOMING_WEBHOOK_URL", "")
    ms_teams_incoming_webhook_url: str = os.getenv("MS_TEAMS_INCOMING_WEBHOOK_URL", "")
    firebase_credentials_path: str = os.getenv("FIREBASE_CREDENTIALS_PATH", "")
    sns_push_topic_arn: str = os.getenv("SNS_PUSH_TOPIC_ARN", "")
    twilio_account_sid: str = os.getenv("TWILIO_ACCOUNT_SID", "")
    twilio_auth_token: str = os.getenv("TWILIO_AUTH_TOKEN", "")
    twilio_whatsapp_from: str = os.getenv("TWILIO_WHATSAPP_FROM", "")

    # API hardening (SlowAPI; in-memory storage — one process or use same limit per instance)
    rate_limit_enabled: bool = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
    rate_limit_default: str = os.getenv("RATE_LIMIT_DEFAULT", "200/minute")
    rate_limit_send: str = os.getenv("RATE_LIMIT_SEND", "60/minute")
    rate_limit_auth_login: str = os.getenv("RATE_LIMIT_AUTH_LOGIN", "30/minute")
    rate_limit_auth_register: str = os.getenv("RATE_LIMIT_AUTH_REGISTER", "20/hour")

    class Config:
        env_file = ".env"

settings = Settings()