# pages/page9.py
import streamlit as st
import pandas as pd
import os
import plotly.express as px

st.set_page_config(layout="wide", page_title="Kesehatan", page_icon="🏥")

st.title("🏥 Kesehatan")
st.write(
    "Halaman ini menampilkan indikator Kesehatan berdasarkan file CSV pada folder `data/`.\n"
    "Script otomatis mendeteksi apakah file berformat *wide* (kolom tahun) atau *long* (country-year-value)."
)

# -----------------------------
# Data folder & mapping file
# -----------------------------
DATA_DIR = "data"
FILES = {
    "Health expenditure (current US$ or % of GDP)": "9.1. HEALTH EXPENDITURE.csv",
    "Maternal mortality (per 100,000 live births)": "9.2. MATERNAL MORTALITY.csv",
    "Infant mortality (per 1,000 live births)": "9.3. INFANT MORTALITY.csv",
    "People using safely managed drinking water services (%)": "9.4. PEOPLE USING SAFELY MANAGED DRINKING WATER SERVICES.csv",
}

# -----------------------------
# Flexible CSV loader
# -----------------------------
@st.cache_data
def load_csv_clean(path: str) -> pd.DataFrame:
    """Try common separators and skip bad lines. Return empty DF if can't read."""
    if not os.path.exists(path):
        return pd.DataFrame()
    for sep in [";", ",", "\t"]:
        try:
            df = pd.read_csv(path, sep=sep, engine="python", on_bad_lines="skip")
            if df.shape[1] > 1:
                return df
        except Exception:
            pass
    try:
        return pd.read_csv(path, engine="python", on_bad_lines="skip")
    except Exception:
        return pd.DataFrame()

# -----------------------------
# Detect available files
# -----------------------------
available = [k for k, v in FILES.items() if os.path.exists(os.path.join(DATA_DIR, v))]
if not available:
    st.error(f"Tidak ditemukan file CSV Page 9 di folder `{DATA_DIR}/`. Letakkan file sesuai nama mapping.")
    st.stop()

indicator = st.selectbox("📌 Pilih indikator Kesehatan:", available)
file_path = os.path.join(DATA_DIR, FILES[indicator])

df = load_csv_clean(file_path)
if df.empty:
    st.error(f"File `{os.path.basename(file_path)}` kosong atau gagal dibaca.")
    st.stop()

st.subheader("📄 Preview data (sample)")
st.dataframe(df.head(12), use_container_width=True)

# -----------------------------
# Helpers: find country col
# -----------------------------
def find_country_col(cols):
    candidates = ["country name", "country", "negara", "entity"]
    for cand in candidates:
        for c in cols:
            if c.strip().lower() == cand:
                return c
    # fallback: first column
    return cols[0]

# -----------------------------
# Detect format: LONG vs WIDE
# -----------------------------
cols_raw = [str(c).strip() for c in df.columns]
cols_lower = [c.lower() for c in cols_raw]

df_long = pd.DataFrame()

if "year" in cols_lower:
    st.info("Format terdeteksi: LONG (country - year - value).")
    # Normalize column names
    rename_map = {}
    for c in df.columns:
        if c.strip().lower() in ["country", "country name", "negara", "entity"]:
            rename_map[c] = "country"
        if c.strip().lower() == "year":
            rename_map[c] = "year"
    df2 = df.rename(columns=rename_map)
    if "country" not in df2.columns or "year" not in df2.columns:
        st.error("Kolom 'country' atau 'year' tidak ditemukan setelah normalisasi. Periksa header CSV.")
        st.stop()
    # find value column(s)
    value_cols = [c for c in df2.columns if c not in ["country", "year"]]
    if not value_cols:
        st.error("Tidak ditemukan kolom nilai pada file long-format.")
        st.stop()
    # if multiple value columns, let user pick
    if len(value_cols) > 1:
        sel_val = st.selectbox("Pilih kolom nilai (value) dari file long-format:", value_cols)
        val_col = sel_val
    else:
        val_col = value_cols[0]
    df_long = df2[["country", "year", val_col]].rename(columns={val_col: "value"}).copy()
    df_long["year"] = pd.to_numeric(df_long["year"], errors="coerce")
    df_long["value"] = pd.to_numeric(df_long["value"], errors="coerce")
    df_long = df_long.dropna(subset=["year", "value"])
else:
    # WIDE format: find year-like columns (4-digit)
    years = [c for c in cols_raw if c.isdigit() and len(c) == 4]
    if not years:
        st.error("Tidak ditemukan kolom tahun (mis. 1990, 2005) dalam header. Jika file long-format, pastikan kolom bernama 'Year'.")
        st.stop()
    st.info("Format terdeteksi: WIDE (kolom tahun di header).")
    country_col = find_country_col(df.columns)
    try:
        df_long = df.melt(
            id_vars=[country_col],
            value_vars=years,
            var_name="year",
            value_name="value"
        ).rename(columns={country_col: "country"})
        df_long["year"] = pd.to_numeric(df_long["year"], errors="coerce")
        df_long["value"] = pd.to_numeric(df_long["value"], errors="coerce")
        df_long = df_long.dropna(subset=["value"])
    except Exception as e:
        st.error("Gagal transformasi wide->long. Periksa struktur CSV.")
        st.exception(e)
        st.stop()

if df_long.empty:
    st.error("Data kosong setelah transformasi. Periksa file.")
    st.stop()

# cleanup
df_long["country"] = df_long["country"].astype(str).str.strip()

# -----------------------------
# Peta options
# -----------------------------
years_sorted = sorted(df_long["year"].unique().astype(int).tolist())
if not years_sorted:
    st.error("Tidak ada tahun valid pada data setelah parsing.")
    st.stop()

st.subheader("🔢 Opsi Peta")
col1, col2 = st.columns([3, 1])
with col2:
    mode = st.radio("Mode warna peta", ("Continuous (nilai)", "Quantile (buckets)"))
    color_scale = st.selectbox("Color scale:", ["Viridis", "Plasma", "Cividis", "Turbo", "Blues"], index=0)
with col1:
    year_select = st.slider("Pilih tahun untuk peta dunia:", int(min(years_sorted)), int(max(years_sorted)), int(max(years_sorted)))

df_map = df_long[df_long["year"] == int(year_select)]

st.subheader(f"🌍 Peta Dunia — {indicator} ({year_select})")
if df_map.empty:
    st.warning("Tidak ada data untuk tahun yang dipilih.")
else:
    try:
        # plotly choropleth
        chosen_scale = color_scale if color_scale in px.colors.named_colorscales() else "Viridis"
        fig = px.choropleth(
            df_map,
            locations="country",
            locationmode="country names",
            color="value",
            hover_name="country",
            color_continuous_scale=chosen_scale,
            labels={"value": indicator},
            title=f"{indicator} — {year_select}"
        )
        fig.update_layout(margin={"r":0,"l":0,"t":30,"b":0}, height=520)
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error("❌ Peta gagal dibuat. Periksa nama negara di CSV (gunakan country names yang dikenali oleh plotly).")
        st.exception(e)

# -----------------------------
# Time series chart
# -----------------------------
st.subheader("📈 Grafik Time Series per Negara")
country_list = sorted(df_long["country"].dropna().unique().tolist())
if not country_list:
    st.info("Tidak ada negara tersedia.")
else:
    default = "Indonesia" if "Indonesia" in country_list else country_list[0]
    selected = st.multiselect("Pilih negara (bisa lebih dari satu):", country_list, default=[default])
    df_ts = df_long[df_long["country"].isin(selected)].sort_values(["country", "year"])
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
        fig_ts.update_layout(xaxis=dict(dtick=5), margin={"l":0,"r":0,"t":30,"b":0})
        st.plotly_chart(fig_ts, use_container_width=True)
        st.dataframe(df_ts.reset_index(drop=True), use_container_width=True)

# -----------------------------
# Summary stats: latest values top/bottom
# -----------------------------
st.subheader("🔎 Statistik Ringkas (nilai terbaru per negara)")
agg = (
    df_long.groupby("country")
    .apply(lambda g: g.loc[g["year"].idxmax(), "value"] if not g.empty else None)
    .reset_index()
)
agg.columns = ["country", "latest_value"]
agg = agg.dropna(subset=["latest_value"]).sort_values("latest_value", ascending=False)

left, right = st.columns(2)
with left:
    st.markdown("**Top 10 (terbesar)**")
    st.table(agg.head(10).style.format({"latest_value": "{:,.2f}"}))
with right:
    st.markdown("**Bottom 10 (terendah)**")
    st.table(agg.tail(10).sort_values("latest_value", ascending=True).style.format({"latest_value": "{:,.2f}"}))

# -----------------------------
# ANALISIS KESEHATAN TERPADU
# -----------------------------
st.subheader("🧠 Analisis Kesehatan Terpadu")


# Asumsi df_health sudah long format:
# kolom: country | year | value | indicator

# pisahkan indikator
df_pivot = df_long.pivot_table(
    index=["country", "year"],
    columns="indicator",
    values="value"
).reset_index()

# pilih tahun terbaru
latest_year = df_pivot["year"].max()
df_latest = df_pivot[df_pivot["year"] == latest_year].dropna()

# normalisasi (min-max)
def minmax(series, inverse=False):
    s = (series - series.min()) / (series.max() - series.min())
    return 1 - s if inverse else s

df_latest["health_exp_n"] = minmax(df_latest["Health Expenditure"])
df_latest["water_n"] = minmax(df_latest["Drinking Water"])
df_latest["infant_n"] = minmax(df_latest["Infant Mortality"], inverse=True)
df_latest["maternal_n"] = minmax(df_latest["Maternal Mortality"], inverse=True)

# skor kesehatan komposit
df_latest["Health_Index"] = (
    df_latest["health_exp_n"] +
    df_latest["water_n"] +
    df_latest["infant_n"] +
    df_latest["maternal_n"]
) / 4

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 🟢 Negara dengan Kinerja Kesehatan Terbaik")
    st.dataframe(
        df_latest.sort_values("Health_Index", ascending=False)
        [["country", "Health_Index"]]
        .head(10),
        use_container_width=True
    )

with col2:
    st.markdown("### 🔴 Negara dengan Krisis Kesehatan")
    st.dataframe(
        df_latest.sort_values("Health_Index")
        [["country", "Health_Index"]]
        .head(10),
        use_container_width=True
    )

st.markdown("""
### A. Gambaran Umum Kesehatan Global

Analisis kesehatan ini mengintegrasikan empat indikator utama, yaitu:
1. **Health Expenditure**
2. **Infant Mortality Rate**
3. **Maternal Mortality Ratio**
4. **Access to Safely Managed Drinking Water**

Keempat indikator tersebut digunakan untuk memberikan gambaran menyeluruh
tentang kapasitas sistem kesehatan, kualitas layanan dasar, dan kondisi kesehatan masyarakat
di berbagai negara.
""")
    
st.markdown("""
### B. Health Expenditure

Berdasarkan statistik terbaru, negara-negara dengan **pengeluaran kesehatan tertinggi**
seperti *United States* dan beberapa negara berpendapatan tinggi
menunjukkan kapasitas fiskal yang besar dalam membiayai sektor kesehatan.

Namun, tingginya belanja kesehatan **tidak selalu berbanding lurus**
dengan hasil kesehatan yang optimal, karena efektivitas belanja,
ketimpangan akses, dan efisiensi sistem pelayanan juga berperan penting.
""")

st.markdown("""
### C. Infant Mortality

Negara-negara dengan **tingkat kematian bayi tertinggi**
didominasi oleh negara berpendapatan rendah dan wilayah konflik,
seperti *South Sudan*, *Somalia*, dan *Nigeria*.

Tingginya angka kematian bayi mencerminkan
keterbatasan akses layanan kesehatan dasar,
kekurangan tenaga medis,
serta kondisi gizi dan sanitasi yang buruk.
""")

st.markdown("""
### D. Maternal Mortality

Pola yang serupa juga terlihat pada indikator kematian ibu.
Negara-negara Afrika Sub-Sahara mendominasi kelompok dengan
rasio kematian ibu tertinggi.

Hal ini menunjukkan lemahnya sistem kesehatan maternal,
terbatasnya fasilitas persalinan yang aman,
serta rendahnya cakupan layanan kesehatan reproduksi.
""")

st.markdown("""
### E. Akses Air Minum Layak

Sebaliknya, negara-negara maju seperti *Singapore*, *New Zealand*,
dan beberapa negara Eropa menunjukkan
akses air minum layak yang hampir universal.

Akses air bersih berperan penting dalam menurunkan risiko penyakit menular,
kematian bayi, serta meningkatkan kualitas kesehatan masyarakat secara keseluruhan.
""")

st.markdown("""
### F. Kesimpulan Analisis Kesehatan Terpadu

Hasil analisis menunjukkan bahwa kualitas kesehatan suatu negara
merupakan hasil interaksi antara **kapasitas fiskal**, **kualitas layanan kesehatan**,
serta **ketersediaan infrastruktur dasar** seperti air bersih.

Negara dengan konflik berkepanjangan dan kemiskinan struktural
cenderung mengalami kegagalan lintas indikator kesehatan,
sementara negara dengan tata kelola dan infrastruktur yang baik
mampu mencapai hasil kesehatan yang lebih optimal.
""")


# -----------------------------
# Download
# -----------------------------
st.subheader("📥 Ekspor Data (long format)")
csv = df_long.to_csv(index=False)
safe = indicator.replace(" ", "_").replace("/", "_").replace("(", "").replace(")", "")
st.download_button("⬇ Download CSV (long)", csv, file_name=f"page9_{safe}_{year_select}.csv", mime="text/csv")

st.caption("Tip: jika banyak negara kosong di peta, periksa nama negara di CSV. Jika mau, kirim file ISO3 / mapping, aku bantu mapping otomatis.")
