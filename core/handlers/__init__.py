from .common import router as common_router
from .inline_handlers import router as inline_router
from .reply_handlers import router as reply_router
from .teacher import router as teacher_router      # Сначала специфичные
from .moderator import router as moderator_router  # Потом модератор
from .admin import router as admin_router          # Админ последним

routers = [
    common_router,    # Базовые команды (/start, /help)
    inline_router,    # Inline-обработчики
    reply_router,     # Reply-обработчики
    teacher_router,   # Команды преподавателя
    moderator_router,  # Команды модератора
    admin_router      # Команды админа (последние!)
]

__all__ = ['routers']
