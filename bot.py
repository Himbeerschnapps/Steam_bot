import asyncio                  # запуск асинхронного кода
import aiohttp                  # запросы к steam api
import aiogram                  # для самого бота
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton


# для управления бото (токен взят у botfather в тг)
BOT_TOKEN = "8089522459:AAGhQWkbu0x3ZUL66CbNPr9CoHSwrh_oQns"

# объект бота
bot = Bot(token=BOT_TOKEN)

# для управленния командами
dp = Dispatcher()

# ссылка steam api для новинок и скидок
STEAM_FEATURED_URL = "https://store.steampowered.com/api/featuredcategories"

# аналогично для игр по жанрам
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
async def start(message: Message):
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
async def help_cmd(message: Message):
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
# только на этапе конечной выверки я заметила, что допустила грамматическую ошибку, но решила, что лучше уже это не трогать

@dp.message(Command("recomendations"))
async def recomendations(message: Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=genre, callback_data=tag)]
            for genre, tag in GENRES.items()
        ]
    )

    await message.answer("Выбери жанр:", reply_markup=keyboard)


@dp.callback_query()
async def genre_selected(callback: CallbackQuery):
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
            f"<a href='{game['url']}'>{game['name']}</a>\n"
            f"{game['price']}\n\n"
        )

    await callback.message.answer(text, parse_mode="HTML")
    await callback.answer()   

# команда /new 
@dp.message(Command("new"))
async def new_games(message: Message):
    games = await get_featured_games("new_releases")

    text = "Популярные новинки:\n\n"
    for game in games[:5]:
        text += (
            f"<a href='{game['url']}'>{game['name']}</a>\n"
            f"{game['price']}\n\n"
        )

    await message.answer(text, parse_mode="HTML")


# команда /discount 
@dp.message(Command("discount"))
async def discounts(message: Message):
    games = await get_featured_games("specials")

    text = "Скидки в Steam:\n\n"
    for game in games[:5]:
        text += (
            f"<a href='{game['url']}'>{game['name']}</a>\n"
            f"{game['discount_percent']}% — {game['price']}\n\n"
        )

    await message.answer(text, parse_mode="HTML")

# использование steam api для получения нужных данных и вывода игр
# для каждой команды отправляем запрос к стиму и выводим полученные данные

# игры по жанру
async def get_games_by_genre(tag):

    params = {
        "tags": tag,
        "cc": "ru",
        "l": "russian",
        "page": 1
    }

    # отправление самого запроса
    async with aiohttp.ClientSession() as session:
        async with session.get(STEAM_SEARCH_URL, params=params) as resp:
            data = await resp.json()

    games = []

    # чтобы не нагромождать бота информацией, я решила взять только пять игр в каждом жанре
    
    for item in data.get("items", [])[:5]:
        price = "Бесплатно" # для бесплатных продуктов

        if item.get("price"):
            price = f"{item['price']['final'] // 100} ₽" # для платных продуктов; на сто делила, потому что изначально программа почему-то берёт цену в копейках, а не в рублях

        appid = item["id"]  # айди игры 

        games.append({
            "name": item["name"],
            "price": price,
            "url": f"https://store.steampowered.com/app/{appid}"
        }) 

    return games


# новинки и скидки

# тут с запросом всё то же самое
async def get_featured_games(category):
    async with aiohttp.ClientSession() as session:
        async with session.get(STEAM_FEATURED_URL) as resp:
            data = await resp.json()

    games = []

    for item in data[category]["items"]:
        price = "Бесплатно" # аналогично жанрам для бесплатных игр

        if item.get("final_price"):
            price = f"{item['final_price'] // 100} ₽" # аналогично жанрам для игр, цена которых почему-то выводится в копейках

        appid = item["id"] # снова айди в стиме

        games.append({
            "name": item["name"],
            "price": price,
            "discount_percent": item.get("discount_percent", 0),
            "url": f"https://store.steampowered.com/app/{appid}"
        })

    return games


# основная часьб закончена, ниже уже только запуск

# запуск самого бота
async def main():
    await dp.start_polling(bot)

# запус программы
if __name__ == "__main__":
    asyncio.run(main())
