import streamlit as st
import pandas as pd
import os
import plotly.express as px

st.set_page_config(layout="wide", page_title="Energi & Lingkungan", page_icon="🌱")

st.title("🌱 Energi & Lingkungan — Peta Dunia + Time Series")
st.write(
    "Halaman ini menampilkan indikator Energi & Lingkungan berdasarkan file CSV yang berada "
    "pada folder `data/`. Script ini otomatis mendeteksi format file (wide atau long) sehingga "
    "file CO2 dengan kolom Year akan terbaca."
)

# -----------------------------
# Folder data & daftar file CSV
# -----------------------------
DATA_DIR = "data"

FILES = {
    "CO2 emissions (metric tons per capita)": "10.1. CO EMISSIONS.csv",
    "Electricity access (% of population)": "10.4. ELECTRICITY ACCESS.csv",
    "Renewable energy consumption (% of total)": "10.2. RENEWABLE ENERGY CONSUMPTION.csv",
    "Forest area (sq. km or % depending on file)": "10.3. FOREST AREA.csv",
}

# -----------------------------
# Loader CSV fleksibel
# -----------------------------
@st.cache_data
def load_csv_clean(path: str) -> pd.DataFrame:
    """Coba beberapa separator umum dan lewati baris rusak. Kembalikan DataFrame kosong jika file tidak ada."""
    if not os.path.exists(path):
        return pd.DataFrame()
    for sep in [";", ",", "\t"]:
        try:
            df = pd.read_csv(path, sep=sep, engine="python", on_bad_lines="skip")
            # Jika parsing menghasilkan >1 kolom, anggap berhasil
            if df.shape[1] > 1:
                return df
        except Exception:
            pass
    # fallback: biarkan pandas coba tebak
    try:
        return pd.read_csv(path, engine="python", on_bad_lines="skip")
    except Exception:
        return pd.DataFrame()

# -----------------------------
# Deteksi file yang tersedia
# -----------------------------
available_files = []
for label, fname in FILES.items():
    if os.path.exists(os.path.join(DATA_DIR, fname)):
        available_files.append(label)

if not available_files:
    st.error(f"Tidak ada file CSV Page 10 ditemukan dalam folder `{DATA_DIR}/`.\n\nPastikan file ditempatkan di folder `data/` dan nama file mengikuti mapping pada kode.")
    st.stop()

# -----------------------------
# Pilih indikator + Load data
# -----------------------------
indicator = st.selectbox("📌 Pilih indikator Energi & Lingkungan:", available_files)
file_path = os.path.join(DATA_DIR, FILES[indicator])

df = load_csv_clean(file_path)
if df.empty:
    st.error(f"File `{os.path.basename(file_path)}` kosong atau gagal dibaca. Periksa file dan struktur CSV.")
    st.stop()

st.subheader("📄 Preview data (sample)")
st.dataframe(df.head(15), use_container_width=True)

# -----------------------------
# IDENTIFIKASI FORMAT: LONG vs WIDE
# -----------------------------
cols_raw = [str(c).strip() for c in df.columns]
cols_lower = [c.lower() for c in cols_raw]

# fungsi bantu: cari nama kolom country candidate
def find_country_col(df_cols):
    candidates = ["country name", "country", "negara", "entity"]
    for cand in candidates:
        for c in df_cols:
            if c.lower() == cand:
                return c
    # fallback: kolom pertama
    return df_cols[0]

df_long = pd.DataFrame()  # inisialisasi

# jika ada kolom 'Year' atau 'year' -> long format (country, year, value)
if "year" in cols_lower:
    st.info("Format data terdeteksi: **LONG format** (kolom Year present).")
    # normalisasi nama country dan year
    rename_map = {}
    for c in df.columns:
        if c.lower() in ["country", "country name", "negara", "entity"]:
            rename_map[c] = "country"
        if c.lower() == "year":
            rename_map[c] = "year"
    df2 = df.rename(columns=rename_map)
    if "country" not in df2.columns or "year" not in df2.columns:
        st.error("Kolom country atau year tidak ditemukan setelah normalisasi. Periksa header CSV.")
        st.stop()
    # cari kolom nilai (semua kolom selain country/year) — idealnya hanya 1
    value_cols = [c for c in df2.columns if c not in ["country", "year"]]
    if len(value_cols) == 0:
        st.error("Tidak ditemukan kolom nilai pada file long-format.")
        st.stop()
    # jika lebih dari satu kolom value, pilih kolom terakhir yang mungkin berisi nilai
    value_col = value_cols[0] if len(value_cols) == 1 else value_cols[-1]
    df_long = df2[["country", "year", value_col]].copy()
    df_long = df_long.rename(columns={value_col: "value"})
    # numeric
    df_long["year"] = pd.to_numeric(df_long["year"], errors="coerce")
    df_long["value"] = pd.to_numeric(df_long["value"], errors="coerce")
    df_long = df_long.dropna(subset=["year", "value"])
else:
    # WIDE format: cari kolom tahun di header (1990, 2000, ...)
    years = [c for c in cols_raw if c.isdigit() and len(c) == 4]
    if not years:
        st.error("Tidak ditemukan kolom tahun (misal 1990, 2005, dst.) di file ini. Periksa header CSV.")
        st.stop()
    st.info("Format data terdeteksi: **WIDE format** (kolom tahun di header).")
    country_col = find_country_col(df.columns)
    try:
        df_long = df.melt(
            id_vars=[country_col],
            value_vars=years,
            var_name="year",
            value_name="value"
        )
        df_long = df_long.rename(columns={country_col: "country"})
        df_long["year"] = pd.to_numeric(df_long["year"], errors="coerce")
        df_long["value"] = pd.to_numeric(df_long["value"], errors="coerce")
        df_long = df_long.dropna(subset=["value"])
    except Exception as e:
        st.error("Gagal transformasi dari wide ke long. Periksa struktur CSV.")
        st.exception(e)
        st.stop()

# cek hasil transformasi
if df_long.empty:
    st.error("Data kosong setelah transformasi. Pastikan file berisi nilai numerik dan kolom tahun valid.")
    st.stop()

# normalisasi nama negara (strip)
df_long["country"] = df_long["country"].astype(str).str.strip()

# -----------------------------
# Pilih tahun untuk peta dunia
# -----------------------------
years_sorted = sorted(df_long["year"].unique().astype(int).tolist())
if not years_sorted:
    st.error("Tidak ada tahun valid pada data setelah parsing.")
    st.stop()

st.subheader("🔢 Opsi Peta")
colp1, colp2 = st.columns([3, 1])
with colp2:
    mode = st.radio("Mode warna peta", ("Continuous (nilai)", "Quantile (buckets)"))
    # opsi skala warna continuous
    color_scale = st.selectbox("Color scale (continuous):", ["Viridis", "Plasma", "Cividis", "Turbo", "Blues"], index=0)

with colp1:
    year_select = st.slider(
        "Pilih tahun untuk peta dunia:",
        int(min(years_sorted)),
        int(max(years_sorted)),
        int(max(years_sorted))
    )

df_map = df_long[df_long["year"] == int(year_select)]

st.subheader(f"🌍 Peta Dunia — {indicator} ({year_select})")
if df_map.empty:
    st.warning("Tidak ada data untuk tahun yang dipilih.")
else:
    try:
        # gunakan choropleth dengan country names
        fig = px.choropleth(
            df_map,
            locations="country",
            locationmode="country names",
            color="value",
            hover_name="country",
            color_continuous_scale=color_scale.lower() if color_scale.lower() in px.colors.named_colorscales() else "Viridis",
            labels={"value": indicator},
            title=f"{indicator} — {year_select}"
        )
        # jika quantile, ubah colorbar/breaks — menggunakan choropleth langsung tidak support buckets mudah,
        # tetapi user sudah dapat memilih color scale; advanced bucket mapping bisa ditambahkan jika mau.
        fig.update_layout(margin={"r":0,"l":0,"t":30,"b":0}, height=520)
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error("❌ Peta gagal dibuat. Periksa kesesuaian nama negara (gunakan country names yang diakui oleh plotly).")
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
# Statistik ringkas & top/bottom
# -----------------------------
st.subheader("🔎 Statistik Ringkas")

agg_latest = df_long.groupby("country").apply(lambda g: g[g["year"] == g["year"].max()]["value"].mean() if not g.empty else None).reset_index()
agg_latest.columns = ["country", "latest_value"]
agg_latest = agg_latest.dropna(subset=["latest_value"]).sort_values("latest_value", ascending=False)

col_top, col_bot = st.columns(2)
with col_top:
    st.markdown("**Top 10 (terbesar)**")
    st.table(agg_latest.head(10).style.format({"latest_value": "{:,.2f}"}))
with col_bot:
    st.markdown("**Bottom 10 (terendah)**")
    st.table(agg_latest.tail(10).sort_values("latest_value", ascending=True).style.format({"latest_value": "{:,.2f}"}))


# =============================
# TEMUAN UTAMA / ANALISIS DATA
# =============================

st.subheader("🔍 Temuan Utama & Interpretasi Data")

st.markdown("""
### 1️⃣ Emisi CO₂ Tidak Selalu Mencerminkan Tingkat Industrialisasi

Berdasarkan indikator **CO₂ emissions**, beberapa negara yang muncul pada kelompok nilai tertinggi 
tidak seluruhnya merupakan negara dengan tingkat industrialisasi yang tinggi atau memiliki kegiatan industri yang maju. 
Hal ini menunjukkan bahwa **tingginya emisi CO₂ tidak dapat langsung diinterpretasikan sebagai tingkat industrialisasi yang tinggi**.

Pada negara-negara berkembang atau wilayah konflik, emisi dapat meningkat akibat:
- penggunaan energi fosil yang tidak efisien,
- ketergantungan pada pembangkit listrik berbasis diesel,
- keterbatasan teknologi ramah lingkungan,
- serta lemahnya infrastruktur energi.

Dengan demikian, emisi CO₂ yang tinggi pada kelompok negara ini lebih mencerminkan **inefisiensi sistem energi**, 
bukan kekuatan dari industrialisasinya.
""")

st.markdown("""
### 2️⃣ Karakteristik Negara Industri Maju

Negara-negara industri seperti **Jepang, Jerman, dan Belgia** menunjukkan pola yang berbeda, yaitu:
- emisi CO₂ relatif tinggi namun **lebih stabil secara time series**,
- tingkat **akses listrik mendekati 100%**,
- serta peningkatan penggunaan **energi terbarukan**.

Pola ini mencerminkan bahwa negara industri cenderung telah memasuki fase 
**pengelolaan emisi dan transisi energi**, bukan sekadar ekspansi produksi.
""")

st.markdown("""
### 3️⃣ Akses Listrik sebagai Indikator Fundamental Pembangunan Suatu Negara

Indikator **Electricity Access** menunjukkan kesenjangan yang jelas antar negara.
Negara dengan akses listrik rendah umumnya memiliki:
- aktivitas ekonomi terbatas,
- tingkat industrialisasi rendah,
- serta emisi CO₂ yang rendah bukan karena keberlanjutan, 
  melainkan keterbatasan pembangunan.

Sebaliknya, akses listrik yang tinggi merupakan prasyarat utama bagi pertumbuhan industri 
dan tolok ukur dalam pembangunan ekonomi dan kesejahteraan suatu negara.
""")

st.markdown("""
### 4️⃣ Energi Terbarukan dan Struktur Energi Negara Berkembang

Beberapa negara berkembang menunjukkan proporsi **energi terbarukan yang relatif tinggi**.
Namun, hal ini sering kali disebabkan oleh:
- ketergantungan pada biomassa dan hidro tradisional,
- bukan karena adopsi teknologi energi hijau yang maju.

Oleh karena itu, tingginya pangsa energi terbarukan pada negara tertentu 
perlu diinterpretasikan dengan hati-hati dan tidak selalu mencerminkan keberhasilan transisi energi.
""")

st.markdown("""
### 5️⃣ Forest Area dan Trade-off Pembangunan

Indikator **Forest Area** menunjukkan adanya trade-off antara:
- ekspansi ekonomi,
- pembangunan energi,
- dan keberlanjutan lingkungan.

Negara dengan emisi dan konsumsi energi tinggi cenderung mengalami tekanan terhadap luas hutan, 
sementara negara dengan hutan luas belum tentu memiliki emisi rendah jika aktivitas ekstraktif meningkat.
""")

# =============================
# TAMBAHAN: SECOND NDC INDONESIA
# =============================

st.markdown("""
### 6️⃣ Second NDC Indonesia (2025) sebagai Lensa Interpretasi Indikator

Second Nationally Determined Contribution (Second NDC) Indonesia menempatkan pembacaan data emisi dan energi
dalam kerangka target nasional yang lebih eksplisit. Dokumen ini menggunakan **reference year 2019**, mencakup
lima sektor **Energy, IPPU, Waste, Agriculture, dan FOLU**, serta memakai metrik **Global Warming Potential (GWP)
100 tahun** untuk konsistensi perhitungan emisi setara CO₂. Dalam proyeksi 2025–2035, dokumen menekankan bahwa
**puncak emisi nasional ditargetkan pada 2030**, lalu lintasan emisi perlu mengarah ke target **Net Zero Emissions 2060
atau lebih cepat**.

Implikasinya terhadap pembacaan indikator di halaman ini:

1. **CO₂ emissions** dan **Renewable energy consumption** dapat dibaca sebagai sinyal arah transisi energi.
   Tren penurunan emisi per kapita bersamaan dengan kenaikan pangsa energi terbarukan lebih konsisten
   dengan upaya menjaga peaking 2030 dan menguatkan dekarbonisasi sektor energi.

2. **Electricity access** memberi konteks pembangunan yang setara. Kenaikan akses listrik penting untuk
   pertumbuhan dan kesejahteraan, namun konsekuensi emisinya bergantung pada bauran energi yang dipakai.
   Dalam kerangka Second NDC, perluasan akses idealnya diiringi perbaikan efisiensi dan peningkatan porsi energi bersih.

3. **Forest area** relevan untuk membaca dinamika FOLU. Stabilitas atau peningkatan tutupan hutan mendukung
   strategi pengendalian deforestasi, restorasi, dan penguatan penyerapan karbon, yang menjadi bagian penting
   dalam target lintas sektor.
""")

st.success("""
🔎 **Kesimpulan Umum**  
Analisis lintas indikator menunjukkan bahwa pembangunan berkelanjutan 
tidak dapat diukur hanya dari satu indikator lingkungan. 
Pendekatan multidimensi diperlukan untuk memahami hubungan antara energi, lingkungan, 
dan tingkat pembangunan ekonomi.
""")


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

# -----------------------------
# Sources
# -----------------------------
st.subheader("📚 Sources")
st.markdown("""
1. World Bank Open Data, World Development Indicators (WDI). Dataset indikator lingkungan dan energi yang dipakai pada folder `data/` mengikuti struktur WDI-style (country dan tahun).
2. Republic of Indonesia. *Second Nationally Determined Contribution (Second NDC)* (2025). Dokumen kerangka komitmen mitigasi Indonesia, termasuk reference year 2019, sektor cakupan, metrik GWP, dan penekanan peaking emisi 2030.
""")

st.write("")
st.caption("Tip: Jika peta menunjukkan banyak negara 'kosong', periksa apakah nama negara di CSV sesuai 'country names' (contoh: 'United States' vs 'United States of America'). Jika perlu, tambahkan kolom ISO3 di file CSV dan beritahu aku, aku bantu sesuaikan mapping.")
