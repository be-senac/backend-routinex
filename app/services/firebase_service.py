import logging

logger = logging.getLogger("routinex")

_firebase_app = None


def _get_firebase_app():
    global _firebase_app
    if _firebase_app is None:
        try:
            import firebase_admin
            from firebase_admin import credentials
            from app.config import settings

            cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
            _firebase_app = firebase_admin.initialize_app(cred)
        except Exception:
            logger.warning("Firebase credentials not found. Push notifications will be disabled.")
    return _firebase_app


def send_push_notification(fcm_token: str, title: str, body: str) -> bool:
    app = _get_firebase_app()
    if not app:
        logger.info(f"Push notification skipped (no Firebase): {title}")
        return False

    try:
        from firebase_admin import messaging
        message = messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            token=fcm_token,
        )
        messaging.send(message, app=app)
        return True
    except Exception as e:
        logger.error(f"Failed to send push notification: {e}")
        return False
