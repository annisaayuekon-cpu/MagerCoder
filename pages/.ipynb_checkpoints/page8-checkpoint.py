# pages/page8.py

import os

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(layout="wide")

st.title("🎓 Pendidikan — Peta Dunia + Time Series")
st.write(
    "Halaman ini menampilkan indikator **pendidikan global** seperti *School Enrollment* "
    "dan *Government Expenditure on Education* berdasarkan file CSV yang berada dalam folder `data/`."
)

# -----------------------------
# Folder dataset
# -----------------------------
DATA_DIR = "data"

FILES = {
    "School Enrollment (%)": "8.1. SCHOOL ENROLLMENT.csv",
    "Government Expenditure on Education (% of GDP)": "8.2. GOVENRMENT EXPENDITURE ON EDUCATION.csv",
}

# -----------------------------
# Loader CSV fleksibel
# -----------------------------
@st.cache_data
def load_csv_clean(path: str) -> pd.DataFrame:
    for sep in [";", ",", "\t"]:
        try:
            df = pd.read_csv(path, sep=sep, engine="python", on_bad_lines="skip")
            if df.shape[1] > 1:
                return df
        except Exception:
            pass
    return pd.read_csv(path, engine="python", on_bad_lines="skip")


# -----------------------------
# Cek file tersedia?
# -----------------------------
available_files = [
    label
    for label, fname in FILES.items()
    if os.path.exists(os.path.join(DATA_DIR, fname))
]

if not available_files:
    st.error(f"Tidak ada file Page 8 ditemukan dalam folder `{DATA_DIR}/`.")
    st.stop()

# -----------------------------
# Pilih indikator dataset
# -----------------------------
indicator = st.selectbox("📌 Pilih indikator pendidikan :", available_files)
file_path = os.path.join(DATA_DIR, FILES[indicator])

try:
    df = load_csv_clean(file_path)
except Exception as e:
    st.error(f"❌ File gagal dibaca: `{os.path.basename(file_path)}`\n\n{e}")
    st.stop()

st.subheader("📄 Preview Data Mentah")
st.dataframe(df.head(20), use_container_width=True)

# -----------------------------
# Identifikasi Tahun & Negara
# -----------------------------
cols = [str(c) for c in df.columns]
years = [c for c in cols if c.isdigit() and len(c) == 4]

if not years:
    st.error("Tidak ditemukan kolom tahun (contoh 1990, 2005). Periksa format CSV.")
    st.stop()

country_col = next(
    (c for c in df.columns if c in ["Country Name", "Country", "Negara", "Entity", "country"]),
    df.columns[0],
)

df_long = df.melt(
    id_vars=[country_col],
    value_vars=years,
    var_name="year",
    value_name="value",
)

# rapikan tipe data
df_long["year"] = pd.to_numeric(df_long["year"], errors="coerce")
df_long["value"] = pd.to_numeric(df_long["value"], errors="coerce")
df_long = (
    df_long.rename(columns={country_col: "country"})
    .dropna(subset=["country", "year", "value"])
)
df_long["year"] = df_long["year"].astype(int)

if df_long.empty:
    st.error("Data kosong setelah dibersihkan — cek format CSV (header tahun & nilai).")
    st.stop()

# -----------------------------
# Peta Dunia Berdasarkan Tahun
# -----------------------------
st.subheader("🌍 World Map View")

years_sorted = sorted(df_long["year"].unique())
year_select = st.slider(
    "Pilih tahun untuk peta",
    int(min(years_sorted)),
    int(max(years_sorted)),
    int(max(years_sorted)),
)

df_map = df_long[df_long["year"] == year_select]

try:
    fig = px.choropleth(
        df_map,
        locations="country",
        locationmode="country names",
        color="value",
        color_continuous_scale="Turbo",
        hover_name="country",
        title=f"{indicator} — {year_select}",
    )
    fig.update_layout(margin={"r": 0, "l": 0, "t": 40, "b": 0})
    st.plotly_chart(fig, use_container_width=True)
except Exception as e:
    st.error("⚠ Peta gagal ditampilkan — cek format nama negara.\n" + str(e))

# -----------------------------
# Grafik Time Series
# -----------------------------
st.subheader("📈 Grafik Time Series (Multi Negara)")

countries = sorted(df_long["country"].dropna().unique().tolist())
if not countries:
    st.error("Daftar negara kosong — cek kolom negara pada CSV.")
    st.stop()

default = "Indonesia" if "Indonesia" in countries else countries[0]
selected = st.multiselect("Pilih negara:", countries, default=[default])

df_ts = df_long[df_long["country"].isin(selected)].sort_values(["country", "year"])

if df_ts.empty:
    st.warning("Tidak ada data untuk negara tersebut.")
else:
    fig_ts = px.line(
        df_ts,
        x="year",
        y="value",
        color="country",
        markers=True,
        labels={"value": indicator, "year": "Tahun", "country": "Negara"},
        title=f"Time Series — {indicator}",
    )
    fig_ts.update_layout(xaxis=dict(dtick=5), margin={"t": 30})
    st.plotly_chart(fig_ts, use_container_width=True)

    st.dataframe(df_ts.reset_index(drop=True), use_container_width=True)

# -----------------------------
# Download CSV
# -----------------------------
st.subheader("📥 Download Dataset")
csv = df_long.to_csv(index=False)
st.download_button(
    "⬇ Download CSV",
    csv,
    file_name=f"page8_{indicator.replace(' ', '_')}.csv",
    mime="text/csv",
)
