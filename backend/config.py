import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = os.getenv("DATABASE_URL", "")
    api_host: str = os.getenv("API_HOST", "0.0.0.0")
    api_port: int = int(os.getenv("API_PORT", "8000"))
    app_env: str = os.getenv("APP_ENV", "development")

    # Redis / RQ:
    # leave empty to process sends inline (dev); set for burst traffic.
    redis_url: str = os.getenv("REDIS_URL", "")
    redis_socket_timeout_seconds: int = int(
        os.getenv("REDIS_SOCKET_TIMEOUT_SECONDS", "5")
    )
    redis_connect_timeout_seconds: int = int(
        os.getenv("REDIS_CONNECT_TIMEOUT_SECONDS", "5")
    )
    queue_name: str = os.getenv("QUEUE_NAME", "sandesh-email")
    queue_worker_concurrency: int = int(
        os.getenv("QUEUE_WORKER_CONCURRENCY", "8")
    )
    queue_poll_timeout_seconds: int = int(
        os.getenv("QUEUE_POLL_TIMEOUT_SECONDS", "5")
    )
    queue_max_retries: int = int(os.getenv("QUEUE_MAX_RETRIES", "5"))
    queue_retry_backoff_seconds: int = int(
        os.getenv("QUEUE_RETRY_BACKOFF_SECONDS", "10")
    )
    queue_job_timeout: str = os.getenv("QUEUE_JOB_TIMEOUT", "10m")
    queue_result_ttl_seconds: int = int(
        os.getenv("QUEUE_RESULT_TTL_SECONDS", "3600")
    )
    queue_failure_ttl_seconds: int = int(
        os.getenv("QUEUE_FAILURE_TTL_SECONDS", "86400")
    )
    queue_inline_fallback: bool = (
        os.getenv("QUEUE_INLINE_FALLBACK", "false").lower() == "true"
    )

    # When true, /notifications and /events/trigger require a subscriber.
    subscriber_required: bool = (
        os.getenv("SUBSCRIBER_REQUIRED", "false").lower() == "true"
    )

    # API Authentication
    api_keys: str = os.getenv("API_KEYS", "")
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    jwt_access_token_expire_minutes: int = int(
        os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", str(60 * 24 * 7))
    )

    # Comma-separated usernames treated as platform admins
    # (in addition to users.is_platform_admin).
    platform_admin_usernames: str = os.getenv("PLATFORM_ADMIN_USERNAMES", "")
    platform_admin_username: str = os.getenv("PLATFORM_ADMIN_USERNAME", "")
    platform_admin_password: str = os.getenv("PLATFORM_ADMIN_PASSWORD", "")
    default_organization: str = os.getenv("DEFAULT_ORGANIZATION", "")

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
    slack_incoming_webhook_url: str = os.getenv(
        "SLACK_INCOMING_WEBHOOK_URL", ""
    )
    ms_teams_incoming_webhook_url: str = os.getenv(
        "MS_TEAMS_INCOMING_WEBHOOK_URL", ""
    )
    firebase_credentials_path: str = os.getenv("FIREBASE_CREDENTIALS_PATH", "")
    sns_push_topic_arn: str = os.getenv("SNS_PUSH_TOPIC_ARN", "")
    twilio_account_sid: str = os.getenv("TWILIO_ACCOUNT_SID", "")
    twilio_auth_token: str = os.getenv("TWILIO_AUTH_TOKEN", "")
    twilio_whatsapp_from: str = os.getenv("TWILIO_WHATSAPP_FROM", "")

    # API hardening (SlowAPI; in-memory storage).
    # For multi-instance deploys, keep the same limit per instance.
    rate_limit_enabled: bool = (
        os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
    )
    rate_limit_default: str = os.getenv("RATE_LIMIT_DEFAULT", "200/minute")
    rate_limit_send: str = os.getenv("RATE_LIMIT_SEND", "60/minute")
    rate_limit_auth_login: str = os.getenv(
        "RATE_LIMIT_AUTH_LOGIN", "30/minute"
    )
    rate_limit_auth_register: str = os.getenv(
        "RATE_LIMIT_AUTH_REGISTER", "20/hour"
    )

    # HTTP/security hardening
    cors_allow_origins: str = os.getenv(
        "CORS_ALLOW_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000",
    )
    cors_allow_methods: str = os.getenv(
        "CORS_ALLOW_METHODS", "GET,POST,PUT,PATCH,DELETE,OPTIONS"
    )
    cors_allow_headers: str = os.getenv("CORS_ALLOW_HEADERS", "*")
    trusted_hosts: str = os.getenv("TRUSTED_HOSTS", "localhost,127.0.0.1")
    security_hsts_seconds: int = int(
        os.getenv("SECURITY_HSTS_SECONDS", "31536000")
    )
    max_request_body_mb: int = int(os.getenv("MAX_REQUEST_BODY_MB", "10"))

    # Database pool sizing for concurrency
    db_pool_size: int = int(os.getenv("DB_POOL_SIZE", "30"))
    db_max_overflow: int = int(os.getenv("DB_MAX_OVERFLOW", "60"))
    db_pool_timeout_seconds: int = int(
        os.getenv("DB_POOL_TIMEOUT_SECONDS", "30")
    )
    db_pool_recycle_seconds: int = int(
        os.getenv("DB_POOL_RECYCLE_SECONDS", "1800")
    )

    class Config:
        env_file = ".env"


settings = Settings()
