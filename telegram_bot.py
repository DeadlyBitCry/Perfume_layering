import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

import pandas as pd

# Твой токен
TOKEN = "7813306753:AAEozSfa8k1XDjXJGWlwcBFMF5fItn86NhI"

# Загрузка базы
def load_base():
    try:
        df = pd.read_csv("big_perfume_base.csv", encoding='utf-8')
        print(f"Загружена большая база: {len(df)} ароматов")
        return df
    except FileNotFoundError:
        try:
            df = pd.read_csv("perfume_base(2).csv", encoding='utf-8')
            print(f"Загружена маленькая база: {len(df)} ароматов")
            return df
        except:
            print("База не найдена!")
            return pd.DataFrame()

df = load_base()
if df.empty:
    raise Exception("Не удалось загрузить базу")

# Универсальные функции
def get_brand(row):
    # Попробуем найти колонку бренда по любому регистру
    brand_col = next((col for col in row.index if col.lower() == "brand"), None)
    if brand_col:
        return row.get(brand_col, 'Неизвестный бренд')
    name = get_name(row)
    if '-' in name:
        return name.split('-')[0].strip()
    words = name.split()
    return words[0] if words else 'Неизвестный бренд'

def get_name(row):
    name_col = next((col for col in row.index if col.lower() == "name"), None)
    if name_col:
        return row.get(name_col, 'Без названия')
    return 'Без названия'

# Поиск
def search_perfumes(query: str):
    query = query.lower()
    mask = pd.Series([False] * len(df))
    if "Name" in df.columns:
        mask = mask | df["Name"].str.lower().str.contains(query, na=False)
    if "Main Accords" in df.columns:
        mask = mask | df["Main Accords"].str.lower().str.contains(query, na=False)
    if "Description" in df.columns:
        mask = mask | df["Description"].str.lower().str.contains(query, na=False)
    return df[mask].head(10).reset_index(drop=True)

# Твои пресеты (вставь свой полный словарь)
PRESETS = {
    ("Mancera French Riviera", "Juliette has a gun Vanilla Vibes"): {
        "compatibility": 85,
        "vibe": "Пляжный вайб с увлажняющим кремом и лёгкой ванильной сладостью 🏖️🧴",
        "risks": [
            "JHAG сразу уменьшает бьющий цитрусовый аромат Mancera",
            "Цветочные ноты Mancera становятся ярче",
            "В итоге — ощущение увлажняющего крема, без намёка на сладость JHAG"
        ],
        "tips": [
            "Порядок: сначала Mancera French Riviera, сверху Vanilla Vibes",
            "Пропорции: примерно 1:1 (с уклоном на Mancera из-за разных пульверизаторов)",
            "Итог: не 'мусорный' запах, но ожидал большего"
        ]
    },
    ("Givenchy Gentleman Reserve Privee", "Dior Homme Intense"): {
        "compatibility": 70,
        "vibe": "Сильная сухая пудровость с древесиной на фоне 🍂✨",
        "risks": [
            "Древесные ноты становятся главенствующими и перебивают всё остальное",
            "Отсутствует гурманская нотка от Givenchy",
            "Просыпается сушняк в горле от сухости"
        ],
        "tips": [
            "Порядок: сначала Dior Homme Intense, сверху Givenchy",
            "Пропорции: 1:1",
            "Итог: база более выраженная, верхние этапы пропущены"
        ]
    },
    ("Paco Rabanne Pure XS", "Dior Homme Intense 2011"): {
        "compatibility": 90,
        "vibe": "Дорогая библиотека с алкоголем и девушками в макияже 📚🥃💄",
        "risks": [
            "Сильная пудра Dior может ужимать сладость Pure XS",
            "Легко переборщить — стать слишком сладким"
        ],
        "tips": [
            "Порядок: сначала Pure XS, сверху Dior Homme Intense 2011",
            "Пропорции: 2:1 (больше Pure XS, чтобы сладость играла ярче)",
            "Итог: пудровые ароматы с гурманикой заходят на ура (зависит от ноты сладости)"
        ]
    },
    ("Fakhar Lattafa", "Juliette has a gun Vanilla Vibes"): {
        "compatibility": 80,
        "vibe": "Процесс готовки сладкой ягодной выпечки с 'французской ванилью' 🧁🍓",
        "risks": [
            "Синтетика JHAG + дешевизна Lattafa = сильный аромат спирта в начале",
            "Ваниль становится более кондитерской, чем воздушной"
        ],
        "tips": [
            "Порядок: сначала JHAG Vanilla Vibes (2 пшика), сверху Fakhar Lattafa",
            "Пропорции: 1:2 (больше JHAG)",
            "Итог: работает не сразу, но через время — оригинальный аромат"
        ]
    },
    ("Fakhar Lattafa", "Versace Dylan Blue"): {
        "compatibility": 75,
        "vibe": "Versace Dylan Blue, но без выделяющегося перца и смородины — более унисекс 🌊🌸",
        "risks": [
            "Цитрусовый старт может дать горечь",
            "Чёрный перец смягчается цветочным ароматом"
        ],
        "tips": [
            "Порядок: сначала Versace Dylan Blue, сверху Fakhar Lattafa",
            "Пропорции: 1:1",
            "Итог: делает Dylan Blue более универсальным по гендеру, но не оригинальнее"
        ]
    },
    # Добавь остальные 4 пресета
}

# Анализ лееринга (упрощённый)
def analyze_layering(perfumes):
    selected_words = set()
    for p in perfumes:
        selected_words.update(get_name(p).lower().split())
        selected_words.update(get_brand(p).lower().split())
    
    for key, data in PRESETS.items():
        preset_words = set(word for name in key for word in name.lower().split())
        if preset_words.issubset(selected_words):
            return data

    return {
        "compatibility": 75,
        "vibe": "Уникальный экспериментальный микс 🧪",
        "risks": ["Минимальные риски"],
        "tips": ["2–3 пшика", "Сначала лёгкий, потом тяжёлый"]
    }

# Клавиатуры
def main_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔥 Готовые миксы", callback_data="presets")],
        [InlineKeyboardButton(text="🔍 Поиск аромата", callback_data="search")],
        [InlineKeyboardButton(text="🎭 Создать лееринг", callback_data="layer")]
    ])

def presets_keyboard():
    kb = InlineKeyboardMarkup(inline_keyboard=[])
    for i, key in enumerate(PRESETS.keys(), 1):
        names = " + ".join(key)
        kb.inline_keyboard.append([InlineKeyboardButton(text=f"{i}. {names}", callback_data=f"preset_{i}")])
    # ← Эта строка должна быть точно такой:
    kb.inline_keyboard.append([InlineKeyboardButton(text="← Назад", callback_data="back_main")])
    return kb

# Бот
bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

@dp.message(Command("start"))
async def start(message: Message):
    await message.answer(
        "🌸 Привет! Я — Perfume Layering Bot\n"
        "Создаю лееринги на основе 70k+ ароматов и моих экспериментов.\n\n"
        "Выбери:",
        reply_markup=main_keyboard()
    )

@dp.callback_query(F.data == "presets")
async def show_presets(callback: types.CallbackQuery):
    await callback.message.edit_text("🔥 Выбери готовый микс:", reply_markup=presets_keyboard())

@dp.callback_query(F.data == "back_main")
async def back_to_main(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "🌸 Главное меню\nВыбери, что хочешь сделать:",
        reply_markup=main_keyboard()
    )

@dp.callback_query(F.data.regexp(r"preset_\d+"))
async def send_preset(callback: types.CallbackQuery):
    idx = int(callback.data.split("_")[1]) - 1
    key = list(PRESETS.keys())[idx]
    data = PRESETS[key]

    perfumes = []
    # Безопасный поиск колонок с игнором регистра
    name_col = next((col for col in df.columns if col.lower() == "name"), None)
    if name_col is None:
        await callback.message.edit_text("Ошибка: колонка с названием аромата не найдена в базе")
        return

    for preset_name in key:
        # Ищем по последнему слову из preset_name (например "Vibes" из "Vanilla Vibes")
        search_term = preset_name.split()[-1].lower()
        match = df[df[name_col].str.lower().str.contains(search_term, na=False)]
        if not match.empty:
            perfumes.append(match.iloc[0])
        else:
            # Если не нашёл — добавляем заглушку
            perfumes.append(pd.Series({name_col: preset_name}))

    text = f"🎭 **Готовый микс #{idx+1}**\n\n"
    text += "\n".join(f"• {get_brand(p)} - {get_name(p)}" for p in perfumes)
    text += f"\n\nСовместимость: {data['compatibility']}%\n"
    text += f"Вайб: {data['vibe']}\n\n"
    text += "Риски:\n" + "\n".join(f"• {r}" for r in data['risks']) + "\n\n"
    text += "Советы:\n" + "\n".join(f"• {t}" for t in data['tips'])

    await callback.message.edit_text(text, reply_markup=main_keyboard())

async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())