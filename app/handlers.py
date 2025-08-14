
from aiogram import F, Router
from aiogram.types import Message, ReplyKeyboardRemove, FSInputFile
from aiogram.filters import Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

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



@router.message(F.text & ~(F.text.startswith('/start') | F.text.startswith('/src')), DeleteMsg.delete)
async def start_handler(message: Message, state: FSMContext):
    try:
        data = await state.get_data()
        await message.bot.delete_message(chat_id=data["delete"][0], message_id=data["delete"][1])
    except:
        pass
    await message.bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)


@router.message(Await.await_audio)
async def start_handler(message : Message, state: FSMContext):
    await message.bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)


# Обработчик команды /start
@router.message(Command("start"))
async def start_handler(message: Message, state: FSMContext):
    if not str(message.from_user.id) in USERS: return
    await state.set_state(DeleteMsg.delete)
    await message.bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)

    await message.answer(
        "👋 Привет! Я — бот, который пришлет тебе mp3 c Youtube\n"
        "просто введи команду /src и потом вставь ссылку на видео или плейлист\n"
        "видео должно быть длинной не более 20 минут\n"
        "плейлист должен быть размером не более 20 видео\n"
        '"это сообщение можно удалить"',
        reply_markup=kb.src
    )


@router.message(Command("src"), DeleteMsg.delete)
async def start_handler(message: Message, state: FSMContext):
    await message.bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)

    msg = await message.bot.send_message(chat_id=message.chat.id, text="Вставьте ссылку", reply_markup=ReplyKeyboardRemove())
    await state.update_data(url=[msg.chat.id, msg.message_id])
    await state.set_state(Input.url)




@router.message(Input.url)
async def start_handler(message: Message, state: FSMContext):
    await state.set_state(Await.await_audio)
    data = await state.get_data()
    await message.bot.delete_message(chat_id=data["url"][0], message_id=data["url"][1])
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
        await state.set_state(DeleteMsg.delete)
        await message.bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        await message.bot.delete_message(chat_id=msg_await.chat.id, message_id=msg_await.message_id)

    await state.set_state(DeleteMsg.delete)
    await message.bot.delete_message(chat_id=msg_await.chat.id, message_id=msg_await.message_id)



    if downloaded_files:
        remove_file(downloaded_files)





