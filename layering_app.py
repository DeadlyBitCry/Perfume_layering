import pandas as pd
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, IntPrompt
from rich import box
import logging
import json

# Настройка логирования и rich-консоли
console = Console()
logging.basicConfig(filename="perfume_layering.log", level=logging.INFO, encoding='utf-8')

# Глобальные правила лееринга
LAYERING_RULES = {
    "positive": [
        ("пудровый", "гурман", 95, "Пудровые ароматы + гурманская сладость = идеальный уютный микс 🍮✨", "зависит от типа сладости (тофи/ваниль — лучше, виски — может сушить)"),
        ("цветочный", "перец", 90, "Цветы смягчают остроту перца → элегантный и мягкий результат 🌸🌶️", ""),
        ("свежий", "ваниль", 85, "Свежий старт + ванильная база = летний десерт на пляже 🏖️🍦", "может быть спиртовой старт, если один из ароматов бюджетный"),
        ("водный", "восточный", 80, "Водные ноты + восточные специи = морской бриз с пряностями 🌊🍂", ""),
        ("мускус", "любой", 90, "Мускус усиливает стойкость и делает микс 'кожным' 🧴", ""),
    ],
    "risks": [
        ("синтетика", "дешевизна", "Сильный спиртовой старт в начале — подожди 5–10 минут"),
        ("два тяжелых", "база", "База может перебить верхние ноты — один аромат станет доминировать"),
        ("гурман", "виски", "Алкогольная сладость может дать сухость и горечь"),
    ]
}

# Пресеты — твои реальные лееринги из документа
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
    }
}

def get_brand(row):
    if "brand" in row.index.str.lower():
        return row.get("brand", "Неизвестный бренд")
    # Если бренда нет — пытаемся извлечь из Name (первые слова до "-" или тире)
    name = row.get("Name", "")
    if "-" in name:
        return name.split("-")[0].strip()
    if " by " in name.lower():
        return name.split(" by ")[0].strip().title()
    # Если ничего — первые 1-2 слова
    words = name.split()
    if len(words) > 1:
        return words[0]
    return "Неизвестный бренд"

def get_name(row):
    return row.get("Name", "Без названия")

# Загрузка базы
def load_base():
    console.print("\n[bold]Выбери базу парфюмов:[/bold]")
    base_choice = Prompt.ask("1 — Моя маленькая база (для теста)\n2 — Большая база Fragrantica (тысячи ароматов)", choices=["1", "2"], default="1")

    if base_choice == "2":
        filepath = "fra_perfumes.csv"  # имя твоего скачанного файла
    else:
        filepath = "perfume_base(2).csv"

    try:
        df = pd.read_csv(filepath, encoding='utf-8')
        required = {"Name"}  # минимальные колонки, в большом датасете могут быть другие названия
        actual_columns = set(df.columns.str.lower())
        missing = required - actual_columns
        if missing:
            console.print(f"[yellow]Предупреждение: в большой базе могут быть другие названия колонок. Использую доступные.[/yellow]")
        
        console.print(f"[green]База загружена: {len(df)} ароматов из {'большой' if base_choice == '2' else 'маленькой'} базы![/green]")
        logging.info(f"Загружена база: {len(df)} записей из {filepath}")
        return df
    except FileNotFoundError:
        console.print(f"[red]Файл {filepath} не найден — используй маленькую базу или скачай большую[/red]")
        return load_base_fallback()  # fallback на маленькую
    except Exception as e:
        console.print(f"[red]Ошибка: {e}[/red]")
        return None

def load_base_fallback():
    try:
        return pd.read_csv("perfume_base(2).csv", encoding='utf-8')
    except:
        return None

# Поиск ароматов по подстроке (имя или бренд)
def search_perfumes(df: pd.DataFrame, query: str) -> pd.DataFrame:
    query = query.lower()
    mask = pd.Series([False] * len(df))  # пустая маска

    # Поиск по колонке Name (название аромата)
    if "Name" in df.columns:
        mask = mask | df["Name"].str.lower().str.contains(query, na=False)

    # Поиск по Main Accords (аккорды/ноты)
    if "Main Accords" in df.columns:
        mask = mask | df["Main Accords"].str.lower().str.contains(query, na=False)

    # Поиск по Description (если там упоминаются ноты или бренд)
    if "Description" in df.columns:
        mask = mask | df["Description"].str.lower().str.contains(query, na=False)

    # Поиск по Perfumers (если там бренд или парфюмер)
    if "Perfumers" in df.columns:
        mask = mask | df["Perfumers"].str.lower().str.contains(query, na=False)

    return df[mask].reset_index(drop=True)

# Показ результатов поиска в красивой таблице
def display_search_results(results: pd.DataFrame):
    if results.empty:
        console.print("[yellow]Ничего не найдено 😔[/yellow]")
        return None

    table = Table(title="Найденные парфюмы", box=box.ROUNDED, show_header=True, header_style="bold magenta")
    table.add_column("№", style="dim", width=4)
    table.add_column("Название", style="cyan", width=30)
    table.add_column("Аккорды", style="white", width=40)
    table.add_column("Рейтинг", style="green")
    table.add_column("Гендер", style="pink1")

    for i, row in results.iterrows():
        name = row.get("Name", "Без названия")
        accords = row.get("Main Accords", "Нет аккордов")[:60] + "..." if len(str(row.get("Main Accords", ""))) > 60 else row.get("Main Accords", "")
        rating = f"{row.get('Rating Value', 'N/A')}/5 ({row.get('Rating Count', 0)} отзывов)"
        gender = row.get("Gender", "Унисекс")

        table.add_row(
            str(i + 1),
            name,
            accords,
            rating,
            gender
        )
    
    console.print(table)
    return results

# Анализ лееринга с поддержкой пресетов
def analyze_layering(perfumes):
    # Загружаем правила
    try:
        with open("layering_rules.json", "r", encoding="utf-8") as f:
            rules = json.load(f)
        positive_rules = rules["positive"]
        risk_rules = rules["risks"]
        negative_rules = rules.get("negative", [])  # Новый раздел
    except FileNotFoundError:
        console.print("[yellow]Файл layering_rules.json не найден — использую базовые правила[/yellow]")
        positive_rules = LAYERING_RULES["positive"]
        risk_rules = LAYERING_RULES["risks"]
        negative_rules = []

    # Собираем ноты (без 'notes')
    notes_all = " "
    for p in perfumes:
        notes_all += " " + str(p.get("Main Accords", "")).lower()
        notes_all += " " + str(p.get("Description", "")).lower()

    notes_all = notes_all.strip()

    compatibility = 70
    vibe = "Unique mix — experimental and interesting 🧪"
    risks = []

    tips = ["Apply lighter/fresh scent first, heavy on top", "2–3 sprays total to avoid overload"]

    # Positive правила
    for rule in positive_rules:
        keywords = [k.lower() for k in rule["keywords"]]
        if all(word in notes_all for word in keywords):
            compatibility += rule["bonus"]
            vibe = rule["vibe"]
            if "risk" in rule and rule["risk"]:
                risks.append(rule["risk"])

    # Negative правила (уменьшают совместимость)
    for rule in negative_rules:
        keywords = [k.lower() for k in rule["keywords"]]
        if all(word in notes_all for word in keywords):
            compatibility += rule["penalty"]  # penalty отрицательное
            vibe = rule["vibe"]
            if "risk" in rule and rule["risk"]:
                risks.append(rule["risk"])

    compatibility = max(50, min(100, compatibility + len(perfumes) * 5))  # Минимум 50%, чтобы не было 0

    # Risks
    for rule in risk_rules:
        keywords = [k.lower() for k in rule["keywords"]]
        if all(word in notes_all for word in keywords):
            risks.append(rule["description"])

    if not risks:
        risks = ["Minimal — should work smoothly!"]

    return {
        "compatibility": compatibility,
        "vibe": vibe,
        "risks": risks,
        "tips": tips
    }

# Основное меню
def main():
    console.print(Panel("[bold magenta]🌸 Perfume Layering Assistant 🌸[/bold magenta]\nГенератор леерингов от [cyan]Saint[/cyan]", box=box.DOUBLE))
    
    df = load_base()
    if df is None:
        return

    selected_perfumes = []

    # Меню готовых пресетов
    console.print("\n[bold cyan]У тебя есть готовые проверенные миксы![/bold cyan]")
    use_preset = Prompt.ask("Хочешь сразу выбрать один из моих экспериментов?", choices=["y", "n"], default="n")

    if use_preset == "y":
        preset_table = Table(title="Мои готовые лееринги", box=box.ROUNDED, header_style="bold magenta")
        preset_table.add_column("№", style="dim")
        preset_table.add_column("Микс", style="cyan")
        preset_table.add_column("Краткое описание", style="white")

        preset_list = list(PRESETS.keys())
        for i, key in enumerate(preset_list, 1):
            names = " + ".join(key)
            short_vibe = PRESETS[key]["vibe"][:60] + "..." if len(PRESETS[key]["vibe"]) > 60 else PRESETS[key]["vibe"]
            preset_table.add_row(str(i), names, short_vibe)

        console.print(preset_table)

        choice = IntPrompt.ask("Выбери номер микса", choices=[str(i) for i in range(1, len(preset_list)+1)])
        selected_key = preset_list[choice - 1]

        selected_perfumes = []
        for perfume_name in selected_key:
            match = df[
                df["name"].str.contains(perfume_name.split()[-1], case=False, na=False) |
                (df["brand"] + " " + df["name"]).str.contains(perfume_name, case=False, na=False)
            ]
            if not match.empty:
                selected_perfumes.append(match.iloc[0])
            else:
                console.print(f"[red]Аромат {perfume_name} не найден в базе[/red]")

        if len(selected_perfumes) != len(selected_key):
            console.print("[yellow]Не все ароматы найдены — переходим к ручному выбору[/yellow]")
        else:
            console.print("\n[bold green]Загружен пресет:[/bold green]")
            for p in selected_perfumes:
                console.print(f"• {p['brand']} - {p['name']}")

    else:
        # Ручной выбор ароматов
        while len(selected_perfumes) < 3:
            query = Prompt.ask(f"\n[bold]Введите название или бренд для поиска аромата №{len(selected_perfumes)+1}[/bold] (или 'стоп' для завершения)")
            if query.lower() in ["стоп", "stop", "exit"]:
                break

            results = search_perfumes(df, query)
            if results.empty:
                continue

            displayed = display_search_results(results)
            if displayed is None:
                continue

            choice = IntPrompt.ask("Выберите номер парфюма", choices=[str(i+1) for i in range(len(results))], default=1)
            chosen = results.iloc[choice - 1]
            selected_perfumes.append(chosen)

            console.print(f"[green]Добавлено:[/green] {get_brand(chosen)} - {get_name(chosen)}")

    if len(selected_perfumes) < 2:
        console.print("[yellow]Нужно минимум 2 аромата для лееринга![/yellow]")
        return

    console.print("\n[bold green]Выбранные ароматы:[/bold green]")
    for p in selected_perfumes:
        console.print(f"• {get_brand(p)} - {get_name(p)} ({p.get('season', 'N/A')}, {p.get('Gender', 'Унисекс')})")

    # Генерация и вывод лееринга
    console.print("\n[bold magenta]🎭 Анализ лееринга...[/bold magenta]")
    analysis = analyze_layering(selected_perfumes)

    result_table = Table(box=box.ROUNDED, title="Результат лееринга", title_style="bold gold")
    result_table.add_column("Параметр", style="cyan")
    result_table.add_column("Описание", style="white")

    result_table.add_row("Совместимость", f"[green]{analysis['compatibility']}%[/green]")
    result_table.add_row("Ожидаемый вайб", analysis["vibe"])
    result_table.add_row("Возможные риски", "\n".join(f"• {r}" for r in analysis["risks"]))
    result_table.add_row("Советы по нанесению", "\n".join(f"• {t}" for t in analysis["tips"]))

    console.print(result_table)

    # Сохранение результата
    if Prompt.ask("\nСохранить результат в файл?", choices=["y", "n"], default="y") == "y":
        with open("last_layering.txt", "w", encoding="utf-8") as f:
            f.write(f"Лееринг от {pd.Timestamp('now').strftime('%d.%m.%Y %H:%M')}\n\n")
            for p in selected_perfumes:
                f.write(f"{get_brand(p)} - {get_name(p)} ({p.get('season', 'N/A')}, {p.get('Gender', 'Унисекс')})\n")
            f.write(f"\nСовместимость: {analysis['compatibility']}%\n")
            f.write(f"Вайб: {analysis['vibe']}\n")
            f.write("Риски:\n" + "\n".join(f"- {r}" for r in analysis["risks"]) + "\n")
            f.write("Советы:\n" + "\n".join(f"- {t}" for t in analysis["tips"]) + "\n")
        console.print("[green]Результат сохранён в last_layering.txt[/green]")

if __name__ == "__main__":
    main()