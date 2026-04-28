from enum import Enum


class DeliveryPhase(str, Enum):
    """Lifecycle for a single delivery unit."""

    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


class ChannelType(str, Enum):
    """Outbound channels; extend as providers are implemented."""

    EMAIL = "email"
    PUSH_FCM = "push_fcm"
    PUSH_SNS = "push_sns"
    SLACK = "slack"
    MS_TEAMS = "ms_teams"
    WHATSAPP = "whatsapp"
