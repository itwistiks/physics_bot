import asyncio
from core import bot, dp, register_handlers


async def main():
    await register_handlers()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
