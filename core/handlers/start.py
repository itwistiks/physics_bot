from aiogram import Router, types
from aiogram.filters import Command
from core.keyboards.main_menu import main_menu_kb

router = Router()


@router.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("📚 Привет! Я помогу подготовиться к ОГЭ по физике.\nВыбери действие:",
                         reply_markup=main_menu_kb())


def register(dp):
    dp.include_router(router)
