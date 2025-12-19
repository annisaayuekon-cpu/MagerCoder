# pages/page5.py
import streamlit as st
import pandas as pd
import os
import plotly.express as px

st.set_page_config(layout="wide", page_title="Investasi & Pembentukan Modal", page_icon="💰")

st.title("💰 Investasi & Pembentukan Modal")
st.write(
    "Halaman ini menampilkan indikator investasi berbasis data World Bank "
    "yang tersimpan dalam file CSV lokal di folder `data/`. "
    "Analisis bersifat deskriptif untuk membaca posisi relatif, distribusi global, dan dinamika waktu."
)

# ======================================================
# DEFINISI INDIKATOR
# ======================================================
with st.expander("📌 Definisi indikator (ringkas)", expanded=False):
    st.markdown(
        """
**Foreign Direct Investment (FDI)** menggambarkan arus investasi langsung lintas negara, 
biasanya mencerminkan minat investor asing terhadap prospek ekonomi, stabilitas, dan iklim usaha.

**Gross Capital Formation** menggambarkan pembentukan modal tetap bruto, termasuk investasi pada bangunan, mesin, 
dan infrastruktur. Indikator ini sering dipakai untuk membaca kapasitas pertumbuhan jangka menengah dan panjang.
"""
    )

# ======================================================
# FILE
# ======================================================
DATA_DIR = "data"
FILES = {
    "Foreign direct investment (FDI)": "5.1 Foreign Direct Investment (FDI).csv",
    "Gross capital formation": "5.2 Gross capital formation.csv",
}

@st.cache_data
def load_csv_tolerant(path: str) -> pd.DataFrame:
    for sep in [";", ",", "\t"]:
        try:
            df = pd.read_csv(path, sep=sep, engine="python", on_bad_lines="skip")
            if df.shape[1] > 1:
                return df
        except Exception:
            continue
    return pd.read_csv(path, engine="python", on_bad_lines="skip")

# ======================================================
# CEK FILE
# ======================================================
available = []
for k, v in FILES.items():
    if os.path.exists(os.path.join(DATA_DIR, v)):
        available.append(k)

if not available:
    st.error("File Page 5 tidak ditemukan di folder `data/`.")
    st.stop()

indicator = st.selectbox("📌 Pilih indikator:", available)
file_path = os.path.join(DATA_DIR, FILES[indicator])

df = load_csv_tolerant(file_path)

st.subheader("📄 Preview Data Mentah")
st.dataframe(df.head(15), use_container_width=True)

# ======================================================
# DETEKSI KOLUMN
# ======================================================
year_cols = [c for c in df.columns if str(c).isdigit() and len(str(c)) == 4]
if not year_cols:
    st.error("Tidak ditemukan kolom tahun (format 4 digit).")
    st.stop()

country_col = next(
    (c for c in ["Country Name", "Country", "country", "Negara", "Entity"] if c in df.columns),
    df.columns[0],
)

# ======================================================
# LONG FORMAT
# ======================================================
df_long = df.melt(
    id_vars=[country_col],
    value_vars=year_cols,
    var_name="year",
    value_name="value",
)
df_long = df_long.rename(columns={country_col: "country"})
df_long["year"] = pd.to_numeric(df_long["year"], errors="coerce")
df_long["value"] = pd.to_numeric(df_long["value"], errors="coerce")
df_long = df_long.dropna(subset=["country", "year", "value"])
df_long["year"] = df_long["year"].astype(int)

# ======================================================
# STATISTIK RINGKAS (LATEST)
# ======================================================
st.subheader("🔎 Statistik Ringkas (nilai terbaru per negara)")

df_latest = (
    df_long.sort_values(["country", "year"])
    .groupby("country", as_index=False)
    .tail(1)
    .rename(columns={"year": "latest_year", "value": "latest_value"})
)

top10 = df_latest.sort_values("latest_value", ascending=False).head(10)
bottom10 = df_latest.sort_values("latest_value", ascending=True).head(10)

c1, c2 = st.columns(2)
with c1:
    st.markdown("**Top 10 (terbesar)**")
    st.dataframe(top10[["country", "latest_value"]], use_container_width=True)
with c2:
    st.markdown("**Bottom 10 (terendah)**")
    st.dataframe(bottom10[["country", "latest_value"]], use_container_width=True)

# ======================================================
# PETA DUNIA
# ======================================================
st.subheader("🌍 Peta Dunia")

years = sorted(df_long["year"].unique())
year_min, year_max = int(min(years)), int(max(years))
selected_year = st.slider("Pilih tahun", year_min, year_max, year_max)

df_map = df_long[df_long["year"] == selected_year]

if df_map.empty:
    st.warning("Tidak ada data pada tahun yang dipilih.")
else:
    fig = px.choropleth(
        df_map,
        locations="country",
        locationmode="country names",
        color="value",
        hover_name="country",
        color_continuous_scale="Viridis",
        title=f"{indicator} ({selected_year})",
        labels={"value": indicator},
    )
    fig.update_layout(margin={"l": 0, "r": 0, "t": 40, "b": 0})
    st.plotly_chart(fig, use_container_width=True)

# ======================================================
# INTERPRETASI PETA
# ======================================================
st.subheader("🧠 Interpretasi peta (tahun terpilih)")

vals = df_map["value"].dropna()
if len(vals) >= 5:
    q25, q50, q75 = vals.quantile([0.25, 0.50, 0.75]).tolist()
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Jumlah negara", f"{len(vals):,}")
    m2.metric("Kuartil 1 (Q1)", f"{q25:,.2f}")
    m3.metric("Median (Q2)", f"{q50:,.2f}")
    m4.metric("Kuartil 3 (Q3)", f"{q75:,.2f}")

    if indicator == "Foreign direct investment (FDI)":
        st.markdown(
            """
Pada indikator FDI, posisi relatif yang tinggi mencerminkan arus investasi asing yang besar pada tahun terpilih. 
Perbedaan antar negara sering dipengaruhi oleh ukuran pasar, stabilitas makro, dan iklim kebijakan investasi.

Nilai yang rendah tidak selalu menunjukkan kinerja buruk, karena sebagian negara lebih bergantung pada investasi domestik 
atau memiliki rezim pembatasan tertentu terhadap investasi asing.
"""
        )
    else:
        st.markdown(
            """
Pada pembentukan modal, posisi tinggi biasanya mencerminkan tingkat investasi fisik yang besar, 
yang berperan penting dalam kapasitas produksi jangka menengah dan panjang.

Perbedaan lintas negara sering mencerminkan tahapan pembangunan, struktur ekonomi, dan siklus investasi, 
sehingga pembacaan yang paling informatif adalah membandingkan posisi relatif terhadap median dan kuartil.
"""
        )

st.caption("Catatan: Analisis ini bersifat deskriptif dan tidak dimaksudkan sebagai inferensi kausal.")

# ======================================================
# TIME SERIES PER NEGARA
# ======================================================
st.subheader("📈 Time Series per Negara")

country_list = sorted(df_long["country"].unique())
default_country = "Indonesia" if "Indonesia" in country_list else country_list[0]
selected_country = st.selectbox("Pilih negara:", country_list, index=country_list.index(default_country))

df_cty = df_long[df_long["country"] == selected_country].sort_values("year")

fig_ts = px.line(
    df_cty,
    x="year",
    y="value",
    markers=True,
    title=f"{indicator} — {selected_country}",
    labels={"year": "Tahun", "value": indicator},
)
st.plotly_chart(fig_ts, use_container_width=True)

st.markdown(
    """
Grafik ini menunjukkan dinamika investasi dari waktu ke waktu. 
Kenaikan yang konsisten sering dikaitkan dengan ekspansi kapasitas produksi, 
sementara fluktuasi tajam biasanya mencerminkan siklus bisnis, shock eksternal, atau perubahan kebijakan.
"""
)

# ======================================================
# DOWNLOAD
# ======================================================
st.subheader("📘 Data Lengkap (long format)")

csv_download = df_long.to_csv(index=False)
st.download_button(
    "⬇ Download data (CSV)",
    csv_download,
    file_name=f"page5_investment_{indicator.replace(' ', '_')}.csv",
    mime="text/csv",
)
