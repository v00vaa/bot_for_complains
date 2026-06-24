from aiogram.fsm.state import State, StatesGroup


class CreateBug(StatesGroup):
    waiting_description = State()
    waiting_report = State()