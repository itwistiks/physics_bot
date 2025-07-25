from aiogram import Router, types
from aiogram.filters import Command

router = Router()


@router.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("📚 Привет! Я бот для подготовки к ОГЭ по физике")


def register(dp):
    dp.include_router(router)
