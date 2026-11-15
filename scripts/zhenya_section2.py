"""Доп. расчёты к разделам 2.2, 2.3 и 5 (Женя).

Запуск из корня репозитория: python3 scripts/zhenya_section2.py
Читает data/processed/*.csv и печатает цифры, использованные в report/2_Zhenya.md.
"""
import pandas as pd

L = pd.read_csv("data/processed/listings_clean.csv", low_memory=False, dtype={"id": str})
R = pd.read_csv("data/processed/ose_registrations.csv")
RL = pd.read_csv("data/processed/ose_registration_listings.csv", dtype=str)  # id как текст: 19-значные номера теряют точность в float
st = L[L.short_term].copy()
ref = pd.Timestamp("2026-09-14")

print("Строк:", len(L), "| дублей id:", L.id.duplicated().sum(), "| краткосрочных:", len(st))

# Полнота
print("\nПОЛНОТА")
print("цена, все:", round(L.price_num.notna().mean() * 100, 1), "| краткосрочные:", round(st.price_num.notna().mean() * 100, 1))
print("рейтинг:", round(L.review_scores_rating.notna().mean() * 100, 1))
print("статус регистрации у краткосрочных (не пусто):", round((st.lic_type != "нет").mean() * 100, 1))

# Валидность
print("\nВАЛИДНОСТЬ")
num = st[st.lic_type.isin(["номер OSE", "другое"])]
ok = num.license.str.fullmatch(r"OSE-STRREG-\d{7}")
print("формат номера у краткосрочных: ок", ok.sum(), "из", len(num), "=", round(ok.mean() * 100, 1), "%")
print("после upper() ок:", num.license.str.upper().str.fullmatch(r"OSE-STRREG-\d{7}").sum())
p = L.price_num.dropna()
print("цена вне $10-10000:", (~p.between(10, 10000)).sum(), "из", len(p), "| максимум:", p.max())

# Верификация
print("\nВЕРИФИКАЦИЯ")
o = st[st.lic_type == "номер OSE"].merge(R, left_on="license", right_on="reg_number", how="left")
print("номеров:", len(o), "| найдено в реестре:", o.status.notna().sum())
print(o.status.value_counts().to_string())
pairs = set(zip(RL.reg_number, RL.listing_id))
o["same_listing"] = [(a, str(b)) in pairs for a, b in zip(o.license, o.id)]
print("номер привязан в реестре к этому же объявлению:", o.same_listing.sum(), "из", len(o), "=", round(o.same_listing.mean() * 100, 1), "%")
print("Exempt (верифицировать нечем):", (st.lic_type == "Exempt").sum(), "=", round((st.lic_type == "Exempt").mean() * 100, 1), "%")

# Актуальность
print("\nАКТУАЛЬНОСТЬ")
lr = pd.to_datetime(L.last_review)
has = lr.notna()
print("с отзывами:", has.sum(), "| отзыв <= 12 мес.:", round((lr[has] >= ref - pd.Timedelta(days=365)).mean() * 100, 1), "%")
print("последний отзыв старше 3 лет:", (lr[has] < ref - pd.Timedelta(days=3 * 365)).sum(), "=", round((lr[has] < ref - pd.Timedelta(days=3 * 365)).mean() * 100, 1), "%")
print("без отзывов вообще:", (~has).sum(), "=", round((~has).mean() * 100, 1), "%")
lrs = pd.to_datetime(st.last_review); hs = lrs.notna()
print("краткосрочные: отзыв <= 12 мес.:", round((lrs[hs] >= ref - pd.Timedelta(days=365)).mean() * 100, 1), "% из", hs.sum())
print("дней между снимком S1 и реестром S2:", (pd.Timestamp("2026-11-02") - ref).days)

# Непротиворечивость
print("\nНЕПРОТИВОРЕЧИВОСТЬ")
print("min_nights > max_nights:", (L.minimum_nights > L.maximum_nights).sum())
print("долгосрочные (>=30 ночей) с номером OSE:", ((~L.short_term) & (L.lic_type == "номер OSE")).sum())
vc = st[st.lic_type == "номер OSE"].license.value_counts()
print("номеров OSE на 2+ объявлениях:", (vc > 1).sum(), "из", len(vc))
