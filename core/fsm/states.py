from aiogram.fsm.state import State, StatesGroup


class TaskStates(StatesGroup):
    WAITING_ANSWER = State()
    SHOWING_RESULT = State()
