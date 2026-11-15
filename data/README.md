# Данные проекта (все реальные, открытые)

| ID | Источник | Файл | Дата | Лицензия / условия |
|---|---|---|---|---|
| S1 | Inside Airbnb — объявления Airbnb в Нью-Йорке (90 полей) | `raw/insideairbnb_nyc_2026-09-14_listings_detailed.csv.gz` (+ краткая версия `_summary.csv`) | 14.09.2026 | CC BY 4.0, обязательна ссылка на Inside Airbnb. https://insideairbnb.com/get-the-data/ |
| S2 | Реестр регистраций краткосрочной аренды NYC, Office of Special Enforcement (публикуется по Local Law 18) | `raw/nyc_ose_str_registrations_2026-11-02.xlsx` | 02.11.2026 | Официальная публикация мэрии NYC: https://www.nyc.gov/site/specialenforcement/registration-law/registration-and-listing-data.page (условия использования — проверить на nyc.gov) |
| S3 | Inside Airbnb — границы районов | `raw/..._neighbourhoods.geojson`, `.csv` | 14.09.2026 | CC BY 4.0 |

Загружено автоматически сценарием `.github/workflows/fetch-data.yml` (GitHub Actions) — это и есть пример автоматизированного сбора (ingestion).

## Обработанные файлы (`processed/`) — создаёт `scripts/prepare_data.py`
- `listings_clean.csv` — объявления без персональных полей хостов (минимизация данных); добавлены `price_num`, `short_term` (minimum_nights < 30), `lic_type` (нет / Exempt / номер OSE / другое).
- `ose_registrations.csv` — 1 строка = 1 регистрация; `ose_registration_listings.csv` — связи регистрация → объявление.
- `quality_checks.csv`, `quality_report.md` — реальные проверки качества (полнота, валидность, актуальность, непротиворечивость, верификация по реестру).
- `key_facts.md` — ключевые цифры (baseline для SMART).
- `by_borough.csv`, `license_by_term.csv` — сводные таблицы.

## Графики (`charts/`)
1. `1_registration_status.png` — статус регистрации краткосрочных объявлений.
2. `2_quality_checks.png` — качество данных.
3. `3_by_borough.png` — объявления по районам.

## Важные оговорки
- Inside Airbnb — публичная копия объявлений с сайта Airbnb, а не внутренняя база компании. Снимок на одну дату.
- Поля `bathrooms` и `host_since` в этом выпуске пустые (0% заполнения) — это свойство источника, а не ошибка обработки.
- «Exempt» — заявление хоста об освобождении от регистрации; по открытым данным его проверить нельзя.
