import streamlit as st
import pandas as pd
import os
import plotly.express as px

st.set_page_config(layout="wide", page_title="Energi & Lingkungan", page_icon="🌱")

st.title("🌱 Energi & Lingkungan — Peta Dunia + Time Series")
st.write(
    "Halaman ini menampilkan indikator Energi & Lingkungan berdasarkan file CSV yang berada "
    "pada folder `data/`. Pastikan nama file mengikuti contoh di bawah agar otomatis terdeteksi."
)

# -----------------------------
# Folder data & daftar file CSV (terbaru: termasuk CO2)
# -----------------------------
DATA_DIR = "data"

FILES = {
    "CO2 emissions (metric tons per capita)": "10.1. CO EMISSIONS.csv",
    "Electricity access ( % of population )": "10.4. ELECTRICITY ACCESS.csv",
    "Renewable energy consumption (% of total)": "10.2. RENEWABLE ENERGY CONSUMPTION.csv",
    "Forest area (sq. km or % depending on file)": "10.3. FOREST AREA.csv",
}

# -----------------------------
# Loader CSV fleksibel
# -----------------------------
@st.cache_data
def load_csv_clean(path: str) -> pd.DataFrame:
    """Coba beberapa separator umum dan lewati baris rusak."""
    if not os.path.exists(path):
        return pd.DataFrame()
    for sep in [";", ",", "\t"]:
        try:
            df = pd.read_csv(path, sep=sep, engine="python", on_bad_lines="skip")
            if df.shape[1] > 1:
                return df
        except Exception:
            pass
    return pd.read_csv(path, engine="python", on_bad_lines="skip")

# -----------------------------
# Deteksi file yang tersedia
# -----------------------------
available_files = []
for label, fname in FILES.items():
    if os.path.exists(os.path.join(DATA_DIR, fname)):
        available_files.append(label)

if not available_files:
    st.error(f"Tidak ada file CSV Page 10 ditemukan dalam folder `{DATA_DIR}/`. Silakan masukkan file CSV yang sesuai.")
    st.stop()

# -----------------------------
# Pilih indikator + Load data
# -----------------------------
indicator = st.selectbox("📌 Pilih indikator Energi & Lingkungan:", available_files)
file_path = os.path.join(DATA_DIR, FILES[indicator])

try:
    df = load_csv_clean(file_path)
except Exception as e:
    st.error(f"❌ Gagal membaca file `{os.path.basename(file_path)}`. Error: {e}")
    st.stop()

st.subheader("📄 Preview data (sample)")
st.dataframe(df.head(15), use_container_width=True)

# -----------------------------
# Identifikasi kolom Tahun dan Negara
# -----------------------------
cols = [str(c) for c in df.columns]
years = [c for c in cols if c.isdigit() and len(c) == 4]

if not years:
    st.error("Tidak ditemukan kolom tahun (misal 1990, 2005, dst.) di file ini. Periksa header CSV.")
    st.stop()

possible_country_cols = ["Country Name", "Country", "Negara", "Entity", "country", df.columns[0]]
country_col = next((c for c in df.columns if c in possible_country_cols), df.columns[0])

# -----------------------------
# Konversi ke long format
# -----------------------------
df_long = df.melt(id_vars=[country_col], value_vars=years, var_name="year", value_name="value")
df_long["year"] = pd.to_numeric(df_long["year"], errors="coerce")
df_long = df_long.rename(columns={country_col: "country"})
df_long = df_long.dropna(subset=["value"])
df_long["value"] = pd.to_numeric(df_long["value"], errors="coerce")
df_long = df_long.dropna(subset=["value"])

if df_long.empty:
    st.error("Data kosong setelah transformasi long — kemungkinan format kolom tidak sesuai.")
    st.stop()

# -----------------------------
# Pilih tahun untuk peta dunia
# -----------------------------
years_sorted = sorted(df_long["year"].unique().astype(int).tolist())
if not years_sorted:
    st.error("Tidak ada tahun valid pada data.")
    st.stop()

year_select = st.slider(
    "Pilih tahun untuk peta dunia:",
    int(min(years_sorted)),
    int(max(years_sorted)),
    int(max(years_sorted))
)

df_map = df_long[df_long["year"] == int(year_select)]

st.subheader(f"🌍 Peta Dunia — {indicator} ({year_select})")

if df_map.empty:
    st.warning("Tidak ada data untuk tahun ini.")
else:
    try:
        fig = px.choropleth(
            df_map,
            locations="country",
            locationmode="country names",
            color="value",
            hover_name="country",
            color_continuous_scale="Viridis",
            labels={"value": indicator},
            title=f"{indicator} — {year_select}"
        )
        fig.update_layout(margin={"r":0,"l":0,"t":30,"b":0})
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error("❌ Peta gagal dibuat. Periksa kesesuaian nama negara pada CSV (harus menggunakan country names yang dikenali).")
        st.exception(e)

# -----------------------------
# Grafik Time Series
# -----------------------------
st.subheader("📈 Grafik Time Series per Negara")

country_list = sorted(df_long["country"].dropna().unique().tolist())
if not country_list:
    st.info("Tidak ada daftar negara tersedia.")
else:
    default_country = "Indonesia" if "Indonesia" in country_list else country_list[0]
    selected_countries = st.multiselect(
        "Pilih negara (bisa lebih dari satu):",
        country_list,
        default=[default_country]
    )

    df_ts = df_long[df_long["country"].isin(selected_countries)].sort_values(["country", "year"])
    if df_ts.empty:
        st.info("Tidak ada data time series untuk negara yang dipilih.")
    else:
        fig_ts = px.line(
            df_ts,
            x="year",
            y="value",
            color="country",
            markers=True,
            labels={"year": "Tahun", "value": indicator, "country": "Negara"},
            title=f"Time series — {indicator}"
        )
        fig_ts.update_layout(xaxis=dict(dtick=5), margin={"l": 0, "r": 0, "t": 30, "b": 0})
        st.plotly_chart(fig_ts, use_container_width=True)

        st.dataframe(df_ts.reset_index(drop=True), use_container_width=True)

# -----------------------------
# Download Full Data (long)
# -----------------------------
st.subheader("📥 Ekspor Data (long format)")
csv = df_long.to_csv(index=False)
safe_name = indicator.replace(" ", "_").replace("/", "_").replace("(", "").replace(")", "")
st.download_button(
    label="⬇ Download CSV (long)",
    data=csv,
    file_name=f"page10_{safe_name}_{year_select}.csv",
    mime="text/csv"
)
