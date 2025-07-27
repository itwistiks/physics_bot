from aiogram.fsm.state import State, StatesGroup


class TaskStates(StatesGroup):
    WAITING_ANSWER = State()
    SHOWING_RESULT = State()

    TASK_LIST = State()  # Для хранения списка заданий
    CURRENT_INDEX = State()  # Для хранения текущего индекса
