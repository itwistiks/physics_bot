from aiogram import Router, types
from config.database import SessionLocal
from core.database.models import Task
from aiogram.filters import Command

router = Router()


@router.message(Command("testdb"))
async def cmd_testdb(message: types.Message):
    db = SessionLocal()
    task = db.query(Task).first()
    db.close()

    await message.answer(
        f"Первая задача из БД:\n{task.task_content['text']}\n"
        f"Варианты: {', '.join(task.answer_options)}"
    )
