from core.bot import bot, dp, register_handlers
import asyncio
# from physics_bot.core.bot import bot, dp, register_handlers
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))


async def main():
    await register_handlers()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
