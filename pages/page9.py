# pages/page9.py
import streamlit as st
import pandas as pd
import os
import plotly.express as px

st.set_page_config(layout="wide", page_title="Kesehatan", page_icon="🏥")

st.title("🏥 Kesehatan")
st.write(
    "Halaman ini menyajikan indikator kesehatan berbasis file CSV bergaya World Bank di folder `data/`. "
    "Tampilan mencakup statistik ringkas nilai terbaru per negara, peta dunia per tahun, interpretasi distribusi, "
    "analisis deskriptif lintas negara, serta tren time series per negara."
)

# -----------------------------
# Definisi indikator (template)
# -----------------------------
with st.expander("📌 Definisi indikator (ringkas)", expanded=False):
    st.markdown(
        """
**Health expenditure (current US$ atau % of GDP)** mengukur besaran pengeluaran kesehatan. Pada beberapa file, indikator hadir sebagai nominal (US$) sehingga sangat dipengaruhi ukuran ekonomi dan kurs. Pada file lain, indikator hadir sebagai persentase Produk Domestik Bruto sehingga lebih mudah dibandingkan lintas negara sebagai intensitas belanja kesehatan relatif.

**Maternal mortality (per 100,000 live births)** mengukur risiko kematian ibu terkait kehamilan dan persalinan. Nilai lebih tinggi biasanya mencerminkan keterbatasan akses layanan obstetri, keterlambatan penanganan, serta kualitas sistem rujukan dan layanan prenatal.

**Infant mortality (per 1,000 live births)** mengukur risiko kematian bayi pada tahun pertama kehidupan. Nilai lebih tinggi sering berkaitan dengan gizi, kualitas layanan kesehatan primer, kondisi sanitasi, dan faktor sosial ekonomi.

**People using safely managed drinking water services (%)** mengukur proporsi penduduk dengan akses air minum yang dikelola aman. Nilai lebih tinggi biasanya mencerminkan infrastruktur air bersih yang lebih baik dan perlindungan kesehatan publik yang lebih kuat.
"""
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
# CSV loader (tolerant)
# -----------------------------
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

def _to_float(x):
    try:
        return float(x)
    except Exception:
        return None

def _fmt(v, digits=2):
    v = _to_float(v)
    if v is None:
        return "NA"
    return f"{v:,.{digits}f}"

def _clean_numeric_series(raw: pd.Series) -> pd.Series:
    s = raw.astype(str).str.strip()
    s = s.replace({"..": "", "NA": "", "N/A": "", "nan": "", "None": ""})

    has_comma = s.str.contains(",", na=False)
    has_dot = s.str.contains(r"\.", na=False)

    # 1,234.56 -> 1234.56
    s.loc[has_comma & has_dot] = s.loc[has_comma & has_dot].str.replace(",", "", regex=False)
    # 55,00 -> 55.00
    s.loc[has_comma & ~has_dot] = s.loc[has_comma & ~has_dot].str.replace(",", ".", regex=False)

    s = s.str.replace("\u00a0", "", regex=False)
    return pd.to_numeric(s, errors="coerce")

def find_country_col(cols) -> str:
    candidates = ["Country Name", "country", "Country", "Negara", "Entity"]
    for cand in candidates:
        if cand in cols:
            return cand
    return cols[0]

# -----------------------------
# Filter agregat (konsisten)
# -----------------------------
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
    "oecd", "ida", "ibrd", "hipc",
    "euro area", "european union",
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

def _orientation(label: str) -> str:
    """
    higher_worse: indikator yang nilai lebih tinggi biasanya dibaca sebagai risiko/beban lebih tinggi
    higher_better: indikator yang nilai lebih tinggi biasanya dibaca sebagai capaian lebih baik
    neutral: indikator yang maknanya tergantung konteks
    """
    low = label.lower()
    if "maternal mortality" in low or "infant mortality" in low:
        return "higher_worse"
    if "drinking water" in low:
        return "higher_better"
    if "health expenditure" in low:
        return "neutral"
    return "neutral"

def _interpret_note(indicator_label: str) -> str:
    low = indicator_label.lower()
    if "health expenditure" in low:
        return (
            "Belanja kesehatan lebih informatif jika dibaca bersama struktur pembiayaan (publik vs privat), efisiensi layanan, "
            "serta indikator outcome seperti mortalitas dan akses air bersih."
        )
    if "maternal mortality" in low:
        return (
            "Maternal mortality sensitif pada kualitas layanan obstetri, sistem rujukan, dan akses tenaga kesehatan terlatih, "
            "sehingga pembacaan lintas negara perlu memperhatikan kapasitas layanan dasar dan kedaruratan."
        )
    if "infant mortality" in low:
        return (
            "Infant mortality sering bergerak bersama gizi, sanitasi, dan kualitas layanan kesehatan primer. "
            "Tren menurun biasanya menandakan perbaikan layanan ibu-anak dan kesehatan lingkungan."
        )
    if "drinking water" in low:
        return (
            "Akses air minum aman biasanya berkaitan dengan kualitas infrastruktur dasar. "
            "Perbedaan lintas negara sering mencerminkan kapasitas investasi dan tata kelola layanan air."
        )
    return "Interpretasi bersifat deskriptif dan perlu dibaca bersama konteks struktur layanan dan kondisi sosial ekonomi."

# -----------------------------
# Detect available files
# -----------------------------
available = [k for k, v in FILES.items() if os.path.exists(os.path.join(DATA_DIR, v))]
if not available:
    st.error(f"Tidak ditemukan file CSV Page 9 di folder `{DATA_DIR}/`.")
    st.stop()

indicator = st.selectbox("Pilih indikator", available)
file_path = os.path.join(DATA_DIR, FILES[indicator])

df = load_csv_tolerant(file_path)
if df.empty:
    st.error(f"File `{os.path.basename(file_path)}` kosong atau gagal dibaca.")
    st.stop()

# -----------------------------
# Preview data (template)
# -----------------------------
st.subheader("📄 Preview Data Mentah")
st.dataframe(df.head(15), use_container_width=True)

# -----------------------------
# Transform to long format
# -----------------------------
cols_raw = [str(c).strip() for c in df.columns]
cols_lower = [c.lower() for c in cols_raw]

df_long = pd.DataFrame()

# LONG format jika ada kolom year
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
        st.error("Kolom country atau year tidak ditemukan pada file long-format.")
        st.stop()

    value_cols = [c for c in df2.columns if c not in ["country", "year"]]
    if not value_cols:
        st.error("Tidak ditemukan kolom nilai pada file long-format.")
        st.stop()

    if len(value_cols) > 1:
        val_col = st.selectbox("Pilih kolom nilai (value)", value_cols)
    else:
        val_col = value_cols[0]

    df_long = df2[["country", "year", val_col]].rename(columns={val_col: "value"}).copy()
    df_long["year"] = pd.to_numeric(df_long["year"], errors="coerce")
    df_long["value"] = _clean_numeric_series(df_long["value"])
    df_long = df_long.dropna(subset=["year", "value"])

else:
    # WIDE format: kolom tahun 4 digit
    year_cols = [c for c in cols_raw if c.isdigit() and len(c) == 4]
    if not year_cols:
        st.error("Tidak ditemukan kolom tahun (misalnya 1990, 2005) pada header.")
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
    df_long["value"] = _clean_numeric_series(df_long["value"])
    df_long = df_long.dropna(subset=["year", "value"])

if df_long.empty:
    st.error("Data kosong setelah transformasi.")
    st.stop()

df_long["country"] = df_long["country"].astype(str).str.strip()
df_long["year"] = df_long["year"].astype(int)

# Filter agregat
df_long = df_long[~df_long["country"].apply(is_aggregate_entity)].copy()
if df_long.empty:
    st.error("Data kosong setelah menghapus agregat regional dan kelompok pendapatan.")
    st.stop()

# -----------------------------
# Statistik ringkas (template)
# -----------------------------
st.subheader("🔎 Statistik Ringkas (nilai terbaru per negara)")

df_latest = (
    df_long.sort_values(["country", "year"])
          .groupby("country", as_index=False)
          .tail(1)
          .rename(columns={"year": "latest_year", "value": "latest_value"})
)

top10 = df_latest.sort_values("latest_value", ascending=False).head(10)
bottom10 = df_latest.sort_values("latest_value", ascending=True).head(10)

cL, cR = st.columns(2)
with cL:
    st.markdown("**Top 10 (terbesar)**")
    st.dataframe(top10[["country", "latest_value"]], use_container_width=True)
with cR:
    st.markdown("**Bottom 10 (terendah)**")
    st.dataframe(bottom10[["country", "latest_value"]], use_container_width=True)

# -----------------------------
# Peta dunia (template)
# -----------------------------
years = sorted(df_long["year"].unique().tolist())
year_min = int(min(years))
year_max = int(max(years))

year_select = st.slider("Pilih tahun untuk peta dunia", year_min, year_max, year_max)
df_map = df_long[df_long["year"] == int(year_select)].copy()

st.subheader(f"🌍 Peta Dunia — {indicator} ({year_select})")

if df_map.empty:
    st.warning("Tidak ada data untuk tahun yang dipilih.")
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
            title=f"{indicator} — {year_select}",
        )
        fig.update_layout(margin={"r": 0, "t": 40, "l": 0, "b": 0}, height=520)
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error("Peta gagal dibuat. Periksa apakah nama negara di CSV dikenali oleh Plotly.")
        st.exception(e)

# -----------------------------
# Interpretasi peta (template)
# -----------------------------
st.subheader("🧠 Interpretasi peta (tahun terpilih)")

vals = df_map["value"].dropna()
n = int(vals.shape[0])

if n < 5:
    st.write("Data pada tahun terpilih terlalu sedikit untuk interpretasi distribusi.")
else:
    q25, q50, q75 = vals.quantile([0.25, 0.50, 0.75]).tolist()

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Jumlah negara (ada data)", f"{n:,}")
    m2.metric("Kuartil 1 (Q1)", _fmt(q25))
    m3.metric("Median (Q2)", _fmt(q50))
    m4.metric("Kuartil 3 (Q3)", _fmt(q75))

    orient = _orientation(indicator)

    if orient == "higher_worse":
        st.markdown(
            """
Kuartil memecah negara menjadi empat kelompok pada tahun terpilih. Untuk indikator mortalitas, posisi di atas Q3 berarti kelompok dengan risiko atau beban lebih tinggi pada tahun itu. Posisi di bawah Q1 berarti kelompok dengan risiko lebih rendah. Perbedaan lintas negara biasanya mencerminkan kualitas layanan dasar, akses layanan, serta faktor kesehatan lingkungan.
"""
        )
    elif orient == "higher_better":
        st.markdown(
            """
Kuartil memecah negara menjadi empat kelompok pada tahun terpilih. Untuk akses air minum aman, posisi di atas Q3 berarti kelompok dengan capaian akses lebih tinggi, sedangkan posisi di bawah Q1 berarti kelompok dengan capaian akses lebih rendah. Perbedaan lintas negara sering terkait dengan kualitas infrastruktur dasar dan kapasitas pengelolaan layanan publik.
"""
        )
    else:
        st.markdown(
            """
Kuartil memecah negara menjadi empat kelompok pada tahun terpilih. Untuk belanja kesehatan, nilai yang lebih tinggi perlu dibaca bersama konteks pembiayaan, efisiensi layanan, dan outcome kesehatan. Nilai tinggi dapat mencerminkan kapasitas fiskal yang besar atau biaya layanan yang lebih mahal, sedangkan nilai rendah bisa berarti keterbatasan pendanaan atau sistem yang lebih efisien, tergantung konteks.
"""
        )

    st.caption(_interpret_note(indicator))

# -----------------------------
# Analisis deskriptif (panjang, selevel page lain)
# -----------------------------
st.subheader("🧠 Analisis Kesehatan Deskriptif")

df_rank = df_map[["country", "value"]].dropna().sort_values("value", ascending=False)
top5 = df_rank.head(5)["country"].tolist()
bottom5 = df_rank.tail(5)["country"].tolist()

vmin = float(df_rank["value"].min()) if not df_rank.empty else None
vmax = float(df_rank["value"].max()) if not df_rank.empty else None
iqr = None
if df_rank.shape[0] >= 5:
    q25r, q50r, q75r = df_rank["value"].quantile([0.25, 0.50, 0.75]).tolist()
    iqr = q75r - q25r

orient = _orientation(indicator)

if orient == "higher_worse":
    st.markdown(
        f"""
Pada tahun **{year_select}**, nilai **{indicator}** menunjukkan variasi lintas negara yang tajam. Kelompok nilai tertinggi didominasi oleh **{", ".join(top5)}**, sementara kelompok nilai terendah didominasi oleh **{", ".join(bottom5)}**. Rentang nilai bergerak dari **{_fmt(vmin)}** hingga **{_fmt(vmax)}**, dengan sebaran antar kuartil sekitar **{_fmt(iqr)}** jika dihitung dari distribusi tahun ini.

Untuk indikator mortalitas, nilai tinggi biasanya menandakan beban kesehatan ibu atau bayi yang lebih berat. Angka tersebut cenderung terkait dengan akses layanan kesehatan dasar, kualitas layanan obstetri, cakupan imunisasi dan gizi, serta kondisi sanitasi dan lingkungan. Perbedaan antar negara pada kelompok atas sering mencerminkan keterlambatan penanganan dan kapasitas layanan yang belum merata, terutama pada wilayah dengan keterbatasan fasilitas dan tenaga kesehatan.

Kelompok nilai rendah biasanya menunjukkan sistem layanan maternal dan kesehatan anak yang lebih kuat, dengan jangkauan pelayanan yang lebih merata dan protokol penanganan yang lebih efektif. Tren jangka panjang menjadi pembeda penting, karena penurunan mortalitas yang konsisten sering datang dari kombinasi intervensi kesehatan primer, pembiayaan kesehatan yang stabil, dan perbaikan layanan publik dasar.
"""
    )
elif orient == "higher_better":
    st.markdown(
        f"""
Pada tahun **{year_select}**, indikator **{indicator}** memperlihatkan gap yang jelas antar negara. Kelompok nilai tertinggi didominasi oleh **{", ".join(top5)}**, sedangkan kelompok nilai terendah didominasi oleh **{", ".join(bottom5)}**. Rentang nilai bergerak dari **{_fmt(vmin)}** hingga **{_fmt(vmax)}**, dengan sebaran antar kuartil sekitar **{_fmt(iqr)}** jika dihitung dari distribusi tahun ini.

Untuk akses air minum yang dikelola aman, nilai tinggi biasanya berkaitan dengan ketersediaan infrastruktur air bersih, kualitas pengolahan, serta kepastian layanan yang berkelanjutan. Negara pada kelompok atas umumnya memiliki kapasitas investasi dan tata kelola layanan air yang lebih kuat, sehingga risiko penyakit berbasis air dan beban kesehatan publik cenderung lebih rendah.

Kelompok nilai rendah sering menunjukkan keterbatasan infrastruktur dan tantangan tata kelola yang berdampak langsung pada kesehatan masyarakat. Pembacaan yang lebih kuat biasanya mengaitkan indikator ini dengan outcome lain seperti mortalitas bayi dan beban penyakit menular, karena kualitas air dan sanitasi sering menjadi faktor penentu di banyak konteks.
"""
    )
else:
    st.markdown(
        f"""
Pada tahun **{year_select}**, indikator **{indicator}** menunjukkan perbedaan lintas negara yang besar. Kelompok nilai tertinggi didominasi oleh **{", ".join(top5)}**, sementara kelompok nilai terendah didominasi oleh **{", ".join(bottom5)}**. Rentang nilai bergerak dari **{_fmt(vmin)}** hingga **{_fmt(vmax)}**, dengan sebaran antar kuartil sekitar **{_fmt(iqr)}** jika dihitung dari distribusi tahun ini.

Belanja kesehatan lebih tepat dibaca sebagai sinyal kapasitas pembiayaan dan intensitas pengeluaran pada sektor kesehatan. Nilai tinggi dapat mencerminkan ruang fiskal yang luas, biaya layanan yang relatif mahal, atau struktur pembiayaan yang mendorong spending lebih besar. Nilai rendah dapat berarti keterbatasan pendanaan, tetapi pada beberapa konteks juga dapat muncul dari efisiensi layanan atau model pembiayaan yang berbeda.

Kekuatan interpretasi meningkat saat belanja kesehatan dibaca bersama outcome. Penurunan mortalitas dan peningkatan akses layanan dasar yang berjalan seiring dengan belanja yang memadai sering menjadi indikator sistem kesehatan yang membaik. Jika belanja meningkat tanpa perbaikan outcome, pertanyaan yang biasanya muncul berkaitan dengan efisiensi, ketimpangan akses, dan tata kelola pembiayaan kesehatan.
"""
    )

st.caption("Catatan: Analisis ini bersifat deskriptif dan tidak dimaksudkan sebagai inferensi kausal.")

# -----------------------------
# Time series (template)
# -----------------------------
st.subheader("📈 Time Series per Negara")

country_list = sorted(df_long["country"].dropna().unique().tolist())
if not country_list:
    st.info("Tidak ada negara tersedia.")
else:
    default_country = "Indonesia" if "Indonesia" in country_list else country_list[0]
    selected_country = st.selectbox("Pilih negara untuk grafik time series", country_list, index=country_list.index(default_country))
    df_country = df_long[df_long["country"] == selected_country].sort_values("year")

    if df_country.empty:
        st.write("Tidak ada data time series untuk negara ini.")
    else:
        fig_ts = px.line(
            df_country,
            x="year",
            y="value",
            markers=True,
            title=f"{indicator} — {selected_country}",
            labels={"year": "Tahun", "value": indicator},
        )
        fig_ts.update_layout(margin={"l": 0, "r": 0, "t": 40, "b": 0})
        st.plotly_chart(fig_ts, use_container_width=True)

        st.subheader("🧾 Interpretasi tren (negara terpilih)")

        last_year = int(df_country["year"].max())
        last_val = float(df_country.loc[df_country["year"] == last_year, "value"].iloc[0])

        start_year_candidate = last_year - 10
        df_window = df_country[df_country["year"] >= start_year_candidate].copy()

        if df_window.shape[0] < 2:
            start_year = int(df_country["year"].min())
            start_val = float(df_country.loc[df_country["year"] == start_year, "value"].iloc[0])
            window_label = f"sejak {start_year}"
        else:
            start_year = int(df_window["year"].min())
            start_val = float(df_country.loc[df_country["year"] == start_year, "value"].iloc[0])
            window_label = f"{start_year}–{last_year}"

        delta = last_val - start_val
        years_span = max(1, last_year - start_year)
        avg_change = delta / years_span

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Tahun terakhir", f"{last_year}")
        k2.metric("Nilai terakhir", _fmt(last_val))
        k3.metric(f"Perubahan ({window_label})", _fmt(delta))
        k4.metric("Rata rata perubahan per tahun", _fmt(avg_change))

        orient = _orientation(indicator)
        if orient == "higher_worse":
            if avg_change < 0:
                st.markdown(
                    "Tren menurun mengarah pada perbaikan outcome pada periode pengamatan. "
                    "Penjelasan yang paling sering muncul berkaitan dengan penguatan layanan primer, peningkatan akses, dan perbaikan kesehatan lingkungan."
                )
            elif avg_change > 0:
                st.markdown(
                    "Tren meningkat mengarah pada memburuknya outcome pada periode pengamatan. "
                    "Pembacaan yang rapi mengecek apakah perubahan ini terpusat pada beberapa tahun ekstrem atau bergerak konsisten."
                )
            else:
                st.markdown("Tren relatif stabil pada periode pengamatan.")
        elif orient == "higher_better":
            if avg_change > 0:
                st.markdown(
                    "Tren meningkat mengarah pada perluasan akses pada periode pengamatan. "
                    "Perubahan yang konsisten sering terkait investasi infrastruktur dan perbaikan tata kelola layanan."
                )
            elif avg_change < 0:
                st.markdown(
                    "Tren menurun mengarah pada penurunan capaian akses pada periode pengamatan. "
                    "Pembacaan yang rapi mengecek perubahan definisi, kualitas data, dan episode gangguan layanan."
                )
            else:
                st.markdown("Tren relatif stabil pada periode pengamatan.")
        else:
            if avg_change > 0:
                st.markdown(
                    "Nilai bergerak naik pada periode pengamatan. "
                    "Untuk belanja kesehatan, kenaikan perlu dibaca bersama outcome dan struktur pembiayaan agar interpretasinya tidak keliru."
                )
            elif avg_change < 0:
                st.markdown(
                    "Nilai bergerak turun pada periode pengamatan. "
                    "Untuk belanja kesehatan, penurunan bisa mencerminkan efisiensi atau keterbatasan pembiayaan, tergantung konteks."
                )
            else:
                st.markdown("Tren relatif stabil pada periode pengamatan.")

# -----------------------------
# Sources (template)
# -----------------------------
with st.expander("📚 Sources dan referensi", expanded=False):
    st.markdown(
        """
**Data (World Bank, World Development Indicators)**
Health expenditure kemungkinan menggunakan salah satu indikator berikut, tergantung file yang dipakai:
SH.XPD.CHEX.CD (current US$) atau SH.XPD.CHEX.GD.ZS (% of GDP)  
Maternal mortality ratio: SH.STA.MMRT  
Infant mortality rate: SP.DYN.IMRT.IN  
Safely managed drinking water services: SH.H2O.SMDW.ZS  

**Referensi interpretasi (ringkas)**
World Health Organization: kerangka sistem kesehatan dan pembiayaan kesehatan  
UNICEF dan WHO: kesehatan ibu dan anak, mortalitas, serta faktor determinan  
WHO/UN-Water: relasi air bersih, sanitasi, dan kesehatan publik
"""
    )
    st.link_button("World Bank WDI (home)", "https://databank.worldbank.org/source/world-development-indicators")
    st.link_button("WHO (Health systems and financing)", "https://www.who.int/health-topics/health-systems")
    st.link_button("UNICEF Data (Maternal and child health)", "https://data.unicef.org/topic/maternal-health/")
    st.link_button("WHO/UNICEF JMP (Water, sanitation, hygiene)", "https://washdata.org/")

# -----------------------------
# Download long format (template)
# -----------------------------
st.subheader("📘 Data Lengkap (long format)")

csv_download = df_long.to_csv(index=False)
safe = indicator.replace(" ", "_").replace("/", "_").replace("(", "").replace(")", "")
st.download_button(
    "⬇ Download data (CSV)",
    csv_download,
    file_name=f"page9_kesehatan_{safe}.csv",
    mime="text/csv",
)
