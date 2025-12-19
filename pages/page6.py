# pages/page6.py
import streamlit as st
import pandas as pd
import os
import plotly.express as px

st.set_page_config(layout="wide", page_title="Kemiskinan & Ketimpangan", page_icon="📉")

st.title("📉 Kemiskinan & Ketimpangan")
st.write(
    "Halaman ini menampilkan indikator kemiskinan dan ketimpangan berbasis data World Bank "
    "yang tersimpan dalam file CSV lokal di folder `data/`. "
    "Analisis bersifat deskriptif untuk membaca posisi relatif, distribusi global, dan dinamika waktu."
)

# ======================================================
# DEFINISI INDIKATOR
# ======================================================
with st.expander("📌 Definisi indikator (ringkas)", expanded=False):
    st.markdown(
        """
**Poverty headcount ratio at $4.20 a day** mengukur persentase penduduk yang hidup di bawah garis kemiskinan 
internasional (ambang $4,20/hari PPP). Nilai lebih tinggi berarti proporsi penduduk miskin lebih besar.

**Gini index** mengukur ketimpangan distribusi pendapatan (0 = merata sempurna, 100 = timpang sempurna). 
Nilai lebih tinggi berarti ketimpangan lebih besar.

**Income share held by lowest 20%** mengukur persentase pendapatan nasional yang dinikmati oleh kelompok 20% terbawah. 
Nilai lebih tinggi berarti distribusi pendapatan lebih berpihak pada kelompok bawah.
"""
    )

# ======================================================
# FILE
# ======================================================
DATA_DIR = "data"
FILES = {
    "Poverty headcount ratio at $4.20 a day": "6.1. POVERTY HEADCOUNT RATIO AT $4.20 A DAY.csv",
    "Gini index": "6.2. GINI INDEX.csv",
    "Income share held by lowest 20%": "6.3. INCOME SHARE HELD BY LOWER 20%.csv",
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
    st.error("File Page 6 tidak ditemukan di folder `data/`.")
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

    if indicator == "Poverty headcount ratio at $4.20 a day":
        st.markdown(
            """
Pada indikator kemiskinan, nilai yang lebih tinggi berarti proporsi penduduk miskin lebih besar pada tahun terpilih.
Negara di atas Q3 dapat dikategorikan memiliki tingkat kemiskinan relatif tinggi (pada standar garis $4,20 PPP).

Nilai rendah tidak otomatis berarti tanpa kemiskinan, karena indikator ini bergantung pada metode survei, cakupan data,
dan kesesuaian PPP. Namun secara umum, nilai rendah konsisten dengan kemampuan daya beli dan perlindungan sosial yang lebih baik.
"""
        )
    elif indicator == "Gini index":
        st.markdown(
            """
Pada indeks Gini, nilai yang lebih tinggi berarti ketimpangan lebih besar.
Negara di atas Q3 dapat dikategorikan memiliki ketimpangan relatif tinggi pada tahun itu.

Ketimpangan dipengaruhi struktur pasar kerja, distribusi aset, pajak-transfer, dan akses layanan dasar.
Karena itu, interpretasi yang rapi biasanya membandingkan Gini dengan kemiskinan dan porsi pendapatan kelompok bawah.
"""
        )
    else:
        st.markdown(
            """
Pada income share 20% terbawah, nilai yang lebih tinggi berarti kelompok bawah menikmati porsi pendapatan yang lebih besar,
yang mengarah pada distribusi yang lebih inklusif.

Jika nilainya rendah, ini menandakan bagian pendapatan kelompok bawah kecil, yang sering selaras dengan ketimpangan lebih tinggi.
Namun pembacaan yang kuat juga melihat mekanisme pajak-transfer, upah minimum, dan struktur pekerjaan.
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
Grafik ini menunjukkan dinamika kemiskinan/ketimpangan dari waktu ke waktu. 
Penurunan kemiskinan secara konsisten biasanya selaras dengan pertumbuhan inklusif, perluasan kesempatan kerja, 
dan efektivitas perlindungan sosial. Fluktuasi pada Gini atau income share dapat mencerminkan perubahan struktur pekerjaan,
shock harga, krisis, atau perubahan kebijakan pajak-transfer.
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
    file_name=f"page6_poverty_{indicator.replace(' ', '_')}.csv",
    mime="text/csv",
)
