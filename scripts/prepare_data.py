"""Подготовка реальных открытых данных для проекта.
Вход: data/raw/ (Inside Airbnb NYC 2026-09-14, CC BY 4.0; NYC OSE STR registrations 2026-11-02).
Выход: data/processed/*.csv, data/processed/quality_report.md, data/processed/key_facts.md
Запуск: python scripts/prepare_data.py
"""
import pandas as pd, numpy as np, re, pathlib
R = pathlib.Path('data/raw'); P = pathlib.Path('data/processed'); P.mkdir(exist_ok=True)
L = pd.read_csv(R/'insideairbnb_nyc_2026-09-14_listings_detailed.csv.gz', low_memory=False)
n_raw = len(L)

# ---------- Реестр OSE: «склеиваем» строки-продолжения ----------
X = pd.read_excel(R/'nyc_ose_str_registrations_2026-11-02.xlsx', header=1)
X.columns = ['reg_number','status','expiration','street','unit','borough','zip','bin','booking_service','listing_ref']
reg_cols = ['reg_number','status','expiration','street','unit','borough','zip','bin']
X[reg_cols] = X[reg_cols].ffill()
X['listing_id'] = X['listing_ref'].astype(str).str.extract(r'(\d{5,})')[0]
regs = X.drop_duplicates('reg_number')[['reg_number','status','expiration','borough','zip','bin']]
reg_links = X.dropna(subset=['listing_ref'])[['reg_number','status','booking_service','listing_ref','listing_id']]

# ---------- Объявления: минимизация данных (убираем персональные поля) ----------
drop_personal = ['host_name','host_about','host_picture_url','host_thumbnail_url','host_url','host_profile_url','picture_url','host_location','description','neighborhood_overview']
L = L.drop(columns=[c for c in drop_personal if c in L.columns])

# ---------- Проверки качества ----------
q = []
def add(dim, check, bad, total, note=''):
    q.append(dict(dimension=dim, check=check, bad=int(bad), total=int(total), share_ok=round(100*(1-bad/total),1) if total else None, note=note))
dups = L.duplicated('id').sum(); add('Уникальность','Нет дублей id объявлений', dups, n_raw)
L = L.drop_duplicates('id')
L['price_num'] = pd.to_numeric(L['price'].astype(str).str.replace(r'[\$,]','',regex=True), errors='coerce')
for col,name in [('price_num','Цена'),('review_scores_rating','Рейтинг'),('bedrooms','Спальни'),('bathrooms','Ванные'),('host_since','Дата регистрации хоста'),('license','Поле license (регистрация)'),('neighbourhood_group_cleansed','Боро')]:
    add('Полнота', f'Заполнено: {name}', L[col].isna().sum(), len(L))
inbox = L.latitude.between(40.49,40.92) & L.longitude.between(-74.27,-73.68)
add('Валидность','Координаты в границах NYC', (~inbox).sum(), len(L))
add('Валидность','Цена в диапазоне $10–$10 000 (из заполненных)', (~L.price_num.dropna().between(10,10000)).sum(), L.price_num.notna().sum())
fmt = L['license'].dropna(); fmt = fmt[fmt!='Exempt']
add('Валидность','Номер регистрации в формате OSE-STRREG-XXXXXXX', (~fmt.str.fullmatch(r'OSE-STRREG-\d{7}')).sum(), len(fmt))
last = pd.to_datetime(L['last_review'], errors='coerce'); ref = pd.Timestamp('2026-09-14')
add('Актуальность','Последний отзыв не старше 12 мес. (из имеющих отзывы)', (last.dropna() < ref - pd.Timedelta(days=365)).sum(), last.notna().sum())
bad_minmax = (L.minimum_nights > L.maximum_nights).sum(); add('Непротиворечивость','minimum_nights ≤ maximum_nights', bad_minmax, len(L))

# ---------- Соответствие Local Law 18 ----------
L['short_term'] = L.minimum_nights < 30
L['lic_type'] = np.where(L.license.isna(),'нет', np.where(L.license.eq('Exempt'),'Exempt', np.where(L.license.astype(str).str.startswith('OSE-STRREG'),'номер OSE','другое')))
st = L[L.short_term].copy()
reg_status = regs.set_index('reg_number')['status']
st['reg_status_in_registry'] = st['license'].map(reg_status)
L['id_str'] = L['id'].astype(str)
linked = set(reg_links.listing_id.dropna())
st['listed_in_registry'] = st['id'].astype(str).isin(linked)
# проверка верификации: номер в объявлении есть в реестре?
osenum = st[st.lic_type=='номер OSE']
add('Верификация','Номер OSE из объявления найден в официальном реестре', (~osenum.license.isin(reg_status.index)).sum(), len(osenum), 'сверка с реестром OSE 2026-11-02')

# ---------- Сохранение ----------
keep = ['id','listing_url','last_scraped','host_id','host_since','host_is_superhost','host_identity_verified','host_listings_count','calculated_host_listings_count','neighbourhood_cleansed','neighbourhood_group_cleansed','latitude','longitude','property_type','room_type','accommodates','bedrooms','bathrooms','price_num','minimum_nights','maximum_nights','availability_365','number_of_reviews','number_of_reviews_ltm','last_review','review_scores_rating','estimated_occupancy_l365d','estimated_revenue_l365d','license','lic_type','short_term','instant_bookable']
L[keep].to_csv(P/'listings_clean.csv', index=False)
regs.to_csv(P/'ose_registrations.csv', index=False); reg_links.to_csv(P/'ose_registration_listings.csv', index=False)
Q = pd.DataFrame(q); Q.to_csv(P/'quality_checks.csv', index=False)

boro = L.groupby('neighbourhood_group_cleansed').agg(listings=('id','size'), short_term=('short_term','sum'), median_price=('price_num','median'), avg_rating=('review_scores_rating','mean')).round(2)
boro.to_csv(P/'by_borough.csv')
lic = pd.crosstab(L.short_term.map({True:'краткосрочные (<30 ночей)',False:'долгосрочные (≥30 ночей)'}), L.lic_type, margins=True)
lic.to_csv(P/'license_by_term.csv')
multi = L.groupby('host_id').size(); 
facts = {
 'Объявлений всего (Inside Airbnb, 14.09.2026)': len(L),
 'Краткосрочные (minimum_nights < 30)': int(L.short_term.sum()),
 'Доля краткосрочных, %': round(100*L.short_term.mean(),1),
 'Краткосрочные без номера регистрации и без Exempt': int((st.lic_type=='нет').sum()),
 'Краткосрочные с номером OSE': int((st.lic_type=='номер OSE').sum()),
 'Краткосрочные с Exempt': int((st.lic_type=='Exempt').sum()),
 'Номера OSE в объявлениях, не найденные в реестре': int((~osenum.license.isin(reg_status.index)).sum()),
 'Номера OSE в объявлениях со статусом не Registered': int((osenum.license.map(reg_status).fillna('нет в реестре')!='Registered').sum()),
 'Регистраций в реестре OSE (02.11.2026)': len(regs),
 'из них Registered': int((regs.status=='Registered').sum()),
 'Хостов всего': int(L.host_id.nunique()),
 'Хостов с 2+ объявлениями': int((multi>1).sum()),
 'Доля объявлений у мульти-хостов, %': round(100*L.host_id.map(multi).gt(1).mean(),1),
 'Медианная цена за ночь, $': float(L.price_num.median()),
 'Средний рейтинг (из заполненных)': round(L.review_scores_rating.mean(),2),
 'Доля рейтингов ≥ 4.5 (из заполненных), %': round(100*(L.review_scores_rating.dropna()>=4.5).mean(),1),
 'Объявлений без отзывов, %': round(100*(L.number_of_reviews==0).mean(),1),
}
with open(P/'key_facts.md','w') as f:
    f.write('# Ключевые факты (посчитано скриптом scripts/prepare_data.py по реальным данным)\n\n| Показатель | Значение |\n|---|---|\n')
    for k,v in facts.items(): f.write(f'| {k} | {v} |\n')
    f.write('\n## По районам (боро)\n\n'+boro.to_markdown()+'\n\n## Регистрация по типу аренды\n\n'+lic.to_markdown()+'\n')
with open(P/'quality_report.md','w') as f:
    f.write('# Отчёт о качестве данных (реальные проверки)\n\nИсточник: Inside Airbnb NYC 14.09.2026 + реестр OSE 02.11.2026. Строк до очистки: %d.\n\n' % n_raw)
    f.write(Q.to_markdown(index=False)+'\n\n**Минимизация данных:** при очистке удалены поля с персональными данными хостов: '+', '.join(drop_personal)+'.\n')
print(open(P/'key_facts.md').read()); print(Q.to_string())
