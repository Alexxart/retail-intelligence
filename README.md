# RETAIL INTELLIGENCE · Stage 4
Александр Артёмов | Data Analyst

Практический кейс синтетической мебельной сети, 2024–2025. Hoff — отраслевой референс, не работодатель и не источник внутренних данных.

## Запуск (из корня проекта)
1. Открыть `dashboard.html` в современном браузере: интернет и сервер не нужны.
2. Для пересборки HTML из сохранённого снимка: `pip install -r requirements.txt`, затем `python scripts/dashboard.py`.
3. Для полного пересчёта на существующих исходных данных: `python scripts/analyze.py`, `python scripts/factors.py`, `python scripts/build.py`, `python scripts/stage3.py`, `python scripts/dashboard.py`. factors импортирует stock_metrics; build создаёт первые 21 запрос и промежуточный Notebook; stage3 расширяет до 29 запросов и исполняет итоговый Notebook. Генератор запускать только для намеренного восстановления синтетического снимка (`python scripts/generate.py` перед шагом 3).
4. Notebook: `Retail_Analysis.ipynb`, рабочая директория — корень проекта.
5. PostgreSQL: в пустой базе из корня проекта `psql -v ON_ERROR_STOP=1 -d retail -f sql/schema_postgresql.sql -f sql/import.psql -f sql/view_postgresql.sql -f sql/analysis_postgresql.sql`. 29 запросов; PostgreSQL не исполнялся. SQLite проверен на Stage 3.
6. Браузерный тест: установить playwright, иметь Chromium (`/usr/bin/chromium` или изменить путь в тесте), `python scripts/test_dashboard.py`.

## Структура
14 исходных файлов, обработанные витрины и результаты, 29 SQL-запросов в каждой версии диалекта, исполненный Notebook, автономный HTML, четыре снимка в images, документация docs. `docs/dashboard_template.html` — шаблон, `scripts/dashboard.py` — сборщик. `docs/dashboard.js` — архивный скрипт прежней версии (не используется).

## Источники отраслевого контекста
- https://hoff.ru/about/
- https://loginom.ru/sites/default/files/global-files/textpage/2025/Hoff_Reshape.pdf
- https://www.retail.ru/news/hoff-v-2023-godu-vyruchka-kompanii-vyrosla-na-16-25-yanvarya-2024-237004/

Методология и ограничения: docs/methodology.md, docs/factor_analysis.md, docs/inventory.md, docs/stage3.md, docs/stage4.md. Проверки: docs/quality.md.
