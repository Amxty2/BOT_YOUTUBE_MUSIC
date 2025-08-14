from aiogram import Bot, Dispatcher
from app.handlers import router
import asyncio
from app.variables import TOKEN



import logging
# Создаём бота
bot = Bot(token=TOKEN)
dp = Dispatcher()


# Запуск бота
async def main():
    logging.basicConfig(level=logging.INFO)
    dp.include_router(router)
    await dp.start_polling(bot)




if __name__ == "__main__":
    asyncio.run(main())
