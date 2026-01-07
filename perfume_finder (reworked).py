import pandas as pd
import logging
from typing import Optional


# Загрузка базы парфюмов их csv файла с проверкой на ошибку.
# Loading perfume base from CSV, with errors checking
def base_load(filepath: str =
              "perfume_base(2).csv") -> Optional[pd.DataFrame]:
    try:
        df = pd.read_csv(filepath)
        required_columns = {"name", "brand", "notes", "gender", "season"}
        if not required_columns.issubset(df.columns):
            missing = required_columns - set(df.columns)
            logging.error(f"В файле отсутствуют колонки: {missing}")
            return None
        return df
    except FileNotFoundError:
        logging.error(f"Файл {filepath} не найден")
    except Exception as e:
        logging.error(f"Ошибка загрузки файла: {str(e)}")
    return None


# Система логирования.  Loging system.
def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler("perfume_finder.log", encoding='utf-8'),
            logging.StreamHandler()
        ]
    )


# Функция поиска по нотам с обработкой ошибок.
# Function of searching by notes with error handling
def search_via_notes(df: pd.DataFrame, notes: str) -> Optional[pd.DataFrame]:
    try:
        if not isinstance(notes, str):
            raise ValueError("Ноты должны быть строкой")
        notes_to_find = [n.strip().lower() for n in notes.split(",") if
                         n.strip()]
        if not notes_to_find:
            logging.warning("Получен пустой список нот для поиска")
            return pd.DataFrame()
        return df[df["notes"].apply(
            lambda x: all(
                n in [item.strip().lower() for item in str(x).split(",")]
                for n in notes_to_find
            )
        )]
    except Exception as e:
        logging.error(f"Ошибка поиска по нотам: {str(e)}", exc_info=True)
        return None


# Функция поиска по бренду.  Function of searching by brand
def search_via_brand(df: pd.DataFrame, brands: str) -> Optional[pd.DataFrame]:
    try:
        if not isinstance(brands, str):
            raise ValueError("Бренд должен быть строкой")
        brands_to_find = [b.strip().lower() for b in brands.split(",") if
                          b.strip()]
        if not brands_to_find:
            logging.warning("Нет бренда для поиска")
            return pd.DataFrame()
        return df[df["brands"].apply(
            lambda x: all(
                b in [item.strip().lower() for item in str(x).split(",")]
                for b in brands_to_find
            )
        )]
    except Exception as e:
        logging.error(f"Ошибка поиска по бренду: {str(e)}", exc_info=True)
        return None


# Функция поиска по полу.  Function of searching by gender
def search_via_gender(df: pd.DataFrame, gender: str) -> Optional[pd.DataFrame]:
    try:
        if not isinstance(gender, str):
            raise ValueError("Пол должен быть строкой")
        gender_to_find = [g.strip().lower() for g in gender.split(",") if
                          g.strip()]
        if not gender_to_find:
            logging.warning("Нет пола для поиска")
            return pd.DataFrame()
        return df[df["gender"].apply(
            lambda x: all(
                g in [item.strip().lower() for item in str(x).split(",")]
                for g in gender_to_find
            )
        )]
    except Exception as e:
        logging.error(f"Ошибка поиска по полу: {str(e)}", exc_info=True)
        return None


# Функция поиска по сезону. Function of searching by season
def search_via_season(df: pd.DataFrame, season: str) -> Optional[pd.DataFrame]:
    try:
        if not isinstance(season, str):
            raise ValueError("Сезон должен быть строкой")
        season_to_find = [s.strip().lower() for s in season.split(",") if
                          s.strip()]
        if not season_to_find:
            logging.warning("Нет сезона для поиска")
            return pd.DataFrame()
        return df[df["season"].apply(
            lambda x: all(
                s in [item.strip().lower() for item in str(x).split(",")]
                for s in season_to_find
            )
        )]
    except Exception as e:
        logging.error(f"Ошибка поиска по сезону: {str(e)}", exc_info=True)
        return None


# Словарь с переменными по которым можно искать парфюмы.
# Dictionary with variables by which is possible to search perfume.
search_dictionary = {
    "ноты": search_via_notes,
    "бренд": search_via_brand,
    "гендер": search_via_gender,
    "сезон": search_via_season
    }


# Главная функция.  Main function
def main():
    setup_logging()
    logging.info("Запуск программы")
    df = base_load()
    if df is None:
        logging.critical("Не удалось загрузить данные. Программа остановлена.")
        return
    try:
        print("Доступен поиск по: нотам, бренду, гендеру, сезону\n")
        aspect = input("Введите аспект поиска: ").strip().lower()
        if aspect not in search_dictionary:
            print("Такого аспекта нет")
            logging.warning
            (f"Попытка поиска по несуществующему аспекту: {aspect}")
            return
        search_query = input(f"Что вы ищете по {aspect}: ").strip()
        if not search_query:
            print("Пустой запрос")
            logging.warning("Получен пустой поисковый запрос")
            return
        result = search_dictionary[aspect](df, search_query)
        if result is None:
            print("Произошла ошибка при поиске")
        elif not result.empty:
            print("\nРезультаты:")
            print(result[["name", "brand", "notes"]])
            logging.info
            (f"Найдено {len(result)} результатов для '{search_query}'")
        else:
            print("Ничего не найдено")
            logging.info(f"Нет результатов для '{search_query}'")
    except KeyboardInterrupt:
        logging.info("Программа прервана пользователем")
    except Exception as e:
        logging.critical(f"Критическая ошибка: {str(e)}", exc_info=True)


if __name__ == "__main__":
    main()
