from aiogram.fsm.state import State, StatesGroup


class TaskStates(StatesGroup):
    WAITING_ANSWER = State()  # Состояние ожидания ответа
    SHOWING_RESULT = State()  # Состояние показа результата

    TASK_LIST = State()  # Список заданий
    CURRENT_INDEX = State()  # Для хранения текущего индекса
