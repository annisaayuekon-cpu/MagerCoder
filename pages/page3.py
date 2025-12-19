import streamlit as st
import pandas as pd
import os
import plotly.express as px

st.set_page_config(layout="wide")

st.title("🔥 Inflasi & Pengeluaran Konsumen — Peta Dunia + Time Series")
st.write(
    "Halaman ini menampilkan indikator inflasi dan pengeluaran konsumen "
    "berdasarkan data referensi lokal (file CSV) yang ada di folder `data/`."
)

# -----------------------------------------------------------------------------
# PANDUAN INTERPRETASI (format sama seperti page2)
# -----------------------------------------------------------------------------
with st.expander("📌 Panduan interpretasi indikator (ringkas)", expanded=False):
    st.markdown(
        """
**Inflation, consumer prices (annual %)** mengukur laju perubahan tahunan indeks harga konsumen. Angka tinggi dibaca sebagai tekanan kenaikan harga yang lebih kuat pada tahun tersebut. Nilai mendekati nol mengarah pada inflasi yang lemah. Nilai negatif biasanya dibaca sebagai episode deflasi atau disinflasi yang sangat tajam, lalu perlu dicek konteks guncangan harga dan kebijakan.

**Consumer expenditure** dipakai sebagai proksi permintaan domestik melalui pengeluaran konsumsi rumah tangga. Angka ini umumnya bergerak searah dengan pendapatan, siklus ekonomi, dan dinamika harga. Interpretasi lintas negara lebih aman lewat tren atau metrik per kapita (jika tersedia), karena level sangat dipengaruhi ukuran ekonomi dan populasi.
"""
    )

# -----------------------------
# Lokasi folder data & mapping file
# -----------------------------
DATA_DIR = "data"

# Dibuat toleran: kalau nama file beda sedikit, tetap ketemu yang ada di folder
FILES = {
    "Inflation, consumer prices (annual %)": [
        "3.1 Inflation (consumer prices %).csv",
        "3.1 Inflation, consumer prices (%).csv",
        "3.1 Inflation, consumer prices (%).csv",
        "3.1 Inflation, consumer prices (%).csv",
    ],
    "Consumer expenditure": [
        "3.2 Consumer expenditure.csv",
        "3.2. CONSUMER EXPENDITURE.csv",
        "3.2 Consumer Expenditure.csv",
        "3.2 CONSUMER EXPENDITURE.csv",
    ],
}

# -----------------------------
# Helper baca CSV (lebih toleran)
# -----------------------------
@st.cache_data
def load_csv_tolerant(path: str) -> pd.DataFrame:
    """
    Coba baca CSV dengan beberapa delimiter dan lewati baris bermasalah.
    """
    for sep in [";", ",", "\t"]:
        try:
            df = pd.read_csv(
                path,
                sep=sep,
                engine="python",
                on_bad_lines="skip"
            )
            if df.shape[1] > 1:
                return df
        except Exception:
            continue

    df = pd.read_csv(
        path,
        engine="python",
        on_bad_lines="skip"
    )
    return df


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


def _orientation(label: str) -> str:
    """
    Mengatur arah interpretasi: untuk inflasi, nilai tinggi dibaca sebagai tekanan harga lebih besar.
    """
    if "Inflation" in label:
        return "higher_worse"
    return "neutral"


def _interpret_note(label: str) -> str:
    if "Inflation" in label:
        return (
            "Pada indikator ini, posisi relatif yang lebih tinggi umumnya dibaca sebagai tekanan kenaikan harga yang lebih kuat pada tahun terpilih. "
            "Pembacaan yang rapi menempatkan angka terhadap kuartil dan median, lalu mengaitkannya dengan episode guncangan harga, nilai tukar, serta respons kebijakan."
        )
    if "Consumer expenditure" in label:
        return (
            "Pada indikator ini, pembacaan mengarah pada kekuatan permintaan domestik melalui konsumsi. "
            "Level lintas negara sangat dipengaruhi ukuran ekonomi dan populasi, jadi interpretasi paling kuat biasanya berbasis tren atau per kapita bila tersedia."
        )
    return "Interpretasi bersifat indikatif dan perlu dibaca bersama konteks statistik dan struktur ekonomi negara."


def _pick_existing_file(candidates: list[str]) -> str | None:
    for fname in candidates:
        if os.path.exists(os.path.join(DATA_DIR, fname)):
            return fname
    return None

# -----------------------------
# Cek file yang tersedia
# -----------------------------
available_indicators = []
resolved_files = {}

for label, candidates in FILES.items():
    found = _pick_existing_file(candidates)
    if found:
        available_indicators.append(label)
        resolved_files[label] = found

if not available_indicators:
    st.error(
        f"Tidak ada file CSV Page 3 yang ditemukan di folder `{DATA_DIR}/`. "
        "Pastikan file 3.1 dan 3.2 sudah diletakkan di sana."
    )
    st.stop()

# -----------------------------
# Pilih indikator & load data
# -----------------------------
indicator_label = st.selectbox(
    "Pilih indikator inflasi/pengeluaran", available_indicators
)
file_path = os.path.join(DATA_DIR, resolved_files[indicator_label])

try:
    df = load_csv_tolerant(file_path)
except Exception as e:
    st.error(f"Gagal membaca file `{os.path.basename(file_path)}`: {e}")
    st.stop()

st.subheader("📄 Preview Data Mentah")
st.dataframe(df.head(15), use_container_width=True)

# -----------------------------
# Deteksi kolom tahun & negara
# -----------------------------
cols = [str(c) for c in df.columns]
year_cols = [c for c in cols if c.isdigit() and len(c) == 4]

if not year_cols:
    st.error(
        "Tidak ditemukan kolom tahun (misalnya 1990, 2000, dst.) "
        "di file CSV ini. Cek kembali header kolom."
    )
    st.stop()

country_col = None
for cand in ["Country Name", "country", "Country", "Negara", "Entity"]:
    if cand in df.columns:
        country_col = cand
        break

if country_col is None:
    country_col = df.columns[0]

# Ubah ke format long: country, year, value
df_long = df.melt(
    id_vars=[country_col],
    value_vars=year_cols,
    var_name="year",
    value_name="value",
)

df_long["year"] = pd.to_numeric(df_long["year"], errors="coerce").astype("Int64")
df_long = df_long.rename(columns={country_col: "country"})

# Bersihkan format angka (koma desimal, placeholder missing)
s = df_long["value"].astype(str).str.strip()
mask_decimal_comma = s.str.contains(",", na=False) & ~s.str.contains(r"\.", na=False)
s.loc[mask_decimal_comma] = s.loc[mask_decimal_comma].str.replace(",", ".", regex=False)
s = s.replace({"..": "", "NA": "", "N/A": "", "nan": ""})
df_long["value"] = pd.to_numeric(s, errors="coerce")

df_long = df_long.dropna(subset=["value", "year"])

if df_long.empty:
    st.error("Setelah transformasi, tidak ada data bernilai (semua NaN).")
    st.stop()

df_long["year"] = df_long["year"].astype(int)

# -----------------------------
# Slider tahun untuk peta
# -----------------------------
years = sorted(df_long["year"].unique())
year_min = int(min(years))
year_max = int(max(years))

selected_year = st.slider(
    "Pilih tahun untuk peta dunia", year_min, year_max, year_max
)

df_map = df_long[df_long["year"] == selected_year]

st.subheader(f"🌍 Peta Dunia — {indicator_label} ({selected_year})")

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
            title=f"{indicator_label} — {selected_year}",
            labels={"value": indicator_label},
        )
        fig.update_layout(margin={"r": 0, "t": 40, "l": 0, "b": 0})
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(
            "Gagal membuat peta dunia. "
            "Cek apakah nama negara di CSV sesuai standar country names Plotly.\n\n"
            f"Detail error: {e}"
        )

# -----------------------------------------------------------------------------
# INTERPRETASI PETA (format sama seperti page2, tapi konten sesuai indikator)
# -----------------------------------------------------------------------------
st.subheader("🧠 Interpretasi peta (tahun terpilih)")

vals = df_map["value"].dropna()
n_countries = int(vals.shape[0])

if n_countries < 5:
    st.write("Data pada tahun terpilih terlalu sedikit untuk interpretasi distribusi.")
else:
    q25, q50, q75 = vals.quantile([0.25, 0.50, 0.75]).tolist()

    colA, colB, colC, colD = st.columns(4)
    colA.metric("Jumlah negara (ada data)", f"{n_countries:,}")
    colB.metric("Kuartil 1 (Q1)", _fmt(q25))
    colC.metric("Median (Q2)", _fmt(q50))
    colD.metric("Kuartil 3 (Q3)", _fmt(q75))

    if "Inflation" in indicator_label:
        para2 = (
            "Untuk inflasi, angka yang lebih tinggi dibaca sebagai tekanan kenaikan harga yang lebih kuat pada tahun tersebut. "
            "Pembacaan yang tegas menilai apakah sebuah negara sudah melampaui Q3 atau masih berada di sekitar median. "
            "Nilai yang sangat rendah atau negatif perlu dicek lagi karena bisa mencerminkan deflasi, disinflasi tajam, atau efek basis antar tahun."
        )
    else:
        para2 = (
            "Untuk consumer expenditure, angka yang lebih tinggi biasanya mencerminkan skala konsumsi yang lebih besar, sehingga levelnya tidak diperlakukan sebagai ukuran kesejahteraan lintas negara secara langsung. "
            "Interpretasi yang paling aman memakai kuartil sebagai pembanding posisi, lalu membaca tren untuk melihat penguatan atau pelemahan permintaan domestik."
        )

    st.markdown(
        f"""
Ringkasan kuartil memecah negara menjadi empat kelompok pada tahun terpilih. Median dipakai sebagai patokan, sehingga negara di atas median berada pada setengah distribusi dengan nilai indikator lebih tinggi. Q1 dan Q3 dipakai untuk menilai extreme point, sehingga nilai di bawah Q1 berada pada kelompok terbawah dan nilai di atas Q3 berada pada kelompok teratas.

{para2}
"""
    )
    st.caption(_interpret_note(indicator_label))

# -----------------------------------------------------------------------------
# ANALISIS DESKRIPTIF (format sama seperti page2, panjang selevel)
# -----------------------------------------------------------------------------
st.subheader("🧠 Analisis Ekonomi Deskriptif")

if df_map.empty:
    st.write("Analisis deskriptif membutuhkan data pada tahun yang dipilih.")
else:
    df_rank = (
        df_map[["country", "value"]]
        .dropna()
        .sort_values("value", ascending=False)
    )

    top_n = 5
    bottom_n = 5

    top_df = df_rank.head(top_n).copy()

    # Hindari top dan bottom beririsan bila data memadai
    bottom_pool = df_rank.tail(max(bottom_n * 3, bottom_n)).copy()
    bottom_df = bottom_pool[~bottom_pool["country"].isin(top_df["country"])].tail(bottom_n)
    if bottom_df.empty:
        bottom_df = df_rank.tail(bottom_n)

    top_c = top_df["country"].tolist()
    bottom_c = bottom_df["country"].tolist()

    top_str = ", ".join(top_c) if top_c else "NA"
    bottom_str = ", ".join(bottom_c) if bottom_c else "NA"

    vals_rank = df_rank["value"]
    vmin = float(vals_rank.min())
    vmax = float(vals_rank.max())
    q25r, q50r, q75r = vals_rank.quantile([0.25, 0.50, 0.75]).tolist()
    iqr = float(q75r - q25r)

    st.markdown(
        f"""
Berdasarkan nilai **{indicator_label}** pada **{selected_year}**, terlihat perbedaan antar negara dalam posisi relatif pada distribusi global.

• **Kelompok nilai tertinggi didominasi oleh:** **{top_str}**  
• **Kelompok nilai terendah didominasi oleh:** **{bottom_str}**

Rentang nilai bergerak dari **{_fmt(vmin)}** hingga **{_fmt(vmax)}**, dengan median **{_fmt(q50r)}** dan rentang antar kuartil (Q3–Q1) sebesar **{_fmt(iqr)}**. Pembacaan yang konsisten menempatkan negara terhadap median dan kuartil, lalu menilai seberapa jauh posisinya dari batas kuartil atas.
"""
    )

    if "Inflation" in indicator_label:
        st.markdown(
            """
Pada indikator inflasi, posisi tinggi biasanya dibaca sebagai episode tekanan harga yang lebih kuat. Literatur makro sering menempatkan inflasi sebagai variabel kunci yang dipengaruhi ekspektasi dan mekanisme penetapan harga, termasuk pembahasan dinamika inflasi dalam kerangka New Keynesian Phillips curve [2]. Pada level statistik, CPI sendiri memiliki isu pengukuran yang membuat interpretasi lintas negara perlu disiplin pada definisi keranjang dan bias indeks, terutama ketika inflasi berubah cepat [3].

Perbedaan lintas negara juga sering dikaitkan dengan keterbukaan ekonomi dan struktur guncangan harga, sehingga tingkat inflasi yang berbeda dapat muncul walau siklus global sama [1]. Pada praktik kebijakan, pembacaan yang paling operasional memisahkan negara yang berada di atas Q3 sebagai kelompok tekanan harga relatif tinggi, lalu mengaitkannya dengan respons kebijakan moneter dan stabilitas makro yang relevan [1].
"""
        )
    else:
        st.markdown(
            """
Pada consumer expenditure, posisi tinggi biasanya mencerminkan skala konsumsi agregat yang lebih besar, sehingga interpretasi lintas negara lebih kuat bila fokus pada tren atau per kapita. Literatur konsumsi menempatkan pengeluaran rumah tangga dalam kerangka intertemporal allocation, di mana perubahan konsumsi terkait ekspektasi pendapatan, risiko, dan kendala likuiditas [4]. Bukti klasik menunjukkan konsumsi cenderung lebih halus dibanding pendapatan, sehingga perubahan tahunan yang tajam biasanya mengindikasikan guncangan besar atau perubahan kondisi pembiayaan [5].

Dalam pembacaan deskriptif, negara di atas Q3 dapat dibaca sebagai kelompok dengan skala konsumsi agregat yang lebih besar pada tahun itu, tetapi simpulan kesejahteraan tetap memerlukan normalisasi (per kapita) dan pembacaan bersama indikator harga, karena kenaikan nominal bisa berasal dari kombinasi volume konsumsi dan inflasi.
"""
        )

    st.caption("Catatan: Analisis ini bersifat deskriptif dan tidak dimaksudkan sebagai inferensi kausal.")

    with st.expander("📚 Referensi jurnal (tautan) — dasar interpretasi", expanded=False):
        st.markdown(
            """
[1] Keterbukaan ekonomi dan variasi inflasi lintas negara.  
[2] Dinamika inflasi dalam kerangka struktural (New Keynesian Phillips curve).  
[3] Isu pengukuran dan bias indeks pada CPI.  
[4] Teori fungsi konsumsi dan peran kendala likuiditas.  
[5] Konsumsi dan implikasi hipotesis life cycle–permanent income.
"""
        )

        st.link_button(
            "Romer (1993) — Openness and Inflation: Theory and Evidence (QJE)",
            "https://academic.oup.com/qje/article-abstract/108/4/869/1899970",
        )
        st.link_button(
            "Galí & Gertler (1999) — Inflation dynamics: A structural econometric analysis (JME)",
            "https://www.sciencedirect.com/science/article/pii/S0304393299000239",
        )
        st.link_button(
            "Diewert (1998) — Index Number Issues in the Consumer Price Index (JEP)",
            "https://www.aeaweb.org/articles?id=10.1257/jep.12.1.47",
        )
        st.link_button(
            "Carroll (2001) — A Theory of the Consumption Function (JEP)",
            "https://www.aeaweb.org/articles?id=10.1257/jep.15.3.23",
        )
        st.link_button(
            "Hall (1978) — Stochastic Implications of the Life Cycle-Permanent Income Hypothesis (JPE)",
            "https://www.journals.uchicago.edu/doi/10.1086/260724",
        )

# -----------------------------
# Time series per negara (format sama seperti page2)
# -----------------------------
st.subheader("📈 Time Series per Negara")

country_list = sorted(df_long["country"].dropna().unique().tolist())
selected_country = st.selectbox(
    "Pilih negara untuk grafik time series", country_list
)

df_country = (
    df_long[df_long["country"] == selected_country]
    .sort_values("year")
)

if df_country.empty:
    st.write("Tidak ada data time series untuk negara ini.")
else:
    fig_ts = px.line(
        df_country,
        x="year",
        y="value",
        markers=True,
        title=f"{indicator_label} — {selected_country}",
    )
    fig_ts.update_layout(
        xaxis_title="Tahun",
        yaxis_title=indicator_label,
    )
    st.plotly_chart(fig_ts, use_container_width=True)

    # -----------------------------------------------------------------------------
    # INTERPRETASI TIME SERIES (format sama seperti page2)
    # -----------------------------------------------------------------------------
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
        start_val = float(df_window.loc[df_window["year"] == start_year, "value"].iloc[0])
        window_label = f"{start_year}–{last_year}"

    delta = last_val - start_val
    years_span = max(1, last_year - start_year)
    avg_change = delta / years_span

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Tahun terakhir", f"{last_year}")
    col2.metric("Nilai terakhir", _fmt(last_val))
    col3.metric(f"Perubahan ({window_label})", _fmt(delta))
    col4.metric("Rata-rata perubahan per tahun", _fmt(avg_change))

    orient = _orientation(indicator_label)

    if orient == "higher_worse":
        if avg_change > 0:
            st.markdown(
                "Tren meningkat mengarah pada penguatan tekanan harga pada periode pengamatan. "
                "Cara membacanya adalah mengaitkan pola ini dengan shock harga, kurs, dan respons kebijakan."
            )
        elif avg_change < 0:
            st.markdown(
                "Tren menurun mengarah pada disinflasi atau meredanya tekanan harga pada periode pengamatan. "
                "Validasi biasanya dilakukan dengan membaca stabilitas harga, pertumbuhan, dan perubahan kebijakan yang relevan."
            )
        else:
            st.markdown(
                "Nilai relatif stabil pada periode pengamatan. Variasi kecil tetap bisa diartikan berdampak kalau starting point-nya tinggi."
            )
    else:
        if avg_change > 0:
            st.markdown(
                "Tren meningkat menunjukkan pengeluaran konsumsi bergerak naik pada periode pengamatan. "
                "Jika angka bersifat nominal, kenaikan dapat memuat komponen volume konsumsi dan inflasi."
            )
        elif avg_change < 0:
            st.markdown(
                "Tren menurun menunjukkan pelemahan pengeluaran konsumsi pada periode pengamatan. "
                "Tren bisa dibaca dengan membandingkan kepada siklus ekonomi, pendapatan riil, dan kondisi pembiayaan."
            )
        else:
            st.markdown(
                "Nilai relatif stabil pada periode pengamatan. Pola sebelum dan sesudah guncangan besar dapat dijadikan pertimbangan dengan membandingkan dengan tahun tersebut."
            )

    st.dataframe(df_country.reset_index(drop=True))

# -----------------------------
# Tabel lengkap & download (format sama seperti page2)
# -----------------------------
st.subheader("📘 Data Lengkap (long format)")
st.dataframe(df_long.reset_index(drop=True), use_container_width=True)

csv_download = df_long.to_csv(index=False)
st.download_button(
    "⬇ Download data (CSV)",
    csv_download,
    file_name=f"page3_inflasi_konsumsi_{indicator_label.replace(' ', '_').replace('(', '').replace(')', '')}.csv",
    mime="text/csv",
)
