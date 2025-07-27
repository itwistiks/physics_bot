from .start import router as start_router
from .reply_handlers import router as menu_router
from .inline_handlers import router as inline_router

routers = [
    start_router,
    menu_router,
    inline_router
]
