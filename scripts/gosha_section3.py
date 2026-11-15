"""Расчёты к разделу 3 (Гоша): проверка гипотез на открытых данных.

Запуск из корня репозитория: python3 scripts/gosha_section3.py
Читает data/processed/*.csv, печатает цифры и рисует data/charts/5_hypotheses.png.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

L = pd.read_csv("data/processed/listings_clean.csv", low_memory=False, dtype={"id": str})
R = pd.read_csv("data/processed/ose_registrations.csv")
RL = pd.read_csv("data/processed/ose_registration_listings.csv", dtype=str)
st = L[L.short_term].copy()
# то же определение гостиничного типа, что в scripts/artem_section1.py
HOTEL_RE = r"hotel|Hotel|resort|hostel|aparthotel|serviced"
st["hotel"] = st.property_type.str.contains(HOTEL_RE, regex=True) | (st.room_type == "Hotel room")
st["multi"] = st.calculated_host_listings_count >= 2
st["no"] = st.lic_type == "нет"
st["ex"] = st.lic_type == "Exempt"
nh = st[~st.hotel].copy()
nh["gap"] = nh.no | nh.ex  # нет ни номера OSE, ни гостиничного основания для исключения

def tab(df, by):
    g = df.groupby(by).agg(n=("id", "size"), no=("no", "sum"), ex=("ex", "sum"))
    g["no_%"] = (100 * g.no / g.n).round(1); g["ex_%"] = (100 * g.ex / g.n).round(1)
    return g

print("H1. Мульти-хосты, ВСЕ краткосрочные:\n", tab(st, "multi"))
print("\nH1. Мульти-хосты, БЕЗ гостиничного типа:\n", tab(nh, "multi"))
print("\nH2. Боро, ВСЕ краткосрочные:\n", tab(st, "neighbourhood_group_cleansed"))
print("\nH2. Боро, БЕЗ гостиничного типа:\n", tab(nh, "neighbourhood_group_cleansed"))
print("\nДоля гостиничного типа по боро:\n", (100 * st.groupby("neighbourhood_group_cleansed").hotel.mean()).round(1))

o = st[st.lic_type == "номер OSE"]
vc = o.license.value_counts()
hosts = o.groupby("license").host_id.nunique()
print("\nH3. Уникальных номеров:", len(vc), "| на 2+ объявлениях:", (vc > 1).sum(), "=", round(100 * (vc > 1).mean(), 1), "%",
      "| объявлений с такими номерами:", vc[vc > 1].sum(), "| максимум:", vc.max(), "| номеров у 2+ разных хостов:", (hosts > 1).sum())
print("   распределение (объявлений на номер -> номеров):", vc.value_counts().sort_index().to_dict())

# Искажения
a = RL[RL.booking_service == "Airbnb"]
ids = set(a.listing_id.dropna())
print("\nОшибка выжившего: объявлений Airbnb в реестре OSE:", len(ids), "| есть в снимке S1:", len(ids & set(L.id)),
      "| нет в снимке:", len(ids - set(L.id)), "=", round(100 * len(ids - set(L.id)) / len(ids), 1), "%")
reg = R[R.status == "Registered"].reg_number
print("Действующих регистраций:", len(reg), "| не встречаются ни в одном объявлении снимка:", (~reg.isin(L.license)).sum())
print("Площадки в реестре:\n", RL.booking_service.value_counts().to_string())
r = L.review_scores_rating.dropna()
print("\nГудхарт: рейтингов:", len(r), "| >=4.5:", round(100 * (r >= 4.5).mean(), 1), "% | >=4.8:", round(100 * (r >= 4.8).mean(), 1),
      "% | <4.0:", round(100 * (r < 4).mean(), 1), "% | медиана:", r.median())
print("Без отзывов: все", round(100 * (L.number_of_reviews == 0).mean(), 1), "% | краткосрочные", round(100 * (st.number_of_reviews == 0).mean(), 1), "%")

# График
fig, ax = plt.subplots(1, 2, figsize=(11, 3.8))
g1 = nh.groupby("multi").gap.mean() * 100
ax[0].bar(["1 объявление\n(n=%d)" % (~nh.multi).sum(), "2+ объявлений\n(n=%d)" % nh.multi.sum()], g1.values, color=["#9aa5b1", "#c0392b"])
for i, v in enumerate(g1.values): ax[0].text(i, v + 1.5, f"{v:.1f}%", ha="center", fontsize=11)
ax[0].set_title("По типу хоста", loc="left", fontsize=11)
g2 = (nh.groupby("neighbourhood_group_cleansed").gap.mean() * 100).sort_values(ascending=False)
n2 = nh.groupby("neighbourhood_group_cleansed").size()
ax[1].bar([f"{b}\n(n={n2[b]})" for b in g2.index], g2.values, color=["#c0392b"] + ["#9aa5b1"] * 4)
for i, v in enumerate(g2.values): ax[1].text(i, v + 1.5, f"{v:.1f}%", ha="center", fontsize=11)
ax[1].set_title("По боро", loc="left", fontsize=11)
for x in ax:
    x.set_ylim(0, 95); x.spines[["top", "right"]].set_visible(False); x.set_ylabel("%"); x.tick_params(axis="x", labelsize=8)
fig.suptitle("Краткосрочные квартиры, дома и комнаты без номера OSE (нет регистрации или «Exempt»)", x=0.01, ha="left", fontsize=12)
fig.text(0.01, 0.01, "Источник: Inside Airbnb NYC 14.09.2026 (CC BY 4.0); без объектов гостиничного типа; расчёт команды", fontsize=8)
fig.tight_layout(rect=(0, 0.04, 1, 0.93))
fig.savefig("data/charts/5_hypotheses.png", dpi=150)
print("\nГрафик: data/charts/5_hypotheses.png")
