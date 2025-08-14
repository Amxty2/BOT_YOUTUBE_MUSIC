from aiogram import F, Router
from aiogram.types import Message, ReplyKeyboardRemove, FSInputFile
from aiogram.filters import Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest

import app.keyboards as kb
from app.yt_mp3 import download_mp3_from_youtube, remove_file
from app.variables import USERS

class Input(StatesGroup):
    url = State()

class DeleteMsg(StatesGroup):
    delete = State()

class Await(StatesGroup):
    await_audio = State()

router = Router()


# ---- универсальная функция безопасного удаления ----
async def safe_delete_message(bot, chat_id: int, message_id: int, state: FSMContext = None):
    try:
        await bot.delete_message(chat_id=chat_id, message_id=message_id)

    except TelegramForbiddenError:
        # Если нет прав — отправляем предупреждение и сохраняем в state для удаления
        warn_msg = await bot.send_message(
            chat_id=chat_id,
            text="⚠ У меня нет прав на удаление сообщений. Пожалуйста, выдай их."
        )
        if state:
            await state.update_data(delete=[warn_msg.chat.id, warn_msg.message_id])

    except TelegramBadRequest:
        # Сообщение уже удалено или слишком старое
        pass


@router.message(F.text & ~(F.text.startswith('/start') | F.text.startswith('/src')), DeleteMsg.delete)
async def handler_delete_state(message: Message, state: FSMContext):
    data = await state.get_data()
    if "delete" in data:
        await safe_delete_message(message.bot, data["delete"][0], data["delete"][1])
    await safe_delete_message(message.bot, message.chat.id, message.message_id)


@router.message(Await.await_audio)
async def handler_await_audio(message: Message):
    await safe_delete_message(message.bot, message.chat.id, message.message_id)


@router.message(Command("start"))
async def handler_start(message: Message, state: FSMContext):
    if str(message.from_user.id) not in USERS:
        return
    await state.set_state(DeleteMsg.delete)
    await safe_delete_message(message.bot, message.chat.id, message.message_id)

    await message.answer(
        "👋 Привет! Я — бот, который пришлет тебе mp3 c Youtube\n"
        "просто введи команду /src и потом вставь ссылку на видео или плейлист\n"
        "видео должно быть длинной не более 20 минут\n"
        "плейлист должен быть размером не более 20 видео\n"
        '"это сообщение можно удалить"',
        reply_markup=kb.src
    )


@router.message(Command("src"), DeleteMsg.delete)
async def handler_src(message: Message, state: FSMContext):
    await safe_delete_message(message.bot, message.chat.id, message.message_id)

    msg = await message.bot.send_message(chat_id=message.chat.id, text="Вставьте ссылку", reply_markup=ReplyKeyboardRemove())
    await state.update_data(url=[msg.chat.id, msg.message_id])
    await state.set_state(Input.url)


@router.message(Input.url)
async def handler_url(message: Message, state: FSMContext):
    await state.set_state(Await.await_audio)
    data = await state.get_data()

    await safe_delete_message(message.bot, data["url"][0], data["url"][1])
    msg_await = await message.bot.send_message(chat_id=message.chat.id, text="ожидайте...\nзагрузка может занять от 1 до 10 мин. в зависимости от количества видео")

    downloaded_files = download_mp3_from_youtube(message.text)

    if downloaded_files:
        for file_path in downloaded_files:
            audio = FSInputFile(file_path)
            await message.bot.send_audio(chat_id=message.chat.id, audio=audio, reply_markup=kb.src)
    else:
        await state.set_state(DeleteMsg.delete)
        msg_failed = await message.answer("Не удалось скачать")
        await state.update_data(delete=[msg_failed.chat.id, msg_failed.message_id])
        await safe_delete_message(message.bot, message.chat.id, message.message_id)
        await safe_delete_message(message.bot, msg_await.chat.id, msg_await.message_id)

    await state.set_state(DeleteMsg.delete)
    await safe_delete_message(message.bot, message.chat.id, message.message_id)
    await safe_delete_message(message.bot, msg_await.chat.id, msg_await.message_id)

    if downloaded_files:
        remove_file(downloaded_files)
