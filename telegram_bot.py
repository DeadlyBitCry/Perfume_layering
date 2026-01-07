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
        df = pd.read_csv("fra_perfumes.csv", encoding='utf-8')
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
    # Ищем колонку с брендом (часто в Name до "-")
    name = row.get("Name", "")
    if '-' in name:
        return name.split('-')[0].strip()
    words = name.split()
    return words[0] if words else 'Неизвестный бренд'

def get_name(row):
    return row.get("Name", "Без названия")

# Поиск (универсальный для большой базы)
def search_perfumes(query: str):
    if df.empty or not query:
        return pd.DataFrame()

    query = query.lower().strip()
    mask = pd.Series([False] * len(df))

    for col in df.columns:
        col_lower = col.lower()
        if any(k in col_lower for k in ["name", "title", "perfume", "fragrance"]):
            mask = mask | df[col].astype(str).str.lower().str.contains(query, na=False)
        if any(k in col_lower for k in ["accord", "note", "description"]):
            mask = mask | df[col].astype(str).str.lower().str.contains(query, na=False)

    return df[mask].head(10).reset_index(drop=True)

# Пресеты (твой полный словарь — вставь все 5 миксов)
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
            "Пропорции: примерно 1:1 (с уклоном на Mancera)",
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
            "Пропорции: 2:1 (больше Pure XS)",
            "Итог: пудровые ароматы с гурманикой заходят на ура"
        ]
    },
    ("Fakhar Lattafa", "Juliette has a gun Vanilla Vibes"): {
        "compatibility": 80,
        "vibe": "Процесс готовки сладкой ягодной выпечки с 'французской ванилью' 🧁🍓",
        "risks": [
            "Синтетика JHAG + дешевизна Lattafa = сильный аромат спирта в начале",
            "Ваниль становится более кондитерской"
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
            "Итог: делает Dylan Blue более универсальным по гендеру"
        ]
    }
}

# Анализ лееринга
def analyze_layering(perfumes):
    selected_words = set()
    for p in perfumes:
        selected_words.update(get_name(p).lower().split())
        selected_words.update(get_brand(p).lower().split())
        if "Main Accords" in p.index:
            selected_words.update(str(p["Main Accords"]).lower().split(", "))
    
    for key, data in PRESETS.items():
        preset_words = set(word for name in key for word in name.lower().split())
        if preset_words.issubset(selected_words):
            return data

    # Общий анализ
    return {
        "compatibility": 75,
        "vibe": "Уникальный экспериментальный микс 🧪",
        "risks": ["Минимальные риски"],
        "tips": ["2–3 пшика", "Сначала лёгкий, потом тяжёлый"]
    }

# Состояния (определены правильно — вне декораторов)
class LayeringStates(StatesGroup):
    waiting_for_perfumes = State()

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
        "Выбери действие:",
        reply_markup=main_keyboard()
    )

@dp.callback_query(F.data == "presets")
async def show_presets(callback: types.CallbackQuery):
    await callback.message.edit_text("🔥 Выбери готовый микс:", reply_markup=presets_keyboard())

@dp.callback_query(F.data.regexp(r"preset_\d+"))
async def send_preset(callback: types.CallbackQuery):
    idx = int(callback.data.split("_")[1]) - 1
    key = list(PRESETS.keys())[idx]
    data = PRESETS[key]

    perfumes = []
    name_col = "Name"
    for preset_name in key:
        search_term = "|".join(preset_name.lower().split())
        match = df[df[name_col].str.lower().str.contains(search_term, na=False, regex=True)]
        if not match.empty:
            perfumes.append(match.iloc[0])
        else:
            perfumes.append(pd.Series({name_col: preset_name}))

    text = f"🎭 **Готовый микс #{idx+1}**\n\n"
    text += "\n".join(f"• {get_brand(p)} - {get_name(p)}" for p in perfumes)
    text += f"\n\nСовместимость: {data['compatibility']}%\n"
    text += f"Вайб: {data['vibe']}\n\n"
    text += "Риски:\n" + "\n".join(f"• {r}" for r in data['risks']) + "\n\n"
    text += "Советы:\n" + "\n".join(f"• {t}" for t in data['tips'])

    await callback.message.edit_text(text, reply_markup=main_keyboard())

@dp.callback_query(F.data == "back_main")
async def back_to_main(callback: types.CallbackQuery):
    await callback.message.edit_text("🌸 Главное меню\nВыбери действие:", reply_markup=main_keyboard())

# Ручной лееринг и поиск (исправленные версии)
@dp.callback_query(F.data == "search")
async def cmd_search(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("🔍 Введи запрос для поиска (название, бренд, нота):")
    await state.set_state(LayeringStates.waiting_for_perfumes)
    await state.update_data(selected_indices=[])

@dp.message(LayeringStates.waiting_for_perfumes)
async def process_search(message: Message, state: FSMContext):
    query = message.text.strip()
    if not query:
        await message.answer("Запрос пустой — попробуй ещё раз или вернись в меню:", reply_markup=main_keyboard())
        await state.clear()
        return

    results = search_perfumes(query)
    
    if results.empty:
        await message.answer("Ничего не найдено 😔\nПопробуй другой запрос или вернись в меню:", reply_markup=main_keyboard())
        await state.clear()
        return

    data = await state.get_data()
    selected_indices = data.get("selected_indices", [])

    kb = InlineKeyboardMarkup(inline_keyboard=[])

    result_indices = results.index.tolist()

    for i, local_idx in enumerate(result_indices):
        row = df.loc[local_idx]
        name = get_name(row)
        brand = get_brand(row)
        status = " ✅" if local_idx in selected_indices else ""
        text = f"{brand} - {name}{status}"
        kb.inline_keyboard.append([InlineKeyboardButton(text=text, callback_data=f"select_{i}")])

    kb.inline_keyboard.append([InlineKeyboardButton(text="✅ Готово — анализ", callback_data="analyze")])
    kb.inline_keyboard.append([InlineKeyboardButton(text="← Отмена", callback_data="back_main")])

    await message.answer(
        f"Найдено {len(results)} ароматов. Выбрано: {len(selected_indices)}/3\nВыбери ароматы:",
        reply_markup=kb
    )
    await state.update_data(result_indices=result_indices)

@dp.callback_query(F.data.startswith("select_"))
async def select_perfume(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    result_indices = data.get("result_indices", [])
    selected_indices = data.get("selected_indices", [])

    local_idx = int(callback.data.split("_")[1])
    global_idx = result_indices[local_idx]

    if global_idx in selected_indices:
        await callback.answer("Уже выбран!", show_alert=True)
        return

    if len(selected_indices) >= 3:
        await callback.answer("Максимум 3 аромата!", show_alert=True)
        return

    selected_indices.append(global_idx)
    await state.update_data(selected_indices=selected_indices)

    await callback.answer(f"Добавлено: {get_brand(df.loc[global_idx])} - {get_name(df.loc[global_idx])}")

    await process_search(callback.message, state)

@dp.callback_query(F.data == "analyze")
async def do_analysis(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected_indices = data.get("selected_indices", [])

    if len(selected_indices) < 2:
        await callback.message.answer("Нужно выбрать минимум 2 аромата!", reply_markup=main_keyboard())
        await state.clear()
        return

    perfumes = [df.loc[idx] for idx in selected_indices]
    analysis = analyze_layering(perfumes)

    text = "🎭 **Твой лееринг готов!**\n\n"
    text += "\n".join(f"• {get_brand(p)} - {get_name(p)}" for p in perfumes)
    text += f"\n\nСовместимость: {analysis['compatibility']}%\n"
    text += f"Вайб: {analysis['vibe']}\n\n"
    text += "Риски:\n" + "\n".join(f"• {r}" for r in analysis['risks']) + "\n\n"
    text += "Советы:\n" + "\n".join(f"• {t}" for t in analysis['tips'])

    await callback.message.edit_text(text, reply_markup=main_keyboard())
    await state.clear()

@dp.callback_query(F.data == "layer")
async def start_layer(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("🎭 Создай свой лееринг!\nВведи запрос для поиска первого аромата:")
    await state.set_state(LayeringStates.waiting_for_perfumes)
    await state.update_data(selected_indices=[])

async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())