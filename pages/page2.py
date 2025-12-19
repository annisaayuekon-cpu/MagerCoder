import streamlit as st
import pandas as pd
import os
import plotly.express as px

st.set_page_config(layout="wide")

st.title("👷 Tenaga Kerja & Pengangguran — Peta Dunia + Time Series")
st.write(
    "Halaman ini menampilkan indikator tenaga kerja dan pengangguran "
    "berdasarkan data referensi lokal (file CSV) yang ada di folder `data/`."
)

# -----------------------------------------------------------------------------
# PANDUAN INTERPRETASI (baru)
# -----------------------------------------------------------------------------
with st.expander("📌 Panduan interpretasi indikator (ringkas)", expanded=False):
    st.markdown(
        """
**Labor force participation rate** mengukur proporsi penduduk usia kerja yang aktif di pasar kerja (bekerja atau mencari kerja). Nilai tinggi sering selaras dengan partisipasi kerja yang kuat, sementara nilai rendah dapat terkait dengan demografi, pendidikan yang lebih panjang, hambatan partisipasi, atau efek discouraged workers.

**Unemployment rate** mengukur proporsi angkatan kerja yang tidak bekerja tetapi aktif mencari kerja. Nilai rendah tidak selalu identik dengan kualitas pasar kerja yang baik karena bisa terkait dengan informalitas tinggi atau definisi pencarian kerja yang berbeda antar negara.

**Youth unemployment** biasanya lebih volatil karena transisi sekolah ke kerja dan sensitivitas terhadap siklus ekonomi. Nilai tinggi sering dikaitkan dengan mismatch keterampilan, rigiditas pasar kerja pemula, atau lemahnya penciptaan pekerjaan untuk entry level.

**Employment by sector** menggambarkan struktur penyerapan tenaga kerja menurut sektor. Pergeseran dari pertanian ke industri dan jasa sering dibahas sebagai bagian dari transformasi struktural, tetapi interpretasinya bergantung pada konteks produktivitas dan kualitas pekerjaan.
"""
    )

# -----------------------------
# Lokasi folder data & mapping file
# -----------------------------
DATA_DIR = "data"

FILES = {
    "Labor force participation rate": "2.1 Labor force participation rate.csv",
    "Unemployment rate": "2.2 Unemployment rate.csv",
    "Youth unemployment": "2.3 Youth unemployment.csv",
    "Employment by sector": "2.4 Employment by sector.csv",
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
    Mengatur arah interpretasi: untuk pengangguran, nilai tinggi cenderung berarti tekanan pasar kerja lebih besar.
    """
    if "Unemployment" in label:
        return "higher_worse"
    return "neutral"


def _interpret_note(label: str) -> str:
    if label == "Labor force participation rate":
        return (
            "Pada indikator ini, posisi relatif yang lebih tinggi sering dikaitkan dengan partisipasi pasar kerja yang lebih besar. "
            "Pembacaan tetap perlu mempertimbangkan komposisi usia, pendidikan, dan norma partisipasi kerja."
        )
    if label == "Unemployment rate":
        return (
            "Pada indikator ini, posisi relatif yang lebih tinggi biasanya mencerminkan slack pasar kerja. "
            "Nilai yang sangat rendah perlu dibaca bersama konteks informalitas dan definisi pencarian kerja."
        )
    if label == "Youth unemployment":
        return (
            "Pada indikator ini, posisi relatif yang lebih tinggi sering muncul saat transisi sekolah ke kerja tidak mulus atau penciptaan pekerjaan pemula terbatas. "
            "Perubahan jangka pendek cenderung lebih tajam dibanding indikator lain."
        )
    if label == "Employment by sector":
        return (
            "Pada indikator ini, pembacaan mengarah pada struktur penyerapan tenaga kerja. "
            "Interpretasi yang bermakna biasanya membandingkan perubahan struktur dari waktu ke waktu, bukan satu titik tahun saja."
        )
    return "Interpretasi bersifat indikatif dan perlu dibaca bersama konteks statistik dan struktur ekonomi negara."

# -----------------------------
# Cek file yang tersedia
# -----------------------------
available_indicators = []
for label, fname in FILES.items():
    if os.path.exists(os.path.join(DATA_DIR, fname)):
        available_indicators.append(label)

if not available_indicators:
    st.error(
        f"Tidak ada file CSV Page 2 yang ditemukan di folder `{DATA_DIR}/`. "
        "Pastikan file 2.1–2.4 sudah diletakkan di sana."
    )
    st.stop()

# -----------------------------
# Pilih indikator & load data
# -----------------------------
indicator_label = st.selectbox(
    "Pilih indikator tenaga kerja/pengangguran", available_indicators
)
file_path = os.path.join(DATA_DIR, FILES[indicator_label])

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
df_long["value"] = pd.to_numeric(df_long["value"], errors="coerce")
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
# INTERPRETASI PETA (baru)
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

    st.markdown(
        """
Ringkasan kuartil memberi gambaran sebaran global pada tahun terpilih. Pembacaan peta menjadi lebih informatif jika posisi suatu negara dibandingkan terhadap median dan kuartil, bukan hanya melihat warna pada peta.
"""
    )
    st.caption(_interpret_note(indicator_label))

# -----------------------------------------------------------------------------
# ANALISIS DESKRIPTIF (narasi + rujukan jurnal)
# Letakkan setelah peta (setelah try/except px.choropleth), sebelum Time Series
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
    top_c = df_rank.head(top_n)["country"].tolist()
    bottom_c = df_rank.tail(bottom_n)["country"].tolist()

    top_str = ", ".join(top_c) if top_c else "NA"
    bottom_str = ", ".join(bottom_c) if bottom_c else "NA"

    vals = df_rank["value"]
    vmin = float(vals.min())
    vmax = float(vals.max())
    q25, q50, q75 = vals.quantile([0.25, 0.50, 0.75]).tolist()
    iqr = float(q75 - q25)

    # Narasi pembuka + “contoh interpretasi” gaya seperti page GDP
    st.markdown(
        f"""
Berdasarkan nilai terbaru **{indicator_label}** pada **{selected_year}**, terlihat perbedaan yang jelas antar negara.

• **Kelompok nilai tertinggi didominasi oleh:** **{top_str}**  
• **Kelompok nilai terendah didominasi oleh:** **{bottom_str}**

Rentang nilai pada tahun ini bergerak dari **{_fmt(vmin)}** hingga **{_fmt(vmax)}**, dengan median **{_fmt(q50)}** dan rentang antar kuartil (Q3–Q1) sebesar **{_fmt(iqr)}**. Posisi sebuah negara menjadi lebih bermakna jika dibaca relatif terhadap median dan kuartil, karena peta menampilkan distribusi, bukan “peringkat absolut” yang berdiri sendiri.
"""
    )

    # Narasi komprehensif + sitasi 5 jurnal (dirujuk di bawah via tautan)
    if indicator_label in ["Unemployment rate", "Youth unemployment"]:
        st.markdown(
            """
Pada indikator pengangguran, nilai tinggi lazim dibaca sebagai sinyal tekanan pasar kerja yang lebih besar, sedangkan nilai rendah biasanya mengarah pada kondisi yang lebih longgar. Literatur makro sering menempatkan pengangguran dalam relasi jangka pendek dengan pelemahan output melalui Okun’s law [1]. Untuk youth unemployment, level tinggi sering dikaitkan dengan friksi transisi sekolah ke kerja serta risiko “scarring” pada karier awal yang dampaknya dapat bertahan melampaui fase resesi [2].

Pembacaan lintas negara tetap perlu menempatkan konteks struktur ekonomi. Perubahan komposisi pekerjaan antar sektor dan dinamika transformasi struktural dapat mengubah profil pasar kerja dan produktivitas, sehingga pola pengangguran dan penyerapan tenaga kerja tidak selalu sejalan antar negara [3]. Ukuran pengangguran resmi juga dapat meng-underestimate masalah penyerapan tenaga kerja pada ekonomi dengan informalitas tinggi, sehingga interpretasi yang lebih kuat biasanya melihat indikator partisipasi dan kualitas pekerjaan sebagai pelengkap [5]. Variasi partisipasi angkatan kerja sendiri terkait erat dengan demografi dan fertilitas, yang memengaruhi ukuran angkatan kerja dan komposisi pencari kerja [4].
"""
        )
    elif indicator_label == "Labor force participation rate":
        st.markdown(
            """
Pada indikator partisipasi angkatan kerja, nilai tinggi sering dibaca sebagai partisipasi pasar kerja yang lebih besar, sedangkan nilai rendah dapat mencerminkan komposisi usia, lamanya pendidikan, hambatan partisipasi, atau preferensi rumah tangga. Literatur demografi-ekonomi menunjukkan hubungan kuat antara fertilitas dan partisipasi angkatan kerja perempuan dalam lintas negara, sehingga perbedaan LFPR sering selaras dengan perbedaan struktur demografi dan siklus hidup [4].

Dalam konteks pembangunan, transformasi struktural dan pergeseran pekerjaan antar sektor berperan membentuk peluang kerja, produktivitas, dan insentif partisipasi, sehingga pola LFPR dapat berbeda antara ekonomi yang didominasi pertanian, manufaktur, atau jasa [3]. Interpretasi juga perlu berhati-hati karena definisi “aktif mencari kerja” dan karakter informalitas dapat membuat indikator pasar kerja standar tidak menangkap seluruh tantangan penyerapan tenaga kerja [5]. Keterkaitan antara kondisi pasar kerja dan siklus output juga sering dibahas di literatur makro, termasuk relasi yang stabil antara pengangguran dan output pada banyak negara [1], sehingga membaca LFPR bersama pengangguran dapat memperkaya konteks.
"""
        )
    else:
        st.markdown(
            """
Untuk indikator struktur penyerapan kerja, pembacaan paling informatif biasanya fokus pada arah perubahan dari waktu ke waktu dan konteks transformasi struktural. Literatur pembangunan menekankan bahwa pergeseran tenaga kerja lintas sektor berkaitan dengan produktivitas dan pola pertumbuhan, sehingga komposisi pekerjaan menjadi jendela untuk membaca fase pembangunan dan kerentanan terhadap guncangan [3].

Indikator pasar kerja lintas negara tetap perlu dibaca dengan kehati-hatian karena ukuran standar dapat kurang sensitif terhadap surplus tenaga kerja terselubung pada ekonomi dengan informalitas tinggi [5]. Faktor demografi dan fertilitas juga berpengaruh pada pasokan tenaga kerja dan partisipasi, sehingga perubahan komposisi kerja sering bergerak bersama perubahan struktur penduduk usia kerja [4]. Di level siklis, relasi output dan pengangguran memberi konteks tentang kapan perubahan struktur kerja berkaitan dengan perlambatan ekonomi, bukan sekadar tren jangka panjang [1]. Youth unemployment memberi sinyal tambahan tentang kualitas transisi sekolah-ke-kerja dan risiko dampak jangka panjang pada generasi muda [2].
"""
        )

    st.caption("Catatan: Analisis ini bersifat deskriptif dan tidak dimaksudkan sebagai inferensi kausal.")

    with st.expander("📚 Referensi jurnal (tautan) — dasar interpretasi", expanded=False):
        st.markdown(
            """
[1] Okun’s law dan relasi output–pengangguran (stabil di banyak negara).  
[2] Youth unemployment dan efek jangka panjang pada karier awal.  
[3] Transformasi struktural dan pergeseran pekerjaan antar sektor dalam pembangunan.  
[4] Fertilitas dan partisipasi angkatan kerja perempuan lintas negara.  
[5] Keterbatasan konsep unemployment rate untuk negara berkembang.
"""
        )

        st.link_button(
            "Ball (2017) — Okun’s Law: Fit at Fifty? (Journal of Money, Credit and Banking)",
            "https://onlinelibrary.wiley.com/doi/abs/10.1111/jmcb.12420",
        )
        st.link_button(
            "Bell & Blanchflower (2011) — Young People and the Great Recession (Oxford Review of Economic Policy)",
            "https://academic.oup.com/oxrep/article-abstract/27/2/241/429358",
        )
        st.link_button(
            "McMillan, Rodrik & Verduzco-Gallo (2014) — Globalization, Structural Change, and Productivity Growth (World Development)",
            "https://www.sciencedirect.com/science/article/pii/S0305750X13002246",
        )
        st.link_button(
            "Bloom, Canning, Fink & Finlay (2009) — Fertility and Female LFPR (Journal of Economic Growth)",
            "https://link.springer.com/article/10.1007/s10887-009-9039-9",
        )
        st.link_button(
            "Sylla (2013) — Limitations of unemployment concept in developing countries (International Labour Review)",
            "https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1564-913X.2013.00167.x",
        )
        
# -----------------------------
# Time series per negara
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
    # INTERPRETASI TIME SERIES (baru)
    # -----------------------------------------------------------------------------
    st.subheader("🧾 Interpretasi tren (negara terpilih)")

    last_year = int(df_country["year"].max())
    last_val = float(df_country.loc[df_country["year"] == last_year, "value"].iloc[0])

    # banding 10 tahun terakhir jika tersedia
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
                "Tren meningkat pada periode pengamatan mengarah pada tekanan pasar kerja yang lebih besar dalam indikator pengangguran. "
                "Konfirmasi biasanya dilakukan dengan membaca pertumbuhan ekonomi, struktur pekerjaan, dan dinamika angkatan kerja."
            )
        elif avg_change < 0:
            st.markdown(
                "Tren menurun pada periode pengamatan mengarah pada pelonggaran tekanan pasar kerja dalam indikator pengangguran. "
                "Pembacaan yang lebih kuat biasanya mengaitkan pola ini dengan perubahan penciptaan kerja dan partisipasi angkatan kerja."
            )
        else:
            st.markdown(
                "Nilai relatif stabil pada periode pengamatan. Variasi kecil tetap mungkin bermakna jika negara berada pada level awal yang tinggi."
            )
    else:
        if avg_change > 0:
            st.markdown(
                "Tren meningkat menunjukkan perubahan naik pada indikator terpilih. "
                "Interpretasi konseptual bergantung pada indikator yang dipilih dan struktur pasar kerja negara."
            )
        elif avg_change < 0:
            st.markdown(
                "Tren menurun menunjukkan perubahan turun pada indikator terpilih. "
                "Interpretasi konseptual bergantung pada indikator yang dipilih dan struktur pasar kerja negara."
            )
        else:
            st.markdown(
                "Nilai relatif stabil pada periode pengamatan. Analisis lanjutan dapat melihat perubahan sebelum dan sesudah guncangan (misalnya krisis atau pandemi) jika tahun tersedia."
            )

    st.dataframe(df_country.reset_index(drop=True))

# -----------------------------
# Tabel lengkap & download
# -----------------------------
st.subheader("📘 Data Lengkap (long format)")
st.dataframe(df_long.reset_index(drop=True), use_container_width=True)

csv_download = df_long.to_csv(index=False)
st.download_button(
    "⬇ Download data (CSV)",
    csv_download,
    file_name=f"page2_tenaga_kerja_{indicator_label.replace(' ', '_')}.csv",
    mime="text/csv",
)
