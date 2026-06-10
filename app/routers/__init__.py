from app.routers.auth import router as auth_router
from app.routers.users import router as users_router
from app.routers.tasks import router as tasks_router
from app.routers.agenda import router as agenda_router
from app.routers.notifications import router as notifications_router
from app.routers.chat import router as chat_router
from app.routers.dashboard import router as dashboard_router

__all__ = [
    "auth_router", "users_router", "tasks_router", "agenda_router",
    "notifications_router", "chat_router", "dashboard_router",
]
