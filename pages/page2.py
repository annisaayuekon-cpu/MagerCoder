import streamlit as st
import pandas as pd
import plotly.express as px
import wb_helper as wb

st.set_page_config(layout="wide")

st.title("👷 Tenaga Kerja dan Pengangguran")
st.write("Visualisasi indikator ketenagakerjaan dan pengangguran dari World Bank dalam bentuk peta dunia dan grafik time series.")

# ------------------------------------
# Pilihan indikator tenaga kerja
# ------------------------------------
INDICATORS = {
    "Unemployment rate (% of total labor force)": "SL.UEM.TOTL.ZS",
    "Youth unemployment (% ages 15–24)": "SL.UEM.1524.ZS",
    "Labor force participation rate (% of population ages 15+)": "SL.TLF.CACT.ZS",
    "Employment in agriculture (% of total employment)": "SL.AGR.EMPL.ZS",
    "Employment in industry (% of total employment)": "SL.IND.EMPL.ZS",
    "Employment in services (% of total employment)": "SL.SRV.EMPL.ZS",
}

indicator_label = st.selectbox("Pilih indikator tenaga kerja", list(INDICATORS.keys()))
indicator_code = INDICATORS[indicator_label]

# ------------------------------------
# Ambil data dari helper World Bank
# ------------------------------------
@st.cache_data
def load_indicator(code: str) -> pd.DataFrame:
    """
    Mengambil data indikator dari wb_helper.
    Diasumsikan wb.fetch_indicator() mengembalikan kolom:
    country, iso (opsional), year, value
    """
    # kalau di helper kamu ada fungsi countries_default(), bisa dipakai seperti ini
    try:
        countries = wb.countries_default()
        df = wb.fetch_indicator(code, countries)
    except Exception:
        # fallback kalau helper kamu memakai argumen berbeda
        df = wb.fetch_indicator(code)
    return df

df = load_indicator(indicator_code)

if df.empty:
    st.error("Data untuk indikator ini tidak tersedia.")
    st.stop()

# pastikan tipe tahun integer
df["year"] = df["year"].astype(int)

# ------------------------------------
# Slider tahun untuk peta
# ------------------------------------
years = sorted(df["year"].unique())
year_min, year_max = min(years), max(years)
selected_year = st.slider("Pilih tahun untuk peta dunia", year_min, year_max, year_max)

# ------------------------------------
# Peta dunia choropleth
# ------------------------------------
st.subheader(f"🌍 Peta Dunia — {indicator_label} ({selected_year})")

df_map = df[df["year"] == selected_year].dropna(subset=["value"]).copy()

if df_map.empty:
    st.warning("Tidak ada data untuk tahun yang dipilih.")
else:
    # jika wb_helper menyediakan kolom iso3, gunakan itu
    iso_col = None
    for cand in ["iso3", "iso", "country_code", "iso_code"]:
        if cand in df_map.columns:
            iso_col = cand
            break

    if iso_col is not None:
        fig = px.choropleth(
            df_map,
            locations=iso_col,
            color="value",
            hover_name="country",
            color_continuous_scale="Viridis",
            title=f"{indicator_label} ({selected_year})",
            labels={"value": indicator_label},
        )
    else:
        # pakai nama negara sebagai fallback
        fig = px.choropleth(
            df_map,
            locations="country",
            locationmode="country names",
            color="value",
            hover_name="country",
            color_continuous_scale="Viridis",
            title=f"{indicator_label} ({selected_year})",
            labels={"value": indicator_label},
        )

    fig.update_layout(margin={"r": 0, "t": 40, "l": 0, "b": 0})
    st.plotly_chart(fig, use_container_width=True)

# ------------------------------------
# Time series per negara
# ------------------------------------
st.subheader("📈 Time Series per Negara")

country_list = sorted(df["country"].dropna().unique().tolist())
selected_country = st.selectbox("Pilih negara untuk time series", country_list)

df_country = df[df["country"] == selected_country].sort_values("year")

if df_country.empty:
    st.write("Tidak ada data time series untuk negara ini.")
else:
    ts = df_country.set_index("year")["value"]
    st.line_chart(ts, height=350)
    st.dataframe(df_country.reset_index(drop=True))

# ------------------------------------
# Tabel lengkap dan unduh CSV
# ------------------------------------
st.subheader("📘 Data Lengkap (long format)")

st.dataframe(df.reset_index(drop=True), use_container_width=True)

csv = df.to_csv(index=False)
st.download_button(
    "⬇ Download data sebagai CSV",
    csv,
    file_name=f"tenaga_kerja_{indicator_code}.csv",
    mime="text/csv",
)
