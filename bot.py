import asyncio                  # запуск асинхронного кода
import aiohttp                  # запросы к Steam API
import aiogram                  # для самого бота
from aiogram import Bot, Dispatcher, Types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# для управления бото (токен взят у BotFather)
BOT_TOKEN = "8089522459:AAGhQWkbu0x3ZUL66CbNPr9CoHSwrh_oQns"

# объект бота
bot = Bot(token=BOT_TOKEN)

# для управленния командами
dp = Dispatcher()

# URL Steam API для новинок и скидок
STEAM_FEATURED_URL = "https://store.steampowered.com/api/featuredcategories"

# URL Steam API для поиска игр по жанрам
STEAM_SEARCH_URL = "https://store.steampowered.com/api/storesearch"

GENRES = {
    "Экшен": "action",
    "Приключения": "adventure",
    "RPG": "rpg",
    "Стратегии": "strategy",
    "Инди": "indie",
    "Симуляторы": "simulation"
}

# словарь составлялся так, чтобы текст кнопки соответствовал жанровому тегу в стиме
# решила не загромождать бота излишком жанров и выделила основные

# дальше занялась каждой командой отдельно

# /start — приветствует пользователя и объясняет функционал бота
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "Привет! Это бот-помощник для каждого, кто не определился, во что поиграть вечером, хочет узнать о горячих новинках игровой индустрии или узнать о столь желанных скидках.\n\n"
        "Что можно получить от бота:\n"
        "• Рекомендацию игр по жанрам\n"
        "• Новинки Steam\n"
        "• Скидки Steam\n\n"
        "Для выбора команды напиши /help"
    )


# /help — выводит перечень команд бота
@dp.message(Command("help"))
async def help_cmd(message: types.Message):
    await message.answer(
        "/start — запуск бота\n"
        "/help — список команд\n"
        "/recomendations — рекомендации по жанрам\n"
        "/new — новинки Steam\n"
        "/discount — скидки Steam"
    )

# дополнительные команды
# 1. команда /recomendatons для пожанровых рекомендаций (выводит кнопки с заданными в словаре жанрами, после чего выдаёт несколько рекомендаций внутри каждого жанра
# 2. команда /new для новинок
# 3. команда /discount для скидок

# команда /recomendations 
@dp.message(Command("recomendations"))
async def recomendations(message: types.Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=genre, callback_data=tag)]
            for genre, tag in GENRES.items()
        ]
    )

    await message.answer("Выбери жанр:", reply_markup=keyboard)


@dp.callback_query()
async def genre_selected(callback: types.CallbackQuery):
    tag = callback.data                    
    games = await get_games_by_genre(tag)  

    # на какой-то космический случай, если вдруг список игр пустой
    if not games:
        await callback.message.answer("К сожалению, я не могу дать тебе рекомендацию")
        return

    # ответ бота
    text = "Рекомендации:\n\n"
    for game in games:
        text += (
            f"🎮 <a href='{game['url']}'>{game['name']}</a>\n"
            f"💰 {game['price']}\n\n"
        )

    await callback.message.answer(text, parse_mode="HTML")
    await callback.answer()   

