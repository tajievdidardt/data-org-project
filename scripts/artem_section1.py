"""Доп. расчёты к разделам 1 и 2.1 (Артём).

Запуск из корня репозитория: python3 scripts/artem_section1.py
Читает data/processed/*.csv, печатает цифры и рисует data/charts/4_exempt_hotel_split.png.
"""
import re

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

L = pd.read_csv("data/processed/listings_clean.csv", low_memory=False)
R = pd.read_csv("data/processed/ose_registrations.csv")
st = L[L.short_term].copy()

# Объекты гостиничного типа (кандидаты на исключение Class B): по property_type / room_type Inside Airbnb
HOTEL_RE = r"hotel|Hotel|resort|hostel|aparthotel|serviced"
st["hotel_like"] = st.property_type.str.contains(HOTEL_RE, regex=True) | (st.room_type == "Hotel room")

print("Краткосрочных:", len(st))
print(pd.crosstab(st.lic_type, st.hotel_like, margins=True))

# 1) Неверный формат номера
pat = re.compile(r"^OSE-STRREG-\d{7}$")
bad = st[st.lic_type == "другое"].license.astype(str)
print("\nНеверный формат:", len(bad), "| только регистр букв:", bad.str.upper().str.match(pat).sum(),
      "| после upper() найдены в реестре:", bad.str.upper().isin(R.reg_number).sum())

# 2) Статусы номеров OSE из объявлений
m = st[st.lic_type == "номер OSE"].merge(R, left_on="license", right_on="reg_number", how="left")
print("\nСтатусы номеров из объявлений:\n", m.status.value_counts(dropna=False))
vc = m.license.value_counts()
print("Уникальных номеров:", m.license.nunique(), "| номеров в 2+ объявлениях:", (vc > 1).sum(),
      "| объявлений с такими номерами:", vc[vc > 1].sum(), "| максимум на 1 номер:", vc.max())
print("\nРеестр OSE по статусам:\n", R.status.value_counts())

# 3) Разбор M1 и M2
no = st[st.lic_type == "нет"]
ex = st[st.lic_type == "Exempt"]
ex_nh = ex[~ex.hotel_like]
print("\nM1: без регистрации", len(no), "| гостиничного типа", no.hotel_like.sum(),
      "| прочие", (~no.hotel_like).sum())
print("M2: Exempt", len(ex), "| гостиничного типа", ex.hotel_like.sum(), "| прочие", len(ex_nh))
print("   прочие Exempt, Entire home/apt:", (ex_nh.room_type == "Entire home/apt").sum(),
      "| с отзывами за 12 мес.:", (ex_nh.number_of_reviews_ltm > 0).sum(),
      "| хостов:", ex_nh.host_id.nunique())
print("   оценка выручки Inside Airbnb за 12 мес., $ млн:", round(ex_nh.estimated_revenue_l365d.sum() / 1e6, 1),
      "(есть у", ex_nh.estimated_revenue_l365d.notna().sum(), "объявлений)")
print("   по боро:\n", ex_nh.neighbourhood_group_cleansed.value_counts())

# 4) Полнота цены среди краткосрочных
print("\nЦена заполнена у краткосрочных:", round(st.price_num.notna().mean() * 100, 1), "%")

# График
cats = ["Exempt", "нет"]
labels = ["Exempt (2 826)", "Нет регистрации (757)"]
h = [ex.hotel_like.sum(), no.hotel_like.sum()]
o = [len(ex_nh), (~no.hotel_like).sum()]
fig, ax = plt.subplots(figsize=(10, 3.6))
ax.barh(labels, h, color="#9aa5b1", label="объекты гостиничного типа (кандидаты на Class B)")
ax.barh(labels, o, left=h, color="#c0392b", label="квартиры, дома, комнаты")
for i in range(2):
    ax.text(h[i] / 2, i, f"{h[i]}", va="center", ha="center", color="white", fontsize=11)
    ax.text(h[i] + o[i] + 30, i, f"{o[i]}", va="center", fontsize=11, color="#c0392b")
ax.invert_yaxis()
ax.set_xlim(0, 3300)
ax.spines[["top", "right"]].set_visible(False)
ax.set_title("Краткосрочные объявления без номера OSE: кто это", loc="left", fontsize=13)
ax.legend(loc="lower right", frameon=False, fontsize=9)
fig.text(0.01, 0.01, "Источник: Inside Airbnb NYC 14.09.2026 (CC BY 4.0); тип объекта по полям property_type/room_type; расчёт команды",
         fontsize=8)
fig.tight_layout(rect=(0, 0.04, 1, 1))
fig.savefig("data/charts/4_exempt_hotel_split.png", dpi=150)
print("\nГрафик: data/charts/4_exempt_hotel_split.png")
