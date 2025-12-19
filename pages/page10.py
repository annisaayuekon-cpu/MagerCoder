# pages/page10.py
import os
import base64
import urllib.request
from urllib.error import URLError, HTTPError

import pandas as pd
import streamlit as st
import plotly.express as px
import streamlit.components.v1 as components

st.set_page_config(layout="wide", page_title="Energi & Lingkungan", page_icon="🌱")

# =========================
# Config
# =========================
DATA_DIR = "data"

SNDC_URL = "https://unfccc.int/sites/default/files/2025-10/Indonesia_Second%20NDC_2025.10.24.pdf"

FILES = {
    "CO emissions (metric tons per capita)": [
        "10.1. CO EMISSIONS.csv",
        "10.1 CO EMISSIONS.csv",
        "10.1. CO emissions.csv",
        "10.1 CO emissions.csv",
        "10.1. CO EMISSIONS (per capita).csv",
    ],
    "Renewable energy consumption (% of total)": [
        "10.2. RENEWABLE ENERGY CONSUMPTION.csv",
        "10.2 RENEWABLE ENERGY CONSUMPTION.csv",
        "10.2. Renewable energy consumption.csv",
        "10.2 Renewable energy consumption.csv",
    ],
    "Forest area (sq. km or % depending on file)": [
        "10.3. FOREST AREA.csv",
        "10.3 FOREST AREA.csv",
        "10.3. Forest area.csv",
        "10.3 Forest area.csv",
    ],
    "Electricity access (% of population)": [
        "10.4. ELECTRICITY ACCESS.csv",
        "10.4 ELECTRICITY ACCESS.csv",
        "10.4. Electricity access.csv",
        "10.4 Electricity access.csv",
    ],
}

WDI_CODES = {
    "CO emissions (metric tons per capita)": "EN.ATM.CO2E.PC",
    "Renewable energy consumption (% of total)": "EG.FEC.RNEW.ZS",
    "Forest area (sq. km or % depending on file)": "AG.LND.FRST.K2 (atau AG.LND.FRST.ZS tergantung file)",
    "Electricity access (% of population)": "EG.ELC.ACCS.ZS",
}

SNDC_LENS = {
    "CO emissions (metric tons per capita)": {
        "sector": "Energy",
        "points": [
            "CO emissions membantu membaca intensitas emisi yang berkaitan dengan bauran energi dan efisiensi.",
            "Pembacaan yang rapi memeriksa tren emisi bersama perubahan pangsa energi terbarukan dan perluasan akses listrik.",
        ],
    },
    "Renewable energy consumption (% of total)": {
        "sector": "Energy",
        "points": [
            "Pangsa energi terbarukan memberi sinyal perubahan bauran energi.",
            "Kenaikan pangsa terbarukan lebih kuat maknanya jika diikuti stabilisasi atau penurunan emisi per kapita.",
        ],
    },
    "Forest area (sq. km or % depending on file)": {
        "sector": "FOLU",
        "points": [
            "Forest area relevan untuk membaca dinamika sektor FOLU dan potensi penyerapan karbon.",
            "Stabilitas atau peningkatan luas hutan mendukung interpretasi strategi mitigasi lintas sektor.",
        ],
    },
    "Electricity access (% of population)": {
        "sector": "Energy",
        "points": [
            "Akses listrik adalah indikator layanan dasar dan prasyarat aktivitas ekonomi.",
            "Dalam lensa Second NDC, perluasan akses idealnya sejalan dengan bauran pembangkit yang lebih bersih dan efisiensi.",
        ],
    },
}

SNDC_KEY_MESSAGES = [
    "Second NDC menggunakan reference year 2019, mencakup sektor Energy, IPPU, Waste, Agriculture, dan FOLU.",
    "Dokumen memakai metrik Global Warming Potential 100 tahun berdasarkan IPCC AR5 untuk konsistensi emisi setara CO2.",
    "Dokumen menekankan target puncak emisi nasional pada 2030 dan lintasan menuju Net Zero Emissions 2060 atau lebih cepat.",
]

AGG_EXACT = {
    "World",
    "European Union",
    "Euro area",
    "OECD members",
    "IDA & IBRD total",
    "IBRD only",
    "IDA total",
    "IDA blend",
    "IDA only",
    "Heavily indebted poor countries (HIPC)",
    "Least developed countries: UN classification",
    "Fragile and conflict affected situations",
}

AGG_SUBSTR = [
    " income",
    "oecd",
    "ida",
    "ibrd",
    "hipc",
    "euro area",
    "european union",
    "arab world",
    "central europe and the baltics",
    "east asia & pacific",
    "europe & central asia",
    "latin america & caribbean",
    "middle east & north africa",
    "north america",
    "south asia",
    "sub-saharan africa",
    "small states",
    "developing",
    "dividend",
    "total",
    "excluding",
    "members",
]

# =========================
# Helpers
# =========================
def is_aggregate_entity(name: str) -> bool:
    if not isinstance(name, str):
        return True
    n = name.strip()
    if n in AGG_EXACT:
        return True
    if " & " in n:
        return True
    low = n.lower()
    for t in AGG_SUBSTR:
        if t in low:
            return True
    return False

def orientation(indicator_label: str) -> str:
    low = indicator_label.lower()
    if "co emissions" in low:
        return "higher_worse"
    if "renewable" in low:
        return "higher_better"
    if "forest" in low:
        return "higher_better"
    if "electricity" in low:
        return "higher_better"
    return "neutral"

@st.cache_data
def load_csv_tolerant(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        return pd.DataFrame()
    for sep in [";", ",", "\t"]:
        try:
            df = pd.read_csv(path, sep=sep, engine="python", on_bad_lines="skip")
            if df.shape[1] > 1:
                return df
        except Exception:
            continue
    try:
        return pd.read_csv(path, engine="python", on_bad_lines="skip")
    except Exception:
        return pd.DataFrame()

def pick_existing_file(candidates: list[str]) -> str | None:
    for fname in candidates:
        p = os.path.join(DATA_DIR, fname)
        if os.path.exists(p):
            return p

    if os.path.isdir(DATA_DIR):
        all_files = [f for f in os.listdir(DATA_DIR) if f.lower().endswith(".csv")]
        for cand in candidates:
            key = cand.lower().replace(".csv", "")
            for f in all_files:
                if key in f.lower():
                    return os.path.join(DATA_DIR, f)

    return None

def clean_numeric_series(raw: pd.Series) -> pd.Series:
    s = raw.astype(str).str.strip()
    s = s.replace({"..": "", "NA": "", "N/A": "", "nan": "", "None": ""})

    has_comma = s.str.contains(",", na=False)
    has_dot = s.str.contains(r"\.", na=False)

    s.loc[has_comma & has_dot] = s.loc[has_comma & has_dot].str.replace(",", "", regex=False)
    s.loc[has_comma & ~has_dot] = s.loc[has_comma & ~has_dot].str.replace(",", ".", regex=False)

    s = s.str.replace("\u00a0", "", regex=False)
    return pd.to_numeric(s, errors="coerce")

def fmt(v, digits=2) -> str:
    try:
        return f"{float(v):,.{digits}f}"
    except Exception:
        return "NA"

def find_country_col(cols) -> str:
    for cand in ["Country Name", "country", "Country", "Negara", "Entity"]:
        if cand in cols:
            return cand
    return cols[0]

@st.cache_data
def fetch_pdf_bytes(url: str, timeout_sec: int = 25) -> bytes | None:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
            return resp.read()
    except (HTTPError, URLError, TimeoutError):
        return None
    except Exception:
        return None

def render_pdf_inline(pdf_bytes: bytes, height: int = 700):
    b64 = base64.b64encode(pdf_bytes).decode("utf-8")
    html = f"""
    <iframe
        src="data:application/pdf;base64,{b64}"
        width="100%"
        height="{height}"
        style="border:1px solid rgba(0,0,0,0.08); border-radius:14px;"
    ></iframe>
    """
    components.html(html, height=height + 10, scrolling=True)

# =========================
# Header
# =========================
st.write(
    "Halaman ini menampilkan indikator energi dan lingkungan berbasis file CSV bergaya World Bank yang tersimpan di folder `data/`. "
    "Tampilan mencakup statistik ringkas nilai terbaru per negara, peta dunia per tahun, interpretasi distribusi, analisis deskriptif, "
    "time series per negara, serta integrasi dokumen kebijakan Second NDC Indonesia."
)

with st.expander("📌 Definisi indikator (ringkas)", expanded=False):
    st.markdown(
        """
**CO emissions** menggambarkan emisi karbon dioksida (ekuivalen). Pada banyak dataset World Bank, satuan yang umum adalah emisi per kapita. Indikator ini membantu membaca tekanan emisi yang terkait dengan bauran energi, aktivitas ekonomi, dan intensitas konsumsi energi.

**Renewable energy consumption** menggambarkan porsi konsumsi energi yang bersumber dari energi terbarukan dalam total konsumsi energi. Indikator ini membantu membaca arah transisi energi, namun tetap perlu dipadankan dengan tren emisi dan konteks struktur energi.

**Forest area** menggambarkan luasan atau porsi kawasan berhutan. Indikator ini memberi konteks dinamika penyerapan karbon dan perubahan penggunaan lahan, terutama untuk membaca peran sektor FOLU dalam mitigasi.

**Electricity access** menggambarkan persentase populasi yang memiliki akses listrik. Indikator ini sering dipakai sebagai penanda layanan dasar dan pembangunan, lalu dihubungkan dengan konsekuensi emisi melalui bauran pembangkit.
"""
    )

# =========================
# Pick indicator and load CSV
# =========================
available = {}
for label, candidates in FILES.items():
    p = pick_existing_file(candidates)
    if p:
        available[label] = p

if not available:
    st.error(f"Tidak ada file CSV Page 10 ditemukan di folder `{DATA_DIR}/`.")
    st.stop()

indicator = st.selectbox("Pilih indikator", list(available.keys()))
file_path = available[indicator]

df = load_csv_tolerant(file_path)
if df.empty:
    st.error("File terbaca kosong atau gagal diproses.")
    st.stop()

st.subheader("📄 Preview Data Mentah")
st.dataframe(df.head(15), use_container_width=True)

# =========================
# Transform to long
# =========================
cols = [str(c) for c in df.columns]
cols_lower = [c.lower().strip() for c in cols]

df_long = pd.DataFrame()

if "year" in cols_lower:
    rename_map = {}
    for c in df.columns:
        cl = str(c).strip().lower()
        if cl in ["country", "country name", "negara", "entity"]:
            rename_map[c] = "country"
        if cl == "year":
            rename_map[c] = "year"

    df2 = df.rename(columns=rename_map)
    if "country" not in df2.columns or "year" not in df2.columns:
        st.error("Kolom country atau year tidak ditemukan pada format long.")
        st.stop()

    value_cols = [c for c in df2.columns if c not in ["country", "year"]]
    if not value_cols:
        st.error("Tidak ditemukan kolom nilai pada format long.")
        st.stop()

    value_col = value_cols[0] if len(value_cols) == 1 else st.selectbox("Pilih kolom nilai", value_cols)
    df_long = df2[["country", "year", value_col]].rename(columns={value_col: "value"}).copy()
    df_long["year"] = pd.to_numeric(df_long["year"], errors="coerce")
    df_long["value"] = clean_numeric_series(df_long["value"])
    df_long = df_long.dropna(subset=["year", "value"])
else:
    year_cols = [c for c in cols if c.isdigit() and len(c) == 4]
    if not year_cols:
        st.error("Tidak ditemukan kolom tahun (4 digit) pada format wide.")
        st.stop()

    country_col = find_country_col(df.columns)
    df_long = (
        df.melt(
            id_vars=[country_col],
            value_vars=year_cols,
            var_name="year",
            value_name="value",
        )
        .rename(columns={country_col: "country"})
        .copy()
    )

    df_long["year"] = pd.to_numeric(df_long["year"], errors="coerce")
    df_long["value"] = clean_numeric_series(df_long["value"])
    df_long = df_long.dropna(subset=["year", "value"])

df_long["country"] = df_long["country"].astype(str).str.strip()
df_long["year"] = df_long["year"].astype(int)

df_long = df_long[~df_long["country"].apply(is_aggregate_entity)].copy()
if df_long.empty:
    st.error("Data kosong setelah menghapus agregat regional dan kelompok pendapatan.")
    st.stop()

# =========================
# Latest snapshot stats
# =========================
st.subheader("🔎 Statistik Ringkas (nilai terbaru per negara)")

df_latest = (
    df_long.sort_values(["country", "year"])
    .groupby("country", as_index=False)
    .tail(1)
    .rename(columns={"year": "latest_year", "value": "latest_value"})
)

top10 = df_latest.sort_values("latest_value", ascending=False).head(10).reset_index(drop=True)
bottom10 = df_latest.sort_values("latest_value", ascending=True).head(10).reset_index(drop=True)

c1, c2 = st.columns(2)
with c1:
    st.markdown("**Top 10 (terbesar)**")
    st.dataframe(top10[["country", "latest_value"]], use_container_width=True, hide_index=True)
with c2:
    st.markdown("**Bottom 10 (terendah)**")
    st.dataframe(bottom10[["country", "latest_value"]], use_container_width=True, hide_index=True)

# =========================
# Second NDC lens (indicator-aware)
# =========================
lens = SNDC_LENS.get(indicator)
if lens:
    with st.expander("📌 Second NDC lens untuk indikator yang dipilih", expanded=True):
        st.markdown(f"**Keterkaitan sektor Second NDC**: {lens['sector']}")
        for p in lens["points"]:
            st.write(f"• {p}")
        st.caption("Lens ini dipakai sebagai konteks membaca tren, bukan sebagai klaim kausal.")

# =========================
# World map
# =========================
years = sorted(df_long["year"].unique().tolist())
year_min = int(min(years))
year_max = int(max(years))

st.subheader("🌍 Peta Dunia")

left, right = st.columns([3, 1])
with right:
    map_mode = st.radio("Mode peta", ["Continuous (nilai)", "Quantile (buckets)"])
    color_scale = st.selectbox("Skala warna", ["Viridis", "Plasma", "Cividis", "Turbo", "Blues"], index=0)
with left:
    year_select = st.slider("Pilih tahun", year_min, year_max, year_max)

df_map = df_long[df_long["year"] == int(year_select)].copy()

if df_map.empty:
    st.warning("Tidak ada data untuk tahun yang dipilih.")
else:
    try:
        if map_mode == "Quantile (buckets)":
            q = df_map["value"].dropna()
            if q.shape[0] < 5:
                fig = px.choropleth(
                    df_map,
                    locations="country",
                    locationmode="country names",
                    color="value",
                    hover_name="country",
                    color_continuous_scale=color_scale,
                    labels={"value": indicator},
                    title=f"{indicator} ({year_select})",
                )
            else:
                df_map["bucket"] = pd.qcut(df_map["value"], 4, labels=["Q1", "Q2", "Q3", "Q4"])
                fig = px.choropleth(
                    df_map,
                    locations="country",
                    locationmode="country names",
                    color="bucket",
                    hover_name="country",
                    title=f"{indicator} ({year_select})",
                    labels={"bucket": "Kelompok kuartil"},
                )
        else:
            fig = px.choropleth(
                df_map,
                locations="country",
                locationmode="country names",
                color="value",
                hover_name="country",
                color_continuous_scale=color_scale,
                labels={"value": indicator},
                title=f"{indicator} ({year_select})",
            )

        fig.update_layout(margin={"r": 0, "t": 40, "l": 0, "b": 0}, height=540)
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error("Peta gagal dibuat. Nama negara perlu sesuai standar Plotly.")
        st.exception(e)

# =========================
# Map interpretation
# =========================
st.subheader("🧠 Interpretasi peta (tahun terpilih)")

vals = df_map["value"].dropna()
n = int(vals.shape[0])

if n < 5:
    st.write("Data pada tahun terpilih terlalu sedikit untuk interpretasi distribusi.")
else:
    q25, q50, q75 = vals.quantile([0.25, 0.50, 0.75]).tolist()

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Jumlah negara (ada data)", f"{n:,}")
    m2.metric("Kuartil 1 (Q1)", fmt(q25))
    m3.metric("Median (Q2)", fmt(q50))
    m4.metric("Kuartil 3 (Q3)", fmt(q75))

    o = orientation(indicator)
    if o == "higher_worse":
        st.markdown(
            "Distribusi kuartil memecah negara menjadi empat kelompok pada tahun terpilih. "
            "Nilai di atas Q3 menggambarkan kelompok dengan tekanan emisi lebih tinggi pada tahun itu, "
            "sedangkan nilai di bawah Q1 menggambarkan kelompok dengan tekanan emisi lebih rendah. "
            "Pembacaan yang lebih kuat memeriksa tren beberapa tahun, lalu mengaitkannya dengan bauran energi dan efisiensi."
        )
    else:
        st.markdown(
            "Distribusi kuartil memecah negara menjadi empat kelompok pada tahun terpilih. "
            "Nilai di atas Q3 menggambarkan kelompok capaian lebih tinggi, sedangkan nilai di bawah Q1 menggambarkan kelompok capaian lebih rendah. "
            "Pembacaan yang lebih kuat memeriksa konsistensi tren dan keterkaitannya dengan faktor struktural seperti infrastruktur dan tata kelola."
        )

# =========================
# Time series
# =========================
st.subheader("📈 Time Series per Negara")

country_list = sorted(df_long["country"].dropna().unique().tolist())
default_countries = ["Indonesia"] if "Indonesia" in country_list else ([country_list[0]] if country_list else [])

selected_countries = st.multiselect(
    "Pilih negara (bisa lebih dari satu)",
    country_list,
    default=default_countries,
)

df_ts = df_long[df_long["country"].isin(selected_countries)].sort_values(["country", "year"])

if df_ts.empty:
    st.info("Tidak ada data untuk negara yang dipilih.")
else:
    fig_ts = px.line(
        df_ts,
        x="year",
        y="value",
        color="country",
        markers=True,
        labels={"year": "Tahun", "value": indicator, "country": "Negara"},
        title=f"Time series {indicator}",
    )
    fig_ts.update_layout(margin={"l": 0, "r": 0, "t": 40, "b": 0})
    st.plotly_chart(fig_ts, use_container_width=True)

    with st.expander("📄 Data time series (opsional)", expanded=False):
        st.dataframe(df_ts.reset_index(drop=True), use_container_width=True)

# =========================
# Narrative (kept)
# =========================
st.subheader("🔍 Temuan Utama & Interpretasi Data")

st.markdown(
    """
### 1️⃣ Emisi CO₂ Tidak Selalu Mencerminkan Tingkat Industrialisasi

Berdasarkan indikator **CO emissions**, beberapa negara yang muncul pada kelompok nilai tertinggi tidak seluruhnya merupakan negara dengan tingkat industrialisasi yang tinggi atau memiliki kegiatan industri yang maju. Pola ini menunjukkan bahwa tingginya emisi CO₂ tidak dapat langsung diinterpretasikan sebagai tingkat industrialisasi yang tinggi.

Pada negara berkembang atau wilayah konflik, emisi dapat meningkat karena penggunaan energi fosil yang tidak efisien, ketergantungan pada pembangkit berbasis diesel, keterbatasan teknologi yang lebih bersih, dan kelemahan infrastruktur energi. Pada konteks ini, emisi tinggi lebih dekat dengan gambaran inefisiensi sistem energi dibanding kekuatan industrialisasi.
"""
)

st.markdown(
    """
### 2️⃣ Karakteristik Negara Industri Maju

Negara industri seperti **Jepang, Jerman, dan Belgia** sering menunjukkan pola yang berbeda. Emisi CO₂ berada pada level relatif tinggi, namun cenderung lebih stabil pada time series. Di saat yang sama, akses listrik mendekati penuh dan proporsi energi terbarukan cenderung meningkat. Pola tersebut konsisten dengan fase pengelolaan emisi dan transisi energi yang berjalan bersamaan dengan kapasitas industri yang sudah matang.
"""
)

st.markdown(
    """
### 3️⃣ Akses Listrik sebagai Indikator Fundamental Pembangunan Suatu Negara

Indikator **Electricity access** menunjukkan kesenjangan yang jelas antar negara. Negara dengan akses listrik rendah sering memiliki aktivitas ekonomi yang lebih terbatas. Emisi CO₂ yang rendah pada kelompok ini tidak selalu mencerminkan keberlanjutan, namun dapat merefleksikan keterbatasan pembangunan dan konsumsi energi. Akses listrik yang tinggi berperan sebagai prasyarat bagi produktivitas, layanan dasar, dan aktivitas industri.
"""
)

st.markdown(
    """
### 4️⃣ Energi Terbarukan dan Struktur Energi Negara Berkembang

Beberapa negara berkembang menunjukkan proporsi **energi terbarukan** yang relatif tinggi. Pola ini tidak selalu berarti adopsi teknologi energi hijau yang maju. Pada sejumlah konteks, proporsi terbarukan tinggi dapat muncul karena ketergantungan pada biomassa tradisional atau hidro yang telah lama digunakan. Interpretasi pangsa energi terbarukan lebih kuat jika diperiksa bersama tren emisi, akses listrik, dan indikator kesejahteraan.
"""
)

st.markdown(
    """
### 5️⃣ Forest Area dan Trade off Pembangunan

Indikator **Forest area** sering merefleksikan trade off antara ekspansi ekonomi, pembangunan energi, dan keberlanjutan lingkungan. Negara dengan konsumsi energi dan emisi tinggi dapat menghadapi tekanan terhadap hutan melalui ekspansi lahan dan aktivitas ekstraktif. Negara dengan hutan luas pun dapat mengalami tekanan jika intensitas ekstraksi meningkat. Karena itu, pembacaan forest area perlu ditempatkan pada konteks perubahan tata guna lahan dan kualitas tata kelola.
"""
)

st.markdown(
    """
### 6️⃣ Second NDC Indonesia sebagai Lensa Interpretasi Indikator

Second Nationally Determined Contribution Indonesia menempatkan pembacaan indikator energi dan lingkungan dalam kerangka target nasional yang lebih eksplisit. Dokumen ini menggunakan reference year 2019, mencakup sektor Energy, IPPU, Waste, Agriculture, dan FOLU, serta memakai metrik Global Warming Potential 100 tahun berdasarkan IPCC AR5 untuk konsistensi perhitungan emisi setara CO2. Dokumen menekankan puncak emisi nasional pada 2030 dan lintasan menuju Net Zero Emissions 2060 atau lebih cepat.

Implikasi terhadap pembacaan indikator di halaman ini:

1. **CO emissions** dan **Renewable energy consumption** membantu membaca arah transisi energi. Tren penurunan emisi per kapita bersamaan dengan kenaikan pangsa energi terbarukan lebih konsisten dengan upaya menjaga peaking 2030 dan menguatkan dekarbonisasi sektor energi.

2. **Electricity access** memberi konteks layanan dasar. Kenaikan akses listrik penting untuk kesejahteraan, namun konsekuensi emisinya ditentukan oleh bauran pembangkit. Perluasan akses idealnya bergerak bersama efisiensi dan peningkatan energi bersih.

3. **Forest area** relevan untuk membaca dinamika FOLU. Stabilitas atau peningkatan tutupan hutan mendukung interpretasi strategi pengendalian deforestasi, restorasi, dan penguatan penyerapan karbon.
"""
)

st.success(
    "🔎 Kesimpulan Umum\n\n"
    "Analisis lintas indikator menunjukkan bahwa pembangunan berkelanjutan tidak dapat dibaca dari satu indikator saja. "
    "Pembacaan yang lebih kuat memadankan indikator energi, emisi, layanan dasar, dan kondisi lingkungan dalam satu narasi."
)

# =========================
# Integrated SNDC document (URL)
# =========================
with st.expander("📄 Dokumen kebijakan: Second NDC Indonesia (PDF)", expanded=False):
    st.link_button("Buka dokumen di UNFCCC", SNDC_URL)
    st.markdown("Ringkasan poin kunci yang dipakai sebagai konteks pembacaan halaman ini:")
    for msg in SNDC_KEY_MESSAGES:
        st.write(f"• {msg}")

    pdf_bytes = fetch_pdf_bytes(SNDC_URL)
    if pdf_bytes is None:
        st.warning("PDF tidak bisa diambil dari link saat ini. Coba refresh, atau cek koneksi.")
    else:
        st.download_button(
            "⬇ Download PDF Second NDC",
            data=pdf_bytes,
            file_name="Indonesia_SecondNDC_2025.10.24.pdf",
            mime="application/pdf",
        )
        st.caption("Preview di bawah ini diambil langsung dari file PDF di UNFCCC.")
        render_pdf_inline(pdf_bytes, height=720)

# =========================
# Download long-format (button only)
# =========================
st.subheader("📘 Data Lengkap (long format)")
csv_bytes = df_long.to_csv(index=False).encode("utf-8")
safe = (
    indicator.replace(" ", "_")
    .replace("/", "_")
    .replace("(", "")
    .replace(")", "")
    .replace("%", "pct")
)
st.download_button(
    "⬇ Download data (CSV)",
    data=csv_bytes,
    file_name=f"page10_energi_lingkungan_{safe}.csv",
    mime="text/csv",
)

# =========================
# Sources
# =========================
with st.expander("📚 Sources dan referensi", expanded=False):
    wdi_code = WDI_CODES.get(indicator, "lihat metadata WDI untuk indikator terkait")
    st.markdown(
        f"""
**Data**
1. World Bank, World Development Indicators (WDI). Indikator rujukan: **{wdi_code}**.

**Dokumen kebijakan**
2. UNFCCC. Indonesia Second NDC PDF (diakses melalui tautan pada halaman ini).

**Catatan interpretasi**
3. Pembacaan bersifat deskriptif. Interpretasi tren sebaiknya memeriksa konsistensi antar indikator, perubahan definisi, dan konteks struktural.
"""
    )
    st.link_button("World Bank WDI (home)", "https://databank.worldbank.org/source/world-development-indicators")
    if isinstance(wdi_code, str) and wdi_code and " " not in wdi_code and "(" not in wdi_code:
        st.link_button(f"World Bank Indicator {wdi_code}", f"https://data.worldbank.org/indicator/{wdi_code}")
