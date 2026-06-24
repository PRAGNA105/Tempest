# services/notification.py
# Notification service — deliberately CLEAN.
#
# No production URLs, no imports that reach the staging/prod config chain.
# Everything here points at local/in-process behaviour only.

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
