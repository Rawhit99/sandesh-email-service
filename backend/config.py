import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5433/emails")
    api_host: str = os.getenv("API_HOST", "0.0.0.0")
    api_port: int = int(os.getenv("API_PORT", "8000"))
    
    # API Authentication
    api_keys: str = os.getenv("API_KEYS", "1234")
    
    # Email Provider Configuration
    email_provider: str = os.getenv("EMAIL_PROVIDER", "ses")  # "ses" or "smtp"
    
    # AWS SES Configuration
    aws_access_key_id: str = os.getenv("AWS_ACCESS_KEY_ID", "AKIAWNG7TH4CUDRSJGNZ")
    aws_secret_access_key: str = os.getenv("AWS_SECRET_ACCESS_KEY", "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")
    aws_region: str = os.getenv("AWS_REGION", "ap-south-1")
    ses_sender_email: str = os.getenv("SES_SENDER_EMAIL", "no-reply@zeron.one")
    ses_configuration_set: str = os.getenv("SES_CONFIGURATION_SET", "")
    
    # SMTP Configuration
    smtp_host: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    smtp_username: str = os.getenv("SMTP_USERNAME", "")
    smtp_password: str = os.getenv("SMTP_PASSWORD", "")
    smtp_use_tls: bool = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
    smtp_use_ssl: bool = os.getenv("SMTP_USE_SSL", "false").lower() == "true"
    smtp_sender_email: str = os.getenv("SMTP_SENDER_EMAIL", "")
    
    class Config:
        env_file = ".env"

settings = Settings()