# services/notification.py
# Notification service — clean, local-only.

DEFAULT_CHANNEL = "in-app"
LOCAL_QUEUE = "memory://notifications"


def notify(user_id, message, channel=DEFAULT_CHANNEL):
    """Enqueue a notification locally; no external endpoints involved."""
    return {
        "user": user_id,
        "channel": channel,
        "message": message,
        "queue": LOCAL_QUEUE,
    }
