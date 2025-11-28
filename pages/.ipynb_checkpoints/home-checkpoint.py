# pages/home.py
import streamlit as st
import pandas as pd
import wb_helper as wb  # pastikan wb_helper.py ada di root project

st.set_page_config(layout="wide")

# ---------- Controls (pilihan negara & tahun) ----------
st.markdown("## 🌍 Dashboard Ekonomi (Ringkasan)")
st.write("Ringkasan cepat untuk beberapa indikator utama. Pilih negara dan rentang tahun untuk memperbarui tampilan.")

# gunakan daftar negara default dari wb_helper, tapi tampilkan nama lengkap (user memilih 1 negara agar KPI lebih jelas)
countries_df = wb.fetch_countries()  # returns dataframe with columns ['wb_id','iso','name',...]
country_names = countries_df["name"].tolist()
default = "Indonesia" if "Indonesia" in country_names else country_names[0]

colA, colB = st.columns([3, 1])
with colA:
    country = st.selectbox("Pilih negara untuk ringkasan", country_names, index=country_names.index(default))
with colB:
    year_min, year_max = st.slider("Rentang tahun", 1960, 2023, (2015, 2022))

# helper: get ISO2 for selected country
selected_iso = countries_df.loc[countries_df["name"] == country, "iso"].values
if len(selected_iso) == 0:
    st.error("Kode negara tidak ditemukan.")
    st.stop()
iso = selected_iso[0]

# small util: fetch indicator and get latest two values for delta
def latest_and_delta(indicator_code, iso_code, year_min=None, year_max=None):
    df = wb.fetch_indicator(indicator_code, [iso_code])
    if df.empty:
        return None, None
    # filter years
    if year_min is not None and year_max is not None:
        df = df[(df["year"] >= year_min) & (df["year"] <= year_max)]
    # sort descending by year
    df = df.sort_values("year", ascending=False)
    # latest value and previous (for delta)
    if df.shape[0] == 0:
        return None, None
    latest = df.iloc[0]["value"]
    prev = df.iloc[1]["value"] if df.shape[0] > 1 else None
    return latest, prev

# ---------- KPI ROW (4 cards) ----------
kpi_cols = st.columns(4, gap="large")

# Indicators to use
ind_gdp_growth = "NY.GDP.MKTP.KD.ZG"
ind_inflation = "FP.CPI.TOTL.ZG"
ind_unemp = "SL.UEM.TOTL.ZS"
ind_poverty = "SI.POV.DDAY"  # mungkin NaN untuk beberapa negara

# fetch values
g_latest, g_prev = latest_and_delta(ind_gdp_growth, iso, year_min, year_max)
i_latest, i_prev = latest_and_delta(ind_inflation, iso, year_min, year_max)
u_latest, u_prev = latest_and_delta(ind_unemp, iso, year_min, year_max)
p_latest, p_prev = latest_and_delta(ind_poverty, iso, year_min, year_max)

# display metrics (safely handle None)
def show_metric(col, label, val, prev, unit=""):
    if val is None:
        col.write(f"**{label}**")
        col.write("Data tidak tersedia")
    else:
        # compute delta for display
        delta_text = None
        if prev is not None and prev != 0 and pd.notna(prev):
            try:
                delta_val = val - prev
                # show relative % if values are large? we'll show absolute delta
                col.metric(label, f"{val:,.2f}{unit}", delta=f"{delta_val:+.2f}")
            except Exception:
                col.metric(label, f"{val}", delta=None)
        else:
            col.metric(label, f"{val:,.2f}{unit}")

show_metric(kpi_cols[0], "GDP growth (annual %)", g_latest, g_prev, unit="%")
show_metric(kpi_cols[1], "Inflation (CPI, %)", i_latest, i_prev, unit="%")
show_metric(kpi_cols[2], "Unemployment (%)", u_latest, u_prev, unit="%")
show_metric(kpi_cols[3], "Poverty (% $2.15/day)", p_latest, p_prev, unit="%")

st.divider()

# ---------- MINI CHARTS ROW ----------
st.subheader("Tren Singkat (mini-chart)")

mini_col1, mini_col2, mini_col3, mini_col4 = st.columns(4)

# function untuk membuat mini line chart (sparkline)
def plot_mini(indicator_code, col_obj, title):
    df = wb.fetch_indicator(indicator_code, [iso])
    if df.empty:
        col_obj.write(title)
        col_obj.write("Data tidak tersedia")
        return
    df2 = df[(df["year"] >= year_min) & (df["year"] <= year_max)].pivot(index="year", columns="country", values="value")
    col_obj.write(title)
    # show latest value and a small chart
    try:
        latest_val = df2.iloc[-1, 0]
    except Exception:
        latest_val = None
    if latest_val is not None and pd.notna(latest_val):
        col_obj.caption(f"Nilai terakhir: {latest_val:,.2f}")
    col_obj.line_chart(df2, height=120)

plot_mini("NY.GDP.MKTP.CD", mini_col1, "GDP (current US$)")
plot_mini("NY.GDP.PCAP.CD", mini_col2, "GDP per capita (US$)")
plot_mini("FP.CPI.TOTL.ZG", mini_col3, "Inflation (annual %)")
plot_mini("EN.ATM.CO2E.PC", mini_col4, "CO₂ per kapita")

st.divider()

# ---------- MAIN CHART AREA ----------
st.subheader("Grafik Perbandingan Indikator (lebih besar)")
main_col1, main_col2 = st.columns([2, 1])

with main_col1:
    # user pilih indikator untuk perbandingan
    possible_inds = {
        "GDP growth (%)": "NY.GDP.MKTP.KD.ZG",
        "GDP per capita (US$)": "NY.GDP.PCAP.CD",
        "Inflation (CPI, %)": "FP.CPI.TOTL.ZG",
        "Unemployment (%)": "SL.UEM.TOTL.ZS",
        "CO2 per capita": "EN.ATM.CO2E.PC"
    }
    sel = st.selectbox("Pilih indikator untuk grafik besar", list(possible_inds.keys()))
    code = possible_inds[sel]
    # also allow compare up to 3 countries quickly
    compare_countries = st.multiselect("Bandingkan negara (opsional)", country_names, default=[country], max_selections=3)
    # resolve iso codes
    compare_isos = countries_df.loc[countries_df["name"].isin(compare_countries), "iso"].tolist()
    df_main = wb.fetch_indicator(code, compare_isos)
    if df_main.empty:
        st.warning("Tidak ada data untuk kombinasi yang dipilih.")
    else:
        df_p = df_main[(df_main["year"] >= year_min) & (df_main["year"] <= year_max)].pivot(index="year", columns="country", values="value")
        st.line_chart(df_p, height=350)
        st.dataframe(df_p.tail(20).reset_index())

with main_col2:
    st.subheader("Ringkasan cepat")
    st.write(f"Negara utama: **{country}**")
    st.write(f"Rentang tahun: **{year_min} – {year_max}**")
    st.write("Indikator rekomendasi untuk analisis:")
    st.markdown("- GDP growth\n- Inflation\n- Unemployment\n- Poverty\n- FDI / Trade")

st.divider()

# ---------- BOTTOM: Additional small bar chart (example: population by year) ----------
st.subheader("Populasi (contoh visualisasi bar)")
pop_df = wb.fetch_indicator("SP.POP.TOTL", [iso])
if not pop_df.empty:
    pop_df2 = pop_df[(pop_df["year"] >= year_min) & (pop_df["year"] <= year_max)].pivot(index="year", columns="country", values="value")
    st.bar_chart(pop_df2)
else:
    st.write("Data populasi tidak tersedia untuk rentang yang dipilih.")
