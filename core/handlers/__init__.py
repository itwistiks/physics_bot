from .admin import router as admin_router
from .common import router as common_router
from .inline_handlers import router as inline_router
from .reply_handlers import router as reply_router

routers = [
    admin_router,
    common_router,
    inline_router,
    reply_router
]

__all__ = ['routers']
