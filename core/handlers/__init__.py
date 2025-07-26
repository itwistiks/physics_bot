from .start import router as start_router
from .db_test import router as db_test_router
from .menu_handlers import router as menu_router
from .inline_handlers import router as inline_router

routers = [
    start_router,
    db_test_router,
    menu_router,
    inline_router
]
